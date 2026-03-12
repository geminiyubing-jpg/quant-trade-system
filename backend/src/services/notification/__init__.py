"""
通知服务模块
提供通知配置和基础功能
"""

from loguru import logger
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class NotificationConfig(BaseModel):
    """通知配置"""
    browser_notification_enabled: bool = False
    sound_enabled: bool = False
    email_notification_enabled: bool = False
    quiet_hours_start: Optional[int] = 22  # 静音开始时间
    quiet_hours_end: Optional[int] = 8  # 静音结束时间


class NotificationService:
    """通知服务"""

    def __init__(self, config: Optional[NotificationConfig] = None):
        self._config = config or NotificationConfig()
        logger.info("通知服务已初始化")

    def update_config(self, config: NotificationConfig) -> None:
        """更新配置"""
        if config.browser_notification_enabled is not None:
            self._config.browser_notification_enabled = config.browser_notification_enabled
        if config.sound_enabled is not None:
            self._config.sound_enabled = config.sound_enabled
        if config.email_notification_enabled is not None:
            self._config.email_notification_enabled = config.email_notification_enabled
        if config.quiet_hours_start is not None:
            self._config.quiet_hours_start = config.quiet_hours_start
        if config.quiet_hours_end is not None:
            self._config.quiet_hours_end = config.quiet_hours_end
        logger.info("通知配置已更新")

    def is_quiet_hours(self) -> bool:
        """检查是否在静音时段"""
        if (
            self._config.quiet_hours_start is None
            or self._config.quiet_hours_end is None
        ):
            return False

        now = datetime.now()
        current_hour = now.hour
        start = self._config.quiet_hours_start
        end = self._config.quiet_hours_end

        if start <= end:
            return start <= current_hour < end
        else:
            return current_hour >= start or current_hour < end

    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        发送通知

        Args:
            user_id: 用户ID
            title: 通知标题
            body: 通知内容
            data: 附加数据

        Returns:
            是否发送成功
        """
        if self.is_quiet_hours():
            logger.debug(f"静音时段，跳过通知: {title}")
            return False

        try:
            # 这里可以集成实际的通知服务
            # 例如：邮件、短信、WebSocket推送等
            logger.info(f"发送通知给用户 {user_id}: {title} - {body}")
            return True
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False

    async def send_browser_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        发送浏览器推送通知

        通过WebSocket向前端发送通知请求
        """
        if not self._config.browser_notification_enabled:
            logger.debug("浏览器通知未启用")
            return False

        if self.is_quiet_hours():
            logger.debug(f"静音时段，跳过浏览器通知: {title}")
            return False

        try:
            # 这里需要通过WebSocket发送通知请求到前端
            # 实际的浏览器通知由前端JavaScript处理
            logger.info(f"请求浏览器通知: {title}")
            return True
        except Exception as e:
            logger.error(f"请求浏览器通知失败: {e}")
            return False

    def get_config(self) -> NotificationConfig:
        """获取当前配置"""
        return self._config


# 全局实例
notification_service = NotificationService()
