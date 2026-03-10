"""
策略注册表模块

提供策略的动态注册、自动发现和实例化功能。
支持装饰器注册和目录扫描自动注册。

参考设计：
- Vn.py 的策略加载机制
- Backtrader 的策略注册模式
"""

import os
import importlib
import inspect
import logging
from typing import Dict, List, Type, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from decimal import Decimal

from .base import StrategyBase, StrategyConfig, StrategyStatus

logger = logging.getLogger(__name__)


# ==============================================
# 枚举类型
# ==============================================

class StrategyFrequency(str, Enum):
    """策略运行频率"""
    TICK = "tick"      # Tick 级别
    MIN_1 = "1m"       # 1分钟
    MIN_5 = "5m"       # 5分钟
    MIN_15 = "15m"     # 15分钟
    MIN_30 = "30m"     # 30分钟
    HOUR_1 = "1h"      # 1小时
    HOUR_4 = "4h"      # 4小时
    DAILY = "1d"       # 日线
    WEEKLY = "1w"      # 周线


class StrategyLifecycleStatus(str, Enum):
    """策略生命周期状态"""
    DEVELOPMENT = "development"      # 开发中
    TESTING = "testing"              # 测试中
    BACKTEST_PASSED = "backtest_passed"  # 回测通过
    PAPER_TRADING = "paper_trading"  # 模拟交易
    LIVE_TRADING = "live_trading"    # 实盘交易
    DEPRECATED = "deprecated"        # 已废弃
    SUSPENDED = "suspended"          # 已暂停


# ==============================================
# 策略元数据
# ==============================================

