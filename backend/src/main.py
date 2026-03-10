"""
==============================================
QuantAI Ecosystem - FastAPI 主应用
==============================================
"""

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger
import sys

from .core.config import settings
from .core.database import check_db_connection
from .services.websocket.market_data_service import market_data_service


# ==============================================
# 配置 Loguru 日志
# ==============================================
logger.remove()  # 移除默认处理器
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)
logger.add(
    settings.log_file_path,
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="1 day",
    retention=f"{settings.log_retention_days} days",
    compression="zip",
)


# ==============================================
# 应用生命周期管理
# ==============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 正在启动...")
    logger.info(f"📊 环境: {settings.app_env}")
    logger.info(f"🔧 调试模式: {settings.debug}")

    # 检查数据库连接
    if check_db_connection():
        logger.info("✅ 数据库连接正常")
    else:
        logger.error("❌ 数据库连接失败")
        raise RuntimeError("Database connection failed")

    # 启动行情数据服务
    await market_data_service.start()
    logger.info("✅ 行情数据服务已启动")

    yield  # 应用运行中

    # 关闭时执行
    logger.info(f"🛑 {settings.app_name} 正在关闭...")
    await market_data_service.stop()


# ==============================================
# 创建 FastAPI 应用
# ==============================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="QuantAI Ecosystem - 下一代 AI 驱动的量化交易生态系统",
    docs_url="/docs" if settings.debug else None,  # 生产环境关闭文档
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# ==============================================
# 中间件配置
# ==============================================

# CORS 中间件（跨域资源共享）
# 注意：当 allow_credentials=True 时，allow_origins 不能是 ["*"]，必须指定具体域名
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip 中间件（响应压缩）
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ==============================================
# 全局异常处理器
# ==============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred",
        },
    )


# ==============================================
# 请求日志中间件
# ==============================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    start_time = datetime.utcnow()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # 记录日志
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# ==============================================
# 基础路由
# ==============================================
@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "success": True,
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    db_status = check_db_connection()
    
    return {
        "success": True,
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/config", tags=["Config"])
async def get_config():
    """获取应用配置（仅开发环境）"""
    if not settings.debug:
        return {"success": False, "message": "Not available in production"}
    
    return {
        "success": True,
        "config": {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "app_env": settings.app_env,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "database_url": settings.database_url.split("@")[1] if "@" in settings.database_url else "***",  # 隐藏密码
            "redis_url": settings.redis_url.split("@")[1] if "@" in settings.redis_url else "***",  # 隐藏密码
        },
    }


# ==============================================
# API 路由
# ==============================================
from .api.v1.endpoints import auth, users, trading, health, risk, backtest, websocket, data, watchlist, alerts, data_etl

# 认证路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# 用户管理路由
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

# 交易路由
app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])

# 风控路由
app.include_router(risk.router, prefix="/api/v1/risk", tags=["Risk Control"])

# 回测路由
app.include_router(backtest.router, prefix="/api/v1/backtest", tags=["Backtest"])

# 健康检查路由
app.include_router(health.router, tags=["Health"])

# WebSocket 路由
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])

# 数据管理路由
app.include_router(data.router, prefix="/api/v1/data", tags=["Data"])

# 自选股路由
app.include_router(watchlist.router, prefix="/api/v1/watchlist", tags=["Watchlist"])

# 价格预警路由
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Price Alerts"])

# 数据ETL路由
app.include_router(data_etl.router, prefix="/api/v1/data-etl", tags=["Data ETL"])

# AI功能路由
from .api.v1.endpoints import ai
app.include_router(ai.router, prefix="/api/v1", tags=["AI"])

# 策略进化路由
from .api.v1.endpoints import evolution
app.include_router(evolution.router, prefix="/api/v1", tags=["Strategy Evolution"])


# 添加新模块路由
from .api.v1.endpoints import strategy_versions, backtest_analysis, fills, trading_calendar, daily_trade_stats, portfolio

# 策略版本管理路由
app.include_router(strategy_versions.router, prefix="/api/v1/strategies", tags=["策略版本管理"])

# 回测分析路由
app.include_router(backtest_analysis.router, prefix="/api/v1/backtest", tags=["回测分析"])

# 成交记录路由
app.include_router(fills.router, prefix="/api/v1/fills", tags=["成交记录"])

# 交易日历路由
app.include_router(trading_calendar.router, prefix="/api/v1/trading-calendar", tags=["交易日历"])

# 交易统计路由
app.include_router(daily_trade_stats.router, prefix="/api/v1/trade-stats", tags=["交易统计"])

# 投资组合路由
app.include_router(portfolio.router, prefix="/api/v1/portfolios", tags=["投资组合"])

# 数据质量监控路由
from .api.v1.endpoints import data_quality
app.include_router(data_quality.router, prefix="/api/v1", tags=["Data Quality"])

# 策略注册表路由
from .api.v1.endpoints import strategy_registry
app.include_router(strategy_registry.router, prefix="/api/v1/strategy-registry", tags=["策略注册表"])

# 数据引擎路由
from .api.v1.endpoints import data_engine
app.include_router(data_engine.router, prefix="/api/v1/data-engine", tags=["数据引擎"])

# 板块分析路由
from .api.v1.endpoints import sector
app.include_router(sector.router, prefix="/api/v1/data", tags=["板块分析"])


# ==============================================
# 启动命令
# ==============================================
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Starting {settings.app_name} server...")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower(),
    )
