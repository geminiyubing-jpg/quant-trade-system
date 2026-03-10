"""
==============================================
QuantAI Ecosystem - 事件驱动架构
==============================================

实现事件总线，支持：
- 事件发布/订阅
- 异步事件处理
- 事件溯源
- 事件重放
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Type, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import hashlib
import uuid

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EventType(str, Enum):
    """事件类型"""

    # 订单事件
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELED = "ORDER_CANCELED"
    ORDER_REJECTED = "ORDER_REJECTED"

    # 策略事件
    SIGNAL_GENERATED = "SIGNAL_GENERATED"
    STRATEGY_STARTED = "STRATEGY_STARTED"
    STRATEGY_STOPPED = "STRATEGY_STOPPED"
    STRATEGY_ERROR = "STRATEGY_ERROR"

    # 风控事件
    RISK_ALERT = "RISK_ALERT"
    RISK_LIMIT_BREACH = "RISK_LIMIT_BREACH"
    CIRCUIT_BREAKER_TRIGGERED = "CIRCUIT_BREAKER_TRIGGERED"

    # 市场事件
    MARKET_OPEN = "MARKET_OPEN"
    MARKET_CLOSE = "MARKET_CLOSE"
    PRICE_ALERT = "PRICE_ALERT"
    VOLATILITY_SPIKE = "VOLATILITY_SPIKE"

    # 数据事件
    DATA_UPDATED = "DATA_UPDATED"
    DATA_ERROR = "DATA_ERROR"

    # 组合事件
    POSITION_OPENED = "POSITION_OPENED"
    POSITION_CLOSED = "POSITION_CLOSED"
    PORTFOLIO_REBALANCED = "PORTFOLIO_REBALANCED"

    # 系统事件
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    SYSTEM_ERROR = "SYSTEM_ERROR"


@dataclass
class Event:
    """事件基类"""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM_STARTUP
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "system"
    version: str = "1.0"

    # 事件数据
    data: Dict[str, Any] = field(default_factory=dict)

    # 元数据
    correlation_id: Optional[str] = None  # 关联ID，用于追踪相关事件
    causation_id: Optional[str] = None    # 因果ID，记录导致此事件的事件

    # 重试信息
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "version": self.version,
            "data": self.data,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """从字典反序列化"""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            version=data["version"],
            data=data["data"],
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )

    def create_response(self, event_type: EventType, data: Dict[str, Any]) -> 'Event':
        """创建响应事件"""
        return Event(
            event_type=event_type,
            source=self.source,
            data=data,
            correlation_id=self.correlation_id or self.event_id,
            causation_id=self.event_id,
        )


@dataclass
class OrderCreatedEvent(Event):
    """订单创建事件"""
    event_type: EventType = EventType.ORDER_CREATED
    order_id: str = ""
    symbol: str = ""
    side: str = ""
    quantity: int = 0
    price: Optional[float] = None


@dataclass
class SignalGeneratedEvent(Event):
    """信号生成事件"""
    event_type: EventType = EventType.SIGNAL_GENERATED
    strategy_id: str = ""
    symbol: str = ""
    signal_type: str = ""
    confidence: float = 0.0


@dataclass
class RiskAlertEvent(Event):
    """风控预警事件"""
    event_type: EventType = EventType.RISK_ALERT
    alert_type: str = ""
    severity: str = "MEDIUM"
    message: str = ""
    affected_positions: List[str] = field(default_factory=list)


class EventHandler(ABC):
    """事件处理器接口"""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """处理事件"""
        pass

    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """判断是否能处理该类型事件"""
        pass


class EventHandlerWrapper:
    """事件处理器包装器"""

    def __init__(
        self,
        handler: Callable[[Event], Any],
        event_types: List[EventType],
        priority: int = 0,
        async_handler: bool = False
    ):
        self.handler = handler
        self.event_types = event_types
        self.priority = priority
        self.async_handler = async_handler


class EventBus:
    """
    事件总线

    功能：
    - 事件发布/订阅
    - 异步事件分发
    - 事件优先级
    - 错误处理和重试
    - 事件历史记录
    """

    def __init__(self, event_store=None):
        self._handlers: Dict[EventType, List[EventHandlerWrapper]] = {}
        self._event_store = event_store
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()

    def subscribe(
        self,
        event_types: List[EventType],
        handler: Callable[[Event], Any],
        priority: int = 0,
        async_handler: bool = False
    ) -> None:
        """
        订阅事件

        Args:
            event_types: 要订阅的事件类型列表
            handler: 事件处理函数
            priority: 优先级（数值越大优先级越高）
            async_handler: 是否为异步处理函数
        """
        wrapper = EventHandlerWrapper(
            handler=handler,
            event_types=event_types,
            priority=priority,
            async_handler=async_handler
        )

        for event_type in event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(wrapper)
            # 按优先级排序
            self._handlers[event_type].sort(key=lambda x: -x.priority)

        logger.debug(f"订阅事件: {[e.value for e in event_types]}, 处理器: {handler.__name__}")

    def unsubscribe(
        self,
        event_types: List[EventType],
        handler: Callable[[Event], Any]
    ) -> None:
        """取消订阅"""
        for event_type in event_types:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    w for w in self._handlers[event_type]
                    if w.handler != handler
                ]

    async def publish(self, event: Event) -> None:
        """
        发布事件

        Args:
            event: 要发布的事件
        """
        logger.debug(f"发布事件: {event.event_type.value}, ID: {event.event_id}")

        # 存储事件
        await self._store_event(event)

        # 添加到历史
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        # 分发事件
        await self._dispatch(event)

    async def publish_batch(self, events: List[Event]) -> None:
        """批量发布事件"""
        for event in events:
            await self.publish(event)

    async def _dispatch(self, event: Event) -> None:
        """分发事件到处理器"""
        handlers = self._handlers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"事件无处理器: {event.event_type.value}")
            return

        for wrapper in handlers:
            try:
                if wrapper.async_handler:
                    await wrapper.handler(event)
                else:
                    # 在线程池中执行同步处理器
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, wrapper.handler, event)

            except Exception as e:
                logger.error(
                    f"事件处理失败: {event.event_type.value}, "
                    f"处理器: {wrapper.handler.__name__}, "
                    f"错误: {e}"
                )

                # 重试逻辑
                if event.retry_count < event.max_retries:
                    event.retry_count += 1
                    logger.info(f"重试事件: {event.event_id}, 第 {event.retry_count} 次")
                    await asyncio.sleep(1 * event.retry_count)  # 指数退避
                    await self._dispatch(event)

    async def _store_event(self, event: Event) -> None:
        """存储事件"""
        if self._event_store:
            try:
                await self._event_store.save(event)
            except Exception as e:
                logger.error(f"事件存储失败: {e}")

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """获取事件历史"""
        if event_type:
            return [
                e for e in self._event_history[-limit:]
                if e.event_type == event_type
            ]
        return self._event_history[-limit:]

    def clear_history(self) -> None:
        """清除事件历史"""
        self._event_history.clear()


class EventStore:
    """
    事件存储

    用于持久化事件，支持事件溯源
    """

    def __init__(self, db_session=None):
        self.db = db_session
        self._memory_store: List[Dict] = []

    async def save(self, event: Event) -> None:
        """保存事件"""
        event_data = event.to_dict()

        if self.db:
            # 保存到数据库
            # await self._save_to_db(event_data)
            pass
        else:
            # 保存到内存
            self._memory_store.append(event_data)

    async def get_by_id(self, event_id: str) -> Optional[Event]:
        """根据ID获取事件"""
        for data in self._memory_store:
            if data["event_id"] == event_id:
                return Event.from_dict(data)
        return None

    async def get_by_correlation_id(self, correlation_id: str) -> List[Event]:
        """根据关联ID获取事件链"""
        return [
            Event.from_dict(data)
            for data in self._memory_store
            if data.get("correlation_id") == correlation_id
        ]

    async def get_by_type(
        self,
        event_type: EventType,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """根据类型和时间范围获取事件"""
        events = []
        for data in self._memory_store:
            if data["event_type"] != event_type.value:
                continue

            event_time = datetime.fromisoformat(data["timestamp"])
            if start_time and event_time < start_time:
                continue
            if end_time and event_time > end_time:
                continue

            events.append(Event.from_dict(data))

        return events


# ==========================================
# 装饰器
# ==========================================

def event_handler(*event_types: EventType, priority: int = 0):
    """
    事件处理器装饰器

    用法:
        @event_handler(EventType.ORDER_CREATED, EventType.ORDER_FILLED)
        async def handle_order_events(event: Event):
            print(f"处理订单事件: {event.event_type}")
    """
    def decorator(func: Callable) -> Callable:
        func._event_handler_info = {
            "event_types": list(event_types),
            "priority": priority,
        }
        return func
    return decorator


# ==========================================
# 全局事件总线实例
# ==========================================

_event_bus: Optional[EventBus] = None
_event_store: Optional[EventStore] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(event_store=_event_store)
    return _event_bus


def get_event_store() -> EventStore:
    """获取全局事件存储"""
    global _event_store
    if _event_store is None:
        _event_store = EventStore()
    return _event_store


def init_event_system(db_session=None) -> EventBus:
    """初始化事件系统"""
    global _event_bus, _event_store
    _event_store = EventStore(db_session=db_session)
    _event_bus = EventBus(event_store=_event_store)
    return _event_bus
