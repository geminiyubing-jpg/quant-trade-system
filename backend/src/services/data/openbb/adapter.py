"""
OpenBB Platform 数据适配器

实现 OpenBB Platform 与 Quant-Trade System 数据引擎的集成。
"""

import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from ..engine import (
    DataSourceAdapter,
    DataType,
    DataFrequency,
    DataRequest,
    Bar,
    CorporateAction,
)
from .providers.equity import EquityProvider
from .providers.economy import EconomyProvider
from .providers.technical import TechnicalProvider
from .utils import detect_market
from .cache import get_cache, DataCache


class OpenBBAdapter(DataSourceAdapter):
    """
    OpenBB Platform 数据源适配器

    支持多种数据类型：
    - 股票数据（美股、国际市场）
    - 宏观经济数据（FRED、OECD、IMF）
    - 技术分析指标（RSI、MACD、布林带等）
    - 量化分析工具（CAPM、夏普比率等）

    使用方式：
        adapter = OpenBBAdapter(config={
            'fmp_api_key': 'your_key',
            'fred_api_key': 'your_key',
        })
        await adapter.connect()
        data = await adapter.fetch_history(DataRequest(...))
    """

    # 数据源元信息
    name = "openbb"
    description = "OpenBB Platform 多源数据"
    supported_types = [
        DataType.STOCK_PRICE,
        DataType.STOCK_INFO,
        DataType.INDEX,
        DataType.FUNDAMENTAL,
        DataType.MACRO_ECONOMIC,
        DataType.TECHNICAL_INDICATOR,
        DataType.QUANT_ANALYSIS,
    ]
    supported_frequencies = [
        DataFrequency.TICK,
        DataFrequency.MIN_1,
        DataFrequency.MIN_5,
        DataFrequency.MIN_15,
        DataFrequency.MIN_30,
        DataFrequency.HOUR_1,
        DataFrequency.HOUR_4,
        DataFrequency.DAY,
        DataFrequency.WEEK,
        DataFrequency.MONTH,
    ]
    is_realtime = False  # 可通过 Polygon 实现实时
    priority = 25  # 高于 AkShare(10)，低于 Database(30)

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化 OpenBB 适配器

        Args:
            config: 配置参数，包含：
                - fmp_api_key: FMP API Key
                - polygon_api_key: Polygon API Key
                - fred_api_key: FRED API Key
                - default_equity_provider: 默认股票数据提供商
                - default_economy_provider: 默认宏观经济数据提供商
        """
        super().__init__(config)

        # 初始化各 Provider
        self._equity_provider: Optional[EquityProvider] = None
        self._economy_provider: Optional[EconomyProvider] = None
        self._technical_provider: Optional[TechnicalProvider] = None

        # OpenBB 核心实例
        self._obb = None

        # yfinance 后备模式
        self._use_fallback = False
        self._yfinance = None

    async def connect(self) -> bool:
        """
        连接 OpenBB Platform

        Returns:
            是否连接成功
        """
        try:
            # 延迟导入 OpenBB（避免未安装时报错）
            from openbb import obb

            # 测试 OpenBB SDK 是否正常工作
            # 注意：OpenBB 4.7.x 存在版本兼容性问题，需要捕获 ImportError
            try:
                _ = obb.equity  # 测试访问 equity 模块
            except ImportError as e:
                if "OBBject_EquityInfo" in str(e):
                    raise RuntimeError(f"OpenBB SDK 版本兼容性问题: {e}")

            self._obb = obb

            # 配置 API Keys
            await self._configure_api_keys()

            # 初始化各 Provider
            self._equity_provider = EquityProvider(self._obb, self.config)
            self._economy_provider = EconomyProvider(self._obb, self.config)
            self._technical_provider = TechnicalProvider(self._obb, self.config)

            self._is_connected = True
            logger.info("OpenBB Platform 连接成功")
            return True

        except ImportError as e:
            logger.warning(f"OpenBB 未安装或版本不兼容: {e}")
            logger.info("尝试使用 yfinance 后备模式...")
            return await self._init_yfinance_fallback()

        except RuntimeError as e:
            if "版本兼容性" in str(e):
                logger.warning(str(e))
                logger.info("尝试使用 yfinance 后备模式...")
                return await self._init_yfinance_fallback()
            raise

        except Exception as e:
            logger.error(f"OpenBB 连接失败: {e}")
            self._is_connected = False
            return False

    async def _init_yfinance_fallback(self) -> bool:
        """初始化 yfinance 后备模式"""
        try:
            import yfinance as yf
            self._yfinance = yf
            self._use_fallback = True
            self._is_connected = True
            logger.info("yfinance 后备模式初始化成功")
            return True
        except ImportError:
            logger.error("yfinance 未安装，请运行: pip install yfinance")
            self._is_connected = False
            return False

    async def _configure_api_keys(self) -> None:
        """配置 OpenBB API Keys"""
        try:
            # 如果有 Hub PAT，使用 Hub 登录
            hub_pat = self.config.get('hub_pat')
            if hub_pat:
                self._obb.account.login(pat=hub_pat)
                logger.info("OpenBB Hub 登录成功")
                return

            # 否则配置各个 Provider 的 API Key
            api_keys = {
                'fmp_api_key': self.config.get('fmp_api_key'),
                'polygon_api_key': self.config.get('polygon_api_key'),
                'fred_api_key': self.config.get('fred_api_key'),
                'benzinga_api_key': self.config.get('benzinga_api_key'),
                'intrinio_api_key': self.config.get('intrinio_api_key'),
                'tiingo_api_key': self.config.get('tiingo_api_key'),
            }

            for key_name, key_value in api_keys.items():
                if key_value:
                    provider = key_name.replace('_api_key', '')
                    self._obb.user.credentials.__setattr__(provider, key_value)
                    logger.debug(f"配置 OpenBB Provider: {provider}")

        except Exception as e:
            logger.warning(f"配置 OpenBB API Keys 失败: {e}")

    async def disconnect(self) -> None:
        """断开 OpenBB 连接"""
        try:
            if self._obb:
                # 登出 OpenBB Hub
                if self._obb.account.is_logged_in():
                    self._obb.account.logout()
                self._obb = None
        except Exception:
            pass
        finally:
            self._is_connected = False
            logger.info("OpenBB Platform 已断开连接")

    async def fetch_history(self, request: DataRequest) -> List[Dict[str, Any]]:
        """
        获取历史数据

        根据数据类型路由到对应的 Provider

        Args:
            request: 数据请求

        Returns:
            数据列表
        """
        if not self._is_connected:
            raise RuntimeError("OpenBB 未连接")

        data_type = request.data_type

        # 根据数据类型选择 Provider
        if data_type in [DataType.STOCK_PRICE, DataType.STOCK_INFO, DataType.INDEX]:
            return await self._fetch_equity_history(request)
        elif data_type == DataType.FUNDAMENTAL:
            return await self._fetch_fundamental(request)
        elif data_type == DataType.MACRO_ECONOMIC:
            return await self._fetch_macro(request)
        elif data_type == DataType.TECHNICAL_INDICATOR:
            return await self._fetch_technical(request)
        else:
            raise NotImplementedError(f"OpenBB 不支持数据类型: {data_type}")

    async def _fetch_equity_history(self, request: DataRequest) -> List[Dict[str, Any]]:
        """获取股票历史数据"""
        # 使用 yfinance 后备模式
        if self._use_fallback:
            return await self._fetch_equity_history_yfinance(request)

        if not self._equity_provider:
            raise RuntimeError("Equity Provider 未初始化")

        results = []
        for symbol in request.symbols:
            # 检查市场，A股路由到 AkShare
            market = detect_market(symbol)
            if market == 'cn':
                logger.debug(f"跳过 A股 {symbol}，请使用 AkShare 获取")
                continue

            data = await self._equity_provider.get_historical_price(
                symbol=symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                frequency=request.frequency,
            )
            results.extend(data)

        return results

    async def _fetch_equity_history_yfinance(self, request: DataRequest) -> List[Dict[str, Any]]:
        """使用 yfinance 获取股票历史数据（后备模式）"""
        results = []
        for symbol in request.symbols:
            # 检查市场，A股路由到 AkShare
            market = detect_market(symbol)
            if market == 'cn':
                logger.debug(f"跳过 A股 {symbol}，请使用 AkShare 获取")
                continue

            try:
                ticker = self._yfinance.Ticker(symbol)
                df = ticker.history(
                    start=request.start_date.isoformat() if request.start_date else None,
                    end=request.end_date.isoformat() if request.end_date else None,
                )

                if df.empty:
                    continue

                for idx, row in df.iterrows():
                    results.append({
                        "symbol": symbol,
                        "timestamp": idx.isoformat(),
                        "open": float(row.get("Open", 0)),
                        "high": float(row.get("High", 0)),
                        "low": float(row.get("Low", 0)),
                        "close": float(row.get("Close", 0)),
                        "volume": int(row.get("Volume", 0)),
                        "provider": "yfinance",
                    })

                logger.debug(f"yfinance 获取 {symbol} 历史数据: {len(df)} 条")

            except Exception as e:
                logger.warning(f"yfinance 获取 {symbol} 数据失败: {e}")

        return results

    async def _fetch_fundamental(self, request: DataRequest) -> List[Dict[str, Any]]:
        """获取基本面数据"""
        if not self._equity_provider:
            raise RuntimeError("Equity Provider 未初始化")

        results = []
        for symbol in request.symbols:
            market = detect_market(symbol)
            if market == 'cn':
                continue

            data = await self._equity_provider.get_fundamentals(symbol)
            results.append(data)

        return results

    async def _fetch_macro(self, request: DataRequest) -> List[Dict[str, Any]]:
        """获取宏观经济数据"""
        if not self._economy_provider:
            raise RuntimeError("Economy Provider 未初始化")

        # 从 symbols 中解析指标名称
        indicator = request.symbols[0] if request.symbols else 'GDP'
        data = await self._economy_provider.get_indicator(
            indicator=indicator,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return data

    async def _fetch_technical(self, request: DataRequest) -> List[Dict[str, Any]]:
        """获取技术指标数据"""
        if not self._technical_provider:
            raise RuntimeError("Technical Provider 未初始化")

        results = []
        for symbol in request.symbols:
            market = detect_market(symbol)
            if market == 'cn':
                continue

            data = await self._technical_provider.get_indicators(
                symbol=symbol,
                indicators=request.fields or ['rsi', 'macd'],
            )
            results.extend(data)

        return results

    async def fetch_latest(self, symbols: List[str]) -> Dict[str, Bar]:
        """
        获取最新行情

        Args:
            symbols: 股票代码列表

        Returns:
            {symbol: Bar}
        """
        if not self._is_connected:
            raise RuntimeError("OpenBB 未连接")

        # 使用 yfinance 后备模式
        if self._use_fallback:
            return await self._fetch_latest_yfinance(symbols)

        if not self._equity_provider:
            raise RuntimeError("Equity Provider 未初始化")

        results = {}
        for symbol in symbols:
            market = detect_market(symbol)
            if market == 'cn':
                continue

            try:
                quote = await self._equity_provider.get_quote(symbol)
                if quote:
                    bar = Bar(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        open=Decimal(str(quote.get('open', 0))),
                        high=Decimal(str(quote.get('high', 0))),
                        low=Decimal(str(quote.get('low', 0))),
                        close=Decimal(str(quote.get('close', 0))),
                        volume=quote.get('volume', 0),
                    )
                    results[symbol] = bar
            except Exception as e:
                logger.warning(f"获取 {symbol} 行情失败: {e}")

        return results

    async def _fetch_latest_yfinance(self, symbols: List[str]) -> Dict[str, Bar]:
        """使用 yfinance 获取最新行情（后备模式）"""
        results = {}
        for symbol in symbols:
            market = detect_market(symbol)
            if market == 'cn':
                continue

            try:
                ticker = self._yfinance.Ticker(symbol)
                info = ticker.info

                if info:
                    bar = Bar(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        open=Decimal(str(info.get('open', 0))),
                        high=Decimal(str(info.get('dayHigh', 0))),
                        low=Decimal(str(info.get('dayLow', 0))),
                        close=Decimal(str(info.get('currentPrice', info.get('regularMarketPrice', 0)))),
                        volume=info.get('volume', 0),
                    )
                    results[symbol] = bar
            except Exception as e:
                logger.warning(f"yfinance 获取 {symbol} 行情失败: {e}")

        return results

    # ==============================================
    # 高级 API（直接访问各 Provider）
    # ==============================================

    @property
    def equity(self) -> EquityProvider:
        """获取 Equity Provider"""
        if self._use_fallback:
            raise RuntimeError("yfinance 后备模式不支持此操作")
        if not self._equity_provider:
            raise RuntimeError("Equity Provider 未初始化")
        return self._equity_provider

    @property
    def economy(self) -> EconomyProvider:
        """获取 Economy Provider"""
        if self._use_fallback:
            raise RuntimeError("yfinance 后备模式不支持此操作")
        if not self._economy_provider:
            raise RuntimeError("Economy Provider 未初始化")
        return self._economy_provider

    @property
    def technical(self) -> TechnicalProvider:
        """获取 Technical Provider"""
        if self._use_fallback:
            raise RuntimeError("yfinance 后备模式不支持此操作")
        if not self._technical_provider:
            raise RuntimeError("Technical Provider 未初始化")
        return self._technical_provider

    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        cache = get_cache()
        cache_stats = cache.get_stats()

        # 在 yfinance 后备模式下，技术分析也是可用的
        technical_available = self._technical_provider is not None or self._use_fallback
        # 宏观经济需要 FRED API Key
        economy_available = self._economy_provider is not None or (
            self._use_fallback and self.config.get('fred_api_key')
        )

        return {
            "name": self.name,
            "description": self.description,
            "is_connected": self._is_connected,
            "use_fallback": self._use_fallback,
            "fallback_provider": "yfinance" if self._use_fallback else None,
            "supported_types": [t.value for t in self.supported_types],
            "providers": {
                "equity": self._equity_provider is not None or self._use_fallback,
                "economy": economy_available,
                "technical": technical_available,
            },
            "cache": cache_stats,
        }

    # ==============================================
    # 直接访问方法（支持后备模式）
    # ==============================================

    async def get_quote(self, symbol: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        获取股票实时报价（支持后备模式）

        Args:
            symbol: 股票代码
            provider: 数据提供商（后备模式下忽略）

        Returns:
            报价数据
        """
        if not self._is_connected:
            raise RuntimeError("OpenBB 未连接")

        if self._use_fallback:
            return await self._get_quote_yfinance(symbol)

        if not self._equity_provider:
            raise RuntimeError("Equity Provider 未初始化")

        return await self._equity_provider.get_quote(symbol, provider)

    async def _get_quote_yfinance(self, symbol: str) -> Dict[str, Any]:
        """使用 yfinance 获取报价（后备模式，带缓存）"""
        cache = get_cache()
        cache_key = f"openbb:quote:{symbol}"

        # 尝试从缓存获取
        cached = await cache.get(cache_key)
        if cached:
            logger.debug(f"报价缓存命中: {symbol}")
            return cached

        try:
            ticker = self._yfinance.Ticker(symbol)
            info = ticker.info

            result = {
                "symbol": symbol,
                "price": float(info.get('currentPrice', info.get('regularMarketPrice', 0))),
                "open": float(info.get('open', 0)),
                "high": float(info.get('dayHigh', 0)),
                "low": float(info.get('dayLow', 0)),
                "close": float(info.get('previousClose', 0)),
                "volume": int(info.get('volume', 0)),
                "change": float(info.get('regularMarketChange', 0)),
                "change_percent": float(info.get('regularMarketChangePercent', 0)),
                "previous_close": float(info.get('previousClose', 0)),
                "provider": "yfinance",
            }

            # 缓存结果（60秒）
            if result.get("price"):
                await cache.set(cache_key, result, ttl=60)

            return result
        except Exception as e:
            logger.warning(f"yfinance 获取 {symbol} 报价失败: {e}")
            return {}

    async def get_historical_price(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        frequency: DataFrequency = DataFrequency.DAY,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取历史价格（支持后备模式）

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            provider: 数据提供商（后备模式下忽略）

        Returns:
            历史价格数据列表
        """
        if not self._is_connected:
            raise RuntimeError("OpenBB 未连接")

        if self._use_fallback:
            return await self._get_historical_yfinance(symbol, start_date, end_date)

        if not self._equity_provider:
            raise RuntimeError("Equity Provider 未初始化")

        return await self._equity_provider.get_historical_price(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            provider=provider,
        )

    async def _get_historical_yfinance(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """使用 yfinance 获取历史价格（后备模式）"""
        try:
            ticker = self._yfinance.Ticker(symbol)
            df = ticker.history(
                start=start_date.isoformat() if start_date else None,
                end=end_date.isoformat() if end_date else None,
            )

            if df.empty:
                return []

            results = []
            for idx, row in df.iterrows():
                results.append({
                    "symbol": symbol,
                    "timestamp": idx.isoformat(),
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(row.get("Volume", 0)),
                    "provider": "yfinance",
                })

            return results
        except Exception as e:
            logger.warning(f"yfinance 获取 {symbol} 历史数据失败: {e}")
            return []

    async def get_fundamentals(
        self,
        symbol: str,
        statement_type: str = "balance",
        period: str = "annual",
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取基本面数据（后备模式有限支持）

        Args:
            symbol: 股票代码
            statement_type: 报表类型
            period: 周期
            provider: 数据提供商

        Returns:
            基本面数据
        """
        if not self._is_connected:
            raise RuntimeError("OpenBB 未连接")

        if self._use_fallback:
            return await self._get_fundamentals_yfinance(symbol)

        if not self._equity_provider:
            raise RuntimeError("Equity Provider 未初始化")

        return await self._equity_provider.get_fundamentals(symbol, statement_type, period, provider)

    async def _get_fundamentals_yfinance(self, symbol: str) -> Dict[str, Any]:
        """使用 yfinance 获取基本面数据（后备模式，有限支持）"""
        try:
            ticker = self._yfinance.Ticker(symbol)
            info = ticker.info

            # yfinance 只提供有限的基本面数据
            return {
                "symbol": symbol,
                "statement_type": "summary",
                "period": "current",
                "data": [{
                    "market_cap": info.get('marketCap'),
                    "pe_ratio": info.get('trailingPE'),
                    "pb_ratio": info.get('priceToBook'),
                    "dividend_yield": info.get('dividendYield'),
                    "eps": info.get('trailingEps'),
                    "revenue": info.get('totalRevenue'),
                    "profit_margin": info.get('profitMargins'),
                }],
                "provider": "yfinance",
            }
        except Exception as e:
            logger.warning(f"yfinance 获取 {symbol} 基本面数据失败: {e}")
            return {"symbol": symbol, "data": [], "error": str(e)}

    # ==============================================
    # 技术分析（后备模式支持）
    # ==============================================

    async def get_technical_indicators(
        self,
        symbol: str,
        indicators: List[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取技术指标（支持后备模式）

        Args:
            symbol: 股票代码
            indicators: 指标列表
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供商

        Returns:
            技术指标数据
        """
        if not self._is_connected:
            raise RuntimeError("OpenBB 未连接")

        indicators = indicators or ["rsi", "macd"]

        if self._use_fallback:
            return await self._get_technical_yfinance(symbol, indicators, start_date, end_date)

        if not self._technical_provider:
            raise RuntimeError("Technical Provider 未初始化")

        data = await self._technical_provider.get_indicators(
            symbol=symbol,
            indicators=indicators,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )

        return {
            "symbol": symbol,
            "indicators": indicators,
            "data": data,
            "provider": provider or "yfinance",
            "count": len(data),
        }

    async def _get_technical_yfinance(
        self,
        symbol: str,
        indicators: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """使用 yfinance 获取技术指标（后备模式，手动计算）"""
        import numpy as np
        import pandas as pd

        try:
            # 获取历史价格数据
            ticker = self._yfinance.Ticker(symbol)
            df = ticker.history(
                start=start_date.isoformat() if start_date else None,
                end=end_date.isoformat() if end_date else None,
            )

            if df.empty:
                return {"symbol": symbol, "indicators": indicators, "data": [], "count": 0}

            results = []
            close = df['Close']

            for indicator in indicators:
                indicator = indicator.lower()

                if indicator == "rsi":
                    # 计算 RSI
                    rsi = self._calculate_rsi(close, length=14)
                    for idx, value in rsi.items():
                        if not pd.isna(value):
                            results.append({
                                "symbol": symbol,
                                "indicator": "rsi",
                                "timestamp": idx.isoformat(),
                                "value": float(value),
                            })

                elif indicator == "macd":
                    # 计算 MACD
                    macd_line, signal_line, histogram = self._calculate_macd(close)
                    for idx in macd_line.index:
                        if not pd.isna(macd_line[idx]):
                            results.append({
                                "symbol": symbol,
                                "indicator": "macd",
                                "timestamp": idx.isoformat(),
                                "macd": float(macd_line[idx]) if not pd.isna(macd_line[idx]) else None,
                                "signal": float(signal_line[idx]) if not pd.isna(signal_line[idx]) else None,
                                "histogram": float(histogram[idx]) if not pd.isna(histogram[idx]) else None,
                            })

                elif indicator == "sma":
                    # 计算 SMA
                    sma = close.rolling(window=20).mean()
                    for idx, value in sma.items():
                        if not pd.isna(value):
                            results.append({
                                "symbol": symbol,
                                "indicator": "sma",
                                "timestamp": idx.isoformat(),
                                "value": float(value),
                            })

                elif indicator == "ema":
                    # 计算 EMA
                    ema = close.ewm(span=20, adjust=False).mean()
                    for idx, value in ema.items():
                        if not pd.isna(value):
                            results.append({
                                "symbol": symbol,
                                "indicator": "ema",
                                "timestamp": idx.isoformat(),
                                "value": float(value),
                            })

                elif indicator == "bbands":
                    # 计算布林带
                    sma = close.rolling(window=20).mean()
                    std = close.rolling(window=20).std()
                    upper = sma + (std * 2)
                    lower = sma - (std * 2)
                    for idx in sma.index:
                        if not pd.isna(sma[idx]):
                            results.append({
                                "symbol": symbol,
                                "indicator": "bbands",
                                "timestamp": idx.isoformat(),
                                "upper": float(upper[idx]),
                                "middle": float(sma[idx]),
                                "lower": float(lower[idx]),
                            })

            return {
                "symbol": symbol,
                "indicators": indicators,
                "data": results,
                "provider": "yfinance",
                "count": len(results),
            }

        except Exception as e:
            logger.warning(f"yfinance 获取 {symbol} 技术指标失败: {e}")
            return {"symbol": symbol, "indicators": indicators, "data": [], "error": str(e), "count": 0}

    def _calculate_rsi(self, prices: pd.Series, length: int = 14) -> pd.Series:
        """计算 RSI 指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> tuple:
        """计算 MACD 指标"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    # ==============================================
    # 宏观经济（后备模式支持）
    # ==============================================

    async def get_macro_indicator(
        self,
        indicator: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取宏观经济指标（支持后备模式）

        Args:
            indicator: 指标代码
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供商

        Returns:
            宏观经济数据
        """
        if not self._is_connected:
            raise RuntimeError("OpenBB 未连接")

        if self._use_fallback:
            return await self._get_macro_fred(indicator, start_date, end_date)

        if not self._economy_provider:
            raise RuntimeError("Economy Provider 未初始化")

        data = await self._economy_provider.get_indicator(
            indicator=indicator,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )

        return {
            "indicator": indicator,
            "data": data,
            "provider": provider or "fred",
            "count": len(data),
        }

    async def _get_macro_fred(
        self,
        indicator: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """使用 FRED API 获取宏观经济数据（后备模式）"""
        import aiohttp

        fred_api_key = self.config.get('fred_api_key')
        if not fred_api_key:
            return {
                "indicator": indicator,
                "data": [],
                "error": "FRED API Key 未配置。请在 .env 文件中设置 OPENBB_FRED_API_KEY",
                "provider": "fred",
                "count": 0,
            }

        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": indicator,
                "api_key": fred_api_key,
                "file_type": "json",
                "observation_start": start_date.isoformat() if start_date else "2000-01-01",
                "observation_end": end_date.isoformat() if end_date else None,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "indicator": indicator,
                            "data": [],
                            "error": f"FRED API 错误: {error_text}",
                            "provider": "fred",
                            "count": 0,
                        }

                    data = await response.json()
                    observations = data.get("observations", [])

                    results = []
                    for obs in observations:
                        if obs.get("value") != ".":  # 跳过缺失值
                            results.append({
                                "date": obs["date"],
                                "value": float(obs["value"]),
                            })

                    return {
                        "indicator": indicator,
                        "data": results,
                        "provider": "fred",
                        "count": len(results),
                    }

        except Exception as e:
            logger.warning(f"FRED API 获取 {indicator} 失败: {e}")
            return {
                "indicator": indicator,
                "data": [],
                "error": str(e),
                "provider": "fred",
                "count": 0,
            }
