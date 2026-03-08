"""
用户 Session 管理器 - Redis 缓存 & SQLite 持久化版本。

策略：
  - Redis List 作为热缓存，支持多实例并发读写
  - 每次 add_message_async_safe 同步写入 SQLite（messages 表）(卸载到线程池)
  - 冷启动时从 DB 加载历史，回填到 Redis
  - 完全异步化设计，与 FastAPI 高度契合
"""

from __future__ import annotations

import asyncio
import contextlib
import json

from config.settings import settings
from src.services.redis_client import redis_client
from src.utils.logger import logger


class SessionManager:
    """
    基于 Redis 列表缓存的高可用 Session 管理器。
    """

    def __init__(self, max_history: int = 10):
        self._max_history = max_history
        logger.info(f"SessionManager(Redis版) 初始化 | 最大历史: {max_history}")

    def _redis_key(self, user_id: str) -> str:
        return f"pdd_bot:session:{user_id}"

    def _redis_pause_key(self, user_id: str) -> str:
        return f"pdd_bot:pause:{user_id}"

    # ------------------------------------------------------------------
    # 核心读写操作 - 完全异步
    # ------------------------------------------------------------------

    async def add_message_async_safe(
        self,
        user_id: str,
        role: str,
        content: str,
        db=None,
        platform: str = "test",
        response_time_ms: int | None = None,
    ) -> None:
        """异步安全写入：写入 Redis，并且将 DB 持久化卸载到线程池。"""
        # 1. 写入 Redis 热缓存
        if redis_client.is_available:
            key = self._redis_key(user_id)
            msg_str = json.dumps({"role": role, "content": content}, ensure_ascii=False)
            try:
                pipe = redis_client.client.pipeline()
                pipe.rpush(key, msg_str)
                pipe.ltrim(key, -self._max_history, -1)
                pipe.expire(key, 86400 * 7)  # 保存 7 天
                await pipe.execute()
            except Exception as e:
                logger.error(f"Session Redis 写入失败 | user_id: {user_id} | {e}")
        else:
            logger.warning("SessionManager: Redis 不可用，跳过内存缓存")

        # 2. 写入 SQLite (卸载到线程池)
        if db is not None:
            from src.models.database import run_in_db_thread
            from src.services.db_service import save_message_and_upsert_session

            def _persist():
                save_message_and_upsert_session(
                    db,
                    user_id=user_id,
                    role=role,
                    content=content,
                    platform=platform,
                    response_time_ms=response_time_ms,
                )

            await run_in_db_thread(_persist)

    async def get_history_async_safe(self, user_id: str, db=None) -> list[dict]:
        """异步安全读取：优先 Redis，未命中穿透到 DB (卸载到线程池) 并回填。"""
        if redis_client.is_available:
            key = self._redis_key(user_id)
            try:
                raw_msgs = await redis_client.client.lrange(key, 0, -1)
                if raw_msgs:
                    history = [json.loads(m) for m in raw_msgs]
                    return history
            except Exception as e:
                logger.error(f"Session Redis 读取失败 | {e}")

        # 未命中 Redis，从 DB 加载
        if db is not None:
            from src.models.database import run_in_db_thread

            def _load_from_db() -> list[dict]:
                from src.services.db_service import get_messages

                msgs = get_messages(db, user_id=user_id, limit=self._max_history)
                return [{"role": m.role, "content": m.content} for m in msgs] if msgs else []

            history = await run_in_db_thread(_load_from_db)

            # 回填 Redis
            if history and redis_client.is_available:
                try:
                    pipe = redis_client.client.pipeline()
                    # 防止并发回填造成多份数据，先清空
                    pipe.delete(key)
                    msg_strs = [json.dumps(msg, ensure_ascii=False) for msg in history]
                    pipe.rpush(key, *msg_strs)
                    pipe.expire(key, 86400 * 7)
                    await pipe.execute()
                    logger.info(f"Session 回填 Redis 成功 | user_id: {user_id}")
                except Exception as e:
                    logger.error(f"Session 回填 Redis 失败 | {e}")
            return history

        return []

    # ------------------------------------------------------------------
    # 管理操作
    # ------------------------------------------------------------------

    def clear_session(self, user_id: str) -> None:
        """从 Redis 清空指定用户的缓存。如果是异步调用，应当考虑封装。这里为了兼容保留同步方法，采用 create_task。"""
        if redis_client.is_available:
            key = self._redis_key(user_id)
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(redis_client.delete(key))
            except RuntimeError:
                # Event loop not running (e.g. tests)
                pass

    # ------------------------------------------------------------------
    # AI 暂停控制
    # ------------------------------------------------------------------

    async def is_ai_paused_async_safe(self, user_id: str, db=None) -> bool:
        """异步安全检查 AI 暂停状态。"""
        if redis_client.is_available:
            pause_key = self._redis_pause_key(user_id)
            try:
                val = await redis_client.get(pause_key)
                if val is not None:
                    return val.lower() == "true"
            except Exception as e:
                logger.error(f"Redis is_ai_paused 读取失败 | {e}")

        if db is not None:
            from src.models.database import run_in_db_thread

            def _check_paused():
                from src.models.database import Session as SessionModel

                session_rec = db.query(SessionModel).filter_by(user_id=user_id).first()
                return session_rec.is_ai_paused if session_rec else False

            is_paused = await run_in_db_thread(_check_paused)

            # 回填 Redis
            if redis_client.is_available:
                pause_key = self._redis_pause_key(user_id)
                with contextlib.suppress(Exception):
                    await redis_client.set(pause_key, str(is_paused).lower(), ex=86400)
            return is_paused

        return False

    async def set_ai_paused_async_safe(self, user_id: str, is_paused: bool, db=None) -> None:
        """异步安全设置 AI 暂停状态。"""
        if redis_client.is_available:
            pause_key = self._redis_pause_key(user_id)
            try:
                await redis_client.set(pause_key, str(is_paused).lower(), ex=86400)
            except Exception as e:
                logger.error(f"Redis set_ai_paused 失败 | {e}")

        # 同步 DB
        if db is not None:
            from src.models.database import run_in_db_thread

            def _sync_db():
                from src.models.database import Session as SessionModel

                session_rec = db.query(SessionModel).filter_by(user_id=user_id).first()
                if session_rec:
                    session_rec.is_ai_paused = is_paused
                    db.commit()

            await run_in_db_thread(_sync_db)


# 全局单例
session_manager = SessionManager(max_history=settings.max_history_length)
