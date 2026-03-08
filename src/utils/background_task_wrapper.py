import asyncio
import functools
import os
import traceback
from collections.abc import Callable
from typing import Any

from src.utils.logger import logger


def catch_background_exceptions(func: Callable) -> Callable:
    """
    P1-3: 后台任务异常监控包装器。
    用于捕获 FastAPI BackgroundTasks 或 asyncio.create_task 内部的未处理异常，
    防止它们静默失败并补充完整的错误堆栈追踪到系统日志。
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"🚨 Background Task '{func.__name__}' 崩溃: {e}\n{traceback.format_exc()}")
                # 生产环境通常不重新抛出，防止 ASGI 服务器不干净地崩溃
                if os.getenv("TESTING") == "true":
                    raise e from None

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"🚨 Background Task '{func.__name__}' (Sync) 崩溃: {e}\n{traceback.format_exc()}")

        return sync_wrapper
