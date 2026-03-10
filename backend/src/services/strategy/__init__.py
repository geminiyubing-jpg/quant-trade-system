"""
策略服务模块初始化

包含：
- 策略基类和接口
- 策略注册表
- 隔离上下文
- 策略引擎
- 策略管理器
- 示例策略
"""

from .base import (
    # Enums
    SignalType,
    StrategyStatus,
    # Data Classes
    Signal,
    StrategyConfig,
    BacktestConfig,
    # Base Classes
    StrategyBase,
    StrategyContext,
    # Exceptions
    StrategyError,
    StrategyValidationError,
    StrategyExecutionError,
)

from .registry import (
    # Enums
    StrategyFrequency,
    StrategyLifecycleStatus,
    # Data Classes
    StrategyMetadata,
    # Registry
    StrategyRegistry,
    strategy_registry,
    # Decorators
    strategy,
)

from .context import (
    # Data Classes
    Position,
    Order,
    Trade,
    # Managers
    IndicatorManager,
    DataProvider,
    # Context
    IsolatedStrategyContext,
)

from .examples import (
    BuyAndHoldStrategy,
    MovingAverageStrategy,
    MeanReversionStrategy,
)

from .engine import (
    ExecutionResult,
    StrategyEngine,
    SignalConverter,
)

__all__ = [
    # Enums
    'SignalType',
    'StrategyStatus',
    'StrategyFrequency',
    'StrategyLifecycleStatus',
    # Data Classes
    'Signal',
    'StrategyConfig',
    'BacktestConfig',
    'StrategyMetadata',
    'Position',
    'Order',
    'Trade',
    # Base Classes
    'StrategyBase',
    'StrategyContext',
    # Managers
    'IndicatorManager',
    'DataProvider',
    # Context
    'IsolatedStrategyContext',
    # Registry
    'StrategyRegistry',
    'strategy_registry',
    'strategy',
    # Exceptions
    'StrategyError',
    'StrategyValidationError',
    'StrategyExecutionError',
    # Examples
    'BuyAndHoldStrategy',
    'MovingAverageStrategy',
    'MeanReversionStrategy',
    # Engine
    'ExecutionResult',
    'StrategyEngine',
    'SignalConverter',
]
