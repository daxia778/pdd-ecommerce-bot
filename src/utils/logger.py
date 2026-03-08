"""
统一日志模块 - 使用 Loguru 提供结构化、带颜色和 Trace-ID 追踪的日志输出。

L1 企业化升级:
  - 终端输出: 彩色 + trace_id（开发友好）
  - 文本文件: app.log（人类可读，自动轮转）
  - JSON 文件: app.json.log（机器可读，面向 ELK/Loki 采集）
  - contextvars: 全链路 trace_id 透传，任何深层调用均可自动绑定
"""

import contextvars
import os
import sys
import uuid

from loguru import logger

# ===== Trace ID 全链路追踪 =====
# 通过 contextvars 在整个请求生命周期（包括线程池中的 DB 操作）中传递 trace_id
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")


def generate_trace_id() -> str:
    """生成一个短 Trace ID (8 字符)，用于标记一次请求的完整生命周期"""
    return f"T-{uuid.uuid4().hex[:8]}"


def _trace_id_patcher(record):
    """Loguru patcher: 自动从 contextvars 获取当前 trace_id 注入到日志记录中"""
    record["extra"]["trace_id"] = trace_id_var.get("-")


# 确保日志目录存在
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 移除默认处理器，使用自定义配置
logger.remove()

# 注册 patcher — 所有 sink 共享此 patcher，自动注入 trace_id
logger = logger.patch(_trace_id_patcher)

# ── Sink 1: 终端输出（彩色 + trace_id，开发友好）──
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<yellow>{extra[trace_id]}</yellow> | "
        "<level>{message}</level>"
    ),
    level="INFO",
    colorize=True,
    enqueue=True,
)

# ── Sink 2: 文本文件（人类可读，自动轮转 + 压缩）──
logger.add(
    os.path.join(LOG_DIR, "app.log"),
    rotation="100 MB",
    retention="10 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {extra[trace_id]} | {message}",
    level="INFO",
    encoding="utf-8",
    enqueue=True,
)


# ── Sink 3: JSON 文件（机器可读，面向 ELK/Loki/Grafana 采集）──
logger.add(
    os.path.join(LOG_DIR, "app.json.log"),
    format="{message}",
    serialize=True,
    rotation="100 MB",
    retention="10 days",
    compression="zip",
    level="INFO",
    encoding="utf-8",
    enqueue=True,
)

__all__ = ["logger", "trace_id_var", "generate_trace_id"]
"""
Overwrite the existing logger.py with the upgraded version that includes JSON sink
and contextvars-based trace_id tracking.
"""
