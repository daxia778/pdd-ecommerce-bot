"""
用户 Session 管理器 - Redis 缓存 & SQLite 持久化版本。

策略：
  - Redis List 作为热缓存，支持多实例并发读写
  - 每次 add_message 同步写入 SQLite（messages 表）
  - 冷启动时从 DB 加载历史，回填到 Redis
  - P1-1: 引入 Redis，增强扩展性与并发安全
"""

from __future__ import annotations

import asyncio

from config.settings import settings
from src.utils.logger import logger


class SessionManager:
    """
    基于内存字典缓存的高亮 Session 管理器 (Fallback for Redis)。
    代替之前的 Redis。
    """

    def __init__(self, max_history: int = 10):
        self._max_history = max_history
        self._store = {}
        self._pause_store = {}
        # P1-1: 保护内存缓存的并发读写锁（asyncio 协程级）
        self._lock = asyncio.Lock()
        logger.info(f"SessionManager(Memory) 初始化 | 最大历史: {max_history}")

    def _redis_key(self, user_id: str) -> str:
        return f"pdd_bot:session:{user_id}"

    def _redis_pause_key(self, user_id: str) -> str:
        return f"pdd_bot:pause:{user_id}"

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
        """P1-1: 异步接口，加锁后写入内存和 SQLite"""
        async with self._lock:
            self._write_to_memory(user_id, role, content)
        # SQLite 写操作在锁外执行（同步阻塞操作，不影响协程调度）
        if db is not None:
            self._persist_to_db(user_id, role, content, db, platform)

    def add_message_sync(
        self,
        user_id: str,
        role: str,
        content: str,
        db=None,
        platform: str = "test",
        response_time_ms: int | None = None,
    ) -> None:
        """
        同步接口（从同步上下文调用，如 webhook 处理流程中）。
        P1-1: 内存写操作不能在同步函数中用 asyncio.Lock，使用独立的同步写方法。
        P2-2: 新增 response_time_ms 参数透传到 DB 层，采集 AI 回复耐时。
        """
        self._write_to_memory(user_id, role, content)
        if db is not None:
            self._persist_to_db(user_id, role, content, db, platform, response_time_ms=response_time_ms)

    def _write_to_memory(self, user_id: str, role: str, content: str) -> None:
        """内存写操作的原子单元（供 async/sync 接口共同调用）"""
        key = self._redis_key(user_id)
        msg = {"role": role, "content": content}
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(msg)
        self._store[key] = self._store[key][-self._max_history :]
        logger.debug(f"Session 更新 | user_id: {user_id} | 缓存至 Memory")

    def _persist_to_db(
        self, user_id: str, role: str, content: str, db, platform: str, response_time_ms: int | None = None
    ) -> None:
        """SQLite 持久化（同步，可在锁外执行）"""
        try:
            from src.services.db_service import save_message_and_upsert_session

            save_message_and_upsert_session(
                db,
                user_id=user_id,
                role=role,
                content=content,
                platform=platform,
                response_time_ms=response_time_ms,
            )
        except Exception as e:
            logger.error(f"Session 写库失败 | user_id: {user_id} | {e}")

    # ------------------------------------------------------------------
    # 读操作 — Memory 优先，未命中从 DB 加载（同步版本，向后兼容）
    # ------------------------------------------------------------------

    def get_history(self, user_id: str, db=None) -> list[dict]:
        """同步读取用户对话历史（返回副本防止外部修改污染缓存）"""
        key = self._redis_key(user_id)
        if key in self._store:
            return list(self._store[key])
        if db is not None:
            return self._load_from_db(user_id, db)
        return []

    def _load_from_db(self, user_id: str, db) -> list[dict]:
        """首屏冷启动：从 SQLite 加载历史消息到 Memory 缓存"""
        try:
            from src.services.db_service import get_messages

            msgs = get_messages(db, user_id=user_id, limit=self._max_history)
            if not msgs:
                return []

            history = [{"role": m.role, "content": m.content} for m in msgs]
            key = self._redis_key(user_id)
            self._store[key] = history
            logger.info(f"Session 从DB加载并回填缓存 | user_id: {user_id} | 条数: {len(history)}")
            return history
        except Exception as e:
            logger.error(f"Session 从DB加载失败 | user_id: {user_id} | {e}")
            return []

    # ------------------------------------------------------------------
    # P0-Fix-2: 异步安全接口 — DB 操作卸载到线程池
    #   FastAPI async 路由中必须使用这些方法，避免同步 SQLAlchemy
    #   阻塞 asyncio 主事件循环导致并发请求被挂起。
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
        """异步安全写入：内存写同步完成，DB 写卸载到线程池。"""
        self._write_to_memory(user_id, role, content)
        if db is not None:
            from src.models.database import run_in_db_thread

            await run_in_db_thread(
                self._persist_to_db,
                user_id,
                role,
                content,
                db,
                platform,
                response_time_ms=response_time_ms,
            )

    async def get_history_async_safe(self, user_id: str, db=None) -> list[dict]:
        """异步安全读取：内存命中直接返回，DB 穿透时卸载到线程池。"""
        key = self._redis_key(user_id)
        if key in self._store:
            return list(self._store[key])
        if db is not None:
            from src.models.database import run_in_db_thread

            return await run_in_db_thread(self._load_from_db, user_id, db)
        return []

    async def is_ai_paused_async_safe(self, user_id: str, db=None) -> bool:
        """异步安全检查 AI 暂停状态。"""
        pause_key = self._redis_pause_key(user_id)
        if pause_key in self._pause_store:
            return self._pause_store[pause_key]
        if db is not None:
            from src.models.database import run_in_db_thread

            def _check_paused():
                from src.models.database import Session as SessionModel

                session_rec = db.query(SessionModel).filter_by(user_id=user_id).first()
                is_paused = session_rec.is_ai_paused if session_rec else False
                self._pause_store[pause_key] = is_paused
                return is_paused

            return await run_in_db_thread(_check_paused)
        return False

    # ------------------------------------------------------------------
    # 管理操作
    # ------------------------------------------------------------------

    def clear_session(self, user_id: str) -> None:
        """从 Memory 清空指定用户的缓存"""
        key = self._redis_key(user_id)
        if key in self._store:
            del self._store[key]
        logger.info(f"Session 缓存已清空 | user_id: {user_id}")

    def get_user_count(self) -> int:
        """评估活跃用户：Memory dictionary key counts"""
        return len(self._store)

    # ------------------------------------------------------------------
    # AI 暂停控制 (L2 Shadow Chat)
    # ------------------------------------------------------------------

    def is_ai_paused(self, user_id: str, db=None) -> bool:
        """检查该用户的 AI 是否已被人工暂停"""
        pause_key = self._redis_pause_key(user_id)

        # 先查 Memory 缓存
        if pause_key in self._pause_store:
            return self._pause_store[pause_key]

        # 未命中缓存，查 DB
        if db is not None:
            from src.models.database import Session as SessionModel

            session_rec = db.query(SessionModel).filter_by(user_id=user_id).first()
            is_paused = session_rec.is_ai_paused if session_rec else False

            # 回填 Memory
            self._pause_store[pause_key] = is_paused
            return is_paused

        return False

    def set_ai_paused(self, user_id: str, is_paused: bool, db=None) -> None:
        """设置 AI 暂停状态（同步缓存和数据库）"""
        # 1. 更新 Memory 缓存
        pause_key = self._redis_pause_key(user_id)
        self._pause_store[pause_key] = is_paused

        # 2. 同步 DB
        if db is not None:
            try:
                from src.models.database import Session as SessionModel

                session_rec = db.query(SessionModel).filter_by(user_id=user_id).first()
                if session_rec:
                    session_rec.is_ai_paused = is_paused
                    db.commit()
                    logger.info(f"AI 暂停状态已同步至DB | user_id: {user_id} | paused: {is_paused}")
            except Exception as e:
                logger.error(f"同步 AI 暂停状态到 DB 失败 | {e}")


# 全局单例

session_manager = SessionManager(max_history=settings.max_history_length)
