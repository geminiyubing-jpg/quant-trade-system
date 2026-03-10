"""
回测分析相关的 Pydantic Schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class FactorAnalysisBase(BaseModel):
    """因子分析基础 Schema"""
    factor_name: str = Field(..., min_length=1, max_length=100, description="因子名称")


class FactorAnalysisCreate(FactorAnalysisBase):
    """因子分析创建 Schema"""
    signals: List[Dict[str, Any]] = Field(..., description="信号数据 [{date, symbol, signal_value, return}]")
    returns: List[Dict[str, Any]] = Field(..., description="收益数据 [{date, symbol, return}]")


class FactorAnalysisResponse(FactorAnalysisBase):
    """因子分析响应 Schema"""
    id: str
    backtest_result_id: int
    ic_mean: Optional[Decimal]
    ic_std: Optional[Decimal]
    ic_ir: Optional[Decimal]
    ic_t_stat: Optional[Decimal]
    ic_positive_ratio: Optional[Decimal]
    factor_return: Optional[Decimal]
    factor_volatility: Optional[Decimal]
    factor_t_stat: Optional[Decimal]
    avg_turnover: Optional[Decimal]
    turnover_cost: Optional[Decimal]
    group_returns: Optional[List[Dict[str, Any]]]
    long_short_return: Optional[Decimal]
    ic_series: Optional[List[Dict[str, Any]]]
    factor_return_series: Optional[List[Dict[str, Any]]]
    correlation_matrix: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttributionAnalysisBase(BaseModel):
    """归因分析基础 Schema"""
    benchmark_symbol: Optional[str] = Field(None, max_length=20, description="基准指数代码")


class AttributionAnalysisCreate(AttributionAnalysisBase):
    """归因分析创建 Schema"""
    portfolio_weights: List[Dict[str, Any]]
    benchmark_weights: List[Dict[str, Any]]
    returns_data: List[Dict[str, Any]]


class AttributionAnalysisResponse(AttributionAnalysisBase):
    """归因分析响应 Schema"""
    id: str
    backtest_result_id: int
    allocation_effect: Optional[Decimal]
    selection_effect: Optional[Decimal]
    interaction_effect: Optional[Decimal]
    total_active_return: Optional[Decimal]
    industry_attribution: Optional[List[Dict[str, Any]]]
    risk_factor_attribution: Optional[List[Dict[str, Any]]]
    benchmark_return: Optional[Decimal]
    monthly_attribution: Optional[List[Dict[str, Any]]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestMetricsExtendedBase(BaseModel):
    """扩展绩效指标基础 Schema"""
    sortino_ratio: Optional[Decimal]
    calmar_ratio: Optional[Decimal]
    treynor_ratio: Optional[Decimal]
    information_ratio: Optional[Decimal]
    alpha: Optional[Decimal]
    beta: Optional[Decimal]
    tracking_error: Optional[Decimal]
    downside_deviation: Optional[Decimal]
    max_consecutive_losses: Optional[int]
    max_consecutive_loss_amount: Optional[Decimal]
    profit_factor: Optional[Decimal]
    payoff_ratio: Optional[Decimal]
    risk_reward_ratio: Optional[Decimal]
    avg_holding_days: Optional[Decimal]
    max_holding_days: Optional[int]
    min_holding_days: Optional[int]
    avg_drawdown: Optional[Decimal]
    drawdown_duration_avg: Optional[Decimal]
    recovery_factor: Optional[Decimal]
    upside_volatility: Optional[Decimal]
    downside_volatility: Optional[Decimal]
    avg_turnover_rate: Optional[Decimal]
    total_turnover_cost: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)


class BacktestMetricsExtendedResponse(BacktestMetricsExtendedBase):
    """扩展绩效指标响应 Schema"""
    id: str
    backtest_result_id: int
    sortino_ratio: Optional[Decimal]
    calmar_ratio: Optional[Decimal]
    treynor_ratio: Optional[Decimal]
    information_ratio: Optional[Decimal]
    alpha: Optional[Decimal]
    beta: Optional[Decimal]
    tracking_error: Optional[Decimal]
    downside_deviation: Optional[Decimal]
    max_consecutive_losses: Optional[int]
    max_consecutive_loss_amount: Optional[Decimal]
    profit_factor: Optional[Decimal]
    payoff_ratio: Optional[Decimal]
    risk_reward_ratio: Optional[Decimal]
    avg_holding_days: Optional[Decimal]
    max_holding_days: Optional[int]
    min_holding_days: Optional[int]
    avg_drawdown: Optional[Decimal]
    drawdown_duration_avg: Optional[Decimal]
    recovery_factor: Optional[Decimal]
    upside_volatility: Optional[Decimal]
    downside_volatility: Optional[Decimal]
    avg_turnover_rate: Optional[Decimal]
    total_turnover_cost: Optional[Decimal]
    created_at: datetime
