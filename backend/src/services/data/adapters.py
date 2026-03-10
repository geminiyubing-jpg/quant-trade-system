"""
数据源适配器模块

提供多种数据源的适配器实现：
- AkShareAdapter: AkShare 免费数据源
- TushareAdapter: Tushare Pro 数据源
- DatabaseAdapter: PostgreSQL 数据库适配器
- MemoryAdapter: 内存数据适配器（用于测试）

每个适配器实现统一的 DataSourceAdapter 接口。
"""

from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime, date, timedelta
from decimal import Decimal
import asyncio
import logging
import random

from .engine import (
    DataSourceAdapter,
    DataRequest,
    Bar,
    CorporateAction,
    DataType,
    DataFrequency,
)

logger = logging.getLogger(__name__)


# ==============================================
# AkShare 适配器
# ==============================================

class AkShareAdapter(DataSourceAdapter):
    """
    AkShare 数据源适配器

    使用 AkShare 库获取免费行情数据。

    支持的数据：
    - A 股日线行情
    - A 股分钟行情
    - 股票基本信息
    - 公司行动
    """

    name = "akshare"
    description = "AkShare 免费数据源"
    supported_types = [DataType.STOCK_PRICE, DataType.STOCK_INFO, DataType.INDEX]
    supported_frequencies = [DataFrequency.DAY, DataFrequency.MIN_1, DataFrequency.MIN_5]
    is_realtime = False
    priority = 10

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._akshare = None

    async def connect(self) -> bool:
        """连接数据源（延迟导入）"""
        try:
            import akshare as ak
            self._akshare = ak
            self._is_connected = True
            self.logger.info("AkShare 适配器已连接")
            return True
        except ImportError:
            self.logger.error("未安装 akshare 库，请执行: pip install akshare")
            return False

    async def fetch_history(self, request: DataRequest) -> List[Dict[str, Any]]:
        """
        获取历史数据

        Args:
            request: 数据请求

        Returns:
            数据列表
        """
        if not self._is_connected or self._akshare is None:
            raise RuntimeError("AkShare 未连接")

        results = []

        for symbol in request.symbols:
            try:
                # 转换股票代码格式（如 000001.SZ -> 000001）
                ts_code = symbol.split(".")[0]

                if request.frequency == DataFrequency.DAY:
                    # 获取日线数据
                    df = self._akshare.stock_zh_a_hist(
                        symbol=ts_code,
                        period="daily",
                        start_date=request.start_date.strftime("%Y%m%d") if request.start_date else "19900101",
                        end_date=request.end_date.strftime("%Y%m%d") if request.end_date else datetime.now().strftime("%Y%m%d"),
                        adjust=""  # 不复权，由对齐模块处理
                    )

                    for _, row in df.iterrows():
                        results.append({
                            "symbol": symbol,
                            "timestamp": datetime.strptime(str(row["日期"]), "%Y-%m-%d"),
                            "open": Decimal(str(row["开盘"])),
                            "high": Decimal(str(row["最高"])),
                            "low": Decimal(str(row["最低"])),
                            "close": Decimal(str(row["收盘"])),
                            "volume": int(row["成交量"]),
                            "amount": Decimal(str(row["成交额"])),
                        })

                elif request.frequency in [DataFrequency.MIN_1, DataFrequency.MIN_5]:
                    # 获取分钟数据
                    period = "1" if request.frequency == DataFrequency.MIN_1 else "5"
                    df = self._akshare.stock_zh_a_minute(
                        symbol=ts_code,
                        period=period,
                        adjust=""
                    )

                    for _, row in df.iterrows():
                        results.append({
                            "symbol": symbol,
                            "timestamp": datetime.strptime(str(row["day"]), "%Y-%m-%d %H:%M:%S"),
                            "open": Decimal(str(row["open"])),
                            "high": Decimal(str(row["high"])),
                            "low": Decimal(str(row["low"])),
                            "close": Decimal(str(row["close"])),
                            "volume": int(row["volume"]),
                            "amount": Decimal("0"),
                        })

            except Exception as e:
                self.logger.error(f"获取 {symbol} 数据失败: {e}")
                continue

        return results

    async def fetch_latest(self, symbols: List[str]) -> Dict[str, Bar]:
        """
        获取最新行情

        Args:
            symbols: 股票代码列表

        Returns:
            {symbol: Bar}
        """
        if not self._is_connected or self._akshare is None:
            raise RuntimeError("AkShare 未连接")

        results = {}

        try:
            # 获取实时行情
            df = self._akshare.stock_zh_a_spot_em()

            for symbol in symbols:
                ts_code = symbol.split(".")[0]
                row = df[df["代码"] == ts_code]

                if not row.empty:
                    row = row.iloc[0]
                    results[symbol] = Bar(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        open=Decimal(str(row["今开"])),
                        high=Decimal(str(row["最高"])),
                        low=Decimal(str(row["最低"])),
                        close=Decimal(str(row["最新价"])),
                        volume=int(row["成交量"]),
                        amount=Decimal(str(row["成交额"])),
                        pre_close=Decimal(str(row["昨收"])),
                        change_pct=Decimal(str(row["涨跌幅"])),
                    )

        except Exception as e:
            self.logger.error(f"获取实时行情失败: {e}")

        return results


