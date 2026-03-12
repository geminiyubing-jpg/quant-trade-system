"""
OpenBB Platform 数据适配器模块

提供 OpenBB Platform 的数据集成功能，包括：
- 股票数据（美股、国际市场）
- 宏观经济数据（FRED、OECD、IMF）
- 技术分析指标（RSI、MACD、布林带等）
- 量化分析工具（CAPM、夏普比率等）
"""

from .adapter import OpenBBAdapter
from .providers.equity import EquityProvider
from .providers.economy import EconomyProvider
from .providers.technical import TechnicalProvider

__all__ = [
    "OpenBBAdapter",
    "EquityProvider",
    "EconomyProvider",
    "TechnicalProvider",
]
