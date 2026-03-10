"""
投资组合管理端点

提供投资组合的 CRUD 操作、风险分析和组合优化功能。
"""

from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models.user import User
from src.models.portfolio import (
    Portfolio, PortfolioPosition, PortfolioRiskMetrics, PortfolioOptimization,
    PortfolioStatus, OptimizationMethod
)

router = APIRouter()


# ==============================================
# 请求/响应模型
# ==============================================

class PortfolioCreate(BaseModel):
    """创建投资组合请求"""
    name: str = Field(..., description="组合名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="组合描述")
    benchmark_symbol: Optional[str] = Field(None, description="基准指数代码")
    target_allocation: Optional[dict] = Field(None, description="目标配置")
    rebalance_threshold: Decimal = Field(Decimal("0.05"), ge=0, le=1, description="再平衡阈值")
    rebalance_frequency: str = Field("MONTHLY", description="再平衡频率")
    execution_mode: str = Field("PAPER", description="执行模式")
    initial_capital: Decimal = Field(..., description="初始资金")
    inception_date: Optional[date] = Field(None, description="成立日期")


class PortfolioUpdate(BaseModel):
    """更新投资组合请求"""
    name: Optional[str] = Field(None, description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    benchmark_symbol: Optional[str] = Field(None, description="基准指数代码")
    target_allocation: Optional[dict] = Field(None, description="目标配置")
    rebalance_threshold: Optional[Decimal] = Field(None, description="再平衡阈值")
    rebalance_frequency: Optional[str] = Field(None, description="再平衡频率")
    status: Optional[PortfolioStatus] = Field(None, description="组合状态")


class PortfolioResponse(BaseModel):
    """投资组合响应"""
    id: str = Field(..., description="组合ID")
    user_id: str = Field(..., description="用户ID")
    name: str = Field(..., description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    benchmark_symbol: Optional[str] = Field(None, description="基准指数代码")
    base_currency: str = Field("CNY", description="基础货币")
    target_allocation: Optional[dict] = Field(None, description="目标配置")
    rebalance_threshold: Optional[Decimal] = Field(None, description="再平衡阈值")
    rebalance_frequency: Optional[str] = Field(None, description="再平衡频率")
    status: str = Field(..., description="组合状态")
    execution_mode: str = Field(..., description="执行模式")
    total_value: Decimal = Field(..., description="总价值")
    cash_balance: Decimal = Field(..., description="现金余额")
    inception_date: Optional[date] = Field(None, description="成立日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class PositionResponse(BaseModel):
    """持仓响应"""
    id: str = Field(..., description="持仓ID")
    portfolio_id: str = Field(..., description="组合ID")
    symbol: str = Field(..., description="股票代码")
    quantity: int = Field(..., description="持仓数量")
    avg_cost: Decimal = Field(..., description="平均成本")
    current_price: Optional[Decimal] = Field(None, description="当前价格")
    market_value: Optional[Decimal] = Field(None, description="市值")
    weight: Optional[Decimal] = Field(None, description="权重")
    target_weight: Optional[Decimal] = Field(None, description="目标权重")
    unrealized_pnl: Optional[Decimal] = Field(None, description="未实现盈亏")
    realized_pnl: Optional[Decimal] = Field(None, description="已实现盈亏")
    sector: Optional[str] = Field(None, description="行业")
    industry: Optional[str] = Field(None, description="子行业")
    status: str = Field(..., description="持仓状态")


class RiskMetricsResponse(BaseModel):
    """风险指标响应"""
    id: str = Field(..., description="ID")
    portfolio_id: str = Field(..., description="组合ID")
    calculation_date: date = Field(..., description="计算日期")
    var_95: Optional[Decimal] = Field(None, description="95% VaR")
    var_99: Optional[Decimal] = Field(None, description="99% VaR")
    cvar_95: Optional[Decimal] = Field(None, description="95% CVaR")
    herfindahl_index: Optional[Decimal] = Field(None, description="赫芬达尔指数")
    max_single_weight: Optional[Decimal] = Field(None, description="最大单只权重")
    diversification_ratio: Optional[Decimal] = Field(None, description="分散化比率")
    beta_to_benchmark: Optional[Decimal] = Field(None, description="基准Beta")
    portfolio_volatility: Optional[Decimal] = Field(None, description="组合波动率")
    max_drawdown: Optional[Decimal] = Field(None, description="最大回撤")


class OptimizationResponse(BaseModel):
    """优化结果响应"""
    id: str = Field(..., description="ID")
    portfolio_id: str = Field(..., description="组合ID")
    optimization_method: str = Field(..., description="优化方法")
    current_weights: Optional[dict] = Field(None, description="当前权重")
    optimal_weights: Optional[dict] = Field(None, description="最优权重")
    expected_return: Optional[Decimal] = Field(None, description="预期收益")
    expected_risk: Optional[Decimal] = Field(None, description="预期风险")
    expected_sharpe: Optional[Decimal] = Field(None, description="预期夏普")
    rebalance_trades: Optional[List[dict]] = Field(None, description="调仓建议")
    estimated_transaction_cost: Optional[Decimal] = Field(None, description="预计交易成本")
    status: str = Field(..., description="状态")


# ==============================================
# 投资组合管理端点
# ==============================================

@router.post("", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(
    portfolio: PortfolioCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建投资组合"""
    from src.services.portfolio.manager import PortfolioManager
    manager = PortfolioManager(db)

    new_portfolio = Portfolio(
        user_id=str(current_user.id),
        name=portfolio.name,
        description=portfolio.description,
        benchmark_symbol=portfolio.benchmark_symbol,
        target_allocation=portfolio.target_allocation,
        rebalance_threshold=portfolio.rebalance_threshold,
        rebalance_frequency=portfolio.rebalance_frequency,
        execution_mode=portfolio.execution_mode,
        cash_balance=portfolio.initial_capital,
        total_value=portfolio.initial_capital,
        inception_date=portfolio.inception_date or date.today(),
        status=PortfolioStatus.ACTIVE,
    )

    created = manager.create(new_portfolio)
    return PortfolioResponse(
        id=str(created.id),
        user_id=str(created.user_id),
        name=created.name,
        description=created.description,
        benchmark_symbol=created.benchmark_symbol,
        base_currency=created.base_currency,
        target_allocation=created.target_allocation,
        rebalance_threshold=created.rebalance_threshold,
        rebalance_frequency=created.rebalance_frequency,
        status=created.status,
        execution_mode=created.execution_mode,
        total_value=created.total_value,
        cash_balance=created.cash_balance,
        inception_date=created.inception_date,
        created_at=created.created_at,
        updated_at=created.updated_at
    )


@router.get("", response_model=List[PortfolioResponse])
async def list_portfolios(
    status: Optional[PortfolioStatus] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取投资组合列表"""
    from src.services.portfolio.manager import PortfolioManager
    manager = PortfolioManager(db)
    portfolios = manager.get_by_user(str(current_user.id), status)
    return [
        PortfolioResponse(
            id=str(p.id),
            user_id=str(p.user_id),
            name=p.name,
            description=p.description,
            benchmark_symbol=p.benchmark_symbol,
            base_currency=p.base_currency,
            target_allocation=p.target_allocation,
            rebalance_threshold=p.rebalance_threshold,
            rebalance_frequency=p.rebalance_frequency,
            status=p.status,
            execution_mode=p.execution_mode,
            total_value=p.total_value,
            cash_balance=p.cash_balance,
            inception_date=p.inception_date,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in portfolios
    ]


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取投资组合详情"""
    from src.services.portfolio.manager import PortfolioManager
    manager = PortfolioManager(db)
    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    return PortfolioResponse(
        id=str(portfolio.id),
        user_id=str(portfolio.user_id),
        name=portfolio.name,
        description=portfolio.description,
        benchmark_symbol=portfolio.benchmark_symbol,
        base_currency=portfolio.base_currency,
        target_allocation=portfolio.target_allocation,
        rebalance_threshold=portfolio.rebalance_threshold,
        rebalance_frequency=portfolio.rebalance_frequency,
        status=portfolio.status,
        execution_mode=portfolio.execution_mode,
        total_value=portfolio.total_value,
        cash_balance=portfolio.cash_balance,
        inception_date=portfolio.inception_date,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at
    )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: str,
    portfolio_update: PortfolioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新投资组合"""
    from src.services.portfolio.manager import PortfolioManager
    manager = PortfolioManager(db)
    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    # 更新字段
    if portfolio_update.name is not None:
        portfolio.name = portfolio_update.name
    if portfolio_update.description is not None:
        portfolio.description = portfolio_update.description
    if portfolio_update.benchmark_symbol is not None:
        portfolio.benchmark_symbol = portfolio_update.benchmark_symbol
    if portfolio_update.target_allocation is not None:
        portfolio.target_allocation = portfolio_update.target_allocation
    if portfolio_update.rebalance_threshold is not None:
        portfolio.rebalance_threshold = portfolio_update.rebalance_threshold
    if portfolio_update.rebalance_frequency is not None:
        portfolio.rebalance_frequency = portfolio_update.rebalance_frequency
    if portfolio_update.status is not None:
        portfolio.status = portfolio_update.status

    updated = manager.update(portfolio)
    return PortfolioResponse(
        id=str(updated.id),
        user_id=str(updated.user_id),
        name=updated.name,
        description=updated.description,
        benchmark_symbol=updated.benchmark_symbol,
        base_currency=updated.base_currency,
        target_allocation=updated.target_allocation,
        rebalance_threshold=updated.rebalance_threshold,
        rebalance_frequency=updated.rebalance_frequency,
        status=updated.status,
        execution_mode=updated.execution_mode,
        total_value=updated.total_value,
        cash_balance=updated.cash_balance,
        inception_date=updated.inception_date,
        created_at=updated.created_at,
        updated_at=updated.updated_at
    )


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除投资组合"""
    from src.services.portfolio.manager import PortfolioManager
    manager = PortfolioManager(db)
    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    manager.delete(portfolio_id)
    return {"success": True, "message": "Portfolio deleted"}


# ==============================================
# 持仓管理端点
# ==============================================

@router.get("/{portfolio_id}/positions", response_model=List[PositionResponse])
async def get_positions(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取组合持仓"""
    from src.services.portfolio.manager import PortfolioManager
    manager = PortfolioManager(db)
    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    positions = manager.get_positions(portfolio_id)
    return [
        PositionResponse(
            id=str(p.id),
            portfolio_id=str(p.portfolio_id),
            symbol=p.symbol,
            quantity=p.quantity,
            avg_cost=p.avg_cost,
            current_price=p.current_price,
            market_value=p.market_value,
            weight=p.weight,
            target_weight=p.target_weight,
            unrealized_pnl=p.unrealized_pnl,
            realized_pnl=p.realized_pnl,
            sector=p.sector,
            industry=p.industry,
            status=p.status
        )
        for p in positions
    ]


# ==============================================
# 风险分析端点
# ==============================================

@router.get("/{portfolio_id}/risk-metrics", response_model=List[RiskMetricsResponse])
async def get_risk_metrics(
    portfolio_id: str,
    calculation_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取组合风险指标"""
    from src.services.portfolio.manager import PortfolioManager
    from src.services.portfolio.risk import PortfolioRiskService
    manager = PortfolioManager(db)
    risk_service = PortfolioRiskService(db)

    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    metrics = risk_service.get_metrics_history(portfolio_id, limit)
    return [
        RiskMetricsResponse(
            id=str(m.id),
            portfolio_id=str(m.portfolio_id),
            calculation_date=m.calculation_date,
            var_95=m.var_95,
            var_99=m.var_99,
            cvar_95=m.cvar_95,
            herfindahl_index=m.herfindahl_index,
            max_single_weight=m.max_single_weight,
            diversification_ratio=m.diversification_ratio,
            beta_to_benchmark=m.beta_to_benchmark,
            portfolio_volatility=m.portfolio_volatility,
            max_drawdown=m.max_drawdown
        )
        for m in metrics
    ]


@router.post("/{portfolio_id}/calculate-var")
async def calculate_var(
    portfolio_id: str,
    confidence: float = Query(0.95, ge=0.9, le=0.99),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """计算 VaR"""
    from src.services.portfolio.manager import PortfolioManager
    from src.services.portfolio.risk import PortfolioRiskService
    manager = PortfolioManager(db)
    risk_service = PortfolioRiskService(db)

    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    var_value = await risk_service.calculate_var(portfolio_id, confidence)
    return {"var": float(var_value), "confidence": confidence}


# ==============================================
# 组合优化端点
# ==============================================

@router.post("/{portfolio_id}/optimize", response_model=OptimizationResponse)
async def optimize_portfolio(
    portfolio_id: str,
    method: OptimizationMethod = Query(...),
    constraints: Optional[dict] = Body(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """执行组合优化"""
    from src.services.portfolio.manager import PortfolioManager
    from src.services.portfolio.optimization import PortfolioOptimizationService
    manager = PortfolioManager(db)
    optimization_service = PortfolioOptimizationService(db)

    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    optimization = await optimization_service.optimize(
        portfolio_id=portfolio_id,
        method=method,
        constraints=constraints
    )

    return OptimizationResponse(
        id=str(optimization.id),
        portfolio_id=str(optimization.portfolio_id),
        optimization_method=optimization.optimization_method,
        current_weights=optimization.current_weights,
        optimal_weights=optimization.optimal_weights,
        expected_return=optimization.expected_return,
        expected_risk=optimization.expected_risk,
        expected_sharpe=optimization.expected_sharpe,
        rebalance_trades=optimization.rebalance_trades,
        estimated_transaction_cost=optimization.estimated_transaction_cost,
        status=optimization.status
    )


@router.get("/{portfolio_id}/optimizations", response_model=List[OptimizationResponse])
async def get_optimization_history(
    portfolio_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取优化历史"""
    from src.services.portfolio.manager import PortfolioManager
    from src.services.portfolio.optimization import PortfolioOptimizationService
    manager = PortfolioManager(db)
    optimization_service = PortfolioOptimizationService(db)

    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    optimizations = optimization_service.get_optimization_history(portfolio_id, limit)
    return [
        OptimizationResponse(
            id=str(o.id),
            portfolio_id=str(o.portfolio_id),
            optimization_method=o.optimization_method,
            current_weights=o.current_weights,
            optimal_weights=o.optimal_weights,
            expected_return=o.expected_return,
            expected_risk=o.expected_risk,
            expected_sharpe=o.expected_sharpe,
            rebalance_trades=o.rebalance_trades,
            estimated_transaction_cost=o.estimated_transaction_cost,
            status=o.status
        )
        for o in optimizations
    ]


# ==============================================
# 绩效分析端点
# ==============================================

class PerformanceMetricsResponse(BaseModel):
    """绩效指标响应"""
    portfolio_id: str = Field(..., description="组合ID")
    calculation_date: date = Field(..., description="计算日期")
    start_date: date = Field(..., description="起始日期")
    end_date: date = Field(..., description="结束日期")

    # 收益指标
    total_return: Decimal = Field(..., description="总收益率")
    annualized_return: Decimal = Field(..., description="年化收益率")
    benchmark_return: Optional[Decimal] = Field(None, description="基准收益率")

    # 风险指标
    annualized_volatility: Decimal = Field(..., description="年化波动率")
    downside_volatility: Optional[Decimal] = Field(None, description="下行波动率")
    max_drawdown: Decimal = Field(..., description="最大回撤")

    # 风险调整收益
    sharpe_ratio: Decimal = Field(..., description="夏普比率")
    sortino_ratio: Optional[Decimal] = Field(None, description="索提诺比率")
    calmar_ratio: Optional[Decimal] = Field(None, description="卡尔马比率")
    information_ratio: Optional[Decimal] = Field(None, description="信息比率")
    treynor_ratio: Optional[Decimal] = Field(None, description="特雷诺比率")

    # Alpha/Beta
    alpha: Optional[Decimal] = Field(None, description="Alpha")
    beta: Optional[Decimal] = Field(None, description="Beta")

    # 其他指标
    win_rate: Optional[Decimal] = Field(None, description="胜率")
    profit_loss_ratio: Optional[Decimal] = Field(None, description="盈亏比")


class BenchmarkCreate(BaseModel):
    """创建自定义基准请求"""
    name: str = Field(..., description="基准名称")
    description: Optional[str] = Field(None, description="基准描述")
    composition: List[dict] = Field(..., description="基准成分（股票代码和权重）")
    rebalance_frequency: str = Field("QUARTERLY", description="再平衡频率")


class BenchmarkResponse(BaseModel):
    """基准响应"""
    id: str = Field(..., description="基准ID")
    portfolio_id: str = Field(..., description="组合ID")
    name: str = Field(..., description="基准名称")
    description: Optional[str] = Field(None, description="基准描述")
    composition: List[dict] = Field(..., description="基准成分")
    rebalance_frequency: str = Field(..., description="再平衡频率")
    created_at: datetime = Field(..., description="创建时间")


class AttributionResponse(BaseModel):
    """归因分析响应"""
    portfolio_id: str = Field(..., description="组合ID")
    period_start: date = Field(..., description="期间开始")
    period_end: date = Field(..., description="期间结束")
    total_return: Decimal = Field(..., description="总收益")
    benchmark_return: Decimal = Field(..., description="基准收益")
    active_return: Decimal = Field(..., description="主动收益")

    # 归因分解
    allocation_effect: Decimal = Field(..., description="配置效应")
    selection_effect: Decimal = Field(..., description="选股效应")
    interaction_effect: Decimal = Field(..., description="交互效应")

    # 详细归因
    sector_attribution: Optional[List[dict]] = Field(None, description="行业归因明细")


@router.get("/{portfolio_id}/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    portfolio_id: str,
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    benchmark_id: Optional[str] = Query(None, description="自定义基准ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取投资组合绩效分析

    计算夏普比率、索提诺比率、Alpha、Beta 等绩效指标
    """
    from src.services.portfolio.manager import PortfolioManager
    from src.services.portfolio.performance import PerformanceService

    manager = PortfolioManager(db)
    performance_service = PerformanceService(db)

    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    # 默认使用过去一年
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year - 1, end_date.month, end_date.day)

    try:
        metrics = await performance_service.calculate_performance(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            benchmark_id=benchmark_id
        )

        return PerformanceMetricsResponse(
            portfolio_id=portfolio_id,
            calculation_date=date.today(),
            start_date=start_date,
            end_date=end_date,
            total_return=metrics.get("total_return", Decimal("0")),
            annualized_return=metrics.get("annualized_return", Decimal("0")),
            benchmark_return=metrics.get("benchmark_return"),
            annualized_volatility=metrics.get("annualized_volatility", Decimal("0")),
            downside_volatility=metrics.get("downside_volatility"),
            max_drawdown=metrics.get("max_drawdown", Decimal("0")),
            sharpe_ratio=metrics.get("sharpe_ratio", Decimal("0")),
            sortino_ratio=metrics.get("sortino_ratio"),
            calmar_ratio=metrics.get("calmar_ratio"),
            information_ratio=metrics.get("information_ratio"),
            treynor_ratio=metrics.get("treynor_ratio"),
            alpha=metrics.get("alpha"),
            beta=metrics.get("beta"),
            win_rate=metrics.get("win_rate"),
            profit_loss_ratio=metrics.get("profit_loss_ratio")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"绩效计算失败: {str(e)}")


@router.post("/{portfolio_id}/benchmarks", response_model=BenchmarkResponse, status_code=201)
async def create_benchmark(
    portfolio_id: str,
    benchmark: BenchmarkCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建自定义基准

    允许用户创建自定义基准组合进行绩效比较
    """
    from src.services.portfolio.manager import PortfolioManager
    from src.services.portfolio.performance import PerformanceService

    manager = PortfolioManager(db)
    performance_service = PerformanceService(db)

    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        new_benchmark = await performance_service.create_benchmark(
            portfolio_id=portfolio_id,
            name=benchmark.name,
            description=benchmark.description,
            composition=benchmark.composition,
            rebalance_frequency=benchmark.rebalance_frequency
        )

        return BenchmarkResponse(
            id=str(new_benchmark.id),
            portfolio_id=portfolio_id,
            name=new_benchmark.name,
            description=new_benchmark.description,
            composition=new_benchmark.composition,
            rebalance_frequency=new_benchmark.rebalance_frequency,
            created_at=new_benchmark.created_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建基准失败: {str(e)}")


@router.get("/{portfolio_id}/benchmarks", response_model=List[BenchmarkResponse])
async def list_benchmarks(
    portfolio_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取组合的自定义基准列表"""
    from src.services.portfolio.manager import PortfolioManager
    from src.services.portfolio.performance import PerformanceService

    manager = PortfolioManager(db)
    performance_service = PerformanceService(db)

    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    benchmarks = performance_service.get_benchmarks(portfolio_id)
    return [
        BenchmarkResponse(
            id=str(b.id),
            portfolio_id=portfolio_id,
            name=b.name,
            description=b.description,
            composition=b.composition,
            rebalance_frequency=b.rebalance_frequency,
            created_at=b.created_at
        )
        for b in benchmarks
    ]


@router.post("/{portfolio_id}/attribution", response_model=AttributionResponse)
async def calculate_attribution(
    portfolio_id: str,
    start_date: date = Body(..., description="起始日期"),
    end_date: date = Body(..., description="结束日期"),
    benchmark_id: Optional[str] = Body(None, description="自定义基准ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    计算收益归因分析

    将组合收益分解为配置效应、选股效应和交互效应
    """
    from src.services.portfolio.manager import PortfolioManager
    from src.services.portfolio.performance import PerformanceService

    manager = PortfolioManager(db)
    performance_service = PerformanceService(db)

    portfolio = manager.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if str(portfolio.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        attribution = await performance_service.calculate_attribution(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            benchmark_id=benchmark_id
        )

        return AttributionResponse(
            portfolio_id=portfolio_id,
            period_start=start_date,
            period_end=end_date,
            total_return=attribution.get("total_return", Decimal("0")),
            benchmark_return=attribution.get("benchmark_return", Decimal("0")),
            active_return=attribution.get("active_return", Decimal("0")),
            allocation_effect=attribution.get("allocation_effect", Decimal("0")),
            selection_effect=attribution.get("selection_effect", Decimal("0")),
            interaction_effect=attribution.get("interaction_effect", Decimal("0")),
            sector_attribution=attribution.get("sector_attribution")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"归因分析失败: {str(e)}")
