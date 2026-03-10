"""
==============================================
QuantAI Ecosystem - JWT 认证测试
==============================================

测试 JWT token 生成、验证和用户认证功能。
"""

import pytest
from datetime import timedelta, datetime
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    get_password_hash,
    get_current_user,
)
from src.core.config import settings
from src.models.user import User


# ==============================================
# Fixtures
# ==============================================

@pytest.fixture
def test_user():
    """测试用户数据"""
    return User(
        id="123e4567-e89b-12d3-a456-426614174000",
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )


@pytest.fixture
def test_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    return db


# ==============================================
# 密码操作测试
# ==============================================

class TestPasswordOperations:
    """测试密码哈希和验证"""

    def test_get_password_hash(self):
        """测试生成密码哈希"""
        password = "testpass123"
        hashed = get_password_hash(password)

        # 验证哈希不为空
        assert hashed is not None
        assert len(hashed) > 0

        # 验证哈希不等于明文密码
        assert hashed != password

        # 验证哈希是 bcrypt 格式（以 $2b$ 开头）
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """测试验证正确的密码"""
        password = "testpass123"
        hashed = get_password_hash(password)

        # 验证正确密码
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试验证错误的密码"""
        password = "testpass123"
        wrong_password = "wrongpass456"
        hashed = get_password_hash(password)

        # 验证错误密码
        assert verify_password(wrong_password, hashed) is False


# ==============================================
# JWT Token 操作测试
# ==============================================

class TestJWTTokenOperations:
    """测试 JWT token 生成和验证"""

    def test_create_access_token_default_expiry(self):
        """测试创建访问令牌（默认过期时间）"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(subject=user_id)

        # 验证 token 不为空
        assert token is not None
        assert len(token) > 0

        # 验证 token 可以解码
        payload = decode_token(token)
        assert payload.sub == user_id
        assert payload.exp is not None

    def test_create_access_token_custom_expiry(self):
        """测试创建访问令牌（自定义过期时间）"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        expires_delta = timedelta(minutes=60)
        token = create_access_token(subject=user_id, expires_delta=expires_delta)

        # 验证 token 可以解码
        payload = decode_token(token)
        assert payload.sub == user_id
        assert payload.exp is not None

        # 验证过期时间大约在 60 分钟后
        exp_datetime = datetime.fromtimestamp(payload.exp)
        now = datetime.utcnow()
        diff = exp_datetime - now
        assert timedelta(minutes=59) < diff <= timedelta(minutes=61)

    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_refresh_token(subject=user_id)

        # 验证 token 可以解码
        payload = decode_token(token)
        assert payload.sub == user_id
        assert payload.exp is not None

        # 验证刷新令牌的过期时间更长（7天）
        exp_datetime = datetime.fromtimestamp(payload.exp)
        now = datetime.utcnow()
        diff = exp_datetime - now
        assert timedelta(days=6) < diff <= timedelta(days=8)

    def test_decode_token_valid(self):
        """测试解码有效的 token"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(subject=user_id)

        # 验证可以解码
        payload = decode_token(token)
        assert payload.sub == user_id
        assert payload.exp is not None

    def test_decode_token_invalid(self):
        """测试解码无效的 token"""
        invalid_token = "invalid.token.string"

        # 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            decode_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_decode_token_expired(self):
        """测试解码过期的 token"""
        from jose import jwt

        # 创建一个已过期的 token
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        expire = datetime.utcnow() - timedelta(minutes=1)
        payload = {
            "sub": user_id,
            "exp": expire
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

        # 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)

        assert exc_info.value.status_code == 401


# ==============================================
# 用户认证依赖测试
# ==============================================

class TestGetCurrentUser:
    """测试 get_current_user 依赖"""

    def test_get_current_user_no_token(self, test_db):
        """测试没有提供 token 的情况"""
        # 没有 token
        credentials = None

        # 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_db)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    def test_get_current_user_invalid_token(self, test_db):
        """测试无效 token 的情况"""
        # 创建无效的 credentials
        credentials = Mock()
        credentials.credentials = "invalid.token.string"

        # 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_db)

        assert exc_info.value.status_code == 401

    def test_get_current_user_user_not_found(self, test_db):
        """测试用户不存在的情况"""
        # 创建有效的 token
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(subject=user_id)

        credentials = Mock()
        credentials.credentials = token

        # 模拟数据库查询返回 None
        with patch.object(test_db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None

            # 验证抛出异常
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials, test_db)

            assert exc_info.value.status_code == 401
            assert "User not found" in exc_info.value.detail

    def test_get_current_user_inactive(self, test_db, test_user):
        """测试用户未激活的情况"""
        # 设置用户为未激活
        test_user.is_active = False

        # 创建有效的 token
        token = create_access_token(subject=str(test_user.id))

        credentials = Mock()
        credentials.credentials = token

        # 模拟数据库查询返回未激活的用户
        with patch.object(test_db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = test_user

            # 验证抛出异常
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials, test_db)

            assert exc_info.value.status_code == 403
            assert "Inactive user" in exc_info.value.detail

    def test_get_current_user_success(self, test_db, test_user):
        """测试成功获取当前用户"""
        # 创建有效的 token
        token = create_access_token(subject=str(test_user.id))

        credentials = Mock()
        credentials.credentials = token

        # 模拟数据库查询返回用户
        with patch.object(test_db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = test_user

            # 验证返回用户
            user = get_current_user(credentials, test_db)
            assert user == test_user


# ==============================================
# 集成测试
# ==============================================

class TestAuthIntegration:
    """认证集成测试"""

    def test_complete_auth_flow(self):
        """测试完整的认证流程"""
        # 1. 创建用户密码哈希
        password = "testpass123"
        hashed = get_password_hash(password)

        # 2. 验证密码
        assert verify_password(password, hashed) is True

        # 3. 创建访问令牌
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        access_token = create_access_token(subject=user_id)
        assert access_token is not None

        # 4. 创建刷新令牌
        refresh_token = create_refresh_token(subject=user_id)
        assert refresh_token is not None

        # 5. 解码访问令牌
        payload = decode_token(access_token)
        assert payload.sub == user_id

        # 6. 解码刷新令牌
        refresh_payload = decode_token(refresh_token)
        assert refresh_payload.sub == user_id

        # 7. 验证刷新令牌的过期时间更长
        access_exp = datetime.fromtimestamp(payload.exp)
        refresh_exp = datetime.fromtimestamp(refresh_payload.exp)
        assert refresh_exp > access_exp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
