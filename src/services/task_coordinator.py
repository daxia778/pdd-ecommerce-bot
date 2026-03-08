"""
任务协调器 - PPT 生产流水线中心调度器。
负责管理从需求确认到生成、后处理、审核的完整流程。

P0 修复: 移除模块级 Redis/RQ 强依赖。
  - 有 Redis：推入 RQ 队列，由 worker.py 独立进程消费
  - 无 Redis：fallback 到 asyncio.create_task，在当前进程内异步执行（单机模式）
"""

import asyncio
import json
import uuid
from datetime import datetime

from config.settings import settings
from src.core.order_state_machine import transition_order
from src.models.database import Order, SessionLocal
from src.models.enums import OrderStatus
from src.utils.logger import logger

# ===== 懒加载 Redis/RQ（不在模块加载时执行，避免崩溃）=====

_redis_conn = None
_task_queue = None


def _get_queue():
    """尝试获取 RQ 任务队列，失败则返回 None（降级到 asyncio 模式）"""
    global _redis_conn, _task_queue
    if _task_queue is not None:
        return _task_queue
    try:
        from redis import Redis
        from rq import Queue

        _redis_conn = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        _redis_conn.ping()
        _task_queue = Queue("ppt_tasks", connection=_redis_conn)
        logger.info("✅ TaskCoordinator | RQ 队列初始化成功（Redis 模式）")
        return _task_queue
    except Exception as e:
        logger.warning(f"⚠️ TaskCoordinator | Redis 不可用，降级到 asyncio 本地模式: {e}")
        return None


# ===== 核心流水线逻辑 =====


# P1-2: Playwright 任务全局超时（防止 NotebookLM 卡死导致 worker 永久挂起）
# 分别为「生成PPT」和「去水印」两步配置独立超时，方便后续按需调整
PIPELINE_GENERATE_TIMEOUT_S: int = 480  # 生成步骤最多 8 分钟
PIPELINE_WATERMARK_TIMEOUT_S: int = 120  # 去水印最多 2 分钟


async def _async_run_production_pipeline(order_sn: str):
    """
    后台生产流水线核心异步逻辑。
    NotebookLM Playwright 自动化 → 失败降级到 python-pptx 本地生成

    P1-2: 每个 Playwright 步骤均受 asyncio.wait_for 限制最大执行时长，
          超时后抛出 TimeoutError，由 except 块将订单标记为 failed，
          运营人员可从看板重新触发，防止僵尸 Task 永久占用进程资源。
    """
    db = SessionLocal()
    order = None
    try:
        order = db.query(Order).filter(Order.order_sn == order_sn).first()
        if not order:
            logger.error(f"Pipeline | 订单不存在，跳过 | order_sn: {order_sn}")
            return

        req = json.loads(order.requirement_json or "{}")

        # --- Step 1: 调用 NotebookLM（Playwright 自动化）生成 ---
        transition_order(order, OrderStatus.GENERATING, db=db)
        logger.info(f"Pipeline | 开始生成 | 订单: {order_sn} | 主题: {req.get('topic')}")

        from src.services.notebooklm_client import notebooklm_client

        try:
            # P1-2: 限制 Playwright 最大执行时间，超时则抛 asyncio.TimeoutError
            file_url = await asyncio.wait_for(
                notebooklm_client.generate_ppt(
                    topic=req.get("topic", "未命名主题"),
                    pages=req.get("pages", 10),
                    style=req.get("style", "商务"),
                    requirements=req.get("details", ""),
                ),
                timeout=PIPELINE_GENERATE_TIMEOUT_S,
            )
        except asyncio.TimeoutError as err:
            raise TimeoutError(
                f"NotebookLM 生成步骤超时（>{PIPELINE_GENERATE_TIMEOUT_S}s），可能是网络或 Google 服务异常"
            ) from err
        order.file_url = file_url
        db.commit()

        # --- Step 2: 后处理（去水印）---
        transition_order(order, OrderStatus.PROCESSING, db=db)

        try:
            # P1-2: 去水印步骤独立超时
            clean_url = await asyncio.wait_for(
                notebooklm_client.remove_watermark(file_url),
                timeout=PIPELINE_WATERMARK_TIMEOUT_S,
            )
        except asyncio.TimeoutError as err:
            raise TimeoutError(f"去水印步骤超时（>{PIPELINE_WATERMARK_TIMEOUT_S}s），跳过去水印，使用原文件") from err
        order.clean_file_url = clean_url

        # --- Step 3: 进入待审核状态 ---
        transition_order(order, OrderStatus.AWAITING_REVIEW, db=db)

        logger.info(f"Pipeline | ✅ 任务完成！等待人工审核 | 订单: {order_sn} | 文件: {clean_url}")

    except Exception as e:
        import traceback

        logger.error(f"Pipeline | ❌ 流水线执行异常 [{order_sn}]: {e}", exc_info=True)
        if order:
            err_msg = f"流水线异常: {str(e)}\n{traceback.format_exc()}"
            try:
                transition_order(order, OrderStatus.FAILED, db=db, error_message=err_msg)
            except Exception:
                db.rollback()
    finally:
        db.close()


def run_production_pipeline_sync(order_sn: str):
    """同步包裹器，供 RQ Worker 独立进程调用"""
    asyncio.run(_async_run_production_pipeline(order_sn))


# ===== P0-Root-Cause-Sweep: 死单自动巡检与回收 =====

