"""
交易相关的 Pydantic Schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ==============================================
# 枚举类型
# ==============================================

class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


class OrderSide(str, Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"


class ExecutionMode(str, Enum):
    """执行模式（架构红线：强制隔离模拟/实盘）"""
    PAPER = "PAPER"
    LIVE = "LIVE"


class TimeInForce(str, Enum):
    """订单有效期"""
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


# ==============================================
# 订单 Schema
# ==============================================

class OrderBase(BaseModel):
    """订单基础 Schema"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    side: OrderSide = Field(..., description="订单方向")
    order_type: str = Field(default="LIMIT", description="订单类型（MARKET=市价, LIMIT=限价）")
    quantity: int = Field(..., gt=0, description="数量")
    price: Decimal = Field(..., gt=0, description="价格")
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.PAPER,
        description="执行模式（PAPER=模拟, LIVE=实盘）"
    )


class OrderCreate(OrderBase):
    """订单创建 Schema"""
    user_id: Optional[str] = Field(None, description="用户 ID（自动设置）")
    strategy_id: Optional[str] = Field(None, description="策略 ID")

    # 风控字段
    stop_loss_price: Optional[Decimal] = Field(
        None,
        gt=0,
        description="止损价格"
    )
    take_profit_price: Optional[Decimal] = Field(
        None,
        gt=0,
        description="止盈价格"
    )
    max_slippage: Decimal = Field(
        default=Decimal("0.001"),
        ge=0,
        le=0.1,
        description="最大滑点容忍度（默认 0.1%）"
    )
    time_in_force: TimeInForce = Field(
        default=TimeInForce.DAY,
        description="订单有效期"
    )


class OrderUpdate(BaseModel):
    """订单更新 Schema"""
    status: Optional[OrderStatus] = None
    filled_quantity: Optional[int] = Field(None, ge=0)
    filled_amount: Optional[Decimal] = Field(None, ge=0)
    commission: Optional[Decimal] = Field(None, ge=0)


class OrderResponse(BaseModel):
    """订单响应 Schema"""
    id: str
    symbol: str
    side: OrderSide
    order_type: str
    quantity: int
    price: Decimal
    execution_mode: ExecutionMode
    status: str
    filled_quantity: int
    avg_price: Decimal
    strategy_id: Optional[str] = None
    user_id: str
    create_time: datetime
    update_time: Optional[datetime] = None
    filled_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """订单列表响应 Schema"""
    total: int
    items: list[OrderResponse]


# ==============================================
# 持仓 Schema
# ==============================================

class PositionBase(BaseModel):
    """持仓基础 Schema"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.PAPER,
        description="执行模式"
    )


class PositionResponse(PositionBase):
    """持仓响应 Schema"""
    id: str
    user_id: str
    strategy_id: Optional[str]
    quantity: int
    avg_price: Decimal
    current_price: Optional[Decimal]
    market_value: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]

    # 额外字段
    cost_basis: Optional[Decimal]
    realized_pnl: Decimal
    max_quantity_limit: Optional[int]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PositionListResponse(BaseModel):
    """持仓列表响应 Schema"""
    total: int
    items: list[PositionResponse]


# ==============================================
# 持仓汇总 Schema
# ==============================================

class PositionSummary(BaseModel):
    """持仓汇总 Schema"""
    total_market_value: Decimal = Field(..., description="总市值")
    total_unrealized_pnl: Decimal = Field(..., description="总浮动盈亏")
    total_realized_pnl: Decimal = Field(..., description="总已实现盈亏")
    position_count: int = Field(..., description="持仓数量")


# ==============================================
# 交易模式切换 Schema
# ==============================================

class LiveTradingPasswordRequest(BaseModel):
    """实盘交易密码设置请求 Schema"""
    password: str = Field(
        ...,
        min_length=8,
        max_length=50,
        description="实盘交易密码（8-50个字符）"
    )
    confirm_password: str = Field(
        ...,
        description="确认密码"
    )


class LiveTradingPasswordResponse(BaseModel):
    """实盘交易密码设置响应 Schema"""
    success: bool = Field(..., description="设置是否成功")
    message: str = Field(..., description="响应消息")
    has_password: bool = Field(..., description="是否已设置密码")


class TradingModeSwitchRequest(BaseModel):
    """交易模式切换请求 Schema"""
    mode: ExecutionMode = Field(
        ...,
        description="目标交易模式（PAPER=模拟, LIVE=实盘）"
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=50,
        description="实盘模式切换需要密码验证"
    )
    confirm: bool = Field(
        ...,
        description="确认标志，防止误操作"
    )


class TradingModeSwitchResponse(BaseModel):
    """交易模式切换响应 Schema"""
    success: bool = Field(..., description="切换是否成功")
    mode: ExecutionMode = Field(..., description="当前交易模式")
    message: str = Field(..., description="响应消息")
    previous_mode: ExecutionMode = Field(..., description="切换前的模式")


class TradingModeStatus(BaseModel):
    """交易模式状态 Schema"""
    current_mode: ExecutionMode = Field(..., description="当前交易模式")
    can_switch_to_live: bool = Field(..., description="是否允许切换到实盘")
    requirements: list[str] = Field(
        default_factory=list,
        description="切换到实盘的前置要求"
    )
    warning_message: Optional[str] = Field(None, description="警告消息")
