"""
业务状态枚举定义 — 消除 Magic Strings，让类型检查器和 IDE 帮你在编码阶段捕获拼写错误。

P1-Fix-1: 集中管理所有业务状态常量。
"""

from enum import Enum


class OrderStatus(str, Enum):
    """PPT 订单状态机"""

    CONSULTING = "consulting"  # 咨询中
    WECHAT_PENDING = "wechat_pending"  # 等待微信二维码
    REQ_FIXED = "req_fixed"  # 需求已确认
    GENERATING = "generating"  # 自动生成中
    PROCESSING = "processing"  # 人工处理中
    AWAITING_REVIEW = "awaiting_review"  # 待审核
    SHIPPED = "shipped"  # 已交付
    FAILED = "failed"  # 生成失败


class SessionStatus(str, Enum):
    """会话状态"""

    ACTIVE = "active"
    ESCALATED = "escalated"
    CLOSED = "closed"


class EscalationStatus(str, Enum):
    """升级记录状态"""

    PENDING = "pending"
    CLAIMED = "claimed"
    RESOLVED = "resolved"


class EscalationReason(str, Enum):
    """升级原因标签"""

    URGENT = "urgent"
    BARGAIN = "bargain"
    COMPLAINT = "complaint"
    LARGE_ORDER = "large_order"
    OFFLINE = "offline"
    OTHER = "other"
    NONE = "none"


class OrderType(str, Enum):
    """订单类型"""

    SINGLE_PAGE = "single_page"  # 1-3页小单
    STANDARD = "standard"  # 标准单
    LARGE = "large"  # 大单


class Urgency(str, Enum):
    """紧急度"""

    NORMAL = "normal"
    URGENT = "urgent"
    VERY_URGENT = "very_urgent"


class MessageRole(str, Enum):
    """消息角色"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
