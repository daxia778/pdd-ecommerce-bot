"""
FastAPI 路由层 - 核心 API 端点：
1. POST /chat       - 开发测试对话接口（含 RAG + SQLite 持久化 + 升级检测）
2. POST /webhook/pdd - 模拟 PDD 平台 Webhook
3. GET  /health     - 健康检查（P1-6: 含 LLM 可达性探测）

P1-6: /health 端点新增 LLM ping 探测，快速确认 LLM API 是否可用
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import ipaddress
import json
import re
import socket
import time
from urllib.parse import urlparse

from cachetools import TTLCache
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession

from config.settings import settings
from src.api.websocket_manager import manager
from src.core.content_guardrail import check_ai_output
from src.core.escalation_detector import analyze as analyze_escalation
from src.core.llm_client import get_llm_client
from src.core.rag_engine import get_rag_engine
from src.core.session_manager import session_manager
from src.models.database import get_db, run_in_db_thread
from src.services import db_service
from src.services.pdd_api_client import pdd_api_client
from src.services.redis_client import redis_client
from src.services.task_coordinator import task_coordinator
from src.utils.background_task_wrapper import catch_background_exceptions
from src.utils.logger import logger
from src.utils.prompt_loader import prompt_loader
from src.utils.safe_task import create_safe_task

router = APIRouter()

# P1-2 (P0-3 修复): 语义防抖缓存，当无 Redis 时退化为 TTLCache 避免内存泄漏
_debounce_cache = TTLCache(maxsize=1000, ttl=3600)

# P1-Fix-3: Webhook 防重放攻击缓存 (内存兜底)
_webhook_nonce_cache = TTLCache(maxsize=5000, ttl=300)
WEBHOOK_TIMESTAMP_TOLERANCE = 300  # 签名时间戳容差: 5分钟

# ===== PPT 设计店铺精细化 System Prompt =====
# 已通过 L2 企业化迁移至 data/prompts/ppt_consultant.yaml 热重载配置中
# 使用 prompt_loader 获取


# ===== 请求/响应数据模型 =====


class ChatRequest(BaseModel):
    # P1-Fix-2: 入参安全限长，防止超大 payload 打穿 LLM Token 费用或擑出 Embedding OOM
    user_id: str = Field(default="test_user", max_length=128)
    message: str = Field(..., max_length=2000, description="聊天单条内容，最多2000字符")
    platform: str = Field(default="test", max_length=32)
    clear_history: bool = False
    image_url: str | None = Field(default=None, max_length=1024)


class ChatResponse(BaseModel):
    user_id: str
    reply: str
    history_length: int
    escalated: bool = False  # 本次是否触发了人工升级
    escalation_reason: str = ""  # 升级原因标签（如有）


class PddWebhookRequest(BaseModel):
    """
    PDD Webhook 结构
    type: customer_message (客户发给店里) 或 seller_message (人工回复了客户)
    """

    # P1-Fix-2: 入参安全限长
    type: str = Field(default="customer_message", max_length=32)
    buyer_id: str = Field(..., max_length=128)
    shop_id: str = Field(default="default_shop", max_length=128)
    content: str = Field(..., max_length=2000)
    timestamp: int | None = None
    image_url: str | None = Field(default=None, max_length=1024)


# ===== 核心对话逻辑（内部复用函数）=====


async def _process_chat(
    user_id: str,
    message: str,
    platform: str,
    db: DBSession,
    clear_history: bool = False,
    image_url: str | None = None,
) -> dict:
    """
    完整对话处理流程：
    RAG 检索 → 历史加载 → LLM → 升级检测 → DB持久化
    """
    llm = get_llm_client()
    rag = get_rag_engine()

    # ---------------------------------------------------------
    # 0. 检查是否已被人工接管 (AI Paused)
    # P0-Fix-2: 使用异步安全方法，避免同步 DB I/O 阻塞事件循环
    # ---------------------------------------------------------
    if await session_manager.is_ai_paused_async_safe(user_id, db):
        logger.info(f"Chat | AI 已被暂停，忽略此消息 | user_id: {user_id}")
        await session_manager.add_message_async_safe(user_id, "user", message, db=db, platform=platform)
        history = await session_manager.get_history_async_safe(user_id, db=db)
        return {
            "reply": "[系统提示: 该会话已由人工接管，AI 已暂停自动回复]",
            "history_length": len(history),
            "escalated": False,
            "escalation_reason": "none",
        }

    # 可选：清空内存历史
    if clear_history:
        session_manager.clear_session(user_id)
        logger.info(f"清空会话历史 | user_id: {user_id}")

    # P1-2 (P0-3 修复): 语义缓存 (Semantic Cache) - 用 MD5 保证重启/多进程下的稳定一致
    hash_obj = hashlib.md5(message.encode("utf-8")).hexdigest()
    cache_key = f"qa_cache:{hash_obj}"
    try:
        cached_reply = None
        if redis_client.is_available:
            cached_reply = await redis_client.get(cache_key)
        else:
            cached_reply = _debounce_cache.get(cache_key)

        if cached_reply:
            logger.info("🎯 Redis/Memory 全局精确匹配缓存命中，跳过 LLM 调用。")
            # P0-Root-Cause-Sweep: 使用异步安全方法，避免同步 DB I/O 阻塞事件循环
            await session_manager.add_message_async_safe(user_id, "user", message, db=db, platform=platform)
            await session_manager.add_message_async_safe(user_id, "assistant", cached_reply, db=db, platform=platform)
            history = await session_manager.get_history_async_safe(user_id, db=db)
            return {
                "reply": cached_reply,
                "history_length": len(history),
                "escalated": False,
                "escalation_reason": "",
            }
    except Exception as e:
        logger.warning(f"Memory cache error: {e}")

    # === RAG 检索（含 P1-2 相关性过滤）===
    # P0-1 修复：改用异步 retrieve_async 将运算卸载到线程池
    retrieved_docs = await rag.retrieve_async(query=message, top_k=3)
    rag_context = rag.build_context(retrieved_docs)

    # L2: 动态加载 Prompt
    prompt_cfg = prompt_loader.get("ppt_consultant")
    system_prompt = prompt_cfg["base_system_prompt"].format(
        rag_context=rag_context if rag_context else "（知识库暂未入库，请凭经验回答）"
    )

    # === P0-Fix-2: 加入用户消息（异步安全 DB 写入）===
    await session_manager.add_message_async_safe(user_id, "user", message, db=db, platform=platform)

    # === P0-Fix-2: 从内存/DB 获取历史（异步安全读取）===
    full_history = await session_manager.get_history_async_safe(user_id, db=db)

    # 性能优化：限制发送给 LLM 的历史轮数（仅保留最近 8 条），减少 Token 消耗加快响应
    MAX_HISTORY_FOR_LLM = 8
    history = full_history[-MAX_HISTORY_FOR_LLM:] if len(full_history) > MAX_HISTORY_FOR_LLM else full_history

    # P2: Vision API 支持
    if image_url and history and history[-1]["role"] == "user":
        history[-1]["content"] = [
            {"type": "text", "text": history[-1]["content"]},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

    logger.info(
        f"处理消息 | user: {user_id} | platform: {platform} | 消息: {message[:40]} | RAG命中: {len(retrieved_docs)} 条"
    )

    # === 预处理：Slot Filling 检查（检测 PPT 生成核心要素）===
    ppt_keywords = prompt_cfg.get("ppt_keywords", ["PPT"])
    if any(k in message for k in ppt_keywords) and "[[CREATE_ORDER" not in message:
        system_prompt += "\n\n" + prompt_cfg.get("slot_filling_hint", "")

    _llm_start = time.monotonic()
    try:
        reply = await llm.chat(messages=history, system_prompt=system_prompt, max_tokens=500)
        response_time_ms = int((time.monotonic() - _llm_start) * 1000)
        with contextlib.suppress(Exception):
            if redis_client.is_available:
                await redis_client.set(cache_key, reply, ex=3600)
            else:
                _debounce_cache[cache_key] = reply
    except Exception as e:
        logger.error(f"LLM 调用异常: {e}")
        raise HTTPException(status_code=503, detail=f"AI 服务暂时不可用: {str(e)}") from e

    # === P0-Fix-2: AI 回复持久化（异步安全写入）===
    await session_manager.add_message_async_safe(
        user_id, "assistant", reply, db=db, platform=platform, response_time_ms=response_time_ms
    )
    final_history = await session_manager.get_history_async_safe(user_id, db=db)

    # === PPT 自动化任务触发检测 ===
    if "[[CREATE_ORDER:" in reply:
        try:
            match = re.search(r"\[\[CREATE_ORDER:(.*?)\]\]", reply, re.DOTALL)
            if match:
                raw_json = match.group(1).strip()
                try:
                    req_data = json.loads(raw_json)
                except json.JSONDecodeError:
                    # Fallback for slightly malformed JSON sometimes produced by LLMs
                    import ast

                    try:
                        req_data = ast.literal_eval(raw_json)
                    except Exception:
                        req_data = {}

                # Make sure req_data is a dict
                if isinstance(req_data, dict):
                    order_sn = await task_coordinator.create_order(
                        user_id=user_id, platform=platform, requirement=req_data
                    )

                    # === 下单成功后：自动发送"第二步"引导图 ===
                    if order_sn and platform == "pdd":
                        try:
                            guide_image_url = f"{settings.pdd_bot_base_url}/static/assets/step2_wechat_guide.png"
                            await pdd_api_client.send_file_message(
                                mall_id=req_data.get("shop_id", "default_shop"),
                                buyer_id=user_id,
                                file_url=guide_image_url,
                            )
                            logger.info(f"已自动发送第二步引导图 | user: {user_id} | order: {order_sn}")
                        except Exception as e:
                            logger.warning(f"发送引导图失败（不影响订单）: {e}")

                # 从回复中移除指令标记，避免买家看到
                reply = reply.replace(match.group(0), "").strip()
        except Exception as e:
            logger.error(f"解析订单指令失败: {e}")

    # === L2: 内容安全门网 (Guardrail) 拦截 ===
    guardrail_result = check_ai_output(reply)
    if guardrail_result.blocked:
        # 被拦截，使用安全替换词
        reply = guardrail_result.safe_reply
        # 主动触发升级拦截
        escalation_result = {"should_escalate": True, "reason": "guardrail_blocked", "reason_label": "安全红线拦截"}
        escalated = True
        reason = escalation_result["reason"]
        logger.warning(f"Guardrail 拦截 | 用户: {user_id} | 触发规则: {guardrail_result.triggered_rules}")
    else:
        # === 升级检测 ===
        escalation_result = await analyze_escalation(message, reply)
        escalated = escalation_result["should_escalate"]
        reason = escalation_result["reason"]

    if escalated:
        try:
            # P0-Fix-2: 使用 run_in_db_thread 卸载同步 DB 写操作
            await run_in_db_thread(
                db_service.create_escalation,
                db=db,
                user_id=user_id,
                trigger_message=message,
                ai_reply=reply,
                reason=reason,
                platform=platform,
            )
            await run_in_db_thread(db_service.update_session, db, user_id=user_id, status="escalated")
            logger.info(
                f"人工升级已标记 | user_id: {user_id} | reason: {reason} | "
                f"reason_label: {escalation_result['reason_label']}"
            )
        except Exception as e:
            logger.error(f"升级记录写入失败 | user_id: {user_id} | {e}")

    return {
        "reply": reply,
        "history_length": len(final_history),
        "escalated": escalated,
        "escalation_reason": escalation_result["reason_label"] if escalated else "",
    }


# ===== 路由 =====


@router.post("/chat", response_model=ChatResponse, summary="PPT客服对话接口（含RAG+持久化）")
async def chat(req: ChatRequest, db: DBSession = Depends(get_db)):
    """
    核心对话接口 - 集成 RAG 知识库检索 + SQLite 持久化 + 升级检测。
    流程：用户消息 → RAG检索 → LLM生成 → 升级检测 → 写库
    """
    result = await _process_chat(
        user_id=req.user_id,
        message=req.message,
        platform=req.platform,
        db=db,
        clear_history=req.clear_history,
        image_url=req.image_url,
    )

    # 触发前端看板实时更新
    await manager.broadcast({"event": "update", "user_id": req.user_id})

    return ChatResponse(user_id=req.user_id, **result)


@router.get("/extract_requirements/{user_id}", summary="提取买家对话中的结构化需求 (无需鉴权)")
async def extract_requirements_public(user_id: str, db: DBSession = Depends(get_db)):
    """
    从指定用户的对话中提取结构化需求信息。
    供买家模拟器直接调用（无需 JWT），逻辑与 dashboard 版一致。
    """
    from src.models.database import Message, run_in_db_thread

    def _get_all_messages(db_session: DBSession):
        return db_session.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at).all()

    messages = await run_in_db_thread(_get_all_messages, db)

    buyer_msgs = [m.content for m in messages if m.role == "user"]
    all_msgs = [m.content for m in messages]
    buyer_content = " ".join(buyer_msgs)
    all_content = " ".join(all_msgs)

    fields = ["topic", "pages", "style", "deadline", "budget", "audience", "outline", "assets"]
    result = {k: "" for k in fields}
    confidence = {k: 0 for k in fields}
    result["source"] = "none"

    # 1. 优先从 [[CREATE_ORDER:...]] 提取
    order_match = re.search(r"\[\[CREATE_ORDER:(.*?)\]\]", all_content, re.DOTALL)
    if order_match:
        try:
            raw = order_match.group(1).strip()
            data = json.loads(raw)
            for field in fields:
                val = data.get(field, "") or (data.get("details", "") if field == "outline" else "")
                if val and str(val).strip():
                    result[field] = str(val).strip()
                    confidence[field] = 95 if field in ("topic", "pages") else 88
            result["source"] = "order_token"
            result["confidence"] = confidence
            return result
        except Exception:
            pass

    # 2. 启发式关键词提取 — 仅从买家消息中提取
    pages_m = re.search(r"(\d+)\s*[页pP]", buyer_content)
    if pages_m:
        result["pages"] = f"{pages_m.group(1)}页"
        confidence["pages"] = 90

    topic_patterns = [
        r"(?:做|要|需要|定制|制作)\s*([\u4e00-\u9fa5a-zA-Z]{2,15}(?:PPT|ppt|计划书|报告|方案|汇报|总结|答辩|展示|投标|培训|介绍|宣传))",
        r"([\u4e00-\u9fa5]{2,8}(?:计划书|报告|方案|汇报|总结|答辩|投标|培训|宣传|介绍))",
    ]
    for pat in topic_patterns:
        topic_m = re.search(pat, buyer_content)
        if topic_m:
            result["topic"] = topic_m.group(1).strip()
            confidence["topic"] = 80
            break

    style_keywords = ["商务", "学术", "简约", "科技", "高端", "创投", "正规", "现代", "简洁", "大气"]
    for kw in style_keywords:
        if kw in buyer_content:
            result["style"] = kw
            confidence["style"] = 75
            break

    deadline_keywords = ["明天", "后天", "本周", "下周", "月底", "紧急", "加急", "尽快", "马上"]
    for kw in deadline_keywords:
        if kw in buyer_content:
            result["deadline"] = kw
            confidence["deadline"] = 82
            break

    budget_m = re.search(r"(\d+)\s*[元块]", buyer_content)
    if budget_m:
        result["budget"] = f"{budget_m.group(1)}元"
        confidence["budget"] = 78

    if any(result[k] for k in fields):
        result["source"] = "heuristic"

    result["confidence"] = confidence
    return result


@router.post("/webhook/pdd", summary="PDD Webhook 消息接收 (含双轨制学习)")
async def pdd_webhook(
    request: Request,
    req: PddWebhookRequest,
    background_tasks: BackgroundTasks,
    x_pdd_sign: str | None = Header(None, alias="X-PDD-Sign"),
    db: DBSession = Depends(get_db),
):
    """
    模拟 PDD 平台的 Webhook 推送。
    1. 客户消息 (customer_message) -> AI 自动回复逻辑
    2. 人工回复 (seller_message) -> 自动学习逻辑 (QA同步至RAG)
    """
    # P3-3 + P1-Fix-3: Webhook HMAC 校验 + 防重放攻击
    if settings.pdd_webhook_secret:
        if not x_pdd_sign:
            logger.warning("Webhook 校验失败: 缺少 X-PDD-Sign 头")
            raise HTTPException(status_code=401, detail="缺少签名")

        body_bytes = await request.body()
        expected_sign = hmac.new(settings.pdd_webhook_secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sign, x_pdd_sign):
            logger.warning("Webhook 校验失败: 签名不匹配")
            raise HTTPException(status_code=401, detail="签名错误")

        # P1-Fix-3: 防重放攻击 — 检查时间戳 + nonce 去重
        if req.timestamp is not None:
            import time as _time

            now = int(_time.time())
            if abs(now - req.timestamp) > WEBHOOK_TIMESTAMP_TOLERANCE:
                logger.warning(f"Webhook 拒绝: timestamp 超时 | now={now} req.ts={req.timestamp}")
                raise HTTPException(status_code=401, detail="签名已过期")

        # Nonce 去重：同一个签名 5 分钟内不允许重复提交
        is_replayed = False
        if redis_client.is_available:
            nonce_key = f"webhook_nonce:{x_pdd_sign}"
            # nx=True 保证原子性
            acquired = await redis_client.client.set(nonce_key, "1", ex=300, nx=True)
            if not acquired:
                is_replayed = True
        else:
            if x_pdd_sign in _webhook_nonce_cache:
                is_replayed = True
            else:
                _webhook_nonce_cache[x_pdd_sign] = True

        if is_replayed:
            logger.warning(f"Webhook 拒绝: 重放攻击检测 | sign={x_pdd_sign[:16]}...")
            raise HTTPException(status_code=409, detail="重复请求")
    else:
        logger.debug("未配置 pdd_webhook_secret，跳过 Webhook 签名校验")

    rag = get_rag_engine()

    # --- 情况 A: 人工客服回复的消息（自动触发学习模式） ---
    if req.type == "seller_message":
        # P0-Root-Cause-Sweep: 使用异步安全方法，避免同步 DB I/O 阻塞事件循环
        history = await session_manager.get_history_async_safe(req.buyer_id, db=db)
        last_user_msg = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)

        if last_user_msg:
            # P0-Root-Cause-Sweep: 使用异步版本将 Embedding 计算卸载到线程池
            qa_content = f"问：{last_user_msg}\n答：{req.content}"
            await rag.add_document_async(
                content=qa_content,
                metadata={"source": "human_sync", "question": last_user_msg[:100]},
            )
            logger.info(f"🔥 双轨制学习：同步一条人工话术 | 问: {last_user_msg[:20]}... | 答: {req.content[:20]}...")
            await manager.broadcast({"event": "update", "user_id": req.buyer_id})
            return {"status": "learned", "msg": "人工经验已同步"}
        return {"status": "skipped", "msg": "未找到对应的用户提问，无法学习"}

    # --- 情况 B: 客户发来的消息 (原有 AI 自动回复逻辑) ---
    logger.info(f"PDD Webhook | buyer_id: {req.buyer_id} | 内容: {req.content[:50]}")

    if req.type != "customer_message":
        return {"status": "ignored", "reason": f"不处理消息类型: {req.type}"}

    # P0-2 修复: 异步解耦，立即返回 ACK 避免拼多多等平台超时重发导致重复订单和刷屏
    background_tasks.add_task(_process_pdd_webhook_background, req)

    return {
        "status": "success",
        "msg": "queued",
        "buyer_id": req.buyer_id,
    }


@catch_background_exceptions
async def _process_pdd_webhook_background(req: PddWebhookRequest):
    """P0-2: 背景处理 PDD Webhook 请求大模型，独立提供数据库 session 防止关闭报错"""
    from src.models.database import SessionLocal

    db = SessionLocal()
    try:
        try:
            result = await _process_chat(
                user_id=req.buyer_id,
                message=req.content,
                platform="pdd",
                db=db,
                image_url=req.image_url,
            )
        except HTTPException:
            reply = "亲，客服系统正在维护中，请稍后再联系我们，抱歉给您带来不便！🙏"
            result = {"reply": reply, "escalated": False, "escalation_reason": ""}

        logger.info(f"PDD Webhook 回复 (后台) | buyer_id: {req.buyer_id} | 升级: {result['escalated']}")

        # Phase 4 & L2: 异步调用 PDD 开放平台 API
        # 如果失败，抛入重试死信队列
        from src.services.message_retry_queue import retry_queue

        try:
            send_ok = await pdd_api_client.send_customer_message(
                mall_id=req.shop_id, buyer_id=req.buyer_id, content=result["reply"]
            )
            if not send_ok:
                raise RuntimeError("pdd_api_client returned False")
        except Exception as e:
            logger.warning(f"向买家发送 PDD 消息失败，推入重试队列 | buyer_id: {req.buyer_id} | error: {e}")
            await retry_queue.enqueue(mall_id=req.shop_id, buyer_id=req.buyer_id, content=result["reply"])

        # 触发前端看板实时更新
        await manager.broadcast({"event": "update", "user_id": req.buyer_id})
    except Exception as e:
        logger.error(f"处理 PDD Webhook 背景任务异常: {e}")
    finally:
        db.close()


@router.get("/health", summary="健康检查（含LLM可达性探测）")
async def health(db: DBSession = Depends(get_db)):
    """
    健康检查端点：返回服务状态、知识库和数据库信息。
    P1-6: 新增 LLM ping 探测和数据库连通性确认
    """
    rag = get_rag_engine()

    # 探测数据库连通性
    db_status = "ok"
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    stats = db_service.get_stats(db)

    # LLM 可达性探测
    llm_status = "unknown"
    try:
        llm = get_llm_client()
        ping_reply = await llm.chat(
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
            temperature=0.1,
        )
        llm_status = "ok" if ping_reply else "empty_response"
    except Exception as e:
        llm_status = f"error: {type(e).__name__}"
        logger.warning(f"LLM 健康检查失败: {e}")

    return {
        "status": "ok",
        "database": db_status,
        "llm_status": llm_status,
        "active_sessions_memory": "redis_backed",
        "knowledge_docs": rag.get_doc_count(),
        "db_stats": stats,
    }


# ===== 微信二维码接收端点 =====

# P0-SEC: SSRF 防护 - 图片下载域名白名单
_ALLOWED_IMAGE_HOST_PATTERNS = [
    r".*\.pinduoduo\.com$",
    r".*\.pddpic\.com$",
    r".*\.weixin\.qq\.com$",
    r"^mmbiz\.qpic\.cn$",
    r".*\.myqcloud\.com$",
    r".*\.wechat\.com$",
]


def _validate_image_url(url: str) -> None:
    """
    P0-SEC: 校验图片 URL，防止 SSRF 攻击。
    1. 仅允许 http/https 协议
    2. 解析目标 IP，拒绝私有/回环/链路本地地址
    3. 校验 Host 是否在允许的 CDN 白名单中
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="仅支持 HTTP/HTTPS 协议的图片地址")

    host = parsed.hostname
    if not host:
        raise HTTPException(status_code=400, detail="无效的图片 URL")

    # 拒绝私有 / 回环 / 链路本地 IP
    try:
        resolved_ip = socket.gethostbyname(host)
        addr = ipaddress.ip_address(resolved_ip)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            logger.warning(f"P0-SEC SSRF 拦截 | url={url} | resolved_ip={resolved_ip}")
            raise HTTPException(status_code=403, detail="禁止访问内部网络地址")
    except socket.gaierror:
        raise HTTPException(status_code=400, detail=f"无法解析域名: {host}") from None

    # 白名单校验
    if not any(re.match(pattern, host) for pattern in _ALLOWED_IMAGE_HOST_PATTERNS):
        logger.warning(f"P0-SEC SSRF 域名拦截 | host={host} | url={url}")
        raise HTTPException(status_code=403, detail=f"域名 {host} 不在允许的图片来源白名单中")