# ==============================================
# Tushare 适配器
# ==============================================

class TushareAdapter(DataSourceAdapter):
    """
    Tushare Pro 数据源适配器

    使用 Tushare Pro API 获取高质量数据。

    支持的数据：
    - A 股日线/分钟/Tick 行情
    - 指数数据
    - 基本面数据
    - 公司行动
    """

    name = "tushare"
    description = "Tushare Pro 数据源"
    supported_types = [
        DataType.STOCK_PRICE,
        DataType.STOCK_MINUTE,
        DataType.STOCK_TICK,
        DataType.STOCK_INFO,
        DataType.INDEX,
        DataType.FUNDAMENTAL,
        DataType.CORPORATE_ACTION,
    ]
    supported_frequencies = [
        DataFrequency.TICK,
        DataFrequency.MIN_1,
        DataFrequency.MIN_5,
        DataFrequency.MIN_15,
        DataFrequency.MIN_30,
        DataFrequency.DAY,
        DataFrequency.WEEK,
        DataFrequency.MONTH,
    ]
    is_realtime = False
    priority = 20  # 优先级高于 AkShare

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._tushare = None
        self._pro = None
        self._token = config.get("token") if config else None

    async def connect(self) -> bool:
        """连接数据源"""
        try:
            import tushare as ts
            self._tushare = ts

            if self._token:
                ts.set_token(self._token)
                self._pro = ts.pro_api()
            else:
                self._pro = ts.pro_api()

            self._is_connected = True
            self.logger.info("Tushare 适配器已连接")
            return True

        except ImportError:
            self.logger.error("未安装 tushare 库，请执行: pip install tushare")
            return False
        except Exception as e:
            self.logger.error(f"Tushare 连接失败: {e}")
            return False

    async def fetch_history(self, request: DataRequest) -> List[Dict[str, Any]]:
        """获取历史数据"""
        if not self._is_connected or self._pro is None:
            raise RuntimeError("Tushare 未连接")

        results = []

        for symbol in request.symbols:
            try:
                # Tushare 使用 ts_code 格式（如 000001.SZ）
                ts_code = symbol

                if request.frequency == DataFrequency.DAY:
                    df = self._pro.daily(
                        ts_code=ts_code,
                        start_date=request.start_date.strftime("%Y%m%d") if request.start_date else None,
                        end_date=request.end_date.strftime("%Y%m%d") if request.end_date else None,
                    )

                    for _, row in df.iterrows():
                        results.append({
                            "symbol": symbol,
                            "timestamp": datetime.strptime(str(row["trade_date"]), "%Y%m%d"),
                            "open": Decimal(str(row["open"])),
                            "high": Decimal(str(row["high"])),
                            "low": Decimal(str(row["low"])),
                            "close": Decimal(str(row["close"])),
                            "volume": int(row["vol"] * 100) if row["vol"] else 0,
                            "amount": Decimal(str(row["amount"] * 1000)) if row["amount"] else Decimal("0"),
                        })

                elif request.frequency in [DataFrequency.MIN_1, DataFrequency.MIN_5, DataFrequency.MIN_15, DataFrequency.MIN_30]:
                    freq_map = {
                        DataFrequency.MIN_1: "1min",
                        DataFrequency.MIN_5: "5min",
                        DataFrequency.MIN_15: "15min",
                        DataFrequency.MIN_30: "30min",
                    }

                    df = self._pro.pro_bar(
                        ts_code=ts_code,
                        freq=freq_map[request.frequency],
                        start_date=request.start_date.strftime("%Y%m%d") if request.start_date else None,
                        end_date=request.end_date.strftime("%Y%m%d") if request.end_date else None,
                    )

                    for _, row in df.iterrows():
                        results.append({
                            "symbol": symbol,
                            "timestamp": datetime.strptime(str(row["trade_time"]), "%Y-%m-%d %H:%M:%S"),
                            "open": Decimal(str(row["open"])),
                            "high": Decimal(str(row["high"])),
                            "low": Decimal(str(row["low"])),
                            "close": Decimal(str(row["close"])),
                            "volume": int(row["vol"]) if row["vol"] else 0,
                            "amount": Decimal(str(row["amount"])) if row["amount"] else Decimal("0"),
                        })

            except Exception as e:
                self.logger.error(f"获取 {symbol} 数据失败: {e}")
                continue

        return results

    async def get_corporate_actions(
        self,
        symbol: str,
        start_date: date = None,
        end_date: date = None
    ) -> List[CorporateAction]:
        """获取公司行动"""
        if not self._is_connected or self._pro is None:
            raise RuntimeError("Tushare 未连接")

        results = []

        try:
            # 获取分红送股数据
            df = self._pro.dividend(
                ts_code=symbol,
            )

            for _, row in df.iterrows():
                results.append(CorporateAction(
                    symbol=symbol,
                    action_type="dividend",
                    ex_date=datetime.strptime(str(row["ex_date"]), "%Y%m%d").date() if row["ex_date"] else None,
                    record_date=datetime.strptime(str(row["record_date"]), "%Y%m%d").date() if row["record_date"] else None,
                    pay_date=datetime.strptime(str(row["pay_date"]), "%Y%m%d").date() if row["pay_date"] else None,
                    dividend_per_share=Decimal(str(row["cash_div"]) if row["cash_div"] else "0"),
                    bonus_per_share=Decimal(str(row["bonus_ratio_r"]) if row["bonus_ratio_r"] else "0"),
                    transfer_per_share=Decimal(str(row["transfer_ratio_r"]) if row["transfer_ratio_r"] else "0"),
                ))

        except Exception as e:
            self.logger.error(f"获取 {symbol} 公司行动失败: {e}")

        return results


