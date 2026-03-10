"""
用户 Repository
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .base import BaseRepository
from ..models.user import User


class UserRepository(BaseRepository[User, User, User]):
    """用户 Repository"""

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            用户实例或 None
        """
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        根据邮箱获取用户

        Args:
            db: 数据库会话
            email: 邮箱

        Returns:
            用户实例或 None
        """
        return db.query(User).filter(User.email == email).first()

    def get_by_username_or_email(
        self,
        db: Session,
        *,
        username: str,
        email: str
    ) -> Optional[User]:
        """
        根据用户名或邮箱获取用户

        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱

        Returns:
            用户实例或 None
        """
        return db.query(User).filter(
            or_(User.username == username, User.email == email)
        ).first()

    def get_active_users(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        获取活跃用户列表

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            用户实例列表
        """
        return db.query(User).filter(
            User.is_active == True
        ).offset(skip).limit(limit).all()

    def authenticate(
        self,
        db: Session,
        *,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        验证用户凭据

        Args:
            db: 数据库会话
            username: 用户名
            password: 密码

        Returns:
            用户实例或 None
        """
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        if not user.is_active:
            return None
        return user

    def is_superuser(self, db: Session, *, user_id: str) -> bool:
        """
        检查用户是否是超级用户

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            是否是超级用户
        """
        user = self.get(db, id=user_id)
        if not user:
            return False
        return user.is_superuser
