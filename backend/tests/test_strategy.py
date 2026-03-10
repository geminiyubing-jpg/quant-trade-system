"""
策略引擎测试

测试策略的基础功能、执行引擎等。
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.services.strategy.base import (
    StrategyBase,
    StrategyConfig,
    StrategyContext,
    Signal,
    SignalType,
    StrategyStatus,
    StrategyError
)
from src.services.strategy.examples import (
    BuyAndHoldStrategy,
    MovingAverageStrategy,
    MeanReversionStrategy
)
from src.services.strategy.engine import (
    StrategyEngine,
    SignalConverter,
    ExecutionResult
)


# ==============================================
# 策略基类测试
# ==============================================

class TestStrategyBase:
    """策略基类测试"""

    def test_strategy_initialization(self):
        """测试策略初始化"""
        config = StrategyConfig(
            name="测试策略",
            description="这是一个测试策略",
            parameters={"param1": 100}
        )

        class TestStrategy(StrategyBase):
            def initialize(self, context):
                pass

            def on_data(self, context):
                pass

            def finalize(self, context):
                pass

        strategy = TestStrategy(config)

        assert strategy.name == "测试策略"
        assert strategy.description == "这是一个测试策略"
        assert strategy.parameters == {"param1": 100}
        assert strategy.status == StrategyStatus.CREATED

    def test_strategy_state(self):
        """测试策略状态"""
        config = StrategyConfig(name="测试策略")

        class TestStrategy(StrategyBase):
            def initialize(self, context):
                pass

            def on_data(self, context):
                pass

            def finalize(self, context):
                pass

        strategy = TestStrategy(config)
        state = strategy.get_state()

        assert state["name"] == "测试策略"
        assert state["status"] == StrategyStatus.CREATED.value
        assert "parameters" in state


# ==============================================
# 买入持有策略测试
# ==============================================

class TestBuyAndHoldStrategy:
    """买入持有策略测试"""

    def test_initialization(self):
        """测试策略初始化"""
        config = StrategyConfig(
            name="买入持有策略",
            parameters={"symbol": "AAPL"}
        )

        strategy = BuyAndHoldStrategy(config)
        context = StrategyContext(
            current_time=datetime.now(),
            current_price=150.0,
            cash=10000.0,
            position=0
        )

        strategy.initialize(context)

        assert strategy.has_bought is False

    def test_generate_buy_signal(self):
        """测试生成买入信号"""
        config = StrategyConfig(
            name="买入持有策略",
            parameters={"symbol": "AAPL"}
        )

        strategy = BuyAndHoldStrategy(config)
        context = StrategyContext(
            current_time=datetime.now(),
            current_price=150.0,
            cash=10000.0,
            position=0
        )

        strategy.initialize(context)
        signals = strategy.on_data(context)

        assert signals is not None
        assert len(signals) == 1
        assert signals[0].signal_type == SignalType.BUY
        assert signals[0].quantity == 66  # 10000 / 150 = 66

    def test_no_second_buy(self):
        """测试不会第二次买入"""
        config = StrategyConfig(
            name="买入持有策略",
            parameters={"symbol": "AAPL"}
        )

        strategy = BuyAndHoldStrategy(config)
        context = StrategyContext(
            current_time=datetime.now(),
            current_price=150.0,
            cash=10000.0,
            position=0
        )

        strategy.initialize(context)

        # 第一次买入
        signals = strategy.on_data(context)
        assert signals is not None
        assert len(signals) == 1

        # 第二次不应该买入
        context.position = 66
        signals = strategy.on_data(context)
        assert signals is None or len(signals) == 0


# ==============================================
# 移动平均线策略测试
# ==============================================

class TestMovingAverageStrategy:
    """移动平均线策略测试"""

    def test_initialization(self):
        """测试策略初始化"""
        config = StrategyConfig(
            name="移动平均线策略",
            parameters={
                "symbol": "AAPL",
                "short_window": 5,
                "long_window": 20
            }
        )

        strategy = MovingAverageStrategy(config)
        context = StrategyContext(
            current_time=datetime.now(),
            current_price=150.0,
            cash=10000.0,
            position=0
        )

        strategy.initialize(context)

        assert len(strategy.price_history) == 0
        assert strategy.prev_short_ma is None
        assert strategy.prev_long_ma is None

    def test_parameter_validation(self):
        """测试参数验证"""
        # 无效参数：短期窗口 >= 长期窗口
        config = StrategyConfig(
            name="移动平均线策略",
            parameters={
                "short_window": 20,
                "long_window": 5
            }
        )

        strategy = MovingAverageStrategy(config)
        is_valid, error_msg = strategy.validate_parameters()

        assert is_valid is False
        assert "短期窗口必须小于长期窗口" in error_msg

    def test_generate_signals(self):
        """测试生成信号"""
        config = StrategyConfig(
            name="移动平均线策略",
            parameters={
                "symbol": "AAPL",
                "short_window": 3,
                "long_window": 5
            }
        )

        strategy = MovingAverageStrategy(config)
        context = StrategyContext(
            current_time=datetime.now(),
            current_price=150.0,
            cash=10000.0,
            position=0
        )

        strategy.initialize(context)

        # 模拟价格数据
        prices = [100, 102, 104, 103, 105, 107, 110, 108, 106, 105]

        for i, price in enumerate(prices):
            context.current_price = price
            context.current_time = datetime.now() + timedelta(days=i)
            signals = strategy.on_data(context)

            # 在足够数据后，应该开始生成信号
            if i >= strategy.long_window:
                # 检查信号是否生成
                if signals:
                    assert len(signals) > 0
                    assert signals[0].symbol == "AAPL"


# ==============================================
# 策略执行引擎测试
# ==============================================

class TestStrategyEngine:
    """策略执行引擎测试"""

    def test_add_strategy(self):
        """测试添加策略"""
        engine = StrategyEngine()

        config = StrategyConfig(name="测试策略")
        strategy = BuyAndHoldStrategy(config)

        engine.add_strategy("test_strategy", strategy)

        assert "test_strategy" in engine.strategies
        assert "test_strategy" in engine.strategy_states

    def test_execute_strategy(self):
        """测试执行策略"""
        engine = StrategyEngine()

        config = StrategyConfig(
            name="测试策略",
            parameters={"symbol": "AAPL"}
        )
        strategy = BuyAndHoldStrategy(config)

        engine.add_strategy("test_strategy", strategy)

        context = StrategyContext(
            current_time=datetime.now(),
            current_price=150.0,
            cash=10000.0,
            position=0
        )

        result = engine.execute_strategy("test_strategy", context)

        assert result.success is True
        assert len(result.signals_generated) > 0

    def test_start_stop_strategy(self):
        """测试启动和停止策略"""
        engine = StrategyEngine()

        config = StrategyConfig(name="测试策略")
        strategy = BuyAndHoldStrategy(config)

        engine.add_strategy("test_strategy", strategy)

        context = StrategyContext(
            current_time=datetime.now(),
            current_price=150.0,
            cash=10000.0,
            position=0
        )

        # 启动策略
        result = engine.start_strategy("test_strategy", context)
        assert result.success is True

        state = engine.get_strategy_state("test_strategy")
        assert state["status"] == StrategyStatus.RUNNING

        # 停止策略
        result = engine.stop_strategy("test_strategy", context)
        assert result.success is True

        state = engine.get_strategy_state("test_strategy")
        assert state["status"] == StrategyStatus.STOPPED

    def test_pause_resume_strategy(self):
        """测试暂停和恢复策略"""
        engine = StrategyEngine()

        config = StrategyConfig(name="测试策略")
        strategy = BuyAndHoldStrategy(config)

        engine.add_strategy("test_strategy", strategy)

        # 暂停策略
        result = engine.pause_strategy("test_strategy")
        assert result.success is True

        state = engine.get_strategy_state("test_strategy")
        assert state["status"] == StrategyStatus.PAUSED

        # 恢复策略
        result = engine.resume_strategy("test_strategy")
        assert result.success is True

        state = engine.get_strategy_state("test_strategy")
        assert state["status"] == StrategyStatus.RUNNING


# ==============================================
# 信号转换器测试
# ==============================================

class TestSignalConverter:
    """信号转换器测试"""

    def test_signal_to_order(self):
        """测试信号转换为订单"""
        signal = Signal(
            symbol="AAPL",
            signal_type=SignalType.BUY,
            timestamp=datetime.now(),
            price=150.0,
            quantity=100,
            confidence=0.9,
            reason="测试买入"
        )

        order = SignalConverter.signal_to_order(signal, user_id="test_user", strategy_id="test_strategy")

        assert order["symbol"] == "AAPL"
        assert order["side"] == "BUY"
        assert order["quantity"] == 100
        assert order["price"] == Decimal("150")
        assert order["user_id"] == "test_user"
        assert order["strategy_id"] == "test_strategy"
        assert order["status"] == "PENDING"

    def test_signals_to_orders(self):
        """测试批量转换信号"""
        signals = [
            Signal(
                symbol="AAPL",
                signal_type=SignalType.BUY,
                timestamp=datetime.now(),
                price=150.0,
                quantity=100
            ),
            Signal(
                symbol="GOOGL",
                signal_type=SignalType.SELL,
                timestamp=datetime.now(),
                price=2500.0,
                quantity=50
            )
        ]

        orders = SignalConverter.signals_to_orders(signals, user_id="test_user")

        assert len(orders) == 2
        assert orders[0]["symbol"] == "AAPL"
        assert orders[1]["symbol"] == "GOOGL"
        assert orders[0]["side"] == "BUY"
        assert orders[1]["side"] == "SELL"
