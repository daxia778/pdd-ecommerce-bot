from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from datetime import datetime
import os

from src.models.database import get_db, Session, Message, Escalation, Order
from src.services import db_service
from src.utils.auth import verify_admin

router = APIRouter(dependencies=[Depends(verify_admin)])

# 模板目录路径
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")

@router.get("/", response_class=HTMLResponse, summary="后台管理 Dashboard")
async def dashboard_page(request: Request):
    """返回看板前端 HTML 页面（直接读文件，绕过 Jinja2 解析以兼容 Vue.js {{ }} 语法）"""
    html_path = os.path.join(template_dir, "dashboard.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>dashboard.html 模板文件未找到</h1>", status_code=404)

@router.get("/api/dashboard/stats")
async def get_stats(db: DBSession = Depends(get_db)):
    """获取整体统计数据"""
    active_sessions = db.query(Session).filter(Session.status == "active").count()
    pending_escalations = db.query(Escalation).filter(Escalation.status == "pending").count()
    active_orders = db.query(Order).filter(Order.status.in_(["generating", "processing", "awaiting_review"])).count()
    
    return {
        "active_sessions": active_sessions,
        "pending_escalations": pending_escalations,
        "active_orders": active_orders
    }

@router.get("/api/dashboard/sessions")
async def get_sessions(db: DBSession = Depends(get_db)):
    """获取最近的会话列表"""
    sessions = db.query(Session).order_by(desc(Session.updated_at)).limit(20).all()
    return [{
        "id": s.id,
        "user_id": s.user_id,
        "platform": s.platform,
        "status": s.status,
        "message_count": s.message_count,
        "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M:%S") if s.updated_at else ""
    } for s in sessions]

@router.get("/api/dashboard/messages/{user_id}")
async def get_messages(user_id: str, db: DBSession = Depends(get_db)):
    """获取指定用户的历史消息"""
    messages = db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at).all()
    return [{
        "role": m.role,
        "content": m.content,
        "created_at": m.created_at.strftime("%H:%M:%S") if m.created_at else ""
    } for m in messages]

@router.get("/api/dashboard/escalations")
async def get_escalations(db: DBSession = Depends(get_db)):
    """获取需要人工处理的升级记录"""
    escalations = db.query(Escalation).filter(Escalation.status == "pending").order_by(desc(Escalation.created_at)).all()
    return [{
        "id": e.id,
        "user_id": e.user_id,
        "trigger_message": e.trigger_message,
        "ai_reply": e.ai_reply,
        "reason_label": e.reason,
        "created_at": e.created_at.strftime("%Y-%m-%d %H:%M:%S") if e.created_at else ""
    } for e in escalations]

@router.post("/api/dashboard/escalations/{esc_id}/resolve")
async def resolve_escalation(esc_id: int, db: DBSession = Depends(get_db)):
    """标记升级问题为已处理 (人工介入完成)"""
    esc = db.query(Escalation).filter(Escalation.id == esc_id).first()
    if esc:
        esc.status = "resolved"
        
        # 恢复会话状态为 active
        session = db.query(Session).filter(Session.user_id == esc.user_id).first()
        if session:
            session.status = "active"
            
        db.commit()
        return {"status": "success"}
    return {"status": "error", "msg": "Not found"}

@router.get("/api/dashboard/orders")
async def get_orders(db: DBSession = Depends(get_db)):
    """获取 PPT 生产流水线池子"""
    orders = db.query(Order).order_by(desc(Order.created_at)).limit(20).all()
    return [{
        "id": o.id,
        "order_sn": o.order_sn,
        "user_id": o.user_id,
        "status": o.status,
        "requirement": o.requirement_json,
        "file_url": o.file_url,
        "clean_file_url": o.clean_file_url,
        "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else ""
    } for o in orders]

@router.post("/api/dashboard/orders/{order_id}/approve")
async def approve_order(order_id: int, db: DBSession = Depends(get_db)):
    """人工批准发货"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "shipped"
        db.commit()
        # TODO: 实际调用 PDD API 发送文件给买家
        return {"status": "success"}
    return {"status": "error", "msg": "Not found"}
