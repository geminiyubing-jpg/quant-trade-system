"""
数据缓存模块

提供多层缓存机制，优化数据访问性能：
- L1 缓存：内存缓存（最快）
- L2 缓存：Redis 缓存（可选）
- 支持缓存过期和失效

特性：
- TTL（生存时间）支持
- 批量操作支持
- 通配符失效
- 缓存命中率统计
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
import json
import hashlib
import logging
import threading
import time
import fnmatch

logger = logging.getLogger(__name__)


# ==============================================
# 缓存统计
# ==============================================

@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0           # 命中次数
    misses: int = 0         # 未命中次数
    sets: int = 0           # 设置次数
    deletes: int = 0        # 删除次数
    evictions: int = 0      # 驱逐次数（因容量限制）
    errors: int = 0         # 错误次数

    @property
    def total_requests(self) -> int:
        """总请求数"""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "errors": self.errors,
            "total_requests": self.total_requests,
            "hit_rate": f"{self.hit_rate * 100:.2f}%",
        }


# ==============================================
# 缓存条目
# ==============================================

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def touch(self):
        """更新访问时间和计数"""
        self.last_accessed = datetime.now()
        self.access_count += 1


# ==============================================
# L1 内存缓存
# ==============================================

class MemoryCache:
    """
    内存缓存（L1 缓存）

    特性：
    - 线程安全
    - 容量限制（LRU 驱逐）
    - TTL 支持
    - 访问统计
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600
    ):
        """
        初始化内存缓存

        Args:
            max_size: 最大条目数
            default_ttl: 默认过期时间（秒）
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        self._stats = CacheStats()
        self.logger = logging.getLogger("MemoryCache")

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或 None
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None

            entry.touch()
            self._stats.hits += 1
            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        with self._lock:
            try:
                # 检查容量
                if len(self._cache) >= self._max_size and key not in self._cache:
                    self._evict_lru()

                now = datetime.now()
                expires_at = None
                if ttl is not None or self._default_ttl > 0:
                    actual_ttl = ttl if ttl is not None else self._default_ttl
                    expires_at = now + timedelta(seconds=actual_ttl)

                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=now,
                    expires_at=expires_at,
                )

                self._cache[key] = entry
                self._stats.sets += 1
                return True

            except Exception as e:
                self._stats.errors += 1
                self.logger.error(f"设置缓存失败: {e}")
                return False

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.deletes += 1
                return True
            return False

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                del self._cache[key]
                return False
            return True

    def clear(self) -> int:
        """
        清空缓存

        Returns:
            清除的条目数
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def invalidate(self, pattern: str) -> int:
        """
        使匹配的缓存失效

        Args:
            pattern: 通配符模式（如 "data:*"）

        Returns:
            删除的条目数
        """
        with self._lock:
            keys_to_delete = []
            for key in self._cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]
                self._stats.deletes += 1

            return len(keys_to_delete)

    def _evict_lru(self) -> None:
        """驱逐最近最少使用的条目"""
        if not self._cache:
            return

        # 找到最久未访问的条目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )

        del self._cache[lru_key]
        self._stats.evictions += 1

    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        return self._stats

    def get_size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)


# ==============================================
# L2 Redis 缓存
# ==============================================

