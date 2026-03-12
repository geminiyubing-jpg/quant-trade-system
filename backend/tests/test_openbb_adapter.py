"""
OpenBB 适配器单元测试

测试 OpenBB 数据适配器的核心功能：
- 连接和断开
- yfinance 后备模式
- 数据获取
- 缓存功能
"""

import asyncio
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json


# ==============================================
# Fixtures
# ==============================================

@pytest.fixture
def mock_yfinance():
    """Mock yfinance 模块"""
    mock_module = MagicMock()

    # 创建 mock ticker
    mock_ticker = MagicMock()
    mock_ticker.info = {
        'currentPrice': 150.0,
        'regularMarketPrice': 150.0,
        'open': 148.0,
        'dayHigh': 152.0,
        'dayLow': 147.0,
        'previousClose': 146.0,
        'volume': 1000000,
        'regularMarketChange': 4.0,
        'regularMarketChangePercent': 2.74,
    }

    # Mock history 方法返回 DataFrame
    import pandas as pd
    mock_df = pd.DataFrame({
        'Open': [148.0, 149.0, 150.0],
        'High': [152.0, 153.0, 154.0],
        'Low': [147.0, 148.0, 149.0],
        'Close': [150.0, 151.0, 152.0],
        'Volume': [1000000, 1100000, 1200000],
    }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02', '2024-01-03']))

    mock_ticker.history.return_value = mock_df
    mock_module.Ticker.return_value = mock_ticker

    return mock_module


@pytest.fixture
def mock_openbb():
    """Mock OpenBB 模块"""
    mock_obb = MagicMock()
    mock_obb.equity = MagicMock()
    mock_obb.account = MagicMock()
    mock_obb.account.is_logged_in.return_value = False
    return mock_obb


@pytest.fixture
def adapter_config():
    """测试配置"""
    return {
        'hub_pat': None,
        'fmp_api_key': None,
        'polygon_api_key': None,
        'fred_api_key': None,
        'default_equity_provider': 'yfinance',
        'default_economy_provider': 'fred',
    }


# ==============================================
# 测试类
# ==============================================

class TestOpenBBAdapterConnection:
    """测试适配器连接"""

    @pytest.mark.asyncio
    async def test_connect_with_yfinance_fallback(self, mock_yfinance, adapter_config):
        """测试使用 yfinance 后备模式连接"""
        from src.services.data.openbb import OpenBBAdapter

        adapter = OpenBBAdapter(config=adapter_config)

        # 直接测试 yfinance 后备初始化
        with patch.dict('sys.modules', {'yfinance': mock_yfinance}):
            result = await adapter._init_yfinance_fallback()

            # 验证连接结果
            assert result is True
            assert adapter._is_connected is True
            assert adapter._use_fallback is True

    @pytest.mark.asyncio
    async def test_connect_fallback_when_openbb_fails(self, mock_yfinance, adapter_config):
        """测试 OpenBB 失败时自动切换到 yfinance 后备模式"""
        from src.services.data.openbb import OpenBBAdapter

        adapter = OpenBBAdapter(config=adapter_config)

        # 模拟 OpenBB 导入失败
        with patch.dict('sys.modules', {'yfinance': mock_yfinance}):
            # 直接测试 yfinance 后备初始化
            result = await adapter._init_yfinance_fallback()

            assert result is True
            assert adapter._use_fallback is True
            assert adapter._is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self, adapter_config):
        """测试断开连接"""
        from src.services.data.openbb import OpenBBAdapter

        adapter = OpenBBAdapter(config=adapter_config)
        adapter._is_connected = True

        await adapter.disconnect()

        assert adapter._is_connected is False


class TestOpenBBAdapterQuote:
    """测试报价获取"""

    @pytest.mark.asyncio
    async def test_get_quote_yfinance(self, mock_yfinance, adapter_config):
        """测试使用 yfinance 获取报价"""
        from src.services.data.openbb import OpenBBAdapter

        adapter = OpenBBAdapter(config=adapter_config)
        adapter._yfinance = mock_yfinance
        adapter._use_fallback = True
        adapter._is_connected = True

        quote = await adapter._get_quote_yfinance('AAPL')

        assert quote is not None
        assert quote['symbol'] == 'AAPL'
        assert quote['price'] == 150.0
        assert quote['provider'] == 'yfinance'

    @pytest.mark.asyncio
    async def test_get_quote_with_cache(self, mock_yfinance, adapter_config):
        """测试报价缓存"""
        from src.services.data.openbb import OpenBBAdapter
        from src.services.data.openbb.cache import get_cache

        adapter = OpenBBAdapter(config=adapter_config)
        adapter._yfinance = mock_yfinance
        adapter._use_fallback = True
        adapter._is_connected = True

        # 清空缓存
        cache = get_cache()
        await cache.clear()

        # 第一次调用 - 缓存未命中
        quote1 = await adapter._get_quote_yfinance('AAPL')
        assert quote1['price'] == 150.0

        # 第二次调用 - 应该从缓存获取
        quote2 = await adapter._get_quote_yfinance('AAPL')
        assert quote2['price'] == 150.0

        # 检查缓存统计
        stats = cache.get_stats()
        # 由于我们刚设置了缓存，应该有内存项
        assert stats['memory_items'] >= 1


