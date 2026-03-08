"""
==============================================
QuantAI Ecosystem - 回测管理端点
==============================================

提供策略回测功能和回测结果查询。
"""

from typing import List, Annotated
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from src.core.security import get_current_active_user
from src.models.user import User
from src.models.strategy import BacktestJob, BacktestResult as BacktestResultModel
from src.services.backtest import BacktestEngine
from src.services.backtest.models import (
    BacktestConfig,
    BacktestResult,
    BacktestMetrics,
    Trade,
    EquityCurve,
)
from src.repositories.backtest import BacktestJobRepository, BacktestResultRepository
from src.core.database import get_db


router = APIRouter()

# 初始化 Repository
backtest_job_repo = BacktestJobRepository(BacktestJob)
backtest_result_repo = BacktestResultRepository(BacktestResultModel)


# ==============================================
# 请求/响应模型
# ==============================================

class CreateBacktestRequest(BaseModel):
    """创建回测请求"""
    strategy_id: str = Field(..., description="策略 ID")
    strategy_name: str = Field(..., description="策略名称")
    symbols: List[str] = Field(..., description="股票代码列表", min_length=1)
    start_date: date = Field(..., description="回测开始日期")
    end_date: date = Field(..., description="回测结束日期")
    initial_capital: Decimal = Field(
        default=Decimal("100000"),
        gt=0,
        description="初始资金"
    )
    commission_rate: Decimal = Field(
        default=Decimal("0.0003"),
        ge=0,
        description="佣金费率"
    )
    slippage_rate: Decimal = Field(
        default=Decimal("0.001"),
        ge=0,
        description="滑点率"
    )
    benchmark_symbol: str = Field(
        default=None,
        description="基准指数代码"
    )


class BacktestSummary(BaseModel):
    """回测摘要"""
    backtest_id: str = Field(..., description="回测 ID")
    strategy_name: str = Field(..., description="策略名称")
    created_at: datetime = Field(..., description="创建时间")
    status: str = Field(..., description="状态")
    total_return: Decimal = Field(..., description="总收益率")
    annual_return: Decimal = Field(..., description="年化收益率")
    max_drawdown: Decimal = Field(..., description="最大回撤")
    sharpe_ratio: Decimal = Field(..., description="夏普比率")
    total_trades: int = Field(..., description="总交易次数")


# ==============================================
# 回测执行端点
# ==============================================

@router.post("/run", response_model=BacktestResult, status_code=status.HTTP_201_CREATED)
async def run_backtest(
    request: CreateBacktestRequest,
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """
    运行回测

    执行策略回测并返回回测结果。
    结果会自动保存到数据库。
    """
    config = BacktestConfig(
        strategy_id=request.strategy_id,
        strategy_name=request.strategy_name,
        symbols=request.symbols,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        execution_mode="PAPER",
        commission_rate=request.commission_rate,
        slippage_rate=request.slippage_rate,
        benchmark_symbol=request.benchmark_symbol
    )

    engine = BacktestEngine(config=config)

    try:
        result = engine.run()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回测执行失败: {str(e)}"
        )

    # 保存回测结果到数据库
    try:
        db = next(get_db())

        # 步骤 1: 先创建 backtest_job 记录（解决外键约束）
        job_config = {
            'strategy_id': request.strategy_id,
            'strategy_name': request.strategy_name,
            'symbols': request.symbols,
            'start_date': str(request.start_date),
            'end_date': str(request.end_date),
            'initial_capital': str(request.initial_capital),
            'execution_mode': 'PAPER'
        }

        backtest_job_repo.create_job(
            db,
            job_id=result.backtest_id,
            strategy_id=request.strategy_id,
            name=request.strategy_name,
            config=job_config,
            created_by=str(current_user.id) if current_user else None
        )

        # 步骤 2: 保存回测结果
        # 计算最终资金
        initial_capital = float(request.initial_capital)
        total_return = float(result.metrics.total_return)
        final_capital = initial_capital * (1 + total_return)

        # 获取 equity_curve 的最终值作为验证
        if result.equity_curve:
            final_capital = float(result.equity_curve[-1].equity)

        backtest_result_repo.create_from_result(
            db,
            job_id=result.backtest_id,
            strategy_id=request.strategy_id,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annual_return=float(result.metrics.annual_return),
            sharpe_ratio=float(result.metrics.sharpe_ratio),
            sortino_ratio=0.0,  # BacktestMetrics 没有此字段，设默认值
            max_drawdown=float(result.metrics.max_drawdown),
            win_rate=float(result.metrics.win_rate),
            total_trades=result.metrics.total_trades,
            winning_trades=0,  # BacktestMetrics 没有此字段，设默认值
            losing_trades=0,  # BacktestMetrics 没有此字段，设默认值
            avg_trade=float(result.metrics.avg_trade_return),
            avg_win=0.0,  # BacktestMetrics 没有此字段，设默认值
            avg_loss=0.0,  # BacktestMetrics 没有此字段，设默认值
            profit_factor=float(result.metrics.profit_factor or 0),
            equity_curve=[{'trade_date': str(e.trade_date), 'equity': float(e.equity), 'daily_return': float(e.daily_return), 'drawdown': float(e.drawdown)} for e in result.equity_curve],
            trades=[{'trade_date': str(t.trade_date), 'symbol': t.symbol, 'side': t.side, 'price': float(t.price), 'quantity': t.quantity} for t in result.trades] if result.trades else []
        )
    except Exception as e:
        # 记录错误但不影响响应
        import logging
        logging.error(f"保存回测结果失败: {str(e)}")

    return result


