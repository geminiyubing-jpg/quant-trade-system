"""
==============================================
QuantAI Ecosystem - 高级风控系统
==============================================

提供完整的风控体系：
- 事前风控（预交易检查）
- 事中风控（实时监控）
- 事后风控（复盘分析）
- 熔断机制
- 风险报告
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAction(str, Enum):
    """风控动作"""
    ALLOW = "ALLOW"               # 允许
    WARN = "WARN"                 # 警告
    BLOCK = "BLOCK"               # 阻止
    FORCE_SELL = "FORCE_SELL"     # 强制卖出
    CIRCUIT_BREAK = "CIRCUIT_BREAK"  # 熔断


class RiskCategory(str, Enum):
    """风险类别"""
    POSITION = "POSITION"         # 持仓风险
    MARKET = "MARKET"             # 市场风险
    LIQUIDITY = "LIQUIDITY"       # 流动性风险
    CONCENTRATION = "CONCENTRATION"  # 集中度风险
    LEVERAGE = "LEVERAGE"         # 杠杆风险
    COUNTERPARTY = "COUNTERPARTY" # 对手方风险
    OPERATIONAL = "OPERATIONAL"   # 操作风险


@dataclass
class RiskAlert:
    """风险预警"""
    alert_id: str
    category: RiskCategory
    level: RiskLevel
    title: str
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    affected_positions: List[str] = field(default_factory=list)
    suggested_action: RiskAction = RiskAction.WARN
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "category": self.category.value,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "affected_positions": self.affected_positions,
            "suggested_action": self.suggested_action.value,
            "metadata": self.metadata,
        }


@dataclass
class RiskCheckResult:
    """风控检查结果"""
    passed: bool
    risk_level: RiskLevel
    action: RiskAction
    alerts: List[RiskAlert] = field(default_factory=list)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class RiskChecker(ABC):
    """风控检查器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """检查器名称"""
        pass

    @property
    @abstractmethod
    def category(self) -> RiskCategory:
        """风险类别"""
        pass

    @abstractmethod
    async def check(self, context: Dict[str, Any]) -> RiskCheckResult:
        """执行检查"""
        pass


class PositionLimitChecker(RiskChecker):
    """持仓限制检查器"""

    @property
    def name(self) -> str:
        return "持仓限制检查"

    @property
    def category(self) -> RiskCategory:
        return RiskCategory.POSITION

    def __init__(
        self,
        max_position_value: float = 1000000,
        max_single_position_pct: float = 0.2,
        max_sector_pct: float = 0.4
    ):
        self.max_position_value = max_position_value
        self.max_single_position_pct = max_single_position_pct
        self.max_sector_pct = max_sector_pct

    async def check(self, context: Dict[str, Any]) -> RiskCheckResult:
        """检查持仓限制"""
        alerts = []
        passed = True
        risk_level = RiskLevel.LOW

        positions = context.get("positions", [])
        total_value = context.get("total_value", 0)
        order = context.get("order", {})

        # 检查总持仓价值
        if total_value > self.max_position_value:
            alerts.append(RiskAlert(
                alert_id=f"pos_limit_{datetime.utcnow().timestamp()}",
                category=self.category,
                level=RiskLevel.HIGH,
                title="总持仓超限",
                message=f"总持仓价值 {total_value:,.0f} 超过限制 {self.max_position_value:,.0f}",
                source=self.name,
                suggested_action=RiskAction.BLOCK
            ))
            passed = False
            risk_level = RiskLevel.HIGH

        # 检查单只股票集中度
        for position in positions:
            position_pct = position.get("value", 0) / max(total_value, 1)
            if position_pct > self.max_single_position_pct:
                alerts.append(RiskAlert(
                    alert_id=f"conc_limit_{position.get('symbol')}_{datetime.utcnow().timestamp()}",
                    category=RiskCategory.CONCENTRATION,
                    level=RiskLevel.MEDIUM,
                    title="持仓集中度过高",
                    message=f"股票 {position.get('symbol')} 占比 {position_pct:.1%} 超过限制 {self.max_single_position_pct:.1%}",
                    source=self.name,
                    affected_positions=[position.get("symbol")],
                    suggested_action=RiskAction.WARN
                ))
                risk_level = max(risk_level, RiskLevel.MEDIUM, key=lambda x: list(RiskLevel).index(x))

        # 检查行业集中度
        sector_exposure = self._calculate_sector_exposure(positions)
        for sector, exposure in sector_exposure.items():
            if exposure > self.max_sector_pct:
                alerts.append(RiskAlert(
                    alert_id=f"sector_limit_{sector}_{datetime.utcnow().timestamp()}",
                    category=RiskCategory.CONCENTRATION,
                    level=RiskLevel.MEDIUM,
                    title="行业集中度过高",
                    message=f"行业 {sector} 占比 {exposure:.1%} 超过限制 {self.max_sector_pct:.1%}",
                    source=self.name,
                    suggested_action=RiskAction.WARN
                ))

        return RiskCheckResult(
            passed=passed,
            risk_level=risk_level,
            action=RiskAction.ALLOW if passed else RiskAction.BLOCK,
            alerts=alerts,
            message="持仓限制检查通过" if passed else "持仓限制检查未通过"
        )

    def _calculate_sector_exposure(self, positions: List[Dict]) -> Dict[str, float]:
        """计算行业暴露"""
        sector_values = {}
        total_value = sum(p.get("value", 0) for p in positions)

        for position in positions:
            sector = position.get("sector", "未知")
            sector_values[sector] = sector_values.get(sector, 0) + position.get("value", 0)

        return {k: v / max(total_value, 1) for k, v in sector_values.items()}


