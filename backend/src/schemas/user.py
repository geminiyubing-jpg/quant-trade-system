"""
用户相关的 Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==============================================
# 用户基础 Schema
# ==============================================

class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    is_active: bool = Field(True, description="是否激活")


class UserCreate(UserBase):
    """用户创建 Schema"""
    password: str = Field(..., min_length=8, max_length=100, description="密码")


class UserUpdate(BaseModel):
    """用户更新 Schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """数据库中的用户 Schema"""
    id: str
    password_hash: str
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==============================================
# 用户响应 Schema
# ==============================================

class UserResponse(UserBase):
    """用户响应 Schema（不包含敏感信息）"""
    id: str
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """用户列表响应 Schema"""
    total: int = Field(..., description="总记录数")
    items: list[UserResponse] = Field(..., description="用户列表")


# ==============================================
# 认证 Schema
# ==============================================

class LoginRequest(BaseModel):
    """登录请求 Schema"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应 Schema"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")


class TokenPayload(BaseModel):
    """令牌载荷 Schema"""
    sub: str = Field(..., description="用户 ID")
    exp: Optional[int] = Field(None, description="过期时间")
