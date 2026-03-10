"""
==============================================
QuantAI Ecosystem - 风控数据模型
==============================================

风控检查和规则的数据模型。
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class RiskCheckType(str, Enum):
    """风控检查类型"""
    POSITION_LIMIT = "position_limit"  # 持仓限制检查
    STOP_LOSS = "stop_loss"  # 止损检查
    TAKE_PROFIT = "take_profit"  # 止盈检查
    DAILY_LOSS_LIMIT = "daily_loss_limit"  # 单日亏损限制
    ORDER_SIZE = "order_size"  # 订单大小限制
    CONCENTRATION = "concentration"  # 持仓集中度检查
    VOLATILITY = "volatility"  # 波动率检查


class RiskSeverity(str, Enum):
    """风险严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RiskCheckResult(BaseModel):
    """风控检查结果"""
    check_type: RiskCheckType = Field(..., description="检查类型")
    passed: bool = Field(..., description="是否通过检查")
    severity: RiskSeverity = Field(default=RiskSeverity.INFO, description="严重程度")
    message: str = Field(..., description="检查结果消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间")

    model_config = ConfigDict(use_enum_values=True)


class RiskRuleConfig(BaseModel):
    """风控规则配置"""
    enabled: bool = Field(default=True, description="是否启用")
    max_position_ratio: Decimal = Field(
        default=Decimal("0.3"),
        ge=Decimal("0"),
        le=Decimal("1"),
        description="最大单仓比例"
    )
    max_daily_loss_ratio: Decimal = Field(
        default=Decimal("0.05"),
        ge=Decimal("0"),
        le=Decimal("1"),
        description="最大单日亏损比例"
    )
    stop_loss_ratio: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
        description="止损比例（例如 0.05 表示 5% 止损）"
    )
    take_profit_ratio: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0"),
        description="止盈比例（例如 0.10 表示 10% 止盈）"
    )
    max_order_size: Optional[int] = Field(
        default=None,
        gt=0,
        description="最大订单数量（股）"
    )
    max_concentration_ratio: Decimal = Field(
        default=Decimal("0.5"),
        ge=Decimal("0"),
        le=Decimal("1"),
        description="最大持仓集中度（单只股票占总资产比例）"
    )

    model_config = ConfigDict(use_enum_values=True)


class RiskMetrics(BaseModel):
    """风险指标"""
    total_market_value: Decimal = Field(default=Decimal("0"), description="总市值")
    total_cost: Decimal = Field(default=Decimal("0"), description="总成本")
    unrealized_pnl: Decimal = Field(default=Decimal("0"), description="未实现盈亏")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="已实现盈亏")
    daily_pnl: Decimal = Field(default=Decimal("0"), description="当日盈亏")
    position_count: int = Field(default=0, description="持仓数量")
    max_single_position_ratio: Decimal = Field(default=Decimal("0"), description="最大单仓比例")

    model_config = ConfigDict(use_enum_values=True)
