"""
报警系统模块

提供多渠道报警功能：
- 邮件报警
- Webhook 报警（钉钉、企业微信、Slack）
- 短信报警（预留接口）
- 自定义报警渠道

使用示例：
    from services.monitoring.alerts import AlertSystem, Alert

    # 创建报警系统
    alert_system = AlertSystem()

    # 添加报警渠道
    alert_system.add_channel(EmailChannel(config))
    alert_system.add_channel(DingTalkChannel(webhook_url))

    # 发送报警
    alert = Alert(
        title="风险预警",
        message="单日亏损超过 5%",
        severity="WARNING"
    )
    await alert_system.send(alert)
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
import asyncio
import logging
import json
import aiohttp

logger = logging.getLogger(__name__)


# ==============================================
# 报警级别
# ==============================================

class AlertSeverity(str, Enum):
    """报警严重程度"""
    INFO = "INFO"               # 信息
    WARNING = "WARNING"         # 警告
    ERROR = "ERROR"             # 错误
    CRITICAL = "CRITICAL"       # 严重


class AlertType(str, Enum):
    """报警类型"""
    RISK = "RISK"               # 风险报警
    TRADE = "TRADE"             # 交易报警
    SYSTEM = "SYSTEM"           # 系统报警
    STRATEGY = "STRATEGY"       # 策略报警
    DATA = "DATA"               # 数据报警
    PERFORMANCE = "PERFORMANCE" # 性能报警


# ==============================================
# 报警数据类
# ==============================================

@dataclass
class Alert:
    """
    报警消息

    封装报警的完整信息。
    """
    title: str                              # 标题
    message: str                            # 消息内容
    severity: AlertSeverity = AlertSeverity.INFO  # 严重程度
    alert_type: AlertType = AlertType.SYSTEM      # 报警类型

    # 上下文信息
    strategy_id: str = ""                   # 策略 ID
    symbol: str = ""                        # 股票代码
    source: str = ""                        # 来源

    # 时间
    timestamp: datetime = None              # 时间戳

    # 附加数据
    details: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # 去重
    fingerprint: str = ""                   # 指纹（用于去重）

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        # 生成指纹
        if not self.fingerprint:
            self.fingerprint = f"{self.alert_type}:{self.title}:{self.strategy_id}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "alert_type": self.alert_type.value,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "tags": self.tags,
        }


# ==============================================
# 报警渠道基类
# ==============================================

class AlertChannel:
    """
    报警渠道基类

    所有报警渠道都需要继承此类。
    """

    channel_name: str = "base"
    supported_severities: List[AlertSeverity] = None  # None 表示支持所有级别

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"AlertChannel.{self.channel_name}")

    async def send(self, alert: Alert) -> bool:
        """
        发送报警

        Args:
            alert: 报警消息

        Returns:
            是否成功
        """
        raise NotImplementedError

    def should_send(self, alert: Alert) -> bool:
        """
        检查是否应该发送

        Args:
            alert: 报警消息

        Returns:
            是否应该发送
        """
        if self.supported_severities is None:
            return True

        return alert.severity in self.supported_severities


# ==============================================
# Webhook 渠道
# ==============================================

class WebhookChannel(AlertChannel):
    """
    Webhook 报警渠道

    支持自定义 Webhook URL。
    """

    channel_name = "webhook"

    def __init__(
        self,
        webhook_url: str,
        headers: Dict[str, str] = None,
        timeout: int = 10
    ):
        super().__init__({
            "webhook_url": webhook_url,
            "headers": headers,
            "timeout": timeout
        })
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout

    async def send(self, alert: Alert) -> bool:
        """发送报警"""
        if not self.should_send(alert):
            return True

        try:
            payload = alert.to_dict()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status >= 400:
                        self.logger.error(f"Webhook 发送失败: {response.status}")
                        return False

                    self.logger.debug(f"Webhook 发送成功: {alert.title}")
                    return True

        except asyncio.TimeoutError:
            self.logger.error("Webhook 发送超时")
            return False

        except Exception as e:
            self.logger.error(f"Webhook 发送失败: {e}")
            return False


# ==============================================
# 钉钉渠道
# ==============================================

class DingTalkChannel(AlertChannel):
    """
    钉钉机器人报警渠道

    使用钉钉自定义机器人发送报警。
    """

    channel_name = "dingtalk"

    def __init__(
        self,
        webhook_url: str,
        secret: str = None,
        at_mobiles: List[str] = None,
        at_all: bool = False
    ):
        super().__init__({
            "webhook_url": webhook_url,
            "secret": secret
        })
        self.webhook_url = webhook_url
        self.secret = secret
        self.at_mobiles = at_mobiles or []
        self.at_all = at_all

    def _get_severity_emoji(self, severity: AlertSeverity) -> str:
        """获取严重程度对应的表情"""
        emoji_map = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }
        return emoji_map.get(severity, "📢")

    async def send(self, alert: Alert) -> bool:
        """发送钉钉消息"""
        if not self.should_send(alert):
            return True

        try:
            emoji = self._get_severity_emoji(alert.severity)

            # 构建消息
            content = f"{emoji} **{alert.title}**\n\n"
            content += f"**级别**: {alert.severity.value}\n"
            content += f"**类型**: {alert.alert_type.value}\n"
            content += f"**时间**: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += f"**内容**:\n{alert.message}\n"

            if alert.strategy_id:
                content += f"\n**策略**: {alert.strategy_id}"
            if alert.symbol:
                content += f"\n**标的**: {alert.symbol}"

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": alert.title,
                    "text": content,
                },
                "at": {
                    "atMobiles": self.at_mobiles,
                    "isAtAll": self.at_all,
                }
            }

            # 如果有签名，添加签名
            if self.secret:
                import hmac
                import hashlib
                import base64
                import time as time_module
                import urllib.parse

                timestamp = str(round(time_module.time() * 1000))
                string_to_sign = f"{timestamp}\n{self.secret}"
                hmac_code = hmac.new(
                    self.secret.encode("utf-8"),
                    string_to_sign.encode("utf-8"),
                    digestmod=hashlib.sha256
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

                url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.webhook_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()

                    if result.get("errcode", 0) != 0:
                        self.logger.error(f"钉钉发送失败: {result}")
                        return False

                    self.logger.info(f"钉钉发送成功: {alert.title}")
                    return True

        except Exception as e:
            self.logger.error(f"钉钉发送失败: {e}")
            return False


# ==============================================
# 企业微信渠道
# ==============================================

class WeChatWorkChannel(AlertChannel):
    """
    企业微信机器人报警渠道
    """

    channel_name = "wechat_work"

    def __init__(self, webhook_url: str, mentioned_list: List[str] = None):
        super().__init__({"webhook_url": webhook_url})
        self.webhook_url = webhook_url
        self.mentioned_list = mentioned_list or []

    async def send(self, alert: Alert) -> bool:
        """发送企业微信消息"""
        if not self.should_send(alert):
            return True

        try:
            content = f"**{alert.title}**\n"
            content += f"> 级别: {alert.severity.value}\n"
            content += f"> 类型: {alert.alert_type.value}\n"
            content += f"> 时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += alert.message

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content,
                    "mentioned_list": self.mentioned_list,
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()

                    if result.get("errcode", 0) != 0:
                        self.logger.error(f"企业微信发送失败: {result}")
                        return False

                    self.logger.info(f"企业微信发送成功: {alert.title}")
                    return True

        except Exception as e:
            self.logger.error(f"企业微信发送失败: {e}")
            return False


# ==============================================
# 日志渠道
# ==============================================

class LogChannel(AlertChannel):
    """
    日志报警渠道

    将报警写入日志。
    """

    channel_name = "log"

    def __init__(self, log_file: str = None):
        super().__init__({"log_file": log_file})

        self.logger = logging.getLogger("AlertLog")

        if log_file:
            handler = logging.FileHandler(log_file, encoding="utf-8")
            handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            ))
            self.logger.addHandler(handler)

    async def send(self, alert: Alert) -> bool:
        """写入日志"""
        if not self.should_send(alert):
            return True

        log_message = (
            f"[{alert.severity.value}] {alert.alert_type.value}: "
            f"{alert.title} - {alert.message}"
        )

        if alert.strategy_id:
            log_message += f" (策略: {alert.strategy_id})"

        if alert.severity == AlertSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif alert.severity == AlertSeverity.ERROR:
            self.logger.error(log_message)
        elif alert.severity == AlertSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        return True


# ==============================================
# 报警系统
# ==============================================

class AlertSystem:
    """
    报警系统

    管理多个报警渠道，统一发送报警。

    功能：
    - 多渠道支持
    - 报警去重
    - 频率限制
    - 异步发送

    使用示例：
        system = AlertSystem()

        # 添加渠道
        system.add_channel(DingTalkChannel(webhook_url))
        system.add_channel(LogChannel("alerts.log"))

        # 发送报警
        await system.send(Alert(
            title="风险预警",
            message="单日亏损超过 5%",
            severity=AlertSeverity.WARNING
        ))
    """

    def __init__(
        self,
        dedup_window_seconds: int = 300,  # 去重窗口（秒）
        rate_limit_per_minute: int = 10   # 每分钟最大报警数
    ):
        """
        初始化报警系统

        Args:
            dedup_window_seconds: 去重窗口
            rate_limit_per_minute: 频率限制
        """
        self._channels: List[AlertChannel] = []
        self._sent_alerts: Dict[str, datetime] = {}  # fingerprint -> last_sent
        self._dedup_window = dedup_window_seconds
        self._rate_limit = rate_limit_per_minute
        self._recent_count = 0
        self._last_minute = datetime.now().minute
        self._logger = logging.getLogger("AlertSystem")

    def add_channel(self, channel: AlertChannel) -> None:
        """添加报警渠道"""
        self._channels.append(channel)
        self._logger.info(f"添加报警渠道: {channel.channel_name}")

    def remove_channel(self, channel_name: str) -> bool:
        """移除报警渠道"""
        for i, channel in enumerate(self._channels):
            if channel.channel_name == channel_name:
                self._channels.pop(i)
                return True
        return False

    async def send(self, alert: Alert) -> Dict[str, bool]:
        """
        发送报警

        Args:
            alert: 报警消息

        Returns:
            {channel_name: 是否成功}
        """
        # 检查去重
        if self._is_duplicate(alert):
            self._logger.debug(f"报警去重: {alert.fingerprint}")
            return {}

        # 检查频率限制
        if not self._check_rate_limit():
            self._logger.warning(f"报警频率超限，跳过: {alert.title}")
            return {}

        # 记录已发送
        self._sent_alerts[alert.fingerprint] = datetime.now()

        # 并发发送到所有渠道
        results = {}
        tasks = []

        for channel in self._channels:
            tasks.append(self._send_to_channel(channel, alert))

        if tasks:
            channel_results = await asyncio.gather(*tasks, return_exceptions=True)

            for channel, result in zip(self._channels, channel_results):
                if isinstance(result, Exception):
                    results[channel.channel_name] = False
                    self._logger.error(
                        f"渠道 {channel.channel_name} 发送失败: {result}"
                    )
                else:
                    results[channel.channel_name] = result

        self._logger.info(
            f"报警发送完成: {alert.title} -> {results}"
        )

        return results

    async def _send_to_channel(
        self,
        channel: AlertChannel,
        alert: Alert
    ) -> bool:
        """发送到单个渠道"""
        try:
            return await channel.send(alert)
        except Exception as e:
            self._logger.error(f"渠道 {channel.channel_name} 异常: {e}")
            return False

    def _is_duplicate(self, alert: Alert) -> bool:
        """检查是否重复"""
        if not alert.fingerprint:
            return False

        last_sent = self._sent_alerts.get(alert.fingerprint)
        if last_sent is None:
            return False

        elapsed = (datetime.now() - last_sent).total_seconds()
        return elapsed < self._dedup_window

    def _check_rate_limit(self) -> bool:
        """检查频率限制"""
        now = datetime.now()

        # 新的一分钟，重置计数
        if now.minute != self._last_minute:
            self._last_minute = now.minute
            self._recent_count = 0

        self._recent_count += 1
        return self._recent_count <= self._rate_limit

    # ==========================================
    # 便捷方法
    # ==========================================

    async def alert_risk(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.WARNING,
        **kwargs
    ) -> Dict[str, bool]:
        """发送风险报警"""
        return await self.send(Alert(
            title=title,
            message=message,
            severity=severity,
            alert_type=AlertType.RISK,
            **kwargs
        ))

    async def alert_trade(
        self,
        title: str,
        message: str,
        symbol: str = "",
        **kwargs
    ) -> Dict[str, bool]:
        """发送交易报警"""
        return await self.send(Alert(
            title=title,
            message=message,
            alert_type=AlertType.TRADE,
            symbol=symbol,
            **kwargs
        ))

    async def alert_system(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.ERROR,
        **kwargs
    ) -> Dict[str, bool]:
        """发送系统报警"""
        return await self.send(Alert(
            title=title,
            message=message,
            severity=severity,
            alert_type=AlertType.SYSTEM,
            **kwargs
        ))

    # ==========================================
    # 维护
    # ==========================================

    def clear_old_alerts(self, max_age_hours: int = 24) -> int:
        """
        清除旧的报警记录

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            清除的数量
        """
        cutoff = datetime.now() - __import__('datetime').timedelta(hours=max_age_hours)

        to_remove = [
            fp for fp, ts in self._sent_alerts.items()
            if ts < cutoff
        ]

        for fp in to_remove:
            del self._sent_alerts[fp]

        if to_remove:
            self._logger.info(f"清除了 {len(to_remove)} 条旧报警记录")

        return len(to_remove)


# ==============================================
# 默认报警系统
# ==============================================

def create_default_alert_system() -> AlertSystem:
    """创建默认报警系统"""
    system = AlertSystem()

    # 添加日志渠道
    system.add_channel(LogChannel())

    return system


# 默认实例
default_alert_system = create_default_alert_system()
