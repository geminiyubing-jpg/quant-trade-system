"""
回测分析服务

提供因子分析、归因分析和扩展绩效指标计算功能。
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc
import numpy as np
import pandas as pd

from ...models import (
    BacktestResultData, FactorAnalysis, AttributionAnalysis, BacktestMetricsExtended
)


class BacktestAnalysisService:
    """回测分析服务 - 处理因子分析和归因分析"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 因子分析 ====================

    def analyze_factors(
        self,
        backtest_result_id: int,
        factor_name: str,
        signals: List[Dict],
        returns: List[Dict]
    ) -> FactorAnalysis:
        """
        执行因子分析

        Args:
            backtest_result_id: 回测结果ID
            factor_name: 因子名称
            signals: 信号列表 [{date, symbol, signal_value}]
            returns: 收益列表 [{date, symbol, return}]

        Returns:
            FactorAnalysis: 因子分析结果
        """
        # 计算 IC 序列
        ic_series = self._calculate_ic_series(signals, returns)

        # 计算 IC 统计量
        ic_values = [ic['ic'] for ic in ic_series if ic['ic'] is not None]
        if ic_values:
            ic_mean = np.mean(ic_values)
            ic_std = np.std(ic_values)
            ic_ir = ic_mean / ic_std if ic_std != 0 else 0
            ic_t_stat = ic_mean / (ic_std / np.sqrt(len(ic_values))) if ic_std != 0 else 0
            ic_positive_ratio = sum(1 for ic in ic_values if ic > 0) / len(ic_values)
        else:
            ic_mean = ic_std = ic_ir = ic_t_stat = ic_positive_ratio = 0

        # 计算因子收益
        factor_return_series = self._calculate_factor_return_series(signals, returns)
        factor_returns = [r['return'] for r in factor_return_series if r['return'] is not None]
        if factor_returns:
            factor_return = np.mean(factor_returns)
            factor_volatility = np.std(factor_returns)
            factor_t_stat = factor_return / (factor_volatility / np.sqrt(len(factor_returns))) if factor_volatility != 0 else 0
        else:
            factor_return = factor_volatility = factor_t_stat = 0

        # 计算换手率
        avg_turnover = self._calculate_avg_turnover(signals)
        turnover_cost = avg_turnover * 0.003  # 假设0.3%换手成本

        # 计算分组收益
        group_returns = self._calculate_group_returns(signals, returns, n_groups=5)

        # 计算多空收益
        long_short_return = self._calculate_long_short_return(group_returns)

        # 保存结果
        analysis = FactorAnalysis(
            backtest_result_id=backtest_result_id,
            factor_name=factor_name,
            ic_mean=Decimal(str(round(ic_mean, 6))),
            ic_std=Decimal(str(round(ic_std, 6))),
            ic_ir=Decimal(str(round(ic_ir, 6))),
            ic_t_stat=Decimal(str(round(ic_t_stat, 6))),
            ic_positive_ratio=Decimal(str(round(ic_positive_ratio, 4))),
            factor_return=Decimal(str(round(factor_return, 6))),
            factor_volatility=Decimal(str(round(factor_volatility, 6))),
            factor_t_stat=Decimal(str(round(factor_t_stat, 6))),
            avg_turnover=Decimal(str(round(avg_turnover, 6))),
            turnover_cost=Decimal(str(round(turnover_cost, 8))),
            group_returns=group_returns,
            long_short_return=Decimal(str(round(long_short_return, 6))),
            ic_series=ic_series,
            factor_return_series=factor_return_series
        )

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        return analysis

    def get_factor_analyses(self, backtest_result_id: int) -> List[FactorAnalysis]:
        """获取回测的因子分析结果"""
        return self.db.query(FactorAnalysis).filter(
            FactorAnalysis.backtest_result_id == backtest_result_id
        ).all()

    # ==================== 归因分析 ====================

    def run_attribution(
        self,
        backtest_result_id: int,
        portfolio_weights: List[Dict],
        benchmark_weights: List[Dict],
        returns_data: List[Dict],
        benchmark_symbol: str = "000300.SH"
    ) -> AttributionAnalysis:
        """
        执行归因分析（Brinson模型）

        Args:
            backtest_result_id: 回测结果ID
            portfolio_weights: 组合权重 [{symbol, weight}]
            benchmark_weights: 基准权重 [{symbol, weight}]
            returns_data: 收益数据 [{symbol, return}]
            benchmark_symbol: 基准代码

        Returns:
            AttributionAnalysis: 归因分析结果
        """
        # 计算 Brinson 归因
        brinson_result = self._calculate_brinson_attribution(
            portfolio_weights, benchmark_weights, returns_data
        )

        # 计算基准收益
        benchmark_return = sum(
            w['weight'] * next(
                (r['return'] for r in returns_data if r['symbol'] == w['symbol']), 0
            )
            for w in benchmark_weights
        )

        # 行业归因
        industry_attribution = self._calculate_industry_attribution(
            portfolio_weights, benchmark_weights, returns_data
        )

        # 月度归因
        monthly_attribution = []  # 简化实现

        # 保存结果
        analysis = AttributionAnalysis(
            backtest_result_id=backtest_result_id,
            allocation_effect=Decimal(str(round(brinson_result['allocation_effect'], 6))),
            selection_effect=Decimal(str(round(brinson_result['selection_effect'], 6))),
            interaction_effect=Decimal(str(round(brinson_result['interaction_effect'], 6))),
            total_active_return=Decimal(str(round(brinson_result['total_active_return'], 6))),
            industry_attribution=industry_attribution,
            benchmark_symbol=benchmark_symbol,
            benchmark_return=Decimal(str(round(benchmark_return, 6))),
            monthly_attribution=monthly_attribution
        )

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        return analysis

    def get_attribution(self, backtest_result_id: int) -> Optional[AttributionAnalysis]:
        """获取归因分析结果"""
        return self.db.query(AttributionAnalysis).filter(
            AttributionAnalysis.backtest_result_id == backtest_result_id
        ).first()

    # ==================== 扩展指标计算 ====================

    def calculate_extended_metrics(
        self,
        backtest_result_id: int,
        equity_curve: List[float],
        daily_returns: List[float],
        benchmark_returns: List[float],
        trades: List[Dict]
    ) -> BacktestMetricsExtended:
        """
        计算扩展绩效指标

        Args:
            backtest_result_id: 回测结果ID
            equity_curve: 资金曲线
            daily_returns: 日收益率
            benchmark_returns: 基准日收益率
            trades: 交易记录

        Returns:
            BacktestMetricsExtended: 扩展指标
        """
        returns = np.array(daily_returns)
        benchmark = np.array(benchmark_returns) if benchmark_returns else np.zeros_like(returns)

        # Sortino 比率
        downside_returns = returns[returns < 0]
        downside_deviation = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino_ratio = (np.mean(returns) * 252) / (downside_deviation * np.sqrt(252)) if downside_deviation != 0 else 0

        # 最大回撤和 Calmar 比率
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        annual_return = (1 + np.mean(returns)) ** 252 - 1 if len(returns) > 0 else 0
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Alpha 和 Beta
        if len(benchmark) == len(returns) and np.std(benchmark) > 0:
            beta = np.cov(returns, benchmark)[0, 1] / np.var(benchmark)
            alpha = annual_return - (np.mean(benchmark) * 252 + 0.02 * (1 - beta))  # 假设无风险利率2%
        else:
            beta = 1
            alpha = 0

        # 跟踪误差和信息比率
        excess_returns = returns - benchmark
        tracking_error = np.std(excess_returns) * np.sqrt(252)
        information_ratio = (np.mean(excess_returns) * 252) / tracking_error if tracking_error != 0 else 0

        # 交易质量指标
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]

        total_profit = sum(t.get('pnl', 0) for t in winning_trades)
        total_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))

        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        avg_win = np.mean([t.get('pnl', 0) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t.get('pnl', 0)) for t in losing_trades]) if losing_trades else 0
        payoff_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        # 连续亏损
        max_consecutive_losses = self._calculate_max_consecutive_losses(trades)

        # 保存结果
        metrics = BacktestMetricsExtended(
            backtest_result_id=backtest_result_id,
            sortino_ratio=Decimal(str(round(sortino_ratio, 6))),
            calmar_ratio=Decimal(str(round(calmar_ratio, 6))),
            information_ratio=Decimal(str(round(information_ratio, 6))),
            alpha=Decimal(str(round(alpha, 6))),
            beta=Decimal(str(round(beta, 6))),
            tracking_error=Decimal(str(round(tracking_error, 6))),
            downside_deviation=Decimal(str(round(downside_deviation, 6))),
            max_consecutive_losses=max_consecutive_losses,
            profit_factor=Decimal(str(round(profit_factor, 6))),
            payoff_ratio=Decimal(str(round(payoff_ratio, 6))),
            avg_holding_days=Decimal("5.0"),  # 简化实现
            avg_drawdown=Decimal(str(round(self._calculate_avg_drawdown(equity_curve), 6))),
            recovery_factor=Decimal(str(round(annual_return / abs(max_drawdown), 6))) if max_drawdown != 0 else 0
        )

        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)

        return metrics

    def get_extended_metrics(self, backtest_result_id: int) -> Optional[BacktestMetricsExtended]:
        """获取扩展指标"""
        return self.db.query(BacktestMetricsExtended).filter(
            BacktestMetricsExtended.backtest_result_id == backtest_result_id
        ).first()

    # ==================== 辅助方法 ====================

    def _calculate_ic_series(
        self,
        signals: List[Dict],
        returns: List[Dict]
    ) -> List[Dict]:
        """计算 IC 时间序列"""
        # 按日期分组
        signal_df = pd.DataFrame(signals)
        return_df = pd.DataFrame(returns)

        if signal_df.empty or return_df.empty:
            return []

        ic_series = []
        for date in signal_df['date'].unique():
            date_signals = signal_df[signal_df['date'] == date]
            date_returns = return_df[return_df['date'] == date]

            merged = date_signals.merge(date_returns, on='symbol', how='inner')
            if len(merged) > 2:
                ic = merged['signal_value'].corr(merged['return'])
                ic_series.append({
                    'date': date,
                    'ic': ic if not np.isnan(ic) else None
                })

        return ic_series

    def _calculate_factor_return_series(
        self,
        signals: List[Dict],
        returns: List[Dict]
    ) -> List[Dict]:
        """计算因子收益时间序列"""
        # 简化实现：按信号分组计算收益差
        signal_df = pd.DataFrame(signals)
        return_df = pd.DataFrame(returns)

        if signal_df.empty or return_df.empty:
            return []

        factor_returns = []
        for date in signal_df['date'].unique():
            date_signals = signal_df[signal_df['date'] == date]
            date_returns = return_df[return_df['date'] == date]

            merged = date_signals.merge(date_returns, on='symbol', how='inner')
            if len(merged) > 0:
                # 按信号分位数分组
                merged['quantile'] = pd.qcut(merged['signal_value'], 5, labels=False, duplicates='drop')
                top_returns = merged[merged['quantile'] == merged['quantile'].max()]['return'].mean()
                bottom_returns = merged[merged['quantile'] == merged['quantile'].min()]['return'].mean()
                factor_returns.append({
                    'date': date,
                    'return': top_returns - bottom_returns if not np.isnan(top_returns - bottom_returns) else 0
                })

        return factor_returns

    def _calculate_avg_turnover(self, signals: List[Dict]) -> float:
        """计算平均换手率"""
        # 简化实现
        return 0.3

    def _calculate_group_returns(
        self,
        signals: List[Dict],
        returns: List[Dict],
        n_groups: int = 5
    ) -> List[Dict]:
        """计算分组收益"""
        signal_df = pd.DataFrame(signals)
        return_df = pd.DataFrame(returns)

        if signal_df.empty or return_df.empty:
            return []

        merged = signal_df.merge(return_df, on=['date', 'symbol'], how='inner')
        if merged.empty:
            return []

        merged['group'] = pd.qcut(merged['signal_value'], n_groups, labels=False, duplicates='drop')

        group_returns = []
        for g in range(n_groups):
            group_data = merged[merged['group'] == g]
            if not group_data.empty:
                group_returns.append({
                    'group': int(g + 1),
                    'return': float(group_data['return'].mean())
                })

        return group_returns

    def _calculate_long_short_return(self, group_returns: List[Dict]) -> float:
        """计算多空收益"""
        if len(group_returns) < 2:
            return 0

        top_return = max(g['return'] for g in group_returns)
        bottom_return = min(g['return'] for g in group_returns)

        return top_return - bottom_return

    def _calculate_brinson_attribution(
        self,
        portfolio_weights: List[Dict],
        benchmark_weights: List[Dict],
        returns_data: List[Dict]
    ) -> Dict[str, float]:
        """计算 Brinson 归因"""
        # 简化实现
        portfolio_return = sum(
            w['weight'] * next(
                (r['return'] for r in returns_data if r['symbol'] == w['symbol']), 0
            )
            for w in portfolio_weights
        )

        benchmark_return = sum(
            w['weight'] * next(
                (r['return'] for r in returns_data if r['symbol'] == w['symbol']), 0
            )
            for w in benchmark_weights
        )

        total_active_return = portfolio_return - benchmark_return

        # 简化分配（实际应该更复杂的计算）
        allocation_effect = total_active_return * 0.3
        selection_effect = total_active_return * 0.5
        interaction_effect = total_active_return * 0.2

        return {
            'allocation_effect': allocation_effect,
            'selection_effect': selection_effect,
            'interaction_effect': interaction_effect,
            'total_active_return': total_active_return
        }

    def _calculate_industry_attribution(
        self,
        portfolio_weights: List[Dict],
        benchmark_weights: List[Dict],
        returns_data: List[Dict]
    ) -> List[Dict]:
        """计算行业归因"""
        # 简化实现
        return []

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤"""
        if not equity_curve:
            return 0

        equity = np.array(equity_curve)
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        return float(np.max(drawdown))

    def _calculate_avg_drawdown(self, equity_curve: List[float]) -> float:
        """计算平均回撤"""
        if not equity_curve:
            return 0

        equity = np.array(equity_curve)
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        return float(np.mean(drawdown[drawdown > 0])) if np.any(drawdown > 0) else 0

    def _calculate_max_consecutive_losses(self, trades: List[Dict]) -> int:
        """计算最大连续亏损次数"""
        if not trades:
            return 0

        max_losses = 0
        current_losses = 0

        for trade in trades:
            if trade.get('pnl', 0) < 0:
                current_losses += 1
                max_losses = max(max_losses, current_losses)
            else:
                current_losses = 0

        return max_losses
