"""
Data Endpoint

数据管理相关端点。
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/stocks")
async def get_stocks():
    """获取股票列表"""
    return {"success": True, "data": {"message": "Get stocks endpoint - TODO"}}

@router.get("/stocks/{symbol}")
async def get_stock_detail(symbol: str):
    """获取股票详情"""
    return {"success": True, "data": {"symbol": symbol, "message": "Get stock detail - TODO"}}
