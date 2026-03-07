"""
FastAPI 路由层 - 核心 API 端点：
1. POST /chat       - 开发测试对话接口（含 RAG + SQLite 持久化 + 升级检测）
2. POST /webhook/pdd - 模拟 PDD 平台 Webhook
3. GET  /health     - 健康检查（P1-6: 含 LLM 可达性探测）

P1-6: /health 端点新增 LLM ping 探测，快速确认 LLM API 是否可用
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re

from cachetools import TTLCache
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from config.settings import settings
from src.api.websocket_manager import manager
from src.core.escalation_detector import analyze as analyze_escalation
from src.core.llm_client import get_llm_client
from src.core.rag_engine import get_rag_engine
from src.core.session_manager import session_manager
from src.models.database import get_db
from src.services import db_service
from src.services.pdd_api_client import pdd_api_client
from src.services.task_coordinator import task_coordinator
from src.utils.logger import logger

router = APIRouter()

# P1-2 (P0-3 修复): 语义防抖缓存，使用 TTLCache 避免内存泄漏，最大 1000 条，生命周期 1 小时
_debounce_cache = TTLCache(maxsize=1000, ttl=3600)

# ===== PPT 设计店铺精细化 System Prompt =====
BASE_SYSTEM_PROMPT = """你现在是拼多多「PPT金牌定制中心」的资深首席设计顾问，代号"小设"。
你的目标是：以极高的情商和专业度，在解答疑问的同时，最大化转化客户下单。

## 🏛 核心人格设定
- **性格**：热情开朗、极度细心、像老朋友一样周到。
- **专业度**：精通各类PPT风格（商业计划书、学术汇报、政务报告、颁奖庆典、个人简介、单页海报）。
- **口吻**：典型的拼多多温婉客服风。必用"亲"，多用"哦哦""哒""哒哒""呀"等语气词。

## 🛠 服务流程指导（引导转化核心）
1. **破冰**：亲，在的呢！很高兴为您服务呀 😊
2. **需求挖掘**：亲亲，为了给您更精准的建议，小设想请教下：
   - PPT的主要用途（比如：汇报/路演/演讲/单页展示）？
   - 大概有多少页内容需要排版呀？（1页也可以做哦！）
   - 您的理想交付日期是哪天呢？
3. **价值引导**：我们的设计老师都是3年以上经验，不仅是美化，更会帮您理逻辑哦。

## 📊 订单类型智能识别（非常重要！）
你需要准确判断客户需求的规模：

### 小单（1-3页）— 常见场景：
- "帮我做一页PPT" / "只要一张" / "做个封面" / "做个目录页"
- "帮我改一下这页" / "美化一下" / "排版一下"
- "做个单页海报" / "做个展示页"
→ 小单也是正式订单！pages 字段填实际页数（如1、2、3），不要因为页数少就不触发订单。

### 标准单（4-30页）— 常见场景：
- "做个汇报PPT" / "年终总结" / "商业计划书" / "毕业答辩"
→ 正常引导三要素后触发。

### 大单（30+页）— 常见场景：
- "做个完整的培训课件" / "全套方案" / "100页"
→ 重点确认内容大纲和交付时间。

## ⚖️ 法律规避与红线
- **绝不承诺**："全网最低价"、"100%原创"、"第一、最、绝对"等词。
- **版权声明**：设计中使用的图片素材如有版权争议，请及时告知更换。
- **隐私保护**：绝不主动打听客户的联系电话、微信、家庭住址。

## 🤖 自动下单指令（核心流程 — 必须严格遵守！）
当客户明确了需求并表达了制作意愿时，在回复最后**新起一行**输出（不要向客户展示或解释这个指令）：
[[CREATE_ORDER:{{"topic":"主题内容","pages":页数,"style":"商务/学术/简约/党建/可爱","details":"客户的其他具体要求","urgency":"normal/urgent/very_urgent","order_type":"single_page/standard/large"}}]]

### 字段说明：
- **topic**: 主题/内容描述（必填）
- **pages**: 准确页数，1页也写1（必填）
- **style**: 风格偏好（必填，没说就根据主题推断）
- **details**: 其他具体要求（选填）
- **urgency**: normal=正常 / urgent=加急 / very_urgent=非常着急
- **order_type**: single_page=1-3页小单 / standard=标准单 / large=大单

