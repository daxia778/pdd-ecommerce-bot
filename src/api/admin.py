"""
管理员 API 路由 - 提供管理后台所需的所有 REST 接口。
访问：GET /admin → 管理后台 HTML 页面

升级记录状态流转：
  pending → claimed（接单）→ resolved（完成）

P1-5: list_escalations 支持 claimed 状态 Tab，返回 claimed_at / operator_name
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.settings import settings
from src.api.websocket_manager import manager as ws_manager
from src.core.rag_engine import get_rag_engine
from src.core.session_manager import session_manager
from src.models.database import get_db
from src.services import db_service
from src.utils.auth import create_access_token, verify_admin, verify_password
from src.utils.logger import logger

# 依赖注入保护整个 router 的 API 接口（除 /login 外，由于要兼容现有代码，我们只在需要的端点加或独立一个 Auth router）
# 为了兼容前端，我们先单独提供一个不需要 verify_admin 依赖的 login router
auth_router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@auth_router.post("/login", tags=["Auth"])
async def login(req: LoginRequest):
    stored_password = getattr(settings, "admin_password_hash", None) or settings.admin_password
    if verify_password(req.password, stored_password) and req.username == settings.admin_username:
        access_token = create_access_token(data={"sub": req.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
    )


router = APIRouter(dependencies=[Depends(verify_admin)])

# ===== Pydantic 模型 =====


class ResolveRequest(BaseModel):
    operator_note: str = ""


class ClaimRequest(BaseModel):
    operator_name: str = "人工客服"


class PauseRequest(BaseModel):
    paused: bool | None = None  # None = toggle, True = pause, False = resume


class EscalationItemResponse(BaseModel):
    id: int
    user_id: str
    trigger_keyword: str
    original_message: str
    status: str
    created_at: str


class KnowledgeItem(BaseModel):
    id: str | None = None
    content: str
    source: str | None = "admin_ui"


# ===== 路由: 知识库管理 =====
@router.get("/api/admin/knowledge", summary="获取知识库列表")
async def get_knowledge_list(include_deleted: bool = False):
    try:
        rag_engine = get_rag_engine()
        # P2-3: 传递 include_deleted 参数过滤已软删除项目
        data = rag_engine.get_all_documents(include_deleted=include_deleted)
        docs = []
        if data and "ids" in data:
            for i in range(len(data["ids"])):
                docs.append(
                    {
                        "id": data["ids"][i],
                        "content": data["documents"][i] if "documents" in data else "",
                        "metadata": data["metadatas"][i] if "metadatas" in data else {},
                    }
                )
        return {"status": "success", "data": docs}
    except Exception as e:
        logger.error(f"获取知识库异常: {e}")
        raise HTTPException(status_code=500, detail="获取知识库异常") from e


@router.post("/api/admin/knowledge", summary="添加新知识")
async def add_knowledge(item: KnowledgeItem):
    """添加知识片段，统一走 add_document() 确保向量化正确入库"""
    try:
        rag_engine = get_rag_engine()
        # 始终使用公共接口，确保 embedding 被正确计算后再存入
        doc_id = rag_engine.add_document(content=item.content, metadata={"source": item.source or "admin_ui"})
        return {"status": "success", "id": doc_id}
    except Exception as e:
        logger.error(f"添加知识异常: {e}")
        raise HTTPException(status_code=500, detail="添加知识异常") from e


@router.delete("/api/admin/knowledge/{doc_id}", summary="删除特定知识")
async def delete_knowledge(doc_id: str):
    rag_engine = get_rag_engine()
    # P2-3: 改为使用软删除，以免找不回来
    success = rag_engine.soft_delete_document(doc_id)
    if success:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="删除知识失败,可能ID不存在")


# ===== 统计接口 =====


@router.get("/api/admin/stats", summary="获取仪表盘统计数据")
def get_stats(db: Session = Depends(get_db)):
    """返回仪表盘核心指标"""
    return db_service.get_stats(db)


# ===== 会话管理 =====


@router.get("/api/admin/sessions", summary="获取会话列表")
def list_sessions(limit: int = 50, db: Session = Depends(get_db)):
    """获取最近的会话列表，含最新消息摘要"""
    return db_service.get_all_sessions_with_latest(db, limit=limit)


@router.get("/api/admin/sessions/{user_id}/messages", summary="获取会话详细消息")
def get_session_messages(user_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """获取指定用户的完整对话记录"""
    messages = db_service.get_messages(db, user_id=user_id, limit=limit)
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.strftime("%H:%M:%S"),
            "platform": m.platform,
        }
        for m in messages
    ]


@router.post("/api/admin/sessions/{user_id}/pause", summary="切换 AI 暂停状态（Shadow Chat）")
async def toggle_ai_pause(
    user_id: str,
    body: PauseRequest = PauseRequest(),
    db: Session = Depends(get_db),
):
    """
    为特定会话切换 AI 自动回复的暂停状态。
    - 传 paused=true  → 暂停 AI，进入人工接管模式
    - 传 paused=false → 恢复 AI 自动回复
    - 不传 paused     → 自动切换（toggle）
    """
    if body.paused is None:
        # 自动切换
        current_state = session_manager.is_ai_paused(user_id, db=db)
        new_state = not current_state
    else:
        new_state = body.paused

    session_manager.set_ai_paused(user_id, new_state, db=db)
    action = "paused" if new_state else "resumed"
    logger.info(f"AI 暂停状态已更新 | user_id: {user_id} | 新状态: {action}")

    # 广播 WebSocket 通知
    asyncio.create_task(
        ws_manager.broadcast(
            {
                "event": "ai_pause_toggled",
                "user_id": user_id,
                "is_paused": new_state,
            }
        )
    )

    return {"success": True, "user_id": user_id, "is_paused": new_state, "action": action}


class SendMessageRequest(BaseModel):
    content: str
    operator_name: str = "人工客服"


@router.post("/api/admin/sessions/{user_id}/send_message", summary="人工客服手动发送消息（Shadow Chat）")
async def send_manual_message(
    user_id: str,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
):
    """
    由管理员/人工客服直接向买家发送消息。
    - 消息通过 PDD 开放平台 API 推送给买家
    - 同时写入 SQLite 保留记录（platform=manual）
    - 广播 WebSocket 通知前端实时更新对话窗口
    """
    if not body.content or not body.content.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    from src.services.db_service import save_message_and_upsert_session
    from src.services.pdd_api_client import pdd_api_client

    # 1. 调用 PDD API 发送给买家（失败不阻断流程，仍记录）
    send_ok = False
    try:
        send_ok = await pdd_api_client.send_customer_message(
            mall_id="default_shop", buyer_id=user_id, content=body.content
        )
    except Exception as e:
        logger.warning(f"人工消息 PDD 推送失败（已记录到 DB）| user_id: {user_id} | {e}")

    # 2. 写入 SQLite，标记 platform=manual 区分 AI 自动回复
    try:
        save_message_and_upsert_session(
            db,
            user_id=user_id,
            role="assistant",
            content=f"[{body.operator_name}] {body.content}",
            platform="manual",
        )
    except Exception as e:
        logger.error(f"人工消息写入 DB 失败 | {e}")

    logger.info(f"人工消息已发送 | user_id: {user_id} | operator: {body.operator_name} | pdd_ok: {send_ok}")

    # 3. 广播 WebSocket 通知，前端立即刷新对话记录
    asyncio.create_task(
        ws_manager.broadcast(
            {
                "event": "manual_message_sent",
                "user_id": user_id,
                "content": body.content,
                "operator_name": body.operator_name,
            }
        )
    )

    return {
        "success": True,
        "user_id": user_id,
        "pdd_push_ok": send_ok,
        "message": body.content,
    }


# ===== 升级/人工干预池管理 =====


@router.get("/api/admin/escalations", summary="获取升级记录列表")
def list_escalations(
    status: str | None = None,
    reason: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    获取升级记录列表。
    - status: pending | claimed | resolved（不传则全部）
    - reason: urgent | bargain | complaint | large_order | offline | other
    """
    escalations = db_service.get_escalations(db, status=status, reason=reason, limit=limit)
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "platform": e.platform,
            "trigger_message": e.trigger_message,
            "ai_reply": e.ai_reply,
            "reason": e.reason,
            "status": e.status,
            "created_at": e.created_at.strftime("%m-%d %H:%M"),
            # P1-5/P0-5: 使用正确的字段
            "claimed_at": e.claimed_at.strftime("%m-%d %H:%M") if e.claimed_at else None,
            "resolved_at": e.resolved_at.strftime("%m-%d %H:%M") if e.resolved_at else None,
            "operator_note": e.operator_note,
            "operator_name": e.operator_name,
        }
        for e in escalations
    ]


