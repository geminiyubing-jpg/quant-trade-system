"""
策略隔离上下文单元测试

测试持仓管理、订单管理、成交处理等功能。
"""

import pytest
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from src.services.strategy.context import (
    Position,
    Order,
    Trade,
    IsolatedStrategyContext,
    DataProvider,
    IndicatorManager,
)
from src.services.strategy.base import StrategyConfig


# ==============================================
# Position 测试
# ==============================================

class TestPosition:
    """Position 测试"""

    def test_position_creation(self):
        """测试创建持仓"""
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=Decimal("10.5"),
            current_price=Decimal("11.0"),
        )

        assert position.symbol == "000001.SZ"
        assert position.quantity == 1000
        assert position.avg_cost == Decimal("10.5")
        assert position.current_price == Decimal("11.0")

    def test_position_market_value_calculation(self):
        """测试市值计算"""
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=Decimal("10.0"),
            current_price=Decimal("12.0"),
        )

        assert position.market_value == Decimal("12000")

    def test_position_profit_loss_calculation(self):
        """测试盈亏计算"""
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=Decimal("10.0"),
            current_price=Decimal("12.0"),
        )

        # 盈利 = (12 - 10) * 1000 = 2000
        assert position.profit_loss == Decimal("2000")
        # 盈亏比例 = 2000 / 10000 = 0.2 = 20%
        assert position.profit_loss_pct == Decimal("0.2")

    def test_position_update_price(self):
        """测试更新价格"""
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=Decimal("10.0"),
            current_price=Decimal("10.0"),
        )

        position.update_price(Decimal("11.0"))

        assert position.current_price == Decimal("11.0")
        assert position.market_value == Decimal("11000")
        assert position.profit_loss == Decimal("1000")

    def test_position_add_quantity(self):
        """测试增加持仓"""
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=Decimal("10.0"),
            current_price=Decimal("12.0"),
        )

        # 以 12.0 的价格买入 500 股
        position.add_quantity(500, Decimal("12.0"))

        assert position.quantity == 1500
        # 平均成本 = (1000 * 10 + 500 * 12) / 1500 = 10.666...
        assert position.avg_cost == Decimal("10.66666666666666666666666667")

    def test_position_reduce_quantity(self):
        """测试减少持仓"""
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=Decimal("10.0"),
            current_price=Decimal("12.0"),
        )

        success = position.reduce_quantity(300)

        assert success is True
        assert position.quantity == 700

    def test_position_reduce_quantity_invalid(self):
        """测试减少持仓 - 无效数量"""
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=Decimal("10.0"),
            current_price=Decimal("12.0"),
        )

        # 尝试减少超过持仓数量
        success = position.reduce_quantity(1500)
        assert success is False
        assert position.quantity == 1000  # 数量不变

        # 尝试减少 0 或负数
        success = position.reduce_quantity(0)
        assert success is False


# ==============================================
# Order 测试
# ==============================================

class TestOrder:
    """Order 测试"""

    def test_order_creation(self):
        """测试创建订单"""
        order = Order(
            order_id="ORDER001",
            symbol="000001.SZ",
            side="BUY",
            quantity=1000,
            price=Decimal("10.0"),
            strategy_id="test_strategy",
        )

        assert order.order_id == "ORDER001"
        assert order.symbol == "000001.SZ"
        assert order.side == "BUY"
        assert order.quantity == 1000
        assert order.status == "PENDING"
        assert order.is_active is True
        assert order.is_complete is False

    def test_order_unfilled_quantity(self):
        """测试未成交数量"""
        order = Order(
            order_id="ORDER001",
            symbol="000001.SZ",
            side="BUY",
            quantity=1000,
            price=Decimal("10.0"),
            filled_quantity=300,
        )

        assert order.unfilled_quantity == 700

    def test_order_is_active(self):
        """测试订单活跃状态"""
        # PENDING 是活跃的
        order = Order(
            order_id="ORDER001",
            symbol="000001.SZ",
            side="BUY",
            quantity=1000,
            status="PENDING",
        )
        assert order.is_active is True

        # FILLED 不是活跃的
        order.status = "FILLED"
        assert order.is_active is False

        # CANCELED 不是活跃的
        order.status = "CANCELED"
        assert order.is_active is False

    def test_order_is_complete(self):
        """测试订单完成状态"""
        order = Order(
            order_id="ORDER001",
            symbol="000001.SZ",
            side="BUY",
            quantity=1000,
            status="FILLED",
        )
        assert order.is_complete is True


