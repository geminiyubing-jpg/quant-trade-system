"""
OpenBB API 端点

提供 OpenBB Platform 数据的 REST API 接口。
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from ....core.config import settings
from ....services.data.openbb import OpenBBAdapter


router = APIRouter()


# ==============================================
# Pydantic 模型
# ==============================================

class EquityQuoteResponse(BaseModel):
    """股票报价响应"""
    symbol: str
    price: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    previous_close: Optional[float] = None
    provider: str


class HistoricalPriceResponse(BaseModel):
    """历史价格响应"""
    symbol: str
    data: List[Dict[str, Any]]
    provider: str
    count: int


class FundamentalsResponse(BaseModel):
    """基本面数据响应"""
    symbol: str
    statement_type: str
    period: str
    data: List[Dict[str, Any]]
    provider: str


class MacroIndicatorResponse(BaseModel):
    """宏观经济指标响应"""
    indicator: str
    data: List[Dict[str, Any]]
    provider: str
    count: int


class TechnicalIndicatorResponse(BaseModel):
    """技术指标响应"""
    symbol: str
    indicators: List[str]
    data: List[Dict[str, Any]]
    provider: str
    count: int


# ==============================================
# 适配器依赖
# ==============================================

_adapter: Optional[OpenBBAdapter] = None
_adapter_error: Optional[str] = None


async def get_adapter() -> OpenBBAdapter:
    """获取 OpenBB 适配器实例"""
    global _adapter, _adapter_error

    if _adapter_error:
        # 之前初始化失败，直接返回错误
        raise HTTPException(status_code=503, detail=f"OpenBB 服务不可用: {_adapter_error}")

    if _adapter is None:
        try:
            config = {
                'hub_pat': settings.openbb_hub_pat,
                'fmp_api_key': settings.openbb_fmp_api_key,
                'polygon_api_key': settings.openbb_polygon_api_key,
                'benzinga_api_key': settings.openbb_benzinga_api_key,
                'intrinio_api_key': settings.openbb_intrinio_api_key,
                'fred_api_key': settings.openbb_fred_api_key,
                'tiingo_api_key': settings.openbb_tiingo_api_key,
                'default_equity_provider': settings.openbb_default_equity_provider,
                'default_economy_provider': settings.openbb_default_economy_provider,
            }
            _adapter = OpenBBAdapter(config=config)
            result = await _adapter.connect()
            logger.info(f"OpenBB 适配器初始化: connected={result}, is_connected={_adapter.is_connected}")

            if not result or not _adapter.is_connected:
                _adapter_error = "连接失败"
                raise HTTPException(status_code=503, detail="OpenBB 服务连接失败")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OpenBB 适配器初始化失败: {e}")
            _adapter_error = str(e)
            raise HTTPException(status_code=503, detail=f"OpenBB 服务不可用: {e}")

    if not _adapter.is_connected:
        raise HTTPException(status_code=503, detail="OpenBB 服务未连接")

    return _adapter


# ==============================================
# 股票数据端点
# ==============================================

@router.get("/equity/quote/{symbol}", response_model=EquityQuoteResponse)
async def get_equity_quote(
    symbol: str,
    provider: Optional[str] = Query(None, description="数据提供商 (yfinance, fmp, polygon)"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """
    获取股票实时报价

    支持的提供商:
    - yfinance (免费)
    - fmp (Financial Modeling Prep)
    - polygon
    """
    try:
        quote = await adapter.get_quote(symbol, provider)

        if not quote:
            raise HTTPException(status_code=404, detail=f"未找到股票 {symbol}")

        return EquityQuoteResponse(**quote)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报价失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equity/historical/{symbol}", response_model=HistoricalPriceResponse)
async def get_equity_historical(
    symbol: str,
    start_date: Optional[date] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    provider: Optional[str] = Query(None, description="数据提供商"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """
    获取股票历史价格数据

    默认获取最近 30 个交易日的数据。
    """
    try:
        from ....services.data.engine import DataFrequency

        data = await adapter.get_historical_price(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            frequency=DataFrequency.DAY,
            provider=provider,
        )

        return HistoricalPriceResponse(
            symbol=symbol,
            data=data,
            provider=provider or settings.openbb_default_equity_provider,
            count=len(data),
        )

    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equity/fundamentals/{symbol}", response_model=FundamentalsResponse)
async def get_equity_fundamentals(
    symbol: str,
    statement_type: str = Query("balance", description="报表类型 (balance, income, cash)"),
    period: str = Query("annual", description="周期 (annual, quarterly)"),
    provider: Optional[str] = Query(None, description="数据提供商"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """
    获取股票基本面数据

    报表类型:
    - balance: 资产负债表
    - income: 利润表
    - cash: 现金流量表
    """
    try:
        data = await adapter.get_fundamentals(
            symbol=symbol,
            statement_type=statement_type,
            period=period,
            provider=provider,
        )

        return FundamentalsResponse(
            symbol=symbol,
            statement_type=statement_type,
            period=period,
            data=data.get("data", []),
            provider=data.get("provider", "yfinance"),
        )

    except Exception as e:
        logger.error(f"获取基本面数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equity/valuation/{symbol}")
async def get_equity_valuation(
    symbol: str,
    provider: Optional[str] = Query(None, description="数据提供商"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """
    获取股票估值指标

    返回 P/E、P/B、EV/EBITDA 等估值指标。
    """
    try:
        # 使用基本面数据计算估值指标
        fundamentals = await adapter.equity.get_fundamentals(
            symbol=symbol,
            statement_type="balance",
            period="annual",
            provider=provider or "fmp",
        )

        # 获取价格数据
        quote = await adapter.equity.get_quote(symbol, provider)

        # TODO: 计算估值指标

        return {
            "symbol": symbol,
            "price": quote.get("price"),
            "valuation_metrics": {
                "pe_ratio": None,  # 待实现
                "pb_ratio": None,
                "ev_ebitda": None,
            },
            "provider": provider or "fmp",
        }

    except Exception as e:
        logger.error(f"获取估值数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================
# 宏观经济数据端点
# ==============================================

@router.get("/economy/macro/{indicator}", response_model=MacroIndicatorResponse)
async def get_macro_indicator(
    indicator: str,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    provider: Optional[str] = Query(None, description="数据提供商 (fred, oecd)"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """
    获取宏观经济指标

    常用指标:
    - GDP: 国内生产总值
    - CPI: 消费者物价指数
    - UNRATE: 失业率
    - FEDFUNDS: 联邦基金利率
    - DGS10: 10年期国债收益率
    """
    try:
        data = await adapter.economy.get_indicator(
            indicator=indicator,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )

        return MacroIndicatorResponse(
            indicator=indicator,
            data=data,
            provider=provider or settings.openbb_default_economy_provider,
            count=len(data),
        )

    except Exception as e:
        logger.error(f"获取宏观数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economy/treasury")
async def get_treasury_rates(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    provider: Optional[str] = Query(None, description="数据提供商"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """
    获取美国国债收益率

    返回各期限国债收益率数据。
    """
    try:
        data = await adapter.economy.get_treasury_rates(
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )

        return {
            "data": data,
            "provider": provider or "fred",
            "count": len(data),
        }

    except Exception as e:
        logger.error(f"获取国债收益率失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================
# 技术分析端点
# ==============================================

@router.get("/technical/indicators/{symbol}", response_model=TechnicalIndicatorResponse)
async def get_technical_indicators(
    symbol: str,
    indicators: str = Query("rsi,macd", description="技术指标列表 (逗号分隔)"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    provider: Optional[str] = Query(None, description="数据提供商"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """
    获取技术分析指标

    支持的指标:
    - rsi: 相对强弱指数
    - macd: 异同移动平均线
    - bbands: 布林带
    - sma: 简单移动平均
    - ema: 指数移动平均
    - atr: 平均真实波幅
    - adx: 平均趋向指数
    - stoch: 随机指标
    """
    try:
        indicator_list = [i.strip().lower() for i in indicators.split(",")]

        data = await adapter.technical.get_indicators(
            symbol=symbol,
            indicators=indicator_list,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )

        return TechnicalIndicatorResponse(
            symbol=symbol,
            indicators=indicator_list,
            data=data,
            provider=provider or "yfinance",
            count=len(data),
        )

    except Exception as e:
        logger.error(f"获取技术指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical/rsi/{symbol}")
async def get_rsi(
    symbol: str,
    length: int = Query(14, ge=1, le=100, description="RSI 周期"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """获取 RSI 指标"""
    try:
        data = await adapter.technical.get_rsi(
            symbol=symbol,
            length=length,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "symbol": symbol,
            "indicator": "rsi",
            "length": length,
            "data": data,
            "count": len(data),
        }

    except Exception as e:
        logger.error(f"获取 RSI 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical/macd/{symbol}")
async def get_macd(
    symbol: str,
    fast: int = Query(12, ge=1, le=50, description="快线周期"),
    slow: int = Query(26, ge=1, le=100, description="慢线周期"),
    signal: int = Query(9, ge=1, le=50, description="信号线周期"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    adapter: OpenBBAdapter = Depends(get_adapter),
):
    """获取 MACD 指标"""
    try:
        data = await adapter.technical.get_macd(
            symbol=symbol,
            fast=fast,
            slow=slow,
            signal=signal,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "symbol": symbol,
            "indicator": "macd",
            "parameters": {"fast": fast, "slow": slow, "signal": signal},
            "data": data,
            "count": len(data),
        }

    except Exception as e:
        logger.error(f"获取 MACD 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================
# 系统状态端点
# ==============================================

@router.get("/status")
async def get_status(adapter: OpenBBAdapter = Depends(get_adapter)):
    """
    获取 OpenBB 服务状态

    返回连接状态和支持的数据类型。
    """
    return adapter.get_status()


@router.get("/providers")
async def list_providers():
    """
    列出支持的 OpenBB 数据提供商

    返回所有可用的数据提供商列表。
    """
    return {
        "equity": {
            "free": ["yfinance"],
            "paid": ["fmp", "polygon", "intrinio"],
        },
        "economy": {
            "free": ["fred"],
            "paid": ["oecd", "tradingeconomics"],
        },
        "news": {
            "paid": ["benzinga", "biztoc"],
        },
    }
