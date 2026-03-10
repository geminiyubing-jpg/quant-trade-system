"""
订单路由模块

提供智能订单路由功能：
- 多通道管理（券商、交易所）
- 路由规则引擎
- 最优通道选择
- 故障转移和负载均衡

设计目标：
- 最优执行价格
- 最小滑点
- 高可用性
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import Decimal
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


# ==============================================
# 枚举类型
# ==============================================

class BrokerType(str, Enum):
    """券商/通道类型"""
    SIMULATED = "simulated"       # 模拟通道
    CTP = "ctp"                   # CTP 期货
    XTP = "xtp"                   # XTP 证券
    COMSTAR = "comstar"           # ComStar 债券
    BINANCE = "binance"           # 币安
    OKX = "okx"                   # OKX


class OrderType(str, Enum):
    """订单类型"""
    MARKET = "MARKET"             # 市价单
    LIMIT = "LIMIT"               # 限价单
    STOP = "STOP"                 # 止损单
    STOP_LIMIT = "STOP_LIMIT"     # 止损限价单
    ICEBERG = "ICEBERG"           # 冰山单
    TWAP = "TWAP"                 # 时间加权均价
    VWAP = "VWAP"                 # 成交量加权均价


class RoutingPriority(str, Enum):
    """路由优先级策略"""
    PRICE = "price"               # 价格优先
    SPEED = "speed"               # 速度优先
    COST = "cost"                 # 成本优先
    RELIABILITY = "reliability"   # 可靠性优先


# ==============================================
# 数据类
# ==============================================

@dataclass
class BrokerInfo:
    """券商/通道信息"""
    broker_id: str                        # 券商 ID
    broker_type: BrokerType               # 券商类型
    name: str                             # 券商名称
    is_available: bool = True             # 是否可用
    supported_markets: List[str] = field(default_factory=list)  # 支持的市场
    supported_order_types: List[OrderType] = field(default_factory=list)  # 支持的订单类型

    # 性能指标
    avg_latency_ms: int = 0               # 平均延迟（毫秒）
    success_rate: Decimal = Decimal("1")  # 成功率
    commission_rate: Decimal = Decimal("0")  # 佣金率

    # 限制
    max_order_size: int = 0               # 最大单笔订单量
    max_daily_orders: int = 0             # 每日最大订单数
    current_daily_orders: int = 0         # 当日已下订单数

    # 权重（用于路由决策）
    priority_weight: int = 0              # 优先级权重


@dataclass
class RoutingRule:
    """
    路由规则

    定义订单如何被路由到特定通道。
    """
    rule_id: str                           # 规则 ID
    name: str                              # 规则名称
    description: str = ""                  # 规则描述
    priority: int = 0                      # 规则优先级（数值越大优先级越高）
    is_active: bool = True                 # 是否激活

    # 条件
    market: Optional[str] = None           # 市场过滤（如 "A股", "期货"）
    symbol_pattern: Optional[str] = None   # 股票代码模式（如 "000*"）
    order_type: Optional[OrderType] = None # 订单类型过滤
    min_quantity: Optional[int] = None     # 最小数量
    max_quantity: Optional[int] = None     # 最大数量

    # 动作
    preferred_brokers: List[str] = field(default_factory=list)  # 首选券商（按优先级排序）
    excluded_brokers: List[str] = field(default_factory=list)   # 排除的券商
    fallback_brokers: List[str] = field(default_factory=list)   # 备用券商

    # 时间条件
    valid_start_time: Optional[time] = None  # 有效开始时间
    valid_end_time: Optional[time] = None    # 有效结束时间

    def matches(self, order: 'Order') -> bool:
        """
        检查订单是否匹配此规则

        Args:
            order: 订单对象

        Returns:
            是否匹配
        """
        if not self.is_active:
            return False

        # 检查市场
        if self.market and hasattr(order, 'market'):
            if order.market != self.market:
                return False

        # 检查股票代码模式
        if self.symbol_pattern:
            import fnmatch
            if not fnmatch.fnmatch(order.symbol, self.symbol_pattern):
                return False

        # 检查订单类型
        if self.order_type and hasattr(order, 'order_type'):
            if order.order_type != self.order_type:
                return False

        # 检查数量
        if self.min_quantity and order.quantity < self.min_quantity:
            return False
        if self.max_quantity and order.quantity > self.max_quantity:
            return False

        # 检查时间
        now = datetime.now().time()
        if self.valid_start_time and now < self.valid_start_time:
            return False
        if self.valid_end_time and now > self.valid_end_time:
            return False

        return True


@dataclass
class RoutingDecision:
    """
    路由决策

    记录订单的路由决策结果。
    """
    order_id: str                         # 订单 ID
    selected_broker: str                  # 选择的券商
    routing_rule: Optional[str] = None    # 匹配的规则 ID
    decision_time: datetime = None        # 决策时间
    reason: str = ""                      # 决策原因
    alternatives: List[str] = field(default_factory=list)  # 备选券商
    confidence: Decimal = Decimal("1")    # 决策置信度


# ==============================================
# 订单路由器
# ==============================================

class OrderRouter:
    """
    订单路由器

    智能选择最优的交易通道执行订单。

    功能：
    - 多通道管理
    - 规则引擎
    - 最优通道选择
    - 故障转移

    使用示例：
        router = OrderRouter()

        # 注册券商
        router.register_broker(BrokerInfo(
            broker_id="xtp_main",
            broker_type=BrokerType.XTP,
            name="XTP主通道",
            ...
        ))

        # 添加路由规则
        router.add_rule(RoutingRule(
            rule_id="large_orders",
            name="大单路由",
            min_quantity=10000,
            preferred_brokers=["xtp_main"],
        ))

        # 路由订单
        decision = router.route_order(order)
    """

    def __init__(
        self,
        default_priority: RoutingPriority = RoutingPriority.PRICE
    ):
        """
        初始化订单路由器

        Args:
            default_priority: 默认路由优先级策略
        """
        self._brokers: Dict[str, BrokerInfo] = {}
        self._rules: List[RoutingRule] = []
        self._default_priority = default_priority
        self._routing_history: List[RoutingDecision] = []
        self._logger = logging.getLogger("OrderRouter")

    # ==========================================
    # 券商管理
    # ==========================================

    def register_broker(self, broker: BrokerInfo) -> None:
        """
        注册券商

        Args:
            broker: 券商信息
        """
        self._brokers[broker.broker_id] = broker
        self._logger.info(f"注册券商: {broker.broker_id} ({broker.name})")

    def unregister_broker(self, broker_id: str) -> bool:
        """
        注销券商

        Args:
            broker_id: 券商 ID

        Returns:
            是否成功
        """
        if broker_id in self._brokers:
            del self._brokers[broker_id]
            self._logger.info(f"注销券商: {broker_id}")
            return True
        return False

    def get_broker(self, broker_id: str) -> Optional[BrokerInfo]:
        """
        获取券商信息

        Args:
            broker_id: 券商 ID

        Returns:
            券商信息或 None
        """
        return self._brokers.get(broker_id)

    def list_brokers(self, available_only: bool = True) -> List[BrokerInfo]:
        """
        列出券商

        Args:
            available_only: 是否只返回可用的券商

        Returns:
            券商列表
        """
        brokers = list(self._brokers.values())
        if available_only:
            brokers = [b for b in brokers if b.is_available]
        return brokers

    def update_broker_status(
        self,
        broker_id: str,
        is_available: bool = None,
        **kwargs
    ) -> bool:
        """
        更新券商状态

        Args:
            broker_id: 券商 ID
            is_available: 是否可用
            **kwargs: 其他要更新的属性

        Returns:
            是否成功
        """
        broker = self._brokers.get(broker_id)
        if broker is None:
            return False

        if is_available is not None:
            broker.is_available = is_available

        for key, value in kwargs.items():
            if hasattr(broker, key):
                setattr(broker, key, value)

        self._logger.info(f"更新券商状态: {broker_id}")
        return True

    # ==========================================
    # 规则管理
    # ==========================================

    def add_rule(self, rule: RoutingRule) -> None:
        """
        添加路由规则

        Args:
            rule: 路由规则
        """
        self._rules.append(rule)
        # 按优先级排序
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        self._logger.info(f"添加路由规则: {rule.rule_id} ({rule.name})")

    def remove_rule(self, rule_id: str) -> bool:
        """
        移除路由规则

        Args:
            rule_id: 规则 ID

        Returns:
            是否成功
        """
        for i, rule in enumerate(self._rules):
            if rule.rule_id == rule_id:
                self._rules.pop(i)
                self._logger.info(f"移除路由规则: {rule_id}")
                return True
        return False

    def get_rules(self) -> List[RoutingRule]:
        """获取所有路由规则"""
        return self._rules.copy()

    # ==========================================
    # 路由决策
    # ==========================================

    def route_order(self, order: 'Order') -> RoutingDecision:
        """
        路由订单

        根据规则和券商状态选择最优通道。

        Args:
            order: 订单对象

        Returns:
            路由决策
        """
        decision_time = datetime.now()

        # 1. 查找匹配的规则
        matched_rule = None
        for rule in self._rules:
            if rule.matches(order):
                matched_rule = rule
                break

        # 2. 获取候选券商
        candidates = self._get_candidate_brokers(order, matched_rule)

        if not candidates:
            # 没有可用券商
            self._logger.error(f"没有可用的券商来路由订单: {order.order_id}")
            return RoutingDecision(
                order_id=order.order_id,
                selected_broker="",
                decision_time=decision_time,
                reason="没有可用的券商",
                confidence=Decimal("0"),
            )

        # 3. 选择最优券商
        selected_broker, alternatives, reason = self._select_best_broker(
            order, candidates, matched_rule
        )

        # 4. 创建路由决策
        decision = RoutingDecision(
            order_id=order.order_id,
            selected_broker=selected_broker,
            routing_rule=matched_rule.rule_id if matched_rule else None,
            decision_time=decision_time,
            reason=reason,
            alternatives=alternatives,
            confidence=Decimal("1") if selected_broker else Decimal("0"),
        )

        # 5. 记录历史
        self._routing_history.append(decision)

        self._logger.info(
            f"路由订单 {order.order_id} -> {selected_broker} "
            f"(规则: {matched_rule.rule_id if matched_rule else '默认'})"
        )

        return decision

    def _get_candidate_brokers(
        self,
        order: 'Order',
        matched_rule: Optional[RoutingRule]
    ) -> List[BrokerInfo]:
        """
        获取候选券商列表

        Args:
            order: 订单对象
            matched_rule: 匹配的规则

        Returns:
            候选券商列表
        """
        # 获取所有可用券商
        available_brokers = [
            b for b in self._brokers.values()
            if b.is_available
        ]

        if not available_brokers:
            return []

        # 过滤支持的订单类型
        if hasattr(order, 'order_type'):
            available_brokers = [
                b for b in available_brokers
                if order.order_type in b.supported_order_types or not b.supported_order_types
            ]

        # 过滤支持的市场
        if hasattr(order, 'market') and order.market:
            available_brokers = [
                b for b in available_brokers
                if order.market in b.supported_markets or not b.supported_markets
            ]

        # 应用规则过滤
        if matched_rule:
            # 排除指定券商
            if matched_rule.excluded_brokers:
                available_brokers = [
                    b for b in available_brokers
                    if b.broker_id not in matched_rule.excluded_brokers
                ]

            # 如果有首选券商且在可用列表中，只保留首选
            if matched_rule.preferred_brokers:
                preferred_available = [
                    b for b in available_brokers
                    if b.broker_id in matched_rule.preferred_brokers
                ]
                if preferred_available:
                    # 按首选顺序排序
                    order_map = {
                        bid: i for i, bid in enumerate(matched_rule.preferred_brokers)
                    }
                    preferred_available.sort(key=lambda b: order_map.get(b.broker_id, 999))
                    return preferred_available

        return available_brokers

    def _select_best_broker(
        self,
        order: 'Order',
        candidates: List[BrokerInfo],
        matched_rule: Optional[RoutingRule]
    ) -> tuple[str, List[str], str]:
        """
        选择最优券商

        Args:
            order: 订单对象
            candidates: 候选券商
            matched_rule: 匹配的规则

        Returns:
            (选中的券商ID, 备选券商列表, 原因)
        """
        if not candidates:
            return "", [], "没有候选券商"

        # 根据优先级策略排序
        if self._default_priority == RoutingPriority.PRICE:
            # 价格优先：选择佣金率最低的
            candidates.sort(key=lambda b: b.commission_rate)
            reason = "佣金率最低"

        elif self._default_priority == RoutingPriority.SPEED:
            # 速度优先：选择延迟最低的
            candidates.sort(key=lambda b: b.avg_latency_ms)
            reason = "延迟最低"

        elif self._default_priority == RoutingPriority.RELIABILITY:
            # 可靠性优先：选择成功率最高的
            candidates.sort(key=lambda b: b.success_rate, reverse=True)
            reason = "成功率最高"

        else:  # COST
            # 成本优先：综合考虑佣金和滑点
            candidates.sort(key=lambda b: b.commission_rate)
            reason = "综合成本最低"

        # 考虑优先级权重
        if any(b.priority_weight > 0 for b in candidates):
            candidates.sort(key=lambda b: b.priority_weight, reverse=True)
            reason = "优先级权重最高"

        selected = candidates[0]
        alternatives = [b.broker_id for b in candidates[1:4]]  # 取前 3 个备选

        return selected.broker_id, alternatives, reason

    # ==========================================
    # 故障转移
    # ==========================================

    def route_with_fallback(
        self,
        order: 'Order',
        max_attempts: int = 3
    ) -> RoutingDecision:
        """
        带故障转移的路由

        如果首选券商不可用，自动切换到备选券商。

        Args:
            order: 订单对象
            max_attempts: 最大尝试次数

        Returns:
            路由决策
        """
        decision = self.route_order(order)

        attempts = 1
        while not decision.selected_broker and attempts < max_attempts:
            # 尝试其他券商
            self._logger.warning(
                f"路由失败，尝试备选券商 ({attempts}/{max_attempts})"
            )
            decision = self.route_order(order)
            attempts += 1

        return decision

    # ==========================================
    # 统计和监控
    # ==========================================

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        获取路由统计

        Returns:
            统计字典
        """
        if not self._routing_history:
            return {
                "total_routings": 0,
                "by_broker": {},
            }

        # 按券商统计
        broker_counts: Dict[str, int] = {}
        for decision in self._routing_history:
            broker_counts[decision.selected_broker] = (
                broker_counts.get(decision.selected_broker, 0) + 1
            )

        return {
            "total_routings": len(self._routing_history),
            "by_broker": broker_counts,
            "recent_decisions": [
                {
                    "order_id": d.order_id,
                    "broker": d.selected_broker,
                    "time": d.decision_time.isoformat(),
                    "reason": d.reason,
                }
                for d in self._routing_history[-10:]
            ],
        }

    def clear_history(self) -> None:
        """清除路由历史"""
        self._routing_history.clear()
        self._logger.info("路由历史已清除")

    def reset_daily_counters(self) -> None:
        """重置每日计数器"""
        for broker in self._brokers.values():
            broker.current_daily_orders = 0
        self._logger.info("券商每日计数器已重置")


# ==============================================
# 全局路由器实例
# ==============================================

# 默认路由器实例
default_router = OrderRouter()
