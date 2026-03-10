"""
==============================================
QuantAI Ecosystem - 风控检查模块
==============================================

实现各种风控检查逻辑。
"""

from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session

from .models import (
    RiskCheckResult,
    RiskCheckType,
    RiskSeverity,
    RiskRuleConfig,
    RiskMetrics,
)


class RiskChecker:
    """风控检查基类"""

    def __init__(self, config: RiskRuleConfig):
        self.config = config

    def check(self, **kwargs) -> RiskCheckResult:
        """执行风控检查"""
        raise NotImplementedError("Subclasses must implement check()")


class PositionLimitChecker(RiskChecker):
    """持仓限制检查"""

    def check(
        self,
        order_value: Decimal,
        total_account_value: Decimal,
        **kwargs
    ) -> RiskCheckResult:
        """
        检查订单是否超过持仓限制

        Args:
            order_value: 订单金额
            total_account_value: 总账户价值

        Returns:
            RiskCheckResult: 检查结果
        """
        if not self.config.enabled:
            return RiskCheckResult(
                check_type=RiskCheckType.POSITION_LIMIT,
                passed=True,
                message="持仓限制检查未启用"
            )

        # 计算订单占账户比例
        if total_account_value <= 0:
            return RiskCheckResult(
                check_type=RiskCheckType.POSITION_LIMIT,
                passed=False,
                severity=RiskSeverity.ERROR,
                message="账户价值无效",
                details={"total_account_value": str(total_account_value)}
            )

        position_ratio = order_value / total_account_value

        if position_ratio > self.config.max_position_ratio:
            return RiskCheckResult(
                check_type=RiskCheckType.POSITION_LIMIT,
                passed=False,
                severity=RiskSeverity.ERROR,
                message=f"订单超过最大单仓限制 ({position_ratio:.2%} > {self.config.max_position_ratio:.2%})",
                details={
                    "position_ratio": str(position_ratio),
                    "max_position_ratio": str(self.config.max_position_ratio),
                    "order_value": str(order_value),
                    "total_account_value": str(total_account_value)
                }
            )

        return RiskCheckResult(
            check_type=RiskCheckType.POSITION_LIMIT,
            passed=True,
            message=f"持仓限制检查通过 ({position_ratio:.2%} ≤ {self.config.max_position_ratio:.2%})",
            details={
                "position_ratio": str(position_ratio),
                "max_position_ratio": str(self.config.max_position_ratio)
            }
        )


class StopLossChecker(RiskChecker):
    """止损检查"""

    def check(
        self,
        current_price: Decimal,
        entry_price: Decimal,
        **kwargs
    ) -> RiskCheckResult:
        """
        检查是否触发止损

        Args:
            current_price: 当前价格
            entry_price: 成本价

        Returns:
            RiskCheckResult: 检查结果
        """
        if not self.config.enabled or self.config.stop_loss_ratio is None:
            return RiskCheckResult(
                check_type=RiskCheckType.STOP_LOSS,
                passed=True,
                message="止损检查未启用"
            )

        # 计算亏损比例
        if entry_price <= 0:
            return RiskCheckResult(
                check_type=RiskCheckType.STOP_LOSS,
                passed=False,
                severity=RiskSeverity.ERROR,
                message="成本价无效",
                details={"entry_price": str(entry_price)}
            )

        loss_ratio = (entry_price - current_price) / entry_price

        if loss_ratio >= self.config.stop_loss_ratio:
            return RiskCheckResult(
                check_type=RiskCheckType.STOP_LOSS,
                passed=False,
                severity=RiskSeverity.CRITICAL,
                message=f"触发止损 ({loss_ratio:.2%} ≥ {self.config.stop_loss_ratio:.2%})",
                details={
                    "loss_ratio": str(loss_ratio),
                    "stop_loss_ratio": str(self.config.stop_loss_ratio),
                    "current_price": str(current_price),
                    "entry_price": str(entry_price)
                }
            )

        return RiskCheckResult(
            check_type=RiskCheckType.STOP_LOSS,
            passed=True,
            message=f"未触发止损 ({loss_ratio:.2%} < {self.config.stop_loss_ratio:.2%})",
            details={
                "loss_ratio": str(loss_ratio),
                "stop_loss_ratio": str(self.config.stop_loss_ratio)
            }
        )