# ==============================================
# 数据库适配器
# ==============================================

class DatabaseAdapter(DataSourceAdapter):
    """
    PostgreSQL 数据库适配器

    从本地数据库获取数据，支持高速查询。

    适用场景：
    - 已有历史数据存储
    - 高频数据查询
    - 离线回测
    """

    name = "database"
    description = "PostgreSQL 数据库适配器"
    supported_types = [DataType.STOCK_PRICE, DataType.STOCK_MINUTE, DataType.INDEX]
    supported_frequencies = [
        DataFrequency.MIN_1,
        DataFrequency.MIN_5,
        DataFrequency.MIN_15,
        DataFrequency.MIN_30,
        DataFrequency.HOUR_1,
        DataFrequency.DAY,
        DataFrequency.WEEK,
        DataFrequency.MONTH,
    ]
    is_realtime = False
    priority = 30  # 最高优先级（本地数据最快）

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._pool = None
        self._db_url = config.get("database_url") if config else None

    async def connect(self) -> bool:
        """连接数据库"""
        try:
            # 使用 SQLAlchemy 异步连接池
            from sqlalchemy.ext.asyncio import create_async_engine

            if self._db_url:
                self._pool = create_async_engine(self._db_url)
                self._is_connected = True
                self.logger.info("数据库适配器已连接")
                return True
            else:
                self.logger.warning("未配置数据库 URL")
                return False

        except ImportError:
            self.logger.error("未安装 sqlalchemy 库")
            return False
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return False

    async def fetch_history(self, request: DataRequest) -> List[Dict[str, Any]]:
        """从数据库获取历史数据"""
        if not self._is_connected or self._pool is None:
            raise RuntimeError("数据库未连接")

        # 构建查询
        table_map = {
            DataFrequency.DAY: "stock_prices_daily",
            DataFrequency.MIN_1: "stock_prices_1min",
            DataFrequency.MIN_5: "stock_prices_5min",
        }

        table_name = table_map.get(request.frequency, "stock_prices_daily")

        # 这里是简化的查询逻辑，实际实现需要根据数据库结构调整
        results = []
        # ... 数据库查询代码 ...

        return results


