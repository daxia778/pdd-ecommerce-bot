import os
import sys
import asyncio
from redis import Redis
from rq import Worker, Queue, Connection

# 确保能倒入 src 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.settings import settings
from src.utils.logger import logger

listen = ['ppt_tasks']
redis_conn = Redis.from_url(settings.redis_url)

if __name__ == '__main__':
    logger.info("启动 RQ Worker，监听队列: ppt_tasks")
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        worker.work()
