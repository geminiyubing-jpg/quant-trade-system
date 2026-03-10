"""
价格预警相关的 Pydantic Schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from enum import Enum


# ==============================================
# 预警类型枚举
# ==============================================

class AlertType(str, Enum):
    """预警类型"""
    PRICE_ABOVE = "PRICE_ABOVE"         # 价格高于
    PRICE_BELOW = "PRICE_BELOW"         # 价格低于
    CHANGE_PCT_ABOVE = "CHANGE_PCT_ABOVE"  # 涨幅高于
    CHANGE_PCT_BELOW = "CHANGE_PCT_BELOW"  # 跌幅低于
    VOLUME_ABOVE = "VOLUME_ABOVE"       # 成交量高于
    VOLUME_BELOW = "VOLUME_BELOW"       # 成交量低于


# ==============================================
# 价格预警 Schema
# ==============================================

class PriceAlertBase(BaseModel):
    """价格预警基础 Schema"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    alert_type: AlertType = Field(..., description="预警类型")
    target_value: Decimal = Field(..., gt=0, description="目标值")


class PriceAlertCreate(PriceAlertBase):
    """价格预警创建 Schema"""
    pass


class PriceAlertUpdate(BaseModel):
    """价格预警更新 Schema"""
    target_value: Optional[Decimal] = Field(None, gt=0, description="目标值")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PriceAlertResponse(PriceAlertBase):
    """价格预警响应 Schema"""
    id: UUID
    user_id: str
    current_price: Optional[Decimal] = None
    is_active: bool = True
    is_triggered: bool = False
    triggered_at: Optional[datetime] = None
    notification_sent: bool = False
    created_at: datetime
    updated_at: datetime
    # 股票信息（可选）
    stock_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PriceAlertListResponse(BaseModel):
    """价格预警列表响应 Schema"""
    total: int = Field(..., description="总记录数")
    items: List[PriceAlertResponse] = Field(..., description="预警列表")


# ==============================================
# 预警历史 Schema
# ==============================================

class AlertHistoryBase(BaseModel):
    """预警历史基础 Schema"""
    symbol: str = Field(..., description="股票代码")
    alert_type: AlertType = Field(..., description="预警类型")
    target_value: Decimal = Field(..., description="目标值")
    actual_value: Decimal = Field(..., description="实际触发值")


class AlertHistoryResponse(AlertHistoryBase):
    """预警历史响应 Schema"""
    id: UUID
    user_id: str
    alert_id: Optional[UUID] = None
    triggered_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    # 股票信息（可选）
    stock_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AlertHistoryListResponse(BaseModel):
    """预警历史列表响应 Schema"""
    total: int = Field(..., description="总记录数")
    items: List[AlertHistoryResponse] = Field(..., description="历史列表")


class AlertHistoryAcknowledge(BaseModel):
    """预警历史确认 Schema"""
    acknowledged: bool = Field(True, description="是否确认")


# ==============================================
# 预警触发通知 Schema
# ==============================================

class AlertTriggeredMessage(BaseModel):
    """预警触发消息 Schema（WebSocket 推送）"""
    alert_id: UUID
    symbol: str
    alert_type: AlertType
    target_value: Decimal
    actual_value: Decimal
    triggered_at: datetime
    stock_name: Optional[str] = None
    message: str = Field(..., description="预警消息")


# ==============================================
# 预警设置 Schema
# ==============================================

class AlertSettings(BaseModel):
    """预警设置 Schema"""
    sound_enabled: bool = Field(True, description="是否启用声音提醒")
    browser_notification: bool = Field(True, description="是否启用浏览器通知")
    email_notification: bool = Field(False, description="是否启用邮件通知")
    quiet_hours_start: Optional[str] = Field(None, description="免打扰开始时间 (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="免打扰结束时间 (HH:MM)")


class AlertSettingsUpdate(BaseModel):
    """预警设置更新 Schema"""
    sound_enabled: Optional[bool] = None
    browser_notification: Optional[bool] = None
    email_notification: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
