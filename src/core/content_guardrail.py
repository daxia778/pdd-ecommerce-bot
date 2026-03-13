"""
内容安全门网 — L2 企业化: AI 输出内容安全检查。

在 LLM 回复返回给用户之前，经过此模块进行安全审核。
如果触发红线规则，自动拦截并替换为安全回复 + 触发人工升级。

用法:
    from src.core.content_guardrail import check_ai_output
    result = check_ai_output(reply_text)
    if result.blocked:
        reply = result.safe_reply
        # 触发升级...
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.utils.logger import logger


@dataclass
class GuardrailResult:
    """安全检查结果"""

    blocked: bool = False  # 是否被拦截
    triggered_rules: list[str] = field(default_factory=list)  # 触发的规则名称
    safe_reply: str = ""  # 替换后的安全回复
    original_reply: str = ""  # 原始回复（用于审计日志）


# ===== 红线规则定义 =====
# 每条规则: (规则名, 正则模式, 严重程度)
# severity: "block" = 直接拦截, "warn" = 仅告警不拦截

GUARDRAIL_RULES: list[tuple[str, str, str]] = [
    # === 资损类（直接拦截）===
    (
        "承诺免单",
        r"(免单|免费送|不要钱|不收费|白送|(?<!\d)0\s*元(?!\s*(?:是做不到|做不到|不行|不可以|不可能|没办法|是不行|肯定不行)))",
        "block",
    ),
    ("承诺退款", r"(马上退款|立即退款|全额退款|无条件退款|直接退)", "block"),
    ("虚假承诺", r"(保证.*100%.*满意|100%.*满意|绝对.*满意|保证.*最低价|全网最低价)", "block"),
    ("泄露内部信息", r"(成本价|进货价|利润|内部价|员工价)", "block"),
    # === 合规类（直接拦截）===
    ("绝对化用语", r"(第一品牌|全网第一|最(强|优|佳|棒|牛)的(品牌|产品|公司|店铺|服务商)|NO\.?\s*1)", "block"),
    ("索取隐私", r"(你的(手机号|电话|身份证|银行卡|家庭住址|地址))", "block"),
    # === 竞品类（直接拦截）===
    ("贬低竞品", r"(比.*差|比.*垃圾|千万别.*买|对手|竞品.*不行)", "block"),
    # === 自主定价类（直接拦截）===
    ("自创加急费", r"(加急费|加急.*\+\d+%|\+50%|\+75%|加急.*收费|加急.*加价)", "block"),
    ("自创附加费", r"(设计费|排版费|修改费|服务费|手续费)", "block"),
    ("结构化价格输出", r"(```(json|python|py)|\"日常制作\"\s*[:：]\s*\d|'日常制作'\s*[:：]\s*\d)", "block"),
    # === 情绪类（告警不拦截）===
    ("消极情绪", r"(做不到|没办法|不可能|太难了|搞不定)", "warn"),
    ("推诿客户", r"(不归我管|找别人|跟我没关系|自己看着办)", "block"),
]

# 被拦截时的统一安全回复
DEFAULT_SAFE_REPLY = (
    "亲，感谢您的耐心等待！关于您的问题，我需要跟我们的专业团队确认一下，"
    "马上为您转接人工客服，确保给您最准确的答复哦 😊"
)


def check_ai_output(reply: str) -> GuardrailResult:
    """
    检查 AI 输出是否触发安全红线。

    Args:
        reply: LLM 生成的回复文本

    Returns:
        GuardrailResult 包含是否被拦截、触发的规则、安全替换文本
    """
    result = GuardrailResult(original_reply=reply)

    for rule_name, pattern, severity in GUARDRAIL_RULES:
        match = re.search(pattern, reply)
        if match:
            result.triggered_rules.append(f"[{severity.upper()}] {rule_name}")

            if severity == "block":
                result.blocked = True
                logger.warning(
                    f"🛡️ 内容安全门网 | 拦截 | 规则: {rule_name} | "
                    f"匹配: {match.group()} | "
                    f"原始回复片段: {reply[:100]}..."
                )
            else:
                logger.info(f"🛡️ 内容安全门网 | 告警(未拦截) | 规则: {rule_name}")

    if result.blocked:
        result.safe_reply = DEFAULT_SAFE_REPLY

    return result