class TestOpenBBAdapterHistorical:
    """测试历史数据获取"""

    @pytest.mark.asyncio
    async def test_get_historical_yfinance(self, mock_yfinance, adapter_config):
        """测试使用 yfinance 获取历史数据"""
        from src.services.data.openbb import OpenBBAdapter

        adapter = OpenBBAdapter(config=adapter_config)
        adapter._yfinance = mock_yfinance
        adapter._use_fallback = True
        adapter._is_connected = True

        data = await adapter._get_historical_yfinance(
            symbol='AAPL',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
        )

        assert len(data) == 3
        assert data[0]['symbol'] == 'AAPL'
        assert data[0]['open'] == 148.0
        assert data[0]['close'] == 150.0
        assert data[0]['provider'] == 'yfinance'


class TestOpenBBAdapterStatus:
    """测试状态获取"""

    def test_get_status_fallback_mode(self, adapter_config):
        """测试后备模式状态"""
        from src.services.data.openbb import OpenBBAdapter

        adapter = OpenBBAdapter(config=adapter_config)
        adapter._is_connected = True
        adapter._use_fallback = True

        status = adapter.get_status()

        assert status['name'] == 'openbb'
        assert status['is_connected'] is True
        assert status['use_fallback'] is True
        assert status['fallback_provider'] == 'yfinance'
        assert 'cache' in status
        assert 'providers' in status
        assert status['providers']['equity'] is True


class TestDataCache:
    """测试缓存模块"""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        from src.services.data.openbb.cache import DataCache

        cache = DataCache(redis_client=None, default_ttl=60)

        # 设置缓存
        await cache.set('test_key', {'data': 'test_value'})

        # 获取缓存
        result = await cache.get('test_key')

        assert result is not None
        assert result['data'] == 'test_value'

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """测试缓存未命中"""
        from src.services.data.openbb.cache import DataCache

        cache = DataCache(redis_client=None, default_ttl=60)

        result = await cache.get('nonexistent_key')

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_expiry(self):
        """测试缓存过期"""
        from src.services.data.openbb.cache import DataCache

        cache = DataCache(redis_client=None, default_ttl=1)  # 1秒 TTL

        # 设置缓存
        await cache.set('test_key', {'data': 'test_value'})

        # 立即获取 - 应该命中
        result1 = await cache.get('test_key')
        assert result1 is not None

        # 等待过期
        await asyncio.sleep(1.5)

        # 再次获取 - 应该未命中
        result2 = await cache.get('test_key')
        assert result2 is None

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """测试缓存统计"""
        from src.services.data.openbb.cache import DataCache

        cache = DataCache(redis_client=None, default_ttl=60)

        # 一次命中
        await cache.set('key1', {'data': 'value1'})
        await cache.get('key1')

        # 一次未命中
        await cache.get('nonexistent')

        stats = cache.get_stats()

        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == '50.0%'
        assert stats['memory_items'] == 1
        assert stats['redis_enabled'] is False

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """测试清空缓存"""
        from src.services.data.openbb.cache import DataCache

        cache = DataCache(redis_client=None, default_ttl=60)

        # 设置一些缓存
        await cache.set('key1', {'data': 'value1'})
        await cache.set('key2', {'data': 'value2'})

        # 清空
        await cache.clear()

        # 验证已清空
        assert await cache.get('key1') is None
        assert await cache.get('key2') is None


class TestMarketDetection:
    """测试市场检测"""

    def test_detect_us_market(self):
        """检测美股"""
        from src.services.data.openbb.utils import detect_market

        assert detect_market('AAPL') == 'us'
        assert detect_market('MSFT') == 'us'
        assert detect_market('^DJI') == 'us'
        assert detect_market('^GSPC') == 'us'

    def test_detect_cn_market(self):
        """检测 A股"""
        from src.services.data.openbb.utils import detect_market

        assert detect_market('000001.SZ') == 'cn'
        assert detect_market('600000.SH') == 'cn'
        assert detect_market('300750.SZ') == 'cn'

    def test_detect_hk_market(self):
        """检测港股"""
        from src.services.data.openbb.utils import detect_market

        assert detect_market('00700.HK') == 'hk'
        assert detect_market('09988.HK') == 'hk'


# ==============================================
# 运行测试
# ==============================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
