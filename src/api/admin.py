"""
管理员 API 路由 - 提供管理后台所需的所有 REST 接口。
访问：GET /admin → 管理后台 HTML 页面

升级记录状态流转：
  pending → claimed（接单）→ resolved（完成）

P1-5: list_escalations 支持 claimed 状态 Tab，返回 claimed_at / operator_name
"""
from typing import Optional

from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os

from src.models.database import get_db, Session as ChatSession, Escalation
from src.services import db_service
from src.utils.logger import logger
from src.utils.auth import verify_admin
from src.core.rag_engine import get_rag_engine

# 依赖注入保护整个 router 的 API 接口
router = APIRouter(dependencies=[Depends(verify_admin)])


# ===== Pydantic 模型 =====

class ResolveRequest(BaseModel):
    operator_note: str = ""

class ClaimRequest(BaseModel):
    operator_name: str = "人工客服"

class EscalationItemResponse(BaseModel):
    id: int
    user_id: str
    trigger_keyword: str
    original_message: str
    status: str
    created_at: str

class KnowledgeItem(BaseModel):
    id: Optional[str] = None
    content: str
    source: Optional[str] = "admin_ui"


# ===== 路由: 知识库管理 =====
@router.get("/api/admin/knowledge", summary="获取知识库列表")
async def get_knowledge_list():
    try:
        rag_engine = get_rag_engine()
        data = rag_engine.get_all_documents()
        docs = []
        if data and "ids" in data:
            for i in range(len(data["ids"])):
                docs.append({
                    "id": data["ids"][i],
                    "content": data["documents"][i] if "documents" in data else "",
                    "metadata": data["metadatas"][i] if "metadatas" in data else {}
                })
        return {"status": "success", "data": docs}
    except Exception as e:
        logger.error(f"获取知识库异常: {e}")
        raise HTTPException(status_code=500, detail="获取知识库异常")

@router.post("/api/admin/knowledge", summary="添加新知识")
async def add_knowledge(item: KnowledgeItem):
    try:
        rag_engine = get_rag_engine()
        if item.id:
             rag_engine._collection.add(
                ids=[item.id],
                documents=[item.content],
                metadatas=[{"source": item.source}]
             )
             doc_id = item.id
        else:
             doc_id = rag_engine.add_document(content=item.content, metadata={"source": item.source})
             
        return {"status": "success", "id": doc_id}
    except Exception as e:
        logger.error(f"添加知识异常: {e}")
        raise HTTPException(status_code=500, detail="添加知识异常")

@router.delete("/api/admin/knowledge/{doc_id}", summary="删除特定知识")
async def delete_knowledge(doc_id: str):
    rag_engine = get_rag_engine()
    success = rag_engine.delete_document(doc_id)
    if success:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="删除知识失败,可能ID不存在")

# ===== HTML 页面 =====

@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_page():
    """提供管理后台 HTML 页面"""
    try:
        with open("templates/admin.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>管理后台模板未找到</h1>", status_code=404)


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


# ===== 升级/人工干预池管理 =====

@router.get("/api/admin/escalations", summary="获取升级记录列表")
def list_escalations(
    status: Optional[str] = None,
    reason: Optional[str] = None,
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
    esc = db_service.claim_escalation(
        db, escalation_id=escalation_id, operator_name=body.operator_name
    )
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
    会话状态同步恢复为 active。
    """
    esc = db_service.resolve_escalation(
        db, escalation_id=escalation_id, operator_note=body.operator_note
    )
    if not esc:
        raise HTTPException(status_code=404, detail="升级记录不存在或已完结")
    logger.info(f"升级已处理 | id: {escalation_id} | note: {body.operator_note}")
    return {"success": True, "id": escalation_id, "status": "resolved"}
