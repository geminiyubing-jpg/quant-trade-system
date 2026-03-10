"""
UserSettings Repository

用户设置数据访问层。
"""

from typing import Optional
from sqlalchemy.orm import Session

from src.models.user_settings import UserSettings
from src.models.user import User


class UserSettingsRepository:
    """用户设置 Repository"""

    def __init__(self, model: type[UserSettings] = UserSettings):
        self.model = model

    def get_by_user(self, db: Session, user_id: str) -> Optional[UserSettings]:
        """
        获取用户设置

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户设置对象，不存在则返回 None
        """
        return db.query(self.model).filter(self.model.user_id == user_id).first()

    def get_or_create(self, db: Session, user_id: str) -> UserSettings:
        """
        获取或创建用户设置

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户设置对象
        """
        settings = self.get_by_user(db, user_id)
        if not settings:
            settings = self.model(
                user_id=user_id,
                trading_mode="PAPER",
                live_trading_enabled=False,
                risk_control_enabled=True,
                notifications_enabled=True,
                notification_email=True,
                notification_sms=False,
                language='zh_CN',
                theme='light',
                preferences={}
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return settings

    def update_trading_mode(
        self,
        db: Session,
        user_id: str,
        new_mode: str,
        previous_mode: str
    ) -> UserSettings:
        """
        更新交易模式

        Args:
            db: 数据库会话
            user_id: 用户ID
            new_mode: 新模式
            previous_mode: 旧模式

        Returns:
            更新后的用户设置对象
        """
        from datetime import datetime

        settings = self.get_or_create(db, user_id)
        settings.trading_mode = new_mode
        settings.last_mode_switch_at = datetime.utcnow()
        settings.last_mode_switch_from = previous_mode

        db.commit()
        db.refresh(settings)

        return settings

    def update_live_trading_password(
        self,
        db: Session,
        user_id: str,
        hashed_password: str
    ) -> UserSettings:
        """
        更新实盘交易密码

        Args:
            db: 数据库会话
            user_id: 用户ID
            hashed_password: 哈希后的密码

        Returns:
            更新后的用户设置对象
        """
        settings = self.get_or_create(db, user_id)
        settings.live_trading_password = hashed_password

        db.commit()
        db.refresh(settings)

        return settings

    def enable_live_trading(
        self,
        db: Session,
        user_id: str,
        enabled: bool = True
    ) -> UserSettings:
        """
        启用/禁用实盘交易

        Args:
            db: 数据库会话
            user_id: 用户ID
            enabled: 是否启用

        Returns:
            更新后的用户设置对象
        """
        settings = self.get_or_create(db, user_id)
        settings.live_trading_enabled = enabled

        db.commit()
        db.refresh(settings)

        return settings

    def update_preferences(
        self,
        db: Session,
        user_id: str,
        preferences: dict
    ) -> UserSettings:
        """
        更新用户偏好设置

        Args:
            db: 数据库会话
            user_id: 用户ID
            preferences: 偏好设置字典

        Returns:
            更新后的用户设置对象
        """
        settings = self.get_or_create(db, user_id)
        settings.preferences = {**(settings.preferences or {}), **preferences}

        db.commit()
        db.refresh(settings)

        return settings
