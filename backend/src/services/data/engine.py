"""
数据引擎模块

提供统一的数据管理功能，包括：
- 多数据源适配器管理
- 数据请求路由
- 实时数据订阅
- 数据缓存集成

设计模式：
- 适配器模式：支持多种数据源
- 策略模式：根据请求选择最优数据源
- 观察者模式：实时数据推送
"""

from typing import Dict, List, Optional, Any, Callable, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


# ==============================================
# 数据类型定义
# ==============================================

class DataType(str, Enum):
    """数据类型"""
    STOCK_INFO = "stock_info"           # 股票信息
    STOCK_PRICE = "stock_price"         # 股票价格
    STOCK_MINUTE = "stock_minute"       # 分钟数据
    STOCK_TICK = "stock_tick"           # Tick 数据
    INDEX = "index"                     # 指数数据
    FUNDAMENTAL = "fundamental"         # 基本面数据
    CORPORATE_ACTION = "corp_action"    # 公司行动（分红、拆股）

    # OpenBB 扩展数据类型
    MACRO_ECONOMIC = "macro_economic"       # 宏观经济数据
    TECHNICAL_INDICATOR = "technical"       # 技术指标
    QUANT_ANALYSIS = "quant_analysis"       # 量化分析


class DataFrequency(str, Enum):
    """数据频率"""
    TICK = "tick"
    MIN_1 = "1m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    MIN_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"


class AdjustmentType(str, Enum):
    """复权类型"""
    NONE = "none"       # 不复权
    FORWARD = "qfq"     # 前复权
    BACKWARD = "hfq"    # 后复权


@dataclass
class DataRequest:
    """
    数据请求

    封装数据请求的完整参数。
    """
    symbols: List[str]                              # 股票代码列表
    data_type: DataType = DataType.STOCK_PRICE      # 数据类型
    frequency: DataFrequency = DataFrequency.DAY    # 数据频率
    start_date: Optional[date] = None               # 开始日期
    end_date: Optional[date] = None                 # 结束日期
    adjustment: AdjustmentType = AdjustmentType.NONE  # 复权方式
    fields: Optional[List[str]] = None              # 需要的字段
    limit: Optional[int] = None                     # 限制返回数量

    # 请求元数据
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: int = 0                               # 优先级（数值越大优先级越高）
    timeout: int = 30                               # 超时时间（秒）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "symbols": self.symbols,
            "data_type": self.data_type.value,
            "frequency": self.frequency.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "adjustment": self.adjustment.value,
            "fields": self.fields,
            "limit": self.limit,
            "priority": self.priority,
            "timeout": self.timeout,
        }


@dataclass
class Bar:
    """
    K 线数据

    单根 K 线的完整信息。
    """
    symbol: str                     # 股票代码
    timestamp: datetime             # 时间戳
    open: Decimal                   # 开盘价
    high: Decimal                   # 最高价
    low: Decimal                    # 最低价
    close: Decimal                  # 收盘价
    volume: int                     # 成交量
    amount: Decimal = Decimal("0")  # 成交额
    turnover_rate: Optional[Decimal] = None  # 换手率

    # 扩展字段
    pre_close: Optional[Decimal] = None   # 昨收
    change: Optional[Decimal] = None      # 涨跌额
    change_pct: Optional[Decimal] = None  # 涨跌幅

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": str(self.open),
            "high": str(self.high),
            "low": str(self.low),
            "close": str(self.close),
            "volume": self.volume,
            "amount": str(self.amount),
            "turnover_rate": str(self.turnover_rate) if self.turnover_rate else None,
            "pre_close": str(self.pre_close) if self.pre_close else None,
            "change": str(self.change) if self.change else None,
            "change_pct": str(self.change_pct) if self.change_pct else None,
        }


