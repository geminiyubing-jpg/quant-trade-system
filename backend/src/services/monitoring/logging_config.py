"""
结构化日志配置

提供 JSON 格式的结构化日志，便于日志分析和监控。

特性：
- JSON 格式输出
- 自动添加上下文信息
- 支持日志级别过滤
- 集成到现有日志系统
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from decimal import Decimal
import traceback


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器

    将日志记录转换为 JSON 格式。
    """

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外字段
        if self.include_extra:
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in {
                    "name", "msg", "args", "created", "filename", "funcName",
                    "levelname", "levelno", "lineno", "module", "msecs",
                    "pathname", "process", "processName", "relativeCreated",
                    "stack_info", "exc_info", "exc_text", "thread", "threadName",
                    "message"
                }
            }
            if extra_fields:
                log_data["extra"] = self._serialize(extra_fields)

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[0] else None,
            }

        return json.dumps(log_data, ensure_ascii=False, default=str)

    def _serialize(self, obj: Any) -> Any:
        """序列化对象"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return {k: self._serialize(v) for k, v in obj.__dict__.items()}
        return obj


class StructuredLogger:
    """
    结构化日志器

    提供便捷的结构化日志记录方法。

    使用示例：
        logger = StructuredLogger("strategy.my_strategy")

        logger.log_signal(
            symbol="000001.SZ",
            signal_type="BUY",
            quantity=100,
            price=Decimal("10.5")
        )

        logger.log_order(order_id="123", status="FILLED")

        logger.log_trade(trade_id="456", pnl=Decimal("100"))
    """

    def __init__(self, name: str, context: Dict[str, Any] = None):
        """
        初始化结构化日志器

        Args:
            name: 日志器名称
            context: 默认上下文信息
        """
        self._logger = logging.getLogger(name)
        self._context = context or {}

    def _log(self, level: int, message: str, **kwargs) -> None:
        """内部日志方法"""
        extra = {**self._context, **kwargs}
        self._logger.log(level, message, extra=extra)

    # ==========================================
    # 通用方法
    # ==========================================

    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        self._log(logging.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        self._log(logging.DEBUG, message, **kwargs)

    # ==========================================
    # 策略专用方法
    # ==========================================

    def log_signal(
        self,
        symbol: str,
        signal_type: str,
        quantity: int,
        price: Decimal = None,
        confidence: float = None,
        reason: str = None,
        **kwargs
    ) -> None:
        """记录信号"""
        self._log(
            logging.INFO,
            f"信号生成: {symbol} {signal_type} {quantity}",
            event_type="signal",
            symbol=symbol,
            signal_type=signal_type,
            quantity=quantity,
            price=float(price) if price else None,
            confidence=confidence,
            reason=reason,
            **kwargs
        )

    def log_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal,
        status: str,
        **kwargs
    ) -> None:
        """记录订单"""
        self._log(
            logging.INFO,
            f"订单状态: {order_id} {symbol} {side} {quantity}@{price} -> {status}",
            event_type="order",
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=float(price),
            status=status,
            **kwargs
        )

    def log_trade(
        self,
        trade_id: str,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal,
        pnl: Decimal = None,
        **kwargs
    ) -> None:
        """记录成交"""
        self._log(
            logging.INFO,
            f"成交: {trade_id} {symbol} {side} {quantity}@{price}",
            event_type="trade",
            trade_id=trade_id,
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=float(price),
            pnl=float(pnl) if pnl else None,
            **kwargs
        )

    def log_position(
        self,
        symbol: str,
        quantity: int,
        avg_cost: Decimal,
        market_value: Decimal,
        pnl: Decimal = None,
        **kwargs
    ) -> None:
        """记录持仓"""
        self._log(
            logging.DEBUG,
            f"持仓更新: {symbol} {quantity}@{avg_cost} 市值={market_value}",
            event_type="position",
            symbol=symbol,
            quantity=quantity,
            avg_cost=float(avg_cost),
            market_value=float(market_value),
            pnl=float(pnl) if pnl else None,
            **kwargs
        )

    def log_portfolio(
        self,
        total_value: Decimal,
        cash: Decimal,
        positions_value: Decimal,
        daily_pnl: Decimal = None,
        **kwargs
    ) -> None:
        """记录组合状态"""
        self._log(
            logging.DEBUG,
            f"组合状态: 总资产={total_value} 现金={cash} 持仓={positions_value}",
            event_type="portfolio",
            total_value=float(total_value),
            cash=float(cash),
            positions_value=float(positions_value),
            daily_pnl=float(daily_pnl) if daily_pnl else None,
            **kwargs
        )

    # ==========================================
    # 风控专用方法
    # ==========================================

    def log_risk_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        **kwargs
    ) -> None:
        """记录风险预警"""
        level = logging.WARNING if severity == "WARNING" else logging.ERROR
        self._log(
            level,
            f"风险预警 [{alert_type}]: {message}",
            event_type="risk_alert",
            alert_type=alert_type,
            severity=severity,
            **kwargs
        )

    # ==========================================
    # 性能专用方法
    # ==========================================

    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        **kwargs
    ) -> None:
        """记录性能"""
        self._log(
            logging.DEBUG,
            f"性能: {operation} 耗时 {duration_ms:.2f}ms",
            event_type="performance",
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )


def setup_structured_logging(
    level: int = logging.INFO,
    output_file: str = None
) -> None:
    """
    配置结构化日志

    Args:
        level: 日志级别
        output_file: 输出文件路径（可选）
    """
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 移除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建结构化格式化器
    formatter = StructuredFormatter()

    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 添加文件处理器
    if output_file:
        file_handler = logging.FileHandler(output_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


# 便捷函数
def get_logger(name: str, **context) -> StructuredLogger:
    """
    获取结构化日志器

    Args:
        name: 日志器名称
        **context: 默认上下文

    Returns:
        结构化日志器实例
    """
    return StructuredLogger(name, context)
