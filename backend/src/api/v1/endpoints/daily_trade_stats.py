"""
交易统计 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models.user import User
from src.models.trading_ext import DailyTradeStats

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

class DailyTradeStatsResponse(BaseModel):
    """交易统计响应"""
    id: str
    user_id: str
    trade_date: date
    execution_mode: str
    total_orders: int
    filled_orders: int
    canceled_orders: int
    rejected_orders: int
    buy_count: int
    sell_count: int
    buy_volume: int
    sell_volume: int
    buy_amount: Optional[Decimal]
    sell_amount: Optional[Decimal]
    total_commission: Optional[Decimal]
    total_stamp_duty: Optional[Decimal]
    total_transfer_fee: Optional[Decimal]
    total_fees: Optional[Decimal]
    realized_pnl: Optional[Decimal]
    daily_pnl: Optional[Decimal]
    position_count: int
    total_market_value: Optional[Decimal]
    total_unrealized_pnl: Optional[Decimal]
    cash_balance: Optional[Decimal]
    total_equity: Optional[Decimal]

    class Config:
        from_attributes = True


class DailyTradeStatsSummary(BaseModel):
    """交易统计汇总"""
    total_orders: int
    filled_orders: int
    canceled_orders: int
    total_buy_amount: Decimal
    total_sell_amount: Decimal
    total_commission: Decimal
    total_fees: Decimal
    total_realized_pnl: Decimal
    total_daily_pnl: Decimal
    days: int


# ==============================================
# 交易统计端点
# ==============================================

@router.get("/daily/{trade_date}", response_model=Optional[DailyTradeStatsResponse])
async def get_daily_stats(
    trade_date: date,
    execution_mode: Optional[str] = Query(None, description="执行模式"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取每日交易统计"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    stats = service.get_or_create_daily_stats(
        user_id=str(current_user.id),
        trade_date=trade_date,
        execution_mode=execution_mode or "PAPER"
    )
    if not stats:
        return None
    return DailyTradeStatsResponse(
        id=str(stats.id),
        user_id=str(stats.user_id),
        trade_date=stats.trade_date,
        execution_mode=stats.execution_mode,
        total_orders=stats.total_orders or 0,
        filled_orders=stats.filled_orders or 0,
        canceled_orders=stats.canceled_orders or 0,
        rejected_orders=stats.rejected_orders or 0,
        buy_count=stats.buy_count or 0,
        sell_count=stats.sell_count or 0,
        buy_volume=stats.buy_volume or 0,
        sell_volume=stats.sell_volume or 0,
        buy_amount=stats.buy_amount,
        sell_amount=stats.sell_amount,
        total_commission=stats.total_commission,
        total_stamp_duty=stats.total_stamp_duty,
        total_transfer_fee=stats.total_transfer_fee,
        total_fees=stats.total_fees,
        realized_pnl=stats.realized_pnl,
        daily_pnl=stats.daily_pnl,
        position_count=stats.position_count or 0,
        total_market_value=stats.total_market_value,
        total_unrealized_pnl=stats.total_unrealized_pnl,
        cash_balance=stats.cash_balance,
        total_equity=stats.total_equity
    )


@router.get("/range", response_model=List[DailyTradeStatsResponse])
async def get_stats_range(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    execution_mode: Optional[str] = Query(None, description="执行模式"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取日期范围内的交易统计"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    stats_list = service.get_stats_range(
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
        execution_mode=execution_mode
    )
    return [
        DailyTradeStatsResponse(
            id=str(s.id),
            user_id=str(s.user_id),
            trade_date=s.trade_date,
            execution_mode=s.execution_mode,
            total_orders=s.total_orders or 0,
            filled_orders=s.filled_orders or 0,
            canceled_orders=s.canceled_orders or 0,
            rejected_orders=s.rejected_orders or 0,
            buy_count=s.buy_count or 0,
            sell_count=s.sell_count or 0,
            buy_volume=s.buy_volume or 0,
            sell_volume=s.sell_volume or 0,
            buy_amount=s.buy_amount,
            sell_amount=s.sell_amount,
            total_commission=s.total_commission,
            total_stamp_duty=s.total_stamp_duty,
            total_transfer_fee=s.total_transfer_fee,
            total_fees=s.total_fees,
            realized_pnl=s.realized_pnl,
            daily_pnl=s.daily_pnl,
            position_count=s.position_count or 0,
            total_market_value=s.total_market_value,
            total_unrealized_pnl=s.total_unrealized_pnl,
            cash_balance=s.cash_balance,
            total_equity=s.total_equity
        )
        for s in stats_list
    ]


@router.get("/summary", response_model=DailyTradeStatsSummary)
async def get_stats_summary(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    execution_mode: Optional[str] = Query(None, description="执行模式"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取交易统计汇总"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    stats_list = service.get_stats_range(
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
        execution_mode=execution_mode
    )

    # 计算汇总
    summary = DailyTradeStatsSummary(
        total_orders=sum(s.total_orders or 0 for s in stats_list),
        filled_orders=sum(s.filled_orders or 0 for s in stats_list),
        canceled_orders=sum(s.canceled_orders or 0 for s in stats_list),
        total_buy_amount=sum(s.buy_amount or Decimal("0") for s in stats_list),
        total_sell_amount=sum(s.sell_amount or Decimal("0") for s in stats_list),
        total_commission=sum(s.total_commission or Decimal("0") for s in stats_list),
        total_fees=sum(s.total_fees or Decimal("0") for s in stats_list),
        total_realized_pnl=sum(s.realized_pnl or Decimal("0") for s in stats_list),
        total_daily_pnl=sum(s.daily_pnl or Decimal("0") for s in stats_list),
        days=len(stats_list)
    )
    return summary


@router.post("/calculate/{trade_date}", response_model=DailyTradeStatsResponse)
async def calculate_daily_stats(
    trade_date: date,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """计算并保存每日交易统计"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    stats = service.calculate_daily_stats(
        user_id=str(current_user.id),
        trade_date=trade_date
    )
    return DailyTradeStatsResponse(
        id=str(stats.id),
        user_id=str(stats.user_id),
        trade_date=stats.trade_date,
        execution_mode=stats.execution_mode,
        total_orders=stats.total_orders or 0,
        filled_orders=stats.filled_orders or 0,
        canceled_orders=stats.canceled_orders or 0,
        rejected_orders=stats.rejected_orders or 0,
        buy_count=stats.buy_count or 0,
        sell_count=stats.sell_count or 0,
        buy_volume=stats.buy_volume or 0,
        sell_volume=stats.sell_volume or 0,
        buy_amount=stats.buy_amount,
        sell_amount=stats.sell_amount,
        total_commission=stats.total_commission,
        total_stamp_duty=stats.total_stamp_duty,
        total_transfer_fee=stats.total_transfer_fee,
        total_fees=stats.total_fees,
        realized_pnl=stats.realized_pnl,
        daily_pnl=stats.daily_pnl,
        position_count=stats.position_count or 0,
        total_market_value=stats.total_market_value,
        total_unrealized_pnl=stats.total_unrealized_pnl,
        cash_balance=stats.cash_balance,
        total_equity=stats.total_equity
    )