@dataclass
class CorporateAction:
    """
    公司行动

    记录分红、送股、配股等公司行动。
    """
    symbol: str                     # 股票代码
    action_type: str                # 行动类型（dividend/split/rights_issue）
    ex_date: date                   # 除权除息日
    record_date: Optional[date] = None  # 股权登记日
    pay_date: Optional[date] = None     # 派息日

    # 分红
    dividend_per_share: Decimal = Decimal("0")  # 每股股息

    # 送股/转增
    bonus_per_share: Decimal = Decimal("0")     # 每股送股
    transfer_per_share: Decimal = Decimal("0")  # 每股转增

    # 配股
    rights_per_share: Decimal = Decimal("0")    # 每股配股
    rights_price: Decimal = Decimal("0")        # 配股价

    # 拆股/合股
    split_ratio: Decimal = Decimal("1")         # 拆股比例


# ==============================================
# 数据源适配器基类
# ==============================================

class DataSourceAdapter:
    """
    数据源适配器基类

    定义数据源的统一接口。
    所有数据源适配器都需要继承此类并实现相应方法。
    """

    # 数据源元信息
    name: str = "base"
    description: str = "基础数据源"
    supported_types: List[DataType] = []
    supported_frequencies: List[DataFrequency] = []
    is_realtime: bool = False
    priority: int = 0  # 优先级（数值越大优先级越高）

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化适配器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self._is_connected = False
        self.logger = logging.getLogger(f"DataAdapter.{self.name}")

    async def connect(self) -> bool:
        """
        连接数据源

        Returns:
            是否连接成功
        """
        self._is_connected = True
        return True

    async def disconnect(self) -> None:
        """断开连接"""
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected

    async def fetch_history(self, request: DataRequest) -> List[Dict[str, Any]]:
        """
        获取历史数据

        Args:
            request: 数据请求

        Returns:
            数据列表（每条数据为字典格式）

        Raises:
            NotImplementedError: 子类必须实现
        """
        raise NotImplementedError(f"{self.name} 不支持获取历史数据")

    async def fetch_latest(self, symbols: List[str]) -> Dict[str, Bar]:
        """
        获取最新行情

        Args:
            symbols: 股票代码列表

        Returns:
            {symbol: Bar}

        Raises:
            NotImplementedError: 子类必须实现
        """
        raise NotImplementedError(f"{self.name} 不支持获取最新行情")

    async def subscribe_realtime(
        self,
        symbols: List[str]
    ) -> AsyncIterator[Bar]:
        """
        订阅实时数据

        Args:
            symbols: 股票代码列表

        Yields:
            Bar: 实时 K 线数据

        Raises:
            NotImplementedError: 子类必须实现
        """
        raise NotImplementedError(f"{self.name} 不支持实时数据订阅")
        yield  # 使类型检查器满意

    async def get_corporate_actions(
        self,
        symbol: str,
        start_date: date = None,
        end_date: date = None
    ) -> List[CorporateAction]:
        """
        获取公司行动

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            公司行动列表

        Raises:
            NotImplementedError: 子类必须实现
        """
        raise NotImplementedError(f"{self.name} 不支持获取公司行动")

    def supports(self, data_type: DataType, frequency: DataFrequency) -> bool:
        """
        检查是否支持指定数据类型和频率

        Args:
            data_type: 数据类型
            frequency: 数据频率

        Returns:
            是否支持
        """
        return (
            data_type in self.supported_types and
            frequency in self.supported_frequencies
        )


# ==============================================
# 数据引擎
# ==============================================

