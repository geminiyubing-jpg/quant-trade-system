"""
交易扩展相关的 Pydantic Schemas

成交记录、交易日历、交易统计
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from .trading import OrderSide, ExecutionMode


# ==============================================
# 成交记录 Schema
# ==============================================

class FillBase(BaseModel):
    """成交记录基础 Schema"""
    order_id: str
    symbol: str = Field(..., min_length=1, max_length=20)
    side: OrderSide
    execution_mode: ExecutionMode


class FillCreate(FillBase):
    """成交记录创建 Schema"""
    strategy_id: Optional[str] = None
    fill_id: Optional[str] = None
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    commission: Decimal = Field(default=Decimal("0"))
    stamp_duty: Decimal = Field(default=Decimal("0"))
    transfer_fee: Decimal = Field(default=Decimal("0"))
    fill_time: datetime


class FillResponse(FillBase):
    """成交记录响应 Schema"""
    id: str
    user_id: str
    quantity: int
    price: Decimal
    fill_amount: Optional[Decimal]
    total_fees: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FillListResponse(BaseModel):
    """成交记录列表响应 Schema"""
    total: int
    items: List[FillResponse]


# ==============================================
# 交易日历 Schema
# ==============================================

class TradingCalendarBase(BaseModel):
    """交易日历基础 Schema"""
    market: str = Field(default="A-SHARE")


class TradingCalendarResponse(TradingCalendarBase):
    """交易日历响应 Schema"""
    id: int
    trade_date: date
    is_trading_day: bool
    is_half_day: bool
    open_time: Optional[str]
    close_time: Optional[str]
    holiday_name: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================
# 交易统计 Schema
# ==============================================

class DailyTradeStatsBase(BaseModel):
    """交易统计基础 Schema"""
    trade_date: date
    execution_mode: ExecutionMode


class DailyTradeStatsCreate(DailyTradeStatsBase):
    """交易统计创建 Schema"""
    total_orders: int = Field(default=0)
    filled_orders: int = Field(default=0)
    canceled_orders: int = Field(default=0)


class DailyTradeStatsResponse(DailyTradeStatsBase):
    """交易统计响应 Schema"""
    id: str
    user_id: str
    total_orders: int
    filled_orders: int
    canceled_orders: int
    rejected_orders: int
    buy_count: int
    sell_count: int
    buy_volume: int
    sell_volume: int
    buy_amount: Decimal
    sell_amount: Decimal
    total_commission: Decimal
    total_stamp_duty: Decimal
    total_transfer_fee: Decimal
    total_fees: Decimal
    realized_pnl: Decimal
    daily_pnl: Decimal
    position_count: int
    total_market_value: Decimal
    total_unrealized_pnl: Decimal
    cash_balance: Optional[Decimal]
    total_equity: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailyTradeStatsListResponse(BaseModel):
    """交易统计列表响应 Schema"""
    total: int
    items: List[DailyTradeStatsResponse]