class TakeProfitChecker(RiskChecker):
    """止盈检查"""

    def check(
        self,
        current_price: Decimal,
        entry_price: Decimal,
        **kwargs
    ) -> RiskCheckResult:
        """
        检查是否触发止盈

        Args:
            current_price: 当前价格
            entry_price: 成本价

        Returns:
            RiskCheckResult: 检查结果
        """
        if not self.config.enabled or self.config.take_profit_ratio is None:
            return RiskCheckResult(
                check_type=RiskCheckType.TAKE_PROFIT,
                passed=True,
                message="止盈检查未启用"
            )

        # 计算盈利比例
        if entry_price <= 0:
            return RiskCheckResult(
                check_type=RiskCheckType.TAKE_PROFIT,
                passed=False,
                severity=RiskSeverity.ERROR,
                message="成本价无效",
                details={"entry_price": str(entry_price)}
            )

        profit_ratio = (current_price - entry_price) / entry_price

        if profit_ratio >= self.config.take_profit_ratio:
            return RiskCheckResult(
                check_type=RiskCheckType.TAKE_PROFIT,
                passed=False,
                severity=RiskSeverity.WARNING,
                message=f"触发止盈 ({profit_ratio:.2%} ≥ {self.config.take_profit_ratio:.2%})",
                details={
                    "profit_ratio": str(profit_ratio),
                    "take_profit_ratio": str(self.config.take_profit_ratio),
                    "current_price": str(current_price),
                    "entry_price": str(entry_price)
                }
            )

        return RiskCheckResult(
            check_type=RiskCheckType.TAKE_PROFIT,
            passed=True,
            message=f"未触发止盈 ({profit_ratio:.2%} < {self.config.take_profit_ratio:.2%})",
            details={
                "profit_ratio": str(profit_ratio),
                "take_profit_ratio": str(self.config.take_profit_ratio)
            }
        )


class DailyLossLimitChecker(RiskChecker):
    """单日亏损限制检查"""

    def check(
        self,
        daily_pnl: Decimal,
        total_account_value: Decimal,
        **kwargs
    ) -> RiskCheckResult:
        """
        检查当日亏损是否超过限制

        Args:
            daily_pnl: 当日盈亏（负数表示亏损）
            total_account_value: 总账户价值

        Returns:
            RiskCheckResult: 检查结果
        """
        if not self.config.enabled:
            return RiskCheckResult(
                check_type=RiskCheckType.DAILY_LOSS_LIMIT,
                passed=True,
                message="单日亏损限制检查未启用"
            )

        # 计算当日亏损比例
        if total_account_value <= 0:
            return RiskCheckResult(
                check_type=RiskCheckType.DAILY_LOSS_LIMIT,
                passed=False,
                severity=RiskSeverity.ERROR,
                message="账户价值无效",
                details={"total_account_value": str(total_account_value)}
            )

        # 只有亏损时才检查
        if daily_pnl >= 0:
            return RiskCheckResult(
                check_type=RiskCheckType.DAILY_LOSS_LIMIT,
                passed=True,
                message="当日盈利，无需检查亏损限制",
                details={"daily_pnl": str(daily_pnl)}
            )

        loss_ratio = abs(daily_pnl) / total_account_value

        if loss_ratio >= self.config.max_daily_loss_ratio:
            return RiskCheckResult(
                check_type=RiskCheckType.DAILY_LOSS_LIMIT,
                passed=False,
                severity=RiskSeverity.CRITICAL,
                message=f"超过单日最大亏损限制 ({loss_ratio:.2%} ≥ {self.config.max_daily_loss_ratio:.2%})",
                details={
                    "loss_ratio": str(loss_ratio),
                    "max_daily_loss_ratio": str(self.config.max_daily_loss_ratio),
                    "daily_pnl": str(daily_pnl),
                    "total_account_value": str(total_account_value)
                }
            )

        return RiskCheckResult(
            check_type=RiskCheckType.DAILY_LOSS_LIMIT,
            passed=True,
            message=f"单日亏损限制检查通过 ({loss_ratio:.2%} < {self.config.max_daily_loss_ratio:.2%})",
            details={
                "loss_ratio": str(loss_ratio),
                "max_daily_loss_ratio": str(self.config.max_daily_loss_ratio),
                "daily_pnl": str(daily_pnl)
            }
        )


