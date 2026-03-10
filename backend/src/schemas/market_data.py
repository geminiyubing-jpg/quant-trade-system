"""
==============================================
WebSocket 实时行情 - 数据模型
==============================================
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MarketQuote(BaseModel):
    """实时行情数据"""

    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    price: float = Field(..., description="最新价", ge=0)
    change: float = Field(..., description="涨跌额")
    change_pct: float = Field(..., description="涨跌幅(%)")
    volume: int = Field(..., description="成交量(手)", ge=0)
    amount: float = Field(..., description="成交额(元)", ge=0)
    bid_price: Optional[float] = Field(None, description="买一价", ge=0)
    ask_price: Optional[float] = Field(None, description="卖一价", ge=0)
    high: Optional[float] = Field(None, description="最高价", ge=0)
    low: Optional[float] = Field(None, description="最低价", ge=0)
    open: Optional[float] = Field(None, description="今开价", ge=0)
    prev_close: Optional[float] = Field(None, description="昨收价", ge=0)
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class WebSocketMessage(BaseModel):
    """WebSocket 消息基类"""

    type: str = Field(..., description="消息类型")


class SubscriptionRequest(WebSocketMessage):
    """订阅请求"""

    type: str = Field(default="subscribe", description="消息类型")
    symbols: list[str] = Field(..., description="股票代码列表", min_length=1, max_length=100)


class UnsubscribeRequest(WebSocketMessage):
    """取消订阅请求"""

    type: str = Field(default="unsubscribe", description="消息类型")
    symbols: list[str] = Field(..., description="股票代码列表", min_length=1, max_length=100)


class PingMessage(WebSocketMessage):
    """心跳消息"""

    type: str = Field(default="ping", description="消息类型")


class PongMessage(WebSocketMessage):
    """心跳响应"""

    type: str = Field(default="pong", description="消息类型")


class QuotePushMessage(WebSocketMessage):
    """行情推送消息"""

    type: str = Field(default="quote", description="消息类型")
    data: MarketQuote = Field(..., description="行情数据")


class ErrorMessage(WebSocketMessage):
    """错误消息"""

    type: str = Field(default="error", description="消息类型")
    message: str = Field(..., description="错误信息")
    code: int = Field(..., description="错误码", ge=400, le=599)
