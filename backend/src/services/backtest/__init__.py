"""
==============================================
QuantAI Ecosystem - 回测服务模块
==============================================

提供策略回测功能和历史表现分析。
"""

from .engine import BacktestEngine
from .models import (
    BacktestConfig,
    BacktestResult,
    BacktestMetrics,
    Trade,
    EquityCurve,
)

__all__ = [
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    "BacktestMetrics",
    "Trade",
    "EquityCurve",
]
