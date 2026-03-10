"""
回测分析 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models.user import User
from src.models.backtest_analysis import FactorAnalysis, AttributionAnalysis, BacktestMetricsExtended

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

class FactorAnalysisCreate(BaseModel):
    """创建因子分析请求"""
    factor_name: str = Field(..., description="因子名称")
    signals: Optional[List[dict]] = Field(None, description="信号数据")
    returns: Optional[List[dict]] = Field(None, description="收益数据")


class FactorAnalysisResponse(BaseModel):
    """因子分析响应"""
    id: str
    backtest_result_id: int
    factor_name: Optional[str]
    ic_mean: Optional[float]
    ic_std: Optional[float]
    ic_ir: Optional[float]
    factor_return: Optional[float]
    avg_turnover: Optional[float]
    long_short_return: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class AttributionAnalysisCreate(BaseModel):
    """创建归因分析请求"""
    portfolio_weights: Optional[dict] = Field(None, description="组合权重")
    benchmark_weights: Optional[dict] = Field(None, description="基准权重")
    returns_data: Optional[List[dict]] = Field(None, description="收益数据")
    benchmark_symbol: Optional[str] = Field(None, description="基准代码")


class AttributionAnalysisResponse(BaseModel):
    """归因分析响应"""
    id: str
    backtest_result_id: int
    allocation_effect: Optional[float]
    selection_effect: Optional[float]
    interaction_effect: Optional[float]
    total_active_return: Optional[float]
    benchmark_symbol: Optional[str]
    benchmark_return: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class BacktestMetricsExtendedResponse(BaseModel):
    """扩展指标响应"""
    id: str
    backtest_result_id: int
    sortino_ratio: Optional[float]
    calmar_ratio: Optional[float]
    treynor_ratio: Optional[float]
    information_ratio: Optional[float]
    alpha: Optional[float]
    beta: Optional[float]
    profit_factor: Optional[float]
    tracking_error: Optional[float]
    downside_deviation: Optional[float]
    avg_holding_days: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================
# 因子分析端点
# ==============================================

@router.post("/results/{result_id}/factor-analysis", response_model=FactorAnalysisResponse)
async def analyze_factors(
    result_id: int,
    request: FactorAnalysisCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """执行因子分析"""
    from src.services.backtest.analysis import BacktestAnalysisService
    service = BacktestAnalysisService(db)
    analysis = service.analyze_factors(
        backtest_result_id=result_id,
        factor_name=request.factor_name,
        signals=request.signals,
        returns=request.returns
    )
    return FactorAnalysisResponse(
        id=str(analysis.id),
        backtest_result_id=analysis.backtest_result_id,
        factor_name=analysis.factor_name,
        ic_mean=float(analysis.ic_mean) if analysis.ic_mean else None,
        ic_std=float(analysis.ic_std) if analysis.ic_std else None,
        ic_ir=float(analysis.ic_ir) if analysis.ic_ir else None,
        factor_return=float(analysis.factor_return) if analysis.factor_return else None,
        avg_turnover=float(analysis.avg_turnover) if analysis.avg_turnover else None,
        long_short_return=float(analysis.long_short_return) if analysis.long_short_return else None,
        created_at=analysis.created_at
    )


@router.get("/results/{result_id}/factor-analysis", response_model=List[FactorAnalysisResponse])
async def get_factor_analysis(
    result_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取因子分析结果"""
    from src.services.backtest.analysis import BacktestAnalysisService
    service = BacktestAnalysisService(db)
    analyses = service.get_factor_analyses(result_id)
    return [
        FactorAnalysisResponse(
            id=str(a.id),
            backtest_result_id=a.backtest_result_id,
            factor_name=a.factor_name,
            ic_mean=float(a.ic_mean) if a.ic_mean else None,
            ic_std=float(a.ic_std) if a.ic_std else None,
            ic_ir=float(a.ic_ir) if a.ic_ir else None,
            factor_return=float(a.factor_return) if a.factor_return else None,
            avg_turnover=float(a.avg_turnover) if a.avg_turnover else None,
            long_short_return=float(a.long_short_return) if a.long_short_return else None,
            created_at=a.created_at
        )
        for a in analyses
    ]


