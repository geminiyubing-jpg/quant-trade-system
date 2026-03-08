"""
API v1 Router

聚合所有 v1 版本的 API 路由。
"""

from fastapi import APIRouter

from src.api.v1.endpoints import (
    health,
    auth,
    users,
    data,
    strategy,
    backtest,
    trading,
)


# 创建 API 路由器
api_router = APIRouter()

# ==============================================
# 注册各个模块的路由
# ==============================================

# 健康检查
api_router.include_router(health.router, tags=["Health"])

# 认证
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# 用户管理
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# 数据管理
api_router.include_router(data.router, prefix="/data", tags=["Data"])

# 策略管理
api_router.include_router(strategy.router, prefix="/strategies", tags=["Strategies"])

# 回测
api_router.include_router(backtest.router, prefix="/backtest", tags=["Backtest"])

# 交易
api_router.include_router(trading.router, prefix="/trading", tags=["Trading"])
