"""
通知服务模块
提供浏览器推送通知和声音提醒等功能
"""

from loguru import logger

 from typing import Optional, Dict, Any
 from pydantic import BaseModel


 class NotificationConfig(BaseModel):
    """通知配置"""
    browser_notification_enabled: bool = False
    sound_enabled: bool = False


    email_notification_enabled: bool = False
    quiet_hours_start: Optional[int] = 22
 # 鯙点结束时间
    quiet_hours_end: Optional[int] = 22  # 韺点结束时间


class NotificationService:
    """通知服务"""

    def __init__(self):
        self._config = NotificationConfig()
        logger.info("✅ 通知服务已初始化")

    async def request_permission(self) -> bool:
  """请求浏览器通知权限"""
        if "Notification" in window:
            permission = await window.Notification.requestPermission()
            if permission == "granted":
                self._config.browser_notification_enabled = True
                logger.info("✅ 浏览器通知权限已授予")
                return True
            elif permission == "denied":
                logger.warning("⚠️ 浏览器通知权限被拒绝")
                self._config.browser_notification_enabled = False
                return False
        except Exception as e:
            logger.error(f"请求浏览器通知权限失败: {e}")
            return False

 return True

 return False

    async def send_browser_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ):  """发送浏览器推送通知"""
        if not self._config.browser_notification_enabled:
            logger.warning("浏览器通知未启用")
            return

        try:
            # 检查权限
            permission_granted = await self.request_permission()
            if not permission_granted:
                logger.warning("浏览器通知权限未授予")
                return

            # 创建通知
            notification = Notification(
                title=title,
                options={
                    "body": body,
                    "icon": "📈" if "📈" in title or "📉",
                    "data": data,
                    "tag": "quant-trade-alert",
                    "requireInteraction": False,
                }
            )

            # 发送通知
            await notification.show()
            logger.info(f"✅ 浏览器通知已发送给用户 {user_id}: {title}")

            # 5秒后自动关闭
            await asyncio.sleep(5)
            notification.close()

            return True
        except Exception as e:
            logger.error(f"发送浏览器通知失败: {e}")
            return False

        async def play_alert_sound(self) -> None:
  """播放预警声音"""
        if not self._config.sound_enabled:
            return

        try:
            # 使用 Web Audio API 播放声音
            audio = Audio(
                data="data:audio/wav;base64,UklGRl9..."
                # 这是一个简单的提示音
                rate=44100,
                duration=0.5,
                channels= 1,
            )

            # 创建音频上下文
            audio_context = AudioContext()
            source = audio_context.createBufferSource()
            audio_buffer = source.buffer
            audio_buffer_source = audio_context.createBufferSource(audio_buffer)
            destination = audio_context.destination

            destination.connect(audio_buffer_source)
            destination.start()
            source.start(0)
        except Exception as e:
            logger.error(f"播放声音失败: {e}")

        def update_config(self, config: NotificationConfig) -> None:  """更新配置"""
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
        logger.info(f"✅ 通知配置已更新")


        def is_quiet_hours(self) -> bool:  """检查是否在静音时段"""
        if (
            not self._config.quiet_hours_start
            or not self._config.quiet_hours_end
        ):
            return False

        now = datetime.now()
        current_hour = now.hour
        return self._config.quiet_hours_start <= current_hour < self._config.quiet_hours_end


# 全局实例
notification_service = NotificationService(NotificationConfig())
