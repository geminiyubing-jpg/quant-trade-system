"""
价格预警触发服务
负责检查价格是否触发预警条件，并发送通知
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from loguru import logger
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.alert import PriceAlert, AlertHistory, AlertType
from src.models.stock import Stock
from src.services.websocket.connection_manager import manager as ws_manager
from src.services.notification import notification_service


class AlertTriggerService:
    """预警触发服务"""

    def __init__(self):
        self._check_interval = 30  # 检查间隔（秒）
        self._running = False
        self._task = None
        self._db = None

    async def start(self):
        """启动服务"""
        self._running = True
        self._db = next(get_db())
        logger.info("预警触发服务已启动")

        # 启动定期检查任务
        self._task = asyncio.create_task(self._check_loop())
        logger.info("预警检查循环已启动")

    async def stop(self):
        """停止服务"""
        self._running = False
        if self._task:
            self._task.cancel()
            logger.info("预警触发服务已停止")

    async def _check_loop(self):
        """检查循环"""
        while self._running:
            try:
                await self._check_alerts()
            except Exception as e:
                logger.error(f"检查预警失败: {e}")

            await asyncio.sleep(self._check_interval)

    async def _check_alerts(self):
        """检查所有活跃的预警"""
        if not self._db:
            return

        alerts = self._db.query(PriceAlert).filter(
            PriceAlert.is_active == True,
            PriceAlert.is_triggered == False
        ).all()

        for alert in alerts:
            try:
                await self._check_single_alert(alert)
            except Exception as e:
                logger.error(f"检查预警 {alert.id} 失败: {e}")

    async def _check_single_alert(self, alert: PriceAlert):
        """检查单个预警"""
        # 获取当前价格
        stock = self._db.query(Stock).filter(
            Stock.symbol == alert.symbol
        ).first()

        if not stock:
            logger.warning(f"股票 {alert.symbol} 不存在，跳过")
            return

        current_price = stock.current_price if stock.current_price else Decimal("0")

        # 更新当前价格
        alert.current_price = current_price
        self._db.commit()

        # 检查是否触发条件
        triggered = False
        trigger_value = None

        if alert.alert_type == AlertType.PRICE_ABOVE:
            if current_price >= alert.target_value:
                triggered = True
                trigger_value = alert.target_value
        elif alert.alert_type == AlertType.PRICE_BELOW:
            if current_price <= alert.target_value:
                triggered = True
                trigger_value = alert.target_value
        elif alert.alert_type == AlertType.PERCENT_UP:
            if alert.current_price and alert.current_price > 0:
                percent_change = (current_price - alert.current_price) / alert.current_price * 100
                if percent_change >= alert.target_value:
                    triggered = True
                    trigger_value = alert.target_value
        elif alert.alert_type == AlertType.PERCENT_DOWN:
            if alert.current_price and alert.current_price > 0:
                percent_change = (current_price - alert.current_price) / alert.current_price * 100
                if percent_change <= -alert.target_value:
                    triggered = True
                    trigger_value = alert.target_value

        if triggered:
            await self._trigger_alert(alert, current_price, trigger_value)

    async def _trigger_alert(
        self,
        alert: PriceAlert,
        current_price: Decimal,
        trigger_value: Decimal,
    ):
        """触发预警"""
        logger.info(
            f"预警触发: {alert.symbol} {alert.alert_type.value} "
            f"目标: {trigger_value}, 当前: {current_price}"
        )

        # 更新预警状态
        alert.is_triggered = True
        alert.triggered_at = datetime.utcnow()
        self._db.commit()

        # 创建历史记录
        history = AlertHistory(
            user_id=alert.user_id,
            alert_id=alert.id,
            symbol=alert.symbol,
            alert_type=alert.alert_type,
            target_value=alert.target_value,
            actual_value=current_price,
            triggered_at=datetime.utcnow(),
        )
        self._db.add(history)
        self._db.commit()

        # 发送通知
        await self._send_notification(alert, current_price)

        # 通过 WebSocket 发送通知
        try:
            await ws_manager.broadcast_to_user(
                alert.user_id,
                {
                    "type": "alert_triggered",
                    "data": {
                        "alert_id": alert.id,
                        "symbol": alert.symbol,
                        "alert_type": alert.alert_type.value,
                        "target_value": float(trigger_value),
                        "current_price": float(current_price),
                        "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
                        "message": f"预警触发: {alert.symbol} {alert.alert_type.value}",
                    }
                }
            )
        except Exception as e:
            logger.error(f"WebSocket广播失败: {e}")

        logger.info(f"预警通知已发送给用户 {alert.user_id}")

    async def _send_notification(self, alert: PriceAlert, current_price: Decimal):
        """发送外部通知"""
        try:
            # 发送浏览器通知
            await notification_service.send_browser_notification(
                user_id=str(alert.user_id),
                title=f"价格预警: {alert.symbol}",
                body=f"您的 {alert.symbol} 预警已触发！当前价格: {current_price}",
                data={
                    "symbol": alert.symbol,
                    "alert_type": alert.alert_type.value,
                    "target_value": float(alert.target_value),
                    "current_price": float(current_price),
                }
            )
        except Exception as e:
            logger.error(f"发送通知失败: {e}")


# 全局实例
alert_trigger_service = AlertTriggerService()
