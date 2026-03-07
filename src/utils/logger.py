"""
统一日志模块 - 使用 Loguru 提供结构化、带颜色和 Request-ID 追踪的日志输出。
P1 升级: 增加 request_id 上下文绑定，支持全链路追踪
"""

import os
import sys

from loguru import logger

# 确保日志目录存在
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 移除默认处理器，使用自定义配置
logger.remove()

# 终端输出：带颜色 + request_id
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<yellow>{extra[request_id]}</yellow> | "
        "<level>{message}</level>"
    ),
    level="INFO",
    colorize=True,
    enqueue=True,
)

# 文件输出：自动轮转、保留 10 天、zip 压缩
logger.add(
    os.path.join(LOG_DIR, "app.log"),
    rotation="100 MB",
    retention="10 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {extra[request_id]} | {message}",
    level="INFO",
    encoding="utf-8",
    enqueue=True,
)

# 默认 request_id 为空串（无请求上下文时不显示 request_id）
logger = logger.bind(request_id="-")

__all__ = ["logger"]
