"""
Technical Provider - 技术分析指标提供者

提供 RSI、MACD、布林带等技术分析指标。
"""

import asyncio
from datetime import date
from typing import Any, Dict, List, Optional, Union

from loguru import logger


class TechnicalProvider:
    """
    技术分析指标提供者

    支持的指标：
    - RSI (相对强弱指数)
    - MACD (异同移动平均线)
    - Bollinger Bands (布林带)
    - SMA/EMA (简单/指数移动平均)
    - ATR (平均真实波幅)
    - ADX (平均趋向指数)
    - Stochastic (随机指标)
    - VWAP (成交量加权平均价)
    - etc.
    """

    # 支持的技术指标列表
    SUPPORTED_INDICATORS = [
        "sma",      # 简单移动平均
        "ema",      # 指数移动平均
        "rsi",      # 相对强弱指数
        "macd",     # 异同移动平均线
        "bbands",   # 布林带
        "atr",      # 平均真实波幅
        "adx",      # 平均趋向指数
        "cci",      # 顺势指标
        "stoch",    # 随机指标
        "williams", # 威廉指标
        "obv",      # 能量潮
        "vwap",     # 成交量加权平均价
        "roc",      # 变动率
        "mom",      # 动量
    ]

    def __init__(self, obb, config: Dict[str, Any] = None):
        """
        初始化 Technical Provider

        Args:
            obb: OpenBB 实例
            config: 配置参数
        """
        self._obb = obb
        self._config = config or {}

    async def get_indicators(
        self,
        symbol: str,
        indicators: List[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取技术指标数据

        Args:
            symbol: 股票代码
            indicators: 指标列表
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供商

        Returns:
            技术指标数据列表
        """
        indicators = indicators or ["rsi", "macd"]
        provider = provider or 'yfinance'

        try:
            # 首先获取价格数据
            price_result = await asyncio.to_thread(
                self._obb.equity.price.historical,
                symbol=symbol,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                provider=provider,
            )

            price_df = price_result.to_df()
            if price_df.empty:
                return []

            results = []

            # 计算各项指标
            for indicator in indicators:
                indicator = indicator.lower()
                if indicator not in self.SUPPORTED_INDICATORS:
                    logger.warning(f"不支持的技术指标: {indicator}")
                    continue

                try:
                    indicator_data = await self._calculate_indicator(
                        data=price_df,
                        indicator=indicator,
                        symbol=symbol,
                    )
                    results.extend(indicator_data)
                except Exception as e:
                    logger.warning(f"计算 {indicator} 失败: {e}")

            return results

        except Exception as e:
            logger.error(f"获取 {symbol} 技术指标失败: {e}")
            return []

    async def _calculate_indicator(
        self,
        data,
        indicator: str,
        symbol: str,
        **params,
    ) -> List[Dict[str, Any]]:
        """
        计算单个技术指标

        Args:
            data: 价格数据 DataFrame
            indicator: 指标名称
            symbol: 股票代码
            **params: 指标参数

        Returns:
            指标数据列表
        """
        try:
            # 使用 OpenBB 技术分析扩展
            if indicator == "rsi":
                result = await asyncio.to_thread(
                    self._obb.technical.rsi,
                    data=data,
                    target="close",
                    length=params.get("length", 14),
                )
            elif indicator == "macd":
                result = await asyncio.to_thread(
                    self._obb.technical.macd,
                    data=data,
                    target="close",
                    fast=params.get("fast", 12),
                    slow=params.get("slow", 26),
                    signal=params.get("signal", 9),
                )
            elif indicator == "bbands":
                result = await asyncio.to_thread(
                    self._obb.technical.bbands,
                    data=data,
                    target="close",
                    length=params.get("length", 20),
                    std=params.get("std", 2),
                )
            elif indicator == "sma":
                result = await asyncio.to_thread(
                    self._obb.technical.sma,
                    data=data,
                    target="close",
                    length=params.get("length", 20),
                )
            elif indicator == "ema":
                result = await asyncio.to_thread(
                    self._obb.technical.ema,
                    data=data,
                    target="close",
                    length=params.get("length", 20),
                )
            elif indicator == "atr":
                result = await asyncio.to_thread(
                    self._obb.technical.atr,
                    data=data,
                    length=params.get("length", 14),
                )
            elif indicator == "adx":
                result = await asyncio.to_thread(
                    self._obb.technical.adx,
                    data=data,
                    length=params.get("length", 14),
                )
            elif indicator == "stoch":
                result = await asyncio.to_thread(
                    self._obb.technical.stoch,
                    data=data,
                    k_length=params.get("k_length", 14),
                    d_length=params.get("d_length", 3),
                )
            else:
                logger.warning(f"未实现的指标: {indicator}")
                return []

            df = result.to_df()
            if df.empty:
                return []

            # 转换为标准格式
            results = []
            for idx, row in df.iterrows():
                item = {
                    "symbol": symbol,
                    "indicator": indicator,
                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                }
                # 添加指标值
                for col in df.columns:
                    value = row.get(col)
                    if value is not None and not (isinstance(value, float) and value != value):  # 检查非 NaN
                        item[col] = float(value)

                results.append(item)

            return results

        except Exception as e:
            logger.error(f"计算指标 {indicator} 失败: {e}")
            return []

    async def get_rsi(
        self,
        symbol: str,
        length: int = 14,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取 RSI 指标

        Args:
            symbol: 股票代码
            length: 周期长度
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供商

        Returns:
            RSI 数据列表
        """
        return await self.get_indicators(
            symbol=symbol,
            indicators=["rsi"],
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )

    async def get_macd(
        self,
        symbol: str,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取 MACD 指标

        Args:
            symbol: 股票代码
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供商

        Returns:
            MACD 数据列表
        """
        return await self.get_indicators(
            symbol=symbol,
            indicators=["macd"],
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )

    async def get_bollinger_bands(
        self,
        symbol: str,
        length: int = 20,
        std: float = 2.0,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取布林带指标

        Args:
            symbol: 股票代码
            length: 周期长度
            std: 标准差倍数
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供商

        Returns:
            布林带数据列表
        """
        return await self.get_indicators(
            symbol=symbol,
            indicators=["bbands"],
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )

    def get_supported_indicators(self) -> List[str]:
        """
        获取支持的技术指标列表

        Returns:
            指标名称列表
        """
        return self.SUPPORTED_INDICATORS.copy()