@router.post("/wechat_qr", summary="接收顾客微信二维码图片")
async def upload_wechat_qr(
    user_id: str,
    image_url: str,
    db: DBSession = Depends(get_db),
):
    """
    顾客下单后发送微信二维码，系统保存并关联到订单。
    - 查找该用户最近的 wechat_pending 订单
    - 保存二维码图片路径
    - 状态流转: wechat_pending -> req_fixed
    - 通知后台工作人员

    P0-Root-Cause-Sweep: 所有 DB 操作通过 run_in_db_thread 卸载，
    HTTP 下载使用 pdd_api_client 的共享连接池。
    """
    import os

    from src.models.database import Order

    # P0-Root-Cause-Sweep: 将同步 DB 查询卸载到线程池
    def _find_pending_order(db_session: DBSession):
        return (
            db_session.query(Order)
            .filter(Order.user_id == user_id, Order.status == "wechat_pending")
            .order_by(Order.created_at.desc())
            .first()
        )

    order = await run_in_db_thread(_find_pending_order, db)

    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"未找到用户 {user_id} 的待处理订单",
        )

    # 下载并保存二维码图片
    qr_dir = os.path.join("data", "wechat_qr", user_id)
    os.makedirs(qr_dir, exist_ok=True)
    qr_filename = f"{order.order_sn}_qr.png"
    qr_path = os.path.join(qr_dir, qr_filename)

    try:
        # P0-SEC: SSRF 防护 — 校验 image_url 合法性
        _validate_image_url(image_url)
        # P0-Root-Cause-Sweep: 使用共享连接池下载，不再每次新建 httpx client
        resp = await pdd_api_client._client.get(image_url)
        if resp.status_code == 200:
            with open(qr_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"微信二维码已保存 | user: {user_id} | path: {qr_path}")
        else:
            qr_path = image_url
            logger.warning(f"二维码下载失败，保存URL | user: {user_id}")
    except Exception as e:
        qr_path = image_url
        logger.warning(f"二维码下载异常: {e}，保存URL")

    # P0-Root-Cause-Sweep: 将同步 DB 写操作卸载到线程池
    def _update_order(db_session: DBSession):
        from src.core.order_state_machine import transition_order
        from src.models.enums import OrderStatus

        order.wechat_qr_image_path = qr_path
        transition_order(order, OrderStatus.REQ_FIXED, db=db_session)

    await run_in_db_thread(_update_order, db)

    logger.info(f"微信二维码已关联订单 | order: {order.order_sn} | user: {user_id} | 状态: wechat_pending -> req_fixed")

    # 异步通知企业微信
    try:
        from src.services.wecom_client import wecom_client

        if wecom_client.is_configured:
            requirement = json.loads(order.requirement_json or "{}")

            create_safe_task(
                wecom_client.send_text_message(
                    user_ids=settings.wecom_default_notify_ids,
                    content=(
                        f"📱 收到顾客微信二维码\n"
                        f"订单: {order.order_sn}\n"
                        f"主题: {requirement.get('topic', '?')}\n"
                        f"请尽快添加顾客微信！"
                    ),
                ),
                name="wecom-notify-qr-received",
            )
    except Exception:
        pass

    # 广播前端更新
    await manager.broadcast({"event": "wechat_qr_received", "user_id": user_id, "order_sn": order.order_sn})

    # P0 修复：在此环节（收到QR之后）才启动自动化生产流水线
    task_coordinator.start_pipeline(order.order_sn)

    return {
        "status": "ok",
        "message": "微信二维码已接收并关联订单",
        "order_sn": order.order_sn,
        "qr_path": qr_path,
    }