# ==============================================
# 内存适配器（用于测试）
# ==============================================

class MemoryAdapter(DataSourceAdapter):
    """
    内存数据适配器

    用于测试和开发，数据存储在内存中。

    特性：
    - 预加载历史数据
    - 模拟实时数据推送
    - 支持随机数据生成
    """

    name = "memory"
    description = "内存数据适配器（测试用）"
    supported_types = [DataType.STOCK_PRICE, DataType.STOCK_MINUTE]
    supported_frequencies = [DataFrequency.DAY, DataFrequency.MIN_1]
    is_realtime = True
    priority = 5

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._data: Dict[str, List[Dict[str, Any]]] = {}
        self._latest: Dict[str, Bar] = {}
        self._running = False

    def load_data(self, symbol: str, data: List[Dict[str, Any]]) -> None:
        """
        加载历史数据

        Args:
            symbol: 股票代码
            data: 数据列表
        """
        self._data[symbol] = data

    def load_bars(self, symbol: str, bars: List[Bar]) -> None:
        """
        加载 Bar 数据

        Args:
            symbol: 股票代码
            bars: Bar 列表
        """
        self._data[symbol] = [bar.to_dict() for bar in bars]

    async def connect(self) -> bool:
        """连接（内存适配器始终可用）"""
        self._is_connected = True
        self.logger.info("内存适配器已就绪")
        return True

    async def fetch_history(self, request: DataRequest) -> List[Dict[str, Any]]:
        """获取历史数据"""
        results = []

        for symbol in request.symbols:
            data = self._data.get(symbol, [])

            # 过滤日期范围
            if request.start_date or request.end_date:
                filtered = []
                for bar in data:
                    ts = bar.get("timestamp")
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts)
                    if isinstance(ts, datetime):
                        bar_date = ts.date()
                    else:
                        continue

                    if request.start_date and bar_date < request.start_date:
                        continue
                    if request.end_date and bar_date > request.end_date:
                        continue
                    filtered.append(bar)
                data = filtered

            # 限制数量
            if request.limit:
                data = data[-request.limit:]

            results.extend(data)

        return results

    async def fetch_latest(self, symbols: List[str]) -> Dict[str, Bar]:
        """获取最新行情"""
        return {symbol: bar for symbol, bar in self._latest.items() if symbol in symbols}

    async def subscribe_realtime(
        self,
        symbols: List[str]
    ) -> AsyncIterator[Bar]:
        """
        模拟实时数据推送

        遍历历史数据并模拟实时推送。
        """
        self._running = True

        for symbol in symbols:
            data = self._data.get(symbol, [])

            for bar_data in data:
                if not self._running:
                    break

                bar = Bar(
                    symbol=symbol,
                    timestamp=datetime.fromisoformat(bar_data["timestamp"])
                    if isinstance(bar_data["timestamp"], str)
                    else bar_data["timestamp"],
                    open=Decimal(str(bar_data["open"])),
                    high=Decimal(str(bar_data["high"])),
                    low=Decimal(str(bar_data["low"])),
                    close=Decimal(str(bar_data["close"])),
                    volume=int(bar_data["volume"]),
                    amount=Decimal(str(bar_data.get("amount", 0))),
                )

                self._latest[symbol] = bar
                yield bar

                # 模拟实时延迟
                await asyncio.sleep(0.1)

    async def disconnect(self) -> None:
        """断开连接"""
        self._running = False
        await super().disconnect()

    def generate_random_data(
        self,
        symbol: str,
        days: int = 365,
        start_price: float = 10.0
    ) -> None:
        """
        生成随机测试数据

        Args:
            symbol: 股票代码
            days: 天数
            start_price: 起始价格
        """
        data = []
        price = Decimal(str(start_price))
        base_date = datetime.now() - timedelta(days=days)

        for i in range(days):
            # 随机波动
            change = Decimal(str(random.uniform(-0.03, 0.03)))
            open_price = price
            close_price = price * (1 + change)
            high_price = max(open_price, close_price) * Decimal(str(1 + random.uniform(0, 0.02)))
            low_price = min(open_price, close_price) * Decimal(str(1 - random.uniform(0, 0.02)))
            volume = random.randint(1000000, 10000000)

            data.append({
                "symbol": symbol,
                "timestamp": base_date + timedelta(days=i),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
                "amount": close_price * volume,
            })

            price = close_price

        self._data[symbol] = data
        self.logger.info(f"生成 {symbol} 的随机数据: {len(data)} 条")


