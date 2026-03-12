"""
Equity Provider - 股票数据提供者

提供股票行情、基本面、估值、分析师评级等数据。
"""

import asyncio
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from ...engine import DataFrequency


class EquityProvider:
    """
    股票数据提供者

    支持的功能：
    - 历史行情数据
    - 实时报价
    - 基本面数据（资产负债表、利润表、现金流量表）
    - 估值指标（P/E、P/B、EV/EBITDA）
    - 分析师评级和目标价
    - 公司信息

    数据提供商：
    - yfinance (免费)
    - fmp (Financial Modeling Prep)
    - polygon
    - intrinio
    """

    def __init__(self, obb, config: Dict[str, Any] = None):
        """
        初始化 Equity Provider

        Args:
            obb: OpenBB 实例
            config: 配置参数
        """
        self._obb = obb
        self._config = config or {}
        self._default_provider = config.get('default_equity_provider', 'yfinance')

    async def get_historical_price(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        frequency: DataFrequency = DataFrequency.DAY,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取历史价格数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            provider: 数据提供商

        Returns:
            历史价格数据列表
        """
        provider = provider or self._default_provider

        try:
            # 转换频率格式
            interval_map = {
                DataFrequency.MIN_1: "1m",
                DataFrequency.MIN_5: "5m",
                DataFrequency.MIN_15: "15m",
                DataFrequency.MIN_30: "30m",
                DataFrequency.HOUR_1: "1h",
                DataFrequency.DAY: "1d",
                DataFrequency.WEEK: "1w",
                DataFrequency.MONTH: "1M",
            }
            interval = interval_map.get(frequency, "1d")

            # 调用 OpenBB API
            result = await asyncio.to_thread(
                self._obb.equity.price.historical,
                symbol=symbol,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                interval=interval,
                provider=provider,
            )

            # 转换为标准格式
            df = result.to_df()
            if df.empty:
                return []

            results = []
            for idx, row in df.iterrows():
                results.append({
                    "symbol": symbol,
                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": int(row.get("volume", 0)),
                    "adj_close": float(row.get("adj_close", row.get("close", 0))),
                    "provider": provider,
                })

            logger.debug(f"获取 {symbol} 历史数据: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"获取 {symbol} 历史数据失败: {e}")
            return []

    async def get_quote(
        self,
        symbol: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取实时报价

        Args:
            symbol: 股票代码
            provider: 数据提供商

        Returns:
            报价数据
        """
        provider = provider or self._default_provider

        try:
            result = await asyncio.to_thread(
                self._obb.equity.price.quote,
                symbol=symbol,
                provider=provider,
            )

            df = result.to_df()
            if df.empty:
                return {}

            row = df.iloc[0]
            return {
                "symbol": symbol,
                "price": float(row.get("price", 0)),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": int(row.get("volume", 0)),
                "change": float(row.get("change", 0)),
                "change_percent": float(row.get("change_percent", 0)),
                "previous_close": float(row.get("previous_close", 0)),
                "provider": provider,
            }

        except Exception as e:
            logger.error(f"获取 {symbol} 实时报价失败: {e}")
            return {}

    async def get_fundamentals(
        self,
        symbol: str,
        statement_type: str = "balance",
        period: str = "annual",
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取基本面数据

        Args:
            symbol: 股票代码
            statement_type: 报表类型 (balance, income, cash)
            period: 周期 (annual, quarterly)
            provider: 数据提供商

        Returns:
            基本面数据
        """
        provider = provider or 'fmp'  # 基本面数据推荐使用 FMP

        try:
            # 根据报表类型选择对应的 OpenBB 接口
            if statement_type == "balance":
                result = await asyncio.to_thread(
                    self._obb.equity.fundamental.balance,
                    symbol=symbol,
                    period=period,
                    provider=provider,
                )
            elif statement_type == "income":
                result = await asyncio.to_thread(
                    self._obb.equity.fundamental.income,
                    symbol=symbol,
                    period=period,
                    provider=provider,
                )
            elif statement_type == "cash":
                result = await asyncio.to_thread(
                    self._obb.equity.fundamental.cash,
                    symbol=symbol,
                    period=period,
                    provider=provider,
                )
            else:
                raise ValueError(f"不支持的报表类型: {statement_type}")

            df = result.to_df()
            if df.empty:
                return {"symbol": symbol, "data": []}

            return {
                "symbol": symbol,
                "statement_type": statement_type,
                "period": period,
                "data": df.to_dict(orient='records'),
                "provider": provider,
            }

        except Exception as e:
            logger.error(f"获取 {symbol} 基本面数据失败: {e}")
            return {"symbol": symbol, "data": [], "error": str(e)}

    async def get_valuation(
        self,
        symbol: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取估值指标

        Args:
            symbol: 股票代码
            provider: 数据提供商

        Returns:
            估值数据
        """
        provider = provider or 'fmp'

        try:
            # 获取估值指标
            result = await asyncio.to_thread(
                self._obb.equity.fundamental.multiples,
                symbol=symbol,
                provider=provider,
            )

            df = result.to_df()
            if df.empty:
                return {"symbol": symbol, "data": {}}

            row = df.iloc[-1]  # 获取最新数据
            return {
                "symbol": symbol,
                "pe_ratio": float(row.get("pe_ratio", 0)),
                "pb_ratio": float(row.get("pb_ratio", 0)),
                "ps_ratio": float(row.get("ps_ratio", 0)),
                "ev_ebitda": float(row.get("ev_ebitda", 0)),
                "price_to_sales": float(row.get("price_to_sales", 0)),
                "price_to_book": float(row.get("price_to_book", 0)),
                "price_to_cashflow": float(row.get("price_to_cashflow", 0)),
                "provider": provider,
            }

        except Exception as e:
            logger.error(f"获取 {symbol} 估值数据失败: {e}")
            return {"symbol": symbol, "error": str(e)}

    async def get_analyst_ratings(
        self,
        symbol: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取分析师评级

        Args:
            symbol: 股票代码
            provider: 数据提供商

        Returns:
            分析师评级数据
        """
        provider = provider or 'fmp'

        try:
            result = await asyncio.to_thread(
                self._obb.equity.estimates.ratings,
                symbol=symbol,
                provider=provider,
            )

            df = result.to_df()
            if df.empty:
                return {"symbol": symbol, "ratings": []}

            return {
                "symbol": symbol,
                "ratings": df.to_dict(orient='records'),
                "provider": provider,
            }

        except Exception as e:
            logger.error(f"获取 {symbol} 分析师评级失败: {e}")
            return {"symbol": symbol, "ratings": [], "error": str(e)}

    async def get_company_info(
        self,
        symbol: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取公司信息

        Args:
            symbol: 股票代码
            provider: 数据提供商

        Returns:
            公司信息
        """
        provider = provider or self._default_provider

        try:
            result = await asyncio.to_thread(
                self._obb.equity.profile,
                symbol=symbol,
                provider=provider,
            )

            df = result.to_df()
            if df.empty:
                return {"symbol": symbol}

            row = df.iloc[0]
            return {
                "symbol": symbol,
                "name": row.get("name", ""),
                "sector": row.get("sector", ""),
                "industry": row.get("industry", ""),
                "country": row.get("country", ""),
                "exchange": row.get("exchange", ""),
                "market_cap": float(row.get("market_cap", 0)),
                "employees": int(row.get("employees", 0)),
                "description": row.get("description", ""),
                "website": row.get("website", ""),
                "provider": provider,
            }

        except Exception as e:
            logger.error(f"获取 {symbol} 公司信息失败: {e}")
            return {"symbol": symbol, "error": str(e)}

    async def search(
        self,
        query: str,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索股票

        Args:
            query: 搜索关键词
            provider: 数据提供商

        Returns:
            搜索结果列表
        """
        provider = provider or self._default_provider

        try:
            result = await asyncio.to_thread(
                self._obb.equity.search,
                query=query,
                provider=provider,
            )

            df = result.to_df()
            if df.empty:
                return []

            return df.to_dict(orient='records')

        except Exception as e:
            logger.error(f"搜索股票失败: {e}")
            return []
