"""
策略注册表单元测试

测试策略注册、发现、实例化等功能。
"""

import pytest
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from src.services.strategy.registry import (
    StrategyRegistry,
    StrategyMetadata,
    StrategyFrequency,
    StrategyLifecycleStatus,
    strategy,
    strategy_registry,
)
from src.services.strategy.base import (
    StrategyBase,
    StrategyConfig,
    StrategyContext,
    Signal,
    SignalType,
)


# ==============================================
# 测试策略类
# ==============================================

class TestStrategyA(StrategyBase):
    """测试策略 A"""

    def initialize(self, context: StrategyContext) -> None:
        pass

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        return None

    def finalize(self, context: StrategyContext) -> None:
        pass


class TestStrategyB(StrategyBase):
    """测试策略 B"""

    def initialize(self, context: StrategyContext) -> None:
        pass

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        return None

    def finalize(self, context: StrategyContext) -> None:
        pass


# ==============================================
# StrategyMetadata 测试
# ==============================================

class TestStrategyMetadata:
    """StrategyMetadata 测试"""

    def test_metadata_creation(self):
        """测试创建元数据"""
        metadata = StrategyMetadata(
            strategy_id="test_strategy",
            name="测试策略",
            strategy_class=TestStrategyA,
            version="1.0.0",
            author="Test Author",
            description="测试描述",
            category="test",
        )

        assert metadata.strategy_id == "test_strategy"
        assert metadata.name == "测试策略"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.category == "test"
        assert metadata.frequency == StrategyFrequency.DAILY
        assert metadata.status == StrategyLifecycleStatus.DEVELOPMENT

    def test_metadata_to_dict(self):
        """测试转换为字典"""
        metadata = StrategyMetadata(
            strategy_id="test",
            name="测试",
            strategy_class=TestStrategyA,
            tags=["tag1", "tag2"],
        )

        result = metadata.to_dict()

        assert result["strategy_id"] == "test"
        assert result["name"] == "测试"
        assert result["tags"] == ["tag1", "tag2"]
        assert "frequency" in result
        assert "status" in result

    def test_validate_params_success(self):
        """测试参数验证成功"""
        schema = {
            "required": ["period"],
            "properties": {
                "period": {"type": "integer"},
                "threshold": {"type": "number"},
            }
        }

        metadata = StrategyMetadata(
            strategy_id="test",
            name="测试",
            strategy_class=TestStrategyA,
            params_schema=schema,
        )

        params = {"period": 20, "threshold": 0.5}
        is_valid, error = metadata.validate_params(params)

        assert is_valid is True
        assert error is None

    def test_validate_params_missing_required(self):
        """测试参数验证失败 - 缺少必需参数"""
        schema = {
            "required": ["period"],
            "properties": {
                "period": {"type": "integer"},
            }
        }

        metadata = StrategyMetadata(
            strategy_id="test",
            name="测试",
            strategy_class=TestStrategyA,
            params_schema=schema,
        )

        params = {"threshold": 0.5}
        is_valid, error = metadata.validate_params(params)

        assert is_valid is False
        assert "缺少必需参数" in error

    def test_validate_params_wrong_type(self):
        """测试参数验证失败 - 类型错误"""
        schema = {
            "required": [],
            "properties": {
                "period": {"type": "integer"},
            }
        }

        metadata = StrategyMetadata(
            strategy_id="test",
            name="测试",
            strategy_class=TestStrategyA,
            params_schema=schema,
        )

        params = {"period": "not_an_integer"}
        is_valid, error = metadata.validate_params(params)

        assert is_valid is False
        assert "类型错误" in error


# ==============================================
# StrategyRegistry 测试
# ==============================================

