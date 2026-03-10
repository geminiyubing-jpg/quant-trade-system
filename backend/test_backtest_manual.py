#!/usr/bin/env python3
"""
回测模块手动验证脚本
"""

import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import date, datetime, timedelta
from decimal import Decimal

from src.services.backtest import BacktestEngine
from src.services.backtest.models import BacktestConfig


def test_backtest_engine():
    """测试回测引擎"""
    print("\n" + "="*60)
    print("回测引擎功能测试")
    print("="*60)

    # 1. 创建回测配置
    config = BacktestConfig(
        strategy_id="test_strategy_001",
        strategy_name="测试策略",
        symbols=["000001.SZ", "000002.SZ"],
        start_date=date.today() - timedelta(days=30),
        end_date=date.today(),
        initial_capital=Decimal("100000"),
        execution_mode="PAPER",
        commission_rate=Decimal("0.0003"),
        slippage_rate=Decimal("0.001")
    )

    print(f"✓ 回测配置创建成功")
    print(f"  策略: {config.strategy_name}")
    print(f"  股票: {config.symbols}")
    print(f"  日期: {config.start_date} ~ {config.end_date}")
    print(f"  初始资金: {config.initial_capital}")

    # 2. 创建回测引擎
    engine = BacktestEngine(config=config)
    print(f"\n✓ 回测引擎初始化成功")
    print(f"  回测 ID: {engine.backtest_id}")

    # 3. 运行回测
    print(f"\n⏳ 正在运行回测...")
    result = engine.run()

    # 4. 输出结果
    print(f"\n✅ 回测完成！")
    print(f"\n回测指标:")
    print(f"  总收益率: {result.metrics.total_return:.2%}")
    print(f"  年化收益率: {result.metrics.annual_return:.2%}")
    print(f"  最大回撤: {result.metrics.max_drawdown:.2%}")
    print(f"  夏普比率: {result.metrics.sharpe_ratio:.2f}")
    print(f"  交易次数: {result.metrics.total_trades}")
    print(f"  胜率: {result.metrics.win_rate:.2%}")
    print(f"  平均每笔收益率: {result.metrics.avg_trade_return:.2%}")

    print(f"\n资金曲线:")
    print(f"  数据点数: {len(result.equity_curve)}")
    if result.equity_curve:
        print(f"  初始权益: {result.equity_curve[0].equity:.2f}")
        print(f"  最终权益: {result.equity_curve[-1].equity:.2f}")

    print(f"\n交易记录:")
    print(f"  总交易数: {len(result.trades)}")
    if result.trades:
        print(f"  示例交易:")
        for trade in result.trades[:3]:
            print(f"    {trade.side} {trade.symbol} {trade.quantity}股 @ {trade.price:.2f}")

    # 5. 验证结果
    assert result.backtest_id == engine.backtest_id
    assert len(result.equity_curve) > 0
    assert result.metrics.total_trades == len(result.trades)

    print(f"\n✅ 所有验证通过！")


def test_quick_backtest():
    """测试快速回测"""
    print("\n" + "="*60)
    print("快速回测测试")
    print("="*60)

    end_date = date.today()
    start_date = end_date - timedelta(days=7)  # 7天回测

    config = BacktestConfig(
        strategy_id="quick_test",
        strategy_name="快速回测（7天）",
        symbols=["000001.SZ"],
        start_date=start_date,
        end_date=end_date,
        initial_capital=Decimal("100000"),
        execution_mode="PAPER"
    )

    engine = BacktestEngine(config=config)
    result = engine.run()

    print(f"\n✅ 快速回测完成！")
    print(f"  总收益率: {result.metrics.total_return:.2%}")
    print(f"  年化收益率: {result.metrics.annual_return:.2%}")
    print(f"  最大回撤: {result.metrics.max_drawdown:.2%}")
    print(f"  交易次数: {result.metrics.total_trades}")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("回测模块手动验证")
    print("="*60)

    try:
        test_backtest_engine()
        test_quick_backtest()

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
