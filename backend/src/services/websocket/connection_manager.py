"""
==============================================
WebSocket 实时行情 - 连接管理器
==============================================
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Set

from fastapi import WebSocket

from src.services.websocket.redis_manager import redis_manager

logger = logging.getLogger(__name__)


class Connection:
    """WebSocket 连接类"""

    def __init__(self, websocket: WebSocket, user_id: str):
        """
        初始化连接

        Args:
            websocket: WebSocket 实例
            user_id: 用户 ID
        """
        self.connection_id = str(uuid.uuid4())
        self.websocket = websocket
        self.user_id = user_id
        self.subscriptions: Set[str] = set()
        self.connected_at = datetime.now()
        self.last_ping = datetime.now()

    async def send_json(self, data: dict):
        """
        发送 JSON 消息

        Args:
            data: 消息数据
        """
        try:
            import json

            await self.websocket.send_json(data)
        except Exception as e:
            logger.error(f"❌ 发送消息失败 (连接: {self.connection_id}): {e}")
            raise

    async def close(self, code: int = 1000, reason: str = ""):
        """
        关闭连接

        Args:
            code: 关闭码
            reason: 关闭原因
        """
        try:
            await self.websocket.close(code=code, reason=reason)
            logger.info(f"🔌 连接已关闭: {self.connection_id} (用户: {self.user_id})")
        except Exception as e:
            logger.error(f"❌ 关闭连接失败: {e}")


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        """初始化连接管理器"""
        # 活跃连接: {connection_id: Connection}
        self.active_connections: Dict[str, Connection] = {}
        # 用户连接映射: {user_id: set[connection_id]}
        self.user_connections: Dict[str, Set[str]] = {}
        # 心跳检查间隔（秒）
        self.heartbeat_interval = 30
        # 心跳超时时间（秒）
        self.heartbeat_timeout = 60
        # 启动心跳检查任务
        self.heartbeat_task = None

    async def connect(self, websocket: WebSocket, user_id: str) -> Connection:
        """
        接受新的 WebSocket 连接

        Args:
            websocket: WebSocket 实例
            user_id: 用户 ID

        Returns:
            Connection: 连接对象
        """
        await websocket.accept()
        connection = Connection(websocket, user_id)

        # 保存连接
        self.active_connections[connection.connection_id] = connection

        # 更新用户连接映射
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection.connection_id)

        # 保存到 Redis
        redis_manager.save_connection(connection.connection_id, user_id)

        logger.info(f"✅ 新连接: {connection.connection_id} (用户: {user_id}, 总连接: {len(self.active_connections)})")

        # 启动心跳检查（如果未启动）
        if self.heartbeat_task is None:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_check())

        return connection

    async def disconnect(self, connection_id: str):
        """
        断开连接

        Args:
            connection_id: 连接 ID
        """
        if connection_id not in self.active_connections:
            return

        connection = self.active_connections[connection_id]
        user_id = connection.user_id

        # 清理订阅关系
        if connection.subscriptions:
            for symbol in connection.subscriptions:
                redis_manager.remove_subscription(user_id, symbol)

        # 从用户连接映射中移除
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # 删除连接
        del self.active_connections[connection_id]

        # 从 Redis 删除
        redis_manager.delete_connection(connection_id)

        logger.info(
            f"🔌 断开连接: {connection_id} (用户: {user_id}, 剩余连接: {len(self.active_connections)})"
        )

    async def send_to_connection(self, connection_id: str, data: dict) -> bool:
        """
        向指定连接发送消息

        Args:
            connection_id: 连接 ID
            data: 消息数据

        Returns:
            bool: 是否发送成功
        """
        if connection_id not in self.active_connections:
            logger.warning(f"⚠️  连接不存在: {connection_id}")
            return False

        connection = self.active_connections[connection_id]
        try:
            await connection.send_json(data)
            return True
        except Exception as e:
            logger.error(f"❌ 发送消息失败 (连接: {connection_id}): {e}")
            # 发送失败，移除连接
            await self.disconnect(connection_id)
            return False

    async def broadcast_to_user(self, user_id: str, data: dict) -> int:
        """
        向用户的所有连接广播消息

        Args:
            user_id: 用户 ID
            data: 消息数据

        Returns:
            int: 成功发送的连接数
        """
        if user_id not in self.user_connections:
            return 0

        success_count = 0
        connection_ids = list(self.user_connections[user_id])

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, data):
                success_count += 1

        return success_count

    async def broadcast_to_subscribers(self, symbol: str, data: dict) -> int:
        """
        向订阅某股票的所有用户广播消息

        Args:
            symbol: 股票代码
            data: 消息数据

        Returns:
            int: 成功发送的连接数
        """
        # 从 Redis 获取订阅者列表
        subscriber_ids = redis_manager.get_symbol_subscribers(symbol)
        if not subscriber_ids:
            return 0

        success_count = 0
        for user_id in subscriber_ids:
            success_count += await self.broadcast_to_user(user_id, data)

        logger.debug(f"📢 广播行情 {symbol}: {success_count} 个连接")
        return success_count

    def get_connection_count(self) -> int:
        """
        获取当前连接数

        Returns:
            int: 连接数
        """
        return len(self.active_connections)

    def get_user_connection_count(self, user_id: str) -> int:
        """
        获取用户的连接数

        Args:
            user_id: 用户 ID

        Returns:
            int: 连接数
        """
        return len(self.user_connections.get(user_id, set()))

    def update_last_ping(self, connection_id: str):
        """
        更新连接的最后心跳时间

        Args:
            connection_id: 连接 ID
        """
        if connection_id in self.active_connections:
            self.active_connections[connection_id].last_ping = datetime.now()

    async def _heartbeat_check(self):
        """
        心跳检查任务（定期清理超时连接）
        """
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                now = datetime.now()
                timeout_connections = []

                # 检查所有连接的心跳时间
                for connection_id, connection in self.active_connections.items():
                    idle_time = (now - connection.last_ping).total_seconds()
                    if idle_time > self.heartbeat_timeout:
                        timeout_connections.append(connection_id)

                # 清理超时连接
                for connection_id in timeout_connections:
                    logger.warning(f"⚠️  连接超时: {connection_id}")
                    await self.disconnect(connection_id)

                if timeout_connections:
                    logger.info(f"🧹 清理了 {len(timeout_connections)} 个超时连接")

            except asyncio.CancelledError:
                logger.info("💓 心跳检查任务已停止")
                break
            except Exception as e:
                logger.error(f"❌ 心跳检查异常: {e}")

    async def cleanup(self):
        """
        清理所有连接
        """
        logger.info("🧹 清理所有 WebSocket 连接...")
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

        # 停止心跳检查
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass


# 全局连接管理器实例
connection_manager = ConnectionManager()
