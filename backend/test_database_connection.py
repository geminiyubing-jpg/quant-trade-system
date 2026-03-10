#!/usr/bin/env python3
"""
数据库连接验证脚本
"""

import sys
import os
import uuid

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import date
from decimal import Decimal

from src.core.database import engine, SessionLocal, check_db_connection, Base
from src.models.user import User
from src.models.trading import Order, Position
from src.repositories.user import UserRepository
from src.core.security import get_password_hash


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "="*60)
    print("数据库连接测试")
    print("="*60)

    # 1. 测试基本连接
    print("\n1. 测试基本连接...")
    if check_db_connection():
        print("✅ 数据库连接成功")
    else:
        print("❌ 数据库连接失败")
        return False

    # 2. 测试 SQLAlchemy Engine
    print("\n2. 测试 SQLAlchemy Engine...")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ Engine 连接成功")
            print(f"   数据库版本: {version[0]}")
    except Exception as e:
        print(f"❌ Engine 连接失败: {e}")
        return False

    # 3. 测试 Session 创建
    print("\n3. 测试 Session 创建...")
    try:
        db = SessionLocal()
        print("✅ Session 创建成功")
        db.close()
    except Exception as e:
        print(f"❌ Session 创建失败: {e}")
        return False

    return True


def test_crud_operations():
    """测试 CRUD 操作"""
    print("\n" + "="*60)
    print("CRUD 操作测试")
    print("="*60)

    db = SessionLocal()
    user_repo = UserRepository(User)

    try:
        # 1. 创建测试用户
        print("\n1. 测试创建用户...")
        test_user_data = {
            "id": str(uuid.uuid4()),  # 手动生成 ID
            "username": "db_test_user",
            "email": "dbtest@example.com",
            "hashed_password": get_password_hash("testpass123"),  # 使用哈希后的密码
            "full_name": "Database Test User",
            "is_active": True,
            "is_superuser": False,
            "role": "user",
            "preferences": {}
        }

        # 检查用户是否已存在
        existing_user = user_repo.get_by_username(db, username=test_user_data["username"])
        if existing_user:
            print(f"✅ 测试用户已存在: {existing_user.username}")
            test_user = existing_user
        else:
            test_user = user_repo.create(db, obj_in=test_user_data)
            db.commit()
            print(f"✅ 用户创建成功: {test_user.username}")

        # 2. 测试读取用户
        print("\n2. 测试读取用户...")
        user = user_repo.get(db, id=str(test_user.id))
        if user:
            print(f"✅ 用户读取成功: {user.username}")
        else:
            print("❌ 用户读取失败")
            return False

        # 3. 测试更新用户
        print("\n3. 测试更新用户...")
        updated_user = user_repo.update(
            db,
            db_obj=test_user,
            obj_in={"full_name": "Updated Name"}
        )
        db.commit()
        print(f"✅ 用户更新成功: {updated_user.full_name}")

        # 4. 测试创建订单
        print("\n4. 测试创建订单...")
        from src.repositories.trading import OrderRepository
        order_repo = OrderRepository(Order)

        order_data = {
            "user_id": str(test_user.id),
            "symbol": "000001.SZ",
            "side": "BUY",
            "quantity": 100,
            "price": Decimal("10.50"),
            "execution_mode": "PAPER"
        }

        order = order_repo.create(db, obj_in=order_data)
        db.commit()
        print(f"✅ 订单创建成功: {order.symbol} {order.side} {order.quantity}股")

        # 5. 测试查询订单
        print("\n5. 测试查询订单...")
        orders = order_repo.get_user_orders(
            db,
            user_id=str(test_user.id),
            execution_mode="PAPER"
        )
        print(f"✅ 订单查询成功: 找到 {len(orders)} 个订单")

        # 6. 清理测试数据
        print("\n6. 清理测试数据...")
        order_repo.delete(db, id=order.id)
        db.commit()
        print("✅ 测试订单已删除")

        # 不删除测试用户，保留用于后续测试
        print("✅ 测试用户已保留")

        return True

    except Exception as e:
        print(f"❌ CRUD 操作失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


def test_performance():
    """测试数据库性能"""
    print("\n" + "="*60)
    print("数据库性能测试")
    print("="*60)

    import time

    db = SessionLocal()

    try:
        # 1. 测试查询性能
        print("\n1. 测试查询性能...")
        start_time = time.time()

        users = db.query(User).limit(100).all()

        elapsed_time = time.time() - start_time
        print(f"✅ 查询 {len(users)} 个用户耗时: {elapsed_time:.3f}秒")
        print(f"   平均每个用户: {elapsed_time/len(users)*1000:.2f}毫秒")

        # 2. 测试批量插入性能
        print("\n2. 测试批量插入性能...")
        from src.models.trading import Order

        start_time = time.time()

        # 创建测试用户
        test_user_data = {
            "username": "perf_test_user",
            "email": "perftest@example.com",
            "password": "testpass123",
            "full_name": "Performance Test User",
            "is_active": True
        }

        user_repo = UserRepository(User)
        test_user = user_repo.create(db, obj_in=test_user_data)
        db.commit()

        # 批量创建订单
        orders_to_create = []
        for i in range(10):
            order_data = {
                "user_id": str(test_user.id),
                "symbol": f"00000{i % 3}.SZ",
                "side": "BUY" if i % 2 == 0 else "SELL",
                "quantity": 100 + i * 10,
                "price": Decimal("10.50") + Decimal(str(i)),
                "execution_mode": "PAPER"
            }
            orders_to_create.append(order_data)

        start_time = time.time()

        for order_data in orders_to_create:
            order = Order(**order_data)
            db.add(order)

        db.commit()

        elapsed_time = time.time() - start_time
        print(f"✅ 插入 {len(orders_to_create)} 个订单耗时: {elapsed_time:.3f}秒")
        print(f"   平均每个订单: {elapsed_time/len(orders_to_create)*1000:.2f}毫秒")

        # 清理测试数据
        print("\n3. 清理测试数据...")
        db.query(Order).filter(Order.user_id == str(test_user.id)).delete()
        db.query(User).filter(User.id == test_user.id).delete()
        db.commit()
        print("✅ 测试数据已清理")

        # 性能基准
        print("\n性能基准:")
        print(f"  查询性能: {'✅ 优秀' if elapsed_time/len(users)*1000 < 10 else '⚠️ 需要优化'}")
        print(f"  插入性能: {'✅ 优秀' if elapsed_time/len(orders_to_create)*1000 < 50 else '⚠️ 需要优化'}")

        return True

    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


def test_transaction_rollback():
    """测试事务回滚"""
    print("\n" + "="*60)
    print("事务回滚测试")
    print("="*60)

    db = SessionLocal()
    user_repo = UserRepository(User)

    try:
        # 1. 创建测试用户
        print("\n1. 创建测试用户...")
        test_user_data = {
            "username": "rollback_test_user",
            "email": "rollback@example.com",
            "password": "testpass123",
            "full_name": "Rollback Test User",
            "is_active": True
        }

        test_user = user_repo.create(db, obj_in=test_user_data)
        db.commit()
        user_id = str(test_user.id)
        print(f"✅ 用户创建成功: {test_user.username} (ID: {user_id})")

        # 2. 测试事务回滚
        print("\n2. 测试事务回滚...")
        try:
            # 尝试创建重复用户（应该失败）
            duplicate_user = user_repo.create(db, obj_in=test_user_data)
            db.commit()
            print("❌ 事务回滚测试失败：应该抛出异常")
            return False
        except Exception as e:
            db.rollback()
            print(f"✅ 事务回滚成功: {str(e)[:50]}")

        # 3. 验证数据未回滚（只有重复用户的插入被回滚）
        print("\n3. 验证原始数据...")
        user = user_repo.get(db, id=user_id)
        if user:
            print(f"✅ 原始用户数据正常: {user.username}")
        else:
            print("❌ 原始用户数据丢失")
            return False

        # 4. 清理测试数据
        print("\n4. 清理测试数据...")
        user_repo.delete(db, id=user_id)
        db.commit()
        print("✅ 测试数据已清理")

        return True

    except Exception as e:
        print(f"❌ 事务回滚测试失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("数据库连接和功能验证")
    print("="*60)

    all_passed = True

    # 测试 1: 数据库连接
    if not test_database_connection():
        all_passed = False

    # 测试 2: CRUD 操作
    if not test_crud_operations():
        all_passed = False

    # 测试 3: 性能测试
    if not test_performance():
        all_passed = False

    # 测试 4: 事务回滚
    if not test_transaction_rollback():
        all_passed = False

    # 总结
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有测试通过！")
        print("="*60)
        return 0
    else:
        print("❌ 部分测试失败")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
