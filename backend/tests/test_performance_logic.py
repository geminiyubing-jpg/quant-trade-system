"""
绩效分析逻辑测试（简化版）

不依赖外部服务，"""

import pytest
from decimal import Decimal
import math


# ==============================================
# 绩效计算函数
# ==============================================

def calculate_total_return(start_value: float, end_value: float) -> float:
    """计算总收益率"""
    if start_value == 0:
        return 0
    return ((end_value - start_value) / start_value) * 100


def calculate_annualized_return(total_return: float, days: int) -> float:
    """计算年化收益率"""
    if days <= 0:
        return 0
    return ((1 + total_return / 100) ** (365 / days) - 1) * 100


def calculate_sharpe_ratio(returns: list, risk_free_rate: float = 0.03) -> float:
    """计算夏普比率"""
    if not returns:
        return 0

    daily_rf = risk_free_rate / 252
    excess_returns = [r - daily_rf for r in returns]

    mean_excess = sum(excess_returns) / len(excess_returns)
    std_excess = math.sqrt(sum((r - mean_excess) ** 2 for r in excess_returns) / len(excess_returns))

    if std_excess == 0:
        return 0

    return math.sqrt(252) * mean_excess / std_excess


def calculate_max_drawdown(values: list) -> float:
    """计算最大回撤"""
    if not values:
        return 0

    peak = values[0]
    max_dd = 0

    for value in values:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
                max_dd = dd

    return max_dd


def calculate_win_rate(trades: list) -> float:
    """计算胜率"""
    if not trades:
        return 0

    wins = sum(1 for t in trades if t > 0)
    return wins / len(trades)


# ==============================================
# 测试用例
# ==============================================

class TestPerformanceCalculations:
    """绩效计算测试"""

    def test_calculate_total_return_positive(self):
        """测试正收益计算"""
        result = calculate_total_return(100000, 120000)
        assert abs(result - 20.0) < 0.01

    def test_calculate_total_return_negative(self):
        """测试负收益计算"""
        result = calculate_total_return(100000, 80000)
        assert abs(result - (-20.0)) < 0.01

    def test_calculate_total_return_zero_start(self):
        """测试初始值为零的情况"""
        result = calculate_total_return(0, 100000)
        assert result == 0

    def test_calculate_annualized_return(self):
        """测试年化收益计算"""
        # 假设半年总收益10%
        result = calculate_annualized_return(10, 182)
        # 年化收益应该略大于10%
        assert result > 10
        assert result < 25

    def test_calculate_sharpe_ratio_positive(self):
        """测试正夏普比率"""
        # 模拟每日超额收益
        returns = [0.001, 0.002, -0.001, 0.003, 0.001, -0.002, 0.002, 0.001]
        result = calculate_sharpe_ratio(returns, 0.03)
        assert result > 0  # 应该是正的

    def test_calculate_sharpe_ratio_empty(self):
        """测试空收益率列表"""
        result = calculate_sharpe_ratio([], 0.03)
        assert result == 0

    def test_calculate_max_drawdown(self):
        """测试最大回撤计算"""
        values = [100, 105, 110, 108, 100, 95, 98, 102]
        result = calculate_max_drawdown(values)
        # 从110跌到95，回撤约13.6%
        assert result > 10
        assert result < 15

    def test_calculate_max_drawdown_monotonic_increase(self):
        """测试单调递增的情况"""
        values = [100, 105, 110, 115, 120]
        result = calculate_max_drawdown(values)
        assert result == 0

    def test_calculate_win_rate(self):
        """测试胜率计算"""
        trades = [100, -50, 200, -30, 150, -80, 300]
        result = calculate_win_rate(trades)
        assert abs(result - (4/7)) < 0.01  # 4胜3负

    def test_calculate_win_rate_empty(self):
        """测试空交易列表"""
        result = calculate_win_rate([])
        assert result == 0


class TestSectorCalculations:
    """板块计算测试"""

    def test_sector_ranking(self):
        """测试板块排名"""
        sectors = [
            {'name': '半导体', 'change_pct': 2.5},
            {'name': '计算机', 'change_pct': 1.8},
            {'name': '通信', 'change_pct': -0.5},
            {'name': '新能源', 'change_pct': 3.2},
        ]

        sorted_sectors = sorted(sectors, key=lambda x: x['change_pct'], reverse=True)

        assert sorted_sectors[0]['name'] == '新能源'
        assert sorted_sectors[-1]['name'] == '通信'

    def test_market_sentiment(self):
        """测试市场情绪"""
        sectors = [
            {'change_pct': 2.5},
            {'change_pct': 1.8},
            {'change_pct': -0.5},
            {'change_pct': 3.2},
            {'change_pct': -1.2},
        ]

        up_count = sum(1 for s in sectors if s['change_pct'] > 0)
        down_count = sum(1 for s in sectors if s['change_pct'] < 0)

        assert up_count == 3
        assert down_count == 2

    def test_sector_concentration(self):
        """测试板块集中度"""
        sectors = [
            {'amount': 15000000000},
            {'amount': 12000000000},
            {'amount': 8000000000},
        ]

        total = sum(s['amount'] for s in sectors)

        ratios = [s['amount'] / total for s in sectors]

        assert abs(sum(ratios) - 1.0) < 0.0001


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
