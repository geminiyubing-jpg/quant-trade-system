"""
==============================================
QuantAI Ecosystem - 高级风控规则引擎
==============================================

提供更复杂的风险控制和实时监控功能。
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import logging

from sqlalchemy.orm import Session

from .models import RiskCheckResult, RiskCheckType

logger = logging.getLogger(__name__)


# ==============================================
# 数据模型
# ==============================================

class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    """告警类型"""
    POSITION_LIMIT = "POSITION_LIMIT"
    DAILY_LOSS = "DAILY_LOSS"
    VOLATILITY = "VOLATILITY"
    CORRELATION = "CORRELATION"
    LIQUIDITY = "LIQUIDITY"
    BLACK_SWAN = "BLACK_SWAN"
    DRAWDOWN = "DRAWDOWN"
    CONCENTRATION = "CONCENTRATION"


@dataclass
class AdvancedRiskConfig:
    """高级风控配置"""
    # 波动率调整
    volatility_lookback: int = 20  # 波动率回溯天数
    max_volatility: Decimal = Decimal("0.05")  # 最大日波动率 5%
    volatility_adjustment_factor: Decimal = Decimal("0.5")  # 波动率调整因子

    # 相关性风险
    max_correlation: Decimal = Decimal("0.7")  # 最大相关性
    correlation_lookback: int = 30  # 相关性回溯天数

    # 流动性风险
    min_avg_volume: int = 100000  # 最小日均成交量
    min_turnover_rate: Decimal = Decimal("0.01")  # 最小换手率

    # 黑天鹅保护
    black_swan_threshold: Decimal = Decimal("0.03")  # 3% 单日跌幅阈值
    black_swan_action: str = "HALT"  # HALT, REDUCE, NOTIFY

    # 动态仓位
    kelly_fraction: Decimal = Decimal("0.25")  # 凯利分数
    max_position_at_risk: Decimal = Decimal("0.02")  # 最大风险敞口 2%

    # 回撤控制
    max_drawdown: Decimal = Decimal("0.10")  # 最大回撤 10%
    drawdown_alert_threshold: Decimal = Decimal("0.05")  # 回撤告警阈值 5%

    # VaR 配置
    var_confidence: float = 0.95  # VaR 置信度
    var_limit: Decimal = Decimal("0.05")  # VaR 限制 5%


@dataclass
class VolatilityMetrics:
    """波动率指标"""
    daily_volatility: Decimal
    weekly_volatility: Decimal
    monthly_volatility: Decimal
    annualized_volatility: Decimal
    volatility_trend: str  # RISING, FALLING, STABLE


@dataclass
class CorrelationMetrics:
    """相关性指标"""
    symbol: str
    correlation: Decimal
    beta: Decimal
    r_squared: Decimal


@dataclass
class LiquidityMetrics:
    """流动性指标"""
    avg_daily_volume: int
    turnover_rate: Decimal
    bid_ask_spread: Decimal
    market_impact: Decimal
    liquidity_score: Decimal


@dataclass
class RiskAlert:
    """风险告警"""
    alert_id: str
    alert_type: AlertType
    risk_level: RiskLevel
    symbol: Optional[str]
    message: str
    current_value: Decimal
    threshold: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    action_taken: Optional[str] = None


    details: Dict[str, Any] = field(default_factory=dict)


# ==============================================
# 波动率分析器
# ==============================================

class VolatilityAnalyzer:
    """
    波动率分析器

    计算和分析资产的波动率。
    """

    def __init__(self, config: AdvancedRiskConfig):
        self.config = config

    def calculate_volatility(
        self,
        returns: List[Decimal]
    ) -> VolatilityMetrics:
        """
        计算波动率指标

        Args:
            returns: 收益率列表

        Returns:
            VolatilityMetrics: 波动率指标
        """
        if not returns:
            return VolatilityMetrics(
                daily_volatility=Decimal("0"),
                weekly_volatility=Decimal("0"),
                monthly_volatility=Decimal("0"),
                annualized_volatility=Decimal("0"),
                volatility_trend="STABLE"
            )

        # 转换为 numpy 数组
        returns_array = np.array([float(r) for r in returns])

        # 计算日波动率（标准差）
        daily_vol = np.std(returns_array)

        # 计算周波动率
        weekly_vol = daily_vol * np.sqrt(5)

        # 计算月波动率
        monthly_vol = daily_vol * np.sqrt(22)

        # 年化波动率
        annualized_vol = daily_vol * np.sqrt(252)

        # 判断波动率趋势
        if len(returns) >= 10:
            recent_vol = np.std(returns_array[-5:])
            earlier_vol = np.std(returns_array[-10:-5])

            if recent_vol > earlier_vol * 1.2:
                trend = "RISING"
            elif recent_vol < earlier_vol * 0.8:
                trend = "FALLING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        return VolatilityMetrics(
            daily_volatility=Decimal(str(round(daily_vol, 6))),
            weekly_volatility=Decimal(str(round(weekly_vol, 6))),
            monthly_volatility=Decimal(str(round(monthly_vol, 6))),
            annualized_volatility=Decimal(str(round(annualized_vol, 6))),
            volatility_trend=trend
        )

    def check_volatility_risk(
        self,
        returns: List[Decimal],
        threshold: Optional[Decimal] = None
    ) -> RiskCheckResult:
        """
        检查波动率风险

        Args:
            returns: 收益率列表
            threshold: 波动率阈值

        Returns:
            RiskCheckResult: 检查结果
        """
        threshold = threshold or self.config.max_volatility
        metrics = self.calculate_volatility(returns)

        passed = metrics.daily_volatility <= threshold

        return RiskCheckResult(
            check_type=RiskCheckType.CUSTOM,
            passed=passed,
            severity="HIGH" if not passed else "LOW",
            message=f"Daily volatility: {metrics.daily_volatility:.4f}, threshold: {threshold:.4f}",
            details={
                "daily_volatility": float(metrics.daily_volatility),
                "weekly_volatility": float(metrics.weekly_volatility),
                "trend": metrics.volatility_trend
            }
        )


# ==============================================
# 相关性分析器
# ==============================================

class CorrelationAnalyzer:
    """
    相关性分析器

    分析资产之间的相关性和系统性风险。
    """

    def __init__(self, config: AdvancedRiskConfig):
        self.config = config

    def calculate_correlation(
        self,
        asset_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> CorrelationMetrics:
        """
        计算与基准的相关性

        Args:
            asset_returns: 资产收益率
            benchmark_returns: 基准收益率

        Returns:
            CorrelationMetrics: 相关性指标
        """
        if not asset_returns or not benchmark_returns:
            return CorrelationMetrics(
                symbol="UNKNOWN",
                correlation=Decimal("0"),
                beta=Decimal("1"),
                r_squared=Decimal("0")
            )

        # 转换为 numpy 数组
        asset = np.array([float(r) for r in asset_returns])
        benchmark = np.array([float(r) for r in benchmark_returns])

        # 计算相关系数
        correlation = np.corrcoef(asset, benchmark)[0, 1]

        # 计算 Beta
        benchmark_var = np.var(benchmark)
        if benchmark_var > 0:
            beta = np.cov(asset, benchmark)[0, 1] / benchmark_var
        else:
            beta = 1.0

        # 计算 R-squared
        r_squared = correlation ** 2

        return CorrelationMetrics(
            symbol="BENCHMARK",
            correlation=Decimal(str(round(correlation, 4))),
            beta=Decimal(str(round(beta, 4))),
            r_squared=Decimal(str(round(r_squared, 4)))
        )

    def check_correlation_risk(
        self,
        positions: Dict[str, List[Decimal]],
        threshold: Optional[Decimal] = None
    ) -> List[RiskCheckResult]:
        """
        检查持仓之间的相关性风险

        Args:
            positions: {symbol: returns}
            threshold: 相关性阈值

        Returns:
            List[RiskCheckResult]: 检查结果列表
        """
        threshold = threshold or self.config.max_correlation
        results = []

        symbols = list(positions.keys())
        for i, symbol1 in enumerate(symbols):
            for symbol2 in symbols[i + 1:]:
                returns1 = positions[symbol1]
                returns2 = positions[symbol2]

                if not returns1 or not returns2:
                    continue

                arr1 = np.array([float(r) for r in returns1])
                arr2 = np.array([float(r) for r in returns2])

                if len(arr1) != len(arr2):
                    continue

                correlation = abs(np.corrcoef(arr1, arr2)[0, 1])

                if correlation > float(threshold):
                    results.append(RiskCheckResult(
                        check_type=RiskCheckType.CUSTOM,
                        passed=False,
                        severity="MEDIUM",
                        message=f"High correlation between {symbol1} and {symbol2}: {correlation:.2f}",
                        details={
                            "symbol1": symbol1,
                            "symbol2": symbol2,
                            "correlation": round(correlation, 4)
                        }
                    ))

        return results


# ==============================================
# 流动性分析器
# ==============================================

class LiquidityAnalyzer:
    """
    流动性分析器

    评估资产的流动性风险。
    """

    def __init__(self, config: AdvancedRiskConfig):
        self.config = config

    def calculate_liquidity(
        self,
        volumes: List[int],
        turnover_rates: List[Decimal],
        bid_ask_spreads: List[Decimal]
    ) -> LiquidityMetrics:
        """
        计算流动性指标

        Args:
            volumes: 成交量列表
            turnover_rates: 换手率列表
            bid_ask_spreads: 买卖价差列表

        Returns:
            LiquidityMetrics: 流动性指标
        """
        if not volumes:
            return LiquidityMetrics(
                avg_daily_volume=0,
                turnover_rate=Decimal("0"),
                bid_ask_spread=Decimal("0"),
                market_impact=Decimal("0"),
                liquidity_score=Decimal("0")
            )

        avg_volume = int(np.mean(volumes))
        avg_turnover = Decimal(str(np.mean([float(t) for t in turnover_rates]))) if turnover_rates else Decimal("0")
        avg_spread = Decimal(str(np.mean([float(s) for s in bid_ask_spreads]))) if bid_ask_spreads else Decimal("0")

        # 计算市场冲击（简化实现）
        market_impact = avg_spread * Decimal("2")

        # 计算流动性评分（0-100，越高越好）
        volume_score = min(100, avg_volume / self.config.min_avg_volume * 50)
        turnover_score = min(50, float(avg_turnover) / float(self.config.min_turnover_rate) * 25)
        spread_score = max(0, 25 - float(avg_spread) * 1000)

        liquidity_score = Decimal(str(int(volume_score + turnover_score + spread_score)))

        return LiquidityMetrics(
            avg_daily_volume=avg_volume,
            turnover_rate=avg_turnover,
            bid_ask_spread=avg_spread,
            market_impact=market_impact,
            liquidity_score=liquidity_score
        )

    def check_liquidity_risk(
        self,
        symbol: str,
        volumes: List[int],
        turnover_rates: List[Decimal],
        min_volume: Optional[int] = None,
        min_turnover: Optional[Decimal] = None
    ) -> RiskCheckResult:
        """
        检查流动性风险

        Args:
            symbol: 股票代码
            volumes: 成交量列表
            turnover_rates: 换手率列表
            min_volume: 最小成交量
            min_turnover: 最小换手率

        Returns:
            RiskCheckResult: 检查结果
        """
        min_volume = min_volume or self.config.min_avg_volume
        min_turnover = min_turnover or self.config.min_turnover_rate

        metrics = self.calculate_liquidity(volumes, turnover_rates, [])

        issues = []

        if metrics.avg_daily_volume < min_volume:
            issues.append(f"Low volume: {metrics.avg_daily_volume} < {min_volume}")

        if metrics.turnover_rate < min_turnover:
            issues.append(f"Low turnover: {metrics.turnover_rate:.4f} < {min_turnover:.4f}")

        passed = len(issues) == 0

        return RiskCheckResult(
            check_type=RiskCheckType.CUSTOM,
            passed=passed,
            severity="MEDIUM" if not passed else "LOW",
            message="; ".join(issues) if issues else "Liquidity OK",
            details={
                "symbol": symbol,
                "avg_volume": metrics.avg_daily_volume,
                "turnover_rate": float(metrics.turnover_rate),
                "liquidity_score": float(metrics.liquidity_score)
            }
        )


# ==============================================
# 黑天鹅保护器
# ==============================================

class BlackSwanProtector:
    """
    黑天鹅保护器

    检测极端市场事件并触发保护措施。
    """

    def __init__(self, config: AdvancedRiskConfig):
        self.config = config
        self.alerts: List[RiskAlert] = []

    def detect_black_swan(
        self,
        current_price: Decimal,
        previous_close: Decimal,
        index_change: Optional[Decimal] = None
    ) -> Optional[RiskAlert]:
        """
        检测黑天鹅事件

        Args:
            current_price: 当前价格
            previous_close: 前收盘价
            index_change: 指数变化

        Returns:
            Optional[RiskAlert]: 黑天鹅告警
        """
        if previous_close <= 0:
            return None

        price_change = (current_price - previous_close) / previous_close

        # 检查个股黑天鹅
        if abs(price_change) >= self.config.black_swan_threshold:
                alert = RiskAlert(
                    alert_id=f"BLACK_SWAN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    alert_type=AlertType.BLACK_SWAN,
                    risk_level=RiskLevel.CRITICAL,
                    symbol=None,
                    message=f"Black swan detected: price change {price_change:.2%}",
                    current_value=price_change,
                    threshold=self.config.black_swan_threshold,
                    details={
                        "price_change": float(price_change),
                        "action": self.config.black_swan_action
                    }
                )

                self.alerts.append(alert)
                return alert

        # 检查系统性黑天鹅
        if index_change is not None and abs(index_change) >= self.config.black_swan_threshold:
                alert = RiskAlert(
                    alert_id=f"SYSTEM_BLACK_SWAN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    alert_type=AlertType.BLACK_SWAN,
                    risk_level=RiskLevel.CRITICAL,
                    symbol=None,
                    message=f"System black swan detected: index change {index_change:.2%}",
                    current_value=index_change,
                    threshold=self.config.black_swan_threshold,
                    details={
                        "index_change": float(index_change),
                        "action": self.config.black_swan_action
                    }
                )

                self.alerts.append(alert)
                return alert

        return None

    def get_action(self, alert: RiskAlert) -> str:
        """
        获取黑天鹅应对措施

        Args:
            alert: 风险告警

        Returns:
            str: 应对措施
        """
        action = self.config.black_swan_action

        if action == "HALT":
            return "Immediately halt all trading and close positions"
        elif action == "REDUCE":
            return "Reduce position sizes by 50%"
        else:
            return "Notify risk manager and await instructions"


# ==============================================
# 高级风控引擎
# ==============================================

class AdvancedRiskEngine:
    """
    高级风控引擎

    整合所有高级风控功能，提供统一的风险管理接口。
    """

    def __init__(
        self,
        db: Session,
        config: Optional[AdvancedRiskConfig] = None
    ):
        self.db = db
        self.config = config or AdvancedRiskConfig()

        # 初始化分析器
        self.volatility_analyzer = VolatilityAnalyzer(self.config)
        self.correlation_analyzer = CorrelationAnalyzer(self.config)
        self.liquidity_analyzer = LiquidityAnalyzer(self.config)
        self.black_swan_protector = BlackSwanProtector(self.config)

        # 告警历史
        self.alerts: List[RiskAlert] = []

        # 风险回调
        self.risk_callbacks: List[Callable] = []

    def register_callback(self, callback: Callable):
        """注册风险回调"""
        self.risk_callbacks.append(callback)

    def perform_comprehensive_check(
        self,
        user_id: str,
        positions: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行综合风险检查

        Args:
            user_id: 用户ID
            positions: 持仓信息
            market_data: 市场数据

        Returns:
            Dict: 综合检查结果
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "checks": {},
            "alerts": [],
            "recommendations": []
        }

        # 1. 波动率检查
        for symbol, position in positions.items():
            returns = position.get("returns", [])
            if returns:
                vol_check = self.volatility_analyzer.check_volatility_risk(returns)
                results["checks"][f"{symbol}_volatility"] = {
                    "passed": vol_check.passed,
                    "message": vol_check.message,
                    "details": vol_check.details
                }

        # 2. 相关性检查
        all_returns = {s: p.get("returns", []) for s, p in positions.items() if p.get("returns")}
        if len(all_returns) > 1:
            corr_checks = self.correlation_analyzer.check_correlation_risk(all_returns)
            for check in corr_checks:
                results["checks"][f"correlation_{check.details.get('symbol1')}_{check.details.get('symbol2')}"] = {
                    "passed": check.passed,
                    "message": check.message,
                    "details": check.details
                }

        # 3. 流动性检查
        for symbol, position in positions.items():
                volumes = position.get("volumes", [])
                turnover = position.get("turnover_rates", [])
                if volumes:
                    liq_check = self.liquidity_analyzer.check_liquidity_risk(
                        symbol, volumes, turnover
                    )
                    results["checks"][f"{symbol}_liquidity"] = {
                        "passed": liq_check.passed,
                        "message": liq_check.message,
                        "details": liq_check.details
                    }

        # 4. 黑天鹅检查
        for symbol, position in positions.items():
            current_price = position.get("current_price", Decimal("0"))
            prev_close = position.get("prev_close", Decimal("0"))

            black_swan = self.black_swan_protector.detect_black_swan(
                current_price, prev_close
            )

            if black_swan:
                results["alerts"].append({
                    "alert_id": black_swan.alert_id,
                    "type": black_swan.alert_type.value,
                    "level": black_swan.risk_level.value,
                    "message": black_swan.message,
                    "action": self.black_swan_protector.get_action(black_swan)
                })

        # 5. 生成建议
        results["recommendations"] = self._generate_recommendations(results)

        # 6. 触发回调
        for callback in self.risk_callbacks:
            try:
                callback(results)
            except Exception as e:
                logger.error(f"Risk callback error: {e}")

        return results

    def calculate_position_size(
        self,
        capital: Decimal,
        volatility: Decimal,
        win_rate: Decimal = Decimal("0.5"),
        max_risk: Optional[Decimal] = None
    ) -> Decimal:
        """
        计算动态仓位大小（基于凯利公式）

        Args:
            capital: 可用资金
            volatility: 波动率
            win_rate: 胜率
            max_risk: 最大风险敞口

        Returns:
            Decimal: 建议仓位金额
        """
        max_risk = max_risk or self.config.max_position_at_risk

        # 简化的凯利公式
        # f = p - (1-p)/odds
        # 其中 odds = 1/win_rate - 1
        if win_rate <= 0 or win_rate >= 1:
            kelly_fraction = Decimal("0")
        else:
            odds = (1 / float(win_rate)) - 1
            kelly_fraction = Decimal(str(win_rate)) - (Decimal("1") - Decimal(str(win_rate))) / Decimal(str(odds))

        # 应用凯利分数限制
        kelly_fraction = min(kelly_fraction, self.config.kelly_fraction)

        # 考虑波动率调整
        if volatility > self.config.max_volatility:
            adjustment = self.config.volatility_adjustment_factor
            kelly_fraction *= adjustment

        # 计算最终仓位
        position_size = capital * kelly_fraction

        # 限制最大风险敞口
        max_position = capital * max_risk
        position_size = min(position_size, max_position)

        return position_size

    def monitor_drawdown(
        self,
        equity_curve: List[Decimal]
    ) -> Optional[RiskAlert]:
        """
        监控回撤

        Args:
            equity_curve: 权益曲线

        Returns:
            Optional[RiskAlert]: 回撤告警
        """
        if not equity_curve:
            return None

        peak = max(equity_curve)
        current = equity_curve[-1]

        if peak <= 0:
            return None

        drawdown = (peak - current) / peak

        if drawdown >= self.config.max_drawdown:
            return RiskAlert(
                alert_id=f"DRAWDOWN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                alert_type=AlertType.DRAWDOWN,
                risk_level=RiskLevel.CRITICAL,
                symbol=None,
                message=f"Critical drawdown: {drawdown:.2%} exceeds limit {self.config.max_drawdown:.2%}",
                current_value=drawdown,
                threshold=self.config.max_drawdown,
                details={
                    "peak": float(peak),
                    "current": float(current),
                    "drawdown": float(drawdown)
                }
            )

        elif drawdown >= self.config.drawdown_alert_threshold:
            return RiskAlert(
                alert_id=f"DRAWDOWN_WARNING_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                alert_type=AlertType.DRAWDOWN,
                risk_level=RiskLevel.HIGH,
                symbol=None,
                message=f"Drawdown warning: {drawdown:.2%}",
                current_value=drawdown,
                threshold=self.config.drawdown_alert_threshold,
                details={
                    "peak": float(peak),
                    "current": float(current),
                    "drawdown": float(drawdown)
                }
            )

        return None

    def get_active_alerts(
        self,
        user_id: Optional[str] = None,
        risk_level: Optional[RiskLevel] = None
    ) -> List[RiskAlert]:
        """
        获取活动告警

        Args:
            user_id: 用户ID
            risk_level: 风险等级

        Returns:
            List[RiskAlert]: 活动告警列表
        """
        alerts = [a for a in self.alerts if not a.acknowledged]

        if risk_level:
            alerts = [a for a in alerts if a.risk_level == risk_level]

        return alerts

    def acknowledge_alert(self, alert_id: str, action_taken: str) -> bool:
        """
        确认告警

        Args:
            alert_id: 告警ID
            action_taken: 采取的措施

        Returns:
            bool: 是否成功
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.action_taken = action_taken
                return True
        return False

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成风险建议"""
        recommendations = []

        # 检查波动率
        for check_name, check in results["checks"].items():
            if "volatility" in check_name and not check["passed"]:
                recommendations.append(
                    f"Reduce position size for high volatility assets"
                )

        # 检查相关性
        for check_name, check in results["checks"].items():
            if "correlation" in check_name and not check["passed"]:
                recommendations.append(
                    f"Diversify portfolio to reduce correlation risk"
                )

        # 检查流动性
        for check_name, check in results["checks"].items():
            if "liquidity" in check_name and not check["passed"]:
                recommendations.append(
                    f"Be cautious with low liquidity assets - consider smaller positions"
                )

        # 检查黑天鹅
        if results["alerts"]:
            recommendations.append(
                f"CRITICAL: Review all positions immediately due to market anomaly"
            )

        return recommendations


# ==============================================
# 全局实例
# ==============================================

_advanced_engine_instance: Optional[AdvancedRiskEngine] = None


def get_advanced_risk_engine(
    db: Session,
    config: Optional[AdvancedRiskConfig] = None
) -> AdvancedRiskEngine:
    """获取高级风控引擎实例"""
    global _advanced_engine_instance
    if _advanced_engine_instance is None or _advanced_engine_instance.db != db:
        _advanced_engine_instance = AdvancedRiskEngine(db, config)
    return _advanced_engine_instance
