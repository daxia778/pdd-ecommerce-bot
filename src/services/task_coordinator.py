"""
任务协调器 - PPT 生产流水线中心调度器。
负责管理从需求确认到生成、后处理、审核的完整流程。
"""
import json
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from redis import Redis
from rq import Queue

from config.settings import settings
from src.models.database import Order, SessionLocal
from src.services.notebooklm_client import notebooklm_client
from src.utils.logger import logger

redis_conn = Redis.from_url(settings.redis_url)
task_queue = Queue('ppt_tasks', connection=redis_conn)

async def _async_run_production_pipeline(order_sn: str):
    """
    后台生产流水线核心异步逻辑。
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_sn == order_sn).first()
        if not order:
            return

        req = json.loads(order.requirement_json)

        # --- Step 1: 调用 NotebookLM 生成 ---
        order.status = "generating"
        order.generated_at = datetime.now()
        db.commit()

        file_url = await notebooklm_client.generate_ppt(
            topic=req.get("topic", "未命名主题"),
            pages=req.get("pages", 10),
            style=req.get("style", "商务"),
            requirements=req.get("details", "")
        )
        order.file_url = file_url
        db.commit()

        # --- Step 2: 后处理（去水印）---
        order.status = "processing"
        db.commit()

        clean_url = await notebooklm_client.remove_watermark(file_url)
        order.clean_file_url = clean_url
        
        # --- Step 3: 进入待审核状态 ---
        order.status = "awaiting_review"
        db.commit()
        
        logger.info(f"Pipeline | 任务完成！等待人工审核 | 订单: {order_sn} | 文件: {clean_url}")
        
    except Exception as e:
        logger.error(f"Pipeline | 流水线执行异常 [{order_sn}]: {e}")
    finally:
        db.close()

def run_production_pipeline_sync(order_sn: str):
    """同步包裹器，供 RQ Worker 调用"""
    asyncio.run(_async_run_production_pipeline(order_sn))


class TaskCoordinator:
    async def create_and_start_pipeline(self, user_id: str, platform: str, requirement: dict):
        """
        创建一个新任务并推入 RQ 队列异步生成。
        """
        order_sn = f"PPT{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id[-4:]}"
        
        # 1. 持久化到数据库
        db = SessionLocal()
        try:
            new_order = Order(
                order_sn=order_sn,
                user_id=user_id,
                platform=platform,
                status="req_fixed",
                requirement_json=json.dumps(requirement, ensure_ascii=False)
            )
            db.add(new_order)
            db.commit()
            logger.info(f"Pipeline | 订单创建成功: {order_sn} | 用户: {user_id}")
            
            # 2. 推入 Redis 任务队列
            # 将运行环境交由专门的 worker.py 独立进程负责，避免污染 Web 主流程
            job = task_queue.enqueue(run_production_pipeline_sync, order_sn)
            logger.info(f"Pipeline | 已加入 RQ 队列 | Job ID: {job.id}")
            
            return order_sn
        except Exception as e:
            logger.error(f"Pipeline | 创建订单失败: {e}")
            db.rollback()
            return None
        finally:
            db.close()


task_coordinator = TaskCoordinator()
