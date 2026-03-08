"""
Health Check Endpoint

健康检查端点，用于监控系统状态。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.core.database import get_db, check_db_health
from src.core.config import settings


router = APIRouter()


@router.get("/health", summary="健康检查")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    系统健康检查

    检查系统各个组件的健康状态：
    - 应用状态
    - 数据库连接
    - 环境信息

    Returns:
        dict: 健康状态信息
    """
    # 检查数据库
    db_healthy = await check_db_health()

    return {
        "success": True,
        "data": {
            "status": "healthy" if db_healthy else "unhealthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "components": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "host": settings.POSTGRES_HOST,
                    "port": settings.POSTGRES_PORT,
                }
            }
        }
    }


@router.get("/ping", summary="Ping 检查")
async def ping():
    """
    简单的 Ping 检查，用于负载均衡器健康检查。

    Returns:
        dict: pong 响应
    """
    return {"success": True, "data": {"message": "pong"}}
