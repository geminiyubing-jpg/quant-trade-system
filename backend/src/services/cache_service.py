"""
==============================================
QuantAI Ecosystem - Redis 缓存服务
==============================================

提供多层级缓存策略，优化系统性能。
支持热点数据缓存、会话管理、分布式锁等功能。
"""

import json
import hashlib
import functools
from datetime import datetime, timedelta
from typing import Optional, Any, Callable, Dict, List, Union
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """缓存层级"""
    L1_HOT = "L1_HOT"           # 热点数据 (3秒)
    L2_SESSION = "L2_SESSION"   # 会话数据 (24小时)
    L3_CONFIG = "L3_CONFIG"     # 配置数据 (5分钟)
    L4_MARKET = "L4_MARKET"     # 市场数据 (1分钟)
    L5_RESULT = "L5_RESULT"     # 计算结果 (1小时)


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl_map: Dict[CacheLevel, int] = None

    def __post_init__(self):
        if self.ttl_map is None:
            self.ttl_map = {
                CacheLevel.L1_HOT: 3,        # 3秒
                CacheLevel.L2_SESSION: 86400, # 24小时
                CacheLevel.L3_CONFIG: 300,    # 5分钟
                CacheLevel.L4_MARKET: 60,     # 1分钟
                CacheLevel.L5_RESULT: 3600,   # 1小时
            }

    def get_ttl(self, level: CacheLevel) -> int:
        return self.ttl_map.get(level, 60)