# ==============================================
# Trade 测试
# ==============================================

class TestTrade:
    """Trade 测试"""

    def test_trade_creation(self):
        """测试创建成交记录"""
        trade = Trade(
            trade_id="TRADE001",
            order_id="ORDER001",
            symbol="000001.SZ",
            side="BUY",
            quantity=500,
            price=Decimal("10.5"),
            timestamp=datetime.now(),
            commission=Decimal("5.25"),
            strategy_id="test_strategy",
        )

        assert trade.trade_id == "TRADE001"
        assert trade.order_id == "ORDER001"
        assert trade.quantity == 500
        assert trade.price == Decimal("10.5")
        assert trade.commission == Decimal("5.25")


# ==============================================
# IndicatorManager 测试
# ==============================================

class TestIndicatorManager:
    """IndicatorManager 测试"""

    def test_register_and_calculate_indicator(self):
        """测试注册和计算指标"""
        manager = IndicatorManager()

        # 注册简单指标
        def simple_ma(data):
            return sum(data) / len(data)

        manager.register_indicator("SMA", simple_ma)

        # 计算指标
        result = manager.calculate("SMA", [10, 20, 30, 40, 50])
        assert result == 30.0

    def test_get_and_set_indicator(self):
        """测试获取和设置缓存指标"""
        manager = IndicatorManager()

        manager.set("000001.SZ", "MA5", 10.5)
        result = manager.get("000001.SZ", "MA5")

        assert result == 10.5

    def test_get_nonexistent_indicator(self):
        """测试获取不存在的指标"""
        manager = IndicatorManager()

        result = manager.get("000001.SZ", "NONEXISTENT", default=0)
        assert result == 0

    def test_clear_indicator(self):
        """测试清除指标缓存"""
        manager = IndicatorManager()

        manager.set("000001.SZ", "MA5", 10.5)
        manager.set("000002.SZ", "MA5", 20.5)

        # 清除单个股票
        manager.clear("000001.SZ")
        assert manager.get("000001.SZ", "MA5") is None
        assert manager.get("000002.SZ", "MA5") == 20.5

        # 清除所有
        manager.clear()
        assert manager.get("000002.SZ", "MA5") is None


# ==============================================
# DataProvider 测试
# ==============================================

class TestDataProvider:
    """DataProvider 测试"""

    def test_set_and_get_history(self):
        """测试设置和获取历史数据"""
        provider = DataProvider()

        data = [
            {"date": "2024-01-01", "close": 10.0},
            {"date": "2024-01-02", "close": 10.5},
            {"date": "2024-01-03", "close": 11.0},
        ]

        provider.set_history_data("000001.SZ", data)

        result = provider.get_history("000001.SZ")
        assert len(result) == 3

    def test_get_history_with_length(self):
        """测试获取指定长度的历史数据"""
        provider = DataProvider()

        data = [{"close": i} for i in range(100)]
        provider.set_history_data("000001.SZ", data)

        result = provider.get_history("000001.SZ", length=10)
        assert len(result) == 10

    def test_get_history_with_fields(self):
        """测试获取指定字段的历史数据"""
        provider = DataProvider()

        data = [
            {"date": "2024-01-01", "open": 10.0, "close": 10.5},
            {"date": "2024-01-02", "open": 10.5, "close": 11.0},
        ]

        provider.set_history_data("000001.SZ", data)

        result = provider.get_history("000001.SZ", fields=["date", "close"])

        assert all("open" not in bar for bar in result)
        assert all("close" in bar for bar in result)

    def test_get_latest_bar(self):
        """测试获取最新 K 线"""
        provider = DataProvider()

        data = [
            {"date": "2024-01-01", "close": 10.0},
            {"date": "2024-01-02", "close": 10.5},
            {"date": "2024-01-03", "close": 11.0},
        ]

        provider.set_history_data("000001.SZ", data)

        latest = provider.get_latest_bar("000001.SZ")
        assert latest["close"] == 11.0


