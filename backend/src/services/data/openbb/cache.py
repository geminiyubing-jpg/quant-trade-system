"""
OpenBB 数据缓存模块

提供内存缓存和 Redis 缓存支持，减少外部 API 调用。
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional

from loguru import logger


class DataCache:
    """
    数据缓存类

    支持两级缓存：
    1. 内存缓存（L1）- 快速访问
    2. Redis 缓存（L2）- 跨进程共享

    当 Redis 不可用时，自动降级到纯内存缓存。
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        default_ttl: int = 60,
        max_memory_items: int = 1000,
    ):
        """
        初始化缓存

        Args:
            redis_client: Redis 客户端实例（可选）
            default_ttl: 默认缓存时间（秒）
            max_memory_items: 内存缓存最大条目数
        """
        self._redis = redis_client
        self._default_ttl = default_ttl
        self._max_memory_items = max_memory_items

        # 内存缓存
        # 结构: {key: {"data": Any, "expires_at": float}}
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = asyncio.Lock()

        # 统计信息
        self._hits = 0
        self._misses = 0

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        hash_key = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"openbb:{prefix}:{hash_key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，不存在或已过期返回 None
        """
        # 先检查内存缓存
        async with self._cache_lock:
            mem_entry = self._memory_cache.get(key)
            if mem_entry:
                if time.time() < mem_entry["expires_at"]:
                    self._hits += 1
                    logger.debug(f"缓存命中（内存）: {key}")
                    return mem_entry["data"]
                else:
                    # 已过期，删除
                    del self._memory_cache[key]

        # 检查 Redis 缓存
        if self._redis:
            try:
                redis_data = await self._redis.get(key)
                if redis_data:
                    data = json.loads(redis_data)
                    # 回填内存缓存
                    async with self._cache_lock:
                        self._memory_cache[key] = {
                            "data": data,
                            "expires_at": time.time() + self._default_ttl,
                        }
                    self._hits += 1
                    logger.debug(f"缓存命中（Redis）: {key}")
                    return data
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")

        self._misses += 1
        return None

    async def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存数据

        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl: 缓存时间（秒），默认使用 default_ttl

        Returns:
            是否设置成功
        """
        ttl = ttl or self._default_ttl
        expires_at = time.time() + ttl

        # 设置内存缓存
        async with self._cache_lock:
            # 检查是否需要清理
            if len(self._memory_cache) >= self._max_memory_items:
                await self._cleanup_memory_cache()

            self._memory_cache[key] = {
                "data": data,
                "expires_at": expires_at,
            }

        # 设置 Redis 缓存
        if self._redis:
            try:
                await self._redis.setex(
                    key,
                    ttl,
                    json.dumps(data, default=str),
                )
                logger.debug(f"缓存已设置（Redis）: {key}, TTL={ttl}s")
            except Exception as e:
                logger.warning(f"Redis 写入失败: {e}")

        logger.debug(f"缓存已设置（内存）: {key}, TTL={ttl}s")
        return True

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._cache_lock:
            self._memory_cache.pop(key, None)

        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis 删除失败: {e}")

        return True

    async def clear(self) -> None:
        """清空所有缓存"""
        async with self._cache_lock:
            self._memory_cache.clear()

        if self._redis:
            try:
                # 删除所有 openbb: 开头的键
                keys = await self._redis.keys("openbb:*")
                if keys:
                    await self._redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis 清空失败: {e}")

        logger.info("缓存已清空")

    async def _cleanup_memory_cache(self) -> None:
        """清理过期的内存缓存"""
        now = time.time()
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if v["expires_at"] < now
        ]

        for key in expired_keys:
            del self._memory_cache[key]

        # 如果还是太多，删除最旧的
        if len(self._memory_cache) >= self._max_memory_items:
            # 按过期时间排序，删除最旧的 10%
            sorted_items = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1]["expires_at"],
            )
            to_remove = int(self._max_memory_items * 0.1)
            for key, _ in sorted_items[:to_remove]:
                del self._memory_cache[key]

        logger.debug(f"清理内存缓存: 删除 {len(expired_keys)} 个过期条目")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total * 100 if total > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "memory_items": len(self._memory_cache),
            "redis_enabled": self._redis is not None,
        }


# 全局缓存实例
_cache_instance: Optional[DataCache] = None


def get_cache(
    redis_client: Optional[Any] = None,
    default_ttl: int = 60,
) -> DataCache:
    """
    获取全局缓存实例

    Args:
        redis_client: Redis 客户端（仅首次调用时使用）
        default_ttl: 默认缓存时间

    Returns:
        DataCache 实例
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = DataCache(
            redis_client=redis_client,
            default_ttl=default_ttl,
        )

    return _cache_instance


def cached(
    prefix: str,
    ttl: int = 60,
    key_builder: Optional[callable] = None,
):
    """
    缓存装饰器

    用法:
        @cached("quote", ttl=30)
        async def get_quote(symbol: str):
            ...

    Args:
        prefix: 缓存键前缀
        ttl: 缓存时间（秒）
        key_builder: 自定义键生成函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # 生成缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 默认使用第一个参数作为键的一部分
                primary_arg = args[1] if len(args) > 1 else kwargs.get("symbol", "unknown")
                cache_key = cache._generate_key(prefix, primary_arg)

            # 尝试从缓存获取
            cached_data = await cache.get(cache_key)
            if cached_data is not None:
                return cached_data

            # 调用原函数
            result = await func(*args, **kwargs)

            # 缓存结果
            if result:
                await cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
