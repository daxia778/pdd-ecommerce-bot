"""
升级信号检测器 - 通过 LLM 轻量级意图分类判断是否触发人工升级。
同时识别升级原因标签，供管理员快速分类处理，并保留关键词作为兜底降级策略。

P1-Root-Cause-Sweep: 使用 Pydantic BaseModel 校验 LLM JSON 输出，
防止 LLM 幻觉产生不合法字段值导致下游异常。
"""

import json
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from src.core.llm_client import get_llm_client
from src.utils.logger import logger

# 升级触发关键词（与 System Prompt 中的转人工话术对应，用作兜底）
ESCALATION_KEYWORDS = [
    "人工客服会尽快",
    "已为您标记",
    "专业客服进一步确认",
    "转接一下人工",
    "人工客服小姐姐",
]

# 升级原因识别规则（消息内容 → 原因标签，用作兜底）
REASON_RULES = [
    # (触发关键词列表, 原因标签, 中文描述)
    (["加急", "今天", "明天", "当天", "今晚", "明日"], "urgent", "紧急交付"),
    (["便宜", "打折", "优惠", "降价", "少一点", "能不能低", "砍价", "最低"], "bargain", "价格谈判"),
    (["投诉", "骗", "差评", "退款", "举报", "不满意", "维权", "消协", "12315"], "complaint", "投诉纠纷"),
    (["万", "高端", "定制模板", "多套", "大项目", "长期合作", "几十套", "批发"], "large_order", "大额/长期订单"),
    (["线下", "上门", "面谈", "见面", "现场"], "offline", "线下服务"),
]

INTENT_SYSTEM_PROMPT = """
你是一个电商智能客服系统的「意图分类器」。你的任务是分析【买家】的话语以及【AI客服】的回复，判断是否需要将对话移交给「人工客服」，并提取原因。

【必须转接人工的条件】
1. 强烈要求：买家明确说出需要人工客服、真人。
2. 投诉纠纷：买家情绪激动，提到投诉、骗子、差评、退款、12315等。
3. 复杂商务：涉及几十上百套的大额订单、长期合作、线下见面。
4. 价格死磕：买家反复要求降价、给最低价，或者明确不满意当前价格。
5. 极端紧急：要求几小时内马上出图等极度紧急的交付要求。
6. AI已承诺：如果AI回复中已经明确表示了将要「转接人工」、「已为您标记人工」，则必须为 true。

请严格输出以下 JSON 格式（不要输出任何 Markdown 标记和代码块，必须是纯 JSON 字符串）：
{
    "should_escalate": true 或 false,
    "reason_code": "urgent" | "bargain" | "complaint" | "large_order" | "offline" | "other" | "none",
    "reason_label": "对应的中文标签，如果不需要转人工则是'无'"
}
"""


# P1-Root-Cause-Sweep: 使用 Pydantic 模型校验 LLM 返回的 JSON
class EscalationResult(BaseModel):
    """LLM 意图分类结果的结构化校验模型"""

    should_escalate: bool = False
    reason_code: Literal["urgent", "bargain", "complaint", "large_order", "offline", "other", "none"] = "none"
    reason_label: str = Field(default="无", max_length=50)


def detect_escalation(ai_reply: str) -> bool:
    """关键词兜底检测"""
    return any(kw in ai_reply for kw in ESCALATION_KEYWORDS)


def identify_reason(user_message: str) -> tuple[str, str]:
    """关键词兜底原因识别"""
    for keywords, code, label in REASON_RULES:
        if any(kw in user_message for kw in keywords):
            return code, label
    return "other", "其他"


async def analyze(user_message: str, ai_reply: str) -> dict:
    """
    综合分析：使用 LLM 动态判断是否需要升级 + 升级原因。
    失败时自动降级到基于关键词的规则匹配。

    P1-Root-Cause-Sweep: 使用 Pydantic 模型校验 LLM 输出，
    防止 reason_code 幻觉值或 JSON 格式异常导致下游写入错误。
    """
    llm = get_llm_client()
    prompt = f"【买家消息】：{user_message}\n【AI回复】：{ai_reply}\n\n请输出JSON结果："

    try:
        response_text = await llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=INTENT_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=150,
        )

        # 使用正则安全提取 JSON 对象
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not match:
            raise ValueError(f"未找到 JSON 内容 | raw: {response_text[:100]}")

        raw_json = match.group()

        # P1-Root-Cause-Sweep: Pydantic 结构化校验（双重解析策略）
        try:
            result = EscalationResult.model_validate_json(raw_json)
        except (ValidationError, ValueError):
            # 兼容 LLM 返回的 Python 风格布尔值 (True/False 而非 true/false)
            data = json.loads(raw_json)
            result = EscalationResult.model_validate(data)

        # 二次保险：如果 LLM 判断为 False，但 AI 回复明确提到转接人工，则强制纠正
        if not result.should_escalate and detect_escalation(ai_reply):
            result.should_escalate = True
            if result.reason_code == "none":
                code, label = identify_reason(user_message)
                result.reason_code = code  # type: ignore[assignment]
                result.reason_label = label

        logger.debug(f"LLM 意图识别成功 | should_escalate: {result.should_escalate} | reason: {result.reason_code}")
        return {
            "should_escalate": result.should_escalate,
            "reason": result.reason_code,
            "reason_label": result.reason_label,
        }

    except Exception as e:
        logger.warning(f"LLM 意图识别失败，回退到关键词匹配: {e}")
        # 降级逻辑
        should_escalate = detect_escalation(ai_reply)
        reason, reason_label = identify_reason(user_message) if should_escalate else ("none", "无")
        return {
            "should_escalate": should_escalate,
            "reason": reason,
            "reason_label": reason_label,
        }
