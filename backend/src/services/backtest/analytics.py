"""
回测绩效分析模块

提供全面的回测绩效分析功能：
- 收益率指标（总收益、年化收益、超额收益）
- 风险指标（波动率、最大回撤、VaR、CVaR）
- 风险调整收益（夏普比率、索提诺比率、卡尔玛比率）
- 交易分析（胜率、盈亏比、平均持仓）
- 归因分析（Brison 模型、因子归因）
- 基准比较

参考标准：
- CFA Institute - GIPS 标准
- BarclayHedge 指标计算方法
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


# ==============================================
# 绩效指标数据类
# ==============================================

@dataclass
class PerformanceMetrics:
    """
    绩效指标集合

    包含策略回测的所有关键绩效指标。
    """
    # 收益指标
    total_return: Decimal = Decimal("0")           # 总收益率
    annual_return: Decimal = Decimal("0")          # 年化收益率
    benchmark_return: Optional[Decimal] = None     # 基准收益率
    excess_return: Optional[Decimal] = None        # 超额收益率
    monthly_return_avg: Decimal = Decimal("0")     # 月均收益
    daily_return_avg: Decimal = Decimal("0")       # 日均收益

    # 风险指标
    volatility: Decimal = Decimal("0")             # 年化波动率
    max_drawdown: Decimal = Decimal("0")           # 最大回撤
    max_drawdown_duration: int = 0                 # 最大回撤持续天数
    var_95: Optional[Decimal] = None               # 95% VaR
    cvar_95: Optional[Decimal] = None              # 95% CVaR
    downside_deviation: Optional[Decimal] = None   # 下行偏差

    # 风险调整收益
    sharpe_ratio: Decimal = Decimal("0")           # 夏普比率
    sortino_ratio: Optional[Decimal] = None        # 索提诺比率
    calmar_ratio: Optional[Decimal] = None         # 卡尔玛比率
    information_ratio: Optional[Decimal] = None    # 信息比率
    treynor_ratio: Optional[Decimal] = None        # 特雷诺比率

    # Alpha/Beta
    alpha: Optional[Decimal] = None                # Alpha
    beta: Optional[Decimal] = None                 # Beta

    # 交易指标
    total_trades: int = 0                          # 总交易次数
    winning_trades: int = 0                        # 盈利交易次数
    losing_trades: int = 0                         # 亏损交易次数
    win_rate: Decimal = Decimal("0")               # 胜率
    profit_factor: Optional[Decimal] = None        # 盈亏比
    avg_trade_return: Decimal = Decimal("0")       # 平均交易收益
    avg_winning_return: Optional[Decimal] = None   # 平均盈利收益
    avg_losing_return: Optional[Decimal] = None    # 平均亏损收益
    max_consecutive_wins: int = 0                  # 最大连续盈利次数
    max_consecutive_losses: int = 0                # 最大连续亏损次数

    # 持仓指标
    avg_holding_period: Optional[Decimal] = None   # 平均持仓天数
    turnover_rate: Optional[Decimal] = None        # 换手率
    position_efficiency: Optional[Decimal] = None  # 资金使用效率

    # 时间指标
    trading_days: int = 0                          # 交易天数
    start_date: Optional[date] = None              # 开始日期
    end_date: Optional[date] = None                # 结束日期

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            # 收益指标
            "total_return": f"{float(self.total_return) * 100:.2f}%",
            "annual_return": f"{float(self.annual_return) * 100:.2f}%",
            "benchmark_return": f"{float(self.benchmark_return) * 100:.2f}%" if self.benchmark_return else None,
            "excess_return": f"{float(self.excess_return) * 100:.2f}%" if self.excess_return else None,

            # 风险指标
            "volatility": f"{float(self.volatility) * 100:.2f}%",
            "max_drawdown": f"{float(self.max_drawdown) * 100:.2f}%",
            "var_95": f"{float(self.var_95) * 100:.2f}%" if self.var_95 else None,
            "cvar_95": f"{float(self.cvar_95) * 100:.2f}%" if self.cvar_95 else None,

            # 风险调整收益
            "sharpe_ratio": f"{float(self.sharpe_ratio):.2f}",
            "sortino_ratio": f"{float(self.sortino_ratio):.2f}" if self.sortino_ratio else None,
            "calmar_ratio": f"{float(self.calmar_ratio):.2f}" if self.calmar_ratio else None,

            # Alpha/Beta
            "alpha": f"{float(self.alpha):.4f}" if self.alpha else None,
            "beta": f"{float(self.beta):.4f}" if self.beta else None,

            # 交易指标
            "total_trades": self.total_trades,
            "win_rate": f"{float(self.win_rate) * 100:.2f}%",
            "profit_factor": f"{float(self.profit_factor):.2f}" if self.profit_factor else None,

            # 其他
            "trading_days": self.trading_days,
        }


@dataclass
class TradeAnalysis:
    """
    交易分析结果

    单笔交易的详细分析。
    """
    trade_id: str
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    side: str  # LONG/SHORT
    gross_pnl: Decimal
    commission: Decimal
    slippage: Decimal
    net_pnl: Decimal
    return_pct: Decimal
    holding_days: int
    max_drawdown: Decimal  # 持仓期间最大浮亏
    tags: List[str] = field(default_factory=list)


@dataclass
class AttributionResult:
    """
    归因分析结果

    基于 Brison 模型的收益归因。
    """
    # 总收益分解
    total_return: Decimal
    allocation_effect: Decimal = Decimal("0")      # 配置效应
    selection_effect: Decimal = Decimal("0")       # 选股效应
    interaction_effect: Decimal = Decimal("0")     # 交互效应

    # 行业归因
    industry_attribution: Dict[str, Decimal] = field(default_factory=dict)

    # 因子归因
    factor_attribution: Dict[str, Decimal] = field(default_factory=dict)

    # 时间归因
    periodic_returns: Dict[str, Decimal] = field(default_factory=dict)


# ==============================================
# 绩效分析器
# ==============================================

class PerformanceAnalytics:
    """
    绩效分析器

    提供全面的策略绩效分析功能。

    使用示例：
        analytics = PerformanceAnalytics()

        # 计算绩效指标
        metrics = analytics.calculate_metrics(
            equity_curve=equity_curve,
            trades=trades,
            benchmark_returns=benchmark_returns
        )

        # 生成报告
        report = analytics.generate_report(metrics)
    """

    def __init__(
        self,
        risk_free_rate: Decimal = Decimal("0.03"),  # 无风险利率（年化）
        trading_days_per_year: int = 252             # 每年交易日数
    ):
        """
        初始化绩效分析器

        Args:
            risk_free_rate: 无风险利率（年化）
            trading_days_per_year: 每年交易日数
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year
        self.logger = logging.getLogger("PerformanceAnalytics")

    def calculate_metrics(
        self,
        equity_curve: List[Decimal],
        returns: List[Decimal] = None,
        trades: List[TradeAnalysis] = None,
        benchmark_returns: List[Decimal] = None,
        start_date: date = None,
        end_date: date = None
    ) -> PerformanceMetrics:
        """
        计算绩效指标

        Args:
            equity_curve: 权益曲线（每日净值列表）
            returns: 日收益率列表（可选，如果不提供则从权益曲线计算）
            trades: 交易列表（可选）
            benchmark_returns: 基准收益率列表（可选）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            绩效指标对象
        """
        if not equity_curve:
            return PerformanceMetrics()

        # 计算日收益率
        if returns is None:
            returns = self._calculate_returns(equity_curve)

        if not returns:
            return PerformanceMetrics()

        metrics = PerformanceMetrics()
        metrics.trading_days = len(returns)
        metrics.start_date = start_date
        metrics.end_date = end_date

        # 1. 收益指标
        metrics.total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        metrics.daily_return_avg = sum(returns) / len(returns)

        # 年化收益率
        years = Decimal(len(returns)) / Decimal(self.trading_days_per_year)
        if years > 0:
            metrics.annual_return = (Decimal("1") + metrics.total_return) ** (Decimal("1") / years) - Decimal("1")

        # 月均收益
        months = max(1, len(returns) // 21)  # 假设每月 21 个交易日
        metrics.monthly_return_avg = metrics.total_return / Decimal(months)

        # 2. 风险指标
        metrics.volatility = self._calculate_volatility(returns)
        metrics.max_drawdown = self._calculate_max_drawdown(equity_curve)

        # VaR 和 CVaR
        metrics.var_95 = self._calculate_var(returns, Decimal("0.95"))
        metrics.cvar_95 = self._calculate_cvar(returns, Decimal("0.95"))

        # 下行偏差
        metrics.downside_deviation = self._calculate_downside_deviation(returns)

        # 3. 风险调整收益
        daily_rf = self.risk_free_rate / Decimal(self.trading_days_per_year)
        excess_returns = [r - daily_rf for r in returns]

        if metrics.volatility > 0:
            # 夏普比率（年化）
            metrics.sharpe_ratio = (
                (metrics.annual_return - self.risk_free_rate) / metrics.volatility
            )

        if metrics.downside_deviation and metrics.downside_deviation > 0:
            # 索提诺比率
            metrics.sortino_ratio = (
                (metrics.annual_return - self.risk_free_rate) /
                (metrics.downside_deviation * Decimal(math.sqrt(self.trading_days_per_year)))
            )

        if metrics.max_drawdown > 0:
            # 卡尔玛比率
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown

        # 4. 基准比较
        if benchmark_returns and len(benchmark_returns) == len(returns):
            metrics.benchmark_return = self._calculate_total_return(benchmark_returns)
            metrics.excess_return = metrics.total_return - metrics.benchmark_return

            # 信息比率
            tracking_error = self._calculate_tracking_error(returns, benchmark_returns)
            if tracking_error > 0:
                excess_annual = (metrics.excess_return / years) if years > 0 else Decimal("0")
                metrics.information_ratio = excess_annual / tracking_error

            # Alpha 和 Beta
            metrics.alpha, metrics.beta = self._calculate_alpha_beta(
                returns, benchmark_returns
            )

        # 5. 交易分析
        if trades:
            metrics = self._analyze_trades(metrics, trades)

        return metrics

    def _calculate_returns(self, equity_curve: List[Decimal]) -> List[Decimal]:
        """计算日收益率"""
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i - 1] > 0:
                ret = (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
                returns.append(ret)
        return returns

    def _calculate_total_return(self, returns: List[Decimal]) -> Decimal:
        """计算总收益率"""
        if not returns:
            return Decimal("0")

        cumulative = Decimal("1")
        for r in returns:
            cumulative *= (Decimal("1") + r)
        return cumulative - Decimal("1")

    def _calculate_volatility(self, returns: List[Decimal]) -> Decimal:
        """计算年化波动率"""
        if len(returns) < 2:
            return Decimal("0")

        # 计算标准差
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        daily_std = Decimal(math.sqrt(float(variance)))

        # 年化
        return daily_std * Decimal(math.sqrt(self.trading_days_per_year))

    def _calculate_max_drawdown(self, equity_curve: List[Decimal]) -> Decimal:
        """计算最大回撤"""
        if not equity_curve:
            return Decimal("0")

        peak = equity_curve[0]
        max_dd = Decimal("0")

        for value in equity_curve:
            if value > peak:
                peak = value

            if peak > 0:
                drawdown = (peak - value) / peak
                if drawdown > max_dd:
                    max_dd = drawdown

        return max_dd

    def _calculate_var(
        self,
        returns: List[Decimal],
        confidence: Decimal
    ) -> Decimal:
        """
        计算 VaR（Value at Risk）

        Args:
            returns: 收益率列表
            confidence: 置信水平（如 0.95）

        Returns:
            VaR 值（正数表示潜在损失）
        """
        if not returns:
            return Decimal("0")

        sorted_returns = sorted(returns)
        index = int((Decimal("1") - confidence) * len(sorted_returns))
        index = max(0, min(index, len(sorted_returns) - 1))

        # VaR 是损失，返回正数
        return abs(sorted_returns[index])

    def _calculate_cvar(
        self,
        returns: List[Decimal],
        confidence: Decimal
    ) -> Decimal:
        """
        计算 CVaR（Conditional Value at Risk）

        Args:
            returns: 收益率列表
            confidence: 置信水平

        Returns:
            CVaR 值（正数表示潜在损失）
        """
        if not returns:
            return Decimal("0")

        sorted_returns = sorted(returns)
        index = int((Decimal("1") - confidence) * len(sorted_returns))
        index = max(0, min(index, len(sorted_returns) - 1))

        # CVaR 是尾部损失的平均值
        tail_returns = sorted_returns[:index + 1]
        if tail_returns:
            return abs(sum(tail_returns) / len(tail_returns))
        return Decimal("0")

    def _calculate_downside_deviation(
        self,
        returns: List[Decimal],
        target: Decimal = Decimal("0")
    ) -> Optional[Decimal]:
        """
        计算下行偏差

        Args:
            returns: 收益率列表
            target: 目标收益率（默认为 0）

        Returns:
            下行偏差（日频）
        """
        if not returns:
            return None

        downside_returns = [min(r - target, Decimal("0")) for r in returns]

        if not any(dr != Decimal("0") for dr in downside_returns):
            return Decimal("0")

        variance = sum(dr ** 2 for dr in downside_returns) / len(downside_returns)
        return Decimal(math.sqrt(float(variance)))

    def _calculate_tracking_error(
        self,
        returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Decimal:
        """计算跟踪误差"""
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return Decimal("0")

        diffs = [r - br for r, br in zip(returns, benchmark_returns)]
        mean_diff = sum(diffs) / len(diffs)
        variance = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)

        daily_te = Decimal(math.sqrt(float(variance)))
        return daily_te * Decimal(math.sqrt(self.trading_days_per_year))

    def _calculate_alpha_beta(
        self,
        returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        计算 Alpha 和 Beta

        使用线性回归：
        R_p - R_f = Alpha + Beta * (R_b - R_f) + epsilon

        Args:
            returns: 策略收益率
            benchmark_returns: 基准收益率

        Returns:
            (Alpha, Beta)
        """
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return None, None

        n = len(returns)
        daily_rf = float(self.risk_free_rate / self.trading_days_per_year)

        # 转换为浮点数计算
        r_p = [float(r) - daily_rf for r in returns]
        r_b = [float(br) - daily_rf for br in benchmark_returns]

        # 计算 Beta
        mean_p = sum(r_p) / n
        mean_b = sum(r_b) / n

        covariance = sum((rp - mean_p) * (rb - mean_b) for rp, rb in zip(r_p, r_b)) / n
        variance_b = sum((rb - mean_b) ** 2 for rb in r_b) / n

        if variance_b == 0:
            return None, None

        beta = Decimal(str(covariance / variance_b))

        # 计算 Alpha（年化）
        alpha = Decimal(str(mean_p - float(beta) * mean_b)) * Decimal(self.trading_days_per_year)

        return alpha, beta

    def _analyze_trades(
        self,
        metrics: PerformanceMetrics,
        trades: List[TradeAnalysis]
    ) -> PerformanceMetrics:
        """分析交易记录"""
        if not trades:
            return metrics

        metrics.total_trades = len(trades)

        winning = [t for t in trades if t.net_pnl > 0]
        losing = [t for t in trades if t.net_pnl < 0]

        metrics.winning_trades = len(winning)
        metrics.losing_trades = len(losing)

        if metrics.total_trades > 0:
            metrics.win_rate = Decimal(metrics.winning_trades) / Decimal(metrics.total_trades)

        # 平均交易收益
        trade_returns = [t.return_pct for t in trades]
        metrics.avg_trade_return = sum(trade_returns) / len(trade_returns)

        # 平均盈利/亏损
        if winning:
            metrics.avg_winning_return = sum(t.return_pct for t in winning) / len(winning)
        if losing:
            metrics.avg_losing_return = sum(t.return_pct for t in losing) / len(losing)

        # 盈亏比
        if losing and metrics.avg_losing_return:
            metrics.profit_factor = abs(
                sum(t.net_pnl for t in winning) / sum(t.net_pnl for t in losing)
            ) if sum(t.net_pnl for t in losing) != 0 else None

        # 平均持仓天数
        holding_days = [t.holding_days for t in trades]
        metrics.avg_holding_period = Decimal(sum(holding_days)) / len(holding_days)

        # 连续盈亏
        metrics.max_consecutive_wins = self._calculate_max_consecutive(
            [1 if t.net_pnl > 0 else 0 for t in trades], 1
        )
        metrics.max_consecutive_losses = self._calculate_max_consecutive(
            [1 if t.net_pnl < 0 else 0 for t in trades], 1
        )

        return metrics

    def _calculate_max_consecutive(
        self,
        sequence: List[int],
        target: int
    ) -> int:
        """计算最大连续次数"""
        max_count = 0
        current_count = 0

        for val in sequence:
            if val == target:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count

    def calculate_rolling_metrics(
        self,
        equity_curve: List[Decimal],
        window: int = 252
    ) -> Dict[str, List[Decimal]]:
        """
        计算滚动绩效指标

        Args:
            equity_curve: 权益曲线
            window: 滚动窗口大小

        Returns:
            滚动指标字典
        """
        if len(equity_curve) < window:
            return {}

        returns = self._calculate_returns(equity_curve)

        rolling_sharpe = []
        rolling_volatility = []
        rolling_return = []
        rolling_drawdown = []

        for i in range(window, len(returns)):
            window_returns = returns[i - window:i]
            window_equity = equity_curve[i - window:i + 1]

            # 滚动收益率
            period_return = (window_equity[-1] - window_equity[0]) / window_equity[0]
            rolling_return.append(period_return)

            # 滚动波动率
            vol = self._calculate_volatility(window_returns)
            rolling_volatility.append(vol)

            # 滚动夏普
            if vol > 0:
                annual_return = period_return * Decimal(self.trading_days_per_year / window)
                sharpe = (annual_return - self.risk_free_rate) / vol
                rolling_sharpe.append(sharpe)
            else:
                rolling_sharpe.append(Decimal("0"))

            # 滚动回撤
            rolling_drawdown.append(self._calculate_max_drawdown(window_equity))

        return {
            "rolling_return": rolling_return,
            "rolling_volatility": rolling_volatility,
            "rolling_sharpe": rolling_sharpe,
            "rolling_drawdown": rolling_drawdown,
        }

    def attribution_analysis(
        self,
        portfolio_returns: List[Decimal],
        benchmark_returns: List[Decimal],
        portfolio_weights: Dict[str, Decimal],
        benchmark_weights: Dict[str, Decimal],
        sector_returns: Dict[str, List[Decimal]]
    ) -> AttributionResult:
        """
        Brison 归因分析

        将组合收益分解为：
        - 配置效应（Allocation Effect）
        - 选股效应（Selection Effect）
        - 交互效应（Interaction Effect）

        Args:
            portfolio_returns: 组合收益率
            benchmark_returns: 基准收益率
            portfolio_weights: 组合权重 {sector: weight}
            benchmark_weights: 基准权重 {sector: weight}
            sector_returns: 行业收益率 {sector: returns}

        Returns:
            归因分析结果
        """
        result = AttributionResult(
            total_return=self._calculate_total_return(portfolio_returns)
        )

        # Brison 分解
        total_allocation = Decimal("0")
        total_selection = Decimal("0")
        total_interaction = Decimal("0")

        for sector in portfolio_weights:
            w_p = portfolio_weights.get(sector, Decimal("0"))
            w_b = benchmark_weights.get(sector, Decimal("0"))
            r_b = sector_returns.get(sector, [Decimal("0")])

            if r_b:
                r_b_total = self._calculate_total_return(r_b)
            else:
                r_b_total = Decimal("0")

            # 配置效应 = (Wp - Wb) * Rb
            allocation = (w_p - w_b) * r_b_total
            total_allocation += allocation

            # 选股效应 = Wb * (Rp - Rb)
            # 这里简化处理，实际需要各股票的收益
            selection = Decimal("0")

            # 交互效应 = (Wp - Wb) * (Rp - Rb)
            interaction = Decimal("0")

        result.allocation_effect = total_allocation
        result.selection_effect = total_selection
        result.interaction_effect = total_interaction

        return result

    def generate_report(
        self,
        metrics: PerformanceMetrics,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        生成绩效报告

        Args:
            metrics: 绩效指标
            include_details: 是否包含详细信息

        Returns:
            报告字典
        """
        report = {
            "summary": {
                "performance": "优秀" if float(metrics.sharpe_ratio) > 1.5 else "良好" if float(metrics.sharpe_ratio) > 1.0 else "一般",
                "annual_return": f"{float(metrics.annual_return) * 100:.2f}%",
                "sharpe_ratio": f"{float(metrics.sharpe_ratio):.2f}",
                "max_drawdown": f"{float(metrics.max_drawdown) * 100:.2f}%",
                "win_rate": f"{float(metrics.win_rate) * 100:.2f}%",
            },
            "metrics": metrics.to_dict(),
        }

        if include_details:
            report["analysis"] = {
                "risk_assessment": self._assess_risk(metrics),
                "return_assessment": self._assess_return(metrics),
                "recommendations": self._generate_recommendations(metrics),
            }

        return report

    def _assess_risk(self, metrics: PerformanceMetrics) -> str:
        """评估风险水平"""
        if float(metrics.max_drawdown) > 0.3:
            return "高风险：最大回撤超过 30%"
        elif float(metrics.max_drawdown) > 0.2:
            return "中等风险：最大回撤在 20%-30% 之间"
        elif float(metrics.max_drawdown) > 0.1:
            return "中低风险：最大回撤在 10%-20% 之间"
        else:
            return "低风险：最大回撤小于 10%"

    def _assess_return(self, metrics: PerformanceMetrics) -> str:
        """评估收益水平"""
        if float(metrics.annual_return) > 0.2:
            return "优秀：年化收益超过 20%"
        elif float(metrics.annual_return) > 0.1:
            return "良好：年化收益在 10%-20% 之间"
        elif float(metrics.annual_return) > 0:
            return "一般：年化收益在 0%-10% 之间"
        else:
            return "亏损：年化收益为负"

    def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if float(metrics.sharpe_ratio) < 1.0:
            recommendations.append("建议优化风险调整收益，考虑降低波动率或提高收益率")

        if float(metrics.max_drawdown) > 0.2:
            recommendations.append("建议加强风险控制，考虑添加止损或仓位管理")

        if float(metrics.win_rate) < 0.5:
            recommendations.append("建议优化入场逻辑，提高胜率")

        if metrics.profit_factor and float(metrics.profit_factor) < 1.5:
            recommendations.append("建议优化盈亏比，让盈利奔跑，及时止损")

        if not recommendations:
            recommendations.append("策略表现良好，继续保持")

        return recommendations
