"""
Trading Endpoint

交易相关端点。
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/orders")
async def get_orders():
    """获取订单列表"""
    return {"success": True, "data": {"message": "Get orders endpoint - TODO"}}

@router.post("/orders")
async def create_order():
    """创建订单"""
    return {"success": True, "data": {"message": "Create order endpoint - TODO"}}
