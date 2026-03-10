"""
回测事件系统模块

提供事件驱动架构的核心组件：
- EventBus: 事件总线，负责事件的分发和路由
- Event: 事件基类，定义事件的通用结构
- 各种具体事件类型

事件驱动架构优势：
- 模块解耦：各组件通过事件通信，互不直接依赖
- 易于测试：可以模拟事件进行单元测试
- 可扩展性：新增功能只需订阅相关事件

事件流：
MarketEvent -> Strategy.on_data() -> SignalEvent -> RiskEngine -> OrderEvent -> ExecutionEngine -> FillEvent
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
import queue
import logging
import uuid

logger = logging.getLogger(__name__)


# ==============================================
# 事件类型枚举
# ==============================================

class EventType(str, Enum):
    """事件类型"""
    # 市场数据事件
    MARKET = "MARKET"               # 市场数据更新
    BAR_CLOSE = "BAR_CLOSE"         # K 线闭合
    TICK = "TICK"                   # Tick 数据

    # 策略事件
    SIGNAL = "SIGNAL"               # 交易信号

    # 订单事件
    ORDER_NEW = "ORDER_NEW"         # 新订单
    ORDER_UPDATE = "ORDER_UPDATE"   # 订单更新
    ORDER_CANCEL = "ORDER_CANCEL"   # 订单取消

    # 成交事件
    FILL = "FILL"                   # 成交

    # 定时事件
    TIMER = "TIMER"                 # 定时器
    SESSION_START = "SESSION_START" # 交易日开始
    SESSION_END = "SESSION_END"     # 交易日结束

    # 风控事件
    RISK_ALERT = "RISK_ALERT"       # 风险预警
    RISK_BREACH = "RISK_BREACH"     # 风险违规

    # 系统事件
    ERROR = "ERROR"                 # 错误
    LOG = "LOG"                     # 日志


# ==============================================
# 事件基类
# ==============================================

@dataclass
class Event:
    """
    事件基类

    所有事件都包含基本的事件信息。
    """
    type: EventType                      # 事件类型
    timestamp: datetime                  # 事件时间戳
    source: str = ""                     # 事件来源
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 事件 ID
    priority: int = 0                    # 优先级（数值越大优先级越高）
    data: Any = None                     # 事件数据

    def __lt__(self, other: 'Event') -> bool:
        """用于优先队列排序"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp


# ==============================================
# 市场数据事件
# ==============================================

@dataclass
class MarketEvent(Event):
    """
    市场数据事件

    当有新的市场数据到达时触发。
    """
    symbol: str = ""                     # 股票代码
    open: Decimal = Decimal("0")         # 开盘价
    high: Decimal = Decimal("0")         # 最高价
    low: Decimal = Decimal("0")          # 最低价
    close: Decimal = Decimal("0")        # 收盘价
    volume: int = 0                      # 成交量
    amount: Decimal = Decimal("0")       # 成交额

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: int,
        amount: Decimal = Decimal("0"),
        **kwargs
    ):
        super().__init__(
            type=EventType.MARKET,
            timestamp=timestamp,
            **kwargs
        )
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.amount = amount


@dataclass
class BarCloseEvent(Event):
    """
    K 线闭合事件

    当一根 K 线完成时触发。
    """
    symbol: str = ""
    frequency: str = "1d"
    bar_data: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        frequency: str = "1d",
        bar_data: Dict[str, Any] = None,
        **kwargs
    ):
        super().__init__(
            type=EventType.BAR_CLOSE,
            timestamp=timestamp,
            **kwargs
        )
        self.symbol = symbol
        self.frequency = frequency
        self.bar_data = bar_data or {}


# ==============================================
# 信号事件
# ==============================================

@dataclass
class SignalEvent(Event):
    """
    交易信号事件

    当策略生成交易信号时触发。
    """
    strategy_id: str = ""                # 策略 ID
    symbol: str = ""                     # 股票代码
    signal_type: str = ""                # 信号类型（BUY/SELL/CLOSE）
    quantity: int = 0                    # 数量
    price: Optional[Decimal] = None      # 价格（None 表示市价）
    confidence: float = 1.0              # 置信度
    reason: str = ""                     # 信号原因
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        signal_type: str,
        timestamp: datetime,
        quantity: int,
        price: Optional[Decimal] = None,
        confidence: float = 1.0,
        reason: str = "",
        metadata: Dict[str, Any] = None,
        **kwargs
    ):
        super().__init__(
            type=EventType.SIGNAL,
            timestamp=timestamp,
            source=strategy_id,
            **kwargs
        )
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.signal_type = signal_type
        self.quantity = quantity
        self.price = price
        self.confidence = confidence
        self.reason = reason
        self.metadata = metadata or {}


