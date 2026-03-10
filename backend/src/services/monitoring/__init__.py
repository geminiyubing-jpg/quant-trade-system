"""
监控模块

提供策略和交易系统的监控功能：
- 结构化日志
- Prometheus 指标
- 多渠道报警
"""

from .logging_config import (
    StructuredLogger,
    StructuredFormatter,
    setup_structured_logging,
    get_logger,
)

from .metrics import (
    StrategyMetrics,
    SystemMetrics,
    initialize_metrics,
    PROMETHEUS_AVAILABLE,
)

from .alerts import (
    Alert,
    AlertSeverity,
    AlertType,
    AlertChannel,
    AlertSystem,
    WebhookChannel,
    DingTalkChannel,
    WeChatWorkChannel,
    LogChannel,
    default_alert_system,
)


__all__ = [
    # 日志
    "StructuredLogger",
    "StructuredFormatter",
    "setup_structured_logging",
    "get_logger",

    # 指标
    "StrategyMetrics",
    "SystemMetrics",
    "initialize_metrics",
    "PROMETHEUS_AVAILABLE",

    # 报警
    "Alert",
    "AlertSeverity",
    "AlertType",
    "AlertChannel",
    "AlertSystem",
    "WebhookChannel",
    "DingTalkChannel",
    "WeChatWorkChannel",
    "LogChannel",
    "default_alert_system",
]
