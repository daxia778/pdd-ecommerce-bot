"""
RQ Worker - PPT 生产流水线任务队列消费者。
监听 ppt_tasks 队列，处理异步 PPT 生成任务。

使用新版 SimpleWorker / Worker API (rq >= 1.16)
"""

import os
import sys

# 确保能导入 src 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis import Redis
from rq import Queue, Worker

from config.settings import settings
from src.utils.logger import logger

LISTEN_QUEUES = ["ppt_tasks"]

if __name__ == "__main__":
    redis_conn = Redis.from_url(settings.redis_url)
    queues = [Queue(name, connection=redis_conn) for name in LISTEN_QUEUES]

    logger.info(f"✅ RQ Worker 启动 | 监听队列: {LISTEN_QUEUES} | Redis: {settings.redis_url}")

    worker = Worker(queues, connection=redis_conn)
    worker.work(with_scheduler=True)