class LossLimitChecker(RiskChecker):
    """亏损限制检查器"""

    @property
    def name(self) -> str:
        return "亏损限制检查"

    @property
    def category(self) -> RiskCategory:
        return RiskCategory.POSITION

    def __init__(
        self,
        max_daily_loss: float = 50000,
        max_daily_loss_pct: float = 0.02,
        max_total_loss_pct: float = 0.1
    ):
        self.max_daily_loss = max_daily_loss
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_total_loss_pct = max_total_loss_pct

    async def check(self, context: Dict[str, Any]) -> RiskCheckResult:
        """检查亏损限制"""
        alerts = []
        passed = True
        risk_level = RiskLevel.LOW

        daily_pnl = context.get("daily_pnl", 0)
        total_pnl = context.get("total_pnl", 0)
        initial_capital = context.get("initial_capital", 1)

        # 检查日亏损
        if daily_pnl < 0:
            daily_loss_pct = abs(daily_pnl) / initial_capital

            if abs(daily_pnl) > self.max_daily_loss:
                alerts.append(RiskAlert(
                    alert_id=f"daily_loss_{datetime.utcnow().timestamp()}",
                    category=self.category,
                    level=RiskLevel.CRITICAL,
                    title="日亏损超限",
                    message=f"日亏损 {abs(daily_pnl):,.0f} 超过限制 {self.max_daily_loss:,.0f}",
                    source=self.name,
                    suggested_action=RiskAction.CIRCUIT_BREAK
                ))
                passed = False
                risk_level = RiskLevel.CRITICAL

            elif daily_loss_pct > self.max_daily_loss_pct:
                alerts.append(RiskAlert(
                    alert_id=f"daily_loss_pct_{datetime.utcnow().timestamp()}",
                    category=self.category,
                    level=RiskLevel.HIGH,
                    title="日亏损比例超限",
                    message=f"日亏损比例 {daily_loss_pct:.1%} 超过限制 {self.max_daily_loss_pct:.1%}",
                    source=self.name,
                    suggested_action=RiskAction.WARN
                ))
                risk_level = RiskLevel.HIGH

        # 检查总亏损
        if total_pnl < 0:
            total_loss_pct = abs(total_pnl) / initial_capital
            if total_loss_pct > self.max_total_loss_pct:
                alerts.append(RiskAlert(
                    alert_id=f"total_loss_{datetime.utcnow().timestamp()}",
                    category=self.category,
                    level=RiskLevel.CRITICAL,
                    title="总亏损超限",
                    message=f"总亏损比例 {total_loss_pct:.1%} 超过限制 {self.max_total_loss_pct:.1%}",
                    source=self.name,
                    suggested_action=RiskAction.FORCE_SELL
                ))
                passed = False
                risk_level = RiskLevel.CRITICAL

        return RiskCheckResult(
            passed=passed,
            risk_level=risk_level,
            action=RiskAction.CIRCUIT_BREAK if not passed else RiskAction.ALLOW,
            alerts=alerts,
            message="亏损限制检查通过" if passed else "亏损限制检查未通过"
        )


