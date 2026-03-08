"""
订单状态机 — L2 企业化: 严格的订单状态流转控制。

所有订单状态变更必须通过此模块执行，禁止直接赋值 order.status = "xxx"。
非法状态跳转会被拒绝并记录告警日志，防止数据错乱。

合法状态流转图:
    consulting → wechat_pending → req_fixed → generating → processing → awaiting_review → shipped
                                                    ↘ failed (任何 generating/processing 阶段都可能失败)
    failed → generating (允许重试)
"""

from __future__ import annotations

from datetime import datetime

from src.models.enums import OrderStatus
from src.utils.logger import logger

# ===== 合法状态转移表 =====
# key: 当前状态, value: 可转移到的目标状态集合
VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CONSULTING: {OrderStatus.WECHAT_PENDING},
    OrderStatus.WECHAT_PENDING: {OrderStatus.REQ_FIXED, OrderStatus.FAILED},
    OrderStatus.REQ_FIXED: {OrderStatus.GENERATING, OrderStatus.FAILED},
    OrderStatus.GENERATING: {OrderStatus.PROCESSING, OrderStatus.FAILED},
    OrderStatus.PROCESSING: {OrderStatus.AWAITING_REVIEW, OrderStatus.FAILED},
    OrderStatus.AWAITING_REVIEW: {OrderStatus.SHIPPED, OrderStatus.FAILED},
    OrderStatus.SHIPPED: set(),  # 终态，不可变
    OrderStatus.FAILED: {OrderStatus.GENERATING},  # 失败后允许重试
}


class InvalidTransitionError(Exception):
    """非法状态转换异常"""

    def __init__(self, order_sn: str, current: OrderStatus, target: OrderStatus):
        self.order_sn = order_sn
        self.current = current
        self.target = target
        super().__init__(
            f"非法状态跳转 | order: {order_sn} | {current.value} → {target.value} | "
            f"合法目标: {[s.value for s in VALID_TRANSITIONS.get(current, set())]}"
        )


def transition_order(order, target_status: OrderStatus, *, db=None, error_message: str | None = None) -> bool:
    """
    安全地将订单状态转换到目标状态。

    Args:
        order: SQLAlchemy Order 对象
        target_status: 目标状态
        db: 可选的数据库 session（传入则自动 commit）
        error_message: 失败时的错误信息（仅 target=FAILED 时有效）

    Returns:
        True 表示转换成功

    Raises:
        InvalidTransitionError: 非法状态跳转
    """
    current = OrderStatus(order.status)
    valid_targets = VALID_TRANSITIONS.get(current, set())

    if target_status not in valid_targets:
        err = InvalidTransitionError(order.order_sn, current, target_status)
        logger.error(str(err))
        raise err

    old_status = order.status
    order.status = target_status.value
    order.updated_at = datetime.now()

    # 设置特殊时间戳
    if target_status == OrderStatus.GENERATING:
        order.generated_at = datetime.now()
    elif target_status == OrderStatus.SHIPPED:
        order.shipped_at = datetime.now()

    # 失败时记录错误信息
    if target_status == OrderStatus.FAILED and error_message:
        order.error_message = error_message

    logger.info(f"状态机 | ✅ {old_status} → {target_status.value} | order: {order.order_sn}")

    if db is not None:
        db.commit()

    return True


def can_transition(order, target_status: OrderStatus) -> bool:
    """检查状态转换是否合法（不执行，仅查询）"""
    current = OrderStatus(order.status)
    return target_status in VALID_TRANSITIONS.get(current, set())
