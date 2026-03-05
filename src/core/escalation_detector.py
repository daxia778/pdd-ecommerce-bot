"""
升级信号检测器 - 通过关键词识别 AI 回复是否触发了人工升级。
同时识别升级原因标签，供管理员快速分类处理。
"""
from typing import Tuple

# 升级触发关键词（与 System Prompt 中的转人工话术对应）
ESCALATION_KEYWORDS = [
    "人工客服会尽快",
    "已为您标记",
    "专业客服进一步确认",
    "转接一下人工",
    "人工客服小姐姐",
]

# 升级原因识别规则（消息内容 → 原因标签）
REASON_RULES = [
    # (触发关键词列表, 原因标签, 中文描述)
    (["加急", "今天", "明天", "当天", "今晚", "明日"], "urgent", "紧急交付"),
    (["便宜", "打折", "优惠", "降价", "少一点", "能不能低", "砍价", "最低"], "bargain", "价格谈判"),
    (["投诉", "骗", "差评", "退款", "举报", "不满意", "维权"], "complaint", "投诉纠纷"),
    (["万", "高端", "定制模板", "多套", "大项目", "长期合作"], "large_order", "大额/长期订单"),
    (["线下", "上门", "面谈", "见面", "现场"], "offline", "线下服务"),
]


def detect_escalation(ai_reply: str) -> bool:
    """
    检测 AI 回复是否包含人工升级信号。
    返回 True 表示需要创建升级记录。
    """
    return any(kw in ai_reply for kw in ESCALATION_KEYWORDS)


def identify_reason(user_message: str) -> Tuple[str, str]:
    """
    根据用户原始消息识别升级原因标签。
    返回 (reason_code, reason_label)
    """
    for keywords, code, label in REASON_RULES:
        if any(kw in user_message for kw in keywords):
            return code, label
    return "other", "其他"


def analyze(user_message: str, ai_reply: str) -> dict:
    """
    综合分析：是否需要升级 + 升级原因。
    返回 {
        "should_escalate": bool,
        "reason": str,          # reason code
        "reason_label": str,    # 中文标签
    }
    """
    should_escalate = detect_escalation(ai_reply)
    reason, reason_label = identify_reason(user_message) if should_escalate else ("none", "无")
    return {
        "should_escalate": should_escalate,
        "reason": reason,
        "reason_label": reason_label,
    }
