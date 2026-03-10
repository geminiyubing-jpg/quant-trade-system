"""
==============================================
QuantAI Ecosystem - 风控模块测试
==============================================

测试风控规则引擎和检查模块。
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.services.risk import RiskControlEngine
from src.services.risk.models import (
    RiskCheckResult,
    RiskCheckType,
    RiskSeverity,
    RiskRuleConfig,
    RiskMetrics,
)
from src.services.risk.checks import (
    PositionLimitChecker,
    StopLossChecker,
    TakeProfitChecker,
    DailyLossLimitChecker,
    OrderSizeChecker,
    ConcentrationChecker,
)


# ==============================================
# Fixtures
# ==============================================

@pytest.fixture
def default_config():
    """默认风控配置"""
    return RiskRuleConfig(
        enabled=True,
        max_position_ratio=Decimal("0.3"),
        max_daily_loss_ratio=Decimal("0.05"),
        stop_loss_ratio=Decimal("0.05"),
        take_profit_ratio=Decimal("0.10"),
        max_order_size=10000,
        max_concentration_ratio=Decimal("0.5")
    )


@pytest.fixture
def risk_engine(default_config):
    """风控引擎"""
    return RiskControlEngine(config=default_config)


# ==============================================
# 持仓限制检查测试
# ==============================================

class TestPositionLimitChecker:
    """测试持仓限制检查"""

    def test_position_limit_passed(self, default_config):
        """测试持仓限制检查通过"""
        checker = PositionLimitChecker(default_config)

        result = checker.check(
            order_value=Decimal("20000"),
            total_account_value=Decimal("100000")
        )

        assert result.passed is True
        assert result.check_type == RiskCheckType.POSITION_LIMIT
        assert "20.00%" in result.message

    def test_position_limit_failed(self, default_config):
        """测试持仓限制检查失败"""
        checker = PositionLimitChecker(default_config)

        result = checker.check(
            order_value=Decimal("40000"),
            total_account_value=Decimal("100000")
        )

        assert result.passed is False
        assert result.severity == RiskSeverity.ERROR
        assert "超过最大单仓限制" in result.message
        assert result.details["position_ratio"] == Decimal("0.4")

    def test_position_limit_disabled(self):
        """测试持仓限制检查未启用"""
        config = RiskRuleConfig(enabled=False)
        checker = PositionLimitChecker(config)

        result = checker.check(
            order_value=Decimal("40000"),
            total_account_value=Decimal("100000")
        )

        assert result.passed is True
        assert "未启用" in result.message


# ==============================================
# 止损检查测试
# ==============================================

class TestStopLossChecker:
    """测试止损检查"""

    def test_stop_loss_not_triggered(self, default_config):
        """测试未触发止损"""
        checker = StopLossChecker(default_config)

        result = checker.check(
            current_price=Decimal("97"),
            entry_price=Decimal("100")
        )

        assert result.passed is True
        assert result.check_type == RiskCheckType.STOP_LOSS
        assert "未触发止损" in result.message

    def test_stop_loss_triggered(self, default_config):
        """测试触发止损"""
        checker = StopLossChecker(default_config)

        result = checker.check(
            current_price=Decimal("94"),
            entry_price=Decimal("100")
        )

        assert result.passed is False
        assert result.severity == RiskSeverity.CRITICAL
        assert "触发止损" in result.message
        assert result.details["loss_ratio"] == Decimal("0.06")

    def test_stop_loss_disabled(self):
        """测试止损检查未启用"""
        config = RiskRuleConfig(enabled=True, stop_loss_ratio=None)
        checker = StopLossChecker(config)

        result = checker.check(
            current_price=Decimal("90"),
            entry_price=Decimal("100")
        )

        assert result.passed is True
        assert "未启用" in result.message


# ==============================================
# 止盈检查测试
# ==============================================

class TestTakeProfitChecker:
    """测试止盈检查"""

    def test_take_profit_not_triggered(self, default_config):
        """测试未触发止盈"""
        checker = TakeProfitChecker(default_config)

        result = checker.check(
            current_price=Decimal("105"),
            entry_price=Decimal("100")
        )

        assert result.passed is True
        assert "未触发止盈" in result.message

    def test_take_profit_triggered(self, default_config):
        """测试触发止盈"""
        checker = TakeProfitChecker(default_config)

        result = checker.check(
            current_price=Decimal("112"),
            entry_price=Decimal("100")
        )

        assert result.passed is False
        assert result.severity == RiskSeverity.WARNING
        assert "触发止盈" in result.message
        assert result.details["profit_ratio"] == Decimal("0.12")


# ==============================================
# 单日亏损限制检查测试
# ==============================================

class TestDailyLossLimitChecker:
    """测试单日亏损限制检查"""

    def test_daily_loss_within_limit(self, default_config):
        """测试单日亏损在限制内"""
        checker = DailyLossLimitChecker(default_config)

        result = checker.check(
            daily_pnl=Decimal("-3000"),
            total_account_value=Decimal("100000")
        )

        assert result.passed is True
        assert "单日亏损限制检查通过" in result.message

    def test_daily_loss_exceeds_limit(self, default_config):
        """测试单日亏损超过限制"""
        checker = DailyLossLimitChecker(default_config)

        result = checker.check(
            daily_pnl=Decimal("-6000"),
            total_account_value=Decimal("100000")
        )

        assert result.passed is False
        assert result.severity == RiskSeverity.CRITICAL
        assert "超过单日最大亏损限制" in result.message

    def test_daily_profit_no_check(self, default_config):
        """测试当日盈利无需检查"""
        checker = DailyLossLimitChecker(default_config)

        result = checker.check(
            daily_pnl=Decimal("5000"),
            total_account_value=Decimal("100000")
        )

        assert result.passed is True
        assert "盈利" in result.message


# ==============================================
# 订单大小限制检查测试
# ==============================================

class TestOrderSizeChecker:
    """测试订单大小限制检查"""

    def test_order_size_within_limit(self, default_config):
        """测试订单大小在限制内"""
        checker = OrderSizeChecker(default_config)

        result = checker.check(order_quantity=5000)

        assert result.passed is True
        assert "订单大小检查通过" in result.message

    def test_order_size_exceeds_limit(self, default_config):
        """测试订单大小超过限制"""
        checker = OrderSizeChecker(default_config)

        result = checker.check(order_quantity=15000)

        assert result.passed is False
        assert result.severity == RiskSeverity.ERROR
        assert "订单数量超过限制" in result.message


# ==============================================
# 持仓集中度检查测试
# ==============================================

class TestConcentrationChecker:
    """测试持仓集中度检查"""

    def test_concentration_within_limit(self, default_config):
        """测试持仓集中度在限制内"""
        checker = ConcentrationChecker(default_config)

        result = checker.check(
            symbol_market_value=Decimal("40000"),
            total_account_value=Decimal("100000")
        )

        assert result.passed is True
        assert "持仓集中度检查通过" in result.message

    def test_concentration_exceeds_limit(self, default_config):
        """测试持仓集中度过高"""
        checker = ConcentrationChecker(default_config)

        result = checker.check(
            symbol_market_value=Decimal("60000"),
            total_account_value=Decimal("100000")
        )

        assert result.passed is False
        assert result.severity == RiskSeverity.WARNING
        assert "持仓集中度过高" in result.message


# ==============================================
# 风控引擎集成测试
# ==============================================

class TestRiskControlEngine:
    """测试风控规则引擎"""

    def test_validate_order_all_checks_passed(self, risk_engine):
        """测试订单验证 - 所有检查通过"""
        # 注意：这个测试需要 mock 数据库
        # 这里先测试引擎的初始化
        assert risk_engine is not None
        assert len(risk_engine.checkers) == 6

    def test_get_all_checkers(self, risk_engine):
        """测试获取所有检查器"""
        checkers = risk_engine.checkers

        assert RiskCheckType.POSITION_LIMIT in checkers
        assert RiskCheckType.STOP_LOSS in checkers
        assert RiskCheckType.TAKE_PROFIT in checkers
        assert RiskCheckType.DAILY_LOSS_LIMIT in checkers
        assert RiskCheckType.ORDER_SIZE in checkers
        assert RiskCheckType.CONCENTRATION in checkers


# ==============================================
# 风控配置测试
# ==============================================

class TestRiskRuleConfig:
    """测试风控规则配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = RiskRuleConfig()

        assert config.enabled is True
        assert config.max_position_ratio == Decimal("0.3")
        assert config.max_daily_loss_ratio == Decimal("0.05")

    def test_custom_config(self):
        """测试自定义配置"""
        config = RiskRuleConfig(
            max_position_ratio=Decimal("0.5"),
            max_daily_loss_ratio=Decimal("0.10"),
            stop_loss_ratio=Decimal("0.03")
        )

        assert config.max_position_ratio == Decimal("0.5")
        assert config.max_daily_loss_ratio == Decimal("0.10")
        assert config.stop_loss_ratio == Decimal("0.03")

    def test_config_validation(self):
        """测试配置验证"""
        # 无效的 max_position_ratio（> 1）
        with pytest.raises(ValueError):
            RiskRuleConfig(max_position_ratio=Decimal("1.5"))

        # 无效的 stop_loss_ratio（< 0）
        with pytest.raises(ValueError):
            RiskRuleConfig(stop_loss_ratio=Decimal("-0.1"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
