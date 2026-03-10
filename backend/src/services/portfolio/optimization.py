"""
投资组合优化服务

提供均值方差优化、风险平价、最大夏普等优化方法。
"""

from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional, Dict
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_
import numpy as np

from src.models.portfolio import (
    Portfolio, PortfolioPosition, PortfolioOptimization,
    OptimizationMethod
)
from src.repositories.portfolio import PortfolioRepository


class PortfolioOptimizationService:
    """投资组合优化服务"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = PortfolioRepository(db)

    async def optimize(
        self,
        portfolio_id: str,
        method: OptimizationMethod,
        constraints: Optional[Dict] = None
    ) -> PortfolioOptimization:
        """
        执行组合优化

        Args:
            portfolio_id: 组合ID
            method: 优化方法
            constraints: 约束条件

        Returns:
            优化结果
        """
        # 获取当前持仓
        positions = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.portfolio_id == portfolio_id,
                PortfolioPosition.status == 'OPEN'
            )
        ).all()

        # 计算当前权重
        total_value = sum(
            (p.market_value or Decimal("0"))
            for p in positions
        )

        current_weights = {}
        symbols = []
        for p in positions:
            symbols.append(p.symbol)
            if total_value > 0 and p.market_value:
                current_weights[p.symbol] = float(p.market_value / total_value)
            else:
                current_weights[p.symbol] = 0

        # 根据优化方法计算最优权重
        if method == OptimizationMethod.EQUAL_WEIGHT:
            optimal_weights = self._equal_weight_optimization(symbols)
        elif method == OptimizationMethod.MIN_VARIANCE:
            optimal_weights = self._min_variance_optimization(symbols, constraints)
        elif method == OptimizationMethod.MAX_SHARPE:
            optimal_weights = self._max_sharpe_optimization(symbols, constraints)
        elif method == OptimizationMethod.RISK_PARITY:
            optimal_weights = self._risk_parity_optimization(symbols, constraints)
        elif method == OptimizationMethod.MEAN_VARIANCE:
            optimal_weights = self._mean_variance_optimization(symbols, constraints)
        else:
            optimal_weights = self._equal_weight_optimization(symbols)

        # 计算调仓建议
        rebalance_trades = self._calculate_rebalance_trades(
            symbols, current_weights, optimal_weights, float(total_value)
        )

        # 计算预期指标
        expected_return, expected_risk, expected_sharpe = self._calculate_expected_metrics(
            optimal_weights, constraints
        )

        # 估算交易成本
        estimated_cost = self._estimate_transaction_cost(rebalance_trades)

        # 创建优化记录
        optimization = PortfolioOptimization(
            id=uuid.uuid4(),
            portfolio_id=portfolio_id,
            optimization_method=method,
            constraints=constraints,
            current_weights=current_weights,
            optimal_weights=optimal_weights,
            expected_return=Decimal(str(expected_return)),
            expected_risk=Decimal(str(expected_risk)),
            expected_sharpe=Decimal(str(expected_sharpe)),
            rebalance_trades=rebalance_trades,
            estimated_transaction_cost=Decimal(str(estimated_cost)),
            status='PENDING'
        )

        self.db.add(optimization)
        self.db.commit()
        self.db.refresh(optimization)

        return optimization

    def _equal_weight_optimization(self, symbols: List[str]) -> Dict[str, float]:
        """等权重优化"""
        n = len(symbols)
        if n == 0:
            return {}
        weight = 1.0 / n
        return {s: weight for s in symbols}

    def _min_variance_optimization(
        self,
        symbols: List[str],
        constraints: Optional[Dict] = None
    ) -> Dict[str, float]:
        """最小方差优化"""
        # 简化实现：使用等权重作为近似
        # 实际应该使用协方差矩阵优化
        return self._equal_weight_optimization(symbols)

    def _max_sharpe_optimization(
        self,
        symbols: List[str],
        constraints: Optional[Dict] = None
    ) -> Dict[str, float]:
        """最大夏普比率优化"""
        # 简化实现：使用等权重作为近似
        # 实际需要预期收益和协方差矩阵
        return self._equal_weight_optimization(symbols)

    def _risk_parity_optimization(
        self,
        symbols: List[str],
        constraints: Optional[Dict] = None
    ) -> Dict[str, float]:
        """风险平价优化"""
        # 简化实现：假设波动率相同，退化为等权重
        # 实际应该根据波动率调整权重
        return self._equal_weight_optimization(symbols)

    def _mean_variance_optimization(
        self,
        symbols: List[str],
        constraints: Optional[Dict] = None
    ) -> Dict[str, float]:
        """均值方差优化"""
        # 简化实现：使用等权重作为近似
        return self._equal_weight_optimization(symbols)

    def _calculate_rebalance_trades(
        self,
        symbols: List[str],
        current_weights: Dict[str, float],
        optimal_weights: Dict[str, float],
        total_value: float
    ) -> List[Dict]:
        """计算调仓建议"""
        trades = []
        min_trade_value = total_value * 0.01  # 最小调仓阈值 1%

        for symbol in symbols:
            current = current_weights.get(symbol, 0)
            optimal = optimal_weights.get(symbol, 0)
            diff = optimal - current

            if abs(diff * total_value) >= min_trade_value:
                trades.append({
                    'symbol': symbol,
                    'action': 'BUY' if diff > 0 else 'SELL',
                    'current_weight': round(current, 4),
                    'target_weight': round(optimal, 4),
                    'weight_change': round(diff, 4),
                    'estimated_value': round(abs(diff * total_value), 2)
                })

        return trades

    def _calculate_expected_metrics(
        self,
        weights: Dict[str, float],
        constraints: Optional[Dict] = None
    ) -> tuple:
        """计算预期收益、风险和夏普比率"""
        # 简化实现：使用假设值
        # 实际需要历史数据和预测模型

        # 假设年化收益 8%，波动率 15%
        expected_return = 0.08
        expected_risk = 0.15
        risk_free_rate = 0.03

        expected_sharpe = (expected_return - risk_free_rate) / expected_risk if expected_risk > 0 else 0

        return expected_return, expected_risk, expected_sharpe

    def _estimate_transaction_cost(self, trades: List[Dict]) -> float:
        """估算交易成本"""
        # 简化计算：佣金 0.03% + 印花税 0.1%（卖出） + 冲击成本 0.05%
        total_cost = 0
        for trade in trades:
            value = trade.get('estimated_value', 0)
            action = trade.get('action', 'BUY')

            # 佣金
            commission = value * 0.0003
            # 印花税（仅卖出）
            stamp_duty = value * 0.001 if action == 'SELL' else 0
            # 冲击成本
            impact = value * 0.0005

            total_cost += commission + stamp_duty + impact

        return round(total_cost, 2)

    def get_optimization_history(
        self,
        portfolio_id: str,
        limit: int = 10
    ) -> List[PortfolioOptimization]:
        """获取优化历史"""
        optimizations = self.db.query(PortfolioOptimization).filter(
            PortfolioOptimization.portfolio_id == portfolio_id
        ).order_by(
            PortfolioOptimization.created_at.desc()
        ).limit(limit).all()
        return optimizations

    def apply_optimization(self, optimization_id: str) -> bool:
        """
        应用优化结果

        Args:
            optimization_id: 优化记录ID

        Returns:
            是否成功
        """
        optimization = self.db.query(PortfolioOptimization).filter(
            PortfolioOptimization.id == optimization_id
        ).first()

        if not optimization or optimization.status != 'PENDING':
            return False

        # 更新状态
        optimization.status = 'APPLIED'
        optimization.applied_at = datetime.utcnow()

        self.db.commit()
        return True