@router.post("/quick", response_model=BacktestSummary, status_code=status.HTTP_201_CREATED)
async def quick_backtest(
    strategy_id: str = Query(..., description="策略 ID"),
    symbols: List[str] = Query(..., description="股票代码列表"),
    days: int = Query(30, ge=1, le=365, description="回测天数"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """
    快速回测

    使用默认参数执行快速回测。
    结果会自动保存到数据库。
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    config = BacktestConfig(
        strategy_id=strategy_id,
        strategy_name=f"Quick Backtest ({days} days)",
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=Decimal("100000"),
        execution_mode="PAPER"
    )

    engine = BacktestEngine(config=config)
    result = engine.run()

    # 保存回测结果到数据库
    try:
        db = next(get_db())

        # 步骤 1: 先创建 backtest_job 记录（解决外键约束）
        job_config = {
            'strategy_id': strategy_id,
            'strategy_name': f"Quick Backtest ({days} days)",
            'symbols': symbols,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'initial_capital': '100000',
            'execution_mode': 'PAPER'
        }

        backtest_job_repo.create_job(
            db,
            job_id=result.backtest_id,
            strategy_id=strategy_id,
            name=f"Quick Backtest ({days} days)",
            config=job_config,
            created_by=str(current_user.id) if current_user else None
        )

        # 步骤 2: 保存回测结果
        # 计算最终资金
        initial_capital = 100000.0
        total_return = float(result.metrics.total_return)
        final_capital = initial_capital * (1 + total_return)

        # 获取 equity_curve 的最终值作为验证
        if result.equity_curve:
            final_capital = float(result.equity_curve[-1].equity)

        backtest_result_repo.create_from_result(
            db,
            job_id=result.backtest_id,
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annual_return=float(result.metrics.annual_return),
            sharpe_ratio=float(result.metrics.sharpe_ratio),
            sortino_ratio=0.0,  # BacktestMetrics 没有此字段，设默认值
            max_drawdown=float(result.metrics.max_drawdown),
            win_rate=float(result.metrics.win_rate),
            total_trades=result.metrics.total_trades,
            winning_trades=0,  # BacktestMetrics 没有此字段，设默认值
            losing_trades=0,  # BacktestMetrics 没有此字段，设默认值
            avg_trade=float(result.metrics.avg_trade_return),
            avg_win=0.0,  # BacktestMetrics 没有此字段，设默认值
            avg_loss=0.0,  # BacktestMetrics 没有此字段，设默认值
            profit_factor=float(result.metrics.profit_factor or 0),
            equity_curve=[{'trade_date': str(e.trade_date), 'equity': float(e.equity), 'daily_return': float(e.daily_return), 'drawdown': float(e.drawdown)} for e in result.equity_curve],
            trades=[{'trade_date': str(t.trade_date), 'symbol': t.symbol, 'side': t.side, 'price': float(t.price), 'quantity': t.quantity} for t in result.trades] if result.trades else []
        )
    except Exception as e:
        # 记录错误但不影响响应
        import logging
        logging.error(f"保存回测结果失败: {str(e)}")

    return BacktestSummary(
        backtest_id=result.backtest_id,
        strategy_name=result.config.strategy_name,
        created_at=result.created_at,
        status=result.status,
        total_return=result.metrics.total_return,
        annual_return=result.metrics.annual_return,
        max_drawdown=result.metrics.max_drawdown,
        sharpe_ratio=result.metrics.sharpe_ratio,
        total_trades=result.metrics.total_trades
    )


# ==============================================
# 回测结果查询端点
# ==============================================

@router.get("/results", response_model=List[BacktestSummary])
async def list_backtest_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """获取回测结果列表"""
    db = next(get_db())
    results = backtest_result_repo.get_multi(db, skip=skip, limit=limit)

    return [
        BacktestSummary(
            backtest_id=r.job_id,
            strategy_name=f"Strategy {r.strategy_id}",
            created_at=r.created_at,
            status="COMPLETED",
            total_return=Decimal(str(r.total_return)),
            annual_return=Decimal(str(r.annual_return)),
            max_drawdown=Decimal(str(r.max_drawdown)),
            sharpe_ratio=Decimal(str(r.sharpe_ratio)),
            total_trades=r.total_trades
        )
        for r in results
    ]


@router.get("/results/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(
    backtest_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """获取回测详情"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="回测结果不存在"
    )


# ==============================================
# 回测分析端点
# ==============================================

@router.get("/results/{backtest_id}/trades", response_model=List[Trade])
async def get_backtest_trades(
    backtest_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """获取回测交易记录"""
    return []


@router.get("/results/{backtest_id}/equity-curve", response_model=List[EquityCurve])
async def get_equity_curve(
    backtest_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """获取资金曲线"""
    return []


@router.get("/results/{backtest_id}/metrics", response_model=BacktestMetrics)
async def get_backtest_metrics(
    backtest_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """获取回测指标"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="回测指标不存在"
    )


# ==============================================
# 回测比较端点
# ==============================================

@router.post("/compare")
async def compare_backtests(
    backtest_ids: List[str],
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """比较多个回测结果"""
    return {
        "message": "回测对比功能待实现",
        "backtest_ids": backtest_ids
    }
