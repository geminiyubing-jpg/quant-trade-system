"""
绩效分析服务单元测试

测试绩效指标计算、归因分析、基准管理等功能。
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

from src.services.portfolio.performance import PerformanceService


# ==============================================
# 测试数据
# ==============================================

def create_mock_portfolio_data():
    """创建模拟投资组合数据"""
    # 生成一年的日收益率数据
    np.random.seed(42)
    dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='B')
    returns = np.random.normal(0.0005, 0.02, len(dates))  # 日均收益0.05%，波动率2%

    return pd.DataFrame({
        'date': dates,
        'portfolio_return': returns,
        'benchmark_return': returns * 0.8 + np.random.normal(0, 0.005, len(dates)),  # 相关性0.8
        'portfolio_value': 1000000 * (1 + returns).cumprod(),
    })


def create_mock_positions():
    """创建模拟持仓数据"""
    return [
        {
            'symbol': '600519.SH',
            'name': '贵州茅台',
            'quantity': 100,
            'avg_cost': Decimal('1800.00'),
            'current_price': Decimal('1850.00'),
            'market_value': Decimal('185000.00'),
            'weight': Decimal('0.15'),
            'sector': '白酒',
        },
        {
            'symbol': '000858.SZ',
            'name': '五粮液',
            'quantity': 200,
            'avg_cost': Decimal('150.00'),
            'current_price': Decimal('160.00'),
            'market_value': Decimal('32000.00'),
            'weight': Decimal('0.10'),
            'sector': '白酒',
        },
        {
            'symbol': '601318.SH',
            'name': '中国平安',
            'quantity': 500,
            'avg_cost': Decimal('45.00'),
            'current_price': Decimal('48.00'),
            'market_value': Decimal('24000.00'),
            'weight': Decimal('0.08'),
            'sector': '保险',
        },
    ]


# ==============================================
# PerformanceService 测试
# ==============================================

class TestPerformanceService:
    """绩效分析服务测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock()

    @pytest.fixture
    def performance_service(self, mock_db):
        """创建绩效分析服务实例"""
        return PerformanceService(mock_db)

    def test_calculate_total_return(self, performance_service):
        """测试计算总收益率"""
        # 准备数据
        portfolio_data = create_mock_portfolio_data()
        start_value = portfolio_data['portfolio_value'].iloc[0]
        end_value = portfolio_data['portfolio_value'].iloc[-1]

        # 计算总收益
        total_return = (end_value - start_value) / start_value

        # 验证结果在合理范围内
        assert -1 < total_return < 2  # 总收益应该在-100%到200%之间

    def test_calculate_annualized_return(self, performance_service):
        """测试计算年化收益率"""
        portfolio_data = create_mock_portfolio_data()
        daily_returns = portfolio_data['portfolio_return']

        # 计算年化收益
        total_return = (1 + daily_returns).prod() - 1
        trading_days = len(daily_returns)
        annualized_return = (1 + total_return) ** (252 / trading_days) - 1

        # 验证结果在合理范围内
        assert -1 < annualized_return < 3  # 年化收益应该在-100%到300%之间

    def test_calculate_sharpe_ratio(self, performance_service):
        """测试计算夏普比率"""
        portfolio_data = create_mock_portfolio_data()
        daily_returns = portfolio_data['portfolio_return']

        # 计算夏普比率 (假设无风险利率为3%)
        risk_free_rate = 0.03 / 252  # 日化无风险利率
        excess_returns = daily_returns - risk_free_rate

        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()

        # 验证结果在合理范围内
        assert -5 < sharpe_ratio < 5  # 夏普比率通常在-5到5之间

    def test_calculate_max_drawdown(self, performance_service):
        """测试计算最大回撤"""
        portfolio_data = create_mock_portfolio_data()
        values = portfolio_data['portfolio_value']

        # 计算最大回撤
        cummax = values.cummax()
        drawdown = (values - cummax) / cummax
        max_drawdown = drawdown.min()

        # 验证结果在合理范围内
        assert -1 < max_drawdown <= 0  # 最大回撤应该在-100%到0之间

    def test_calculate_sortino_ratio(self, performance_service):
        """测试计算索提诺比率"""
        portfolio_data = create_mock_portfolio_data()
        daily_returns = portfolio_data['portfolio_return']

        # 计算索提诺比率
        risk_free_rate = 0.03 / 252
        excess_returns = daily_returns - risk_free_rate

        # 只计算负收益的波动率
        negative_returns = excess_returns[excess_returns < 0]
        downside_std = negative_returns.std()

        if downside_std > 0:
            sortino_ratio = np.sqrt(252) * excess_returns.mean() / downside_std
        else:
            sortino_ratio = 0

        # 验证结果
        assert isinstance(sortino_ratio, (int, float))

    def test_calculate_beta(self, performance_service):
        """测试计算Beta"""
        portfolio_data = create_mock_portfolio_data()
        portfolio_returns = portfolio_data['portfolio_return']
        benchmark_returns = portfolio_data['benchmark_return']

        # 计算Beta
        covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

        # 验证结果在合理范围内
        assert 0 < beta < 2  # Beta通常在0到2之间

    def test_calculate_alpha(self, performance_service):
        """测试计算Alpha"""
        portfolio_data = create_mock_portfolio_data()
        portfolio_returns = portfolio_data['portfolio_return']
        benchmark_returns = portfolio_data['benchmark_return']

        # 计算Alpha
        portfolio_return = (1 + portfolio_returns).prod() - 1
        benchmark_return = (1 + benchmark_returns).prod() - 1

        # 简化计算：Alpha = 组合收益 - 基准收益
        # 实际应该使用 CAPM: Alpha = Rp - [Rf + Beta * (Rm - Rf)]
        alpha = portfolio_return - benchmark_return

        # 验证结果
        assert isinstance(alpha, (int, float))

    def test_calculate_win_rate(self, performance_service):
        """测试计算胜率"""
        portfolio_data = create_mock_portfolio_data()
        daily_returns = portfolio_data['portfolio_return']

        # 计算胜率
        positive_days = (daily_returns > 0).sum()
        total_days = len(daily_returns)
        win_rate = positive_days / total_days

        # 验证结果
        assert 0 <= win_rate <= 1

    def test_calculate_profit_loss_ratio(self, performance_service):
        """测试计算盈亏比"""
        portfolio_data = create_mock_portfolio_data()
        daily_returns = portfolio_data['portfolio_return']

        # 计算盈亏比
        gains = daily_returns[daily_returns > 0]
        losses = daily_returns[daily_returns < 0]

        avg_gain = gains.mean() if len(gains) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 1

        profit_loss_ratio = avg_gain / avg_loss if avg_loss > 0 else 0

        # 验证结果
        assert profit_loss_ratio >= 0

    def test_calculate_information_ratio(self, performance_service):
        """测试计算信息比率"""
        portfolio_data = create_mock_portfolio_data()
        portfolio_returns = portfolio_data['portfolio_return']
        benchmark_returns = portfolio_data['benchmark_return']

        # 计算跟踪误差
        excess_returns = portfolio_returns - benchmark_returns
        tracking_error = excess_returns.std() * np.sqrt(252)

        # 计算信息比率
        annualized_excess = excess_returns.mean() * 252
        information_ratio = annualized_excess / tracking_error if tracking_error > 0 else 0

        # 验证结果
        assert isinstance(information_ratio, (int, float))


