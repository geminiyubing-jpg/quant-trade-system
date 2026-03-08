"""
==============================================
QuantAI Ecosystem - 认证端点
==============================================

提供用户登录、登出和令牌刷新功能。
"""

from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
)
from src.repositories.user import UserRepository
from src.schemas.user import LoginRequest, LoginResponse, UserResponse
from src.models.user import User


router = APIRouter()


def get_user_repository() -> UserRepository:
    """获取用户 Repository"""
    return UserRepository(User)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    login_in: LoginRequest,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    用户登录

    Args:
        login_in: 登录请求（用户名/邮箱 + 密码）
        db: 数据库会话
        user_repo: 用户 Repository

    Returns:
        LoginResponse: 访问令牌和用户信息

    Raises:
        HTTPException: 认证失败（用户名或密码错误）
    """
    # 1. 验证用户凭据
    user = user_repo.authenticate(
        db,
        username=login_in.username,
        password=login_in.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. 生成访问令牌
    access_token = create_access_token(subject=str(user.id))

    # 3. 生成刷新令牌（可选，用于后续实现刷新令牌功能）
    refresh_token = create_refresh_token(subject=str(user.id))

    # 4. 返回令牌和用户信息
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    用户登出

    Args:
        current_user: 当前用户

    Returns:
        None

    Note:
        在无状态的 JWT 认证中，登出通常在客户端处理（删除 token）。
        如果需要服务端登出，可以使用 Redis 黑名单机制。
    """
    # 客户端删除 token 即可
    # 如需实现服务端 token 黑名单，可以在这里添加逻辑
    return None


@router.post("/refresh", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    刷新访问令牌

    Args:
        refresh_token: 刷新令牌
        db: 数据库会话
        user_repo: 用户 Repository

    Returns:
        LoginResponse: 新的访问令牌和用户信息

    Raises:
        HTTPException: 刷新令牌无效或用户不存在
    """
    from src.core.security import decode_token

    # 1. 解码刷新令牌
    try:
        token_payload = decode_token(refresh_token)

        # 验证这是刷新令牌
        if token_payload.exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}"
        )

    # 2. 从数据库获取用户
    from uuid import UUID

    try:
        user_id = UUID(token_payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )

    user = user_repo.get(db, id=str(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # 3. 生成新的访问令牌
    access_token = create_access_token(subject=str(user.id))

    # 4. 返回新令牌和用户信息
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    获取当前用户信息

    Args:
        current_user: 当前用户

    Returns:
        UserResponse: 当前用户信息
    """
    return UserResponse.model_validate(current_user)