class VolatilityChecker(RiskChecker):
    """波动率检查器"""

    @property
    def name(self) -> str:
        return "波动率检查"

    @property
    def category(self) -> RiskCategory:
        return RiskCategory.MARKET

    def __init__(
        self,
        max_volatility: float = 0.03,
        volatility_window: int = 20
    ):
        self.max_volatility = max_volatility
        self.volatility_window = volatility_window

    async def check(self, context: Dict[str, Any]) -> RiskCheckResult:
        """检查波动率"""
        alerts = []
        passed = True
        risk_level = RiskLevel.LOW

        market_volatility = context.get("market_volatility", 0)
        portfolio_volatility = context.get("portfolio_volatility", 0)

        # 检查市场波动
        if market_volatility > self.max_volatility:
            alerts.append(RiskAlert(
                alert_id=f"mkt_vol_{datetime.utcnow().timestamp()}",
                category=self.category,
                level=RiskLevel.HIGH,
                title="市场波动过大",
                message=f"市场波动率 {market_volatility:.2%} 超过阈值 {self.max_volatility:.2%}",
                source=self.name,
                suggested_action=RiskAction.WARN
            ))
            risk_level = RiskLevel.HIGH

        # 检查组合波动
        if portfolio_volatility > self.max_volatility * 1.5:
            alerts.append(RiskAlert(
                alert_id=f"port_vol_{datetime.utcnow().timestamp()}",
                category=self.category,
                level=RiskLevel.HIGH,
                title="组合波动过大",
                message=f"组合波动率 {portfolio_volatility:.2%} 超过阈值",
                source=self.name,
                suggested_action=RiskAction.WARN
            ))
            risk_level = max(risk_level, RiskLevel.MEDIUM, key=lambda x: list(RiskLevel).index(x))

        return RiskCheckResult(
            passed=passed,
            risk_level=risk_level,
            action=RiskAction.ALLOW,
            alerts=alerts,
            message="波动率检查通过" if passed else "波动率异常"
        )


class CircuitBreaker:
    """
    熔断器

    当风险达到临界级别时，自动触发熔断
    """

    def __init__(
        self,
        cooldown_period: int = 300,  # 5分钟冷却期
        auto_recovery: bool = False
    ):
        self.cooldown_period = cooldown_period
        self.auto_recovery = auto_recovery
        self._triggered = False
        self._triggered_at: Optional[datetime] = None
        self._trigger_count = 0

    @property
    def is_triggered(self) -> bool:
        """是否已触发熔断"""
        if not self._triggered:
            return False

        # 检查冷却期
        if self.auto_recovery and self._triggered_at:
            elapsed = (datetime.utcnow() - self._triggered_at).total_seconds()
            if elapsed > self.cooldown_period:
                self._triggered = False
                logger.info("熔断器自动恢复")
                return False

        return True

    def trigger(self, reason: str = "") -> None:
        """触发熔断"""
        self._triggered = True
        self._triggered_at = datetime.utcnow()
        self._trigger_count += 1

        logger.warning(f"熔断器触发! 原因: {reason}, 触发次数: {self._trigger_count}")

    def reset(self) -> None:
        """重置熔断器"""
        self._triggered = False
        self._triggered_at = None
        logger.info("熔断器已重置")


