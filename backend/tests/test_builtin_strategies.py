"""
内置策略单元测试
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestRSIFunctions:
    """RSI函数测试"""

    def test_calculate_rsi_normal(self):
        """测试RSI计算 - 正常情况"""
        from src.strategies.builtin.rsi import calculate_rsi

        # 模拟价格上涨的价格序列
        prices = [100 + i for i in range(20)]
        rsi = calculate_rsi(prices, 14)
        assert 0 <= rsi <= 100
        assert rsi > 50  # 上涨趋势应该RSI较高

    def test_calculate_rsi_oversold(self):
        """测试RSI计算 - 超卖"""
        from src.strategies.builtin.rsi import calculate_rsi

        # 模拟价格下跌的价格序列
        prices = [100 - i for i in range(20)]
        rsi = calculate_rsi(prices, 14)
        assert 0 <= rsi <= 100
        assert rsi < 50  # 下跌趋势应该RSI较低

    def test_calculate_rsi_short_data(self):
        """测试RSI计算 - 数据不足"""
        from src.strategies.builtin.rsi import calculate_rsi

        prices = [100, 101]
        rsi = calculate_rsi(prices, 14)
        assert rsi == 50.0  # 默认返回中性值


class TestBollingerFunctions:
    """布林带函数测试"""

    def test_calculate_bollinger(self):
        """测试布林带计算"""
        from src.strategies.builtin.bollinger import calculate_bollinger

        prices = [100] * 20  # 稳定价格
        result = calculate_bollinger(prices, 20, 2.0)

        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert "bandwidth" in result

        # 稳定价格时，带宽为0
        assert result["bandwidth"] == 0

    def test_calculate_bollinger_volatile(self):
        """测试布林带计算 - 波动价格"""
        from src.strategies.builtin.bollinger import calculate_bollinger

        prices = [100 + (i % 2) * 10 for i in range(20)]  # 波动价格
        result = calculate_bollinger(prices, 20, 2.0)

        assert result["upper"] > result["middle"]
        assert result["middle"] > result["lower"]
        assert result["bandwidth"] > 0

    def test_calculate_bollinger_position(self):
        """测试价格位置计算"""
        from src.strategies.builtin.bollinger import calculate_bollinger_position

        # 价格在下轨
        pos = calculate_bollinger_position(90, 110, 100, 90)
        assert pos == 0.0

        # 价格在中轨
        pos = calculate_bollinger_position(100, 110, 100, 90)
        assert pos == 0.5

        # 价格在上轨
        pos = calculate_bollinger_position(110, 110, 100, 90)
        assert pos == 1.0


class TestStrategyRegistry:
    """策略注册表测试"""

    def test_strategies_are_registered(self):
        """测试策略是否正确注册"""
        from src.services.strategy.registry import strategy_registry

        # 检查内置策略是否已注册
        expected_strategies = ["ma_cross", "momentum", "mean_reversion", "rsi", "bollinger"]

        for strategy_id in expected_strategies:
            strategy = strategy_registry.get_strategy(strategy_id)
            assert strategy is not None, f"策略 {strategy_id} 未注册"

    def test_strategy_metadata(self):
        """测试策略元数据"""
        from src.services.strategy.registry import strategy_registry

        # 获取RSI策略元数据
        rsi_meta = strategy_registry.get_strategy("rsi")
        assert rsi_meta is not None
        assert rsi_meta.name == "RSI策略"
        assert rsi_meta.category == "oscillator"

    def test_get_strategies_by_category(self):
        """测试按类别获取策略"""
        from src.services.strategy.registry import strategy_registry

        # 获取所有趋势类策略
        trend_strategies = strategy_registry.get_strategies_by_category("trend")
        assert len(trend_strategies) > 0

    def test_get_all_strategies(self):
        """测试获取所有策略"""
        from src.services.strategy.registry import strategy_registry

        all_strategies = strategy_registry.list_strategies()
        assert len(all_strategies) >= 5  # 至少5个内置策略


class TestStrategyBase:
    """策略基类测试"""

    def test_strategy_parameters(self):
        """测试策略参数"""
        from src.strategies.builtin.moving_average import MovingAverageStrategy
        from src.services.strategy.base import StrategyConfig

        config = StrategyConfig(
            name="test_ma",
            parameters={"fast_period": 5, "slow_period": 10, "position_size": 0.3}
        )

        strategy = MovingAverageStrategy(config)
        assert strategy.parameters.get("fast_period") == 5
        assert strategy.parameters.get("slow_period") == 10

    def test_strategy_status(self):
        """测试策略状态"""
        from src.strategies.builtin.momentum import MomentumStrategy
        from src.services.strategy.base import StrategyConfig, StrategyStatus

        config = StrategyConfig(name="test_momentum")
        strategy = MomentumStrategy(config)

        # 初始状态应该是STOPPED
        assert strategy.status == StrategyStatus.STOPPED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
