"""
P1-FIX: 安全的 asyncio.create_task 封装。

裸 asyncio.create_task() 返回的 Task 如果没有被任何变量引用，
Python GC 可能在 Task 执行期间回收它，导致任务静默消失。

本模块维护一个全局 Set 持有所有后台 Task 的强引用，
Task 完成后通过 done_callback 自动移除。

用法:
    from src.utils.safe_task import create_safe_task
    create_safe_task(some_coroutine(), name="notify-wecom")
"""

from __future__ import annotations

import asyncio

from src.utils.logger import logger

# 全局强引用集合，防止 GC 回收正在运行的 Task
_background_tasks: set[asyncio.Task] = set()


def create_safe_task(coro, *, name: str | None = None) -> asyncio.Task:
    """
    创建一个受强引用保护的后台 asyncio Task。

    - 自动加入 _background_tasks 集合，防止 GC 回收
    - Task 完成（成功/失败/取消）后自动从集合中移除
    - 捕获并记录未处理的异常，防止静默失败
    """
    task = asyncio.create_task(coro, name=name)
    _background_tasks.add(task)
    task.add_done_callback(_on_task_done)
    return task


def _on_task_done(task: asyncio.Task) -> None:
    """Task 完成回调：移除强引用 + 记录未捕获异常。"""
    _background_tasks.discard(task)
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        task_name = task.get_name() if hasattr(task, "get_name") else "unnamed"
        logger.error(f"后台任务异常 [{task_name}]: {type(exc).__name__}: {exc}")