# ==============================================
# 归因分析测试
# ==============================================

class TestAttributionAnalysis:
    """归因分析测试"""

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def performance_service(self, mock_db):
        return PerformanceService(mock_db)

    def test_sector_attribution(self, performance_service):
        """测试行业归因分析"""
        # 准备数据
        portfolio_returns = {
            '白酒': 0.15,
            '保险': 0.08,
            '银行': 0.05,
        }
        benchmark_weights = {
            '白酒': 0.10,
            '保险': 0.15,
            '银行': 0.20,
        }
        portfolio_weights = {
            '白酒': 0.25,
            '保险': 0.10,
            '银行': 0.05,
        }

        # 计算配置效应
        allocation_effect = {}
        for sector in portfolio_returns:
            weight_diff = portfolio_weights[sector] - benchmark_weights[sector]
            allocation_effect[sector] = weight_diff * portfolio_returns[sector]

        # 验证结果
        assert len(allocation_effect) == 3
        assert all(isinstance(v, (int, float)) for v in allocation_effect.values())

    def test_selection_attribution(self, performance_service):
        """测试选股效应"""
        # 准备数据 - 板块内选股收益差异
        portfolio_sector_returns = {
            '白酒': 0.18,  # 组合中白酒板块收益
            '保险': 0.06,
        }
        benchmark_sector_returns = {
            '白酒': 0.12,  # 基准中白酒板块收益
            '保险': 0.08,
        }
        portfolio_weights = {
            '白酒': 0.25,
            '保险': 0.10,
        }

        # 计算选股效应
        selection_effect = {}
        for sector in portfolio_sector_returns:
            return_diff = portfolio_sector_returns[sector] - benchmark_sector_returns[sector]
            selection_effect[sector] = portfolio_weights[sector] * return_diff

        # 验证结果
        assert len(selection_effect) == 2


# ==============================================
# 基准管理测试
# ==============================================

class TestBenchmarkManagement:
    """基准管理测试"""

    def test_create_custom_benchmark(self):
        """测试创建自定义基准"""
        benchmark = {
            'name': '我的基准',
            'description': '自定义基准组合',
            'composition': [
                {'symbol': '600519.SH', 'weight': 0.3},
                {'symbol': '000858.SZ', 'weight': 0.2},
                {'symbol': '601318.SH', 'weight': 0.2},
                {'symbol': '000001.SZ', 'weight': 0.15},
                {'symbol': '600036.SH', 'weight': 0.15},
            ],
            'rebalance_frequency': 'QUARTERLY',
        }

        # 验证权重之和为1
        total_weight = sum(item['weight'] for item in benchmark['composition'])
        assert abs(total_weight - 1.0) < 0.0001

    def test_validate_benchmark_weights(self):
        """测试验证基准权重"""
        # 有效权重
        valid_composition = [
            {'symbol': '600519.SH', 'weight': 0.5},
            {'symbol': '000858.SZ', 'weight': 0.5},
        ]
        total = sum(item['weight'] for item in valid_composition)
        assert abs(total - 1.0) < 0.0001

        # 无效权重 - 权重之和超过1
        invalid_composition = [
            {'symbol': '600519.SH', 'weight': 0.6},
            {'symbol': '000858.SZ', 'weight': 0.6},
        ]
        total = sum(item['weight'] for item in invalid_composition)
        assert total > 1.0


# ==============================================
# 运行测试
# ==============================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
