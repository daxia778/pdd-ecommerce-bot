"""
用户 Session 管理器 - Redis 缓存 & SQLite 持久化版本。

策略：
  - Redis List 作为热缓存，支持多实例并发读写
  - 每次 add_message 同步写入 SQLite（messages 表）
  - 冷启动时从 DB 加载历史，回填到 Redis
  - P1-1: 引入 Redis，增强扩展性与并发安全
"""
import json
import redis
from typing import List
from src.utils.logger import logger
from config.settings import settings


class SessionManager:
    """
    基于 Redis 缓存的高亮 Session 管理器。
    代替之前的单进程内存 dict 缓存。
    """

    def __init__(self, max_history: int = 10):
        self._max_history = max_history
        self._redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        logger.info(f"SessionManager(Redis) 初始化 | Redis: {settings.redis_url} | 最大历史: {max_history}")
        
    def _redis_key(self, user_id: str) -> str:
        return f"pdd_bot:session:{user_id}"

    # ------------------------------------------------------------------
    # 写操作 — 同步写库
    # ------------------------------------------------------------------

    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        db=None,
        platform: str = "test",
    ) -> None:
        """异步接口，底层直接调用同步防重入"""
        self.add_message_sync(user_id, role, content, db, platform)

    def add_message_sync(
        self,
        user_id: str,
        role: str,
        content: str,
        db=None,
        platform: str = "test",
    ) -> None:
        """
        向用户会话添加一条消息。
        - 写入 Redis List (RPUSH + LTRIM)
        - 写入 SQLite
        """
        key = self._redis_key(user_id)
        msg_json = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        
        # 1. 写入 Redis
        pipeline = self._redis_client.pipeline()
        pipeline.rpush(key, msg_json)
        # LTRIM 保留最新的 N 条 (-N to -1)
        # 例如 max_history=10, 保留 -10 0 (其实 Redis LTRIM 支持负数索引)
        pipeline.ltrim(key, -self._max_history, -1)
        # 设置过期时间 24H 自动清理冷数据
        pipeline.expire(key, 86400)
        pipeline.execute()

        # 2. 写 SQLite（持久化）
        if db is not None:
            try:
                from src.services.db_service import save_message_and_upsert_session
                save_message_and_upsert_session(
                    db,
                    user_id=user_id,
                    role=role,
                    content=content,
                    platform=platform,
                )
            except Exception as e:
                logger.error(f"Session 写库失败 | user_id: {user_id} | {e}")

        logger.debug(f"Session 更新 | user_id: {user_id} | 缓存至 Redis")

    # ------------------------------------------------------------------
    # 读操作 — Redis 优先，未命中从 DB 加载
    # ------------------------------------------------------------------

    def get_history(self, user_id: str, db=None) -> List[dict]:
        """
        获取用户的完整对话历史。
        """
        key = self._redis_key(user_id)
        
        # 1. 尝试从 Redis 取
        if self._redis_client.exists(key):
            cached_msgs = self._redis_client.lrange(key, 0, -1)
            return [json.loads(m) for m in cached_msgs]
            
        # 2. 从 DB 穿透查询
        if db is not None:
            return self._load_from_db(user_id, db)
            
        return []

    def _load_from_db(self, user_id: str, db) -> List[dict]:
        """首屏冷启动：从 SQLite 加载历史消息到 Redis 缓存"""
        try:
            from src.services.db_service import get_messages
            msgs = get_messages(db, user_id=user_id, limit=self._max_history)
            if not msgs:
                return []
                
            history = [{"role": m.role, "content": m.content} for m in msgs]
            
            # 回填 Redis
            key = self._redis_key(user_id)
            pipeline = self._redis_client.pipeline()
            for h in history:
                pipeline.rpush(key, json.dumps(h, ensure_ascii=False))
            pipeline.expire(key, 86400)
            pipeline.execute()
            
            logger.info(f"Session 从DB加载并回填缓存 | user_id: {user_id} | 条数: {len(history)}")
            return history
            
        except Exception as e:
            logger.error(f"Session 从DB加载失败 | user_id: {user_id} | {e}")
            return []

    # ------------------------------------------------------------------
    # 管理操作
    # ------------------------------------------------------------------

    def clear_session(self, user_id: str) -> None:
        """从 Redis 清空指定用户的缓存"""
        self._redis_client.delete(self._redis_key(user_id))
        logger.info(f"Session 缓存已清空 | user_id: {user_id}")

    def get_user_count(self) -> int:
        """评估活跃用户：扫描 Redis 中的 session keys"""
        # 注意: keys() 在极大键量下可能阻塞，但在中小型项目可做快速统计
        cache_keys = self._redis_client.keys("pdd_bot:session:*")
        return len(cache_keys)


# 全局单例
from config.settings import settings
session_manager = SessionManager(max_history=settings.max_history_length)
