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
        order.status = OrderStatus.GENERATING
        order.generated_at = datetime.now()
        db.commit()
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
        order.status = OrderStatus.PROCESSING
        db.commit()

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
        order.status = OrderStatus.AWAITING_REVIEW
        db.commit()

        logger.info(f"Pipeline | ✅ 任务完成！等待人工审核 | 订单: {order_sn} | 文件: {clean_url}")

    except Exception as e:
        import traceback

        logger.error(f"Pipeline | ❌ 流水线执行异常 [{order_sn}]: {e}", exc_info=True)
        if order:
            order.status = OrderStatus.FAILED
            order.error_message = f"流水线异常: {str(e)}\n{traceback.format_exc()}"
            try:
                db.commit()
            except Exception:
                db.rollback()
    finally:
        db.close()


def run_production_pipeline_sync(order_sn: str):
    """同步包裹器，供 RQ Worker 独立进程调用"""
    asyncio.run(_async_run_production_pipeline(order_sn))


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
