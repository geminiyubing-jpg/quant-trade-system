"""
投资组合相关的 Pydantic Schemas

投资组合管理、持仓管理、风险分析、 组合优化
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class PortfolioStatus(str, Enum):
    """投资组合状态"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


class OptimizationMethod(str, Enum):
    """优化方法"""
    MEAN_VARIANCE = "MEAN_VARIANCE"
    RISK_PARITY = "RISK_PARITY"
    MIN_VARIANCE = "MIN_VARIANCE"
    MAX_SHARPE = "MAX_SHARPE"
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    BLACK_LITTERMAN = "BLACK_LITTERMAN"


# ==============================================
# 投资组合 Schema
# ==============================================

class PortfolioBase(BaseModel):
    """投资组合基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    benchmark_symbol: Optional[str] = None
    target_allocation: Optional[Dict[str, float]] = None
    rebalance_threshold: Decimal = Field(default=Decimal("0.05"))
    rebalance_frequency: str = Field(default="MONTHLY")
    execution_mode: str = Field(default="PAPER")
    initial_capital: Optional[Decimal] = None


class PortfolioCreate(PortfolioBase):
    """投资组合创建 Schema"""
    pass


class PortfolioUpdate(BaseModel):
    """投资组合更新 Schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    benchmark_symbol: Optional[str] = None
    target_allocation: Optional[Dict[str, float]] = None
    rebalance_threshold: Optional[Decimal] = None
    rebalance_frequency: Optional[str] = None
    status: Optional[PortfolioStatus] = None


class PortfolioResponse(PortfolioBase):
    """投资组合响应 Schema"""
    id: str
    user_id: str
    base_currency: str
    status: PortfolioStatus
    total_value: Decimal
    cash_balance: Decimal
    inception_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioListResponse(BaseModel):
    """投资组合列表响应 Schema"""
    total: int
    items: List[PortfolioResponse]


# ==============================================
# 组合持仓 Schema
# ==============================================

class PositionResponse(BaseModel):
    """组合持仓响应 Schema"""
    id: str
    portfolio_id: str
    symbol: str
    quantity: int
    avg_cost: Decimal
    current_price: Optional[Decimal]
    market_value: Optional[Decimal]
    weight: Optional[Decimal]
    target_weight: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]
    realized_pnl: Optional[Decimal]
    sector: Optional[str]
    industry: Optional[str]
    status: str

    model_config = ConfigDict(from_attributes=True)


class PositionListResponse(BaseModel):
    """持仓列表响应 Schema"""
    total: int
    items: List[PositionResponse]


# ==============================================
# 风险指标 Schema
# ==============================================

class RiskMetricsResponse(BaseModel):
    """风险指标响应 Schema"""
    id: str
    portfolio_id: str
    calculation_date: datetime
    var_95: Optional[Decimal]
    var_99: Optional[Decimal]
    cvar_95: Optional[Decimal]
    herfindahl_index: Optional[Decimal]
    max_single_weight: Optional[Decimal]
    top_5_weight: Optional[Decimal]
    top_10_weight: Optional[Decimal]
    diversification_ratio: Optional[Decimal]
    beta_to_benchmark: Optional[Decimal]
    portfolio_volatility: Optional[Decimal]
    max_drawdown: Optional[Decimal]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================
# 组合优化 Schema
# ==============================================

class OptimizeResponse(BaseModel):
    """优化结果响应 Schema"""
    id: str
    portfolio_id: str
    optimization_method: OptimizationMethod
    current_weights: Optional[Dict[str, float]]
    optimal_weights: Optional[Dict[str, float]]
    expected_return: Optional[Decimal]
    expected_risk: Optional[Decimal]
    expected_sharpe: Optional[Decimal]
    rebalance_trades: Optional[List[Dict[str, Any]]]
    estimated_transaction_cost: Optional[Decimal]
    status: str

    model_config = ConfigDict(from_attributes=True)


class OptimizationListResponse(BaseModel):
    """优化历史列表响应 Schema"""
    total: int
    items: List[OptimizeResponse]