# ==============================================
# 订单事件
# ==============================================

@dataclass
class OrderEvent(Event):
    """
    订单事件

    当订单状态发生变化时触发。
    """
    order_id: str = ""                   # 订单 ID
    strategy_id: str = ""                # 策略 ID
    symbol: str = ""                     # 股票代码
    side: str = ""                       # 买卖方向
    order_type: str = "LIMIT"            # 订单类型
    quantity: int = 0                    # 委托数量
    price: Decimal = Decimal("0")        # 委托价格
    status: str = "PENDING"              # 订单状态
    filled_quantity: int = 0             # 成交数量
    filled_price: Decimal = Decimal("0") # 成交均价
    old_status: str = ""                 # 旧状态（用于 ORDER_UPDATE）

    def __init__(
        self,
        order_id: str,
        timestamp: datetime,
        event_type: EventType = EventType.ORDER_NEW,
        **kwargs
    ):
        super().__init__(
            type=event_type,
            timestamp=timestamp,
            **kwargs
        )
        self.order_id = order_id


# ==============================================
# 成交事件
# ==============================================

@dataclass
class FillEvent(Event):
    """
    成交事件

    当订单成交时触发。
    """
    order_id: str = ""                   # 订单 ID
    trade_id: str = ""                   # 成交 ID
    strategy_id: str = ""                # 策略 ID
    symbol: str = ""                     # 股票代码
    side: str = ""                       # 买卖方向
    quantity: int = 0                    # 成交数量
    price: Decimal = Decimal("0")        # 成交价格
    commission: Decimal = Decimal("0")   # 佣金
    slippage: Decimal = Decimal("0")     # 滑点

    def __init__(
        self,
        order_id: str,
        trade_id: str,
        timestamp: datetime,
        **kwargs
    ):
        super().__init__(
            type=EventType.FILL,
            timestamp=timestamp,
            **kwargs
        )
        self.order_id = order_id
        self.trade_id = trade_id


# ==============================================
# 定时事件
# ==============================================

@dataclass
class TimerEvent(Event):
    """
    定时器事件

    按照设定的时间间隔触发。
    """
    timer_name: str = ""                 # 定时器名称
    interval_seconds: int = 0            # 间隔秒数
    trigger_count: int = 0               # 触发次数

    def __init__(
        self,
        timer_name: str,
        timestamp: datetime,
        interval_seconds: int = 0,
        trigger_count: int = 0,
        **kwargs
    ):
        super().__init__(
            type=EventType.TIMER,
            timestamp=timestamp,
            **kwargs
        )
        self.timer_name = timer_name
        self.interval_seconds = interval_seconds
        self.trigger_count = trigger_count


@dataclass
class SessionEvent(Event):
    """
    交易日事件

    交易日开始/结束时触发。
    """
    session_date: datetime = None        # 交易日日期
    is_trading_day: bool = True          # 是否交易日

    def __init__(
        self,
        event_type: EventType,
        timestamp: datetime,
        session_date: datetime = None,
        is_trading_day: bool = True,
        **kwargs
    ):
        super().__init__(
            type=event_type,
            timestamp=timestamp,
            **kwargs
        )
        self.session_date = session_date or timestamp
        self.is_trading_day = is_trading_day


# ==============================================
# 风控事件
# ==============================================

@dataclass
class RiskEvent(Event):
    """
    风险事件

    当触发风险预警或违规时触发。
    """
    risk_type: str = ""                  # 风险类型
    severity: str = "WARNING"            # 严重程度（WARNING/CRITICAL）
    message: str = ""                    # 风险信息
    details: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        risk_type: str,
        timestamp: datetime,
        severity: str = "WARNING",
        message: str = "",
        details: Dict[str, Any] = None,
        **kwargs
    ):
        event_type = EventType.RISK_ALERT if severity == "WARNING" else EventType.RISK_BREACH
        super().__init__(
            type=event_type,
            timestamp=timestamp,
            **kwargs
        )
        self.risk_type = risk_type
        self.severity = severity
        self.message = message
        self.details = details or {}


# ==============================================
# 事件总线
# ==============================================

