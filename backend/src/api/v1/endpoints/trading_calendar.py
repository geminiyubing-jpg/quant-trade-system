"""
交易日历 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models.user import User
from src.models.trading_ext import TradingCalendar

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

class TradingDayResponse(BaseModel):
    """交易日响应"""
    date: date
    is_trading_day: bool
    market: str
    open_time: Optional[str]
    close_time: Optional[str]
    holiday_name: Optional[str]

    class Config:
        from_attributes = True


class TradingHoursResponse(BaseModel):
    """交易时间响应"""
    date: date
    market: str
    is_trading_day: bool
    open_time: Optional[str]
    close_time: Optional[str]
    lunch_start: Optional[str]
    lunch_end: Optional[str]
    is_half_day: bool


# ==============================================
# 交易日历端点
# ==============================================

@router.get("/is-trading-day/{trade_date}")
async def is_trading_day(
    trade_date: date,
    market: str = Query(default="A-SHARE", description="市场代码"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """判断是否为交易日"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    result = service.is_trading_day(trade_date, market)
    return {
        "date": trade_date,
        "is_trading_day": result,
        "market": market
    }


@router.get("/range", response_model=List[date])
async def get_trading_days_range(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    market: str = Query(default="A-SHARE", description="市场代码"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取日期范围内的交易日列表"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    trading_days = service.get_trading_days(start_date, end_date, market)
    return trading_days


@router.get("/next/{trade_date}", response_model=Optional[date])
async def get_next_trading_day(
    trade_date: date,
    market: str = Query(default="A-SHARE", description="市场代码"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取下一个交易日"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    next_day = service.get_next_trading_day(trade_date, market)
    return next_day


@router.get("/previous/{trade_date}", response_model=Optional[date])
async def get_previous_trading_day(
    trade_date: date,
    market: str = Query(default="A-SHARE", description="市场代码"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取上一个交易日"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    prev_day = service.get_previous_trading_day(trade_date, market)
    return prev_day


@router.get("/hours/{trade_date}", response_model=Optional[TradingHoursResponse])
async def get_trading_hours(
    trade_date: date,
    market: str = Query(default="A-SHARE", description="市场代码"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取交易时间"""
    from src.services.trading.fill_service import FillService
    service = FillService(db)
    hours = service.get_trading_hours(trade_date, market)
    if not hours:
        return None
    return TradingHoursResponse(
        date=trade_date,
        market=hours.get("market", market),
        is_trading_day=hours.get("is_trading_day", False),
        open_time=str(hours["open_time"]) if hours.get("open_time") else None,
        close_time=str(hours["close_time"]) if hours.get("close_time") else None,
        lunch_start=str(hours["lunch_start"]) if hours.get("lunch_start") else None,
        lunch_end=str(hours["lunch_end"]) if hours.get("lunch_end") else None,
        is_half_day=hours.get("is_half_day", False)
    )
