"""
事前风控模块

在订单提交前进行风险检查，拦截不合规的订单。

风控规则：
- 仓位限制（单票、总仓位）
- 订单大小限制
- 黑名单/白名单
- 交易时间检查
- 资金充足性
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==============================================
# 风控检查结果
# ==============================================

class RiskCheckResult:
    """风控检查结果"""

    def __init__(
        self,
        passed: bool,
        rule_name: str = "",
        message: str = "",
        severity: str = "WARNING"
    ):
        self.passed = passed
        self.rule_name = rule_name
        self.message = message
        self.severity = severity  # WARNING, ERROR, CRITICAL

    def __bool__(self) -> bool:
        return self.passed


# ==============================================
# 风控规则基类
# ==============================================

class PreTradeRule:
    """
    事前风控规则基类

    所有风控规则都需要继承此类。
    """

    rule_id: str = "base"
    rule_name: str = "基础规则"
    description: str = ""
    severity: str = "WARNING"

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"RiskRule.{self.rule_id}")

    def check(self, order: Dict[str, Any], portfolio: Dict[str, Any]) -> RiskCheckResult:
        """
        执行风控检查

        Args:
            order: 订单信息
            portfolio: 投资组合信息

        Returns:
            检查结果
        """
        raise NotImplementedError


# ==============================================
# 具体风控规则
# ==============================================

class MaxPositionRule(PreTradeRule):
    """
    最大持仓限制

    限制单只股票的持仓比例。
    """

    rule_id = "max_position"
    rule_name = "单票持仓限制"

    def __init__(self, max_ratio: Decimal = Decimal("0.10")):
        super().__init__({"max_ratio": max_ratio})
        self.max_ratio = max_ratio

    def check(self, order: Dict, portfolio: Dict) -> RiskCheckResult:
        symbol = order.get("symbol")
        order_value = Decimal(str(order.get("price", 0))) * order.get("quantity", 0)
        total_value = Decimal(str(portfolio.get("total_value", 0)))

        if total_value <= 0:
            return RiskCheckResult(True, self.rule_name)

        # 计算当前持仓 + 新订单的比例
        current_position = Decimal(str(portfolio.get("positions", {}).get(symbol, 0)))
        new_position_value = current_position + order_value
        position_ratio = new_position_value / total_value

        if position_ratio > self.max_ratio:
            return RiskCheckResult(
                False,
                self.rule_name,
                f"单票持仓比例 {float(position_ratio)*100:.2f}% 超过限制 {float(self.max_ratio)*100:.2f}%",
                self.severity
            )

        return RiskCheckResult(True, self.rule_name)


class MaxOrderSizeRule(PreTradeRule):
    """
    最大订单限制

    限制单笔订单的金额或数量。
    """

    rule_id = "max_order_size"
    rule_name = "订单大小限制"

    def __init__(
        self,
        max_value: Decimal = Decimal("1000000"),
        max_quantity: int = 100000
    ):
        super().__init__({
            "max_value": max_value,
            "max_quantity": max_quantity
        })
        self.max_value = max_value
        self.max_quantity = max_quantity

    def check(self, order: Dict, portfolio: Dict) -> RiskCheckResult:
        order_value = Decimal(str(order.get("price", 0))) * order.get("quantity", 0)
        quantity = order.get("quantity", 0)

        if order_value > self.max_value:
            return RiskCheckResult(
                False,
                self.rule_name,
                f"订单金额 {float(order_value):.2f} 超过限制 {float(self.max_value):.2f}",
                self.severity
            )

        if quantity > self.max_quantity:
            return RiskCheckResult(
                False,
                self.rule_name,
                f"订单数量 {quantity} 超过限制 {self.max_quantity}",
                self.severity
            )

        return RiskCheckResult(True, self.rule_name)


class BlacklistRule(PreTradeRule):
    """
    黑名单规则

    禁止交易特定股票。
    """

    rule_id = "blacklist"
    rule_name = "黑名单检查"
    severity = "ERROR"

    def __init__(self, blacklist: List[str] = None):
        super().__init__({"blacklist": blacklist or []})
        self.blacklist = set(blacklist or [])

    def add_symbol(self, symbol: str) -> None:
        """添加到黑名单"""
        self.blacklist.add(symbol)

    def remove_symbol(self, symbol: str) -> None:
        """从黑名单移除"""
        self.blacklist.discard(symbol)

    def check(self, order: Dict, portfolio: Dict) -> RiskCheckResult:
        symbol = order.get("symbol", "")

        if symbol in self.blacklist:
            return RiskCheckResult(
                False,
                self.rule_name,
                f"股票 {symbol} 在黑名单中，禁止交易",
                self.severity
            )

        return RiskCheckResult(True, self.rule_name)


class TradingHoursRule(PreTradeRule):
    """
    交易时间检查

    只允许在交易时段下单。
    """

    rule_id = "trading_hours"
    rule_name = "交易时间检查"
    severity = "ERROR"

    def __init__(
        self,
        trading_hours: List[tuple] = None
    ):
        # A股交易时间：9:30-11:30, 13:00-15:00
        default_hours = [
            (time(9, 30), time(11, 30)),
            (time(13, 0), time(15, 0)),
        ]
        super().__init__({"trading_hours": trading_hours or default_hours})
        self.trading_hours = trading_hours or default_hours

    def check(self, order: Dict, portfolio: Dict) -> RiskCheckResult:
        now = datetime.now().time()

        for start, end in self.trading_hours:
            if start <= now <= end:
                return RiskCheckResult(True, self.rule_name)

        return RiskCheckResult(
            False,
            self.rule_name,
            f"当前时间 {now.strftime('%H:%M:%S')} 不在交易时段内",
            self.severity
        )


class CashSufficiencyRule(PreTradeRule):
    """
    资金充足性检查

    确保有足够的资金进行买入。
    """

    rule_id = "cash_sufficiency"
    rule_name = "资金充足性检查"

    def __init__(self, buffer_ratio: Decimal = Decimal("1.01")):
        super().__init__({"buffer_ratio": buffer_ratio})
        self.buffer_ratio = buffer_ratio  # 预留缓冲

    def check(self, order: Dict, portfolio: Dict) -> RiskCheckResult:
        if order.get("side") != "BUY":
            return RiskCheckResult(True, self.rule_name)

        order_value = Decimal(str(order.get("price", 0))) * order.get("quantity", 0)
        required_cash = order_value * self.buffer_ratio
        available_cash = Decimal(str(portfolio.get("cash", 0)))

        if available_cash < required_cash:
            return RiskCheckResult(
                False,
                self.rule_name,
                f"可用资金 {float(available_cash):.2f} 不足，需要 {float(required_cash):.2f}",
                self.severity
            )

        return RiskCheckResult(True, self.rule_name)


# ==============================================
# 事前风控引擎
# ==============================================

class PreTradeRiskEngine:
    """
    事前风控引擎

    在订单提交前执行所有风控检查。

    使用示例：
        engine = PreTradeRiskEngine()

        # 添加规则
        engine.add_rule(MaxPositionRule(Decimal("0.10")))
        engine.add_rule(BlacklistRule(["000001.SZ"]))

        # 检查订单
        result = engine.validate(order, portfolio)
        if not result.passed:
            print(f"风控拦截: {result.message}")
    """

    def __init__(self):
        """初始化风控引擎"""
        self._rules: List[PreTradeRule] = []
        self._logger = logging.getLogger("PreTradeRiskEngine")

    def add_rule(self, rule: PreTradeRule) -> None:
        """添加风控规则"""
        self._rules.append(rule)
        self._logger.info(f"添加风控规则: {rule.rule_name}")

    def remove_rule(self, rule_id: str) -> bool:
        """移除风控规则"""
        for i, rule in enumerate(self._rules):
            if rule.rule_id == rule_id:
                self._rules.pop(i)
                self._logger.info(f"移除风控规则: {rule_id}")
                return True
        return False

    def validate(
        self,
        order: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> RiskCheckResult:
        """
        验证订单

        Args:
            order: 订单信息
            portfolio: 投资组合信息

        Returns:
            检查结果（只有所有规则都通过才返回通过）
        """
        for rule in self._rules:
            result = rule.check(order, portfolio)

            if not result.passed:
                self._logger.warning(
                    f"风控拦截: {rule.rule_name} - {result.message}"
                )
                return result

        return RiskCheckResult(True, "全部通过", "所有风控检查通过")

    def get_rules(self) -> List[PreTradeRule]:
        """获取所有规则"""
        return self._rules.copy()


# ==============================================
# 默认风控引擎
# ==============================================

def create_default_engine() -> PreTradeRiskEngine:
    """创建默认风控引擎"""
    engine = PreTradeRiskEngine()

    # 添加默认规则
    engine.add_rule(MaxPositionRule(Decimal("0.10")))
    engine.add_rule(MaxOrderSizeRule(Decimal("1000000"), 100000))
    engine.add_rule(TradingHoursRule())
    engine.add_rule(CashSufficiencyRule())

    return engine


# 默认引擎实例
default_engine = create_default_engine()
