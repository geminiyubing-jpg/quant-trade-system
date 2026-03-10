"""
==============================================
QuantAI Ecosystem - 宏观数据管道
==============================================

从多个数据源获取宏观经济指标数据：
- FRED (美国经济数据)
- BLS (美国劳工数据)
- NBS (中国国家统计局)
- Eurostat (欧盟统计数据)
- Yahoo Finance (市场数据)
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import os

from .merrill_clock_engine import MacroIndicator

logger = logging.getLogger(__name__)


class DataSource(str, Enum):
    """数据源"""
    FRED = "fred"              # 美联储经济数据
    BLS = "bls"                # 美国劳工统计局
    NBS = "nbs"                # 中国国家统计局
    EUROSTAT = "eurostat"      # 欧盟统计局
    YAHOO = "yahoo"            # Yahoo Finance
    AKSHARE = "akshare"        # AkShare
    TUSHARE = "tushare"        # Tushare


@dataclass
class DataSeries:
    """数据序列"""
    series_id: str
    name: str
    country: str
    frequency: str
    units: str
    values: List[Dict]         # [{date, value}, ...]
    last_updated: datetime
    source: DataSource


@dataclass
class PipelineConfig:
    """管道配置"""
    update_frequency: int = 5     # 更新频率 (小时)
    retry_count: int = 3
    timeout: int = 30
    cache_ttl: int = 3600        # 缓存时间 (秒)


class MacroDataPipeline:
    """
    宏观数据管道

    功能：
    - 多数据源集成
    - 自动数据更新
    - 数据缓存
    - 错误重试
    """

    # FRED关键指标映射
    FRED_INDICATORS = {
        'gdp_growth': {'series_id': 'GDP', 'name': 'GDP增长率', 'frequency': 'quarterly'},
        'cpi': {'series_id': 'CPIAUCSL', 'name': 'CPI', 'frequency': 'monthly'},
        'core_pce': {'series_id': 'PCEPILFE', 'name': '核心PCE', 'frequency': 'monthly'},
        'unemployment_rate': {'series_id': 'UNRATE', 'name': '失业率', 'frequency': 'monthly'},
        'pmi': {'series_id': 'MANEMP', 'name': '制造业就业', 'frequency': 'monthly'},
        'fed_funds_rate': {'series_id': 'FEDFUNDS', 'name': '联邦基金利率', 'frequency': 'monthly'},
        '10y_treasury': {'series_id': 'GS10', 'name': '10年期国债', 'frequency': 'monthly'},
        'industrial_production': {'series_id': 'INDPRO', 'name': '工业生产指数', 'frequency': 'monthly'}
    }

    # 中国宏观指标映射
    CHINA_INDICATORS = {
        'gdp_growth': {'name': 'GDP增长率', 'frequency': 'quarterly'},
        'cpi': {'name': 'CPI', 'frequency': 'monthly'},
        'ppi': {'name': 'PPI', 'frequency': 'monthly'},
        'pmi': {'name': 'PMI', 'frequency': 'monthly'},
        'unemployment_rate': {'name': '城镇调查失业率', 'frequency': 'monthly'},
        'industrial_production': {'name': '工业增加值', 'frequency': 'monthly'},
        'retail_sales': {'name': '社会消费品零售总额', 'frequency': 'monthly'},
        'fixed_asset_investment': {'name': '固定资产投资', 'frequency': 'monthly'}
    }

    # 欧盟指标映射
    EU_INDICATORS = {
        'gdp_growth': {'name': 'GDP增长率', 'frequency': 'quarterly'},
        'cpi': {'name': 'HICP', 'frequency': 'monthly'},
        'unemployment_rate': {'name': '失业率', 'frequency': 'monthly'}
    }

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        db_connection=None,
        cache_service=None
    ):
        self.config = config or PipelineConfig()
        self.db = db_connection
        self.cache = cache_service
        self.api_keys = self._load_api_keys()
        self.session: Optional[aiohttp.ClientSession] = None
        self._indicator_cache: Dict[str, MacroIndicator] = {}

    async def initialize(self):
        """初始化"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        logger.info("宏观数据管道初始化完成")

    async def close(self):
        """关闭"""
        if self.session:
            await self.session.close()
            logger.info("宏观数据管道已关闭")

    def _load_api_keys(self) -> Dict[str, str]:
        """加载API密钥"""
        return {
            'fred': os.getenv('FRED_API_KEY', ''),
            'bls': os.getenv('BLS_API_KEY', ''),
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_KEY', ''),
            'tushare': os.getenv('TUSHARE_TOKEN', ''),
        }

    async def fetch_all_indicators(
        self,
        countries: List[str] = None
    ) -> Dict[str, MacroIndicator]:
        """
        获取所有指标

        Args:
            countries: 国家列表，默认 ['US', 'CN']

        Returns:
            Dict[str, MacroIndicator]: 指标字典
        """
        countries = countries or ['US', 'CN']
        all_indicators = {}

        for country in countries:
            logger.info(f"获取 {country} 宏观指标...")
            indicators = await self._fetch_country_indicators(country)
            all_indicators.update(indicators)

        logger.info(f"共获取 {len(all_indicators)} 个指标")
        return all_indicators

    async def _fetch_country_indicators(self, country: str) -> Dict[str, MacroIndicator]:
        """获取特定国家的指标"""
        if country == 'US':
            return await self._fetch_us_indicators()
        elif country == 'CN':
            return await self._fetch_china_indicators()
        elif country == 'EU':
            return await self._fetch_eu_indicators()
        else:
            logger.warning(f"不支持的国家: {country}")
            return {}

    async def _fetch_us_indicators(self) -> Dict[str, MacroIndicator]:
        """获取美国宏观指标"""
        indicators = {}

        # 尝试从FRED获取
        fred_data = await self._fetch_fred_indicators()
        indicators.update(fred_data)

        # 尝试从BLS获取补充数据
        bls_data = await self._fetch_bls_indicators()
        indicators.update(bls_data)

        return indicators

    async def _fetch_fred_indicators(self) -> Dict[str, MacroIndicator]:
        """获取FRED数据"""
        indicators = {}

        if not self.api_keys.get('fred'):
            logger.warning("未配置FRED API密钥，使用模拟数据")
            return self._get_mock_us_indicators()

        for indicator_id, config in self.FRED_INDICATORS.items():
            try:
                # 检查缓存
                cache_key = f"macro:fred:{indicator_id}"
                if self.cache:
                    cached = await self.cache.get(cache_key)
                    if cached:
                        indicators[indicator_id] = self._parse_cached_indicator(cached)
                        continue

                # API调用
                series_id = config['series_id']
                url = "https://api.stlouisfed.org/fred/series/observations"
                params = {
                    'series_id': series_id,
                    'api_key': self.api_keys['fred'],
                    'file_type': 'json',
                    'limit': 2,
                    'sort_order': 'desc'
                }

                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        indicator = self._parse_fred_response(indicator_id, config, data)
                        if indicator:
                            indicators[indicator_id] = indicator

                            # 缓存
                            if self.cache:
                                await self.cache.set(
                                    cache_key,
                                    self._serialize_indicator(indicator),
                                    ttl=self.config.cache_ttl
                                )

            except Exception as e:
                logger.error(f"获取FRED指标 {indicator_id} 失败: {e}")

        return indicators

    async def _fetch_bls_indicators(self) -> Dict[str, MacroIndicator]:
        """获取BLS数据"""
        # BLS指标获取逻辑
        return {}

    async def _fetch_china_indicators(self) -> Dict[str, MacroIndicator]:
        """获取中国宏观数据"""
        # 使用AkShare或Tushare获取中国数据
        # 这里返回模拟数据用于演示
        return self._get_mock_china_indicators()

    async def _fetch_eu_indicators(self) -> Dict[str, MacroIndicator]:
        """获取欧盟宏观数据"""
        return self._get_mock_eu_indicators()

    def _parse_fred_response(
        self,
        indicator_id: str,
        config: Dict,
        data: Dict
    ) -> Optional[MacroIndicator]:
        """解析FRED响应"""
        try:
            observations = data.get('observations', [])
            if len(observations) < 2:
                return None

            current = float(observations[0].get('value', 0))
            previous = float(observations[1].get('value', 0))

            # 计算同比和环比变化
            yoy_change = (current - previous) / abs(previous) if previous != 0 else 0
            mom_change = yoy_change  # 简化处理

            return MacroIndicator(
                indicator_id=f"US_{indicator_id}",
                name=config['name'],
                current_value=current,
                previous_value=previous,
                yoy_change=yoy_change,
                mom_change=mom_change,
                trend='upward' if yoy_change > 0 else ('downward' if yoy_change < 0 else 'stable'),
                last_updated=datetime.utcnow(),
                data_source='FRED',
                frequency=config['frequency']
            )
        except Exception as e:
            logger.error(f"解析FRED响应失败: {e}")
            return None

    def _get_mock_us_indicators(self) -> Dict[str, MacroIndicator]:
        """获取模拟美国指标"""
        now = datetime.utcnow()
        return {
            'US_gdp_growth': MacroIndicator(
                indicator_id='US_gdp_growth',
                name='GDP增长率',
                current_value=2.5,
                previous_value=2.3,
                yoy_change=0.025,
                mom_change=0.005,
                trend='upward',
                last_updated=now,
                data_source='MOCK',
                frequency='quarterly'
            ),
            'US_cpi': MacroIndicator(
                indicator_id='US_cpi',
                name='CPI',
                current_value=310.5,
                previous_value=308.2,
                yoy_change=0.032,
                mom_change=0.007,
                trend='upward',
                last_updated=now,
                data_source='MOCK',
                frequency='monthly'
            ),
            'US_unemployment_rate': MacroIndicator(
                indicator_id='US_unemployment_rate',
                name='失业率',
                current_value=3.8,
                previous_value=3.9,
                yoy_change=-0.026,
                mom_change=-0.01,
                trend='downward',
                last_updated=now,
                data_source='MOCK',
                frequency='monthly'
            ),
            'US_pmi': MacroIndicator(
                indicator_id='US_pmi',
                name='PMI',
                current_value=52.3,
                previous_value=51.8,
                yoy_change=0.025,
                mom_change=0.01,
                trend='upward',
                last_updated=now,
                data_source='MOCK',
                frequency='monthly'
            ),
        }

    def _get_mock_china_indicators(self) -> Dict[str, MacroIndicator]:
        """获取模拟中国指标"""
        now = datetime.utcnow()
        return {
            'CN_gdp_growth': MacroIndicator(
                indicator_id='CN_gdp_growth',
                name='GDP增长率',
                current_value=5.2,
                previous_value=5.0,
                yoy_change=0.052,
                mom_change=0.02,
                trend='upward',
                last_updated=now,
                data_source='MOCK',
                frequency='quarterly'
            ),
            'CN_cpi': MacroIndicator(
                indicator_id='CN_cpi',
                name='CPI',
                current_value=102.5,
                previous_value=102.2,
                yoy_change=0.025,
                mom_change=0.003,
                trend='stable',
                last_updated=now,
                data_source='MOCK',
                frequency='monthly'
            ),
            'CN_pmi': MacroIndicator(
                indicator_id='CN_pmi',
                name='PMI',
                current_value=50.5,
                previous_value=49.8,
                yoy_change=0.015,
                mom_change=0.014,
                trend='upward',
                last_updated=now,
                data_source='MOCK',
                frequency='monthly'
            ),
        }

    def _get_mock_eu_indicators(self) -> Dict[str, MacroIndicator]:
        """获取模拟欧盟指标"""
        now = datetime.utcnow()
        return {
            'EU_gdp_growth': MacroIndicator(
                indicator_id='EU_gdp_growth',
                name='GDP增长率',
                current_value=1.2,
                previous_value=1.0,
                yoy_change=0.012,
                mom_change=0.005,
                trend='stable',
                last_updated=now,
                data_source='MOCK',
                frequency='quarterly'
            ),
            'EU_cpi': MacroIndicator(
                indicator_id='EU_cpi',
                name='HICP',
                current_value=128.5,
                previous_value=127.8,
                yoy_change=0.028,
                mom_change=0.005,
                trend='upward',
                last_updated=now,
                data_source='MOCK',
                frequency='monthly'
            ),
        }

    def _parse_cached_indicator(self, cached: str) -> MacroIndicator:
        """解析缓存指标"""
        data = json.loads(cached)
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return MacroIndicator(**data)

    def _serialize_indicator(self, indicator: MacroIndicator) -> str:
        """序列化指标"""
        return json.dumps(indicator.to_dict())

    async def update_indicators(self) -> Dict[str, MacroIndicator]:
        """更新所有指标"""
        return await self.fetch_all_indicators()

    def get_cached_indicator(self, indicator_id: str) -> Optional[MacroIndicator]:
        """获取缓存指标"""
        return self._indicator_cache.get(indicator_id)


# 单例实例
_macro_data_pipeline: Optional[MacroDataPipeline] = None


async def get_macro_data_pipeline() -> MacroDataPipeline:
    """获取宏观数据管道实例"""
    global _macro_data_pipeline
    if _macro_data_pipeline is None:
        _macro_data_pipeline = MacroDataPipeline()
        await _macro_data_pipeline.initialize()
    return _macro_data_pipeline
