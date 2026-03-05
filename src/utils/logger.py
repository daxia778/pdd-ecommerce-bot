"""
统一日志模块 - 使用 Loguru 提供结构化、带颜色的日志输出。
"""
import sys
from loguru import logger

# 移除默认 handler，使用自定义格式
logger.remove()

# 控制台 - 带颜色，便于开发调试
logger.add(
    sys.stdout,
    level="DEBUG",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    colorize=True,
)

# 文件日志 - 自动轮转，保留 7 天
logger.add(
    "logs/app.log",
    level="INFO",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

__all__ = ["logger"]
