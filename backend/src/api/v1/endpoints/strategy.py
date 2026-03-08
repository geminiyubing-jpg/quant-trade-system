"""
Strategy Endpoint

策略管理相关端点。
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_strategies():
    """获取策略列表"""
    return {"success": True, "data": {"message": "Get strategies endpoint - TODO"}}

@router.post("/")
async def create_strategy():
    """创建策略"""
    return {"success": True, "data": {"message": "Create strategy endpoint - TODO"}}
