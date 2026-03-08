"""
Backtest Endpoint

回测相关端点。
"""

from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def run_backtest():
    """运行回测"""
    return {"success": True, "data": {"message": "Run backtest endpoint - TODO"}}

@router.get("/results/{result_id}")
async def get_backtest_result(result_id: str):
    """获取回测结果"""
    return {"success": True, "data": {"result_id": result_id, "message": "Get result - TODO"}}
