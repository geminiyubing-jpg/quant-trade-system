"""
交易执行 API 端点

提供实时交易执行、多策略组合管理等功能。
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models.user import User
from src.services.trading.executor import (
    TradingExecutor,
    ExecutionConfig,
    TradingSignal,
    SignalType,
    get_executor
)
from src.services.portfolio.multi_strategy import (
    MultiStrategyManager,
    MultiStrategyConfig,
    AllocationMethod,
    StrategyStatus,
    get_multi_strategy_manager
)


router = APIRouter(prefix="/execution", tags=["Trading Execution"])


# ========================================
# Pydantic 模型
# ========================================

class SignalTypeEnum(str, Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradingSignalRequest(BaseModel):
    """交易信号请求"""
    symbol: str = Field(..., description="股票代码")
    signal_type: SignalTypeEnum = Field(..., description="信号类型")
    quantity: int = Field(..., ge=1, description="数量")
    price: Optional[float] = Field(default=None, description="价格")
    confidence: float = Field(default=1.0, ge=0, le=1, description="置信度")
    reason: str = Field(default="", description="信号原因")
    strategy_id: Optional[str] = Field(default=None, description="策略ID")


class BatchSignalRequest(BaseModel):
    """批量信号请求"""
    signals: List[TradingSignalRequest] = Field(..., description="信号列表")
    execution_mode: str = Field(default="PAPER", description="执行模式")


class ExecutionConfigRequest(BaseModel):
    """执行配置请求"""
    execution_mode: str = Field(default="PAPER", description="执行模式")
    order_type: str = Field(default="LIMIT", description="订单类型")
    time_in_force: str = Field(default="GTC", description="有效期")
    slippage_tolerance: float = Field(default=0.001, description="滑点容忍度")


class StrategyAllocationRequest(BaseModel):
    """策略分配请求"""
    strategy_id: str = Field(..., description="策略ID")
    strategy_name: str = Field(..., description="策略名称")
    initial_weight: Optional[float] = Field(default=None, description="初始权重")
    custom_capital: Optional[float] = Field(default=None, description="自定义资金")


class MultiStrategyConfigRequest(BaseModel):
    """多策略配置请求"""
    total_capital: float = Field(..., description="总资金")
    allocation_method: str = Field(default="EQUAL", description="分配方法")
    rebalance_threshold: float = Field(default=0.05, description="再平衡阈值")
    max_strategies: int = Field(default=10, description="最大策略数")


class CapitalAllocationRequest(BaseModel):
    """资金分配请求"""
    strategy_id: str = Field(..., description="策略ID")
    amount: float = Field(..., ge=0, description="分配金额")


# ========================================
# 依赖注入
# ========================================

def get_trading_executor(
    db: Session = Depends(get_db)
) -> TradingExecutor:
    """获取交易执行器"""
    return get_executor(db)


def get_strategy_manager(
    db: Session = Depends(get_db)
) -> MultiStrategyManager:
    """获取多策略管理器"""
    return get_multi_strategy_manager(db)


# ========================================
# API 端点
# ========================================

@router.post("/signal", summary="执行交易信号")
async def execute_signal(
    request: TradingSignalRequest,
    current_user: User = Depends(get_current_active_user),
    executor: TradingExecutor = Depends(get_trading_executor)
):
    """
    执行单个交易信号

    - **symbol**: 股票代码（如：000001.SZ）
    - **signal_type**: 信号类型（BUY/SELL/HOLD）
    - **quantity**: 交易数量
    - **price**: 交易价格（限价单必填）
    - **confidence**: 信号置信度（0-1）
    - **reason**: 信号原因
    - **strategy_id**: 关联策略ID
    """
    try:
        signal = TradingSignal(
            symbol=request.symbol,
            signal_type=SignalType(request.signal_type.value),
            quantity=request.quantity,
            price=Decimal(str(request.price)) if request.price else None,
            confidence=request.confidence,
            reason=request.reason,
            strategy_id=request.strategy_id
        )

        result = await executor.execute_signal(
            signal=signal,
            user_id=str(current_user.id)
        )

        return {
            "success": result.success,
            "order_id": result.order_id,
            "fills": result.fills,
            "error": result.error,
            "message": result.message
        }

    except Exception as e:
        logger.error(f"Signal execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal/batch", summary="批量执行交易信号")
async def execute_batch_signals(
    request: BatchSignalRequest,
    current_user: User = Depends(get_current_active_user),
    executor: TradingExecutor = Depends(get_trading_executor)
):
    """
    批量执行交易信号

    - **signals**: 信号列表
    - **execution_mode**: 执行模式（PAPER/LIVE）
    """
    try:
        signals = [
            TradingSignal(
                symbol=s.symbol,
                signal_type=SignalType(s.signal_type.value),
                quantity=s.quantity,
                price=Decimal(str(s.price)) if s.price else None,
                confidence=s.confidence,
                reason=s.reason,
                strategy_id=s.strategy_id
            )
            for s in request.signals
        ]

        results = await executor.execute_signals_batch(
            signals=signals,
            user_id=str(current_user.id),
            execution_mode=request.execution_mode
        )

        return {
            "success": True,
            "total_signals": len(signals),
            "results": [
                {
                    "success": r.success,
                    "order_id": r.order_id,
                    "error": r.error
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Batch signal execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order/{order_id}", summary="获取订单状态")
async def get_order_status(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    executor: TradingExecutor = Depends(get_trading_executor)
):
    """
    获取订单状态

    - **order_id**: 订单ID
    """
    result = await executor.get_order_status(order_id, str(current_user.id))

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.delete("/order/{order_id}", summary="撤销订单")
async def cancel_order(
    order_id: str,
    reason: str = "",
    current_user: User = Depends(get_current_active_user),
    executor: TradingExecutor = Depends(get_trading_executor)
):
    """
    撤销订单

    - **order_id**: 订单ID
    - **reason**: 撤销原因
    """
    result = await executor.cancel_order(
        order_id=order_id,
        user_id=str(current_user.id),
        reason=reason
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/history", summary="获取执行历史")
async def get_execution_history(
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    executor: TradingExecutor = Depends(get_trading_executor)
):
    """
    获取执行历史

    - **limit**: 返回数量限制
    """
    history = executor.get_execution_history(
        user_id=str(current_user.id),
        limit=limit
    )

    return {
        "success": True,
        "total": len(history),
        "history": history
    }


# ========================================
# 多策略组合管理
# ========================================

@router.post("/portfolio/init", summary="初始化多策略组合")
async def init_multi_strategy_portfolio(
    request: MultiStrategyConfigRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    初始化多策略组合

    - **total_capital**: 总资金
    - **allocation_method**: 分配方法（EQUAL/RISK_PARITY/KELLY/CUSTOM）
    - **rebalance_threshold**: 再平衡阈值
    - **max_strategies**: 最大策略数
    """
    try:
        config = MultiStrategyConfig(
            total_capital=Decimal(str(request.total_capital)),
            allocation_method=AllocationMethod(request.allocation_method),
            rebalance_threshold=Decimal(str(request.rebalance_threshold)),
            max_strategies=request.max_strategies
        )

        manager = MultiStrategyManager(db, config)

        return {
            "success": True,
            "config": {
                "total_capital": float(config.total_capital),
                "allocation_method": config.allocation_method.value,
                "rebalance_threshold": float(config.rebalance_threshold),
                "max_strategies": config.max_strategies
            }
        }

    except Exception as e:
        logger.error(f"Portfolio initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/strategy", summary="添加策略到组合")