class RedisCache:
    """
    Redis 缓存（L2 缓存）

    特性：
    - 分布式缓存
    - 持久化支持
    - 高可用

    需要安装 redis 库。
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "quant:",
        default_ttl: int = 3600
    ):
        """
        初始化 Redis 缓存

        Args:
            redis_url: Redis 连接 URL
            prefix: 键前缀
            default_ttl: 默认过期时间（秒）
        """
        self._redis_url = redis_url
        self._prefix = prefix
        self._default_ttl = default_ttl
        self._redis = None
        self._stats = CacheStats()
        self._connected = False
        self.logger = logging.getLogger("RedisCache")

    async def connect(self) -> bool:
        """
        连接 Redis

        Returns:
            是否连接成功
        """
        try:
            import redis.asyncio as redis

            self._redis = await redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self._connected = True
            self.logger.info("Redis 缓存已连接")
            return True

        except ImportError:
            self.logger.warning("未安装 redis 库，Redis 缓存不可用")
            return False
        except Exception as e:
            self.logger.error(f"Redis 连接失败: {e}")
            return False

    async def disconnect(self) -> None:
        """断开 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._connected = False

    def _make_key(self, key: str) -> str:
        """生成完整的缓存键"""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或 None
        """
        if not self._connected or self._redis is None:
            self._stats.misses += 1
            return None

        try:
            full_key = self._make_key(key)
            value = await self._redis.get(full_key)

            if value is None:
                self._stats.misses += 1
                return None

            # 反序列化
            data = json.loads(value)
            self._stats.hits += 1
            return data

        except Exception as e:
            self._stats.errors += 1
            self.logger.error(f"获取 Redis 缓存失败: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        if not self._connected or self._redis is None:
            return False

        try:
            full_key = self._make_key(key)
            serialized = json.dumps(value, default=str)

            actual_ttl = ttl if ttl is not None else self._default_ttl

            if actual_ttl > 0:
                await self._redis.setex(full_key, actual_ttl, serialized)
            else:
                await self._redis.set(full_key, serialized)

            self._stats.sets += 1
            return True

        except Exception as e:
            self._stats.errors += 1
            self.logger.error(f"设置 Redis 缓存失败: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        if not self._connected or self._redis is None:
            return False

        try:
            full_key = self._make_key(key)
            result = await self._redis.delete(full_key)

            if result > 0:
                self._stats.deletes += 1
                return True
            return False

        except Exception as e:
            self._stats.errors += 1
            self.logger.error(f"删除 Redis 缓存失败: {e}")
            return False

    async def invalidate(self, pattern: str) -> int:
        """
        使匹配的缓存失效

        Args:
            pattern: 通配符模式

        Returns:
            删除的条目数
        """
        if not self._connected or self._redis is None:
            return 0

        try:
            full_pattern = self._make_key(pattern)
            keys = []

            async for key in self._redis.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                deleted = await self._redis.delete(*keys)
                self._stats.deletes += deleted
                return deleted

            return 0

        except Exception as e:
            self._stats.errors += 1
            self.logger.error(f"Redis 缓存失效失败: {e}")
            return 0

    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        return self._stats


# ==============================================
# 统一数据缓存
# ==============================================

class DataCache:
    """
    统一数据缓存

    提供多层缓存访问接口：
    - L1: 内存缓存（快速访问）
    - L2: Redis 缓存（可选，分布式共享）

    使用方式：
        cache = DataCache()

        # 设置缓存
        cache.set("data:000001.SZ", stock_data, ttl=3600)

        # 获取缓存
        data = cache.get("data:000001.SZ")

        # 使缓存失效
        cache.invalidate("data:*")
    """

    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_default_ttl: int = 300,
        l2_redis_url: str = None,
        l2_default_ttl: int = 3600
    ):
        """
        初始化数据缓存

        Args:
            l1_max_size: L1 缓存最大条目数
            l1_default_ttl: L1 缓存默认 TTL（秒）
            l2_redis_url: L2 Redis URL（如果为 None 则不使用 L2）
            l2_default_ttl: L2 缓存默认 TTL（秒）
        """
        # L1 内存缓存
        self._l1 = MemoryCache(
            max_size=l1_max_size,
            default_ttl=l1_default_ttl
        )

        # L2 Redis 缓存（可选）
        self._l2: Optional[RedisCache] = None
        if l2_redis_url:
            self._l2 = RedisCache(
                redis_url=l2_redis_url,
                default_ttl=l2_default_ttl
            )

        self.logger = logging.getLogger("DataCache")

    async def initialize(self) -> bool:
        """
        初始化缓存（连接 L2）

        Returns:
            是否初始化成功
        """
        if self._l2:
            return await self._l2.connect()
        return True

    async def close(self) -> None:
        """关闭缓存连接"""
        if self._l2:
            await self._l2.disconnect()

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存（同步版本，只查 L1）

        Args:
            key: 缓存键

        Returns:
            缓存值或 None
        """
        return self._l1.get(key)

    async def get_async(self, key: str) -> Optional[Any]:
        """
        获取缓存（异步版本，查 L1 和 L2）

        Args:
            key: 缓存键

        Returns:
            缓存值或 None
        """
        # 先查 L1
        value = self._l1.get(key)
        if value is not None:
            return value

        # 再查 L2
        if self._l2:
            value = await self._l2.get(key)
            if value is not None:
                # 回填 L1
                self._l1.set(key, value)
                return value

        return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        设置缓存（同步版本，只设置 L1）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        return self._l1.set(key, value, ttl)

    async def set_async(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        设置缓存（异步版本，同时设置 L1 和 L2）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        # 设置 L1
        l1_success = self._l1.set(key, value, ttl)

        # 设置 L2
        l2_success = True
        if self._l2:
            l2_success = await self._l2.set(key, value, ttl)

        return l1_success and l2_success

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        return self._l1.delete(key)

    def invalidate(self, pattern: str) -> int:
        """
        使缓存失效

        Args:
            pattern: 通配符模式

        Returns:
            删除的条目数
        """
        return self._l1.invalidate(pattern)

    async def invalidate_async(self, pattern: str) -> int:
        """
        使缓存失效（异步版本，同时清除 L1 和 L2）

        Args:
            pattern: 通配符模式

        Returns:
            删除的总条目数
        """
        l1_count = self._l1.invalidate(pattern)

        l2_count = 0
        if self._l2:
            l2_count = await self._l2.invalidate(pattern)

        return l1_count + l2_count

    def clear(self) -> int:
        """
        清空所有缓存

        Returns:
            清除的条目数
        """
        return self._l1.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计

        Returns:
            统计信息
        """
        stats = {
            "l1": self._l1.get_stats().to_dict(),
            "l1_size": self._l1.get_size(),
        }

        if self._l2:
            stats["l2"] = self._l2.get_stats().to_dict()

        return stats

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        return self._l1.exists(key)
