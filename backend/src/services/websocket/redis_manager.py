"""
==============================================
WebSocket 实时行情 - Redis 缓存管理器
==============================================
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import redis
from redis import Redis

from src.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis 缓存管理器 - 用于行情数据缓存"""

    def __init__(self):
        """初始化 Redis 连接"""
        self.redis_client: Optional[Redis] = None
        self._connect()

    def _connect(self):
        """建立 Redis 连接"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True,  # 自动解码为字符串
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("✅ Redis 连接成功")
        except Exception as e:
            logger.warning(f"⚠️  Redis 连接失败: {e}")
            logger.warning("⚠️  行情数据缓存功能将被禁用，但不影响其他功能")
            self.redis_client = None

    # ==============================================
    # 行情数据缓存
    # ==============================================

    def save_quote(self, symbol: str, quote_data: dict, ttl: int = 5) -> bool:
        """
        保存行情数据到 Redis

        Args:
            symbol: 股票代码
            quote_data: 行情数据字典
            ttl: 过期时间（秒），默认 5 秒

        Returns:
            bool: 是否保存成功
        """
        if not self.redis_client:
            return False
        try:
            key = f"market:quote:{symbol}"
            # 添加时间戳
            quote_data["timestamp"] = datetime.now().isoformat()
            # 保存到 Redis Hash
            self.redis_client.hset(key, mapping=quote_data)
            # 设置过期时间
            self.redis_client.expire(key, ttl)
            logger.debug(f"✅ 缓存行情数据: {symbol}")
            return True
        except Exception as e:
            logger.error(f"❌ 保存行情数据失败 {symbol}: {e}")
            return False

    def get_quote(self, symbol: str) -> Optional[dict]:
        """
        从 Redis 获取行情数据

        Args:
            symbol: 股票代码

        Returns:
            dict: 行情数据，如果不存在返回 None
        """
        if not self.redis_client:
            return None
        try:
            key = f"market:quote:{symbol}"
            data = self.redis_client.hgetall(key)
            if data:
                logger.debug(f"✅ 命中缓存: {symbol}")
                return data
            logger.debug(f"⚠️  缓存未命中: {symbol}")
            return None
        except Exception as e:
            logger.error(f"❌ 获取行情数据失败 {symbol}: {e}")
            return None

    def get_quotes_batch(self, symbols: list[str]) -> dict[str, dict]:
        """
        批量获取行情数据

        Args:
            symbols: 股票代码列表

        Returns:
            dict: {symbol: quote_data}
        """
        result = {}
        if not self.redis_client:
            return result
        try:
            pipe = self.redis_client.pipeline()
            for symbol in symbols:
                key = f"market:quote:{symbol}"
                pipe.hgetall(key)
            results = pipe.execute()
            for symbol, data in zip(symbols, results):
                if data:
                    result[symbol] = data
            logger.debug(f"✅ 批量获取行情: {len(result)}/{len(symbols)} 命中")
            return result
        except Exception as e:
            logger.error(f"❌ 批量获取行情失败: {e}")
            return result

    # ==============================================
    # 订阅关系管理
    # ==============================================

    def add_subscription(self, user_id: str, symbol: str) -> bool:
        """
        添加订阅关系

        Args:
            user_id: 用户 ID
            symbol: 股票代码

        Returns:
            bool: 是否添加成功
        """
        if not self.redis_client:
            return False
        try:
            # 用户订阅列表
            user_key = f"market:subscription:{user_id}"
            self.redis_client.sadd(user_key, symbol)

            # 股票订阅者列表（反向索引）
            symbol_key = f"market:subscribers:{symbol}"
            self.redis_client.sadd(symbol_key, str(user_id))

            logger.debug(f"✅ 用户 {user_id} 订阅 {symbol}")
            return True
        except Exception as e:
            logger.error(f"❌ 添加订阅失败: {e}")
            return False

    def remove_subscription(self, user_id: str, symbol: str) -> bool:
        """
        移除订阅关系

        Args:
            user_id: 用户 ID
            symbol: 股票代码

        Returns:
            bool: 是否移除成功
        """
        if not self.redis_client:
            return False
        try:
            # 用户订阅列表
            user_key = f"market:subscription:{user_id}"
            self.redis_client.srem(user_key, symbol)

            # 股票订阅者列表
            symbol_key = f"market:subscribers:{symbol}"
            self.redis_client.srem(symbol_key, str(user_id))

            logger.debug(f"✅ 用户 {user_id} 取消订阅 {symbol}")
            return True
        except Exception as e:
            logger.error(f"❌ 移除订阅失败: {e}")
            return False

    def get_user_subscriptions(self, user_id: str) -> set[str]:
        """
        获取用户的所有订阅

        Args:
            user_id: 用户 ID

        Returns:
            set: 股票代码集合
        """
        if not self.redis_client:
            return set()
        try:
            key = f"market:subscription:{user_id}"
            subscriptions = self.redis_client.smembers(key)
            return subscriptions
        except Exception as e:
            logger.error(f"❌ 获取用户订阅失败: {e}")
            return set()

    def clear_user_subscriptions(self, user_id: str) -> bool:
        """
        清除用户的所有订阅

        Args:
            user_id: 用户 ID

        Returns:
            bool: 是否清除成功
        """
        if not self.redis_client:
            return False
        try:
            # 获取用户的所有订阅
            key = f"market:subscription:{user_id}"
            symbols = self.redis_client.smembers(key)

            # 从每个股票的订阅者列表中移除该用户
            pipe = self.redis_client.pipeline()
            for symbol in symbols:
                symbol_key = f"market:subscribers:{symbol}"
                pipe.srem(symbol_key, str(user_id))

            # 删除用户订阅列表
            pipe.delete(key)
            pipe.execute()

            logger.info(f"✅ 清除用户 {user_id} 的所有订阅 ({len(symbols)} 个)")
            return True
        except Exception as e:
            logger.error(f"❌ 清除用户订阅失败: {e}")
            return False

    def get_symbol_subscribers(self, symbol: str) -> set[str]:
        """
        获取订阅某股票的所有用户

        Args:
            symbol: 股票代码

        Returns:
            set: 用户 ID 集合
        """
        if not self.redis_client:
            return set()
        try:
            key = f"market:subscribers:{symbol}"
            subscribers = self.redis_client.smembers(key)
            return subscribers
        except Exception as e:
            logger.error(f"❌ 获取股票订阅者失败: {e}")
            return set()

    # ==============================================
    # 连接管理
    # ==============================================

    def save_connection(self, connection_id: str, user_id: str, ttl: int = 3600) -> bool:
        """
        保存 WebSocket 连接信息

        Args:
            connection_id: 连接 ID
            user_id: 用户 ID
            ttl: 过期时间（秒），默认 1 小时

        Returns:
            bool: 是否保存成功
        """
        if not self.redis_client:
            return False
        try:
            key = f"market:connection:{connection_id}"
            self.redis_client.hset(key, mapping={"user_id": str(user_id), "connected_at": datetime.now().isoformat()})
            self.redis_client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"❌ 保存连接信息失败: {e}")
            return False

    def get_connection_user(self, connection_id: str) -> Optional[str]:
        """
        获取连接对应的用户 ID

        Args:
            connection_id: 连接 ID

        Returns:
            int: 用户 ID，如果不存在返回 None
        """
        if not self.redis_client:
            return None
        try:
            key = f"market:connection:{connection_id}"
            data = self.redis_client.hgetall(key)
            if data and "user_id" in data:
                return data["user_id"]
            return None
        except Exception as e:
            logger.error(f"❌ 获取连接用户失败: {e}")
            return None

    def delete_connection(self, connection_id: str) -> bool:
        """
        删除连接信息

        Args:
            connection_id: 连接 ID

        Returns:
            bool: 是否删除成功
        """
        if not self.redis_client:
            return False
        try:
            key = f"market:connection:{connection_id}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"❌ 删除连接信息失败: {e}")
            return False

    # ==============================================
    # 健康检查
    # ==============================================

    def ping(self) -> bool:
        """
        测试 Redis 连接

        Returns:
            bool: 是否连接正常
        """
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"❌ Redis 连接异常: {e}")
            return False

    def close(self):
        """关闭 Redis 连接"""
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info("✅ Redis 连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭 Redis 连接失败: {e}")


# 全局 Redis 管理器实例
redis_manager = RedisManager()
