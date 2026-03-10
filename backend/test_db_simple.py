#!/usr/bin/env python3
"""
简化的数据库连接测试 - 专注于核心功能
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.database import engine, SessionLocal, check_db_connection
from src.models.user import User
from src.repositories.user import UserRepository
from src.core.security import get_password_hash, verify_password


def test_basic_connection():
    """测试基本连接"""
    print("\n" + "="*60)
    print("1. 数据库连接测试")
    print("="*60)

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ 数据库连接成功")
            print(f"   版本: {version[0][:50]}...")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_user_operations():
    """测试用户操作"""
    print("\n" + "="*60)
    print("2. 用户 CRUD 操作测试")
    print("="*60)

    db = SessionLocal()
    user_repo = UserRepository(User)

    try:
        # 1. 创建用户
        print("\n   [1/4] 创建用户...")
        test_user_data = {
            "id": str(uuid.uuid4()),
            "username": "test_user",
            "email": "test@example.com",
            "hashed_password": get_password_hash("testpass123"),
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False,
            "role": "user",
            "preferences": {}
        }

        # 检查是否已存在
        existing = user_repo.get_by_username(db, username="test_user")
        if existing:
            print(f"   ✅ 用户已存在: {existing.username}")
            test_user = existing
        else:
            test_user = user_repo.create(db, obj_in=test_user_data)
            db.commit()
            print(f"   ✅ 用户创建成功: {test_user.username}")

        # 2. 读取用户
        print("\n   [2/4] 读取用户...")
        user = user_repo.get(db, id=test_user.id)
        if user:
            print(f"   ✅ 用户读取成功: {user.username} ({user.email})")
        else:
            print("   ❌ 用户读取失败")
            return False

        # 3. 验证密码
        print("\n   [3/4] 验证密码...")
        if test_user.verify_password("testpass123"):
            print(f"   ✅ 密码验证成功")
        else:
            print("   ❌ 密码验证失败")
            return False

        # 4. 更新用户
        print("\n   [4/4] 更新用户...")
        updated = user_repo.update(
            db,
            db_obj=test_user,
            obj_in={"full_name": "Updated Test User"}
        )
        db.commit()
        print(f"   ✅ 用户更新成功: {updated.full_name}")

        return True

    except Exception as e:
        print(f"   ❌ 操作失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_password_functions():
    """测试密码哈希函数"""
    print("\n" + "="*60)
    print("3. 密码哈希功能测试")
    print("="*60)

    try:
        # 1. 测试密码哈希
        print("\n   [1/2] 生成密码哈希...")
        password = "test123"
        hashed = get_password_hash(password)
        print(f"   ✅ 哈希生成成功: {hashed[:50]}...")

        # 2. 测试密码验证
        print("\n   [2/2] 验证密码...")
        if verify_password(password, hashed):
            print("   ✅ 密码验证成功")
        else:
            print("   ❌ 密码验证失败")
            return False

        # 3. 测试错误密码
        print("\n   [3/3] 测试错误密码...")
        if not verify_password("wrongpass", hashed):
            print("   ✅ 错误密码正确拒绝")
        else:
            print("   ❌ 错误密码未正确拒绝")
            return False

        return True

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


def test_table_exists():
    """测试关键表是否存在"""
    print("\n" + "="*60)
    print("4. 数据库表结构检查")
    print("="*60)

    critical_tables = [
        'users',
        'strategies',
        'orders',
        'positions',
        'backtest_jobs',
        'backtest_results',
        'refresh_tokens',
        'system_config'
    ]

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """))
            existing_tables = {row[0] for row in result.fetchall()}

        print("\n   关键表检查:")
        all_exist = True
        for table in critical_tables:
            exists = table in existing_tables
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
            if not exists:
                all_exist = False

        print(f"\n   总表数: {len(existing_tables)}")

        return all_exist

    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("QuantAI Ecosystem - 数据库功能验证")
    print("="*60)

    results = []

    # 运行测试
    results.append(("数据库连接", test_basic_connection()))
    results.append(("用户操作", test_user_operations()))
    results.append(("密码功能", test_password_functions()))
    results.append(("表结构", test_table_exists()))

    # 输出结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "="*60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("="*60)

    if failed == 0:
        print("\n🎉 所有测试通过！数据库连接正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查日志。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
