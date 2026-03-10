"""
Data Endpoint

数据管理相关端点。
"""

from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from src.services.data.akshare import AkShareDataSource

router = APIRouter()


@router.get("/stocks")
async def get_stocks(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=500, description="每页数量"),
    search: Optional[str] = Query(default=None, description="搜索关键词（代码或名称）"),
    market: Optional[str] = Query(default=None, description="市场筛选（SHSE/SZSE）"),
    industry: Optional[str] = Query(default=None, description="行业筛选")
):
    """
    获取股票列表

    Args:
        page: 页码（从1开始）
        page_size: 每页数量（1-500）
        search: 搜索关键词（支持代码和名称模糊匹配）
        market: 市场筛选（SHSE=上海, SZSE=深圳）
        industry: 行业筛选

    Returns:
        分页的股票列表
    """
    try:
        data_source = AkShareDataSource()

        # 确定市场参数
        market_param = "all"
        if market == "SHSE":
            market_param = "sh"
        elif market == "SZSE":
            market_param = "sz"

        # 获取股票列表
        stocks = data_source.get_stock_list(market=market_param)

        if not stocks:
            return {
                "success": True,
                "data": [],
                "meta": {
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "total_pages": 0
                }
            }

        # 搜索过滤
        if search:
            search_lower = search.lower()
            stocks = [
                s for s in stocks
                if search_lower in s.symbol.lower() or search_lower in s.name.lower()
            ]

        # 行业过滤（需要获取详细信息，可能较慢，暂时简化处理）
        # TODO: 后续可添加缓存或预加载行业信息

        # 分页
        total = len(stocks)
        total_pages = (total + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_stocks = stocks[start_idx:end_idx]

        # 转换为响应格式
        stock_list = []
        for s in paginated_stocks:
            stock_list.append({
                "symbol": s.symbol,
                "name": s.name,
                "market": s.market,
                "industry": s.industry,
                "sector": s.sector
            })

        return {
            "success": True,
            "data": stock_list,
            "meta": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")


@router.get("/stocks/{symbol}")
async def get_stock_detail(symbol: str):
    """
    获取股票详情

    Args:
        symbol: 股票代码（如: 000001, 600000）

    Returns:
        股票详细信息（基本面、行业等）
    """
    try:
        data_source = AkShareDataSource()

        # 获取股票基本信息
        stock_info = data_source.get_stock_info(symbol)

        if not stock_info:
            return {
                "success": False,
                "message": f"未找到股票 {symbol}",
                "data": None
            }

        # 获取最新行情
        latest_price = data_source.get_latest_price(symbol)

        # 构建响应
        result = {
            "symbol": stock_info.symbol,
            "name": stock_info.name,
            "market": stock_info.market,
            "industry": stock_info.industry,
            "sector": stock_info.sector,
            "latest_price": None
        }

        # 添加最新行情
        if latest_price:
            result["latest_price"] = {
                "price": float(latest_price.close),
                "open": float(latest_price.open),
                "high": float(latest_price.high),
                "low": float(latest_price.low),
                "volume": latest_price.volume,
                "amount": float(latest_price.amount) if latest_price.amount else 0,
                "timestamp": int(latest_price.timestamp.timestamp() * 1000)
            }

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票详情失败: {str(e)}")


@router.get("/kline/{symbol}")
async def get_kline_data(
    symbol: str,
    period: str = Query(default="daily", description="周期: daily, weekly, monthly"),
    days: int = Query(default=120, description="获取最近N天的数据", ge=1, le=1000),
    start_date: Optional[str] = Query(default=None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="结束日期 (YYYY-MM-DD)")
):
    """
    获取 K 线数据

    Args:
        symbol: 股票代码（如: 000001.SZ, 600000.SH）
        period: 周期 (daily=日K, weekly=周K, monthly=月K)
        days: 获取最近N天的数据（当未指定 start_date/end_date 时使用）
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        K线数据列表
    """
    try:
        data_source = AkShareDataSource()

        # 处理日期
        if start_date and end_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        else:
            end = date.today()
            start = end - timedelta(days=days)

        # 映射周期
        period_map = {
            "daily": "1d",
            "weekly": "1w",
            "monthly": "1M"
        }
        interval = period_map.get(period, "1d")

        # 获取数据
        prices = data_source.get_stock_prices(
            symbol=symbol,
            start_date=start,
            end_date=end,
            interval=interval
        )

        if not prices:
            return {
                "success": False,
                "message": f"未获取到 {symbol} 的K线数据",
                "data": []
            }

        # 转换为前端需要的格式
        kline_data = []
        for p in prices:
            kline_data.append({
                "date": p.timestamp.strftime("%Y-%m-%d"),
                "timestamp": int(p.timestamp.timestamp() * 1000),
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "volume": p.volume,
                "amount": float(p.amount) if p.amount else 0,
                "symbol": p.symbol
            })

        return {
            "success": True,
            "data": kline_data,
            "meta": {
                "symbol": symbol,
                "period": period,
                "count": len(kline_data),
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/quote/{symbol}")
async def get_realtime_quote(symbol: str):
    """
    获取实时行情

    Args:
        symbol: 股票代码

    Returns:
        实时行情数据
    """
    try:
        data_source = AkShareDataSource()
        price = data_source.get_latest_price(symbol)

        if not price:
            return {
                "success": False,
                "message": f"未获取到 {symbol} 的实时行情",
                "data": None
            }

        return {
            "success": True,
            "data": {
                "symbol": price.symbol,
                "timestamp": int(price.timestamp.timestamp() * 1000),
                "open": float(price.open),
                "high": float(price.high),
                "low": float(price.low),
                "price": float(price.close),
                "volume": price.volume,
                "amount": float(price.amount) if price.amount else 0
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时行情失败: {str(e)}")