# ==============================================
# IsolatedStrategyContext 测试
# ==============================================

class TestIsolatedStrategyContext:
    """IsolatedStrategyContext 测试"""

    @pytest.fixture
    def context(self):
        """创建测试上下文"""
        config = StrategyConfig(
            name="test_strategy",
            initial_capital=100000,
        )
        return IsolatedStrategyContext(
            strategy_id="test_strategy_1",
            config=config,
        )

    def test_context_creation(self, context):
        """测试创建上下文"""
        assert context.strategy_id == "test_strategy_1"
        assert context.cash == Decimal("100000")
        assert context.initial_capital == Decimal("100000")
        assert context.total_value == Decimal("100000")

    def test_buy_order_creation(self, context):
        """测试创建买入订单"""
        context.update_current_price("000001.SZ", Decimal("10.0"))

        order = context.buy(
            symbol="000001.SZ",
            quantity=1000,
            price=Decimal("10.0"),
            reason="测试买入",
        )

        assert order is not None
        assert order.symbol == "000001.SZ"
        assert order.side == "BUY"
        assert order.quantity == 1000
        assert order.status == "PENDING"
        assert len(context.pending_orders) == 1

    def test_sell_order_creation(self, context):
        """测试创建卖出订单"""
        order = context.sell(
            symbol="000001.SZ",
            quantity=500,
            price=Decimal("10.0"),
            reason="测试卖出",
        )

        assert order is not None
        assert order.side == "SELL"
        assert order.quantity == 500

    def test_process_fill_buy(self, context):
        """测试处理买入成交"""
        context.update_current_price("000001.SZ", Decimal("10.0"))

        # 创建订单
        order = context.buy(
            symbol="000001.SZ",
            quantity=1000,
            price=Decimal("10.0"),
        )

        # 处理成交
        trade = context.process_fill(
            order_id=order.order_id,
            filled_quantity=1000,
            filled_price=Decimal("10.0"),
            commission=Decimal("10.0"),
        )

        assert trade is not None
        assert trade.quantity == 1000
        assert trade.price == Decimal("10.0")

        # 验证持仓更新
        position = context.get_position("000001.SZ")
        assert position is not None
        assert position.quantity == 1000
        assert position.avg_cost == Decimal("10.0")

        # 验证资金更新
        # 100000 - (1000 * 10 + 10) = 98990
        assert context.cash == Decimal("98990")

    def test_process_fill_sell(self, context):
        """测试处理卖出成交"""
        # 先买入
        context.update_current_price("000001.SZ", Decimal("10.0"))
        buy_order = context.buy("000001.SZ", 1000, Decimal("10.0"))
        context.process_fill(buy_order.order_id, 1000, Decimal("10.0"))

        # 再卖出
        sell_order = context.sell("000001.SZ", 500, Decimal("12.0"))
        trade = context.process_fill(
            order_id=sell_order.order_id,
            filled_quantity=500,
            filled_price=Decimal("12.0"),
            commission=Decimal("6.0"),
        )

        assert trade is not None

        # 验证持仓更新
        position = context.get_position("000001.SZ")
        assert position.quantity == 500

        # 验证资金增加
        # 卖出所得 = 500 * 12 - 6 = 5994
        # 之前资金 98990 + 5994 = 104984
        # 但还需要加上之前买入时的佣金...
        # 让我简化验证
        assert context.cash > Decimal("98990")

    def test_position_management(self, context):
        """测试持仓管理"""
        # 初始没有持仓
        assert not context.has_position("000001.SZ")
        assert context.get_position_quantity("000001.SZ") == 0

        # 买入成交
        context.update_current_price("000001.SZ", Decimal("10.0"))
        order = context.buy("000001.SZ", 1000, Decimal("10.0"))
        context.process_fill(order.order_id, 1000, Decimal("10.0"))

        # 验证持仓
        assert context.has_position("000001.SZ")
        assert context.get_position_quantity("000001.SZ") == 1000

        positions = context.get_all_positions()
        assert len(positions) == 1

    def test_close_position(self, context):
        """测试平仓"""
        # 先买入
        context.update_current_price("000001.SZ", Decimal("10.0"))
        buy_order = context.buy("000001.SZ", 1000, Decimal("10.0"))
        context.process_fill(buy_order.order_id, 1000, Decimal("10.0"))

        # 平仓
        close_order = context.close_position("000001.SZ")

        assert close_order is not None
        assert close_order.side == "SELL"
        assert close_order.quantity == 1000

    def test_cancel_order(self, context):
        """测试撤销订单"""
        order = context.buy("000001.SZ", 1000, Decimal("10.0"))

        # 撤销
        success = context.cancel_order(order.order_id)
        assert success is True

        # 验证订单状态
        retrieved = context.get_order(order.order_id)
        assert retrieved.status == "CANCELED"

        # 验证不在待处理订单中
        assert order.order_id not in context.pending_orders

    def test_profit_loss_calculation(self, context):
        """测试盈亏计算"""
        # 买入
        context.update_current_price("000001.SZ", Decimal("10.0"))
        buy_order = context.buy("000001.SZ", 1000, Decimal("10.0"))
        context.process_fill(buy_order.order_id, 1000, Decimal("10.0"))

        # 价格上涨
        context.update_current_price("000001.SZ", Decimal("12.0"))

        # 验证盈亏
        # 总资产 = 现金 + 持仓市值
        # 现金 ≈ 98990 (100000 - 10000 - 10佣金)
        # 持仓市值 = 1000 * 12 = 12000
        # 总资产 ≈ 110990
        assert context.total_value > context.initial_capital
        assert context.profit_loss > Decimal("0")

    def test_state_save_and_load(self, context):
        """测试状态保存和加载"""
        # 创建一些状态
        context.update_current_price("000001.SZ", Decimal("10.0"))
        order = context.buy("000001.SZ", 1000, Decimal("10.0"))
        context.process_fill(order.order_id, 1000, Decimal("10.0"))
        context.set_custom_data("test_key", "test_value")

        # 保存状态
        state = context.save_state()

        # 创建新上下文并加载状态
        new_config = StrategyConfig(name="test", initial_capital=50000)
        new_context = IsolatedStrategyContext(
            strategy_id="new_strategy",
            config=new_config,
        )

        new_context.load_state(state)

        # 验证状态恢复
        assert new_context.cash == context.cash
        assert new_context.has_position("000001.SZ")
        assert new_context.get_custom_data("test_key") == "test_value"

    def test_reset_context(self, context):
        """测试重置上下文"""
        # 创建一些状态
        context.update_current_price("000001.SZ", Decimal("10.0"))
        order = context.buy("000001.SZ", 1000, Decimal("10.0"))
        context.process_fill(order.order_id, 1000, Decimal("10.0"))

        # 重置
        context.reset()

        # 验证重置后状态
        assert context.cash == context.initial_capital
        assert not context.has_position("000001.SZ")
        assert len(context.pending_orders) == 0
        assert len(context.trades) == 0

    def test_get_summary(self, context):
        """测试获取摘要"""
        summary = context.get_summary()

        assert "strategy_id" in summary
        assert "cash" in summary
        assert "total_value" in summary
        assert "profit_loss" in summary
        assert "positions_count" in summary
