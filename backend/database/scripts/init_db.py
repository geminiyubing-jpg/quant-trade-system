#!/usr/bin/env python3
"""
Quant-Trade System - 数据库初始化脚本

用法:
    python scripts/init_db.py
"""

import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import asyncpg

from src.core.config import settings
from src.core.database import Base, init_db
from src.models import user, stock, strategy, trading


async def create_database():
    """创建数据库（如果不存在）"""
    print("🔧 检查数据库连接...")
    
    # 使用 psycopg 连接到 postgres 默认数据库
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database='postgres'  # 连接到默认数据库
    )
    
    try:
        # 检查数据库是否存在
        exists = await conn.fetchval(
            "SELECT EXISTS FROM pg_database WHERE datname = $1",
            settings.POSTGRES_DB
        )
        
        if not exists:
            print(f"📦 创建数据库: {settings.POSTGRES_DB}")
            await conn.execute(f'CREATE DATABASE {settings.POSTGRES_DB}')
            print(f"✅ 数据库 {settings.POSTGRES_DB} 创建成功")
        else:
            print(f"✅ 数据库 {settings.POSTGRES_DB} 已存在")
    
    finally:
        await conn.close()


async def run_migrations():
    """运行数据库迁移"""
    print("\n📋 运行数据库迁移...")
    
    # 创建引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )

    # 创建所有表
    async with engine.begin() as conn:
        # 读取并执行 SQL 文件
        sql_file = Path(__file__).parent.parent / 'migrations' / 'init_postgres.sql'
        
        if sql_file.exists():
            print(f"📄 读取 SQL 文件: {sql_file}")
            sql_content = sql_file.read_text()
            
            print("🚀 执行 SQL 脚本...")
            await conn.execute(text(sql_content))
            print("✅ 数据库迁移完成")
        else:
            print("⚠️  SQL 文件不存在，跳过迁移")

    await engine.dispose()


async def insert_test_data():
    """插入测试数据"""
    print("\n📊 插入测试数据...")
    
    from src.models.stock import Stock, StockPrice
    from datetime import datetime, timedelta
    from decimal import Decimal
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 检查是否已有数据
        result = await session.execute(text("SELECT COUNT(*) FROM stocks"))
        stock_count = result.scalar()
        
        if stock_count > 0:
            print(f"✅ 数据库已有 {stock_count} 条股票记录，跳过测试数据插入")
            return

        # 插入测试股票
        test_stocks = [
            Stock(symbol='000001.SZ', name='平安银行', sector='金融', industry='银行', market='SZSE'),
            Stock(symbol='000002.SZ', name='万科A', sector='房地产', industry='房地产开发', market='SZSE'),
            Stock(symbol='600000.SH', name='浦发银行', sector='金融', industry='银行', market='SHSE'),
            Stock(symbol='600036.SH', name='招商银行', sector='金融', industry='银行', market='SHSE'),
        ]

        session.add_all(test_stocks)
        await session.commit()
        print(f"✅ 插入 {len(test_stocks)} 条测试股票记录")

        # 插入测试行情数据（最近7天）
        base_price = Decimal('10.0')
        base_time = datetime.utcnow() - timedelta(days=7)

        for stock in test_stocks:
            for i in range(7):
                price = base_price + Decimal(str(i * 0.1))
                volume = 1000000 + i * 100000
                
                price_record = StockPrice(
                    symbol=stock.symbol,
                    price_close=price,
                    price_open=price,
                    price_high=price * Decimal('1.02'),
                    price_low=price * Decimal('0.98'),
                    volume=volume,
                    amount=price * Decimal(str(volume)),
                    timestamp=base_time + timedelta(days=i)
                )
                session.add(price_record)

        await session.commit()
        print(f"✅ 插入 {len(test_stocks) * 7} 条测试行情记录")

    await engine.dispose()


async def verify_database():
    """验证数据库"""
    print("\n🔍 验证数据库...")
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 检查表
        result = await session.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        
        tables = [row[0] for row in result]
        print(f"✅ 数据库包含 {len(tables)} 个表:")
        for table in tables:
            print(f"   - {table}")

    await engine.dispose()


async def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Quant-Trade System - 数据库初始化")
    print("=" * 60)

    try:
        # 1. 创建数据库
        await create_database()

        # 2. 运行迁移
        await run_migrations()

        # 3. 插入测试数据
        await insert_test_data()

        # 4. 验证数据库
        await verify_database()

        print("\n" + "=" * 60)
        print("✅ 数据库初始化完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
