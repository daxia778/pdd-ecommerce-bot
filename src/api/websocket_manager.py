"""
WebSocket 连接管理器 — 管理所有活跃的 WebSocket 连接。

P0-Fix-3: 增加 asyncio.Lock 保护并发安全，broadcast 遍历时使用快照副本。
"""

from __future__ import annotations

import asyncio
import json

from fastapi import WebSocket

from src.utils.logger import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        # P0-Fix-3: 异步锁保护 connect/disconnect/broadcast 并发安全
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return

        message_str = json.dumps(message)
        dead_connections = []

        # P0-Fix-3: 使用快照副本遍历，防止并发修改导致迭代异常
        async with self._lock:
            snapshot = list(self.active_connections)

        for connection in snapshot:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                dead_connections.append(connection)

        # 清理死连接
        if dead_connections:
            async with self._lock:
                for dead in dead_connections:
                    if dead in self.active_connections:
                        self.active_connections.remove(dead)


# 全局单例
manager = ConnectionManager()
