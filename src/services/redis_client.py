"""
统一 Redis 客户端 — L1 企业化: 提供高可用连接池与异步访问支持。

将原本散落于各处的内存 Cache（TTLCache）和重复初始化的 Redis 连接统一。
支持异常转移与平滑降级（如 Redis 宕机时安全地退回内存模式或拒绝服务避免雪崩）。
"""

from __future__ import annotations

import json

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from config.settings import settings
from src.utils.logger import logger


class RedisClient:
    """
    统一的异步 Redis 客户端封装（带连接池和自动重连）。
    """

    def __init__(self):
        # 初始化连接池
        self.pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=100,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
            decode_responses=True,  # 自动将字节解码为字符串
        )
        self._redis = Redis(connection_pool=self.pool)
        self._is_connected = False

    async def initialize(self) -> bool:
        """启动时校验连接是否可用（给 FastAPI lifespan 调用）"""
        try:
            await self._redis.ping()
            self._is_connected = True
            logger.info("✅ Redis 统一连接池初始化完成。")
            return True
        except RedisError as e:
            logger.warning(f"⚠️ Redis 初始化失败，服务可能降级: {e}")
            self._is_connected = False
            return False

    async def close(self):
        """关闭连接池"""
        try:
            await self._redis.aclose()  # redis-py 5.x 推荐的清理方式
            await self.pool.disconnect()
            logger.info("✅ Redis 连接池已安全关闭。")
        except Exception as e:
            logger.error(f"关闭 Redis 失败: {e}")

    @property
    def is_available(self) -> bool:
        return self._is_connected

    async def get(self, key: str) -> str | None:
        """封装 GET，附带异常捕获"""
        if not self._is_connected:
            return None
        try:
            return await self._redis.get(key)
        except RedisError as e:
            logger.error(f"Redis GET 失败 [{key}]: {e}")
            return None

    async def set(self, key: str, value: str | int | float, ex: int | None = None) -> bool:
        """封装 SET，支持过期时间"""
        if not self._is_connected:
            return False
        try:
            await self._redis.set(key, value, ex=ex)
            return True
        except RedisError as e:
            logger.error(f"Redis SET 失败 [{key}]: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """封装 DEL"""
        if not self._is_connected or not keys:
            return 0
        try:
            return await self._redis.delete(*keys)
        except RedisError as e:
            logger.error(f"Redis DEL 失败 [{keys}]: {e}")
            return 0

    # --- 复杂结构支持 ---

    async def get_json(self, key: str) -> dict | list | None:
        """获取并解析 JSON 数据"""
        val = await self.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(self, key: str, value: dict | list, ex: int | None = None) -> bool:
        """序列化并存入 JSON 数据"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return await self.set(key, json_str, ex=ex)
        except (TypeError, ValueError) as e:
            logger.error(f"Redis JSON 序列化失败 [{key}]: {e}")
            return False

    # --- 高级操作支持 ---

    @property
    def client(self) -> Redis:
        """暴露原生 client 供执行 Pipeline 或 List/Hash 等高级命令"""
        return self._redis


# 懒加载全局单例
redis_client = RedisClient()
