"""
Data ETL Endpoint

数据 ETL（提取、转换、加载）端点。
"""

from typing import Optional, List
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.core.database import get_db
from src.services.data.yahoo_finance import get_yahoo_finance_source
from src.services.data.akshare import get_akshare_source
from src.services.data.validation import DataPipeline, validate_and_clean_prices
from src.services.data.storage import DataStorageService
from src.services.data.base import StockPriceData

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

class DataFetchRequest(BaseModel):
    """数据获取请求"""
    symbol: str = Field(..., description="股票代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    source: str = Field("auto", description="数据源（yahoo, akshare, auto）")
    save_to_db: bool = Field(True, description="是否保存到数据库")


class DataFetchResponse(BaseModel):
    """数据获取响应"""
    success: bool
    symbol: str
    source: str
    records_fetched: int
    records_saved: int
    quality_rate: float
    message: str


# ==============================================
# 数据源管理
# ==============================================

@router.get("/sources")
async def get_data_sources():
    """获取可用的数据源列表"""
    yahoo_source = get_yahoo_finance_source()
    akshare_source = get_akshare_source()

    return {
        "success": True,
        "data": {
            "sources": [
                {
                    "name": "Yahoo Finance",
                    "code": "yahoo",
                    "available": yahoo_source.is_available,
                    "connection_ok": yahoo_source.check_connection() if yahoo_source.is_available else False,
                    "description": "美股、港股等市场数据",
                    "quality": "⭐⭐⭐⭐"
                },
                {
                    "name": "AkShare",
                    "code": "akshare",
                    "available": akshare_source.is_available,
                    "connection_ok": akshare_source.check_connection() if akshare_source.is_available else False,
                    "description": "A股市场数据（沪深）",
                    "quality": "⭐⭐⭐⭐⭐"
                }
            ]
        }
    }


@router.post("/fetch", response_model=DataFetchResponse)
async def fetch_stock_data(
    request: DataFetchRequest,
    db: Session = Depends(get_db)
):
    """获取股票数据并保存到数据库"""
    # 验证日期
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始日期不能晚于结束日期"
        )

    # 自动选择数据源
    source_code = request.source
    if source_code == "auto":
        if request.symbol.endswith((".SZ", ".SH")) or request.symbol.isdigit():
            source_code = "akshare"
        else:
            source_code = "yahoo"

    # 获取数据源
    if source_code == "yahoo":
        source = get_yahoo_finance_source()
    elif source_code == "akshare":
        source = get_akshare_source()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的数据源: {source_code}"
        )

    # 检查数据源可用性
    if not source.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"数据源 {source_code} 不可用"
        )

    # 获取数据
    try:
        prices = source.get_stock_prices(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )

        if not prices:
            return DataFetchResponse(
                success=False,
                symbol=request.symbol,
                source=source_code,
                records_fetched=0,
                records_saved=0,
                quality_rate=0.0,
                message="未获取到数据"
            )

        # 数据清洗和验证
        pipeline = DataPipeline()
        cleaned_prices = pipeline.process_stock_prices(prices)

        # 保存到数据库
        records_saved = 0
        if request.save_to_db:
            storage_service = DataStorageService(db)
            records_saved = storage_service.save_stock_prices_upsert(cleaned_prices)

        # 生成质量报告
        quality_report = pipeline.get_data_quality_report(prices, cleaned_prices)

        return DataFetchResponse(
            success=True,
            symbol=request.symbol,
            source=source_code,
            records_fetched=len(prices),
            records_saved=records_saved,
            quality_rate=quality_report["quality_rate"],
            message=f"成功获取 {len(cleaned_prices)} 条数据，质量率 {quality_report['quality_rate']}%"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据失败: {str(e)}"
        )
