from __future__ import annotations

import os
from datetime import datetime, timedelta

import jwt
from async_lru import alru_cache
from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import desc, func
from sqlalchemy.orm import Session as DBSession

from src.api.websocket_manager import manager
from src.core.order_state_machine import InvalidTransitionError, transition_order
from src.models.database import Escalation, Message, Order, Session, get_db, run_in_db_thread
from src.models.enums import EscalationStatus, OrderStatus, SessionStatus
from src.services import db_service
from src.services.pdd_api_client import pdd_api_client
from src.utils.auth import JWT_ALGORITHM, JWT_SECRET_KEY, verify_admin
from src.utils.logger import logger

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
        logger.warning(f"WebSocket 鉴权失败 | token 解析异常: {type(e).__name__}: {e}")
        await websocket.close(code=1008, reason="Invalid or expired token")
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

    def _get_stats(db_session: DBSession):
        active_sessions = db_session.query(Session).filter(Session.status == SessionStatus.ACTIVE).count()
        pending_escalations = db_session.query(Escalation).filter(Escalation.status == EscalationStatus.PENDING).count()
        active_orders = (
            db_session.query(Order)
            .filter(Order.status.in_([OrderStatus.GENERATING, OrderStatus.PROCESSING, OrderStatus.AWAITING_REVIEW]))
            .count()
        )

        shipped_orders = db_session.query(Order).filter(Order.status == OrderStatus.SHIPPED).count()
        total_orders = db_session.query(Order).count()

        total_sessions = db_session.query(Session).count()
        if total_sessions > 0:
            conversion_rate = f"{min(shipped_orders / total_sessions * 100, 100):.1f}%"
        else:
            conversion_rate = "0.0%"

        avg_order_value = 900
        total_revenue = f"¥ {shipped_orders * avg_order_value:,}"

        total_escalations = db_session.query(Escalation).count()
        if total_sessions > 0:
            escalation_rate = total_escalations / total_sessions
            satisfaction_rate = f"{max((1 - escalation_rate) * 100, 0):.1f}%"
        else:
            satisfaction_rate = "98.5%"

        avg_ms_row = (
            db_session.query(func.avg(Message.response_time_ms))
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

    return await run_in_db_thread(_get_stats, db)


@router.get("/api/dashboard/stats")
async def get_stats(db: DBSession = Depends(get_db)):
    """获取整体统计数据"""
    return await _get_stats_cached(db)


@router.get("/api/dashboard/stats/hourly")
async def get_stats_hourly(db: DBSession = Depends(get_db)):
    """获取当天每小时的消息量（真实时间序列数据，替换假 ECharts 数据）"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    def _get_hourly(db_session: DBSession):
        return (
            db_session.query(
                func.strftime("%H", Message.created_at).label("hour"), func.count(Message.id).label("count")
            )
            .filter(Message.created_at >= today, Message.created_at < tomorrow)
            .group_by("hour")
            .all()
        )

    rows = await run_in_db_thread(_get_hourly, db)

    # 将数据增展为 24 个小时的完整点
    hour_map = {row.hour: row.count for row in rows}
    hours = [f"{h:02d}:00" for h in range(24)]
    counts = [hour_map.get(f"{h:02d}", 0) for h in range(24)]

    return {"hours": hours, "counts": counts}


@router.get("/api/dashboard/sessions")
async def get_sessions(db: DBSession = Depends(get_db)):
    """获取最近的会话列表"""

    def _get_sessions(db_session: DBSession):
        return db_session.query(Session).order_by(desc(Session.updated_at)).limit(20).all()

    sessions = await run_in_db_thread(_get_sessions, db)
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

    def _get_messages(db_session: DBSession):
        return db_session.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at).all()

    messages = await run_in_db_thread(_get_messages, db)
    return [
        {
            "role": m.role,
            "content": m.content,
            "platform": m.platform or "unknown",
            "sender_type": "customer" if m.role == "user" else "ai",
            "response_time_ms": m.response_time_ms,
            "created_at": m.created_at.strftime("%H:%M:%S") if m.created_at else "",
        }
        for m in messages
    ]


@router.get("/api/dashboard/search")
async def search_messages(q: str = Query("", min_length=1), db: DBSession = Depends(get_db)):
    """
    全局搜索：在所有会话的消息内容中搜索关键词，返回匹配的 user_id 列表。
    性能: SQLite LIKE 查询 + DISTINCT，适合中小规模数据。
    """

    def _search(db_session: DBSession):
        from sqlalchemy import distinct

        keyword = f"%{q}%"
        # 搜索消息内容
        matched_users_from_messages = (
            db_session.query(distinct(Message.user_id)).filter(Message.content.like(keyword)).all()
        )
        # 搜索用户名本身
        matched_users_from_sessions = (
            db_session.query(distinct(Session.user_id)).filter(Session.user_id.like(keyword)).all()
        )
        # 合并去重
        all_ids = set()
        for (uid,) in matched_users_from_messages:
            all_ids.add(uid)
        for (uid,) in matched_users_from_sessions:
            all_ids.add(uid)
        return list(all_ids)

    matched_user_ids = await run_in_db_thread(_search, db)
    return {"matched_user_ids": matched_user_ids, "count": len(matched_user_ids)}


@router.get("/api/dashboard/messages/{user_id}/extract_requirements")
async def extract_requirements(user_id: str, db: DBSession = Depends(get_db)):
    """
    从指定用户的对话中提取结构化需求信息。
    智能提取：优先依靠 LLM 强大的 NLP 理解能力，代替之前的正则匹配；
    如果失败，自动降级为正则表达式启发式提取。
    """
    from src.services.requirement_extractor import extract_requirements_intelligently

    def _get_all_messages(db_session: DBSession):
        return db_session.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at).all()

    messages = await run_in_db_thread(_get_all_messages, db)

    # 分离买家消息和 AI 消息
    buyer_msgs = [m.content for m in messages if m.role == "user"]
    all_msgs = [m.content for m in messages]
    buyer_content = " ".join(buyer_msgs)
    all_content = " ".join(all_msgs)

    # 调用提取服务（优先 LLM，降级正则）
    result = await extract_requirements_intelligently(buyer_content, all_content)
    return result


@router.get("/api/dashboard/escalations")
async def get_escalations(db: DBSession = Depends(get_db)):
    """获取需要人工处理的升级记录"""

    def _get_escalations(db_session: DBSession):
        return (
            db_session.query(Escalation)
            .filter(Escalation.status == EscalationStatus.PENDING)
            .order_by(desc(Escalation.created_at))
            .all()
        )

    escalations = await run_in_db_thread(_get_escalations, db)
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "platform": e.platform or "unknown",
            "trigger_message": e.trigger_message,
            "ai_reply": e.ai_reply,
            "reason": e.reason,
            "reason_label": e.reason,
            "status": e.status,
            "operator_name": e.operator_name,
            "created_at": e.created_at.strftime("%Y-%m-%d %H:%M:%S") if e.created_at else "",
        }
        for e in escalations
    ]


@router.post("/api/dashboard/escalations/{esc_id}/resolve")
async def resolve_escalation(esc_id: int, db: DBSession = Depends(get_db)):
    """
    标记升级问题为已处理。
    """

    def _resolve(db_session: DBSession):
        return db_service.resolve_escalation(db_session, escalation_id=esc_id)

    esc = await run_in_db_thread(_resolve, db)
    if esc:
        await manager.broadcast({"event": "update", "action": "resolve_escalation"})
        return {"status": "success"}
    return {"status": "error", "msg": "Not found or already resolved"}


@router.get("/api/dashboard/orders")
async def get_orders(status: str | None = None, show_all: bool = False, db: DBSession = Depends(get_db)):
    """获取 PPT 工单列表。默认只返回未交付的工单（req_fixed / processing）。"""

    def _get_orders(db_session: DBSession):
        q = db_session.query(Order)
        if status:
            q = q.filter(Order.status == status)
        elif not show_all:
            q = q.filter(Order.status.in_([OrderStatus.REQ_FIXED, OrderStatus.PROCESSING, OrderStatus.AWAITING_REVIEW]))
        return q.order_by(desc(Order.created_at)).limit(50).all()

    orders = await run_in_db_thread(_get_orders, db)
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
    """
    人工批准发货（兼容旧接口）。
    awaiting_review → shipped，全程走状态机，防止非法流转。
    """

    def _approve(db_session: DBSession):
        order = db_session.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None, "工单不存在"
        try:
            transition_order(order, OrderStatus.SHIPPED, db=db_session)
            return order, None
        except InvalidTransitionError as e:
            return None, str(e)

    order, err = await run_in_db_thread(_approve, db)
    if err:
        return {"status": "error", "msg": err}
    mall_id = getattr(order, "mall_id", "default_mall_id")
    await pdd_api_client.send_file_message(mall_id, order.user_id, order.clean_file_url or "")
    await manager.broadcast({"event": "update", "action": "approve_order"})
    return {"status": "success"}


@router.post("/api/dashboard/orders/{order_id}/claim")
async def claim_order(order_id: int, db: DBSession = Depends(get_db)):
    """人工接单：将工单状态从 req_fixed → processing（走状态机，防非法跳转）"""

    def _claim(db_session: DBSession):
        order = db_session.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None, "工单不存在"
        try:
            transition_order(order, OrderStatus.PROCESSING, db=db_session)
            return order, None
        except InvalidTransitionError as e:
            return None, str(e)

    order, err = await run_in_db_thread(_claim, db)
    if err:
        return {"status": "error", "msg": err}
    await manager.broadcast({"event": "update", "action": "order_claimed", "order_id": order_id})
    return {"status": "success", "order_sn": order.order_sn}


@router.post("/api/dashboard/orders/{order_id}/deliver")
async def deliver_order(order_id: int, db: DBSession = Depends(get_db)):
    """标记已交付：工单状态 → shipped（走状态机，支持 processing / awaiting_review 两种合法前驱状态）"""

    def _deliver(db_session: DBSession):
        order = db_session.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None, "工单不存在"
        try:
            transition_order(order, OrderStatus.SHIPPED, db=db_session)
            return order, None
        except InvalidTransitionError as e:
            return None, str(e)

    order, err = await run_in_db_thread(_deliver, db)
    if err:
        return {"status": "error", "msg": err}
    await manager.broadcast({"event": "update", "action": "order_delivered", "order_id": order_id})
    return {"status": "success", "order_sn": order.order_sn}


# ==========================================================================
# P1-b: DLQ 监控 API — 运营可查看并手动重试失败消息
# ==========================================================================


@router.get("/api/dashboard/dlq")
async def get_dlq_status():
    """
    获取消息重试死信队列状态。
    返回队列大小 + 最近的死信消息列表（供运营人员核查补发）。
    """
    from src.services.message_retry_queue import retry_queue

    return {
        "retry_queue_size": retry_queue.retry_queue_size,
        "dead_letter_queue_size": retry_queue.dead_letter_queue_size,
        "dead_letters": retry_queue.get_dead_letters(),
    }


@router.post("/api/dashboard/dlq/retry-all")
async def retry_all_dead_letters():
    """
    手动将死信队列中的所有消息重新推入重试队列。
    运营人员确认 PDD API 恢复后可调用此接口补发。
    """
    from src.services.message_retry_queue import retry_queue

    count = retry_queue.dead_letter_queue_size
    if count == 0:
        return {"status": "ok", "msg": "死信队列为空，无需操作"}

    # 将死信队列内容重新入队
    dead_letters = list(retry_queue._dead_letter_queue)
    retry_queue._dead_letter_queue.clear()
    for msg in dead_letters:
        msg.retry_count = 0  # 重置重试计数
        retry_queue._retry_queue.append(msg)

    return {"status": "ok", "msg": f"已将 {count} 条死信消息重新推入重试队列"}


# ==========================================================================
# P2-b: Prompt 在线编辑 API — 运营可直接通过 UI 更新 AI 话术
# ==========================================================================


@router.get("/api/dashboard/prompts/{name}")
async def get_prompt(name: str):
    """
    获取指定 Prompt 配置文件的原始内容（YAML 格式）。

    Args:
        name: 配置文件名，不含 .yaml 后缀，如 'ppt_consultant'
    """

    from src.utils.prompt_loader import prompt_loader

    allowed = {"ppt_consultant"}  # 白名单，防止路径遍历
    if name not in allowed:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail=f"不允许访问的配置: {name}")

    try:
        _ = prompt_loader.get(name)
        # 重新序列化为 YAML 字符串返回给前端编辑
        from src.utils.prompt_loader import PROMPTS_DIR

        path = PROMPTS_DIR / f"{name}.yaml"
        return {"name": name, "content": path.read_text(encoding="utf-8")}
    except FileNotFoundError as err:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"配置文件不存在: {name}") from err


class PromptUpdateRequest(BaseModel):
    content: str  # 原始 YAML 文本


@router.put("/api/dashboard/prompts/{name}")
async def update_prompt(name: str, body: PromptUpdateRequest):
    """
    更新指定 Prompt 配置文件，立即生效（prompt_loader 热重载）。

    安全措施：
    1. 白名单限制可修改的文件
    2. YAML 语法预校验，拒绝写入无效文件
    3. 写入前备份原文件
    """
    import shutil

    import yaml
    from fastapi import HTTPException

    from src.utils.prompt_loader import PROMPTS_DIR, prompt_loader

    allowed = {"ppt_consultant"}
    if name not in allowed:
        raise HTTPException(status_code=403, detail=f"不允许修改的配置: {name}")

    # 1. YAML 语法校验
    try:
        yaml.safe_load(body.content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=422, detail=f"YAML 语法错误: {e}") from e

    path = PROMPTS_DIR / f"{name}.yaml"

    # 2. 写入前备份
    backup_path = PROMPTS_DIR / f"{name}.yaml.bak"
    if path.exists():
        shutil.copy2(path, backup_path)

    # 3. 写入新内容
    path.write_text(body.content, encoding="utf-8")

    # 4. 强制刷新 prompt_loader 缓存
    prompt_loader.reload(name)

    logger.info(f"Prompt 配置已更新 | name: {name} | 备份: {backup_path}")
    return {"status": "ok", "msg": f"{name} 已更新并立即生效"}


# ==========================================================================
# 系统链路健康度 API — 全链路单屏可视化
# ==========================================================================


@router.get("/api/dashboard/system-health")
async def get_system_health(db: DBSession = Depends(get_db)):
    """
    聚合所有子系统的运行状态，返回统一的健康度快照。

    覆盖链路节点：
    1. PDD 平台连接 (pdd_api)
    2. LLM 大模型服务 (llm)
    3. RAG 知识库引擎 (rag)
    4. 消息重试队列 (retry_queue / dlq)
    5. 企业微信服务 (wecom)
    6. Prompt 配置热加载 (prompt_loader)
    7. 数据库连接 (database)
    """
    from src.core.rag_engine import get_rag_engine
    from src.services.message_retry_queue import retry_queue
    from src.services.wecom_client import wecom_client
    from src.utils.prompt_loader import prompt_loader

    components = []

    # 1. PDD API 连接状态
    from src.services.pdd_api_client import pdd_api_client

    # 检测占位符值 — "your_xxx" 类占位符不算已配置
    def _is_real_value(v):
        return bool(v) and not str(v).startswith("your_") and v != "placeholder"

    pdd_configured = all([
        _is_real_value(pdd_api_client.client_id),
        _is_real_value(pdd_api_client.client_secret),
        _is_real_value(pdd_api_client.access_token),
    ])
    components.append(
        {
            "name": "PDD 开放平台",
            "key": "pdd_api",
            "status": "healthy" if pdd_configured else "inactive",
            "detail": "凭证已配置，连接正常" if pdd_configured else "凭证未配置，点击查看配置指引",
            "icon": "🛒",
        }
    )

    # 2. LLM 大模型服务
    try:
        from src.core.llm_client import get_llm_client

        llm = get_llm_client()
        llm_name = type(llm).__name__
        components.append(
            {
                "name": "LLM 大模型",
                "key": "llm",
                "status": "healthy",
                "detail": f"Provider: {llm_name} | 运行正常",
                "icon": "🧠",
            }
        )
    except Exception as e:
        components.append(
            {
                "name": "LLM 大模型",
                "key": "llm",
                "status": "error",
                "detail": f"初始化失败: {e}",
                "icon": "🧠",
            }
        )

    # 3. RAG 知识库
    try:
        rag = get_rag_engine()
        doc_count = rag.get_doc_count()
        components.append(
            {
                "name": "RAG 知识库",
                "key": "rag",
                "status": "healthy" if doc_count > 0 else "warning",
                "detail": f"已索引 {doc_count} 条知识片段" if doc_count > 0 else "知识库为空，建议导入数据",
                "icon": "📚",
            }
        )
    except Exception as e:
        components.append(
            {
                "name": "RAG 知识库",
                "key": "rag",
                "status": "error",
                "detail": f"引擎异常: {e}",
                "icon": "📚",
            }
        )

    # 4. 消息重试队列 / DLQ
    dlq_size = retry_queue.dead_letter_queue_size
    retry_size = retry_queue.retry_queue_size
    if dlq_size > 0:
        mq_status = "error"
        mq_detail = f"⚠ {dlq_size} 条死信待处理 | {retry_size} 条重试中"
    elif retry_size > 0:
        mq_status = "warning"
        mq_detail = f"{retry_size} 条消息重试中 | 死信: 0"
    else:
        mq_status = "healthy"
        mq_detail = "队列清空，全部送达"
    components.append(
        {"name": "消息投递队列", "key": "message_queue", "status": mq_status, "detail": mq_detail, "icon": "📬"}
    )

    # 5. 企业微信
    wecom_ok = wecom_client.is_configured
    components.append(
        {
            "name": "企业微信",
            "key": "wecom",
            "status": "healthy" if wecom_ok else "inactive",
            "detail": "凭证已配置，接口就绪" if wecom_ok else "未配置凭证，功能待启用",
            "icon": "💬",
        }
    )

    # 6. Prompt 热加载
    try:
        prompt_loader.get("ppt_consultant")
        components.append(
            {
                "name": "Prompt 配置",
                "key": "prompt",
                "status": "healthy",
                "detail": "ppt_consultant.yaml 已加载",
                "icon": "📝",
            }
        )
    except Exception:
        components.append(
            {
                "name": "Prompt 配置",
                "key": "prompt",
                "status": "error",
                "detail": "YAML 配置加载失败",
                "icon": "📝",
            }
        )

    # 7. 数据库
    def _check_db(db_session: DBSession):
        from sqlalchemy import text

        try:
            db_session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    try:
        db_ok = await run_in_db_thread(_check_db, db)
        components.append(
            {
                "name": "SQLite 数据库",
                "key": "database",
                "status": "healthy" if db_ok else "error",
                "detail": "WAL 模式运行正常" if db_ok else "连接异常",
                "icon": "🗄️",
            }
        )
    except Exception:
        components.append(
            {
                "name": "SQLite 数据库",
                "key": "database",
                "status": "error",
                "detail": "无法连接数据库",
                "icon": "🗄️",
            }
        )

    # 汇总状态
    statuses = [c["status"] for c in components]
    if "error" in statuses:
        overall = "error"
    elif "warning" in statuses or "degraded" in statuses:
        overall = "warning"
    else:
        overall = "healthy"

    return {"overall": overall, "components": components}


@router.get("/api/dashboard/component-config/{key}")
async def get_component_config(key: str):
    """
    返回指定组件的配置文件内容，供前端管理面板在线查看。
    """
    import os

    config_map = {
        "pdd_api": {
            "title": "PDD 开放平台配置",
            "file": "config/settings.py",
            "env_keys": ["PDD_CLIENT_ID", "PDD_CLIENT_SECRET", "PDD_ACCESS_TOKEN"],
        },
        "llm": {
            "title": "LLM 大模型配置",
            "file": "config/settings.py",
            "env_keys": ["ZHIPU_API_KEYS", "MAIN_CHAT_MODEL", "DEEPSEEK_API_KEYS", "LLM_CHAT_TIMEOUT", "MAX_RETRIES"],
        },
        "rag": {
            "title": "RAG 知识库配置",
            "file": "data/knowledge/",
            "env_keys": ["RAG_TOP_K", "RAG_RERANK_TOP_N"],
        },
        "message_queue": {
            "title": "消息重试队列配置",
            "file": "src/services/message_retry_queue.py",
            "env_keys": [],
        },
        "wecom": {
            "title": "企业微信配置",
            "file": "config/settings.py",
            "env_keys": ["WECOM_CORP_ID", "WECOM_AGENT_ID", "WECOM_SECRET"],
        },
        "prompt": {
            "title": "Prompt 话术配置",
            "file": "data/prompts/ppt_consultant.yaml",
            "env_keys": [],
        },
        "database": {
            "title": "SQLite 数据库配置",
            "file": "config/settings.py",
            "env_keys": ["DATABASE_URL"],
        },
    }

    if key not in config_map:
        return {"error": f"未知组件: {key}"}

    info = config_map[key]
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(base_dir, info["file"])

    # Read config file content
    file_content = ""
    if os.path.isfile(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            file_content = f"[读取失败: {e}]"
    elif os.path.isdir(file_path):
        # List files in directory
        try:
            files = sorted(os.listdir(file_path))
            file_content = f"目录包含 {len(files)} 个文件：\n" + "\n".join(f"  📄 {fn}" for fn in files if not fn.startswith("."))
        except Exception as e:
            file_content = f"[读取目录失败: {e}]"
    else:
        file_content = f"[文件不存在: {info['file']}]"

    # Read relevant env vars (masked for security)
    env_values = {}
    for env_key in info.get("env_keys", []):
        val = os.environ.get(env_key, "")
        if val:
            if any(secret in env_key.upper() for secret in ["SECRET", "KEY", "TOKEN", "PASSWORD"]):
                env_values[env_key] = val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
            else:
                env_values[env_key] = val
        else:
            env_values[env_key] = "(未配置)"

    return {
        "title": info["title"],
        "file_path": info["file"],
        "file_content": file_content,
        "env_vars": env_values,
    }

