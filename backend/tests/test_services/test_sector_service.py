"""
板块分析服务单元测试

测试板块数据获取、板块统计、成分股分析等功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

from src.services.data.akshare import AkShareDataSource


# ==============================================
# 测试数据
# ==============================================

def create_mock_sector_data():
    """创建模拟板块数据"""
    return [
        {'name': '半导体', 'code': 'BK0501', 'change_pct': 2.5, 'amount': 15000000000},
        {'name': '计算机', 'code': 'BK0502', 'change_pct': 1.8, 'amount': 12000000000},
        {'name': '通信', 'code': 'BK0503', 'change_pct': -0.5, 'amount': 8000000000},
        {'name': '新能源', 'code': 'BK0504', 'change_pct': 3.2, 'amount': 20000000000},
        {'name': '医药生物', 'code': 'BK0505', 'change_pct': -1.2, 'amount': 10000000000},
    ]


def create_mock_sector_stocks():
    """创建模拟板块成分股数据"""
    return [
        {'symbol': '600519.SH', 'name': '贵州茅台', 'price': 1850.00, 'change_pct': 2.5},
        {'symbol': '000858.SZ', 'name': '五粮液', 'price': 160.00, 'change_pct': 1.8},
        {'symbol': '000568.SZ', 'name': '泸州老窖', 'price': 220.00, 'change_pct': 3.2},
        {'symbol': '002304.SZ', 'name': '洋河股份', 'price': 145.00, 'change_pct': -0.5},
        {'symbol': '000596.SZ', 'name': '古井贡酒', 'price': 260.00, 'change_pct': 1.2},
    ]


# ==============================================
# AkShareDataSource 板块功能测试
# ==============================================

class TestAkShareDataSource:
    """AkShare数据源测试"""

    @pytest.fixture
    def mock_akshare(self):
        """创建模拟AkShare"""
        with patch('src.services.data.akshare.ak') as mock_ak:
            yield mock_ak

    def test_get_industry_sectors_success(self, mock_akshare):
        """测试成功获取行业板块"""
        # 准备模拟数据
        mock_df = pd.DataFrame({
            '板块名称': ['半导体', '计算机', '通信'],
            '板块代码': ['BK0501', 'BK0502', 'BK0503'],
            '涨跌幅': [2.5, 1.8, -0.5],
            '总市值': [1500000000000, 1200000000000, 800000000000],
        })
        mock_akshare.stock_board_industry_name_em.return_value = mock_df

        # 创建数据源实例并调用
        data_source = AkShareDataSource()
        result = data_source.get_industry_sectors()

        # 验证结果
        assert result is not None
        assert len(result) == 3

    def test_get_concept_sectors_success(self, mock_akshare):
        """测试成功获取概念板块"""
        mock_df = pd.DataFrame({
            '板块名称': ['人工智能', '元宇宙', '新能源车'],
            '板块代码': ['BK0601', 'BK0602', 'BK0603'],
            '涨跌幅': [3.5, -1.2, 2.1],
        })
        mock_akshare.stock_board_concept_name_em.return_value = mock_df

        data_source = AkShareDataSource()
        result = data_source.get_concept_sectors()

        assert result is not None
        assert len(result) == 3

    def test_get_region_sectors_success(self, mock_akshare):
        """测试成功获取地域板块"""
        mock_df = pd.DataFrame({
            '板块名称': ['北京', '上海', '广东'],
            '板块代码': ['BK0701', 'BK0702', 'BK0703'],
            '涨跌幅': [0.8, 1.2, 0.5],
        })
        mock_akshare.stock_board_region_name_em.return_value = mock_df

        data_source = AkShareDataSource()
        result = data_source.get_region_sectors()

        assert result is not None
        assert len(result) == 3

    def test_get_sector_stocks_success(self, mock_akshare):
        """测试成功获取板块成分股"""
        mock_df = pd.DataFrame({
            '代码': ['600519', '000858', '000568'],
            '名称': ['贵州茅台', '五粮液', '泸州老窖'],
            '最新价': [1850.00, 160.00, 220.00],
            '涨跌幅': [2.5, 1.8, 3.2],
        })
        mock_akshare.stock_board_industry_cons_em.return_value = mock_df

        data_source = AkShareDataSource()
        result = data_source.get_sector_stocks('白酒', 'industry')

        assert result is not None
        assert len(result) == 3

    def test_get_sector_stats_success(self, mock_akshare):
        """测试成功获取板块统计"""
        mock_df = pd.DataFrame({
            '板块名称': ['半导体', '计算机', '通信'],
            '涨跌幅': [2.5, 1.8, -0.5],
            '成交额': [15000000000, 12000000000, 8000000000],
            '换手率': [5.2, 4.8, 3.5],
        })
        mock_akshare.stock_board_industry_name_em.return_value = mock_df

        data_source = AkShareDataSource()
        result = data_source.get_all_sectors_stats('industry')

        assert result is not None
        assert 'stats' in result or isinstance(result, list)


# ==============================================
# 板块统计计算测试
# ==============================================

class TestSectorStatsCalculation:
    """板块统计计算测试"""

    def test_calculate_sector_ranking(self):
        """测试板块排名计算"""
        sectors = create_mock_sector_data()

        # 按涨跌幅排序
        sorted_sectors = sorted(sectors, key=lambda x: x['change_pct'], reverse=True)

        # 验证排序结果
        assert sorted_sectors[0]['name'] == '新能源'
        assert sorted_sectors[-1]['name'] == '医药生物'

    def test_calculate_market_sentiment(self):
        """测试市场情绪计算"""
        sectors = create_mock_sector_data()

        # 计算上涨/下跌板块数量
        up_count = len([s for s in sectors if s['change_pct'] > 0])
        down_count = len([s for s in sectors if s['change_pct'] < 0])

        # 验证结果
        assert up_count == 3
        assert down_count == 2

    def test_calculate_sector_concentration(self):
        """测试板块集中度计算"""
        sectors = create_mock_sector_data()
        total_amount = sum(s['amount'] for s in sectors)

        # 计算各板块成交额占比
        for sector in sectors:
            sector['amount_ratio'] = sector['amount'] / total_amount

        # 验证占比之和为1
        total_ratio = sum(s['amount_ratio'] for s in sectors)
        assert abs(total_ratio - 1.0) < 0.0001

    def test_identify_leading_stocks(self):
        """测试识别领涨股"""
        stocks = create_mock_sector_stocks()

        # 找出涨幅最大的股票
        leading_stock = max(stocks, key=lambda x: x['change_pct'])

        # 验证结果
        assert leading_stock['name'] == '泸州老窖'
        assert leading_stock['change_pct'] == 3.2


# ==============================================
# 板块轮动分析测试
# ==============================================

class TestSectorRotation:
    """板块轮动分析测试"""

    def test_detect_hot_sectors(self):
        """测试识别热门板块"""
        # 模拟近5日板块涨跌幅
        sector_trends = {
            '半导体': [1.5, 2.0, 1.8, 2.5, 3.0],  # 持续上涨
            '计算机': [0.5, -0.2, 0.8, 1.2, 1.5],  # 震荡上行
            '通信': [-1.0, -0.5, 0.2, 0.5, 0.8],   # 触底反弹
            '医药': [-0.5, -1.0, -0.8, -1.2, -0.5], # 持续下跌
        }

        # 计算近5日累计涨跌幅
        cumulative_returns = {
            sector: sum(returns) for sector, returns in sector_trends.items()
        }

        # 识别热门板块（累计涨幅前2）
        hot_sectors = sorted(
            cumulative_returns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:2]

        # 验证结果
        assert hot_sectors[0][0] == '半导体'
        assert len(hot_sectors) == 2

    def test_detect_sector_momentum(self):
        """测试板块动量检测"""
        # 模拟板块动量数据
        sector_momentum = {
            '半导体': {'momentum_5d': 2.5, 'momentum_10d': 4.0, 'momentum_20d': 8.0},
            '新能源': {'momentum_5d': 3.0, 'momentum_10d': 5.0, 'momentum_20d': 6.0},
            '医药': {'momentum_5d': -0.5, 'momentum_10d': -1.0, 'momentum_20d': 2.0},
        }

        # 计算动量强度（短期权重更高）
        def calculate_momentum_score(momentum_data):
            return (
                momentum_data['momentum_5d'] * 0.5 +
                momentum_data['momentum_10d'] * 0.3 +
                momentum_data['momentum_20d'] * 0.2
            )

        scores = {
            sector: calculate_momentum_score(data)
            for sector, data in sector_momentum.items()
        }

        # 验证结果
        assert scores['新能源'] > scores['医药']


# ==============================================
# 板块相关性分析测试
# ==============================================

class TestSectorCorrelation:
    """板块相关性分析测试"""

    def test_calculate_sector_correlation(self):
        """测试计算板块相关性"""
        # 模拟板块收益率序列
        np.random.seed(42)
        n_days = 100

        sector_a_returns = np.random.normal(0.001, 0.02, n_days)
        sector_b_returns = sector_a_returns * 0.8 + np.random.normal(0, 0.01, n_days)  # 高相关
        sector_c_returns = np.random.normal(0.0005, 0.025, n_days)  # 低相关

        # 计算相关系数
        corr_ab = np.corrcoef(sector_a_returns, sector_b_returns)[0, 1]
        corr_ac = np.corrcoef(sector_a_returns, sector_c_returns)[0, 1]

        # 验证结果
        assert corr_ab > 0.5  # A和B应该高度相关
        assert abs(corr_ac) < corr_ab  # A和C的相关性应该低于A和B

    def test_build_correlation_matrix(self):
        """测试构建相关性矩阵"""
        np.random.seed(42)
        n_days = 50

        # 模拟多个板块的收益率
        sectors = ['半导体', '计算机', '通信', '新能源', '医药']
        returns_data = {
            sector: np.random.normal(0.001, 0.02, n_days)
            for sector in sectors
        }

        # 构建相关性矩阵
        returns_df = pd.DataFrame(returns_data)
        corr_matrix = returns_df.corr()

        # 验证结果
        assert corr_matrix.shape == (5, 5)
        # 对角线应该为1
        for sector in sectors:
            assert abs(corr_matrix.loc[sector, sector] - 1.0) < 0.0001


# ==============================================
# 运行测试
# ==============================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