# ==============================================
# 归因分析端点
# ==============================================

@router.post("/results/{result_id}/attribution", response_model=AttributionAnalysisResponse)
async def run_attribution(
    result_id: int,
    request: AttributionAnalysisCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """执行归因分析"""
    from src.services.backtest.analysis import BacktestAnalysisService
    service = BacktestAnalysisService(db)
    analysis = service.run_attribution(
        backtest_result_id=result_id,
        portfolio_weights=request.portfolio_weights,
        benchmark_weights=request.benchmark_weights,
        returns_data=request.returns_data,
        benchmark_symbol=request.benchmark_symbol
    )
    return AttributionAnalysisResponse(
        id=str(analysis.id),
        backtest_result_id=analysis.backtest_result_id,
        allocation_effect=float(analysis.allocation_effect) if analysis.allocation_effect else None,
        selection_effect=float(analysis.selection_effect) if analysis.selection_effect else None,
        interaction_effect=float(analysis.interaction_effect) if analysis.interaction_effect else None,
        total_active_return=float(analysis.total_active_return) if analysis.total_active_return else None,
        benchmark_symbol=analysis.benchmark_symbol,
        benchmark_return=float(analysis.benchmark_return) if analysis.benchmark_return else None,
        created_at=analysis.created_at
    )


@router.get("/results/{result_id}/attribution", response_model=Optional[AttributionAnalysisResponse])
async def get_attribution(
    result_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取归因分析结果"""
    from src.services.backtest.analysis import BacktestAnalysisService
    service = BacktestAnalysisService(db)
    analysis = service.get_attribution(result_id)
    if not analysis:
        return None
    return AttributionAnalysisResponse(
        id=str(analysis.id),
        backtest_result_id=analysis.backtest_result_id,
        allocation_effect=float(analysis.allocation_effect) if analysis.allocation_effect else None,
        selection_effect=float(analysis.selection_effect) if analysis.selection_effect else None,
        interaction_effect=float(analysis.interaction_effect) if analysis.interaction_effect else None,
        total_active_return=float(analysis.total_active_return) if analysis.total_active_return else None,
        benchmark_symbol=analysis.benchmark_symbol,
        benchmark_return=float(analysis.benchmark_return) if analysis.benchmark_return else None,
        created_at=analysis.created_at
    )


# ==============================================
# 扩展指标端点
# ==============================================

@router.get("/results/{result_id}/metrics-extended", response_model=Optional[BacktestMetricsExtendedResponse])
async def get_extended_metrics(
    result_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取扩展绩效指标"""
    from src.services.backtest.analysis import BacktestAnalysisService
    service = BacktestAnalysisService(db)
    metrics = service.get_extended_metrics(result_id)
    if not metrics:
        return None
    return BacktestMetricsExtendedResponse(
        id=str(metrics.id),
        backtest_result_id=metrics.backtest_result_id,
        sortino_ratio=float(metrics.sortino_ratio) if metrics.sortino_ratio else None,
        calmar_ratio=float(metrics.calmar_ratio) if metrics.calmar_ratio else None,
        treynor_ratio=float(metrics.treynor_ratio) if metrics.treynor_ratio else None,
        information_ratio=float(metrics.information_ratio) if metrics.information_ratio else None,
        alpha=float(metrics.alpha) if metrics.alpha else None,
        beta=float(metrics.beta) if metrics.beta else None,
        profit_factor=float(metrics.profit_factor) if metrics.profit_factor else None,
        tracking_error=float(metrics.tracking_error) if metrics.tracking_error else None,
        downside_deviation=float(metrics.downside_deviation) if metrics.downside_deviation else None,
        avg_holding_days=float(metrics.avg_holding_days) if metrics.avg_holding_days else None,
        created_at=metrics.created_at
    )
