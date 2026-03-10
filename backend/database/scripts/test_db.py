#!/usr/bin/env python3
"""
Quant-Trade System - 数据库连接测试

用法:
    python scripts/test_db.py
"""

import asyncio
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from src.core.config import settings


async def test_connection():
    """测试数据库连接"""
    print("🔧 测试数据库连接...")
    print(f"   主机: {settings.POSTGRES_HOST}")
    print(f"   端口: {settings.POSTGRES_PORT}")
    print(f"   数据库: {settings.POSTGRES_DB}")
    print(f"   用户: {settings.POSTGRES_USER}")

    # 创建引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
    )

    # 测试连接
    try:
        async with engine.begin() as conn:
            # 测试查询
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"\n✅ 数据库连接成功！")
            print(f"   PostgreSQL 版本: {version}")

            # 检查表
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'
            """))
            table_count = result.scalar()
            print(f"   表数量: {table_count}")

            # 检查数据库大小
            result = await conn.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """))
            db_size = result.scalar()
            print(f"   数据库大小: {db_size}")

    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        raise

    finally:
        await engine.dispose()


async def test_crud():
    """测试 CRUD 操作"""
    print("\n🧪 测试 CRUD 操作...")

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 测试插入
        from src.models.stock import Stock
        from decimal import Decimal

        # 创建测试股票
        test_stock = Stock(
            symbol='TEST001',
            name='测试股票',
            sector='测试',
            market='TEST'
        )

        session.add(test_stock)
        await session.commit()
        print("✅ 插入测试数据成功")

        # 测试查询
        result = await session.execute(text("SELECT * FROM stocks WHERE symbol = 'TEST001'"))
        stock = result.fetchone()
        print(f"✅ 查询成功: {stock}")

        # 测试删除
        await session.execute(text("DELETE FROM stocks WHERE symbol = 'TEST001'"))
        await session.commit()
        print("✅ 删除测试数据成功")

    await engine.dispose()


async def main():
    """主函数"""
    print("=" * 60)
    print("🧪 Quant-Trade System - 数据库测试")
    print("=" * 60)
    print()

    try:
        await test_connection()
        await test_crud()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