class EventBus:
    """
    事件总线

    负责事件的注册、分发和路由。采用发布-订阅模式。

    特性：
    - 支持多事件类型订阅
    - 支持优先级排序
    - 支持同步和异步处理
    - 支持事件过滤

    使用示例：
        bus = EventBus()

        # 注册处理器
        bus.register(EventType.MARKET, on_market_data)
        bus.register(EventType.SIGNAL, on_signal)

        # 发布事件
        bus.emit(MarketEvent(...))

        # 处理队列
        bus.process_queue()
    """

    def __init__(self, max_queue_size: int = 10000):
        """
        初始化事件总线

        Args:
            max_queue_size: 事件队列最大大小
        """
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._event_queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_queue_size)
        self._async_queue: List[Event] = []
        self._is_running = False
        self._processed_count = 0
        self._error_count = 0
        self.logger = logging.getLogger("EventBus")

    def register(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
        priority: int = 0
    ) -> None:
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数，接收 Event 参数
            priority: 优先级（同一事件类型的处理器按优先级执行）
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append((priority, handler))
        # 按优先级排序（高优先级在前）
        self._handlers[event_type].sort(key=lambda x: -x[0])

        self.logger.debug(f"注册事件处理器: {event_type.value} -> {handler.__name__}")

    def unregister(
        self,
        event_type: EventType,
        handler: Callable[[Event], None]
    ) -> bool:
        """
        注销事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数

        Returns:
            是否成功注销
        """
        if event_type not in self._handlers:
            return False

        for i, (_, h) in enumerate(self._handlers[event_type]):
            if h == handler:
                self._handlers[event_type].pop(i)
                self.logger.debug(f"注销事件处理器: {event_type.value} -> {handler.__name__}")
                return True

        return False

    def emit(self, event: Event) -> None:
        """
        发布事件

        将事件放入队列等待处理。

        Args:
            event: 事件对象
        """
        try:
            self._event_queue.put_nowait(event)
            self.logger.debug(f"发布事件: {event.type.value} [{event.event_id}]")
        except queue.Full:
            self.logger.error(f"事件队列已满，丢弃事件: {event.type.value}")
            self._error_count += 1

    def emit_immediate(self, event: Event) -> None:
        """
        立即发布事件

        不经过队列，直接调用处理器。

        Args:
            event: 事件对象
        """
        self._dispatch(event)

    def process_queue(self, max_events: int = None) -> int:
        """
        处理事件队列

        Args:
            max_events: 最大处理事件数（None 表示处理全部）

        Returns:
            处理的事件数量
        """
        processed = 0

        while not self._event_queue.empty():
            if max_events and processed >= max_events:
                break

            try:
                event = self._event_queue.get_nowait()
                self._dispatch(event)
                processed += 1
                self._processed_count += 1
            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"处理事件失败: {e}")
                self._error_count += 1

        return processed

    def process_all(self) -> int:
        """
        处理队列中的所有事件

        Returns:
            处理的事件数量
        """
        return self.process_queue()

    def _dispatch(self, event: Event) -> None:
        """
        分发事件到处理器

        Args:
            event: 事件对象
        """
        handlers = self._handlers.get(event.type, [])

        if not handlers:
            self.logger.debug(f"没有处理器注册事件类型: {event.type.value}")
            return

        for priority, handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(
                    f"事件处理器执行失败: {handler.__name__} -> {e}",
                    exc_info=True
                )
                # 继续执行其他处理器

    def clear_queue(self) -> int:
        """
        清空事件队列

        Returns:
            清除的事件数量
        """
        count = 0
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count

    def clear_handlers(self, event_type: EventType = None) -> None:
        """
        清除事件处理器

        Args:
            event_type: 事件类型（None 表示清除所有）
        """
        if event_type:
            self._handlers.pop(event_type, None)
        else:
            self._handlers.clear()

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self._event_queue.qsize()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计字典
        """
        return {
            "queue_size": self.get_queue_size(),
            "processed_count": self._processed_count,
            "error_count": self._error_count,
            "registered_types": list(self._handlers.keys()),
            "handler_counts": {
                et.value: len(handlers)
                for et, handlers in self._handlers.items()
            }
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._processed_count = 0
        self._error_count = 0


# ==============================================
# 事件过滤器
# ==============================================

class EventFilter:
    """
    事件过滤器

    用于过滤不符合条件的事件。
    """

    def __init__(self):
        self._filters: Dict[EventType, List[Callable[[Event], bool]]] = {}

    def add_filter(
        self,
        event_type: EventType,
        filter_func: Callable[[Event], bool]
    ) -> None:
        """
        添加过滤器

        Args:
            event_type: 事件类型
            filter_func: 过滤函数，返回 True 表示通过
        """
        if event_type not in self._filters:
            self._filters[event_type] = []
        self._filters[event_type].append(filter_func)

    def should_process(self, event: Event) -> bool:
        """
        检查事件是否应该被处理

        Args:
            event: 事件对象

        Returns:
            是否应该处理
        """
        filters = self._filters.get(event.type, [])

        for filter_func in filters:
            try:
                if not filter_func(event):
                    return False
            except Exception as e:
                logger.warning(f"过滤器执行失败: {e}")

        return True

    def clear(self, event_type: EventType = None) -> None:
        """清除过滤器"""
        if event_type:
            self._filters.pop(event_type, None)
        else:
            self._filters.clear()
