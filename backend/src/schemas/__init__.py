"""
Pydantic Schemas 初始化
"""

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse,
    UserListResponse,
    LoginRequest,
    LoginResponse,
    TokenPayload,
)

from .trading import (
    OrderStatus,
    OrderSide,
    ExecutionMode,
    TimeInForce,
    OrderBase,
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderListResponse,
    PositionBase,
    PositionResponse,
    PositionListResponse,
    PositionSummary,
)

from .watchlist import (
    WatchlistGroupBase,
    WatchlistGroupCreate,
    WatchlistGroupUpdate,
    WatchlistGroupResponse,
    WatchlistGroupListResponse,
    WatchlistItemBase,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
    WatchlistItemWithQuote,
    WatchlistItemListResponse,
    WatchlistItemWithQuoteListResponse,
    BatchAddItemsRequest,
    BatchRemoveItemsRequest,
    BatchMoveItemsRequest,
    BatchOperationResponse,
)

from .alert import (
    AlertType,
    PriceAlertBase,
    PriceAlertCreate,
    PriceAlertUpdate,
    PriceAlertResponse,
    PriceAlertListResponse,
    AlertHistoryBase,
    AlertHistoryResponse,
    AlertHistoryListResponse,
    AlertHistoryAcknowledge,
    AlertTriggeredMessage,
    AlertSettings,
    AlertSettingsUpdate,
)

# Strategy Version
from .strategy_version import (
    ChangeType,
    ActionType,
    StrategyVersionBase,
    StrategyVersionCreate,
    StrategyVersionResponse,
    StrategyConfigBase,
    StrategyConfigCreate,
    StrategyConfigUpdate,
    StrategyConfigResponse,
    StrategyAuditLogBase,
    StrategyAuditLogCreate,
    StrategyAuditLogResponse,
)

# Backtest Analysis
from .backtest_analysis import (
    FactorAnalysisBase,
    FactorAnalysisCreate,
    FactorAnalysisResponse,
    AttributionAnalysisBase,
    AttributionAnalysisCreate,
    AttributionAnalysisResponse,
    BacktestMetricsExtendedResponse,
)

# Trading Extended
from .trading_ext import (
    FillBase,
    FillCreate,
    FillResponse,
    FillListResponse,
    TradingCalendarBase,
    TradingCalendarResponse,
    DailyTradeStatsBase,
    DailyTradeStatsCreate,
    DailyTradeStatsResponse,
    DailyTradeStatsListResponse,
)

# Portfolio
from .portfolio import (
    PortfolioStatus,
    OptimizationMethod,
    PortfolioBase,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PositionResponse,
    PositionListResponse,
    RiskMetricsResponse,
    OptimizeResponse,
    OptimizationListResponse,
)

__all__ = [
    # User
    'UserBase',
    'UserCreate',
    'UserUpdate',
    'UserInDB',
    'UserResponse',
    'UserListResponse',
    'LoginRequest',
    'LoginResponse',
    'TokenPayload',

    # Trading
    'OrderStatus',
    'OrderSide',
    'ExecutionMode',
    'TimeInForce',
    'OrderBase',
    'OrderCreate',
    'OrderUpdate',
    'OrderResponse',
    'OrderListResponse',
    'PositionBase',
    'PositionResponse',
    'PositionListResponse',
    'PositionSummary',

    # Watchlist
    'WatchlistGroupBase',
    'WatchlistGroupCreate',
    'WatchlistGroupUpdate',
    'WatchlistGroupResponse',
    'WatchlistGroupListResponse',
    'WatchlistItemBase',
    'WatchlistItemCreate',
    'WatchlistItemUpdate',
    'WatchlistItemResponse',
    'WatchlistItemWithQuote',
    'WatchlistItemListResponse',
    'WatchlistItemWithQuoteListResponse',
    'BatchAddItemsRequest',
    'BatchRemoveItemsRequest',
    'BatchMoveItemsRequest',
    'BatchOperationResponse',

    # Alert
    'AlertType',
    'PriceAlertBase',
    'PriceAlertCreate',
    'PriceAlertUpdate',
    'PriceAlertResponse',
    'PriceAlertListResponse',
    'AlertHistoryBase',
    'AlertHistoryResponse',
    'AlertHistoryListResponse',
    'AlertHistoryAcknowledge',
    'AlertTriggeredMessage',
    'AlertSettings',
    'AlertSettingsUpdate',

    # Strategy Version
    'ChangeType',
    'ActionType',
    'StrategyVersionBase',
    'StrategyVersionCreate',
    'StrategyVersionResponse',
    'StrategyConfigBase',
    'StrategyConfigCreate',
    'StrategyConfigUpdate',
    'StrategyConfigResponse',
    'StrategyAuditLogBase',
    'StrategyAuditLogCreate',
    'StrategyAuditLogResponse',

    # Backtest Analysis
    'FactorAnalysisBase',
    'FactorAnalysisCreate',
    'FactorAnalysisResponse',
    'AttributionAnalysisBase',
    'AttributionAnalysisCreate',
    'AttributionAnalysisResponse',
    'BacktestMetricsExtendedResponse',

    # Trading Extended
    'FillBase',
    'FillCreate',
    'FillResponse',
    'FillListResponse',
    'TradingCalendarBase',
    'TradingCalendarResponse',
    'DailyTradeStatsBase',
    'DailyTradeStatsCreate',
    'DailyTradeStatsResponse',
    'DailyTradeStatsListResponse',

    # Portfolio
    'PortfolioStatus',
    'OptimizationMethod',
    'PortfolioBase',
    'PortfolioCreate',
    'PortfolioUpdate',
    'PortfolioResponse',
    'PortfolioListResponse',
    'PositionResponse',
    'PositionListResponse',
    'RiskMetricsResponse',
    'OptimizeResponse',
    'OptimizationListResponse',
]
