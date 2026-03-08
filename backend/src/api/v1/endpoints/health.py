"""
Health Check Endpoint

健康检查端点，用于监控系统状态。
"""

from fastapi import APIRouter
from sqlalchemy.orm import Session
from loguru import logger

from src.core.database import get_db, check_db_connection
from src.core.config import settings


router = APIRouter()


@router.get("/health", summary="健康检查")
async def health_check():
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
    db_healthy = check_db_connection()

    return {
        "success": True,
        "status": "healthy" if db_healthy else "unhealthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "components": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "host": settings.postgres_host,
                "port": settings.postgres_port,
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
    return {"success": True, "message": "pong"}
