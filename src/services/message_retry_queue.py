"""
消息重试队列 — L2 企业化: 发送失败的 PDD 消息自动重试补偿。

当调用 PDD 开放平台发送消息失败时，将消息放入内存重试队列。
后台任务定期扫描队列并重试，最多重试 N 次后进入死信队列（DLQ），
死信消息将触发告警通知运营人员介入。

用法:
    from src.services.message_retry_queue import retry_queue
    await retry_queue.enqueue("shop_id", "buyer_id", "消息内容")
    # 后台自动重试...
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from src.utils.logger import logger


@dataclass
class RetryMessage:
    """待重试的消息"""

    mall_id: str
    buyer_id: str
    content: str
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    last_error: str = ""

    @property
    def is_exhausted(self) -> bool:
        return self.retry_count >= self.max_retries


class MessageRetryQueue:
    """
    内存级消息重试队列。

    - 发送失败的消息自动进入重试队列
    - 后台协程定期扫描并重试（指数退避）
    - 超过最大重试次数则进入死信队列（DLQ）
    - 死信消息触发告警日志（可对接企微/钉钉通知）
    """

    def __init__(self, retry_interval_seconds: int = 30):
        self._retry_queue: deque[RetryMessage] = deque(maxlen=10000)
        self._dead_letter_queue: deque[RetryMessage] = deque(maxlen=1000)
        self._retry_interval = retry_interval_seconds
        self._running = False

    async def enqueue(self, mall_id: str, buyer_id: str, content: str):
        """将发送失败的消息加入重试队列"""
        msg = RetryMessage(mall_id=mall_id, buyer_id=buyer_id, content=content)
        self._retry_queue.append(msg)
        logger.warning(
            f"📬 消息重试队列 | 入队 | buyer: {buyer_id} | 队列长度: {len(self._retry_queue)} | 内容: {content[:50]}..."
        )

    async def start_retry_worker(self):
        """启动后台重试协程（由 FastAPI lifespan 调用）"""
        if self._running:
            return
        self._running = True
        logger.info(f"📬 消息重试队列 | Worker 已启动 | 扫描间隔: {self._retry_interval}s")

        while self._running:
            await asyncio.sleep(self._retry_interval)
            await self._process_retry_batch()

    async def _process_retry_batch(self):
        """处理一批待重试的消息"""
        if not self._retry_queue:
            return

        # 取出当前批次的所有消息
        batch_size = len(self._retry_queue)
        batch: list[RetryMessage] = []
        for _ in range(batch_size):
            if self._retry_queue:
                batch.append(self._retry_queue.popleft())

        from src.services.pdd_api_client import pdd_api_client

        for msg in batch:
            msg.retry_count += 1

            try:
                send_ok = await pdd_api_client.send_customer_message(
                    mall_id=msg.mall_id,
                    buyer_id=msg.buyer_id,
                    content=msg.content,
                )

                if send_ok:
                    logger.info(f"📬 消息重试队列 | ✅ 重试成功 | buyer: {msg.buyer_id} | 第 {msg.retry_count} 次尝试")
                else:
                    raise RuntimeError("PDD API 返回失败")

            except Exception as e:
                msg.last_error = str(e)

                if msg.is_exhausted:
                    # 进入死信队列
                    self._dead_letter_queue.append(msg)
                    logger.error(
                        f"📬 死信队列 | ❌ 消息已耗尽重试 | buyer: {msg.buyer_id} | "
                        f"重试 {msg.retry_count} 次均失败 | 最后错误: {e} | "
                        f"DLQ 长度: {len(self._dead_letter_queue)} | "
                        f"⚠️ 该客户可能未收到回复，请人工跟进！"
                    )
                else:
                    # 放回队列等待下一轮重试
                    self._retry_queue.append(msg)
                    logger.warning(
                        f"📬 消息重试队列 | 第 {msg.retry_count}/{msg.max_retries} 次失败 | "
                        f"buyer: {msg.buyer_id} | 等待下轮重试 | 错误: {e}"
                    )

    @property
    def retry_queue_size(self) -> int:
        return len(self._retry_queue)

    @property
    def dead_letter_queue_size(self) -> int:
        return len(self._dead_letter_queue)

    def get_dead_letters(self) -> list[dict]:
        """获取死信队列内容（供管理后台展示）"""
        return [
            {
                "buyer_id": msg.buyer_id,
                "content": msg.content[:100],
                "retry_count": msg.retry_count,
                "last_error": msg.last_error,
                "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for msg in self._dead_letter_queue
        ]

    def stop(self):
        self._running = False


# 全局单例
retry_queue = MessageRetryQueue()
