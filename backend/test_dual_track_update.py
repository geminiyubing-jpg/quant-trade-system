#!/usr/bin/env python3
"""
测试双轨代码更新
验证 Model 和 Repository 的双轨隔离功能
"""

import sys
import os

# 切换到 backend 目录
os.chdir('/Users/yubing/quant-trade-system/backend')
sys.path.insert(0, '/Users/yubing/quant-trade-system/backend')

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

from src.models.trading import Order, Position
from src.models.user import User
from src.repositories.trading import OrderRepository, PositionRepository


def test_order_model_fields():
    """测试 Order Model 是否有新字段"""
    print("=" * 60)
    print("测试 1: Order Model 字段")
    print("=" * 60)

    # 检查 Order 是否有 user_id 和 execution_mode
    order_attrs = Order.__table__.columns.keys()
    print(f"Order 表字段: {list(order_attrs)}")

    assert 'user_id' in order_attrs, "❌ Order 缺少 user_id 字段"
    assert 'execution_mode' in order_attrs, "❌ Order 缺少 execution_mode 字段"
    print("✅ Order Model 包含 user_id 和 execution_mode 字段")
    print()


def test_position_model_fields():
    """测试 Position Model 是否有新字段"""
    print("=" * 60)
    print("测试 2: Position Model 字段")
    print("=" * 60)

    # 检查 Position 是否有 user_id 和 execution_mode
    position_attrs = Position.__table__.columns.keys()
    print(f"Position 表字段: {list(position_attrs)}")

    assert 'user_id' in position_attrs, "❌ Position 缺少 user_id 字段"
    assert 'execution_mode' in position_attrs, "❌ Position 缺少 execution_mode 字段"
    print("✅ Position Model 包含 user_id 和 execution_mode 字段")
    print()


def test_user_model_relationships():
    """测试 User Model 是否恢复了关联"""
    print("=" * 60)
    print("测试 3: User Model 关联")
    print("=" * 60)

    # 检查 User 是否有 orders 和 positions 关联
    user_relationships = [rel.key for rel in User.__mapper__.relationships]
    print(f"User 关联: {user_relationships}")

    assert 'orders' in user_relationships, "❌ User 缺少 orders 关联"
    assert 'positions' in user_relationships, "❌ User 缺少 positions 关联"
    print("✅ User Model 包含 orders 和 positions 关联")
    print()


def test_order_repository():
    """测试 OrderRepository 是否启用了双轨过滤"""
    print("=" * 60)
    print("测试 4: OrderRepository 双轨过滤")
    print("=" * 60)

    from src.core.database import get_db

    db = next(get_db())
    order_repo = OrderRepository(Order)

    try:
        # 测试获取用户订单（应该使用双轨过滤）
        # 注意：这里只是验证方法可以调用，实际数据可能为空
        orders = order_repo.get_user_orders(
            db,
            user_id="test_user_123",
            execution_mode="PAPER",
            skip=0,
            limit=10
        )
        print(f"✅ OrderRepository.get_user_orders() 调用成功，返回 {len(orders)} 条记录")

        # 测试获取待成交订单
        pending_orders = order_repo.get_pending_orders(
            db,
            user_id="test_user_123",
            execution_mode="PAPER"
        )
        print(f"✅ OrderRepository.get_pending_orders() 调用成功，返回 {len(pending_orders)} 条记录")

    except Exception as e:
        print(f"❌ OrderRepository 测试失败: {e}")
        raise
    finally:
        db.close()

    print()


def test_position_repository():
    """测试 PositionRepository 是否启用了双轨过滤"""
    print("=" * 60)
    print("测试 5: PositionRepository 双轨过滤")
    print("=" * 60)

    from src.core.database import get_db

    db = next(get_db())
    position_repo = PositionRepository(Position)

    try:
        # 测试获取用户持仓（应该使用双轨过滤）
        positions = position_repo.get_user_positions(
            db,
            user_id="test_user_123",
            execution_mode="PAPER",
            skip=0,
            limit=10
        )
        print(f"✅ PositionRepository.get_user_positions() 调用成功，返回 {len(positions)} 条记录")

        # 测试获取特定股票持仓
        position = position_repo.get_position_by_symbol(
            db,
            user_id="test_user_123",
            symbol="000001.SZ",
            execution_mode="PAPER"
        )
        print(f"✅ PositionRepository.get_position_by_symbol() 调用成功，返回: {position}")

    except Exception as e:
        print(f"❌ PositionRepository 测试失败: {e}")
        raise
    finally:
        db.close()

    print()


def test_database_schema():
    """测试数据库 schema 是否有索引"""
    print("=" * 60)
    print("测试 6: 数据库索引")
    print("=" * 60)

    from sqlalchemy import inspect
    from src.core.database import engine

    inspector = inspect(engine)

    # 检查 orders 表索引
    orders_indexes = inspector.get_indexes('orders')
    orders_index_names = [idx['name'] for idx in orders_indexes]
    print(f"Orders 表索引: {orders_index_names}")

    assert 'idx_orders_user_mode' in orders_index_names, "❌ Orders 缺少 idx_orders_user_mode 复合索引"
    print("✅ Orders 表包含 idx_orders_user_mode 复合索引")

    # 检查 positions 表索引
    positions_indexes = inspector.get_indexes('positions')
    positions_index_names = [idx['name'] for idx in positions_indexes]
    print(f"Positions 表索引: {positions_index_names}")

    assert 'idx_positions_user_mode' in positions_index_names, "❌ Positions 缺少 idx_positions_user_mode 复合索引"
    print("✅ Positions 表包含 idx_positions_user_mode 复合索引")

    print()


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 双轨代码更新测试")
    print("=" * 60 + "\n")

    try:
        # 1. 测试 Model 字段
        test_order_model_fields()
        test_position_model_fields()

        # 2. 测试 Model 关联
        test_user_model_relationships()

        # 3. 测试数据库 schema
        test_database_schema()

        # 4. 测试 Repository 方法
        test_order_repository()
        test_position_repository()

        print("=" * 60)
        print("✅ 所有测试通过！双轨代码更新成功！")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
