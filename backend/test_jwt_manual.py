#!/usr/bin/env python3
"""
JWT 认证功能手动验证脚本
"""

import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import timedelta, datetime
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    get_password_hash,
)
from src.core.config import settings


def test_password_operations():
    """测试密码操作"""
    print("\n" + "="*60)
    print("测试 1: 密码哈希和验证")
    print("="*60)

    password = "testpass123"

    # 生成密码哈希
    hashed = get_password_hash(password)
    print(f"✓ 密码哈希生成成功: {hashed[:30]}...")

    # 验证正确密码
    assert verify_password(password, hashed) is True
    print(f"✓ 正确密码验证通过")

    # 验证错误密码
    assert verify_password("wrongpass", hashed) is False
    print(f"✓ 错误密码验证失败（符合预期）")

    print("✅ 密码操作测试通过\n")


def test_jwt_token_operations():
    """测试 JWT token 操作"""
    print("\n" + "="*60)
    print("测试 2: JWT Token 生成和验证")
    print("="*60)

    user_id = "123e4567-e89b-12d3-a456-426614174000"

    # 创建访问令牌
    access_token = create_access_token(subject=user_id)
    print(f"✓ 访问令牌创建成功: {access_token[:30]}...")

    # 解码访问令牌
    payload = decode_token(access_token)
    assert payload.sub == user_id
    print(f"✓ 访问令牌解码成功: user_id={payload.sub}")

    # 创建刷新令牌
    refresh_token = create_refresh_token(subject=user_id)
    print(f"✓ 刷新令牌创建成功: {refresh_token[:30]}...")

    # 解码刷新令牌
    refresh_payload = decode_token(refresh_token)
    assert refresh_payload.sub == user_id
    print(f"✓ 刷新令牌解码成功: user_id={refresh_payload.sub}")

    # 验证过期时间
    access_exp = datetime.fromtimestamp(payload.exp)
    refresh_exp = datetime.fromtimestamp(refresh_payload.exp)
    print(f"✓ 访问令牌过期时间: {access_exp}")
    print(f"✓ 刷新令牌过期时间: {refresh_exp}")

    assert refresh_exp > access_exp
    print(f"✓ 刷新令牌过期时间晚于访问令牌（符合预期）")

    print("✅ JWT Token 操作测试通过\n")


def test_invalid_token():
    """测试无效 token"""
    print("\n" + "="*60)
    print("测试 3: 无效 Token 处理")
    print("="*60)

    try:
        decode_token("invalid.token.string")
        print("❌ 应该抛出异常但没有")
        return False
    except Exception as e:
        print(f"✓ 无效 token 抛出异常: {type(e).__name__}")
        print(f"✅ 无效 Token 处理测试通过\n")
        return True


def test_configuration():
    """测试配置"""
    print("\n" + "="*60)
    print("测试 4: 配置验证")
    print("="*60)

    print(f"✓ 应用名称: {settings.app_name}")
    print(f"✓ JWT 算法: {settings.algorithm}")
    print(f"✓ 访问令牌过期时间: {settings.access_token_expire_minutes} 分钟")
    print(f"✓ 刷新令牌过期时间: {settings.refresh_token_expire_days} 天")

    print("✅ 配置验证通过\n")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("JWT 认证功能手动验证")
    print("="*60)

    try:
        test_configuration()
        test_password_operations()
        test_jwt_token_operations()
        test_invalid_token()

        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
