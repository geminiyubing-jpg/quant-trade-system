"""
增强的因子分析服务

提供全面的因子分析功能：
- IC 分析（Information Coefficient）
- 分组收益分析
- 多空收益分析
- 单调性检验
- 因子相关性分析
- 因子衰减分析
- 因子正交化
- 换手率分析
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger(__name__)


# ==============================================
# 数据类定义
# ==============================================

@dataclass
class ICAnalysisResult:
    """IC分析结果"""
    ic_mean: float
    ic_std: float
    ic_ir: float  # IC信息比率 = IC均值 / IC标准差
    ic_t_stat: float
    ic_positive_ratio: float  # IC正值占比
    ic_series: List[Dict[str, Any]]
    ic_decay: List[float]  # IC衰减序列


@dataclass
class GroupAnalysisResult:
    """分组分析结果"""
    group_returns: List[Dict[str, Any]]
    long_short_return: float
    monotonicity_score: float  # 单调性得分
    spread: float  # 顶部-底部差值


@dataclass
class FactorDecayResult:
    """因子衰减分析结果"""
    half_life: float  # 半衰期
    decay_series: List[float]  # 衰减序列
    optimal_lag: int  # 最优滞后


@dataclass
class ComprehensiveFactorAnalysis:
    """综合因子分析结果"""
    factor_name: str
    ic_analysis: ICAnalysisResult
    group_analysis: GroupAnalysisResult
    decay_analysis: FactorDecayResult
    turnover_analysis: Dict[str, Any]
    correlation_analysis: Dict[str, Any]
    overall_score: float  # 综合评分
    grade: str  # 等级 (A/B/C/D/F)
    created_at: datetime = field(default_factory=datetime.utcnow)


# ==============================================
# 因子分析服务
# ==============================================

class EnhancedFactorAnalysisService:
    """
    增强的因子分析服务

    提供全面的因子评估功能。
    """

    def __init__(self, n_groups: int = 5):
        """
        初始化

        Args:
            n_groups: 分组数量，默认5组
        """
        self.n_groups = n_groups
        self.logger = logging.getLogger("EnhancedFactorAnalysisService")

    def analyze_factor(
        self,
        factor_name: str,
        signals: List[Dict],
        returns: List[Dict],
        other_factors: Dict[str, List[Dict]] = None
    ) -> ComprehensiveFactorAnalysis:
        """
        执行综合因子分析

        Args:
            factor_name: 因子名称
            signals: 信号数据 [{date, symbol, signal_value}]
            returns: 收益数据 [{date, symbol, return}]
            other_factors: 其他因子数据 {factor_name: signals}

        Returns:
            ComprehensiveFactorAnalysis: 综合分析结果
        """
        self.logger.info(f"开始分析因子: {factor_name}")

        # 1. IC分析
        ic_analysis = self._analyze_ic(signals, returns)

        # 2. 分组分析
        group_analysis = self._analyze_groups(signals, returns)

        # 3. 衰减分析
        decay_analysis = self._analyze_decay(signals, returns)

        # 4. 换手率分析
        turnover_analysis = self._analyze_turnover(signals)

        # 5. 相关性分析
        correlation_analysis = self._analyze_correlation(
            signals, returns, other_factors
        )

        # 6. 计算综合评分
        overall_score, grade = self._calculate_overall_score(
            ic_analysis, group_analysis, decay_analysis, turnover_analysis
        )

        return ComprehensiveFactorAnalysis(
            factor_name=factor_name,
            ic_analysis=ic_analysis,
            group_analysis=group_analysis,
            decay_analysis=decay_analysis,
            turnover_analysis=turnover_analysis,
            correlation_analysis=correlation_analysis,
            overall_score=overall_score,
            grade=grade
        )

    def _analyze_ic(
        self,
        signals: List[Dict],
        returns: List[Dict]
    ) -> ICAnalysisResult:
        """
        IC分析

        IC（Information Coefficient）是因子值与未来收益的相关系数。
        通常使用 Spearman 秩相关系数。
        """
        signal_df = pd.DataFrame(signals)
        return_df = pd.DataFrame(returns)

        if signal_df.empty or return_df.empty:
            return ICAnalysisResult(
                ic_mean=0, ic_std=0, ic_ir=0, ic_t_stat=0,
                ic_positive_ratio=0, ic_series=[], ic_decay=[]
            )

        # 计算每日IC
        ic_series = []
        for current_date in signal_df['date'].unique():
            date_signals = signal_df[signal_df['date'] == current_date]
            date_returns = return_df[return_df['date'] == current_date]

            merged = date_signals.merge(date_returns, on='symbol', how='inner')

            if len(merged) > 5:  # 至少需要5个样本
                # 使用 Spearman 秩相关
                ic, _ = stats.spearmanr(merged['signal_value'], merged['return'])
                if not np.isnan(ic):
                    ic_series.append({
                        'date': current_date,
                        'ic': ic
                    })

        if not ic_series:
            return ICAnalysisResult(
                ic_mean=0, ic_std=0, ic_ir=0, ic_t_stat=0,
                ic_positive_ratio=0, ic_series=[], ic_decay=[]
            )

        ic_values = [ic['ic'] for ic in ic_series]

        # IC统计量
        ic_mean = np.mean(ic_values)
        ic_std = np.std(ic_values)
        ic_ir = ic_mean / ic_std if ic_std != 0 else 0
        n = len(ic_values)
        ic_t_stat = ic_mean / (ic_std / np.sqrt(n)) if ic_std != 0 and n > 0 else 0
        ic_positive_ratio = sum(1 for ic in ic_values if ic > 0) / n

        # IC衰减分析
        ic_decay = self._calculate_ic_decay(signal_df, return_df)

        return ICAnalysisResult(
            ic_mean=float(ic_mean),
            ic_std=float(ic_std),
            ic_ir=float(ic_ir),
            ic_t_stat=float(ic_t_stat),
            ic_positive_ratio=float(ic_positive_ratio),
            ic_series=ic_series,
            ic_decay=ic_decay
        )

    def _calculate_ic_decay(
        self,
        signal_df: pd.DataFrame,
        return_df: pd.DataFrame,
        max_lag: int = 20
    ) -> List[float]:
        """
        计算IC衰减

        分析因子对不同滞后期收益的预测能力。
        """
        decay_series = []
        unique_dates = sorted(signal_df['date'].unique())

        for lag in range(1, min(max_lag + 1, len(unique_dates))):
            lag_ics = []

            for i, current_date in enumerate(unique_dates[:-lag]):
                # 获取当天的信号
                date_signals = signal_df[signal_df['date'] == current_date]

                # 获取滞后期的收益
                lag_date = unique_dates[i + lag]
                lag_returns = return_df[return_df['date'] == lag_date]

                merged = date_signals.merge(lag_returns, on='symbol', how='inner')

                if len(merged) > 5:
                    ic, _ = stats.spearmanr(merged['signal_value'], merged['return'])
                    if not np.isnan(ic):
                        lag_ics.append(ic)

            if lag_ics:
                decay_series.append(float(np.mean(lag_ics)))
            else:
                decay_series.append(0.0)

        return decay_series

    def _analyze_groups(
        self,
        signals: List[Dict],
        returns: List[Dict]
    ) -> GroupAnalysisResult:
        """
        分组收益分析

        将股票按因子值分成N组，分析各组收益。
        """
        signal_df = pd.DataFrame(signals)
        return_df = pd.DataFrame(returns)

        if signal_df.empty or return_df.empty:
            return GroupAnalysisResult(
                group_returns=[], long_short_return=0,
                monotonicity_score=0, spread=0
            )

        # 合并数据
        merged = signal_df.merge(return_df, on=['date', 'symbol'], how='inner')

        if merged.empty:
            return GroupAnalysisResult(
                group_returns=[], long_short_return=0,
                monotonicity_score=0, spread=0
            )

        # 按日期分组，计算每组的平均收益
        group_returns = []

        for current_date in merged['date'].unique():
            date_data = merged[merged['date'] == current_date].copy()

            if len(date_data) < self.n_groups:
                continue

            # 按因子值分组
            try:
                date_data['group'] = pd.qcut(
                    date_data['signal_value'],
                    self.n_groups,
                    labels=False,
                    duplicates='drop'
                )
            except ValueError:
                continue

            # 计算每组收益
            for g in range(self.n_groups):
                group_data = date_data[date_data['group'] == g]
                if not group_data.empty:
                    group_returns.append({
                        'date': current_date,
                        'group': int(g + 1),
                        'return': float(group_data['return'].mean())
                    })

        if not group_returns:
            return GroupAnalysisResult(
                group_returns=[], long_short_return=0,
                monotonicity_score=0, spread=0
            )

        # 计算各组的平均收益
        group_df = pd.DataFrame(group_returns)
        avg_group_returns = []

        for g in range(1, self.n_groups + 1):
            group_data = group_df[group_df['group'] == g]
            if not group_data.empty:
                avg_group_returns.append({
                    'group': g,
                    'return': float(group_data['return'].mean())
                })

        # 计算多空收益
        if len(avg_group_returns) >= 2:
            top_return = avg_group_returns[-1]['return']
            bottom_return = avg_group_returns[0]['return']
            long_short_return = top_return - bottom_return
            spread = long_short_return
        else:
            long_short_return = 0
            spread = 0

        # 计算单调性得分
        monotonicity_score = self._calculate_monotonicity(avg_group_returns)

        return GroupAnalysisResult(
            group_returns=avg_group_returns,
            long_short_return=float(long_short_return),
            monotonicity_score=float(monotonicity_score),
            spread=float(spread)
        )

    def _calculate_monotonicity(self, group_returns: List[Dict]) -> float:
        """
        计算单调性得分

        评估分组收益是否随因子值单调变化。
        得分范围：-1 到 1，绝对值越大单调性越好。
        """
        if len(group_returns) < 2:
            return 0

        returns = [g['return'] for g in group_returns]

        # 计算相邻组收益差异
        differences = []
        for i in range(1, len(returns)):
            differences.append(returns[i] - returns[i - 1])

        if not differences:
            return 0

        # 计算正差异比例
        positive_ratio = sum(1 for d in differences if d > 0) / len(differences)

        # 单调性得分
        if positive_ratio >= 0.5:
            return 2 * positive_ratio - 1  # 正单调
        else:
            return 1 - 2 * positive_ratio  # 负单调（取绝对值）

    def _analyze_decay(
        self,
        signals: List[Dict],
        returns: List[Dict]
    ) -> FactorDecayResult:
        """
        因子衰减分析

        分析因子信号的持久性和半衰期。
        """
        signal_df = pd.DataFrame(signals)

        if signal_df.empty:
            return FactorDecayResult(
                half_life=0, decay_series=[], optimal_lag=1
            )

        # 计算因子自相关衰减
        unique_dates = sorted(signal_df['date'].unique())

        if len(unique_dates) < 2:
            return FactorDecayResult(
                half_life=0, decay_series=[], optimal_lag=1
            )

        decay_series = []

        for lag in range(1, min(21, len(unique_dates))):
            correlations = []

            for i in range(len(unique_dates) - lag):
                current_date = unique_dates[i]
                lag_date = unique_dates[i + lag]

                current_signals = signal_df[signal_df['date'] == current_date]
                lag_signals = signal_df[signal_df['date'] == lag_date]

                merged = current_signals.merge(lag_signals, on='symbol', how='inner')

                if len(merged) > 5:
                    corr = merged['signal_value_x'].corr(merged['signal_value_y'])
                    if not np.isnan(corr):
                        correlations.append(corr)

            if correlations:
                decay_series.append(float(np.mean(correlations)))
            else:
                decay_series.append(0.0)

        # 计算半衰期
        half_life = self._calculate_half_life(decay_series)

        # 找到最优滞后（IC最大）
        return_df = pd.DataFrame(returns)
        ic_decay = self._calculate_ic_decay(signal_df, return_df)
        optimal_lag = np.argmax(np.abs(ic_decay)) + 1 if ic_decay else 1

        return FactorDecayResult(
            half_life=float(half_life),
            decay_series=decay_series,
            optimal_lag=int(optimal_lag)
        )

    def _calculate_half_life(self, decay_series: List[float]) -> float:
        """计算半衰期"""
        if not decay_series or decay_series[0] == 0:
            return 0

        initial = abs(decay_series[0])
        half_value = initial / 2

        for i, value in enumerate(decay_series):
            if abs(value) <= half_value:
                return float(i + 1)

        # 如果没有衰减到一半，返回最大滞后期
        return float(len(decay_series))

    def _analyze_turnover(self, signals: List[Dict]) -> Dict[str, Any]:
        """
        换手率分析

        分析因子信号的稳定性。
        """
        signal_df = pd.DataFrame(signals)

        if signal_df.empty:
            return {
                'avg_turnover': 0,
                'turnover_series': [],
                'stability_score': 0
            }

        unique_dates = sorted(signal_df['date'].unique())

        if len(unique_dates) < 2:
            return {
                'avg_turnover': 0,
                'turnover_series': [],
                'stability_score': 100
            }

        turnover_series = []

        for i in range(1, len(unique_dates)):
            prev_date = unique_dates[i - 1]
            curr_date = unique_dates[i]

            prev_signals = signal_df[signal_df['date'] == prev_date]
            curr_signals = signal_df[signal_df['date'] == curr_date]

            # 找到共同股票
            common_symbols = set(prev_signals['symbol']) & set(curr_signals['symbol'])

            if len(common_symbols) > 0:
                # 计算排名变化
                prev_ranks = prev_signals[prev_signals['symbol'].isin(common_symbols)].copy()
                curr_ranks = curr_signals[curr_signals['symbol'].isin(common_symbols)].copy()

                prev_ranks['rank'] = prev_ranks['signal_value'].rank()
                curr_ranks['rank'] = curr_ranks['signal_value'].rank()

                merged = prev_ranks[['symbol', 'rank']].merge(
                    curr_ranks[['symbol', 'rank']],
                    on='symbol',
                    suffixes=('_prev', '_curr')
                )

                # 换手率 = 排名变化的平均比例
                rank_change = np.abs(merged['rank_curr'] - merged['rank_prev'])
                max_change = len(common_symbols)
                turnover = rank_change.mean() / max_change if max_change > 0 else 0

                turnover_series.append(float(turnover))

        avg_turnover = float(np.mean(turnover_series)) if turnover_series else 0

        # 稳定性得分：换手率越低，稳定性越高
        stability_score = max(0, 100 * (1 - avg_turnover * 2))

        return {
            'avg_turnover': avg_turnover,
            'turnover_series': turnover_series,
            'stability_score': float(stability_score)
        }

    def _analyze_correlation(
        self,
        signals: List[Dict],
        returns: List[Dict],
        other_factors: Dict[str, List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        因子相关性分析

        分析当前因子与其他因子的相关性。
        """
        signal_df = pd.DataFrame(signals)

        if signal_df.empty:
            return {
                'correlations': {},
                'max_correlation': 0,
                'is_redundant': False
            }

        correlations = {}

        if other_factors:
            for other_name, other_signals in other_factors.items():
                other_df = pd.DataFrame(other_signals)

                if other_df.empty:
                    continue

                # 计算因子值相关性
                merged = signal_df.merge(other_df, on=['date', 'symbol'], how='inner')

                if len(merged) > 10:
                    corr = merged['signal_value_x'].corr(merged['signal_value_y'])
                    if not np.isnan(corr):
                        correlations[other_name] = float(corr)

        max_corr = max(abs(c) for c in correlations.values()) if correlations else 0

        # 判断是否冗余（相关性过高）
        is_redundant = max_corr > 0.7

        return {
            'correlations': correlations,
            'max_correlation': float(max_corr),
            'is_redundant': is_redundant
        }

    def _calculate_overall_score(
        self,
        ic_analysis: ICAnalysisResult,
        group_analysis: GroupAnalysisResult,
        decay_analysis: FactorDecayResult,
        turnover_analysis: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        计算因子综合评分

        评分维度：
        - IC质量（40%）
        - 分组单调性（25%）
        - 因子稳定性（20%）
        - 衰减特性（15%）
        """
        # IC质量得分
        ic_score = 0
        if abs(ic_analysis.ic_mean) >= 0.03:
            ic_score = 100
        elif abs(ic_analysis.ic_mean) >= 0.02:
            ic_score = 80
        elif abs(ic_analysis.ic_mean) >= 0.01:
            ic_score = 60
        elif abs(ic_analysis.ic_mean) >= 0.005:
            ic_score = 40
        else:
            ic_score = 20

        # IR 加分
        if abs(ic_analysis.ic_ir) >= 2:
            ic_score = min(100, ic_score + 20)
        elif abs(ic_analysis.ic_ir) >= 1:
            ic_score = min(100, ic_score + 10)

        # 分组单调性得分
        mono_score = abs(group_analysis.monotonicity_score) * 100

        # 多空收益得分
        ls_score = 0
        if abs(group_analysis.long_short_return) >= 0.02:
            ls_score = 100
        elif abs(group_analysis.long_short_return) >= 0.01:
            ls_score = 70
        elif abs(group_analysis.long_short_return) >= 0.005:
            ls_score = 50
        else:
            ls_score = 30

        group_score = mono_score * 0.6 + ls_score * 0.4

        # 稳定性得分
        stability_score = turnover_analysis.get('stability_score', 50)

        # 衰减得分
        decay_score = 0
        if decay_analysis.half_life > 0:
            if decay_analysis.half_life >= 10:
                decay_score = 100
            elif decay_analysis.half_life >= 5:
                decay_score = 80
            elif decay_analysis.half_life >= 3:
                decay_score = 60
            else:
                decay_score = 40

        # 综合评分
        overall = ic_score * 0.4 + group_score * 0.25 + stability_score * 0.2 + decay_score * 0.15

        # 确定等级
        if overall >= 85:
            grade = 'A'
        elif overall >= 70:
            grade = 'B'
        elif overall >= 55:
            grade = 'C'
        elif overall >= 40:
            grade = 'D'
        else:
            grade = 'F'

        return float(overall), grade

    def orthogonalize_factors(
        self,
        target_signals: List[Dict],
        reference_signals: List[Dict]
    ) -> List[Dict]:
        """
        因子正交化

        使用施密特正交化方法，从目标因子中去除参考因子的影响。

        Args:
            target_signals: 目标因子信号
            reference_signals: 参考因子信号

        Returns:
            正交化后的信号
        """
        target_df = pd.DataFrame(target_signals)
        ref_df = pd.DataFrame(reference_signals)

        if target_df.empty or ref_df.empty:
            return target_signals

        # 合并数据
        merged = target_df.merge(
            ref_df,
            on=['date', 'symbol'],
            suffixes=('_target', '_ref')
        )

        # 按日期分组正交化
        result = []

        for current_date in merged['date'].unique():
            date_data = merged[merged['date'] == current_date].copy()

            if len(date_data) > 2:
                # 线性回归残差作为正交化结果
                X = date_data['signal_value_ref'].values.reshape(-1, 1)
                y = date_data['signal_value_target'].values

                # 简单线性回归
                slope = np.cov(X.flatten(), y)[0, 1] / np.var(X.flatten())
                intercept = np.mean(y) - slope * np.mean(X.flatten())
                residual = y - (slope * X.flatten() + intercept)

                # 标准化
                residual = (residual - np.mean(residual)) / (np.std(residual) + 1e-8)

                for i, row in date_data.iterrows():
                    result.append({
                        'date': current_date,
                        'symbol': row['symbol'],
                        'signal_value': float(residual[list(date_data.index).index(i)])
                    })

        return result