@dataclass
class StrategyMetadata:
    """
    策略元数据

    包含策略的完整描述信息，用于注册和展示。
    """
    strategy_id: str                           # 唯一标识符
    name: str                                  # 显示名称
    strategy_class: Type[StrategyBase]         # 策略类
    version: str = "1.0.0"                     # 版本号
    author: str = ""                           # 作者
    description: str = ""                      # 描述
    category: str = "general"                  # 分类（趋势、均值回归、套利等）
    frequency: StrategyFrequency = StrategyFrequency.DAILY  # 运行频率
    status: StrategyLifecycleStatus = StrategyLifecycleStatus.DEVELOPMENT  # 生命周期状态
    tags: List[str] = field(default_factory=list)  # 标签
    params_schema: Dict[str, Any] = field(default_factory=dict)  # 参数 JSON Schema
    default_params: Dict[str, Any] = field(default_factory=dict)  # 默认参数
    min_history_bars: int = 0                  # 最小历史 K 线数量
    supported_markets: List[str] = field(default_factory=lambda: ["A股"])  # 支持的市场
    risk_level: str = "medium"                 # 风险等级（low/medium/high）

    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.frequency, str):
            self.frequency = StrategyFrequency(self.frequency)
        if isinstance(self.status, str):
            self.status = StrategyLifecycleStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "category": self.category,
            "frequency": self.frequency.value,
            "status": self.status.value,
            "tags": self.tags,
            "params_schema": self.params_schema,
            "default_params": self.default_params,
            "min_history_bars": self.min_history_bars,
            "supported_markets": self.supported_markets,
            "risk_level": self.risk_level,
        }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证参数是否符合 schema

        Args:
            params: 待验证的参数字典

        Returns:
            (是否有效, 错误信息)
        """
        if not self.params_schema:
            return True, None

        # 简单的参数验证逻辑
        # 实际项目中可以使用 jsonschema 库进行完整验证
        required = self.params_schema.get("required", [])
        properties = self.params_schema.get("properties", {})

        # 检查必需参数
        for req in required:
            if req not in params:
                return False, f"缺少必需参数: {req}"

        # 检查参数类型
        for key, value in params.items():
            if key in properties:
                prop = properties[key]
                expected_type = prop.get("type")
                if expected_type:
                    type_map = {
                        "string": str,
                        "number": (int, float, Decimal),
                        "integer": int,
                        "boolean": bool,
                        "array": list,
                        "object": dict,
                    }
                    if expected_type in type_map:
                        if not isinstance(value, type_map[expected_type]):
                            return False, f"参数 {key} 类型错误，期望 {expected_type}"

        return True, None


# ==============================================
# 策略注册表
# ==============================================

class StrategyRegistry:
    """
    策略注册表（单例模式）

    提供策略的注册、发现和实例化功能。

    使用方式：
        # 方式一：装饰器注册
        @strategy_registry.register(
            strategy_id="ma_cross",
            name="双均线策略",
            ...
        )
        class MovingAverageStrategy(StrategyBase):
            ...

        # 方式二：手动注册
        strategy_registry.register_class(MovingAverageStrategy, metadata)

        # 方式三：目录扫描
        strategy_registry.scan_directory("./strategies")
    """

    _instance: Optional['StrategyRegistry'] = None

    def __new__(cls) -> 'StrategyRegistry':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化注册表"""
        if self._initialized:
            return

        self._strategies: Dict[str, StrategyMetadata] = {}
        self._strategy_instances: Dict[str, StrategyBase] = {}
        self._instance_counter: Dict[str, int] = {}
        self._initialized = True

        logger.info("策略注册表初始化完成")

    def register(
        self,
        strategy_id: str,
        name: str,
        version: str = "1.0.0",
        author: str = "",
        description: str = "",
        category: str = "general",
        frequency: StrategyFrequency = StrategyFrequency.DAILY,
        status: StrategyLifecycleStatus = StrategyLifecycleStatus.DEVELOPMENT,
        tags: List[str] = None,
        params_schema: Dict[str, Any] = None,
        default_params: Dict[str, Any] = None,
        min_history_bars: int = 0,
        supported_markets: List[str] = None,
        risk_level: str = "medium",
    ) -> Callable[[Type[StrategyBase]], Type[StrategyBase]]:
        """
        装饰器方式注册策略

        Args:
            strategy_id: 策略唯一标识
            name: 策略名称
            version: 版本号
            author: 作者
            description: 描述
            category: 分类
            frequency: 运行频率
            status: 生命周期状态
            tags: 标签
            params_schema: 参数 JSON Schema
            default_params: 默认参数
            min_history_bars: 最小历史 K 线数量
            supported_markets: 支持的市场
            risk_level: 风险等级

        Returns:
            装饰器函数
        """
        def decorator(cls: Type[StrategyBase]) -> Type[StrategyBase]:
            if not issubclass(cls, StrategyBase):
                raise TypeError(f"{cls.__name__} 必须继承自 StrategyBase")

            metadata = StrategyMetadata(
                strategy_id=strategy_id,
                name=name,
                strategy_class=cls,
                version=version,
                author=author,
                description=description,
                category=category,
                frequency=frequency,
                status=status,
                tags=tags or [],
                params_schema=params_schema or {},
                default_params=default_params or {},
                min_history_bars=min_history_bars,
                supported_markets=supported_markets or ["A股"],
                risk_level=risk_level,
            )

            self._register_metadata(metadata)
            return cls

        return decorator

    def register_class(
        self,
        strategy_class: Type[StrategyBase],
        metadata: StrategyMetadata = None,
        **kwargs
    ) -> None:
        """
        手动注册策略类

        Args:
            strategy_class: 策略类
            metadata: 策略元数据（可选，如果不提供则使用 kwargs 创建）
            **kwargs: 元数据参数（当 metadata 为 None 时使用）
        """
        if not issubclass(strategy_class, StrategyBase):
            raise TypeError(f"{strategy_class.__name__} 必须继承自 StrategyBase")

        if metadata is None:
            metadata = StrategyMetadata(
                strategy_id=kwargs.get("strategy_id", strategy_class.__name__),
                name=kwargs.get("name", strategy_class.__name__),
                strategy_class=strategy_class,
                **{k: v for k, v in kwargs.items() if k not in ["strategy_id", "name"]}
            )
        else:
            metadata.strategy_class = strategy_class

        self._register_metadata(metadata)

    def _register_metadata(self, metadata: StrategyMetadata) -> None:
        """注册元数据到注册表"""
        if metadata.strategy_id in self._strategies:
            logger.warning(
                f"策略 {metadata.strategy_id} 已存在，将被覆盖"
            )

        self._strategies[metadata.strategy_id] = metadata
        logger.info(
            f"注册策略: {metadata.strategy_id} ({metadata.name} v{metadata.version})"
        )

    def unregister(self, strategy_id: str) -> bool:
        """
        注销策略

        Args:
            strategy_id: 策略 ID

        Returns:
            是否成功注销
        """
        if strategy_id in self._strategies:
            del self._strategies[strategy_id]
            logger.info(f"注销策略: {strategy_id}")
            return True
        return False

    def get_strategy(self, strategy_id: str) -> Optional[StrategyMetadata]:
        """
        获取策略元数据

        Args:
            strategy_id: 策略 ID

        Returns:
            策略元数据或 None
        """
        return self._strategies.get(strategy_id)

    def list_strategies(
        self,
        category: str = None,
        status: StrategyLifecycleStatus = None,
        frequency: StrategyFrequency = None,
        tags: List[str] = None,
    ) -> List[StrategyMetadata]:
        """
        列出策略

        Args:
            category: 按分类过滤
            status: 按状态过滤
            frequency: 按频率过滤
            tags: 按标签过滤（满足任一标签即可）

        Returns:
            策略元数据列表
        """
        result = list(self._strategies.values())

        if category:
            result = [s for s in result if s.category == category]

        if status:
            result = [s for s in result if s.status == status]

        if frequency:
            result = [s for s in result if s.frequency == frequency]

        if tags:
            result = [s for s in result if any(t in s.tags for t in tags)]

        return result

    def create_instance(
        self,
        strategy_id: str,
        config: StrategyConfig = None,
        params: Dict[str, Any] = None,
        instance_id: str = None,
    ) -> StrategyBase:
        """
        创建策略实例

        支持同一策略类创建多个实例（不同参数）。

        Args:
            strategy_id: 策略 ID
            config: 策略配置
            params: 策略参数（会与默认参数合并）
            instance_id: 实例 ID（如果不提供则自动生成）

        Returns:
            策略实例
        """
        metadata = self.get_strategy(strategy_id)
        if metadata is None:
            raise ValueError(f"策略不存在: {strategy_id}")

        # 合并默认参数和用户参数
        final_params = {**metadata.default_params}
        if params:
            final_params.update(params)

        # 验证参数
        is_valid, error_msg = metadata.validate_params(final_params)
        if not is_valid:
            raise ValueError(f"参数验证失败: {error_msg}")

        # 创建配置
        if config is None:
            config = StrategyConfig(
                name=metadata.name,
                description=metadata.description,
                parameters=final_params,
            )
        else:
            config.parameters = {**config.parameters, **final_params}

        # 创建策略实例
        strategy_instance = metadata.strategy_class(config)

        # 生成实例 ID
        if instance_id is None:
            if strategy_id not in self._instance_counter:
                self._instance_counter[strategy_id] = 0
            self._instance_counter[strategy_id] += 1
            instance_id = f"{strategy_id}_{self._instance_counter[strategy_id]}"

        # 存储实例
        self._strategy_instances[instance_id] = strategy_instance

        logger.info(
            f"创建策略实例: {instance_id} (strategy_id={strategy_id}, params={final_params})"
        )

        return strategy_instance

    def get_instance(self, instance_id: str) -> Optional[StrategyBase]:
        """
        获取策略实例

        Args:
            instance_id: 实例 ID

        Returns:
            策略实例或 None
        """
        return self._strategy_instances.get(instance_id)

    def remove_instance(self, instance_id: str) -> bool:
        """
        移除策略实例

        Args:
            instance_id: 实例 ID

        Returns:
            是否成功移除
        """
        if instance_id in self._strategy_instances:
            del self._strategy_instances[instance_id]
            logger.info(f"移除策略实例: {instance_id}")
            return True
        return False

    def list_instances(self) -> Dict[str, StrategyBase]:
        """
        列出所有策略实例

        Returns:
            {instance_id: strategy_instance}
        """
        return self._strategy_instances.copy()

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
    ) -> int:
        """
        扫描目录自动注册策略

        扫描指定目录下的所有 Python 文件，查找并注册策略类。

        Args:
            directory: 目录路径
            recursive: 是否递归扫描子目录

        Returns:
            注册的策略数量
        """
        registered_count = 0
        directory_path = Path(directory)

        if not directory_path.exists():
            logger.warning(f"目录不存在: {directory}")
            return 0

        # 获取所有 Python 文件
        if recursive:
            pattern = "**/*.py"
        else:
            pattern = "*.py"

        py_files = list(directory_path.glob(pattern))

        for py_file in py_files:
            if py_file.name.startswith("_"):
                continue

            try:
                # 构建模块路径
                relative_path = py_file.relative_to(directory_path.parent)
                module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")

                # 动态导入模块
                module = importlib.import_module(module_path)

                # 查找策略类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, StrategyBase) and
                        obj is not StrategyBase and
                        obj.__module__ == module_path):

                        # 检查是否已经注册（通过装饰器）
                        # 如果没有注册，则自动注册
                        strategy_id = obj.__name__
                        if strategy_id not in self._strategies:
                            self.register_class(
                                obj,
                                strategy_id=strategy_id,
                                name=obj.__name__,
                            )
                            registered_count += 1

            except Exception as e:
                logger.warning(f"扫描文件 {py_file} 失败: {e}")
                continue

        logger.info(
            f"扫描目录 {directory} 完成，注册 {registered_count} 个策略"
        )
        return registered_count

    def update_strategy_status(
        self,
        strategy_id: str,
        status: StrategyLifecycleStatus
    ) -> bool:
        """
        更新策略状态

        Args:
            strategy_id: 策略 ID
            status: 新状态

        Returns:
            是否成功更新
        """
        metadata = self.get_strategy(strategy_id)
        if metadata is None:
            return False

        old_status = metadata.status
        metadata.status = status
        logger.info(
            f"更新策略状态: {strategy_id} ({old_status.value} -> {status.value})"
        )
        return True

    def get_strategies_by_status(
        self,
        status: StrategyLifecycleStatus
    ) -> List[StrategyMetadata]:
        """
        按状态获取策略列表

        Args:
            status: 策略状态

        Returns:
            策略列表
        """
        return [s for s in self._strategies.values() if s.status == status]

    def export_registry(self) -> Dict[str, Any]:
        """
        导出注册表信息

        Returns:
            注册表信息字典
        """
        return {
            "strategies": {
                sid: metadata.to_dict()
                for sid, metadata in self._strategies.items()
            },
            "total_strategies": len(self._strategies),
            "total_instances": len(self._strategy_instances),
            "instance_counter": self._instance_counter.copy(),
        }

    def clear(self) -> None:
        """清空注册表"""
        self._strategies.clear()
        self._strategy_instances.clear()
        self._instance_counter.clear()
        logger.info("注册表已清空")


# ==============================================
# 全局注册表实例
# ==============================================

# 全局单例实例
strategy_registry = StrategyRegistry()


# ==============================================
# 便捷装饰器
# ==============================================

def strategy(
    strategy_id: str,
    name: str,
    **kwargs
) -> Callable[[Type[StrategyBase]], Type[StrategyBase]]:
    """
    策略注册便捷装饰器

    使用方式：
        @strategy("ma_cross", "双均线策略", category="趋势")
        class MovingAverageStrategy(StrategyBase):
            ...

    Args:
        strategy_id: 策略唯一标识
        name: 策略名称
        **kwargs: 其他元数据参数

    Returns:
        装饰器函数
    """
    return strategy_registry.register(
        strategy_id=strategy_id,
        name=name,
        **kwargs
    )