class RiskManagementSystem:
    """
    风险管理系统

    整合所有风控组件，提供统一的风控服务
    """

    def __init__(self):
        self._checkers: List[RiskChecker] = []
        self._circuit_breaker = CircuitBreaker()
        self._alert_handlers: List[Callable] = []
        self._alert_history: List[RiskAlert] = []

    def register_checker(self, checker: RiskChecker) -> None:
        """注册检查器"""
        self._checkers.append(checker)
        logger.info(f"注册风控检查器: {checker.name}")

    def register_alert_handler(self, handler: Callable) -> None:
        """注册预警处理器"""
        self._alert_handlers.append(handler)

    async def pre_trade_check(
        self,
        order: Dict[str, Any],
        context: Dict[str, Any]
    ) -> RiskCheckResult:
        """
        事前风控检查

        在订单执行前检查
        """
        # 检查熔断状态
        if self._circuit_breaker.is_triggered:
            return RiskCheckResult(
                passed=False,
                risk_level=RiskLevel.CRITICAL,
                action=RiskAction.BLOCK,
                message="系统处于熔断状态，禁止交易"
            )

        context["order"] = order
        all_alerts = []
        overall_passed = True
        overall_risk_level = RiskLevel.LOW

        # 执行所有检查
        for checker in self._checkers:
            try:
                result = await checker.check(context)

                if not result.passed:
                    overall_passed = False

                if result.alerts:
                    all_alerts.extend(result.alerts)
                    await self._handle_alerts(result.alerts)

                # 更新最高风险等级
                risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
                if risk_levels.index(result.risk_level) > risk_levels.index(overall_risk_level):
                    overall_risk_level = result.risk_level

            except Exception as e:
                logger.error(f"风控检查失败: {checker.name}, 错误: {e}")

        # 决定动作
        action = RiskAction.ALLOW
        if not overall_passed:
            action = RiskAction.BLOCK
        elif overall_risk_level == RiskLevel.CRITICAL:
            action = RiskAction.BLOCK
            self._circuit_breaker.trigger("风险等级达到 CRITICAL")
        elif overall_risk_level == RiskLevel.HIGH:
            action = RiskAction.WARN

        return RiskCheckResult(
            passed=overall_passed,
            risk_level=overall_risk_level,
            action=action,
            alerts=all_alerts,
            message="事前风控检查完成"
        )

    async def intraday_monitor(self, context: Dict[str, Any]) -> List[RiskAlert]:
        """
        事中风控监控

        实时监控持仓和风险
        """
        alerts = []

        # 检查熔断状态
        if self._circuit_breaker.is_triggered:
            alerts.append(RiskAlert(
                alert_id=f"cb_active_{datetime.utcnow().timestamp()}",
                category=RiskCategory.OPERATIONAL,
                level=RiskLevel.CRITICAL,
                title="熔断器激活",
                message="系统处于熔断状态",
                source="RiskManagementSystem",
                suggested_action=RiskAction.CIRCUIT_BREAK
            ))

        # 执行所有检查
        for checker in self._checkers:
            try:
                result = await checker.check(context)
                if result.alerts:
                    alerts.extend(result.alerts)
            except Exception as e:
                logger.error(f"风控监控失败: {checker.name}, 错误: {e}")

        if alerts:
            await self._handle_alerts(alerts)

        return alerts

    async def post_trade_analysis(
        self,
        trade_date: date,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        事后风控分析

        生成日度风险报告
        """
        report = {
            "trade_date": trade_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "alerts_count": len([a for a in self._alert_history if a.timestamp.date() == trade_date]),
            "circuit_breaker_triggered": self._circuit_breaker._trigger_count > 0,
            "risk_metrics": {},
            "recommendations": [],
        }

        # 计算风险指标
        report["risk_metrics"] = {
            "daily_pnl": context.get("daily_pnl", 0),
            "max_drawdown": context.get("max_drawdown", 0),
            "position_concentration": self._calculate_concentration(context.get("positions", [])),
            "sector_diversification": len(self._get_sector_distribution(context.get("positions", []))),
        }

        # 生成建议
        if report["risk_metrics"]["position_concentration"] > 0.3:
            report["recommendations"].append("建议降低持仓集中度，分散投资")

        if report["circuit_breaker_triggered"]:
            report["recommendations"].append("熔断器触发，建议检查策略参数")

        return report

    async def _handle_alerts(self, alerts: List[RiskAlert]) -> None:
        """处理预警"""
        self._alert_history.extend(alerts)

        for alert in alerts:
            logger.warning(f"风险预警: [{alert.level.value}] {alert.title} - {alert.message}")

            # 调用预警处理器
            for handler in self._alert_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    logger.error(f"预警处理失败: {e}")

    def _calculate_concentration(self, positions: List[Dict]) -> float:
        """计算持仓集中度 (HHI)"""
        if not positions:
            return 0

        total_value = sum(p.get("value", 0) for p in positions)
        if total_value == 0:
            return 0

        weights = [p.get("value", 0) / total_value for p in positions]
        return sum(w ** 2 for w in weights)

    def _get_sector_distribution(self, positions: List[Dict]) -> Dict[str, float]:
        """获取行业分布"""
        distribution = {}
        total_value = sum(p.get("value", 0) for p in positions)

        for position in positions:
            sector = position.get("sector", "未知")
            distribution[sector] = distribution.get(sector, 0) + position.get("value", 0)

        if total_value > 0:
            distribution = {k: v / total_value for k, v in distribution.items()}

        return distribution

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        """获取熔断器"""
        return self._circuit_breaker


# ==========================================
# 工厂函数
# ==========================================

def create_default_risk_system() -> RiskManagementSystem:
    """创建默认配置的风险管理系统"""
    system = RiskManagementSystem()

    # 注册默认检查器
    system.register_checker(PositionLimitChecker())
    system.register_checker(LossLimitChecker())
    system.register_checker(VolatilityChecker())

    return system
