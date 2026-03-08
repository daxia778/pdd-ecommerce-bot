"""
数据库 CRUD 服务 - 封装所有数据库操作。
供 webhook、session_manager、admin API 调用。

升级记录状态流转：
  pending  →  claimed（客服接单）
  claimed  →  resolved（处理完毕）
  pending  →  resolved（跳过接单直接关闭）

P0-3 修复: save_message_and_upsert_session 合并消息写入与会话 upsert 为单次事务，
           修复原来双重调用导致 message_count 少计一次的 Bug
P0-5 修复: claim_escalation 使用新增的 claimed_at 字段，不再污染 resolved_at
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.websocket_manager import manager as ws_manager
from src.models.database import Escalation, Message
from src.models.database import Session as SessionModel
from src.models.enums import SessionStatus
from src.utils.logger import logger

# ===== 消息操作 =====


def save_message(db: Session, user_id: str, role: str, content: str, platform: str = "test") -> Message:
    """保存一条消息到数据库（不更新 session，单独使用时调用）"""
    msg = Message(user_id=user_id, role=role, content=content, platform=platform)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def save_message_and_upsert_session(
    db: Session,
    user_id: str,
    role: str,
    content: str,
    platform: str = "test",
    response_time_ms: int | None = None,
) -> Message:
    """
    P0-3/P1-3: 在单次事务中同时完成：
    1. 写入消息记录
    2. Upsert Session（首次创建或更新 updated_at + message_count）

    P2-2: 新增 response_time_ms 参数，将 AI 回复实际耗时落库，供 Dashboard 统计展示
    """
    # 写消息（AI 回复时附带耗时）
    msg = Message(
        user_id=user_id,
        role=role,
        content=content,
        platform=platform,
        response_time_ms=response_time_ms,
    )
    db.add(msg)

    # Upsert Session
    session = db.query(SessionModel).filter(SessionModel.user_id == user_id).first()
    if not session:
        session = SessionModel(
            user_id=user_id,
            platform=platform,
            message_count=1,
        )
        db.add(session)
    else:
        # P0-SEC: 使用 DB 原子自增操作，避免并发下 Lost Update（多个请求读到相同旧值只+1）
        session.message_count = SessionModel.message_count + 1
        session.updated_at = datetime.now()

    db.commit()
    db.refresh(msg)
    return msg


def get_messages(db: Session, user_id: str, limit: int = 20) -> list[Message]:
    """获取用户的消息历史（按时间升序）"""
    return db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at.asc()).limit(limit).all()


def get_all_sessions_with_latest(db: Session, limit: int = 50) -> list[dict]:
    """获取所有会话的最新消息摘要，用于管理后台列表"""
    sessions = db.query(SessionModel).order_by(SessionModel.updated_at.desc()).limit(limit).all()
    result = []
    for s in sessions:
        last_msg = db.query(Message).filter(Message.user_id == s.user_id).order_by(Message.created_at.desc()).first()
        result.append(
            {
                "user_id": s.user_id,
                "platform": s.platform,
                "status": s.status,
                "message_count": s.message_count,
                "created_at": s.created_at.strftime("%m-%d %H:%M"),
                "updated_at": s.updated_at.strftime("%m-%d %H:%M"),
                "last_message": last_msg.content[:60] + "..."
                if last_msg and len(last_msg.content) > 60
                else (last_msg.content if last_msg else ""),
                "last_role": last_msg.role if last_msg else "",
            }
        )
    return result


def get_or_create_session(db: Session, user_id: str, platform: str = "test") -> SessionModel:
    """获取或创建会话元记录（向后兼容保留）"""
    session = db.query(SessionModel).filter(SessionModel.user_id == user_id).first()
    if not session:
        session = SessionModel(user_id=user_id, platform=platform)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def update_session(db: Session, user_id: str, status: str | None = None):
    """更新会话状态（不再自增 message_count，由 save_message_and_upsert_session 负责）"""
    session = db.query(SessionModel).filter(SessionModel.user_id == user_id).first()
    if session:
        session.updated_at = datetime.now()
        if status:
            session.status = status
        db.commit()


# ===== 升级操作 =====


def create_escalation(
    db: Session,
    user_id: str,
    trigger_message: str,
    ai_reply: str,
    reason: str = "other",
    platform: str = "test",
) -> Escalation:
    """创建一条升级记录"""
    esc = Escalation(
        user_id=user_id,
        platform=platform,
        trigger_message=trigger_message,
        ai_reply=ai_reply,
        reason=reason,
    )
    db.add(esc)
    db.commit()
    db.refresh(esc)
    logger.info(f"升级记录已创建 | user_id: {user_id} | reason: {reason}")

    # L2: 实时 WS 广播给后台大屏（仅在 async 上下文中有效，同步调用时静默跳过）
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            ws_manager.broadcast(
                {
                    "type": "new_escalation",
                    "data": {
                        "id": esc.id,
                        "user_id": esc.user_id,
                        "reason": esc.reason,
                        "trigger_message": esc.trigger_message[:50] + "..."
                        if len(esc.trigger_message) > 50
                        else esc.trigger_message,
                    },
                }
            )
        )
    except RuntimeError:
        # 无 running event loop（单元测试/同步 worker 场景），跳过广播
        pass

    return esc


def get_escalations(
    db: Session,
    status: str | None = None,
    limit: int = 50,
    reason: str | None = None,
) -> list[Escalation]:
    """获取升级记录列表（可按状态/原因过滤）"""
    q = db.query(Escalation)
    if status:
        q = q.filter(Escalation.status == status)
    if reason:
        q = q.filter(Escalation.reason == reason)
    return q.order_by(Escalation.created_at.desc()).limit(limit).all()


def get_escalation_by_id(db: Session, escalation_id: int) -> Escalation | None:
    """按 ID 获取升级记录"""
    return db.query(Escalation).filter(Escalation.id == escalation_id).first()


def claim_escalation(
    db: Session,
    escalation_id: int,
    operator_name: str = "人工客服",
) -> Escalation | None:
    """
    接单：将升级记录从 pending → claimed。
    P0-5: 使用独立的 claimed_at 字段记录接单时间，不再污染 resolved_at。
    """
    esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if esc and esc.status == "pending":
        esc.status = "claimed"
        esc.operator_name = operator_name
        esc.operator_note = f"[{operator_name}] 已接单，处理中..."
        # P0-5: 使用正确的 claimed_at 字段
        esc.claimed_at = datetime.now()
        db.commit()
        logger.info(f"升级已接单 | id: {escalation_id} | operator: {operator_name}")
    return esc


def resolve_escalation(
    db: Session,
    escalation_id: int,
    operator_note: str = "",
) -> Escalation | None:
    """标记升级为已处理（resolved），可从 pending 或 claimed 状态流转"""
    esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if esc and esc.status in ("pending", "claimed"):
        esc.status = "resolved"
        esc.resolved_at = datetime.now()  # 现在只记录真实的完成时间
        if operator_note:
            esc.operator_note = operator_note
        db.commit()
        # 同时把 session 状态恢复 active
        session = db.query(SessionModel).filter(SessionModel.user_id == esc.user_id).first()
        if session:
            session.status = SessionStatus.ACTIVE
            db.commit()
        logger.info(f"升级已处理 | id: {escalation_id}")
    return esc


def get_stats(db: Session) -> dict:
    """获取仪表盘统计数据，P1-4: 新增今日新增会话数与消息数"""
    from src.core.rag_engine import get_rag_engine

    today = date.today()

    total_sessions = db.query(SessionModel).count()
    active_sessions = db.query(SessionModel).filter(SessionModel.status == "active").count()
    escalated_sessions = db.query(SessionModel).filter(SessionModel.status == "escalated").count()
    pending_escalations = db.query(Escalation).filter(Escalation.status == "pending").count()
    claimed_escalations = db.query(Escalation).filter(Escalation.status == "claimed").count()
    resolved_escalations = db.query(Escalation).filter(Escalation.status == "resolved").count()
    total_messages = db.query(Message).count()

    # P1-4: 今日新增数据
    today_sessions = db.query(SessionModel).filter(func.date(SessionModel.created_at) == today).count()
    today_messages = db.query(Message).filter(func.date(Message.created_at) == today).count()

    rag = get_rag_engine()
    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "escalated_sessions": escalated_sessions,
        "pending_escalations": pending_escalations,
        "claimed_escalations": claimed_escalations,
        "resolved_escalations": resolved_escalations,
        "total_messages": total_messages,
        "knowledge_docs": rag.get_doc_count(),
        # P1-4: 今日统计
        "today_sessions": today_sessions,
        "today_messages": today_messages,
    }
