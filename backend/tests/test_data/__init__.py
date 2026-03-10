"""
测试数据工厂模块

提供各模块的测试数据生成函数。
"""

from .market_data import (
    create_mock_stock_list,
    create_mock_stock_detail,
    create_mock_sector_data,
    create_mock_kline_data,
    create_mock_realtime_quotes,
)
from .portfolio_data import (
    create_mock_portfolio,
    create_mock_positions,
    create_mock_risk_metrics,
    create_mock_performance_metrics,
    create_mock_optimization_result,
)
from .trading_data import (
    create_mock_orders,
    create_mock_trades,
    create_mock_account_info,
)
from .strategy_data import (
    create_mock_strategy,
    create_mock_backtest_result,
    create_mock_signal,
)

__all__ = [
    # Market Data
    'create_mock_stock_list',
    'create_mock_stock_detail',
    'create_mock_sector_data',
    'create_mock_kline_data',
    'create_mock_realtime_quotes',
    # Portfolio
    'create_mock_portfolio',
    'create_mock_positions',
    'create_mock_risk_metrics',
    'create_mock_performance_metrics',
    'create_mock_optimization_result',
    # Trading
    'create_mock_orders',
    'create_mock_trades',
    'create_mock_account_info',
    # Strategy
    'create_mock_strategy',
    'create_mock_backtest_result',
    'create_mock_signal',
]
