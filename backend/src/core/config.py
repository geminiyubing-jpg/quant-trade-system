"""
Quant-Trade System - Application Configuration

应用配置管理，从环境变量读取配置。
"""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""

    # ==============================================
    # 应用配置
    # ==============================================
    APP_NAME: str = "Quant-Trade System"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ==============================================
    # 服务器配置
    # ==============================================
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # ==============================================
    # 数据库配置 - PostgreSQL
    # ==============================================
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "quant_trade"
    POSTGRES_PASSWORD: str = "quant_trade_pass"
    POSTGRES_DB: str = "quant_trade"
    POSTGRES_MAX_CONNECTIONS: int = 20

    @property
    def DATABASE_URL(self) -> str:
        """数据库连接 URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # ==============================================
    # 缓存配置 - Redis
    # ==============================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 10

    @property
    def REDIS_URL(self) -> str:
        """Redis 连接 URL"""
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ==============================================
    # Celery 配置
    # ==============================================
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672/"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_TIMEOUT: int = 300

    # ==============================================
    # JWT 认证配置
    # ==============================================
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==============================================
    # CORS 配置
    # ==============================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ==============================================
    # 数据源配置
    # ==============================================
    TUSHARE_TOKEN: str = ""
    TUSHARE_PRO_API: str = "https://api.tushare.pro"

    # ==============================================
    # 交易配置
    # ==============================================
    PAPER_TRADING: bool = True
    PAPER_TRADING_INITIAL_CAPITAL: float = 1000000.0

    # 风控配置
    MAX_POSITION_RATIO: float = 0.3
    MAX_SINGLE_STOCK_RATIO: float = 0.1
    MAX_DAILY_LOSS_RATIO: float = 0.05
    STOP_LOSS_RATIO: float = 0.08

    # ==============================================
    # 文件存储
    # ==============================================
    UPLOAD_DIR: str = "uploads/"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB

    # ==============================================
    # 性能配置
    # ==============================================
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    CACHE_TTL: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 1000

    # ==============================================
    # 功能开关
    # ==============================================
    FEATURE_DATA_DOWNLOAD: bool = True
    FEATURE_BACKTEST: bool = True
    FEATURE_LIVE_TRADING: bool = False
    FEATURE_AI_OPTIMIZATION: bool = True

    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例

    使用 lru_cache 确保配置只加载一次。
    """
    return Settings()


# 导出配置实例
settings = get_settings()