class TestStrategyRegistry:
    """StrategyRegistry 测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前清空注册表"""
        strategy_registry.clear()

    def test_singleton_pattern(self):
        """测试单例模式"""
        registry1 = StrategyRegistry()
        registry2 = StrategyRegistry()

        assert registry1 is registry2
        assert registry1 is strategy_registry

    def test_register_with_decorator(self):
        """测试使用装饰器注册策略"""
        @strategy(
            strategy_id="decorated_strategy",
            name="装饰器注册的策略",
            category="trend",
            tags=["ma", "trend"],
        )
        class DecoratedStrategy(StrategyBase):
            def initialize(self, context): pass
            def on_data(self, context): return None
            def finalize(self, context): pass

        # 验证注册成功
        metadata = strategy_registry.get_strategy("decorated_strategy")
        assert metadata is not None
        assert metadata.name == "装饰器注册的策略"
        assert metadata.category == "trend"
        assert "ma" in metadata.tags

    def test_register_class_manually(self):
        """测试手动注册策略类"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="manual_strategy",
            name="手动注册的策略",
            category="test",
        )

        metadata = strategy_registry.get_strategy("manual_strategy")
        assert metadata is not None
        assert metadata.name == "手动注册的策略"

    def test_unregister_strategy(self):
        """测试注销策略"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="to_remove",
            name="将被删除的策略",
        )

        # 确认存在
        assert strategy_registry.get_strategy("to_remove") is not None

        # 注销
        success = strategy_registry.unregister("to_remove")
        assert success is True
        assert strategy_registry.get_strategy("to_remove") is None

        # 再次注销应该失败
        success = strategy_registry.unregister("to_remove")
        assert success is False

    def test_list_strategies(self):
        """测试列出策略"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="strategy_1",
            name="策略1",
            category="trend",
        )
        strategy_registry.register_class(
            TestStrategyB,
            strategy_id="strategy_2",
            name="策略2",
            category="mean_reversion",
        )
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="strategy_3",
            name="策略3",
            category="trend",
        )

        # 列出所有
        all_strategies = strategy_registry.list_strategies()
        assert len(all_strategies) == 3

        # 按分类过滤
        trend_strategies = strategy_registry.list_strategies(category="trend")
        assert len(trend_strategies) == 2

    def test_create_instance(self):
        """测试创建策略实例"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="test_instance_strategy",
            name="测试实例策略",
            default_params={"param1": 10},
        )

        # 创建实例
        instance = strategy_registry.create_instance(
            strategy_id="test_instance_strategy",
            params={"param2": 20},
        )

        assert instance is not None
        assert instance.parameters["param1"] == 10  # 默认参数
        assert instance.parameters["param2"] == 20  # 传入参数

    def test_create_multiple_instances(self):
        """测试创建多个实例"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="multi_instance_strategy",
            name="多实例策略",
        )

        # 创建多个实例
        instance1 = strategy_registry.create_instance(
            strategy_id="multi_instance_strategy",
            params={"value": 1},
        )
        instance2 = strategy_registry.create_instance(
            strategy_id="multi_instance_strategy",
            params={"value": 2},
        )

        assert instance1 is not instance2
        assert instance1.parameters["value"] == 1
        assert instance2.parameters["value"] == 2

    def test_create_instance_with_custom_id(self):
        """测试使用自定义 ID 创建实例"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="custom_id_strategy",
            name="自定义ID策略",
        )

        instance = strategy_registry.create_instance(
            strategy_id="custom_id_strategy",
            instance_id="my_custom_id",
        )

        # 验证可以使用自定义 ID 获取实例
        retrieved = strategy_registry.get_instance("my_custom_id")
        assert retrieved is instance

    def test_create_instance_invalid_strategy(self):
        """测试创建不存在的策略实例"""
        with pytest.raises(ValueError) as exc_info:
            strategy_registry.create_instance(strategy_id="non_existent")

        assert "策略不存在" in str(exc_info.value)

    def test_create_instance_invalid_params(self):
        """测试使用无效参数创建实例"""
        schema = {
            "required": ["required_param"],
            "properties": {
                "required_param": {"type": "integer"},
            }
        }

        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="strict_params_strategy",
            name="严格参数策略",
            params_schema=schema,
        )

        with pytest.raises(ValueError) as exc_info:
            strategy_registry.create_instance(
                strategy_id="strict_params_strategy",
                params={},  # 缺少必需参数
            )

        assert "参数验证失败" in str(exc_info.value)

    def test_update_strategy_status(self):
        """测试更新策略状态"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="status_test_strategy",
            name="状态测试策略",
        )

        # 更新状态
        success = strategy_registry.update_strategy_status(
            strategy_id="status_test_strategy",
            status=StrategyLifecycleStatus.BACKTEST_PASSED,
        )

        assert success is True

        metadata = strategy_registry.get_strategy("status_test_strategy")
        assert metadata.status == StrategyLifecycleStatus.BACKTEST_PASSED

    def test_get_strategies_by_status(self):
        """测试按状态获取策略"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="dev_strategy",
            name="开发中策略",
            status=StrategyLifecycleStatus.DEVELOPMENT,
        )
        strategy_registry.register_class(
            TestStrategyB,
            strategy_id="live_strategy",
            name="实盘策略",
            status=StrategyLifecycleStatus.LIVE_TRADING,
        )

        live_strategies = strategy_registry.get_strategies_by_status(
            StrategyLifecycleStatus.LIVE_TRADING
        )

        assert len(live_strategies) == 1
        assert live_strategies[0].strategy_id == "live_strategy"

    def test_list_instances(self):
        """测试列出所有实例"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="list_instances_strategy",
            name="列表实例策略",
        )

        # 创建多个实例
        strategy_registry.create_instance(strategy_id="list_instances_strategy")
        strategy_registry.create_instance(strategy_id="list_instances_strategy")

        instances = strategy_registry.list_instances()
        assert len(instances) == 2

    def test_remove_instance(self):
        """测试移除实例"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="remove_instance_strategy",
            name="移除实例策略",
        )

        instance = strategy_registry.create_instance(
            strategy_id="remove_instance_strategy",
            instance_id="instance_to_remove",
        )

        # 移除实例
        success = strategy_registry.remove_instance("instance_to_remove")
        assert success is True

        # 验证已移除
        assert strategy_registry.get_instance("instance_to_remove") is None

    def test_export_registry(self):
        """测试导出注册表"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="export_test",
            name="导出测试策略",
        )
        strategy_registry.create_instance(strategy_id="export_test")

        exported = strategy_registry.export_registry()

        assert "strategies" in exported
        assert "total_strategies" in exported
        assert "total_instances" in exported
        assert exported["total_strategies"] >= 1
        assert exported["total_instances"] >= 1

    def test_clear_registry(self):
        """测试清空注册表"""
        strategy_registry.register_class(
            TestStrategyA,
            strategy_id="clear_test",
            name="清空测试策略",
        )
        strategy_registry.create_instance(strategy_id="clear_test")

        strategy_registry.clear()

        assert strategy_registry.get_strategy("clear_test") is None
        assert len(strategy_registry.list_strategies()) == 0
        assert len(strategy_registry.list_instances()) == 0


# ==============================================
# 枚举类型测试
# ==============================================

class TestEnums:
    """枚举类型测试"""

    def test_strategy_frequency(self):
        """测试策略频率枚举"""
        assert StrategyFrequency.DAILY.value == "1d"
        assert StrategyFrequency.MIN_1.value == "1m"
        assert StrategyFrequency.HOUR_1.value == "1h"

    def test_strategy_lifecycle_status(self):
        """测试策略生命周期状态枚举"""
        assert StrategyLifecycleStatus.DEVELOPMENT.value == "development"
        assert StrategyLifecycleStatus.LIVE_TRADING.value == "live_trading"
        assert StrategyLifecycleStatus.DEPRECATED.value == "deprecated"

    def test_enum_from_string(self):
        """测试从字符串创建枚举"""
        freq = StrategyFrequency("1d")
        assert freq == StrategyFrequency.DAILY

        status = StrategyLifecycleStatus("live_trading")
        assert status == StrategyLifecycleStatus.LIVE_TRADING
