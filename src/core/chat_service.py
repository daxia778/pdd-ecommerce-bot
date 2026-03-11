"""
核心对话服务 - 提取自 webhook.py 的共享业务逻辑。
包含:
  1. 问候语快速通道
  2. 反复读机(连续与非连续)去重保护
  3. Prompt 上下文与槽位填充(Slot Filling)组装
  4. 升级信号处理(Guardrail + 关键词)
"""

import re

from src.utils.prompt_loader import prompt_loader

# 统一管理的问候语检测模式
GREETING_PATTERNS = {
    "在吗",
    "你好",
    "在不在",
    "在嘛",
    "客服",
    "hi",
    "hello",
    "在吗？",
    "你好呀",
    "在的吗",
    "有人吗",
    "嗨",
}

GREETING_REPLY = "亲，在的呢！我是云芊艺小店的智小设AI客服，专注PPT/BP/课件定制，请问有什么可以帮您的呀？"


def check_greeting_fastpath(message: str) -> bool:
    """检查是否命中问候语快速通道"""
    msg_stripped = (
        message.strip().lower().replace("？", "").replace("?", "").replace("！", "").replace("!", "").replace("。", "")
    )
    return bool(
        msg_stripped in GREETING_PATTERNS
        or len(msg_stripped) <= 4
        and any(g in msg_stripped for g in ["在吗", "你好", "客服", "在不", "有人"])
    )


def dedup_history(history: list[dict], user_id: str) -> tuple[list[dict], int]:
    """
    反复读机保护：检测所有重复的 assistant 内容（含非连续）。
    模式：[assistant: X, user: Y, assistant: X] 也要去重
    返回去重后的 history 和重复条数。
    """
    seen_assistant_contents = set()
    deduped_history = []
    duplicate_count = 0
    for msg in history:
        if msg["role"] == "assistant":
            content_key = msg["content"].strip()[:200]  # 前200字作为指纹
            if content_key in seen_assistant_contents:
                duplicate_count += 1
                deduped_history.append({"role": "assistant", "content": "[重复回复已省略]"})
                continue
            seen_assistant_contents.add(content_key)
        deduped_history.append(msg)

    return deduped_history, duplicate_count


def prepare_system_prompt(rag_context: str, message: str, duplicate_count: int = 0) -> str:
    """组装 System Prompt，包含基础要求、RAG、重复惩罚和 Slot Filling 提示"""
    # L3: 模块化 Prompt 组装（v3.0 架构）
    system_prompt = prompt_loader.assemble_system_prompt(
        rag_context=rag_context if rag_context else "（知识库暂未入库，请凭经验回答）"
    )

    if duplicate_count > 0:
        system_prompt += (
            "\n\n【紧急系统提示】你刚才的回复和之前一模一样（已被系统标记为[重复回复已省略]），"
            "这说明你没有认真理解客户的最新问题。现在请你：\n"
            "1. 仔细阅读客户最后一条消息\n"
            "2. 给出一个完全不同的、有针对性的新回答\n"
            "3. 绝对不要重复之前说过的任何一句话"
        )

    ppt_keywords = prompt_loader.get_ppt_keywords()
    if any(k in message for k in ppt_keywords) and "[[CREATE_ORDER" not in message:
        system_prompt += "\n\n" + prompt_loader.get_slot_filling_hint()

    return system_prompt


def process_guardrail_and_escalation(reply: str, message: str) -> tuple[str, bool, str]:
    """
    统一处理安全过滤和降级检测
    返回 (处理后的reply, is_escalated, escalation_reason)
    """
    from src.core.content_guardrail import check_ai_output

    # === L2: 内容安全门网 (Guardrail) 拦截 ===
    guardrail_result = check_ai_output(reply)
    if guardrail_result.blocked:
        reply = guardrail_result.safe_reply
        escalated = True
        reason = "guardrail_blocked"
        return reply, escalated, reason

    # === 快速检测需要升级的信号(退款、投诉等) ===
    HIGH_CONFIDENCE_KEYWORDS = ["投诉", "骗", "差评", "退款", "举报", "维权", "人工", "真人", "消协", "12315"]
    if any(kw in message for kw in HIGH_CONFIDENCE_KEYWORDS):
        return reply, True, "keyword_escalation"

    return reply, False, ""


def clean_llm_reply(reply: str) -> str:
    """去除 LLM 输出的前导空白及不再允许的订单指令"""
    if reply:
        reply = reply.lstrip("\n \t")

    # 退化指令拦截：过滤 [[CREATE_ORDER:...]]
    if "[[CREATE_ORDER:" in reply:
        reply = re.sub(r"\[\[CREATE_ORDER:.*?\]\]", "", reply, flags=re.DOTALL).strip()

    return reply
