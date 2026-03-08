"""
Authentication Endpoint

认证相关端点。
"""

from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login():
    """用户登录"""
    return {"success": True, "data": {"message": "Login endpoint - TODO"}}

@router.post("/logout")
async def logout():
    """用户登出"""
    return {"success": True, "data": {"message": "Logout endpoint - TODO"}}
