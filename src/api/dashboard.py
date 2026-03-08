from __future__ import annotations

import os
from datetime import datetime, timedelta

import jwt
from async_lru import alru_cache
from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session as DBSession

from src.api.websocket_manager import manager
from src.models.database import Escalation, Message, Order, Session, get_db, run_in_db_thread
from src.models.enums import EscalationStatus, OrderStatus, SessionStatus
from src.services import db_service
from src.services.pdd_api_client import pdd_api_client
from src.utils.auth import JWT_ALGORITHM, JWT_SECRET_KEY, verify_admin

router = APIRouter(dependencies=[Depends(verify_admin)])
ws_router = APIRouter()
# Public router: serves Vue HTML shell — no auth (Vue handles login in-browser)
public_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """
    WebSocket 实时推送端点。
    连接时需在 query param 中携带有效的 JWT Token：
      ws://host/ws?token=<bearer_token>
    验证失败将以 1008 (Policy Violation) 关闭连接。
    """
    # ===== Token 鉴权 =====
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise jwt.InvalidTokenError("No sub claim")
    except jwt.PyJWTError as e:
        await websocket.close(code=1008, reason=f"Invalid token: {e}")
        return

    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃，等待服务端推送
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


# 模板目录路径
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")


@public_router.get("/", response_class=HTMLResponse, include_in_schema=False)
@public_router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
    """返回看板前端 HTML 页面（公开接口，Vue 负责前端登录流程）"""
    html_path = os.path.join(static_dir, "admin", "index.html")
    try:
        with open(html_path, encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>前端未构建，请先执行 npm run build</h1>", status_code=404)


@alru_cache(maxsize=1, ttl=5)
async def _get_stats_cached(db: DBSession):
    """P0.2: 统计防穿透微缓存 (TTL 5s) - 补充完整字段"""
    active_sessions = db.query(Session).filter(Session.status == SessionStatus.ACTIVE).count()
    pending_escalations = db.query(Escalation).filter(Escalation.status == EscalationStatus.PENDING).count()
    active_orders = (
        db.query(Order)
        .filter(Order.status.in_([OrderStatus.GENERATING, OrderStatus.PROCESSING, OrderStatus.AWAITING_REVIEW]))
        .count()
    )

    # 1. 订单统计
    shipped_orders = db.query(Order).filter(Order.status == OrderStatus.SHIPPED).count()
    total_orders = db.query(Order).count()  # 历史订单总数，供看板展示

    # 2. 成单转化率：已交付订单 / 总会话数（取最大值避免除零）
    total_sessions = db.query(Session).count()
    if total_sessions > 0:
        conversion_rate = f"{min(shipped_orders / total_sessions * 100, 100):.1f}%"
    else:
        conversion_rate = "0.0%"

    # 3. 预估营收：已交付订单 × 平均客单价 ¥900（无价格字段时的合理 fallback）
    avg_order_value = 900
    total_revenue = f"¥ {shipped_orders * avg_order_value:,}"

    # 4. AI 智能解决率：未升级 / 总活跃会话
    total_escalations = db.query(Escalation).count()
    if total_sessions > 0:
        escalation_rate = total_escalations / total_sessions
        satisfaction_rate = f"{max((1 - escalation_rate) * 100, 0):.1f}%"
    else:
        satisfaction_rate = "98.5%"  # 无数据时显示示例值

    # 5. P2-2: 平均响应耗时 — 从 Message.response_time_ms 读取真实数据
    #    仅统计有耗时记录的 AI 回复消息（role=assistant），确保准确性
    avg_ms_row = (
        db.query(func.avg(Message.response_time_ms))
        .filter(Message.role == "assistant", Message.response_time_ms.is_not(None))
        .scalar()
    )
    if avg_ms_row and avg_ms_row > 0:
        avg_response_time = f"{avg_ms_row / 1000:.1f}s"
    else:
        avg_response_time = "暂无数据"

    return {
        "active_sessions": active_sessions,
        "pending_escalations": pending_escalations,
        "active_orders": active_orders,
        "total_orders": total_orders,
        "conversion_rate": conversion_rate,
        "total_revenue": total_revenue,
        "satisfaction_rate": satisfaction_rate,
        "avg_response_time": avg_response_time,
    }


@router.get("/api/dashboard/stats")
async def get_stats(db: DBSession = Depends(get_db)):
    """获取整体统计数据"""
    return await _get_stats_cached(db)


@router.get("/api/dashboard/stats/hourly")
async def get_stats_hourly(db: DBSession = Depends(get_db)):
    """获取当天每小时的消息量（真实时间序列数据，替换假 ECharts 数据）"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    rows = (
        db.query(func.strftime("%H", Message.created_at).label("hour"), func.count(Message.id).label("count"))
        .filter(Message.created_at >= today, Message.created_at < tomorrow)
        .group_by("hour")
        .all()
    )

    # 将数据增展为 24 个小时的完整点
    hour_map = {row.hour: row.count for row in rows}
    hours = [f"{h:02d}:00" for h in range(24)]
    counts = [hour_map.get(f"{h:02d}", 0) for h in range(24)]

    return {"hours": hours, "counts": counts}


@router.get("/api/dashboard/sessions")
async def get_sessions(db: DBSession = Depends(get_db)):
    """获取最近的会话列表"""
    sessions = db.query(Session).order_by(desc(Session.updated_at)).limit(20).all()
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "platform": s.platform,
            "status": s.status,
            "message_count": s.message_count,
            "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M:%S") if s.updated_at else "",
        }
        for s in sessions
    ]


@router.get("/api/dashboard/messages/{user_id}")
async def get_messages(user_id: str, db: DBSession = Depends(get_db)):
    """获取指定用户的历史消息"""
    messages = db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at).all()
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at.strftime("%H:%M:%S") if m.created_at else ""}
        for m in messages
    ]


@router.get("/api/dashboard/escalations")
async def get_escalations(db: DBSession = Depends(get_db)):
    """获取需要人工处理的升级记录"""
    escalations = (
        db.query(Escalation)
        .filter(Escalation.status == EscalationStatus.PENDING)
        .order_by(desc(Escalation.created_at))
        .all()
    )
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "trigger_message": e.trigger_message,
            "ai_reply": e.ai_reply,
            "reason_label": e.reason,
            "created_at": e.created_at.strftime("%Y-%m-%d %H:%M:%S") if e.created_at else "",
        }
        for e in escalations
    ]


@router.post("/api/dashboard/escalations/{esc_id}/resolve")
async def resolve_escalation(esc_id: int, db: DBSession = Depends(get_db)):
    """
    标记升级问题为已处理。
    使用 db_service 确保：状态流转 + 会话状态恢复 + resolved_at 记录均正确完成
    """
    esc = db_service.resolve_escalation(db, escalation_id=esc_id)
    if esc:
        await manager.broadcast({"event": "update", "action": "resolve_escalation"})
        return {"status": "success"}
    return {"status": "error", "msg": "Not found or already resolved"}


@router.get("/api/dashboard/orders")
async def get_orders(status: str | None = None, show_all: bool = False, db: DBSession = Depends(get_db)):
    """获取 PPT 工单列表。默认只返回未交付的工单（req_fixed / processing）。"""
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    elif not show_all:
        q = q.filter(Order.status.in_([OrderStatus.REQ_FIXED, OrderStatus.PROCESSING, OrderStatus.AWAITING_REVIEW]))
    orders = q.order_by(desc(Order.created_at)).limit(50).all()
    return [
        {
            "id": o.id,
            "order_sn": o.order_sn,
            "user_id": o.user_id,
            "status": o.status,
            "requirement": o.requirement_json,
            "file_url": o.file_url,
            "clean_file_url": o.clean_file_url,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else "",
        }
        for o in orders
    ]


@router.post("/api/dashboard/orders/{order_id}/approve")
async def approve_order(order_id: int, db: DBSession = Depends(get_db)):
    """人工批准发货（原有接口，兼容保留）"""

    # P0-Root-Cause-Sweep: 将同步 DB 操作卸载到线程池
    def _approve(db_session: DBSession):
        order = db_session.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = OrderStatus.SHIPPED
            db_session.commit()
        return order

    order = await run_in_db_thread(_approve, db)
    if order:
        mall_id = getattr(order, "mall_id", "default_mall_id")
        await pdd_api_client.send_file_message(mall_id, order.user_id, order.clean_file_url)
        await manager.broadcast({"event": "update", "action": "approve_order"})
        return {"status": "success"}
    return {"status": "error", "msg": "Not found"}


@router.post("/api/dashboard/orders/{order_id}/claim")
async def claim_order(order_id: int, db: DBSession = Depends(get_db)):
    """人工接单：将工单状态从 req_fixed → processing"""

    # P0-Root-Cause-Sweep: 将同步 DB 操作卸载到线程池
    def _claim(db_session: DBSession):
        order = db_session.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None, "工单不存在"
        if order.status != OrderStatus.REQ_FIXED:
            return None, f"当前状态 [{order.status}] 不可接单"
        order.status = OrderStatus.PROCESSING
        db_session.commit()
        return order, None

    order, err = await run_in_db_thread(_claim, db)
    if err:
        return {"status": "error", "msg": err}
    await manager.broadcast({"event": "update", "action": "order_claimed", "order_id": order_id})
    return {"status": "success", "order_sn": order.order_sn}


@router.post("/api/dashboard/orders/{order_id}/deliver")
async def deliver_order(order_id: int, db: DBSession = Depends(get_db)):
    """标记已交付：将工单状态从 processing → shipped（人工生成PPT后手动交付）"""

    # P0-Root-Cause-Sweep: 将同步 DB 操作卸载到线程池
    def _deliver(db_session: DBSession):
        order = db_session.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None, "工单不存在"
        if order.status not in (OrderStatus.PROCESSING, OrderStatus.AWAITING_REVIEW):
            return None, f"当前状态 [{order.status}] 不可标记交付"
        order.status = OrderStatus.SHIPPED
        db_session.commit()
        return order, None

    order, err = await run_in_db_thread(_deliver, db)
    if err:
        return {"status": "error", "msg": err}
    await manager.broadcast({"event": "update", "action": "order_delivered", "order_id": order_id})
    return {"status": "success", "order_sn": order.order_sn}
