#!/usr/bin/env python3
"""
风控模块手动验证脚本
"""

import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from decimal import Decimal
from src.services.risk import RiskControlEngine
from src.services.risk.models import RiskRuleConfig, RiskCheckType, RiskSeverity
from src.services.risk.checks import (
    PositionLimitChecker,
    StopLossChecker,
    TakeProfitChecker,
    DailyLossLimitChecker,
    OrderSizeChecker,
    ConcentrationChecker,
)


def test_position_limit_checker():
    """测试持仓限制检查"""
    print("\n" + "="*60)
    print("测试 1: 持仓限制检查")
    print("="*60)

    config = RiskRuleConfig(
        enabled=True,
        max_position_ratio=Decimal("0.3")
    )
    checker = PositionLimitChecker(config)

    # 测试通过
    result = checker.check(
        order_value=Decimal("20000"),
        total_account_value=Decimal("100000")
    )
    print(f"✓ 订单占比 20% - {result.message}")
    assert result.passed is True

    # 测试失败
    result = checker.check(
        order_value=Decimal("40000"),
        total_account_value=Decimal("100000")
    )
    print(f"✓ 订单占比 40% - {result.message}")
    assert result.passed is False

    print("✅ 持仓限制检查测试通过\n")


def test_stop_loss_checker():
    """测试止损检查"""
    print("\n" + "="*60)
    print("测试 2: 止损检查")
    print("="*60)

    config = RiskRuleConfig(
        enabled=True,
        stop_loss_ratio=Decimal("0.05")
    )
    checker = StopLossChecker(config)

    # 测试未触发止损
    result = checker.check(
        current_price=Decimal("97"),
        entry_price=Decimal("100")
    )
    print(f"✓ 亏损 3% - {result.message}")
    assert result.passed is True

    # 测试触发止损
    result = checker.check(
        current_price=Decimal("94"),
        entry_price=Decimal("100")
    )
    print(f"✓ 亏损 6% - {result.message}")
    assert result.passed is False
    assert result.severity == RiskSeverity.CRITICAL

    print("✅ 止损检查测试通过\n")


def test_take_profit_checker():
    """测试止盈检查"""
    print("\n" + "="*60)
    print("测试 3: 止盈检查")
    print("="*60)

    config = RiskRuleConfig(
        enabled=True,
        take_profit_ratio=Decimal("0.10")
    )
    checker = TakeProfitChecker(config)

    # 测试未触发止盈
    result = checker.check(
        current_price=Decimal("105"),
        entry_price=Decimal("100")
    )
    print(f"✓ 盈利 5% - {result.message}")
    assert result.passed is True

    # 测试触发止盈
    result = checker.check(
        current_price=Decimal("112"),
        entry_price=Decimal("100")
    )
    print(f"✓ 盈利 12% - {result.message}")
    assert result.passed is False
    assert result.severity == RiskSeverity.WARNING

    print("✅ 止盈检查测试通过\n")


def test_daily_loss_limit_checker():
    """测试单日亏损限制检查"""
    print("\n" + "="*60)
    print("测试 4: 单日亏损限制检查")
    print("="*60)

    config = RiskRuleConfig(
        enabled=True,
        max_daily_loss_ratio=Decimal("0.05")
    )
    checker = DailyLossLimitChecker(config)

    # 测试亏损在限制内
    result = checker.check(
        daily_pnl=Decimal("-3000"),
        total_account_value=Decimal("100000")
    )
    print(f"✓ 亏损 3% - {result.message}")
    assert result.passed is True

    # 测试超过限制
    result = checker.check(
        daily_pnl=Decimal("-6000"),
        total_account_value=Decimal("100000")
    )
    print(f"✓ 亏损 6% - {result.message}")
    assert result.passed is False
    assert result.severity == RiskSeverity.CRITICAL

    print("✅ 单日亏损限制检查测试通过\n")


def test_order_size_checker():
    """测试订单大小限制检查"""
    print("\n" + "="*60)
    print("测试 5: 订单大小限制检查")
    print("="*60)

    config = RiskRuleConfig(
        enabled=True,
        max_order_size=10000
    )
    checker = OrderSizeChecker(config)

    # 测试通过
    result = checker.check(order_quantity=5000)
    print(f"✓ 订单数量 5000 - {result.message}")
    assert result.passed is True

    # 测试失败
    result = checker.check(order_quantity=15000)
    print(f"✓ 订单数量 15000 - {result.message}")
    assert result.passed is False

    print("✅ 订单大小限制检查测试通过\n")


def test_concentration_checker():
    """测试持仓集中度检查"""
    print("\n" + "="*60)
    print("测试 6: 持仓集中度检查")
    print("="*60)

    config = RiskRuleConfig(
        enabled=True,
        max_concentration_ratio=Decimal("0.5")
    )
    checker = ConcentrationChecker(config)

    # 测试通过
    result = checker.check(
        symbol_market_value=Decimal("40000"),
        total_account_value=Decimal("100000")
    )
    print(f"✓ 集中度 40% - {result.message}")
    assert result.passed is True

    # 测试失败
    result = checker.check(
        symbol_market_value=Decimal("60000"),
        total_account_value=Decimal("100000")
    )
    print(f"✓ 集中度 60% - {result.message}")
    assert result.passed is False
    assert result.severity == RiskSeverity.WARNING

    print("✅ 持仓集中度检查测试通过\n")


def test_risk_control_engine():
    """测试风控规则引擎"""
    print("\n" + "="*60)
    print("测试 7: 风控规则引擎")
    print("="*60)

    config = RiskRuleConfig(
        enabled=True,
        max_position_ratio=Decimal("0.3"),
        max_daily_loss_ratio=Decimal("0.05"),
        stop_loss_ratio=Decimal("0.05"),
        take_profit_ratio=Decimal("0.10"),
        max_order_size=10000,
        max_concentration_ratio=Decimal("0.5")
    )

    engine = RiskControlEngine(config=config)

    # 检查所有检查器是否初始化
    assert len(engine.checkers) == 6
    print(f"✓ 风控引擎初始化成功，包含 {len(engine.checkers)} 个检查器")

    # 检查所有检查器类型
    checker_types = list(engine.checkers.keys())
    print(f"✓ 检查器类型: {[t.value for t in checker_types]}")

    assert RiskCheckType.POSITION_LIMIT in checker_types
    assert RiskCheckType.STOP_LOSS in checker_types
    assert RiskCheckType.TAKE_PROFIT in checker_types
    assert RiskCheckType.DAILY_LOSS_LIMIT in checker_types
    assert RiskCheckType.ORDER_SIZE in checker_types
    assert RiskCheckType.CONCENTRATION in checker_types

    print("✅ 风控规则引擎测试通过\n")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("风控模块手动验证")
    print("="*60)

    try:
        test_position_limit_checker()
        test_stop_loss_checker()
        test_take_profit_checker()
        test_daily_loss_limit_checker()
        test_order_size_checker()
        test_concentration_checker()
        test_risk_control_engine()

        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
