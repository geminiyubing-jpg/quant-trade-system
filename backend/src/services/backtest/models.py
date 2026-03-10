"""
==============================================
QuantAI Ecosystem - 回测数据模型
==============================================

回测配置、结果和指标的数据模型。
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ExecutionMode(str, Enum):
    """执行模式"""
    PAPER = "PAPER"  # 模拟交易
    LIVE = "LIVE"  # 实盘交易


class BacktestConfig(BaseModel):
    """回测配置"""
    strategy_id: str = Field(..., description="策略 ID")
    strategy_name: str = Field(..., description="策略名称")
    symbols: List[str] = Field(..., description="股票代码列表")
    start_date: date = Field(..., description="回测开始日期")
    end_date: date = Field(..., description="回测结束日期")
    initial_capital: Decimal = Field(
        default=Decimal("100000"),
        gt=0,
        description="初始资金"
    )
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.PAPER,
        description="执行模式"
    )
    commission_rate: Decimal = Field(
        default=Decimal("0.0003"),
        ge=0,
        description="佣金费率（万三）"
    )
    slippage_rate: Decimal = Field(
        default=Decimal("0.001"),
        ge=0,
        description="滑点率（0.1%）"
    )
    benchmark_symbol: Optional[str] = Field(
        default=None,
        description="基准指数代码（如 000300.SH）"
    )

    model_config = ConfigDict(use_enum_values=True)


class Trade(BaseModel):
    """交易记录"""
    symbol: str = Field(..., description="股票代码")
    trade_id: str = Field(..., description="交易 ID")
    side: str = Field(..., description="买卖方向（BUY/SELL）")
    quantity: int = Field(..., description="数量")
    price: Decimal = Field(..., description="成交价格")
    timestamp: datetime = Field(..., description="成交时间")
    commission: Decimal = Field(default=Decimal("0"), description="佣金")
    slippage: Decimal = Field(default=Decimal("0"), description="滑点")
    pnl: Optional[Decimal] = Field(default=None, description="盈亏")

    model_config = ConfigDict(use_enum_values=True)


class EquityCurve(BaseModel):
    """资金曲线"""
    trade_date: date = Field(..., description="交易日期")
    equity: Decimal = Field(..., description="权益")
    daily_return: Decimal = Field(default=Decimal("0"), description="日收益率")
    drawdown: Decimal = Field(default=Decimal("0"), description="回撤")


class BacktestMetrics(BaseModel):
    """回测指标"""
    # 收益指标
    total_return: Decimal = Field(..., description="总收益率")
    annual_return: Decimal = Field(..., description="年化收益率")
    benchmark_return: Optional[Decimal] = Field(
        default=None,
        description="基准收益率"
    )
    excess_return: Optional[Decimal] = Field(
        default=None,
        description="超额收益率"
    )

    # 风险指标
    volatility: Decimal = Field(..., description="波动率")
    max_drawdown: Decimal = Field(..., description="最大回撤")
    sharpe_ratio: Decimal = Field(..., description="夏普比率")
    calmar_ratio: Optional[Decimal] = Field(
        default=None,
        description="卡尔玛比率"
    )

    # 交易指标
    total_trades: int = Field(..., description="总交易次数")
    win_rate: Decimal = Field(..., description="胜率")
    profit_factor: Optional[Decimal] = Field(
        default=None,
        description="盈亏比"
    )
    avg_trade_return: Decimal = Field(..., description="平均每笔收益率")

    # 时间指标
    trading_days: int = Field(..., description="交易天数")
    avg_holding_period: Optional[Decimal] = Field(
        default=None,
        description="平均持仓天数"
    )

    model_config = ConfigDict(use_enum_values=True)


class BacktestResult(BaseModel):
    """回测结果"""
    backtest_id: str = Field(..., description="回测 ID")
    config: BacktestConfig = Field(..., description="回测配置")
    metrics: BacktestMetrics = Field(..., description="回测指标")
    trades: List[Trade] = Field(default_factory=list, description="交易记录")
    equity_curve: List[EquityCurve] = Field(
        default_factory=list,
        description="资金曲线"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间"
    )
    status: str = Field(default="completed", description="状态")

    model_config = ConfigDict(use_enum_values=True)