# 超过此时间仍处于 GENERATING/PROCESSING 状态的订单将被回收
STALE_ORDER_TIMEOUT_MINUTES: int = 30
# 巡检间隔
WATCHDOG_INTERVAL_SECONDS: int = 900  # 15 分钟


def recover_stale_orders() -> int:
    """
    扫描并回收超时的"死单"。

    当进程被强杀或 Redis/Playwright 崩溃时，订单可能永久卡在
    GENERATING 或 PROCESSING 状态。此函数将这些订单回退为 FAILED，
    并记录错误信息以便运营人员排查。

    Returns: 回收的订单数量
    """
    from datetime import timedelta

    db = SessionLocal()
    recovered_count = 0
    try:
        cutoff = datetime.now() - timedelta(minutes=STALE_ORDER_TIMEOUT_MINUTES)
        stale_orders = (
            db.query(Order)
            .filter(
                Order.status.in_([OrderStatus.GENERATING, OrderStatus.PROCESSING]),
                Order.updated_at < cutoff,
            )
            .all()
        )

        for order in stale_orders:
            err_msg = (
                f"[Watchdog] 订单在 {order.status} 状态超过 {STALE_ORDER_TIMEOUT_MINUTES} 分钟，"
                f"已被自动回收。可能原因：进程被强杀、Playwright 超时或网络异常。"
            )
            old_status = order.status
            try:
                transition_order(order, OrderStatus.FAILED, db=db, error_message=err_msg)
                recovered_count += 1
                logger.warning(
                    f"Watchdog | 🔄 回收死单 | order_sn: {order.order_sn} | "
                    f"原状态: {old_status} | updated_at: {order.updated_at}"
                )
            except Exception as e:
                logger.error(f"Watchdog 回收状态转换失败: {e}")
            logger.info(f"Watchdog | ✅ 本轮巡检完成，回收了 {recovered_count} 个死单")
        else:
            logger.debug("Watchdog | 本轮巡检完成，无死单需要回收")

    except Exception as e:
        logger.error(f"Watchdog | ❌ 死单巡检异常: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

    return recovered_count


async def start_stale_order_watchdog():
    """
    启动死单巡检后台任务。

    由 FastAPI lifespan 启动阶段调用，通过 asyncio.create_task 运行。
    每 15 分钟执行一次 recover_stale_orders()，在独立线程中执行避免阻塞事件循环。
    """
    from src.models.database import run_in_db_thread

    logger.info(
        f"Watchdog | 🐕 死单巡检已启动 | 间隔: {WATCHDOG_INTERVAL_SECONDS}s | 超时阈值: {STALE_ORDER_TIMEOUT_MINUTES}min"
    )

    # 启动时立即执行一次
    await run_in_db_thread(recover_stale_orders)

    while True:
        await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)
        try:
            await run_in_db_thread(recover_stale_orders)
        except Exception as e:
            logger.error(f"Watchdog | 后台巡检异常: {e}")


# ===== 任务协调器 =====


class TaskCoordinator:
    async def create_and_start_pipeline(self, user_id: str, platform: str, requirement: dict):
        """
        创建新订单并启动生产流水线。
        - 有 Redis: 推入 RQ 队列（worker.py 消费）
        - 无 Redis: 直接 asyncio.create_task（当前进程后台运行）
        """
        uid_suffix = str(uuid.uuid4()).replace("-", "")[:4].upper()
        order_sn = f"PPT{datetime.now().strftime('%Y%m%d%H%M%S')}{str(user_id)[-4:]}{uid_suffix}"

        # 提取新增字段
        order_type = requirement.get("order_type", "standard")
        urgency = requirement.get("urgency", "normal")

        # 1. 持久化订单到数据库（初始状态：等待微信二维码）
        db = SessionLocal()
        try:
            new_order = Order(
                order_sn=order_sn,
                user_id=user_id,
                platform=platform,
                order_type=order_type,
                urgency=urgency,
                status=OrderStatus.WECHAT_PENDING,
                requirement_json=json.dumps(requirement, ensure_ascii=False),
            )
            db.add(new_order)
            db.commit()
            logger.info(
                f"Pipeline | 订单创建成功: {order_sn} | 用户: {user_id} | 类型: {order_type} | 紧急度: {urgency}"
            )
        except Exception as e:
            logger.error(f"Pipeline | 创建订单失败: {e}")
            db.rollback()
            return None
        finally:
            db.close()

        # 2. 异步通知企业微信（如已配置）
        try:
            from src.services.wecom_client import wecom_client

            asyncio.create_task(
                wecom_client.notify_new_order(
                    order_sn=order_sn,
                    user_id=user_id,
                    requirement=requirement,
                )
            )
        except Exception as e:
            logger.debug(f"企业微信通知跳过: {e}")

        # 3. 分派 PPT 生产任务
        queue = _get_queue()
        if queue is not None:
            # Redis 模式：推入 RQ 队列
            try:
                job = queue.enqueue(run_production_pipeline_sync, order_sn)
                logger.info(f"Pipeline | 已加入 RQ 队列 | Job ID: {job.id}")
            except Exception as e:
                logger.warning(f"Pipeline | RQ 入队失败，降级到 asyncio | {e}")
                asyncio.create_task(_async_run_production_pipeline(order_sn))
        else:
            # asyncio 本地模式
            asyncio.create_task(_async_run_production_pipeline(order_sn))
            logger.info(f"Pipeline | asyncio 本地模式已启动 | 订单: {order_sn}")

        return order_sn


task_coordinator = TaskCoordinator()
