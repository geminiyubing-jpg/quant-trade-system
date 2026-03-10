"""
订单状态机模块

提供严格的订单生命周期管理：
- 状态转换验证
- 状态变更事件
- 状态历史追踪
- 异常状态处理

状态转换图：
PENDING -> SUBMITTED -> PARTIAL_FILLED -> FILLED
       |           -> CANCELED
       |           -> REJECTED
       -> REJECTED
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==============================================
# 订单状态枚举
# ==============================================

class OrderState(str, Enum):
    """订单状态"""
    # 初始状态
    PENDING = "PENDING"                     # 待提交

    # 提交后状态
    SUBMITTED = "SUBMITTED"                 # 已提交
    ACCEPTED = "ACCEPTED"                   # 已接受
    REJECTED = "REJECTED"                   # 已拒绝

    # 执行中状态
    PARTIAL_FILLED = "PARTIAL_FILLED"       # 部分成交
    FILLED = "FILLED"                       # 完全成交

    # 终止状态
    CANCELED = "CANCELED"                   # 已撤销
    EXPIRED = "EXPIRED"                     # 已过期
    FAILED = "FAILED"                       # 失败


# ==============================================
# 状态转换配置
# ==============================================

# 定义合法的状态转换
VALID_TRANSITIONS: Dict[OrderState, List[OrderState]] = {
    OrderState.PENDING: [
        OrderState.SUBMITTED,
        OrderState.CANCELED,
        OrderState.REJECTED,
        OrderState.FAILED,
    ],
    OrderState.SUBMITTED: [
        OrderState.ACCEPTED,
        OrderState.REJECTED,
        OrderState.CANCELED,
        OrderState.PARTIAL_FILLED,
        OrderState.FILLED,
        OrderState.FAILED,
    ],
    OrderState.ACCEPTED: [
        OrderState.PARTIAL_FILLED,
        OrderState.FILLED,
        OrderState.CANCELED,
        OrderState.EXPIRED,
        OrderState.FAILED,
    ],
    OrderState.PARTIAL_FILLED: [
        OrderState.FILLED,
        OrderState.CANCELED,
        OrderState.FAILED,
    ],
    # 终止状态：不允许再转换
    OrderState.FILLED: [],
    OrderState.CANCELED: [],
    OrderState.REJECTED: [],
    OrderState.EXPIRED: [],
    OrderState.FAILED: [],
}

# 终止状态集合
TERMINAL_STATES = {
    OrderState.FILLED,
    OrderState.CANCELED,
    OrderState.REJECTED,
    OrderState.EXPIRED,
    OrderState.FAILED,
}


# ==============================================
# 状态变更记录
# ==============================================

@dataclass
class StateTransition:
    """状态变更记录"""
    from_state: OrderState
    to_state: OrderState
    timestamp: datetime
    reason: str = ""
    operator: str = ""           # 操作者（系统/用户）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderStateInfo:
    """订单状态信息"""
    order_id: str
    current_state: OrderState
    previous_state: Optional[OrderState] = None
    state_history: List[StateTransition] = field(default_factory=list)
    created_at: datetime = None
    updated_at: datetime = None

    # 成交信息
    total_quantity: int = 0
    filled_quantity: int = 0
    filled_price: Decimal = Decimal("0")

    # 错误信息
    error_message: str = ""
    reject_reason: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def is_terminal(self) -> bool:
        """是否处于终止状态"""
        return self.current_state in TERMINAL_STATES

    @property
    def is_active(self) -> bool:
        """是否仍然活跃"""
        return self.current_state not in TERMINAL_STATES

    @property
    def fill_rate(self) -> Decimal:
        """成交比例"""
        if self.total_quantity > 0:
            return Decimal(self.filled_quantity) / Decimal(self.total_quantity)
        return Decimal("0")


# ==============================================
# 订单状态机
# ==============================================

class OrderStateMachine:
    """
    订单状态机

    管理订单的完整生命周期，确保状态转换合法。

    功能：
    - 状态转换验证
    - 状态变更回调
    - 状态历史追踪
    - 异常处理

    使用示例：
        sm = OrderStateMachine()

        # 注册订单
        sm.register_order("ORDER_001", 1000)

        # 状态转换
        sm.transition("ORDER_001", OrderState.SUBMITTED)
        sm.transition("ORDER_001", OrderState.PARTIAL_FILLED, filled_quantity=500)

        # 查询状态
        info = sm.get_state_info("ORDER_001")
        print(f"当前状态: {info.current_state}, 成交率: {info.fill_rate}")
    """

    def __init__(self):
        """初始化状态机"""
        self._orders: Dict[str, OrderStateInfo] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._logger = logging.getLogger("OrderStateMachine")

    # ==========================================
    # 订单注册
    # ==========================================

    def register_order(
        self,
        order_id: str,
        total_quantity: int,
        initial_state: OrderState = OrderState.PENDING
    ) -> OrderStateInfo:
        """
        注册新订单

        Args:
            order_id: 订单 ID
            total_quantity: 总数量
            initial_state: 初始状态

        Returns:
            订单状态信息
        """
        if order_id in self._orders:
            raise ValueError(f"订单已存在: {order_id}")

        info = OrderStateInfo(
            order_id=order_id,
            current_state=initial_state,
            total_quantity=total_quantity,
        )

        self._orders[order_id] = info
        self._logger.info(f"注册订单: {order_id}, 数量: {total_quantity}")

        return info

    def unregister_order(self, order_id: str) -> bool:
        """
        注销订单

        Args:
            order_id: 订单 ID

        Returns:
            是否成功
        """
        if order_id in self._orders:
            del self._orders[order_id]
            self._logger.info(f"注销订单: {order_id}")
            return True
        return False

    # ==========================================
    # 状态查询
    # ==========================================

    def get_state(self, order_id: str) -> Optional[OrderState]:
        """
        获取订单状态

        Args:
            order_id: 订单 ID

        Returns:
            订单状态或 None
        """
        info = self._orders.get(order_id)
        return info.current_state if info else None

    def get_state_info(self, order_id: str) -> Optional[OrderStateInfo]:
        """
        获取订单状态信息

        Args:
            order_id: 订单 ID

        Returns:
            状态信息或 None
        """
        return self._orders.get(order_id)

    def is_terminal(self, order_id: str) -> bool:
        """检查是否处于终止状态"""
        info = self._orders.get(order_id)
        return info.is_terminal if info else True

    def is_active(self, order_id: str) -> bool:
        """检查是否仍然活跃"""
        info = self._orders.get(order_id)
        return info.is_active if info else False

    def get_valid_transitions(self, order_id: str) -> List[OrderState]:
        """
        获取合法的下一状态

        Args:
            order_id: 订单 ID

        Returns:
            可转换的状态列表
        """
        info = self._orders.get(order_id)
        if info is None:
            return []

        return VALID_TRANSITIONS.get(info.current_state, [])

    # ==========================================
    # 状态转换
    # ==========================================

    def transition(
        self,
        order_id: str,
        new_state: OrderState,
        reason: str = "",
        operator: str = "system",
        **kwargs
    ) -> bool:
        """
        状态转换

        Args:
            order_id: 订单 ID
            new_state: 新状态
            reason: 原因
            operator: 操作者
            **kwargs: 额外参数（如 filled_quantity）

        Returns:
            是否成功
        """
        info = self._orders.get(order_id)
        if info is None:
            self._logger.error(f"订单不存在: {order_id}")
            return False

        old_state = info.current_state

        # 验证转换是否合法
        if not self._validate_transition(old_state, new_state):
            self._logger.error(
                f"非法状态转换: {order_id} {old_state.value} -> {new_state.value}"
            )
            return False

        # 执行转换
        info.previous_state = old_state
        info.current_state = new_state
        info.updated_at = datetime.now()

        # 更新成交信息
        if "filled_quantity" in kwargs:
            info.filled_quantity = kwargs["filled_quantity"]
        if "filled_price" in kwargs:
            info.filled_price = kwargs["filled_price"]

        # 更新错误信息
        if "error_message" in kwargs:
            info.error_message = kwargs["error_message"]
        if "reject_reason" in kwargs:
            info.reject_reason = kwargs["reject_reason"]

        # 记录状态变更
        transition_record = StateTransition(
            from_state=old_state,
            to_state=new_state,
            timestamp=datetime.now(),
            reason=reason,
            operator=operator,
            metadata=kwargs,
        )
        info.state_history.append(transition_record)

        self._logger.info(
            f"订单状态变更: {order_id} {old_state.value} -> {new_state.value}"
            + (f" ({reason})" if reason else "")
        )

        # 触发回调
        self._trigger_callbacks(order_id, old_state, new_state, info)

        return True

    def _validate_transition(
        self,
        from_state: OrderState,
        to_state: OrderState
    ) -> bool:
        """
        验证状态转换是否合法

        Args:
            from_state: 原状态
            to_state: 目标状态

        Returns:
            是否合法
        """
        valid_next_states = VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_next_states

    # ==========================================
    # 便捷方法
    # ==========================================

    def submit(self, order_id: str) -> bool:
        """提交订单"""
        return self.transition(order_id, OrderState.SUBMITTED, "订单已提交")

    def accept(self, order_id: str) -> bool:
        """接受订单"""
        return self.transition(order_id, OrderState.ACCEPTED, "订单已接受")

    def reject(self, order_id: str, reason: str = "") -> bool:
        """拒绝订单"""
        return self.transition(
            order_id, OrderState.REJECTED,
            reason or "订单被拒绝",
            reject_reason=reason
        )

    def partial_fill(
        self,
        order_id: str,
        filled_quantity: int,
        filled_price: Decimal
    ) -> bool:
        """部分成交"""
        return self.transition(
            order_id, OrderState.PARTIAL_FILLED,
            f"部分成交 {filled_quantity}",
            filled_quantity=filled_quantity,
            filled_price=filled_price,
        )

    def fill(
        self,
        order_id: str,
        filled_quantity: int,
        filled_price: Decimal
    ) -> bool:
        """完全成交"""
        return self.transition(
            order_id, OrderState.FILLED,
            "订单完全成交",
            filled_quantity=filled_quantity,
            filled_price=filled_price,
        )

    def cancel(self, order_id: str, reason: str = "") -> bool:
        """撤销订单"""
        return self.transition(
            order_id, OrderState.CANCELED,
            reason or "订单已撤销"
        )

    def fail(self, order_id: str, error_message: str = "") -> bool:
        """订单失败"""
        return self.transition(
            order_id, OrderState.FAILED,
            "订单执行失败",
            error_message=error_message
        )

    def expire(self, order_id: str) -> bool:
        """订单过期"""
        return self.transition(order_id, OrderState.EXPIRED, "订单已过期")

    # ==========================================
    # 回调管理
    # ==========================================

    def on_state_change(
        self,
        callback: Callable[[str, OrderState, OrderState, OrderStateInfo], None]
    ) -> None:
        """
        注册状态变更回调

        Args:
            callback: 回调函数 (order_id, old_state, new_state, info) -> None
        """
        if "state_change" not in self._callbacks:
            self._callbacks["state_change"] = []
        self._callbacks["state_change"].append(callback)

    def _trigger_callbacks(
        self,
        order_id: str,
        old_state: OrderState,
        new_state: OrderState,
        info: OrderStateInfo
    ) -> None:
        """触发状态变更回调"""
        callbacks = self._callbacks.get("state_change", [])
        for callback in callbacks:
            try:
                callback(order_id, old_state, new_state, info)
            except Exception as e:
                self._logger.error(f"回调执行失败: {e}")

    # ==========================================
    # 批量操作
    # ==========================================

    def batch_transition(
        self,
        order_ids: List[str],
        new_state: OrderState,
        reason: str = ""
    ) -> Dict[str, bool]:
        """
        批量状态转换

        Args:
            order_ids: 订单 ID 列表
            new_state: 目标状态
            reason: 原因

        Returns:
            {order_id: 是否成功}
        """
        results = {}
        for order_id in order_ids:
            results[order_id] = self.transition(order_id, new_state, reason)
        return results

    def cancel_all_active(self, reason: str = "批量撤销") -> List[str]:
        """
        撤销所有活跃订单

        Args:
            reason: 原因

        Returns:
            被撤销的订单 ID 列表
        """
        cancelled = []
        for order_id, info in self._orders.items():
            if info.is_active:
                if self.cancel(order_id, reason):
                    cancelled.append(order_id)
        return cancelled

    # ==========================================
    # 统计和监控
    # ==========================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取状态统计

        Returns:
            统计信息
        """
        state_counts = {}
        for state in OrderState:
            state_counts[state.value] = 0

        for info in self._orders.values():
            state_counts[info.current_state.value] += 1

        return {
            "total_orders": len(self._orders),
            "by_state": state_counts,
            "active_orders": sum(1 for i in self._orders.values() if i.is_active),
            "terminal_orders": sum(1 for i in self._orders.values() if i.is_terminal),
        }

    def get_history(self, order_id: str) -> List[StateTransition]:
        """
        获取状态变更历史

        Args:
            order_id: 订单 ID

        Returns:
            状态变更记录列表
        """
        info = self._orders.get(order_id)
        return info.state_history if info else []

    def clear_terminal_orders(self) -> int:
        """
        清除已终止的订单

        Returns:
            清除的订单数量
        """
        to_remove = [
            order_id for order_id, info in self._orders.items()
            if info.is_terminal
        ]

        for order_id in to_remove:
            del self._orders[order_id]

        if to_remove:
            self._logger.info(f"清除了 {len(to_remove)} 个已终止订单")

        return len(to_remove)


# ==============================================
# 全局状态机实例
# ==============================================

default_state_machine = OrderStateMachine()
