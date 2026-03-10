"""
Users Endpoint

用户管理端点。
"""

from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_active_user, get_current_superuser
from src.repositories import UserRepository
from src.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from src.models.user import User

router = APIRouter()


def get_user_repository() -> UserRepository:
    """获取用户 Repository"""
    return UserRepository(User)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    创建用户

    Args:
        user_in: 用户创建数据
        db: 数据库会话
        user_repo: 用户 Repository

    Returns:
        创建的用户信息

    Raises:
        HTTPException: 用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    existing_user = user_repo.get_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = user_repo.get_by_email(db, email=user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )

    # 创建用户
    user = user_repo.create(db, obj_in=user_in)
    return user


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    获取用户列表

    Args:
        skip: 跳过记录数
        limit: 返回记录数
        db: 数据库会话
        user_repo: 用户 Repository

    Returns:
        用户列表
    """
    users = user_repo.get_multi(db, skip=skip, limit=limit)
    total = user_repo.count(db)

    return UserListResponse(total=total, items=users)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    获取当前用户信息

    Args:
        current_user: 当前用户

    Returns:
        当前用户信息
    """
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    获取用户详情

    Args:
        user_id: 用户 ID
        db: 数据库会话
        user_repo: 用户 Repository

    Returns:
        用户信息

    Raises:
        HTTPException: 用户不存在
    """
    user = user_repo.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    更新用户信息

    Args:
        user_id: 用户 ID
        user_in: 用户更新数据
        db: 数据库会话
        user_repo: 用户 Repository

    Returns:
        更新后的用户信息

    Raises:
        HTTPException: 用户不存在
    """
    user = user_repo.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 如果更新邮箱，检查是否已存在
    if user_in.email:
        existing_email = user_repo.get_by_email(db, email=user_in.email)
        if existing_email and existing_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

    # 更新用户
    updated_user = user_repo.update(db, db_obj=user, obj_in=user_in)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_superuser)],
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    删除用户（仅超级用户）

    Args:
        user_id: 用户 ID
        db: 数据库会话
        user_repo: 用户 Repository
        current_user: 当前用户（必须是超级用户）

    Raises:
        HTTPException: 用户不存在或权限不足
    """
    user = user_repo.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    user_repo.delete(db, id=user_id)


@router.get("/me/preferences")
async def get_user_preferences(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    获取当前用户偏好设置

    Args:
        current_user: 当前用户

    Returns:
        用户偏好设置（JSON）
    """
    return current_user.preferences or {}


@router.put("/me/preferences")
async def update_user_preferences(
    preferences: dict,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    更新当前用户偏好设置

    Args:
        preferences: 新的偏好设置（JSON）
        current_user: 当前用户
        db: 数据库会话
        user_repo: 用户 Repository

    Returns:
        更新后的用户偏好设置
    """
    # 更新用户偏好设置
    updated_user = user_repo.update(
        db,
        db_obj=current_user,
        obj_in={"preferences": preferences}
    )

    return updated_user.preferences or {}


@router.patch("/me/preferences")
async def patch_user_preferences(
    preferences: dict,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    部分更新当前用户偏好设置（合并而非替换）

    Args:
        preferences: 要更新的偏好设置（JSON）
        current_user: 当前用户
        db: 数据库会话
        user_repo: 用户 Repository

    Returns:
        更新后的用户偏好设置
    """
    # 合并现有偏好设置和新偏好设置
    current_preferences = current_user.preferences or {}
    merged_preferences = {**current_preferences, **preferences}

    # 更新用户偏好设置
    updated_user = user_repo.update(
        db,
        db_obj=current_user,
        obj_in={"preferences": merged_preferences}
    )

    return updated_user.preferences or {}