@router.post("/api/admin/escalations/{escalation_id}/claim", summary="接单：认领升级任务")
def claim_escalation(
    escalation_id: int,
    body: ClaimRequest,
    db: Session = Depends(get_db),
):
    """
    将升级记录状态从 pending → claimed（接单），
    表示人工客服已确认并开始处理此客户。
    """
    esc = db_service.claim_escalation(db, escalation_id=escalation_id, operator_name=body.operator_name)
    if not esc:
        raise HTTPException(status_code=404, detail="升级记录不存在或已被接单")
    logger.info(f"接单成功 | id: {escalation_id} | operator: {body.operator_name}")
    return {"success": True, "id": escalation_id, "status": "claimed"}


@router.post("/api/admin/escalations/{escalation_id}/resolve", summary="完结：标记升级已处理")
def resolve_escalation(
    escalation_id: int,
    body: ResolveRequest,
    db: Session = Depends(get_db),
):
    """
    将升级记录状态流转到 resolved（完成），
    可从 pending 或 claimed 状态流转。
    会话状态同步恢复为 active，并自动恢复 AI 自动回复。
    """
    esc = db_service.resolve_escalation(db, escalation_id=escalation_id, operator_note=body.operator_note)
    if not esc:
        raise HTTPException(status_code=404, detail="升级记录不存在或已完结")

    # 恢复 AI 自动回复
    session_manager.set_ai_paused(esc.user_id, False, db=db)

    logger.info(f"升级已处理 | id: {escalation_id} | note: {body.operator_note}")

    # 广播 WebSocket 通知
    asyncio.create_task(
        ws_manager.broadcast(
            {
                "event": "escalation_resolved",
                "escalation_id": escalation_id,
                "user_id": esc.user_id,
            }
        )
    )

    return {"success": True, "id": escalation_id, "status": "resolved"}