class DataEngine:
    """
    数据引擎

    统一管理多个数据源，提供数据请求路由、缓存和实时订阅功能。

    使用方式：
        engine = DataEngine()

        # 注册适配器
        engine.register_adapter("akshare", AkShareAdapter())
        engine.register_adapter("tushare", TushareAdapter())

        # 获取历史数据
        data = await engine.get_history(DataRequest(
            symbols=["000001.SZ"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        ))

        # 订阅实时数据
        async for bar in engine.subscribe(["000001.SZ"]):
            print(bar)
    """

    def __init__(self, cache: 'DataCache' = None):
        """
        初始化数据引擎

        Args:
            cache: 数据缓存实例（可选）
        """
        self._adapters: Dict[str, DataSourceAdapter] = {}
        self._cache = cache
        self._subscriptions: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, List[Callable]] = {}

        self.logger = logging.getLogger("DataEngine")

    # ==========================================
    # 适配器管理
    # ==========================================

    def register_adapter(self, name: str, adapter: DataSourceAdapter) -> None:
        """
        注册数据源适配器

        Args:
            name: 适配器名称
            adapter: 适配器实例
        """
        if name in self._adapters:
            self.logger.warning(f"适配器 {name} 已存在，将被覆盖")

        self._adapters[name] = adapter
        self.logger.info(f"注册数据适配器: {name} ({adapter.description})")

    def unregister_adapter(self, name: str) -> bool:
        """
        注销数据源适配器

        Args:
            name: 适配器名称

        Returns:
            是否成功
        """
        if name in self._adapters:
            del self._adapters[name]
            self.logger.info(f"注销数据适配器: {name}")
            return True
        return False

    def get_adapter(self, name: str) -> Optional[DataSourceAdapter]:
        """
        获取适配器

        Args:
            name: 适配器名称

        Returns:
            适配器实例或 None
        """
        return self._adapters.get(name)

    def list_adapters(self) -> List[str]:
        """列出所有已注册的适配器"""
        return list(self._adapters.keys())

    def _select_adapter(
        self,
        data_type: DataType,
        frequency: DataFrequency,
        prefer_realtime: bool = False
    ) -> Optional[DataSourceAdapter]:
        """
        选择最优适配器

        根据数据类型、频率和实时性要求选择最优的数据源。

        Args:
            data_type: 数据类型
            frequency: 数据频率
            prefer_realtime: 是否优先选择实时数据源

        Returns:
            最优适配器或 None
        """
        candidates = []

        for adapter in self._adapters.values():
            if adapter.supports(data_type, frequency):
                candidates.append(adapter)

        if not candidates:
            return None

        # 排序：优先级高的优先，实时需求优先选择实时数据源
        def sort_key(a):
            realtime_score = 10 if (prefer_realtime and a.is_realtime) else 0
            return a.priority + realtime_score

        candidates.sort(key=sort_key, reverse=True)
        return candidates[0]

    # ==========================================
    # 连接管理
    # ==========================================

    async def connect_all(self) -> Dict[str, bool]:
        """
        连接所有数据源

        Returns:
            {adapter_name: 是否连接成功}
        """
        results = {}
        for name, adapter in self._adapters.items():
            try:
                results[name] = await adapter.connect()
            except Exception as e:
                self.logger.error(f"连接 {name} 失败: {e}")
                results[name] = False
        return results

    async def disconnect_all(self) -> None:
        """断开所有数据源连接"""
        for name, adapter in self._adapters.items():
            try:
                await adapter.disconnect()
            except Exception as e:
                self.logger.error(f"断开 {name} 失败: {e}")

    # ==========================================
    # 数据获取
    # ==========================================

    async def get_data(self, request: DataRequest) -> List[Dict[str, Any]]:
        """
        获取数据（统一入口）

        根据请求参数自动选择最优数据源，并应用缓存。

        Args:
            request: 数据请求

        Returns:
            数据列表
        """
        # 1. 尝试从缓存获取
        if self._cache:
            cache_key = self._make_cache_key(request)
            cached = self._cache.get(cache_key)
            if cached is not None:
                self.logger.debug(f"缓存命中: {cache_key}")
                return cached

        # 2. 选择适配器
        adapter = self._select_adapter(
            request.data_type,
            request.frequency
        )

        if adapter is None:
            raise ValueError(
                f"没有支持 {request.data_type.value}/{request.frequency.value} 的数据源"
            )

        # 3. 获取数据
        self.logger.info(
            f"获取数据: {request.symbols} via {adapter.name}"
        )

        data = await adapter.fetch_history(request)

        # 4. 写入缓存
        if self._cache and data:
            cache_key = self._make_cache_key(request)
            self._cache.set(cache_key, data)

        return data

    async def get_latest(self, symbols: List[str]) -> Dict[str, Bar]:
        """
        获取最新行情

        Args:
            symbols: 股票代码列表

        Returns:
            {symbol: Bar}
        """
        adapter = self._select_adapter(
            DataType.STOCK_PRICE,
            DataFrequency.DAY,
            prefer_realtime=True
        )

        if adapter is None:
            raise ValueError("没有支持获取最新行情的数据源")

        return await adapter.fetch_latest(symbols)

    async def get_corporate_actions(
        self,
        symbol: str,
        start_date: date = None,
        end_date: date = None
    ) -> List[CorporateAction]:
        """
        获取公司行动

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            公司行动列表
        """
        for adapter in self._adapters.values():
            try:
                return await adapter.get_corporate_actions(
                    symbol, start_date, end_date
                )
            except NotImplementedError:
                continue

        return []

    # ==========================================
    # 实时订阅
    # ==========================================

    async def subscribe(
        self,
        symbols: List[str],
        callback: Callable[[Bar], None],
        frequency: DataFrequency = DataFrequency.MIN_1
    ) -> str:
        """
        订阅实时数据

        Args:
            symbols: 股票代码列表
            callback: 数据回调函数
            frequency: 数据频率

        Returns:
            订阅 ID（用于取消订阅）
        """
        adapter = self._select_adapter(
            DataType.STOCK_PRICE,
            frequency,
            prefer_realtime=True
        )

        if adapter is None or not adapter.is_realtime:
            raise ValueError("没有支持实时数据的适配器")

        subscription_id = str(uuid.uuid4())

        # 存储回调
        if subscription_id not in self._callbacks:
            self._callbacks[subscription_id] = []
        self._callbacks[subscription_id].append(callback)

        # 创建订阅任务
        async def subscription_task():
            try:
                async for bar in adapter.subscribe_realtime(symbols):
                    # 调用所有回调
                    for cb in self._callbacks.get(subscription_id, []):
                        try:
                            cb(bar)
                        except Exception as e:
                            self.logger.error(f"回调执行失败: {e}")
            except asyncio.CancelledError:
                self.logger.info(f"订阅 {subscription_id} 已取消")
            except Exception as e:
                self.logger.error(f"订阅任务错误: {e}")

        self._subscriptions[subscription_id] = asyncio.create_task(subscription_task)

        self.logger.info(f"创建订阅: {subscription_id} for {symbols}")

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅

        Args:
            subscription_id: 订阅 ID

        Returns:
            是否成功
        """
        if subscription_id in self._subscriptions:
            task = self._subscriptions.pop(subscription_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            self._callbacks.pop(subscription_id, None)
            self.logger.info(f"取消订阅: {subscription_id}")
            return True
        return False

    async def unsubscribe_all(self) -> None:
        """取消所有订阅"""
        for subscription_id in list(self._subscriptions.keys()):
            await self.unsubscribe(subscription_id)

    # ==========================================
    # 缓存管理
    # ==========================================

    def set_cache(self, cache: 'DataCache') -> None:
        """
        设置数据缓存

        Args:
            cache: 缓存实例
        """
        self._cache = cache

    def _make_cache_key(self, request: DataRequest) -> str:
        """
        生成缓存键

        Args:
            request: 数据请求

        Returns:
            缓存键
        """
        symbols_str = ",".join(sorted(request.symbols))
        return (
            f"data:{request.data_type.value}:{request.frequency.value}:"
            f"{symbols_str}:{request.start_date}:{request.end_date}:"
            f"{request.adjustment.value}"
        )

    def invalidate_cache(self, pattern: str = None) -> None:
        """
        使缓存失效

        Args:
            pattern: 缓存键模式（支持通配符）
        """
        if self._cache:
            self._cache.invalidate(pattern or "data:*")

    # ==========================================
    # 状态管理
    # ==========================================

    def get_status(self) -> Dict[str, Any]:
        """
        获取引擎状态

        Returns:
            状态字典
        """
        return {
            "adapters": {
                name: {
                    "description": adapter.description,
                    "is_connected": adapter.is_connected,
                    "is_realtime": adapter.is_realtime,
                    "priority": adapter.priority,
                }
                for name, adapter in self._adapters.items()
            },
            "active_subscriptions": len(self._subscriptions),
            "cache_enabled": self._cache is not None,
        }
