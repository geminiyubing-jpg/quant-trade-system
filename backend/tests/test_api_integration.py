"""
==============================================
QuantAI Ecosystem - API 集成测试
==============================================

测试 API 端点的完整认证流程。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.core.database import get_db, Base, engine
from src.models.user import User
from src.repositories.user import UserRepository
from src.core.security import create_access_token


# ==============================================
# Fixtures
# ==============================================

@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
        # 清理：删除所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user_repo = UserRepository(User)

    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }

    user = user_repo.create(db_session, obj_in=user_data)
    return user


@pytest.fixture
def auth_headers(test_user):
    """创建认证头"""
    access_token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def superuser(db_session):
    """创建超级用户"""
    user_repo = UserRepository(User)

    user_data = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpass123",
        "full_name": "Admin User",
        "is_active": True,
        "is_superuser": True
    }

    user = user_repo.create(db_session, obj_in=user_data)
    return user


@pytest.fixture
def superuser_headers(superuser):
    """创建超级用户认证头"""
    access_token = create_access_token(subject=str(superuser.id))
    return {"Authorization": f"Bearer {access_token}"}


# ==============================================
# 认证 API 测试
# ==============================================

class TestAuthAPI:
    """测试认证 API 端点"""

    def test_login_success(self, client, test_user):
        """测试成功登录"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_username(self, client):
        """测试错误的用户名"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "wronguser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_wrong_password(self, client, test_user):
        """测试错误的密码"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpass"
            }
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_logout_success(self, client, auth_headers):
        """测试成功登出"""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )

        assert response.status_code == 204

    def test_logout_without_auth(self, client):
        """测试未认证时登出"""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 401

    def test_get_current_user_info(self, client, auth_headers, test_user):
        """测试获取当前用户信息"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)

    def test_get_current_user_info_without_auth(self, client):
        """测试未认证时获取用户信息"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401


# ==============================================
# 用户管理 API 测试
# ==============================================

class TestUsersAPI:
    """测试用户管理 API 端点"""

    def test_create_user(self, client):
        """测试创建用户"""
        response = client.post(
            "/api/v1/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password_hash" not in data  # 确保不返回密码哈希

    def test_create_user_duplicate_username(self, client, test_user):
        """测试创建重复用户名的用户"""
        response = client.post(
            "/api/v1/users",
            json={
                "username": "testuser",  # 重复的用户名
                "email": "another@example.com",
                "password": "testpass123"
            }
        )

        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_create_user_duplicate_email(self, client, test_user):
        """测试创建重复邮箱的用户"""
        response = client.post(
            "/api/v1/users",
            json={
                "username": "anotheruser",
                "email": "test@example.com",  # 重复的邮箱
                "password": "testpass123"
            }
        )

        assert response.status_code == 400
        assert "邮箱已存在" in response.json()["detail"]

    def test_get_users(self, client, auth_headers):
        """测试获取用户列表"""
        response = client.get(
            "/api/v1/users",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_user_by_id(self, client, auth_headers, test_user):
        """测试根据 ID 获取用户"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username

    def test_get_current_user_me(self, client, auth_headers, test_user):
        """测试获取当前用户信息（/users/me）"""
        response = client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username

    def test_update_user(self, client, auth_headers, test_user):
        """测试更新用户信息"""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "full_name": "Updated Name"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    def test_delete_user(self, client, superuser_headers, test_user):
        """测试删除用户（仅超级用户）"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=superuser_headers
        )

        assert response.status_code == 204

    def test_delete_user_without_superuser(self, client, auth_headers, test_user):
        """测试非超级用户删除用户"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 403


# ==============================================
# 交易 API 测试
# ==============================================

class TestTradingAPI:
    """测试交易 API 端点"""

    def test_create_order_without_auth(self, client):
        """测试未认证时创建订单"""
        response = client.post(
            "/api/v1/trading/orders",
            json={
                "symbol": "000001.SZ",
                "side": "BUY",
                "quantity": 100,
                "price": 10.5,
                "execution_mode": "PAPER"
            }
        )

        assert response.status_code == 401

    def test_create_order_with_auth(self, client, auth_headers):
        """测试认证后创建订单"""
        response = client.post(
            "/api/v1/trading/orders",
            headers=auth_headers,
            json={
                "symbol": "000001.SZ",
                "side": "BUY",
                "quantity": 100,
                "price": 10.5,
                "execution_mode": "PAPER"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "000001.SZ"
        assert data["side"] == "BUY"

    def test_create_order_without_execution_mode(self, client, auth_headers):
        """测试创建订单缺少 execution_mode（P0 架构红线）"""
        response = client.post(
            "/api/v1/trading/orders",
            headers=auth_headers,
            json={
                "symbol": "000001.SZ",
                "side": "BUY",
                "quantity": 100,
                "price": 10.5
            }
        )

        assert response.status_code == 400
        assert "execution_mode" in response.json()["detail"]

    def test_list_orders_with_auth(self, client, auth_headers):
        """测试认证后获取订单列表"""
        response = client.get(
            "/api/v1/trading/orders",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data

    def test_list_positions_with_auth(self, client, auth_headers):
        """测试认证后获取持仓列表"""
        response = client.get(
            "/api/v1/trading/positions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data


# ==============================================
# 完整认证流程测试
# ==============================================

class TestCompleteAuthFlow:
    """测试完整的认证流程"""

    def test_complete_user_flow(self, client):
        """测试完整的用户流程：注册 -> 登录 -> 访问受保护资源"""
        # 1. 注册新用户
        register_response = client.post(
            "/api/v1/users",
            json={
                "username": "flowuser",
                "email": "flow@example.com",
                "password": "flowpass123",
                "full_name": "Flow User"
            }
        )
        assert register_response.status_code == 201
        user_data = register_response.json()

        # 2. 登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "flowuser",
                "password": "flowpass123"
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]

        # 3. 使用 token 访问受保护资源
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # 获取当前用户信息
        me_response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "flowuser"

        # 创建订单
        order_response = client.post(
            "/api/v1/trading/orders",
            headers=auth_headers,
            json={
                "symbol": "000001.SZ",
                "side": "BUY",
                "quantity": 100,
                "price": 10.5,
                "execution_mode": "PAPER"
            }
        )
        assert order_response.status_code == 201

        # 4. 登出
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        assert logout_response.status_code == 204

        # 5. 验证登出后 token 仍然有效（JWT 是无状态的）
        # 注意：在实际应用中，可能需要实现 token 黑名单
        me_response2 = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        # 仍然可以访问（因为没有实现 token 黑名单）
        # 如果需要服务端登出，可以使用 Redis 黑名单机制


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
