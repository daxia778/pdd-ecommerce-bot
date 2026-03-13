"""
升级信号检测器 - 通过 LLM 轻量级意图分类判断是否触发人工升级。
同时识别升级原因标签，供管理员快速分类处理，并保留关键词作为兜底降级策略。

P1-Root-Cause-Sweep: 使用 Pydantic BaseModel 校验 LLM JSON 输出，
防止 LLM 幻觉产生不合法字段值导致下游异常。
"""

import json
import os
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
    (["加急", "当天", "今晚", "几小时内", "马上要"], "urgent", "紧急交付"),
    (["便宜", "打折", "优惠", "降价", "少一点", "能不能低", "砍价"], "bargain", "价格谈判"),
    (["投诉", "骗", "差评", "退款", "举报", "不满意", "维权", "消协", "12315"], "complaint", "投诉纠纷"),
    (["万", "高端", "定制模板", "多套", "大项目", "长期合作", "几十套", "批发"], "large_order", "大额/长期订单"),
    (["线下", "上门", "面谈", "见面", "现场"], "offline", "线下服务"),
]

# 读取外部隔离的意图分类 Prompt（安全加载，文件缺失不会导致崩溃）
PROMPT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "prompts"
)
INTENT_PROMPT_PATH = os.path.join(PROMPT_DIR, "intent_classification", "prompt.md")

_FALLBACK_INTENT_PROMPT = (
    "你是一个意图分类器。根据买家消息和AI回复，判断是否需要转人工。"
    '输出JSON: {"should_escalate": bool, "reason_code": "urgent|bargain|complaint|large_order|offline|other|none", "reason_label": "中文描述"}'
)

try:
    with open(INTENT_PROMPT_PATH, encoding="utf-8") as f:
        INTENT_SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    logger.warning(f"⚠️ 意图分类 Prompt 文件不存在: {INTENT_PROMPT_PATH}，使用内置兜底 Prompt")
    INTENT_SYSTEM_PROMPT = _FALLBACK_INTENT_PROMPT


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
    综合分析：判断是否需要升级 + 升级原因。

    性能优化策略（Keyword-First）：
    1. 先用关键词快速判断 — 如果 AI 回复明确触发了转人工话术，直接返回（~0ms）
    2. 如果买家消息命中高置信度关键词（投诉/加急等），也直接返回（~0ms）
    3. 只有在「关键词无法确定」的模糊边界情况下，才调用 LLM 做精准判断（~1.5s）

    这样 80%+ 的普通对话可以完全跳过第二次 LLM 调用。
    """
    # ── 快速路径 1：AI 回复中已有转人工话术 → 必须升级 ──
    if detect_escalation(ai_reply):
        reason_code, reason_label = identify_reason(user_message)
        logger.debug(f"升级检测(关键词快速命中-AI回复) | reason: {reason_code}")
        return {"should_escalate": True, "reason": reason_code, "reason_label": reason_label}

    # ── 快速路径 2：买家消息命中高置信度关键词 → 直接升级 ──
    # 只对「投诉/纠纷」类高置信度关键词做快速判定，避免误判
    HIGH_CONFIDENCE_KEYWORDS = ["投诉", "骗", "差评", "退款", "举报", "维权", "消协", "12315", "垃圾", "报警"]
    if any(kw in user_message for kw in HIGH_CONFIDENCE_KEYWORDS):
        reason_code, reason_label = identify_reason(user_message)
        logger.debug(f"升级检测(关键词快速命中-投诉) | reason: {reason_code}")
        return {"should_escalate": True, "reason": reason_code, "reason_label": reason_label}

    # ── 快速路径 3：普通对话（无任何升级信号）→ 直接返回不升级 ──
    # 只有在买家消息命中了低置信度关键词（加急/便宜等）时才需要 LLM 精判
    has_ambiguous_signal = False
    for keywords, _code, _label in REASON_RULES:
        if any(kw in user_message for kw in keywords):
            has_ambiguous_signal = True
            break

    if not has_ambiguous_signal:
        # 完全没有任何升级信号 → 跳过 LLM，直接返回（~0ms）
        return {"should_escalate": False, "reason": "none", "reason_label": "无"}

    # ── 慢速路径：模糊信号，需要 LLM 精准判定 ──
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
            data = json.loads(raw_json)
            result = EscalationResult.model_validate(data)

        logger.debug(f"LLM 意图识别成功 | should_escalate: {result.should_escalate} | reason: {result.reason_code}")
        return {
            "should_escalate": result.should_escalate,
            "reason": result.reason_code,
            "reason_label": result.reason_label,
        }

    except Exception as e:
        logger.warning(f"LLM 意图识别失败，回退到安全模式(不升级): {e}")
        # 降级兜底：改为不升级（避免因 LLM 故障导致大量误升级）
        return {
            "should_escalate": False,
            "reason": "none",
            "reason_label": "无",
        }
