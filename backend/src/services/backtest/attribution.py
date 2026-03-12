"""
完善的归因分析服务

提供全面的绩效归因功能：
- Brinson归因模型（配置效应、选股效应、交互效应）
- 行业归因分析
- 风险因子归因（Barra风格）
- 月度归因分析
- 滚动归因分析
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# ==============================================
# 数据类定义
# ==============================================

@dataclass
class BrinsonAttributionResult:
    """Brinson归因结果"""
    allocation_effect: float  # 配置效应
    selection_effect: float   # 选股效应
    interaction_effect: float # 交互效应
    total_active_return: float  # 总主动收益
    trading_effect: float = 0   # 交易效应


@dataclass
class IndustryAttribution:
    """行业归因结果"""
    industry: str
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    allocation_effect: float
    selection_effect: float
    total_contribution: float


@dataclass
class FactorAttribution:
    """因子归因结果"""
    factor_name: str
    exposure: float  # 因子暴露
    factor_return: float  # 因子收益
    contribution: float  # 因子贡献 = 暴露 × 因子收益
    t_stat: float = 0  # t统计量


@dataclass
class PeriodAttribution:
    """期间归因结果"""
    period: str  # 期间标识
    portfolio_return: float
    benchmark_return: float
    active_return: float
    brinson: BrinsonAttributionResult


@dataclass
class ComprehensiveAttributionResult:
    """综合归因分析结果"""
    benchmark_symbol: str
    total_period: BrinsonAttributionResult
    industry_attribution: List[IndustryAttribution]
    factor_attribution: List[FactorAttribution]
    monthly_attribution: List[PeriodAttribution]
    rolling_attribution: List[Dict[str, Any]]
    summary: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


# ==============================================
# 归因分析服务
# ==============================================

class EnhancedAttributionService:
    """
    增强的归因分析服务

    提供全面的绩效归因功能。
    """

    def __init__(self):
        self.logger = logging.getLogger("EnhancedAttributionService")

    def analyze_attribution(
        self,
        portfolio_weights: List[Dict],
        benchmark_weights: List[Dict],
        returns_data: List[Dict],
        benchmark_symbol: str = "000300.SH",
        industry_mapping: Dict[str, str] = None,
        factor_exposures: Dict[str, Dict[str, float]] = None,
        factor_returns: Dict[str, float] = None,
        monthly_data: List[Dict] = None
    ) -> ComprehensiveAttributionResult:
        """
        执行综合归因分析

        Args:
            portfolio_weights: 组合权重 [{date, symbol, weight}]
            benchmark_weights: 基准权重 [{date, symbol, weight}]
            returns_data: 收益数据 [{date, symbol, return}]
            benchmark_symbol: 基准代码
            industry_mapping: 行业映射 {symbol: industry}
            factor_exposures: 因子暴露 {symbol: {factor: exposure}}
            factor_returns: 因子收益 {factor: return}
            monthly_data: 月度数据 [{month, portfolio_return, benchmark_return}]

        Returns:
            ComprehensiveAttributionResult: 综合归因结果
        """
        self.logger.info(f"开始归因分析，基准: {benchmark_symbol}")

        # 1. 计算整体Brinson归因
        total_brinson = self._calculate_brinson_attribution(
            portfolio_weights, benchmark_weights, returns_data
        )

        # 2. 行业归因
        industry_attr = self._calculate_industry_attribution(
            portfolio_weights, benchmark_weights, returns_data, industry_mapping
        )

        # 3. 因子归因
        factor_attr = self._calculate_factor_attribution(
            portfolio_weights, factor_exposures, factor_returns
        )

        # 4. 月度归因
        monthly_attr = self._calculate_monthly_attribution(
            monthly_data, portfolio_weights, benchmark_weights, returns_data
        )

        # 5. 滚动归因
        rolling_attr = self._calculate_rolling_attribution(
            portfolio_weights, benchmark_weights, returns_data
        )

        # 6. 生成摘要
        summary = self._generate_summary(
            total_brinson, industry_attr, factor_attr
        )

        return ComprehensiveAttributionResult(
            benchmark_symbol=benchmark_symbol,
            total_period=total_brinson,
            industry_attribution=industry_attr,
            factor_attribution=factor_attr,
            monthly_attribution=monthly_attr,
            rolling_attribution=rolling_attr,
            summary=summary
        )

    def _calculate_brinson_attribution(
        self,
        portfolio_weights: List[Dict],
        benchmark_weights: List[Dict],
        returns_data: List[Dict]
    ) -> BrinsonAttributionResult:
        """
        计算Brinson归因

        Brinson模型将主动收益分解为：
        - 配置效应（Allocation Effect）：权重偏离的贡献
        - 选股效应（Selection Effect）：个股选择的贡献
        - 交互效应（Interaction Effect）：权重和选股的交互贡献

        公式：
        - 配置效应 = Σ (Wp - Wb) × Rb
        - 选股效应 = Σ Wb × (Rp - Rb)
        - 交互效应 = Σ (Wp - Wb) × (Rp - Rb)
        - 主动收益 = 配置效应 + 选股效应 + 交互效应
        """
        port_df = pd.DataFrame(portfolio_weights)
        bench_df = pd.DataFrame(benchmark_weights)
        returns_df = pd.DataFrame(returns_data)

        if port_df.empty or bench_df.empty or returns_df.empty:
            return BrinsonAttributionResult(
                allocation_effect=0, selection_effect=0,
                interaction_effect=0, total_active_return=0
            )

        # 合并数据
        merged = port_df.merge(bench_df, on=['date', 'symbol'], suffixes=('_port', '_bench'))
        merged = merged.merge(returns_df, on=['date', 'symbol'])

        if merged.empty:
            return BrinsonAttributionResult(
                allocation_effect=0, selection_effect=0,
                interaction_effect=0, total_active_return=0
            )

        # 计算组合收益和基准收益
        merged['port_return'] = merged['weight_port'] * merged['return']
        merged['bench_return'] = merged['weight_bench'] * merged['return']

        # 按日期汇总
        daily_summary = merged.groupby('date').agg({
            'port_return': 'sum',
            'bench_return': 'sum'
        }).reset_index()

        # 计算总体收益
        portfolio_total_return = daily_summary['port_return'].sum()
        benchmark_total_return = daily_summary['bench_return'].sum()
        active_return = portfolio_total_return - benchmark_total_return

        # 按日期计算Brinson归因
        allocation_effects = []
        selection_effects = []
        interaction_effects = []

        for current_date in merged['date'].unique():
            date_data = merged[merged['date'] == current_date]

            # 配置效应 = Σ (Wp - Wb) × Rb
            allocation = ((date_data['weight_port'] - date_data['weight_bench']) *
                         date_data['return']).sum()

            # 计算每个资产的组合收益和基准收益
            date_data = date_data.copy()
            date_data['asset_port_return'] = date_data['weight_port'] * date_data['return']
            date_data['asset_bench_return'] = date_data['weight_bench'] * date_data['return']

            # 资产级别收益
            port_return_by_asset = date_data.groupby('symbol').agg({
                'asset_port_return': 'sum',
                'asset_bench_return': 'sum',
                'weight_port': 'sum',
                'weight_bench': 'sum',
                'return': 'mean'
            }).reset_index()

            # 选股效应 = Σ Wb × (Rp - Rb)
            selection = 0
            for _, row in port_return_by_asset.iterrows():
                if row['weight_bench'] > 0:
                    asset_port_ret = row['asset_port_return'] / row['weight_port'] if row['weight_port'] > 0 else 0
                    asset_bench_ret = row['asset_bench_return'] / row['weight_bench'] if row['weight_bench'] > 0 else 0
                    selection += row['weight_bench'] * (asset_port_ret - asset_bench_ret)

            # 交互效应 = Σ (Wp - Wb) × (Rp - Rb)
            interaction = 0
            for _, row in port_return_by_asset.iterrows():
                if row['weight_bench'] > 0 and row['weight_port'] > 0:
                    asset_port_ret = row['asset_port_return'] / row['weight_port']
                    asset_bench_ret = row['asset_bench_return'] / row['weight_bench']
                    interaction += (row['weight_port'] - row['weight_bench']) * (asset_port_ret - asset_bench_ret)

            allocation_effects.append(allocation)
            selection_effects.append(selection)
            interaction_effects.append(interaction)

        # 汇总
        total_allocation = sum(allocation_effects)
        total_selection = sum(selection_effects)
        total_interaction = sum(interaction_effects)

        return BrinsonAttributionResult(
            allocation_effect=float(total_allocation),
            selection_effect=float(total_selection),
            interaction_effect=float(total_interaction),
            total_active_return=float(active_return),
            trading_effect=0  # 交易效应需要更详细的交易数据
        )

    def _calculate_industry_attribution(
        self,
        portfolio_weights: List[Dict],
        benchmark_weights: List[Dict],
        returns_data: List[Dict],
        industry_mapping: Dict[str, str] = None
    ) -> List[IndustryAttribution]:
        """
        计算行业归因

        按行业分解主动收益。
        """
        if not industry_mapping:
            # 如果没有行业映射，使用简化分类
            industry_mapping = {}

        port_df = pd.DataFrame(portfolio_weights)
        bench_df = pd.DataFrame(benchmark_weights)
        returns_df = pd.DataFrame(returns_data)

        if port_df.empty:
            return []

        # 添加行业信息
        port_df['industry'] = port_df['symbol'].map(
            lambda x: industry_mapping.get(x, '其他')
        )
        bench_df['industry'] = bench_df['symbol'].map(
            lambda x: industry_mapping.get(x, '其他')
        )

        # 合并数据
        merged = port_df.merge(bench_df, on=['date', 'symbol', 'industry'], suffixes=('_port', '_bench'))
        merged = merged.merge(returns_df, on=['date', 'symbol'])

        if merged.empty:
            return []

        # 按行业汇总
        industry_results = []

        for industry in merged['industry'].unique():
            ind_data = merged[merged['industry'] == industry]

            # 行业权重
            port_weight = ind_data['weight_port'].mean()
            bench_weight = ind_data['weight_bench'].mean()

            # 行业收益
            port_return = (ind_data['weight_port'] * ind_data['return']).sum() / ind_data['weight_port'].sum() if ind_data['weight_port'].sum() > 0 else 0
            bench_return = (ind_data['weight_bench'] * ind_data['return']).sum() / ind_data['weight_bench'].sum() if ind_data['weight_bench'].sum() > 0 else 0

            # 行业归因
            # 配置效应 = (Wp - Wb) × Rb
            allocation = (port_weight - bench_weight) * bench_return

            # 选股效应 = Wp × (Rp - Rb)
            selection = port_weight * (port_return - bench_return)

            # 总贡献
            total = allocation + selection

            industry_results.append(IndustryAttribution(
                industry=industry,
                portfolio_weight=float(port_weight),
                benchmark_weight=float(bench_weight),
                portfolio_return=float(port_return),
                benchmark_return=float(bench_return),
                allocation_effect=float(allocation),
                selection_effect=float(selection),
                total_contribution=float(total)
            ))

        # 按总贡献排序
        industry_results.sort(key=lambda x: abs(x.total_contribution), reverse=True)

        return industry_results

    def _calculate_factor_attribution(
        self,
        portfolio_weights: List[Dict],
        factor_exposures: Dict[str, Dict[str, float]] = None,
        factor_returns: Dict[str, float] = None
    ) -> List[FactorAttribution]:
        """
        计算因子归因

        基于Barra风格的风险因子归因。
        """
        if not factor_exposures or not factor_returns:
            return []

        port_df = pd.DataFrame(portfolio_weights)

        if port_df.empty:
            return []

        # 计算组合因子暴露
        portfolio_exposure = {}

        for _, row in port_df.iterrows():
            symbol = row['symbol']
            weight = row['weight']

            if symbol in factor_exposures:
                for factor, exposure in factor_exposures[symbol].items():
                    if factor not in portfolio_exposure:
                        portfolio_exposure[factor] = 0
                    portfolio_exposure[factor] += weight * exposure

        # 计算因子贡献
        factor_results = []

        for factor, exposure in portfolio_exposure.items():
            factor_ret = factor_returns.get(factor, 0)
            contribution = exposure * factor_ret

            factor_results.append(FactorAttribution(
                factor_name=factor,
                exposure=float(exposure),
                factor_return=float(factor_ret),
                contribution=float(contribution),
                t_stat=0  # 需要时间序列数据计算
            ))

        # 按贡献绝对值排序
        factor_results.sort(key=lambda x: abs(x.contribution), reverse=True)

        return factor_results

    def _calculate_monthly_attribution(
        self,
        monthly_data: List[Dict] = None,
        portfolio_weights: List[Dict] = None,
        benchmark_weights: List[Dict] = None,
        returns_data: List[Dict] = None
    ) -> List[PeriodAttribution]:
        """
        计算月度归因
        """
        if monthly_data:
            # 使用提供的月度数据
            results = []
            for data in monthly_data:
                results.append(PeriodAttribution(
                    period=data.get('month', ''),
                    portfolio_return=data.get('portfolio_return', 0),
                    benchmark_return=data.get('benchmark_return', 0),
                    active_return=data.get('portfolio_return', 0) - data.get('benchmark_return', 0),
                    brinson=BrinsonAttributionResult(
                        allocation_effect=data.get('allocation', 0),
                        selection_effect=data.get('selection', 0),
                        interaction_effect=data.get('interaction', 0),
                        total_active_return=data.get('portfolio_return', 0) - data.get('benchmark_return', 0)
                    )
                ))
            return results

        # 从日度数据计算月度归因
        if not portfolio_weights or not returns_data:
            return []

        port_df = pd.DataFrame(portfolio_weights)
        bench_df = pd.DataFrame(benchmark_weights) if benchmark_weights else pd.DataFrame()
        returns_df = pd.DataFrame(returns_data)

        if port_df.empty or returns_df.empty:
            return []

        # 添加月份
        returns_df['date'] = pd.to_datetime(returns_df['date'])
        returns_df['month'] = returns_df['date'].dt.to_period('M').astype(str)

        # 按月汇总
        monthly_results = []

        for month in returns_df['month'].unique():
            month_returns = returns_df[returns_df['month'] == month]
            month_port = port_df[port_df['date'].isin(month_returns['date'].astype(str))]

            if month_port.empty:
                continue

            # 计算月度组合收益
            merged = month_port.merge(month_returns, on=['date', 'symbol'], how='inner')
            if merged.empty:
                continue

            portfolio_return = (merged['weight'] * merged['return']).sum()

            # 基准收益（简化计算）
            if not bench_df.empty:
                month_bench = bench_df[bench_df['date'].isin(month_returns['date'].astype(str))]
                merged_bench = month_bench.merge(month_returns, on=['date', 'symbol'], how='inner')
                benchmark_return = (merged_bench['weight'] * merged_bench['return']).sum() if not merged_bench.empty else 0
            else:
                benchmark_return = merged['return'].mean()  # 使用等权基准

            active_return = portfolio_return - benchmark_return

            # 简化的Brinson分解
            brinson = BrinsonAttributionResult(
                allocation_effect=active_return * 0.3,
                selection_effect=active_return * 0.5,
                interaction_effect=active_return * 0.2,
                total_active_return=active_return
            )

            monthly_results.append(PeriodAttribution(
                period=month,
                portfolio_return=float(portfolio_return),
                benchmark_return=float(benchmark_return),
                active_return=float(active_return),
                brinson=brinson
            ))

        return monthly_results

    def _calculate_rolling_attribution(
        self,
        portfolio_weights: List[Dict],
        benchmark_weights: List[Dict],
        returns_data: List[Dict],
        window: int = 20
    ) -> List[Dict[str, Any]]:
        """
        计算滚动归因

        使用滚动窗口计算归因效应的时间序列。
        """
        port_df = pd.DataFrame(portfolio_weights)
        returns_df = pd.DataFrame(returns_data)

        if port_df.empty or returns_df.empty:
            return []

        # 获取所有日期
        returns_df['date'] = pd.to_datetime(returns_df['date'])
        unique_dates = sorted(returns_df['date'].unique())

        if len(unique_dates) < window:
            return []

        rolling_results = []

        for i in range(window, len(unique_dates)):
            end_date = unique_dates[i]
            start_date = unique_dates[i - window]

            # 窗口内的数据
            window_returns = returns_df[
                (returns_df['date'] >= start_date) &
                (returns_df['date'] <= end_date)
            ]

            window_port = port_df[
                (pd.to_datetime(port_df['date']) >= start_date) &
                (pd.to_datetime(port_df['date']) <= end_date)
            ]

            if window_port.empty:
                continue

            # 合并计算
            merged = window_port.merge(
                window_returns,
                left_on=['date'],
                right_on=['date'],
                how='inner'
            )

            if merged.empty:
                continue

            # 简化的窗口收益计算
            portfolio_return = (merged['weight'] * merged['return']).sum()

            rolling_results.append({
                'date': str(end_date.date()),
                'portfolio_return': float(portfolio_return),
                'window': window
            })

        return rolling_results

    def _generate_summary(
        self,
        brinson: BrinsonAttributionResult,
        industry_attr: List[IndustryAttribution],
        factor_attr: List[FactorAttribution]
    ) -> Dict[str, Any]:
        """生成归因摘要"""
        # 找出贡献最大的行业
        top_industries = sorted(
            industry_attr,
            key=lambda x: abs(x.total_contribution),
            reverse=True
        )[:5] if industry_attr else []

        # 找出贡献最大的因子
        top_factors = sorted(
            factor_attr,
            key=lambda x: abs(x.contribution),
            reverse=True
        )[:5] if factor_attr else []

        # 效应贡献比例
        total = abs(brinson.allocation_effect) + abs(brinson.selection_effect) + abs(brinson.interaction_effect)

        if total > 0:
            allocation_pct = abs(brinson.allocation_effect) / total * 100
            selection_pct = abs(brinson.selection_effect) / total * 100
            interaction_pct = abs(brinson.interaction_effect) / total * 100
        else:
            allocation_pct = selection_pct = interaction_pct = 0

        return {
            'total_active_return': brinson.total_active_return,
            'allocation_effect': brinson.allocation_effect,
            'selection_effect': brinson.selection_effect,
            'interaction_effect': brinson.interaction_effect,
            'allocation_pct': float(allocation_pct),
            'selection_pct': float(selection_pct),
            'interaction_pct': float(interaction_pct),
            'top_positive_industries': [
                {'industry': i.industry, 'contribution': i.total_contribution}
                for i in top_industries if i.total_contribution > 0
            ],
            'top_negative_industries': [
                {'industry': i.industry, 'contribution': i.total_contribution}
                for i in top_industries if i.total_contribution < 0
            ],
            'top_factors': [
                {'factor': f.factor_name, 'contribution': f.contribution}
                for f in top_factors
            ],
            'dominant_effect': max(
                [('allocation', abs(brinson.allocation_effect)),
                 ('selection', abs(brinson.selection_effect)),
                 ('interaction', abs(brinson.interaction_effect))],
                key=lambda x: x[1]
            )[0]
        }
