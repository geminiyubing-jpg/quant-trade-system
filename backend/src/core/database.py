"""
==============================================
QuantAI Ecosystem - 数据库连接模块
==============================================
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool

from .config import settings

# ==============================================
# SQLAlchemy Base
# ==============================================
Base = declarative_base()

# ==============================================
# 数据库引擎
# ==============================================
engine: Engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,  # 验证连接有效性
    echo=settings.debug,  # 开发环境打印 SQL
    future=True,  # 使用 SQLAlchemy 2.0 风格
)

# ==============================================
# Session 工厂
# ==============================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)


# ==============================================
# 数据库依赖注入（FastAPI）
# ==============================================
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依赖注入：获取数据库会话
    
    使用方式:
        @app.get("/users/{user_id}")
        def read_user(user_id: int, db: Session = Depends(get_db)):
            user = db.query(User).filter(User.id == user_id).first()
            return user
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================
# 上下文管理器
# ==============================================
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    数据库会话上下文管理器
    
    使用方式:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ==============================================
# 数据库初始化
# ==============================================
def init_db():
    """初始化数据库（创建所有表）"""
    # 导入所有模型以确保它们被注册到 Base.metadata
    from ..models import user, trading, strategy, risk, stock
    Base.metadata.create_all(bind=engine)


def drop_db():
    """删除所有表（谨慎使用）"""
    # 导入所有模型以确保它们被注册到 Base.metadata
    from ..models import user, trading, strategy, risk, stock
    Base.metadata.drop_all(bind=engine)


# ==============================================
# 健康检查
# ==============================================
def check_db_connection() -> bool:
    """检查数据库连接是否正常"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
