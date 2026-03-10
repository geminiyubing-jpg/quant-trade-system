"""
==============================================
QuantAI Ecosystem - 应用配置模块
==============================================
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类（使用 Pydantic Settings）"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==============================================
    # 应用配置
    # ==============================================
    app_name: str = Field(default="QuantAI_Ecosystem", description="应用名称")
    app_version: str = Field(default="2.0.0", description="应用版本")
    app_env: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """验证运行环境"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    # ==============================================
    # 服务器配置
    # ==============================================
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8000, description="服务器端口", ge=1, le=65535)
    workers: int = Field(default=4, description="工作进程数", ge=1)

    # ==============================================
    # 数据库配置
    # ==============================================
    postgres_host: str = Field(default="localhost", description="PostgreSQL 主机")
    postgres_port: int = Field(default=5432, description="PostgreSQL 端口", ge=1, le=65535)
    postgres_user: str = Field(default="quant_trio", description="PostgreSQL 用户名")
    postgres_password: str = Field(default="quant_trio_pass", description="PostgreSQL 密码")
    postgres_db: str = Field(default="quant_trio", description="PostgreSQL 数据库名")

    @property
    def database_url(self) -> str:
        """生成数据库连接 URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        """生成异步数据库连接 URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # 数据库连接池配置
    db_pool_size: int = Field(default=20, description="连接池大小", ge=1)
    db_max_overflow: int = Field(default=10, description="最大溢出连接数", ge=0)
    db_pool_timeout: int = Field(default=30, description="连接池超时（秒）", ge=1)
    db_pool_recycle: int = Field(default=3600, description="连接回收时间（秒）", ge=0)

    # ==============================================
    # Redis 配置
    # ==============================================
    redis_host: str = Field(default="localhost", description="Redis 主机")
    redis_port: int = Field(default=6379, description="Redis 端口", ge=1, le=65535)
    redis_password: Optional[str] = Field(default=None, description="Redis 密码")
    redis_db: int = Field(default=0, description="Redis 数据库", ge=0, le=15)
    redis_max_connections: int = Field(default=20, description="最大连接数", ge=1)

    @property
    def redis_url(self) -> str:
        """生成 Redis 连接 URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ==============================================
    # 认证配置
    # ==============================================
    secret_key: str = Field(default="change-this-secret-key-in-production", description="JWT 密钥")
    algorithm: str = Field(default="HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间（分钟）", ge=1)
    refresh_token_expire_days: int = Field(default=7, description="刷新令牌过期时间（天）", ge=1)

    # ==============================================
    # 外部 API 密钥
    # ==============================================
    tushare_token: Optional[str] = Field(default=None, description="Tushare Token")
    alpha_vantage_api_key: Optional[str] = Field(default=None, description="Alpha Vantage API Key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    glm_api_key: Optional[str] = Field(default=None, description="GLM API Key")
    glm_api_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4/chat/completions", description="GLM API URL")
    glm_model: str = Field(default="glm-4", description="GLM Model Name")

    # ==============================================
    # 交易配置
    # ==============================================
    default_max_slippage: float = Field(default=0.001, description="默认最大滑点", ge=0)
    default_max_position_ratio: float = Field(default=0.3, description="默认最大单仓比例", ge=0, le=1)
    default_max_daily_loss_ratio: float = Field(default=0.05, description="默认最大单日亏损比例", ge=0, le=1)

    # ==============================================
    # 风控配置
    # ==============================================
    risk_control_enabled: bool = Field(default=True, description="启用实时风控")
    risk_check_interval: int = Field(default=60, description="风险检查间隔（秒）", ge=1)

    # ==============================================
    # 日志配置
    # ==============================================
    log_file_path: str = Field(default="logs/app.log", description="日志文件路径")
    log_retention_days: int = Field(default=30, description="日志保留天数", ge=1)

    # ==============================================
    # Celery 配置
    # ==============================================
    celery_broker_url: str = Field(default="redis://localhost:6379/1", description="Celery Broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", description="Celery Result Backend")

    # ==============================================
    # 项目路径
    # ==============================================
    @property
    def base_dir(self) -> Path:
        """项目根目录"""
        return Path(__file__).resolve().parent.parent.parent

    @property
    def log_dir(self) -> Path:
        """日志目录"""
        return self.base_dir / "logs"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
