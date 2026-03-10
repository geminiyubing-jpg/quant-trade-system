"""
回测服务单元测试

测试回测引擎、回测配置和回测结果。
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from src.services.backtest.models import (
    BacktestConfig,
    BacktestResult,
    BacktestMetrics,
    Trade,
    EquityCurve,
    ExecutionMode,
)
from src.services.backtest.engine import BacktestEngine


# ==============================================
# 测试数据
# ==============================================

def create_test_config(
    symbols: list = None,
    start_date: date = None,
    end_date: date = None
) -> BacktestConfig:
    """创建测试回测配置"""
    return BacktestConfig(
        strategy_id="test_strategy",
        strategy_name="测试策略",
        symbols=symbols or ["000001"],
        start_date=start_date or date(2024, 1, 1),
        end_date=end_date or date(2024, 1, 31),
        initial_capital=Decimal("100000"),
        execution_mode=ExecutionMode.PAPER,
        commission_rate=Decimal("0.0003"),
        slippage_rate=Decimal("0.001")
    )


def create_test_metrics() -> BacktestMetrics:
    """创建测试回测指标"""
    return BacktestMetrics(
        total_return=Decimal("0.10"),
        annual_return=Decimal("0.12"),
        benchmark_return=Decimal("0.08"),
        excess_return=Decimal("0.02"),
        volatility=Decimal("0.15"),
        max_drawdown=Decimal("0.05"),
        sharpe_ratio=Decimal("1.5"),
        calmar_ratio=Decimal("2.0"),
        total_trades=10,
        win_rate=Decimal("0.6"),
        profit_factor=Decimal("1.8"),
        avg_trade_return=Decimal("0.01"),
        trading_days=20,
        avg_holding_period=Decimal("5.0")
    )


# ==============================================
# BacktestConfig 测试
# ==============================================

class TestBacktestConfig:
    """回测配置测试"""

    def test_create_config(self):
        """测试创建配置"""
        config = create_test_config()

        assert config.strategy_id == "test_strategy"
        assert config.strategy_name == "测试策略"
        assert len(config.symbols) == 1
        assert config.initial_capital == Decimal("100000")
        assert config.execution_mode == ExecutionMode.PAPER

    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        config = BacktestConfig(
            strategy_id="test",
            strategy_name="测试",
            symbols=["000001"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            initial_capital=Decimal("100000"),
            execution_mode=ExecutionMode.PAPER
        )
        assert config is not None

    def test_invalid_date_range(self):
        """测试无效日期范围"""
        with pytest.raises((ValueError, Exception)):
            BacktestConfig(
                strategy_id="test",
                strategy_name="测试",
                symbols=["000001"],
                start_date=date(2024, 12, 31),  # 开始日期 > 结束日期
                end_date=date(2024, 1, 1),
                initial_capital=Decimal("100000"),
                execution_mode=ExecutionMode.PAPER
            )


# ==============================================
# BacktestMetrics 测试
# ==============================================

class TestBacktestMetrics:
    """回测指标测试"""

    def test_create_metrics(self):
        """测试创建指标"""
        metrics = create_test_metrics()

        assert metrics.total_return == Decimal("0.10")
        assert metrics.annual_return == Decimal("0.12")
        assert metrics.sharpe_ratio == Decimal("1.5")
        assert metrics.total_trades == 10

    def test_metrics_calculation(self):
        """测试指标计算"""
        metrics = BacktestMetrics(
            total_return=Decimal("0.10"),
            annual_return=Decimal("0.12"),
            volatility=Decimal("0.15"),
            max_drawdown=Decimal("0.05"),
            sharpe_ratio=Decimal("1.5"),
            total_trades=10,
            win_rate=Decimal("0.6"),
            avg_trade_return=Decimal("0.01"),
            trading_days=20
        )

        # 验证基本逻辑
        assert metrics.total_return >= 0
        assert metrics.volatility >= 0
        assert metrics.max_drawdown >= 0
        assert 0 <= metrics.win_rate <= 1


# ==============================================
# Trade 测试
# ==============================================

class TestTrade:
    """交易记录测试"""

    def test_create_trade(self):
        """测试创建交易"""
        trade = Trade(
            symbol="000001",
            trade_id="test_trade_001",
            side="BUY",
            quantity=1000,
            price=Decimal("10.50"),
            timestamp=datetime.now(),
            commission=Decimal("3.15"),
            slippage=Decimal("10.50")
        )

        assert trade.symbol == "000001"
        assert trade.side == "BUY"
        assert trade.quantity == 1000
        assert trade.price == Decimal("10.50")


# ==============================================
# EquityCurve 测试
# ==============================================

class TestEquityCurve:
    """资金曲线测试"""

    def test_create_equity_curve(self):
        """测试创建资金曲线"""
        curve = EquityCurve(
            trade_date=date(2024, 1, 1),
            equity=Decimal("100000"),
            daily_return=Decimal("0.01"),
            drawdown=Decimal("0.02")
        )

        assert curve.trade_date == date(2024, 1, 1)
        assert curve.equity == Decimal("100000")
        assert curve.daily_return == Decimal("0.01")
        assert curve.drawdown == Decimal("0.02")

    def test_cumulative_returns(self):
        """测试累积收益率"""
        curves = [
            EquityCurve(
                trade_date=date(2024, 1, 1),
                equity=Decimal("100000"),
                daily_return=Decimal("0.01"),
                drawdown=Decimal("0.0")
            ),
            EquityCurve(
                trade_date=date(2024, 1, 2),
                equity=Decimal("101000"),
                daily_return=Decimal("0.01"),
                drawdown=Decimal("0.0")
            ),
            EquityCurve(
                trade_date=date(2024, 1, 3),
                equity=Decimal("100500"),
                daily_return=Decimal("-0.005"),
                drawdown=Decimal("0.005")
            )
        ]

        # 验证资金曲线
        assert curves[0].equity == Decimal("100000")
        assert curves[1].equity > curves[0].equity
        assert curves[2].equity < curves[1].equity


# ==============================================
# BacktestResult 测试
# ==============================================

class TestBacktestResult:
    """回测结果测试"""

    def test_create_result(self):
        """测试创建结果"""
        config = create_test_config()
        metrics = create_test_metrics()

        result = BacktestResult(
            backtest_id="test_backtest_001",
            config=config,
            metrics=metrics,
            trades=[],
            equity_curve=[],
            created_at=datetime.now(),
            status="completed"
        )

        assert result.backtest_id == "test_backtest_001"
        assert result.status == "completed"
        assert result.config.strategy_id == "test_strategy"
        assert result.metrics.total_return == Decimal("0.10")


# ==============================================
# BacktestEngine 测试
# ==============================================

class TestBacktestEngine:
    """回测引擎测试"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        config = create_test_config()
        engine = BacktestEngine(config=config)

        assert engine.config == config
        assert engine.backtest_id is not None
        assert engine.current_capital == config.initial_capital
        assert engine.cash == config.initial_capital

    def test_engine_run(self):
        """测试引擎运行"""
        config = create_test_config(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10)  # 短期测试
        )
        engine = BacktestEngine(config=config)

        result = engine.run()

        assert result is not None
        assert result.backtest_id == engine.backtest_id
        assert result.status == "completed"
        assert result.metrics is not None
        assert isinstance(result.equity_curve, list)
        assert isinstance(result.trades, list)

    def test_buy_execution(self):
        """测试买入执行"""
        config = create_test_config()
        engine = BacktestEngine(config=config)

        # 执行买入
        test_date = date(2024, 1, 1)
        engine._execute_buy(
            symbol="000001",
            quantity=100,
            price=Decimal("10.0"),
            trade_date=test_date
        )

        # 验证持仓和资金
        assert "000001" in engine.positions
        assert engine.positions["000001"] == 100
        assert engine.cash < config.initial_capital

    def test_sell_execution(self):
        """测试卖出执行"""
        config = create_test_config()
        engine = BacktestEngine(config=config)

        # 先买入
        test_date = date(2024, 1, 1)
        engine._execute_buy(
            symbol="000001",
            quantity=100,
            price=Decimal("10.0"),
            trade_date=test_date
        )

        initial_cash = engine.cash

        # 再卖出
        engine._execute_sell(
            symbol="000001",
            quantity=100,
            price=Decimal("10.5"),
            trade_date=test_date
        )

        # 验证
        assert "000001" not in engine.positions  # 持仓清空
        assert engine.cash > initial_cash  # 资金增加（盈利）

    def test_insufficient_funds(self):
        """测试资金不足"""
        config = create_test_config(initial_capital=Decimal("1000"))
        engine = BacktestEngine(config=config)

        # 尝试买入超过资金的数量
        engine._execute_buy(
            symbol="000001",
            quantity=100000,  # 需要约 1,000,000
            price=Decimal("10.0"),
            trade_date=date(2024, 1, 1)
        )

        # 验证未执行交易
        assert "000001" not in engine.positions
        assert engine.cash == config.initial_capital

    def test_sell_without_position(self):
        """测试卖出无持仓股票"""
        config = create_test_config()
        engine = BacktestEngine(config=config)

        initial_cash = engine.cash

        # 尝试卖出未持仓的股票
        engine._execute_sell(
            symbol="000001",
            quantity=100,
            price=Decimal("10.0"),
            trade_date=date(2024, 1, 1)
        )

        # 验证未执行交易
        assert engine.cash == initial_cash

    def test_calculate_metrics(self):
        """测试计算指标"""
        config = create_test_config()
        engine = BacktestEngine(config=config)

        # 运行回测
        result = engine.run()
        metrics = result.metrics

        # 验证基本指标存在
        assert metrics.total_return is not None
        assert metrics.annual_return is not None
        assert metrics.max_drawdown is not None
        assert metrics.volatility is not None
        assert metrics.sharpe_ratio is not None
        assert metrics.total_trades >= 0
        assert 0 <= metrics.win_rate <= 1


# ==============================================
# 运行测试
# ==============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
