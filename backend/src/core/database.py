"""
Quant-Trade System - Database Configuration

数据库连接管理和会话配置。
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from src.core.config import settings


# ==============================================
# 数据库引擎配置
# ==============================================

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 数据库基类
Base = declarative_base()


# ==============================================
# 数据库依赖
# ==============================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话

    这是 FastAPI 依赖注入函数，用于在路由中获取数据库会话。

    Yields:
        AsyncSession: 数据库会话

    Example:
        ```python
        @app.get("/users/{user_id}")
        async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


# ==============================================
# 数据库初始化和关闭
# ==============================================

async def init_db():
    """
    初始化数据库

    创建所有表（如果不存在）。
    """
    try:
        async with engine.begin() as conn:
            # 导入所有模型以确保它们被注册
            from src.models import user, strategy, backtest, trading

            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        raise


async def close_db():
    """
    关闭数据库连接

    优雅地关闭数据库引擎。
    """
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}", exc_info=True)
        raise


# ==============================================
# 数据库健康检查
# ==============================================

async def check_db_health() -> bool:
    """
    检查数据库连接健康状态

    Returns:
        bool: 数据库是否可用
    """
    try:
        async with AsyncSessionLocal() as session:
            # 执行简单查询测试连接
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