class OrderSizeChecker(RiskChecker):
    """订单大小限制检查"""

    def check(
        self,
        order_quantity: int,
        **kwargs
    ) -> RiskCheckResult:
        """
        检查订单数量是否超过限制

        Args:
            order_quantity: 订单数量（股）

        Returns:
            RiskCheckResult: 检查结果
        """
        if not self.config.enabled or self.config.max_order_size is None:
            return RiskCheckResult(
                check_type=RiskCheckType.ORDER_SIZE,
                passed=True,
                message="订单大小限制检查未启用"
            )

        if order_quantity > self.config.max_order_size:
            return RiskCheckResult(
                check_type=RiskCheckType.ORDER_SIZE,
                passed=False,
                severity=RiskSeverity.ERROR,
                message=f"订单数量超过限制 ({order_quantity} > {self.config.max_order_size})",
                details={
                    "order_quantity": order_quantity,
                    "max_order_size": self.config.max_order_size
                }
            )

        return RiskCheckResult(
            check_type=RiskCheckType.ORDER_SIZE,
            passed=True,
            message=f"订单大小检查通过 ({order_quantity} ≤ {self.config.max_order_size})",
            details={
                "order_quantity": order_quantity,
                "max_order_size": self.config.max_order_size
            }
        )


class ConcentrationChecker(RiskChecker):
    """持仓集中度检查"""

    def check(
        self,
        symbol_market_value: Decimal,
        total_account_value: Decimal,
        **kwargs
    ) -> RiskCheckResult:
        """
        检查单只股票持仓是否过于集中

        Args:
            symbol_market_value: 单只股票市值
            total_account_value: 总账户价值

        Returns:
            RiskCheckResult: 检查结果
        """
        if not self.config.enabled:
            return RiskCheckResult(
                check_type=RiskCheckType.CONCENTRATION,
                passed=True,
                message="持仓集中度检查未启用"
            )

        if total_account_value <= 0:
            return RiskCheckResult(
                check_type=RiskCheckType.CONCENTRATION,
                passed=False,
                severity=RiskSeverity.ERROR,
                message="账户价值无效",
                details={"total_account_value": str(total_account_value)}
            )

        concentration_ratio = symbol_market_value / total_account_value

        if concentration_ratio > self.config.max_concentration_ratio:
            return RiskCheckResult(
                check_type=RiskCheckType.CONCENTRATION,
                passed=False,
                severity=RiskSeverity.WARNING,
                message=f"持仓集中度过高 ({concentration_ratio:.2%} > {self.config.max_concentration_ratio:.2%})",
                details={
                    "concentration_ratio": str(concentration_ratio),
                    "max_concentration_ratio": str(self.config.max_concentration_ratio),
                    "symbol_market_value": str(symbol_market_value),
                    "total_account_value": str(total_account_value)
                }
            )

        return RiskCheckResult(
            check_type=RiskCheckType.CONCENTRATION,
            passed=True,
            message=f"持仓集中度检查通过 ({concentration_ratio:.2%} ≤ {self.config.max_concentration_ratio:.2%})",
            details={
                "concentration_ratio": str(concentration_ratio),
                "max_concentration_ratio": str(self.config.max_concentration_ratio)
            }
        )
