"""
成交记录 API 端点
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
from src.models.trading_ext import Fill

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

class FillCreate(BaseModel):
    """创建成交记录请求"""
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="股票代码")
    side: str = Field(..., description="买卖方向")
    quantity: int = Field(..., gt=0, description="成交数量")
    price: Decimal = Field(..., gt=0, description="成交价格")
    execution_mode: str = Field(default="PAPER", description="执行模式")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    fill_id: Optional[str] = Field(None, description="成交ID（交易所返回）")
    commission: Optional[Decimal] = Field(None, description="佣金")
    stamp_duty: Optional[Decimal] = Field(None, description="印花税")
    transfer_fee: Optional[Decimal] = Field(None, description="过户费")
    fill_time: Optional[datetime] = Field(None, description="成交时间")


class FillUpdate(BaseModel):
    """更新成交记录请求"""
    commission: Optional[Decimal] = Field(None, description="佣金")
    stamp_duty: Optional[Decimal] = Field(None, description="印花税")
    transfer_fee: Optional[Decimal] = Field(None, description="过户费")


class FillResponse(BaseModel):
    """成交记录响应"""
    id: str
    order_id: str
    user_id: str
    strategy_id: Optional[str]
    symbol: str
    side: str
    quantity: int
    price: Decimal
    fill_amount: Optional[Decimal]
    commission: Optional[Decimal]
    stamp_duty: Optional[Decimal]
    transfer_fee: Optional[Decimal]
    total_fees: Optional[Decimal]
    execution_mode: str
    fill_time: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================
# 成交记录端点
# ==============================================

@router.post("/", response_model=FillResponse)
async def create_fill(
    request: FillCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建成交记录"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    fill = service.record_fill(
        order_id=request.order_id,
        user_id=str(current_user.id),
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        price=request.price,
        execution_mode=request.execution_mode,
        strategy_id=request.strategy_id,
        fill_id=request.fill_id,
        commission=request.commission,
        stamp_duty=request.stamp_duty,
        transfer_fee=request.transfer_fee,
        fill_time=request.fill_time
    )
    return FillResponse(
        id=str(fill.id),
        order_id=str(fill.order_id),
        user_id=str(fill.user_id),
        strategy_id=str(fill.strategy_id) if fill.strategy_id else None,
        symbol=fill.symbol,
        side=fill.side,
        quantity=fill.quantity,
        price=fill.price,
        fill_amount=fill.fill_amount,
        commission=fill.commission,
        stamp_duty=fill.stamp_duty,
        transfer_fee=fill.transfer_fee,
        total_fees=fill.total_fees,
        execution_mode=fill.execution_mode,
        fill_time=fill.fill_time,
        created_at=fill.created_at
    )


@router.get("/{fill_id}", response_model=Optional[FillResponse])
async def get_fill(
    fill_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取成交记录"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    fill = service.get_by_id(fill_id)
    if not fill:
        return None
    return FillResponse(
        id=str(fill.id),
        order_id=str(fill.order_id),
        user_id=str(fill.user_id),
        strategy_id=str(fill.strategy_id) if fill.strategy_id else None,
        symbol=fill.symbol,
        side=fill.side,
        quantity=fill.quantity,
        price=fill.price,
        fill_amount=fill.fill_amount,
        commission=fill.commission,
        stamp_duty=fill.stamp_duty,
        transfer_fee=fill.transfer_fee,
        total_fees=fill.total_fees,
        execution_mode=fill.execution_mode,
        fill_time=fill.fill_time,
        created_at=fill.created_at
    )


@router.get("/order/{order_id}", response_model=List[FillResponse])
async def get_fills_by_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取订单的所有成交"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    fills = service.get_by_order(order_id)
    return [
        FillResponse(
            id=str(f.id),
            order_id=str(f.order_id),
            user_id=str(f.user_id),
            strategy_id=str(f.strategy_id) if f.strategy_id else None,
            symbol=f.symbol,
            side=f.side,
            quantity=f.quantity,
            price=f.price,
            fill_amount=f.fill_amount,
            commission=f.commission,
            stamp_duty=f.stamp_duty,
            transfer_fee=f.transfer_fee,
            total_fees=f.total_fees,
            execution_mode=f.execution_mode,
            fill_time=f.fill_time,
            created_at=f.created_at
        )
        for f in fills
    ]


@router.get("/user/{user_id}", response_model=List[FillResponse])
async def get_fills_by_user(
    user_id: str,
    execution_mode: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的成交记录"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    fills = service.get_by_user(
        user_id=user_id,
        execution_mode=execution_mode,
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    return [
        FillResponse(
            id=str(f.id),
            order_id=str(f.order_id),
            user_id=str(f.user_id),
            strategy_id=str(f.strategy_id) if f.strategy_id else None,
            symbol=f.symbol,
            side=f.side,
            quantity=f.quantity,
            price=f.price,
            fill_amount=f.fill_amount,
            commission=f.commission,
            stamp_duty=f.stamp_duty,
            transfer_fee=f.transfer_fee,
            total_fees=f.total_fees,
            execution_mode=f.execution_mode,
            fill_time=f.fill_time,
            created_at=f.created_at
        )
        for f in fills
    ]
