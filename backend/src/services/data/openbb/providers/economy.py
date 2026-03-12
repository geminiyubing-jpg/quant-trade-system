"""
Economy Provider - 宏观经济数据提供者

提供 FRED、OECD、IMF 等宏观经济数据。
"""

import asyncio
from datetime import date
from typing import Any, Dict, List, Optional

from loguru import logger


class EconomyProvider:
    """
    宏观经济数据提供者

    支持的数据源：
    - FRED (Federal Reserve Economic Data)
    - OECD (Organization for Economic Co-operation and Development)
    - IMF (International Monetary Fund)
    - Trading Economics

    支持的指标：
    - GDP (国内生产总值)
    - CPI (消费者物价指数)
    - Unemployment Rate (失业率)
    - Interest Rates (利率)
    - Treasury Yields (国债收益率)
    - etc.
    """

    # 常用经济指标映射
    INDICATOR_MAP = {
        # FRED 指标
        "gdp": "GDP",
        "real_gdp": "GDPC1",
        "gdp_growth": "A191RL1Q225SBEA",
        "cpi": "CPIAUCSL",
        "core_cpi": "CPILFESL",
        "inflation": "FPCPITOTLZGUSA",
        "unemployment": "UNRATE",
        "nonfarm_payroll": "PAYEMS",
        "fed_funds_rate": "FEDFUNDS",
        "treasury_10y": "GS10",
        "treasury_2y": "GS2",
        "treasury_3m": "GS3M",
        "consumer_confidence": "UMCSENT",
        "industrial_production": "INDPRO",
        "retail_sales": "RSXFS",
        "housing_starts": "HOUST",
        "pmi": "MANEMP",
    }

    def __init__(self, obb, config: Dict[str, Any] = None):
        """
        初始化 Economy Provider

        Args:
            obb: OpenBB 实例
            config: 配置参数
        """
        self._obb = obb
        self._config = config or {}
        self._default_provider = config.get('default_economy_provider', 'fred')

    async def get_indicator(
        self,
        indicator: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        country: str = "united_states",
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取宏观经济指标数据

        Args:
            indicator: 指标名称或代码
            start_date: 开始日期
            end_date: 结束日期
            country: 国家
            provider: 数据提供商

        Returns:
            经济指标数据列表
        """
        provider = provider or self._default_provider

        # 转换指标名称为代码
        indicator_code = self.INDICATOR_MAP.get(indicator.lower(), indicator)

        try:
            result = await asyncio.to_thread(
                self._obb.economy.indicator,
                symbol=indicator_code,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                provider=provider,
            )

            df = result.to_df()
            if df.empty:
                return []

            results = []
            for idx, row in df.iterrows():
                results.append({
                    "indicator": indicator,
                    "indicator_code": indicator_code,
                    "date": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    "value": float(row.get("value", 0)),
                    "country": country,
                    "provider": provider,
                })

            logger.debug(f"获取经济指标 {indicator}: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"获取经济指标 {indicator} 失败: {e}")
            return []

    async def get_treasury_yields(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        maturities: List[str] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取国债收益率

        Args:
            start_date: 开始日期
            end_date: 结束日期
            maturities: 期限列表 (如 ["3m", "2y", "10y"])
            provider: 数据提供商

        Returns:
            {期限: 收益率数据列表}
        """
        provider = provider or self._default_provider
        maturities = maturities or ["3m", "2y", "10y", "30y"]

        results = {}
        maturity_map = {
            "3m": "GS3M",
            "6m": "GS6M",
            "1y": "GS1",
            "2y": "GS2",
            "3y": "GS3",
            "5y": "GS5",
            "7y": "GS7",
            "10y": "GS10",
            "20y": "GS20",
            "30y": "GS30",
        }

        for maturity in maturities:
            code = maturity_map.get(maturity)
            if not code:
                continue

            data = await self.get_indicator(
                indicator=code,
                start_date=start_date,
                end_date=end_date,
                provider=provider,
            )
            results[maturity] = data

        return results

    async def get_gdp(
        self,
        country: str = "united_states",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        real: bool = True,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取 GDP 数据

        Args:
            country: 国家
            start_date: 开始日期
            end_date: 结束日期
            real: 是否为实际 GDP
            provider: 数据提供商

        Returns:
            GDP 数据列表
        """
        indicator = "real_gdp" if real else "gdp"
        return await self.get_indicator(
            indicator=indicator,
            start_date=start_date,
            end_date=end_date,
            country=country,
            provider=provider,
        )

    async def get_inflation(
        self,
        country: str = "united_states",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        indicator: str = "cpi",
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取通胀数据

        Args:
            country: 国家
            start_date: 开始日期
            end_date: 结束日期
            indicator: 指标类型 (cpi, core_cpi, inflation)
            provider: 数据提供商

        Returns:
            通胀数据列表
        """
        return await self.get_indicator(
            indicator=indicator,
            start_date=start_date,
            end_date=end_date,
            country=country,
            provider=provider,
        )

    async def get_employment(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取就业数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供商

        Returns:
            {指标类型: 数据列表}
        """
        provider = provider or self._default_provider

        results = {}
        indicators = ["unemployment", "nonfarm_payroll"]

        for indicator in indicators:
            data = await self.get_indicator(
                indicator=indicator,
                start_date=start_date,
                end_date=end_date,
                provider=provider,
            )
            results[indicator] = data

        return results

    async def get_interest_rates(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取利率数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供商

        Returns:
            {利率类型: 数据列表}
        """
        provider = provider or self._default_provider

        results = {}
        indicators = ["fed_funds_rate", "treasury_10y", "treasury_2y"]

        for indicator in indicators:
            data = await self.get_indicator(
                indicator=indicator,
                start_date=start_date,
                end_date=end_date,
                provider=provider,
            )
            results[indicator] = data

        return results

    async def get_economic_calendar(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        country: str = "united_states",
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取经济日历

        Args:
            start_date: 开始日期
            end_date: 结束日期
            country: 国家
            provider: 数据提供商

        Returns:
            经济事件列表
        """
        provider = provider or 'tradingeconomics'

        try:
            result = await asyncio.to_thread(
                self._obb.economy.calendar,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                country=country,
                provider=provider,
            )

            df = result.to_df()
            if df.empty:
                return []

            return df.to_dict(orient='records')

        except Exception as e:
            logger.error(f"获取经济日历失败: {e}")
            return []

    def get_available_indicators(self) -> Dict[str, str]:
        """
        获取可用的经济指标列表

        Returns:
            {指标名称: 指标代码}
        """
        return self.INDICATOR_MAP.copy()