async def add_strategy_to_portfolio(
    request: StrategyAllocationRequest,
    current_user: User = Depends(get_current_active_user),
    manager: MultiStrategyManager = Depends(get_strategy_manager)
):
    """
    添加策略到组合

    - **strategy_id**: 策略ID
    - **strategy_name**: 策略名称
    - **initial_weight**: 初始权重（0-1）
    - **custom_capital**: 自定义资金（覆盖权重计算）
    """
    try:
        allocation = manager.add_strategy(
            strategy_id=request.strategy_id,
            strategy_name=request.strategy_name,
            initial_weight=Decimal(str(request.initial_weight)) if request.initial_weight else None,
            custom_capital=Decimal(str(request.custom_capital)) if request.custom_capital else None
        )

        return {
            "success": True,
            "allocation": {
                "strategy_id": allocation.strategy_id,
                "strategy_name": allocation.strategy_name,
                "weight": float(allocation.weight),
                "allocated_capital": float(allocation.allocated_capital),
                "available_capital": float(allocation.available_capital),
                "status": allocation.status.value
            }
        }

    except Exception as e:
        logger.error(f"Add strategy error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/portfolio/strategy/{strategy_id}", summary="从组合移除策略")
async def remove_strategy_from_portfolio(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    manager: MultiStrategyManager = Depends(get_strategy_manager)
):
    """
    从组合移除策略

    - **strategy_id**: 策略ID
    """
    success = manager.remove_strategy(strategy_id)

    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return {
        "success": True,
        "message": f"Strategy {strategy_id} removed"
    }