class CacheService:
    """
    Redis 缓存服务

    功能：
    - 多层级缓存策略
    - 自动序列化/反序列化
    - 缓存装饰器
    - 分布式锁
    - 批量操作
    """

    def __init__(self, redis_client=None, config: Optional[CacheConfig] = None):
        self.redis = redis_client
        self.config = config or CacheConfig()
        # 本地缓存（无 Redis 时使用）
        self._local_cache: Dict[str, Dict] = {}

    # ==========================================
    # 基础操作
    # ==========================================

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if self.redis:
                data = self.redis.get(key)
                if data:
                    return json.loads(data)
            else:
                cached = self._local_cache.get(key)
                if cached:
                    if datetime.utcnow() > cached.get("expires_at", datetime.max):
                        del self._local_cache[key]
                        return None
                    return cached.get("value")
            return None
        except Exception as e:
            logger.error(f"缓存读取失败: {key}, 错误: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        level: CacheLevel = CacheLevel.L4_MARKET,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            actual_ttl = ttl or self.config.get_ttl(level)

            if self.redis:
                serialized = json.dumps(value, default=str)
                self.redis.setex(key, actual_ttl, serialized)
            else:
                self._local_cache[key] = {
                    "value": value,
                    "expires_at": datetime.utcnow() + timedelta(seconds=actual_ttl)
                }
            return True
        except Exception as e:
            logger.error(f"缓存写入失败: {key}, 错误: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis:
                self.redis.delete(key)
            else:
                self._local_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"缓存删除失败: {key}, 错误: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        try:
            if self.redis:
                keys = self.redis.keys(pattern)
                if keys:
                    return self.redis.delete(*keys)
            else:
                keys_to_delete = [k for k in self._local_cache if k.startswith(pattern.replace("*", ""))]
                for k in keys_to_delete:
                    del self._local_cache[k]
                return len(keys_to_delete)
            return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败: {pattern}, 错误: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self.redis:
            return bool(self.redis.exists(key))
        return key in self._local_cache

    # ==========================================
    # 高级操作
    # ==========================================

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        level: CacheLevel = CacheLevel.L4_MARKET,
        ttl: Optional[int] = None
    ) -> Any:
        """获取缓存，不存在则计算并缓存"""
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        if value is not None:
            self.set(key, value, level, ttl)
        return value

    async def get_or_set_async(
        self,
        key: str,
        factory: Callable[[], Any],
        level: CacheLevel = CacheLevel.L4_MARKET,
        ttl: Optional[int] = None
    ) -> Any:
        """异步获取缓存，不存在则计算并缓存"""
        value = self.get(key)
        if value is not None:
            return value

        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        if value is not None:
            self.set(key, value, level, ttl)
        return value

    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取"""
        result = {}
        if self.redis:
            values = self.redis.mget(keys)
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except:
                        pass
        else:
            for key in keys:
                value = self.get(key)
                if value is not None:
                    result[key] = value
        return result

    def mset(self, mapping: Dict[str, Any], level: CacheLevel = CacheLevel.L4_MARKET) -> bool:
        """批量设置"""
        try:
            ttl = self.config.get_ttl(level)
            if self.redis:
                pipe = self.redis.pipeline()
                for key, value in mapping.items():
                    serialized = json.dumps(value, default=str)
                    pipe.setex(key, ttl, serialized)
                pipe.execute()
            else:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                for key, value in mapping.items():
                    self._local_cache[key] = {"value": value, "expires_at": expires_at}
            return True
        except Exception as e:
            logger.error(f"批量设置缓存失败: {e}")
            return False

    # ==========================================
    # 装饰器
    # ==========================================

    def cached(
        self,
        key_prefix: str,
        level: CacheLevel = CacheLevel.L4_MARKET,
        ttl: Optional[int] = None,
        key_builder: Optional[Callable] = None
    ):
        """
        缓存装饰器

        用法:
            @cache_service.cached("user_profile", level=CacheLevel.L3_CONFIG)
            def get_user_profile(user_id: str):
                return db.query(User).filter(User.id == user_id).first()
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 构建缓存键
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # 默认使用参数生成键
                    key_parts = [key_prefix]
                    if args:
                        key_parts.extend(str(arg) for arg in args)
                    if kwargs:
                        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = ":".join(key_parts)

                # 尝试获取缓存
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_value

                # 执行函数
                result = func(*args, **kwargs)

                # 缓存结果
                if result is not None:
                    self.set(cache_key, result, level, ttl)
                    logger.debug(f"缓存写入: {cache_key}")

                return result

            return wrapper
        return decorator

    def cached_async(
        self,
        key_prefix: str,
        level: CacheLevel = CacheLevel.L4_MARKET,
        ttl: Optional[int] = None
    ):
        """异步缓存装饰器"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # 构建缓存键
                key_parts = [key_prefix]
                if args:
                    key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

                # 尝试获取缓存
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 缓存结果
                if result is not None:
                    self.set(cache_key, result, level, ttl)

                return result

            return wrapper
        return decorator

    # ==========================================
    # 分布式锁
    # ==========================================

    def acquire_lock(
        self,
        lock_name: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: int = 30
    ) -> bool:
        """获取分布式锁"""
        if self.redis:
            import time
            start_time = time.time()
            lock_key = f"lock:{lock_name}"
            identifier = str(datetime.utcnow().timestamp())

            while True:
                acquired = self.redis.set(lock_key, identifier, nx=True, ex=timeout)
                if acquired:
                    return True

                if not blocking:
                    return False

                if time.time() - start_time > blocking_timeout:
                    return False

                time.sleep(0.1)
        else:
            # 本地锁
            lock_key = f"lock:{lock_name}"
            if lock_key in self._local_cache:
                return False
            self._local_cache[lock_key] = {"expires_at": datetime.utcnow() + timedelta(seconds=timeout)}
            return True

    def release_lock(self, lock_name: str) -> bool:
        """释放分布式锁"""
        lock_key = f"lock:{lock_name}"
        if self.redis:
            self.redis.delete(lock_key)
        else:
            self._local_cache.pop(lock_key, None)
        return True

    # ==========================================
    # 业务缓存方法
    # ==========================================

    def cache_stock_quote(self, symbol: str, quote: Dict) -> bool:
        """缓存股票行情"""
        key = f"quote:{symbol}"
        return self.set(key, quote, level=CacheLevel.L1_HOT)

    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """获取缓存的股票行情"""
        key = f"quote:{symbol}"
        return self.get(key)

    def cache_user_session(self, user_id: str, session_data: Dict) -> bool:
        """缓存用户会话"""
        key = f"session:{user_id}"
        return self.set(key, session_data, level=CacheLevel.L2_SESSION)

    def get_user_session(self, user_id: str) -> Optional[Dict]:
        """获取用户会话"""
        key = f"session:{user_id}"
        return self.get(key)

    def cache_strategy_config(self, strategy_id: str, config: Dict) -> bool:
        """缓存策略配置"""
        key = f"strategy:config:{strategy_id}"
        return self.set(key, config, level=CacheLevel.L3_CONFIG)

    def get_strategy_config(self, strategy_id: str) -> Optional[Dict]:
        """获取缓存的策略配置"""
        key = f"strategy:config:{strategy_id}"
        return self.get(key)

    def cache_backtest_result(self, backtest_id: str, result: Dict) -> bool:
        """缓存回测结果"""
        key = f"backtest:result:{backtest_id}"
        return self.set(key, result, level=CacheLevel.L5_RESULT)

    def get_backtest_result(self, backtest_id: str) -> Optional[Dict]:
        """获取缓存的回测结果"""
        key = f"backtest:result:{backtest_id}"
        return self.get(key)

    def invalidate_user_cache(self, user_id: str) -> int:
        """清除用户相关缓存"""
        return self.delete_pattern(f"*:{user_id}:*")

    def invalidate_strategy_cache(self, strategy_id: str) -> int:
        """清除策略相关缓存"""
        return self.delete_pattern(f"strategy:*:{strategy_id}*")

    # ==========================================
    # 统计和监控
    # ==========================================

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "backend": "redis" if self.redis else "local",
        }

        if self.redis:
            info = self.redis.info()
            stats.update({
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": self.redis.dbsize(),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_misses", 1), 1),
            })
        else:
            stats.update({
                "total_keys": len(self._local_cache),
                "used_memory": "N/A",
            })

        return stats


# 单例实例
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def init_cache_service(redis_client=None, config: Optional[CacheConfig] = None):
    """初始化缓存服务"""
    global _cache_service
    _cache_service = CacheService(redis_client=redis_client, config=config)
    return _cache_service