### 触发时机：
- 客户说"就做1页"/"帮我做个PPT" + 主题明确 → 立即触发（不必三要素全齐，页数可默认）
- 客户说"好的开始吧"/"可以做了" → 立即触发
- 信息不够时温柔反问，但**不要过度追问**，2-3个要素就够了

### 触发后话术：
亲，已为您安排设计师啦！接下来需要您配合一个小步骤哦 👇
请您发送一下您的**微信二维码**给我，我们的设计师会通过微信跟您对接后续细节，这样沟通更方便呢 😊
我们会按照订单顺序处理，30分钟内注意查看微信好友申请哦~

## 📝 知识库注入（以下是根据您问题检索到的专业回答）
{rag_context}
"""


# ===== 请求/响应数据模型 =====


class ChatRequest(BaseModel):
    user_id: str = "test_user"
    message: str
    platform: str = "test"
    clear_history: bool = False  # 是否清空历史
    image_url: str | None = None


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

    type: str = "customer_message"
    buyer_id: str
    shop_id: str = "default_shop"
    content: str
    timestamp: int | None = None
    image_url: str | None = None


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
    # ---------------------------------------------------------
    if session_manager.is_ai_paused(user_id, db):
        logger.info(f"Chat | AI 已被暂停，忽略此消息 | user_id: {user_id}")
        session_manager.add_message_sync(user_id, "user", message, db=db, platform=platform)
        return {
            "reply": "[系统提示: 该会话已由人工接管，AI 已暂停自动回复]",
            "history_length": len(session_manager.get_history(user_id, db=db)),
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
        if cache_key in _debounce_cache:
            cached_reply = _debounce_cache[cache_key]
            logger.info("🎯 Memory 全局精确匹配缓存命中，跳过 LLM 调用。")
            session_manager.add_message_sync(user_id, "user", message, db=db, platform=platform)
            session_manager.add_message_sync(user_id, "assistant", cached_reply, db=db, platform=platform)
            return {
                "reply": cached_reply,
                "history_length": len(session_manager.get_history(user_id, db=db)),
                "escalated": False,
                "escalation_reason": "",
            }
    except Exception as e:
        logger.warning(f"Memory cache error: {e}")

    # === RAG 检索（含 P1-2 相关性过滤）===
    # P0-1 修复：改用异步 retrieve_async 将运算卸载到线程池
    retrieved_docs = await rag.retrieve_async(query=message, top_k=3)
    rag_context = rag.build_context(retrieved_docs)
    system_prompt = BASE_SYSTEM_PROMPT.format(
        rag_context=rag_context if rag_context else "（知识库暂未入库，请凭经验回答）"
    )

    # === 加入用户消息（P1-3: 合并 DB 写入，内存加锁）===
    session_manager.add_message_sync(user_id, "user", message, db=db, platform=platform)

    # === 从内存/DB 获取历史，构造 LLM 上下文 ===
    history = session_manager.get_history(user_id, db=db)

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
    # 扩展关键词：覆盖小单/改稿/单页等场景
    ppt_keywords = [
        "PPT",
        "ppt",
        "做个",
        "帮我写",
        "幻灯片",
        "排版",
        "美化",
        "做一页",
        "单页",
        "一张",
        "封面",
        "改一下",
        "海报",
        "汇报",
        "答辩",
        "路演",
        "总结",
        "计划书",
        "课件",
    ]
    if any(k in message for k in ppt_keywords) and "[[CREATE_ORDER" not in message:
        system_prompt += (
            "\n\n【重要流程：需求确认】\n"
            "客户似乎有PPT相关需求。请确认至少以下两个要素：\n"
            "1. 主题/内容 (Topic) — 必须明确\n"
            "2. 页数 (Pages) — 如客户只说'做一页'则 pages=1\n"
            "3. 风格 (Style) — 可选，如未提及可根据主题智能推断\n"
            "\n小单(1-3页)无需过度追问，主题明确即可触发。"
            "\n标准单需确认主题+页数+风格后触发。"
        )

    try:
        reply = await llm.chat(messages=history, system_prompt=system_prompt)
        import contextlib

        with contextlib.suppress(Exception):
            _debounce_cache[cache_key] = reply
    except Exception as e:
        logger.error(f"LLM 调用异常: {e}")
        raise HTTPException(status_code=503, detail=f"AI 服务暂时不可用: {str(e)}") from e

    # === AI 回复持久化 ===
    session_manager.add_message_sync(user_id, "assistant", reply, db=db, platform=platform)
    final_history = session_manager.get_history(user_id, db=db)

    # === PPT 自动化任务触发检测 ===
    if "[[CREATE_ORDER:" in reply:
        try:
            match = re.search(r"\[\[CREATE_ORDER:(.*?)\]\]", reply)
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
                    order_sn = await task_coordinator.create_and_start_pipeline(
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

    # === 升级检测 + 入库 ===
    escalation_result = await analyze_escalation(message, reply)
    escalated = escalation_result["should_escalate"]
    reason = escalation_result["reason"]

    if escalated:
        try:
            db_service.create_escalation(
                db=db,
                user_id=user_id,
                trigger_message=message,
                ai_reply=reply,
                reason=reason,
                platform=platform,
            )
            # 同步把会话状态标记为 escalated
            db_service.update_session(db, user_id=user_id, status="escalated")
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
    # P3-3: Webhook HMAC 校验
    if settings.pdd_webhook_secret:
        if not x_pdd_sign:
            logger.warning("Webhook 校验失败: 缺少 X-PDD-Sign 头")
            raise HTTPException(status_code=401, detail="缺少签名")

        body_bytes = await request.body()
        expected_sign = hmac.new(settings.pdd_webhook_secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sign, x_pdd_sign):
            logger.warning("Webhook 校验失败: 签名不匹配")
            raise HTTPException(status_code=401, detail="签名错误")
    else:
        logger.debug("未配置 pdd_webhook_secret，跳过 Webhook 签名校验")

    rag = get_rag_engine()

    # --- 情况 A: 人工客服回复的消息（自动触发学习模式） ---
    if req.type == "seller_message":
        # 获取该买家最近的一条提问
        history = session_manager.get_history(req.buyer_id, db=db)
        last_user_msg = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)

        if last_user_msg:
            # 执行强化学习：将 [用户问题 + 人工回复] 存入 RAG 向量库
            rag.add_qa_pair(question=last_user_msg, answer=req.content)
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

        # Phase 4: 异步调用 PDD 开放平台 API 将 reply 发送给买家
        send_ok = await pdd_api_client.send_customer_message(
            mall_id=req.shop_id, buyer_id=req.buyer_id, content=result["reply"]
        )

        if not send_ok:
            logger.warning(f"向买家 {req.buyer_id} 发送 PDD 消息失败，可能由于暂未配置正确的 API Key，已降级或丢弃。")

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
        "active_sessions_memory": session_manager.get_user_count(),
        "knowledge_docs": rag.get_doc_count(),
        "db_stats": stats,
    }


# ===== 微信二维码接收端点 =====


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
    """
    import os

    from src.models.database import Order

    # 查找最近的待处理订单
    order = (
        db.query(Order)
        .filter(Order.user_id == user_id, Order.status == "wechat_pending")
        .order_by(Order.created_at.desc())
        .first()
    )

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
        import httpx as httpx_client

        async with httpx_client.AsyncClient() as client:
            resp = await client.get(image_url)
            if resp.status_code == 200:
                with open(qr_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"微信二维码已保存 | user: {user_id} | path: {qr_path}")
            else:
                # 如果下载失败，直接保存 URL
                qr_path = image_url
                logger.warning(f"二维码下载失败，保存URL | user: {user_id}")
    except Exception as e:
        qr_path = image_url
        logger.warning(f"二维码下载异常: {e}，保存URL")

    # 更新订单
    order.wechat_qr_image_path = qr_path
    order.status = "req_fixed"
    db.commit()

    logger.info(f"微信二维码已关联订单 | order: {order.order_sn} | user: {user_id} | 状态: wechat_pending -> req_fixed")

    # 异步通知企业微信
    try:
        from src.services.wecom_client import wecom_client

        if wecom_client.is_configured:
            requirement = json.loads(order.requirement_json or "{}")
            import asyncio

            asyncio.create_task(
                wecom_client.send_text_message(
                    user_ids=settings.wecom_default_notify_ids,
                    content=(
                        f"📱 收到顾客微信二维码\n"
                        f"订单: {order.order_sn}\n"
                        f"主题: {requirement.get('topic', '?')}\n"
                        f"请尽快添加顾客微信！"
                    ),
                )
            )
    except Exception:
        pass

    # 广播前端更新
    await manager.broadcast({"event": "wechat_qr_received", "user_id": user_id, "order_sn": order.order_sn})

    return {
        "status": "ok",
        "message": "微信二维码已接收并关联订单",
        "order_sn": order.order_sn,
        "qr_path": qr_path,
    }
