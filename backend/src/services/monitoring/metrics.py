"""
Prometheus 指标模块

提供策略和交易系统的 Prometheus 指标收集。

指标类型：
- Counter: 计数器（只增不减）
- Gauge: 仪表（可增可减）
- Histogram: 直方图（分布统计）
- Summary: 摘要（分位数统计）

使用示例：
    from services.monitoring.metrics import StrategyMetrics

    # 记录信号
    StrategyMetrics.record_signal("ma_cross", "BUY", "000001.SZ")

    # 记录订单
    StrategyMetrics.record_order("ma_cross", "BUY", "FILLED")

    # 更新组合价值
    StrategyMetrics.set_portfolio_value(1000000)
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import logging
import time

# 尝试导入 prometheus_client
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Gauge = Histogram = Summary = None
    REGISTRY = None

logger = logging.getLogger(__name__)


# ==============================================
# 策略指标
# ==============================================

class StrategyMetrics:
    """
    策略性能指标

    收集和暴露策略相关的 Prometheus 指标。
    """

    _initialized = False

    # ==========================================
    # 信号指标
    # ==========================================

    signals_generated: Counter = None  # 生成的信号数
    signals_by_type: Counter = None    # 按类型分类的信号数

    # ==========================================
    # 订单指标
    # ==========================================

    orders_submitted: Counter = None   # 提交的订单数
    orders_by_status: Counter = None   # 按状态分类的订单数
    order_value: Histogram = None      # 订单金额分布

    # ==========================================
    # 成交指标
    # ==========================================

    trades_executed: Counter = None    # 执行的成交数
    trade_value: Histogram = None      # 成交金额分布
    trade_pnl: Histogram = None        # 盈亏分布

    # ==========================================
    # 延迟指标
    # ==========================================

    order_latency: Histogram = None    # 订单延迟
    data_latency: Histogram = None     # 数据延迟

    # ==========================================
    # 组合指标
    # ==========================================

    portfolio_value: Gauge = None      # 组合价值
    portfolio_pnl: Gauge = None        # 组合盈亏
    portfolio_drawdown: Gauge = None   # 组合回撤
    position_count: Gauge = None       # 持仓数量
    cash_balance: Gauge = None         # 现金余额

    # ==========================================
    # 风控指标
    # ==========================================

    risk_alerts: Counter = None        # 风险预警数
    orders_rejected: Counter = None    # 被拒绝的订单数

    @classmethod
    def initialize(cls, registry=REGISTRY) -> None:
        """
        初始化指标

        Args:
            registry: Prometheus 注册表
        """
        if cls._initialized:
            return

        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus_client 未安装，指标收集不可用")
            cls._initialized = True
            return

        try:
            # 信号指标
            cls.signals_generated = Counter(
                "strategy_signals_generated_total",
                "Total number of signals generated",
                ["strategy_id"],
                registry=registry
            )

            cls.signals_by_type = Counter(
                "strategy_signals_by_type_total",
                "Number of signals by type",
                ["strategy_id", "signal_type", "symbol"],
                registry=registry
            )

            # 订单指标
            cls.orders_submitted = Counter(
                "strategy_orders_submitted_total",
                "Total number of orders submitted",
                ["strategy_id"],
                registry=registry
            )

            cls.orders_by_status = Counter(
                "strategy_orders_by_status_total",
                "Number of orders by status",
                ["strategy_id", "side", "status"],
                registry=registry
            )

            cls.order_value = Histogram(
                "strategy_order_value",
                "Order value distribution",
                ["strategy_id", "side"],
                buckets=[1000, 5000, 10000, 50000, 100000, 500000, 1000000],
                registry=registry
            )

            # 成交指标
            cls.trades_executed = Counter(
                "strategy_trades_executed_total",
                "Total number of trades executed",
                ["strategy_id"],
                registry=registry
            )

            cls.trade_value = Histogram(
                "strategy_trade_value",
                "Trade value distribution",
                ["strategy_id", "side"],
                buckets=[1000, 5000, 10000, 50000, 100000, 500000, 1000000],
                registry=registry
            )

            cls.trade_pnl = Histogram(
                "strategy_trade_pnl",
                "Trade PnL distribution",
                ["strategy_id"],
                buckets=[-10000, -5000, -1000, -500, -100, 0, 100, 500, 1000, 5000, 10000],
                registry=registry
            )

            # 延迟指标
            cls.order_latency = Histogram(
                "strategy_order_latency_seconds",
                "Order submission latency",
                ["strategy_id"],
                buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
                registry=registry
            )

            cls.data_latency = Histogram(
                "strategy_data_latency_seconds",
                "Data processing latency",
                ["strategy_id"],
                buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
                registry=registry
            )

            # 组合指标
            cls.portfolio_value = Gauge(
                "strategy_portfolio_value",
                "Current portfolio value",
                ["strategy_id"],
                registry=registry
            )

            cls.portfolio_pnl = Gauge(
                "strategy_portfolio_pnl",
                "Current portfolio PnL",
                ["strategy_id"],
                registry=registry
            )

            cls.portfolio_drawdown = Gauge(
                "strategy_portfolio_drawdown",
                "Current portfolio drawdown",
                ["strategy_id"],
                registry=registry
            )

            cls.position_count = Gauge(
                "strategy_position_count",
                "Number of positions",
                ["strategy_id"],
                registry=registry
            )

            cls.cash_balance = Gauge(
                "strategy_cash_balance",
                "Cash balance",
                ["strategy_id"],
                registry=registry
            )

            # 风控指标
            cls.risk_alerts = Counter(
                "strategy_risk_alerts_total",
                "Total number of risk alerts",
                ["strategy_id", "alert_type", "severity"],
                registry=registry
            )

            cls.orders_rejected = Counter(
                "strategy_orders_rejected_total",
                "Total number of orders rejected by risk control",
                ["strategy_id", "reason"],
                registry=registry
            )

            cls._initialized = True
            logger.info("策略指标初始化完成")

        except Exception as e:
            logger.error(f"策略指标初始化失败: {e}")

    # ==========================================
    # 记录方法
    # ==========================================

    @classmethod
    def record_signal(
        cls,
        strategy_id: str,
        signal_type: str,
        symbol: str
    ) -> None:
        """记录信号"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.signals_generated.labels(strategy_id=strategy_id).inc()
            cls.signals_by_type.labels(
                strategy_id=strategy_id,
                signal_type=signal_type,
                symbol=symbol
            ).inc()
        except Exception as e:
            logger.error(f"记录信号指标失败: {e}")

    @classmethod
    def record_order(
        cls,
        strategy_id: str,
        side: str,
        status: str,
        value: float = None
    ) -> None:
        """记录订单"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.orders_submitted.labels(strategy_id=strategy_id).inc()
            cls.orders_by_status.labels(
                strategy_id=strategy_id,
                side=side,
                status=status
            ).inc()

            if value is not None:
                cls.order_value.labels(
                    strategy_id=strategy_id,
                    side=side
                ).observe(value)
        except Exception as e:
            logger.error(f"记录订单指标失败: {e}")

    @classmethod
    def record_trade(
        cls,
        strategy_id: str,
        side: str,
        value: float,
        pnl: float = None
    ) -> None:
        """记录成交"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.trades_executed.labels(strategy_id=strategy_id).inc()
            cls.trade_value.labels(
                strategy_id=strategy_id,
                side=side
            ).observe(value)

            if pnl is not None:
                cls.trade_pnl.labels(strategy_id=strategy_id).observe(pnl)
        except Exception as e:
            logger.error(f"记录成交指标失败: {e}")

    @classmethod
    def record_latency(
        cls,
        strategy_id: str,
        latency_type: str,
        duration_seconds: float
    ) -> None:
        """记录延迟"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            if latency_type == "order":
                cls.order_latency.labels(strategy_id=strategy_id).observe(duration_seconds)
            elif latency_type == "data":
                cls.data_latency.labels(strategy_id=strategy_id).observe(duration_seconds)
        except Exception as e:
            logger.error(f"记录延迟指标失败: {e}")

    @classmethod
    def set_portfolio_value(cls, strategy_id: str, value: float) -> None:
        """设置组合价值"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.portfolio_value.labels(strategy_id=strategy_id).set(value)
        except Exception as e:
            logger.error(f"设置组合价值指标失败: {e}")

    @classmethod
    def set_portfolio_pnl(cls, strategy_id: str, pnl: float) -> None:
        """设置组合盈亏"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.portfolio_pnl.labels(strategy_id=strategy_id).set(pnl)
        except Exception as e:
            logger.error(f"设置组合盈亏指标失败: {e}")

    @classmethod
    def set_portfolio_drawdown(cls, strategy_id: str, drawdown: float) -> None:
        """设置组合回撤"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.portfolio_drawdown.labels(strategy_id=strategy_id).set(drawdown)
        except Exception as e:
            logger.error(f"设置组合回撤指标失败: {e}")

    @classmethod
    def set_position_count(cls, strategy_id: str, count: int) -> None:
        """设置持仓数量"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.position_count.labels(strategy_id=strategy_id).set(count)
        except Exception as e:
            logger.error(f"设置持仓数量指标失败: {e}")

    @classmethod
    def set_cash_balance(cls, strategy_id: str, balance: float) -> None:
        """设置现金余额"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.cash_balance.labels(strategy_id=strategy_id).set(balance)
        except Exception as e:
            logger.error(f"设置现金余额指标失败: {e}")

    @classmethod
    def record_risk_alert(
        cls,
        strategy_id: str,
        alert_type: str,
        severity: str
    ) -> None:
        """记录风险预警"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.risk_alerts.labels(
                strategy_id=strategy_id,
                alert_type=alert_type,
                severity=severity
            ).inc()
        except Exception as e:
            logger.error(f"记录风险预警指标失败: {e}")

    @classmethod
    def record_order_rejected(cls, strategy_id: str, reason: str) -> None:
        """记录订单被拒绝"""
        if not PROMETHEUS_AVAILABLE or not cls._initialized:
            return

        try:
            cls.orders_rejected.labels(
                strategy_id=strategy_id,
                reason=reason
            ).inc()
        except Exception as e:
            logger.error(f"记录订单拒绝指标失败: {e}")


# ==============================================
# 系统指标
# ==============================================

class SystemMetrics:
    """系统级别指标"""

    _initialized = False

    api_requests: Counter = None
    api_latency: Histogram = None
    websocket_connections: Gauge = None
    active_strategies: Gauge = None

    @classmethod
    def initialize(cls, registry=REGISTRY) -> None:
        """初始化系统指标"""
        if cls._initialized:
            return

        if not PROMETHEUS_AVAILABLE:
            cls._initialized = True
            return

        try:
            cls.api_requests = Counter(
                "api_requests_total",
                "Total API requests",
                ["endpoint", "method", "status"],
                registry=registry
            )

            cls.api_latency = Histogram(
                "api_latency_seconds",
                "API request latency",
                ["endpoint", "method"],
                buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
                registry=registry
            )

            cls.websocket_connections = Gauge(
                "websocket_connections",
                "Active WebSocket connections",
                registry=registry
            )

            cls.active_strategies = Gauge(
                "active_strategies",
                "Number of active strategies",
                registry=registry
            )

            cls._initialized = True
            logger.info("系统指标初始化完成")

        except Exception as e:
            logger.error(f"系统指标初始化失败: {e}")


# ==============================================
# 初始化
# ==============================================

def initialize_metrics() -> None:
    """初始化所有指标"""
    StrategyMetrics.initialize()
    SystemMetrics.initialize()


# 自动初始化
initialize_metrics()