@router.get("/portfolio/allocations", summary="获取所有策略分配")
async def get_all_allocations(
    current_user: User = Depends(get_current_active_user),
    manager: MultiStrategyManager = Depends(get_strategy_manager)
):
    """获取所有策略分配"""
    allocations = manager.get_all_allocations()

    return {
        "success": True,
        "total_strategies": len(allocations),
        "allocations": [
            {
                "strategy_id": a.strategy_id,
                "strategy_name": a.strategy_name,
                "weight": float(a.weight),
                "allocated_capital": float(a.allocated_capital),
                "used_capital": float(a.used_capital),
                "available_capital": float(a.available_capital),
                "pnl": float(a.pnl),
                "status": a.status.value
            }
            for a in allocations
        ]
    }


@router.post("/portfolio/allocate", summary="为策略分配资金")
async def allocate_capital_to_strategy(
    request: CapitalAllocationRequest,
    current_user: User = Depends(get_current_active_user),
    manager: MultiStrategyManager = Depends(get_strategy_manager)
):
    """
    为策略分配资金

    - **strategy_id**: 策略ID
    - **amount**: 分配金额
    """
    allocation = manager.allocate_capital(
        strategy_id=request.strategy_id,
        amount=Decimal(str(request.amount))
    )

    if not allocation:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return {
        "success": True,
        "allocation": {
            "strategy_id": allocation.strategy_id,
            "used_capital": float(allocation.used_capital),
            "available_capital": float(allocation.available_capital)
        }
    }


@router.post("/portfolio/rebalance", summary="执行组合再平衡")
async def rebalance_portfolio(
    force: bool = False,
    current_user: User = Depends(get_current_active_user),
    manager: MultiStrategyManager = Depends(get_strategy_manager)
):
    """
    执行组合再平衡

    - **force**: 是否强制执行（忽略阈值检查）
    """
    result = manager.execute_rebalance(force=force)

    if not result:
        return {
            "success": True,
            "message": "Rebalance not needed",
            "result": None
        }

    return {
        "success": True,
        "result": {
            "rebalance_id": result.rebalance_id,
            "timestamp": result.timestamp.isoformat(),
            "trades": result.trades,
            "estimated_cost": float(result.estimated_cost),
            "status": result.status
        }
    }


@router.get("/portfolio/check-rebalance", summary="检查是否需要再平衡")
async def check_rebalance_needed(
    current_user: User = Depends(get_current_active_user),
    manager: MultiStrategyManager = Depends(get_strategy_manager)
):
    """检查是否需要再平衡"""
    check = manager.check_rebalance_needed()

    return {
        "success": True,
        "check": check
    }


@router.get("/portfolio/risk", summary="获取聚合风险指标")
async def get_aggregated_risk(
    current_user: User = Depends(get_current_active_user),
    manager: MultiStrategyManager = Depends(get_strategy_manager)
):
    """获取聚合风险指标"""
    risk = manager.get_aggregated_risk()

    return {
        "success": True,
        "risk": risk
    }


@router.get("/portfolio/performance", summary="获取绩效汇总")
async def get_performance_summary(
    current_user: User = Depends(get_current_active_user),
    manager: MultiStrategyManager = Depends(get_strategy_manager)
):
    """获取绩效汇总"""
    performance = manager.get_performance_summary()

    return {
        "success": True,
        "performance": performance
    }