# ==============================================
# 智能数据源（自动切换）
# ==============================================

class SmartDataSource:
    """
    智能数据源管理器

    特性：
    - 支持多数据源自动切换
    - 根据数据类型和频率选择最优数据源
    - 自动降级：主数据源失败时切换到备用数据源
    - 缓存支持：减少重复请求

    使用示例：
        smart_source = SmartDataSource()
        await smart_source.initialize()

        # 获取历史数据（自动选择最优数据源）
        data = await smart_source.get_history(
            symbols=["000001.SZ"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        # 获取实时数据
        latest = await smart_source.get_latest(["000001.SZ", "600000.SH"])
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化智能数据源

        Args:
            config: 配置字典，可包含：
                - tushare_token: Tushare API Token
                - database_url: 数据库连接 URL
                - cache_enabled: 是否启用缓存（默认 True）
                - cache_ttl: 缓存过期时间（秒，默认 300）
        """
        self.config = config or {}
        self._adapters: List[DataSourceAdapter] = []
        self._connected_adapters: List[DataSourceAdapter] = []
        self._cache: Dict[str, Any] = {}
        self._cache_enabled = self.config.get("cache_enabled", True)
        self._cache_ttl = self.config.get("cache_ttl", 300)  # 5分钟
        self._logger = logging.getLogger(__name__)

    async def initialize(self) -> bool:
        """
        初始化所有数据源适配器

        按优先级顺序尝试连接，记录成功连接的适配器。

        Returns:
            是否至少有一个数据源可用
        """
        adapters_to_try = []

        # 1. 数据库适配器（最高优先级，本地数据最快）
        if self.config.get("database_url"):
            adapters_to_try.append(DatabaseAdapter({
                "database_url": self.config["database_url"]
            }))

        # 2. Tushare 适配器（专业数据源，需要 Token）
        adapters_to_try.append(TushareAdapter({
            "token": self.config.get("tushare_token")
        }))

        # 3. AkShare 适配器（免费数据源，保底）
        adapters_to_try.append(AkShareAdapter())

        # 尝试连接所有适配器
        for adapter in adapters_to_try:
            try:
                if await adapter.connect():
                    self._connected_adapters.append(adapter)
                    self._logger.info(f"数据源 {adapter.name} 已连接")
            except Exception as e:
                self._logger.warning(f"数据源 {adapter.name} 连接失败: {e}")

        # 按优先级排序（高优先级在前）
        self._connected_adapters.sort(key=lambda x: x.priority, reverse=True)

        if self._connected_adapters:
            self._logger.info(f"智能数据源初始化完成，可用数据源: {[a.name for a in self._connected_adapters]}")
            return True
        else:
            self._logger.error("没有可用的数据源")
            return False

    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        import hashlib
        key_parts = [prefix] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if not self._cache_enabled:
            return None

        cached = self._cache.get(key)
        if cached:
            import time
            if time.time() - cached["timestamp"] < self._cache_ttl:
                return cached["data"]
            else:
                del self._cache[key]

        return None

    def _set_cache(self, key: str, data: Any) -> None:
        """设置缓存"""
        if self._cache_enabled:
            import time
            self._cache[key] = {
                "data": data,
                "timestamp": time.time()
            }

    async def get_history(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        frequency: DataFrequency = DataFrequency.DAY
    ) -> List[Dict[str, Any]]:
        """
        获取历史数据

        自动选择最优数据源，失败时自动降级到备用数据源。

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率

        Returns:
            数据列表
        """
        # 检查缓存
        cache_key = self._get_cache_key(
            "history",
            symbols=",".join(symbols),
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            freq=frequency.value
        )
        cached = self._get_from_cache(cache_key)
        if cached:
            self._logger.debug(f"从缓存获取历史数据: {len(cached)} 条")
            return cached

        # 尝试各个数据源
        last_error = None
        for adapter in self._connected_adapters:
            # 检查适配器是否支持该数据类型和频率
            if frequency not in adapter.supported_frequencies:
                continue

            try:
                request = DataRequest(
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency
                )

                data = await adapter.fetch_history(request)

                if data:
                    self._logger.info(f"从 {adapter.name} 获取历史数据: {len(data)} 条")
                    self._set_cache(cache_key, data)
                    return data

            except Exception as e:
                self._logger.warning(f"从 {adapter.name} 获取数据失败: {e}")
                last_error = e
                continue

        self._logger.error(f"所有数据源均无法获取历史数据: {last_error}")
        return []

    async def get_latest(self, symbols: List[str]) -> Dict[str, Bar]:
        """
        获取最新行情

        优先使用支持实时数据的适配器。

        Args:
            symbols: 股票代码列表

        Returns:
            {symbol: Bar}
        """
        # 尝试各个数据源
        for adapter in self._connected_adapters:
            try:
                data = await adapter.fetch_latest(symbols)
                if data:
                    self._logger.debug(f"从 {adapter.name} 获取实时行情: {len(data)} 只")
                    return data
            except Exception as e:
                self._logger.warning(f"从 {adapter.name} 获取实时行情失败: {e}")
                continue

        self._logger.error("所有数据源均无法获取实时行情")
        return {}

    async def get_corporate_actions(
        self,
        symbol: str,
        start_date: date = None,
        end_date: date = None
    ) -> List[CorporateAction]:
        """
        获取公司行动（分红、送股等）

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            公司行动列表
        """
        for adapter in self._connected_adapters:
            if DataType.CORPORATE_ACTION not in adapter.supported_types:
                continue

            try:
                if hasattr(adapter, 'get_corporate_actions'):
                    actions = await adapter.get_corporate_actions(symbol, start_date, end_date)
                    if actions:
                        return actions
            except Exception as e:
                self._logger.warning(f"从 {adapter.name} 获取公司行动失败: {e}")
                continue

        return []

    def get_available_sources(self) -> List[str]:
        """获取当前可用的数据源列表"""
        return [adapter.name for adapter in self._connected_adapters]

    def get_best_source(self, data_type: DataType = DataType.STOCK_PRICE) -> Optional[str]:
        """
        获取指定数据类型的最优数据源

        Args:
            data_type: 数据类型

        Returns:
            数据源名称
        """
        for adapter in self._connected_adapters:
            if data_type in adapter.supported_types:
                return adapter.name
        return None

    async def close(self) -> None:
        """关闭所有数据源连接"""
        for adapter in self._connected_adapters:
            try:
                await adapter.disconnect()
            except Exception as e:
                self._logger.warning(f"关闭 {adapter.name} 失败: {e}")

        self._connected_adapters.clear()
        self._cache.clear()
        self._logger.info("智能数据源已关闭")
