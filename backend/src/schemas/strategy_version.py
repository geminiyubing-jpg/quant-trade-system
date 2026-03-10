"""
策略版本控制相关 Pydantic Schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ChangeType(str, Enum):
    """变更类型"""
    MAJOR = "MAJOR"    # 主版本
    MINOR = "MINOR"    # 次版本
    PATCH = "PATCH"    # 补丁版本


class ActionType(str, Enum):
    """审计动作类型"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    PARAM_CHANGE = "PARAM_CHANGE"
    VERSION_PUBLISH = "VERSION_PUBLISH"
    VERSION_ROLLBACK = "VERSION_ROLLBACK"


# ==============================================
# 策略版本 Schema
# ==============================================

class StrategyVersionBase(BaseModel):
    """策略版本基础 Schema"""
    version_number: str = Field(..., pattern=r'^\d+\.\d+\.\d+$', description="语义化版本号")
    change_log: str = Field(..., min_length=1, description="变更日志")
    change_type: ChangeType = Field(default=ChangeType.PATCH, description="变更类型")


class StrategyVersionCreate(StrategyVersionBase):
    """策略版本创建 Schema"""
    code: str = Field(..., min_length=1, description="策略代码")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="策略参数")


class StrategyVersionResponse(StrategyVersionBase):
    """策略版本响应 Schema"""
    id: str
    strategy_id: str
    version_code_hash: Optional[str] = None
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategyVersionListResponse(BaseModel):
    """策略版本列表响应 Schema"""
    total: int
    items: List[StrategyVersionResponse]


# ==============================================
# 策略配置 Schema
# ==============================================

class StrategyConfigBase(BaseModel):
    """策略配置基础 Schema"""
    symbols: List[str] = Field(default_factory=list, description="股票代码列表")
    market: Optional[str] = Field(None, max_length=20, description="市场")
    allocation_ratio: Decimal = Field(default=Decimal("1.0"), ge=0, le=1, description="资金分配比例")
    max_position_count: int = Field(default=10, ge=1, description="最大持仓数")
    max_single_position_ratio: Decimal = Field(default=Decimal("0.2"), gt=0, le=1, description="单仓上限")
    stop_loss_ratio: Optional[Decimal] = Field(None, gt=0, lt=1, description="止损比例")
    take_profit_ratio: Optional[Decimal] = Field(None, gt=0, description="止盈比例")
    max_drawdown_limit: Decimal = Field(default=Decimal("0.2"), gt=0, lt=1, description="最大回撤限制")
    daily_loss_limit: Decimal = Field(default=Decimal("0.05"), gt=0, lt=1, description="单日亏损限制")
    execution_mode: str = Field(default="PAPER", description="执行模式")
    auto_rebalance: bool = Field(default=False, description="自动再平衡")
    rebalance_frequency: Optional[str] = Field(None, description="再平衡频率")


class StrategyConfigCreate(StrategyConfigBase):
    """策略配置创建 Schema"""
    pass


class StrategyConfigUpdate(BaseModel):
    """策略配置更新 Schema"""
    symbols: Optional[List[str]] = None
    market: Optional[str] = None
    allocation_ratio: Optional[Decimal] = None
    max_position_count: Optional[int] = None
    max_single_position_ratio: Optional[Decimal] = None
    stop_loss_ratio: Optional[Decimal] = None
    take_profit_ratio: Optional[Decimal] = None
    max_drawdown_limit: Optional[Decimal] = None
    daily_loss_limit: Optional[Decimal] = None
    auto_rebalance: Optional[bool] = None
    rebalance_frequency: Optional[str] = None


class StrategyConfigResponse(StrategyConfigBase):
    """策略配置响应 Schema"""
    id: str
    strategy_id: str
    user_id: str
    is_active: bool
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================
# 策略审计日志 Schema
# ==============================================

class StrategyAuditLogBase(BaseModel):
    """策略审计日志基础 Schema"""
    action_type: ActionType = Field(..., description="操作类型")
    action_description: Optional[str] = Field(None, description="操作描述")


class StrategyAuditLogCreate(StrategyAuditLogBase):
    """策略审计日志创建 Schema"""
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class StrategyAuditLogResponse(StrategyAuditLogBase):
    """策略审计日志响应 Schema"""
    id: str
    strategy_id: str
    user_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategyAuditLogListResponse(BaseModel):
    """策略审计日志列表响应 Schema"""
    total: int
    items: List[StrategyAuditLogResponse]


# ==============================================
# 版本比较 Schema
# ==============================================

class VersionCompareResponse(BaseModel):
    """版本比较响应 Schema"""
    version1: Dict[str, Any]
    version2: Dict[str, Any]
    code_changed: bool
    params_changed: bool
