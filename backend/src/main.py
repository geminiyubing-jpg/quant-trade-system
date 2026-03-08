"""
Quant-Trade System - Main Application Entry Point

主应用入口文件，负责创建和配置 FastAPI 应用。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from src.core.config import settings
from src.core.database import init_db, close_db
from src.api.v1.api import api_router


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理

    启动时初始化数据库连接，关闭时清理资源。
    """
    # 启动时执行
    logger.info("🚀 Starting Quant-Trade System...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Version: {settings.APP_VERSION}")

    # 初始化数据库
    await init_db()
    logger.info("✅ Database initialized")

    yield

    # 关闭时执行
    logger.info("🛑 Shutting down Quant-Trade System...")
    await close_db()
    logger.info("✅ Database connections closed")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="专业级量化交易系统 API",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ==============================================
# 中间件配置
# ==============================================

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip 压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ==============================================
# 异常处理器
# ==============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误" if settings.APP_ENV != "development" else str(exc),
            }
        }
    )


# ==============================================
# 路由注册
# ==============================================

# 健康检查
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查端点"""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }
    }


# API 路由
app.include_router(api_router, prefix=settings.API_PREFIX)


# ==============================================
# 启动入口
# ==============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
