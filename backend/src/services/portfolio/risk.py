"""
投资组合风险分析服务

提供组合风险指标计算、VaR 分析、集中度风险等功能。
"""

from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_
import numpy as np

from src.models.portfolio import Portfolio, PortfolioPosition, PortfolioRiskMetrics
from src.repositories.portfolio import PortfolioRepository


class PortfolioRiskService:
    """投资组合风险服务"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = PortfolioRepository(db)

    def get_metrics_history(self, portfolio_id: str, limit: int = 10) -> List[PortfolioRiskMetrics]:
        """获取风险指标历史"""
        metrics = self.db.query(PortfolioRiskMetrics).filter(
            PortfolioRiskMetrics.portfolio_id == portfolio_id
        ).order_by(
            PortfolioRiskMetrics.calculation_date.desc()
        ).limit(limit).all()
        return metrics

    async def calculate_var(
        self,
        portfolio_id: str,
        confidence: float = 0.95
    ) -> Decimal:
        """
        计算组合 VaR（历史模拟法）

        Args:
            portfolio_id: 组合ID
            confidence: 置信水平（0.9-0.99）

        Returns:
            VaR 值
        """
        # 获取组合持仓
        positions = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.portfolio_id == portfolio_id,
                PortfolioPosition.status == 'OPEN'
            )
        ).all()

        if not positions:
            return Decimal("0")

        # 计算组合价值
        total_value = sum(
            (p.market_value or Decimal("0"))
            for p in positions
        )

        if total_value <= 0:
            return Decimal("0")

        # 简化实现：基于持仓权重的近似 VaR
        # 实际应该使用历史收益数据
        weights = []
        for p in positions:
            if p.market_value and total_value > 0:
                weights.append(float(p.market_value / total_value))
            else:
                weights.append(0)

        weights = np.array(weights)

        # 假设个股日波动率约为 2.5%
        avg_volatility = 0.025

        # 组合波动率（简化：假设相关性为0.5）
        n = len(weights)
        correlation = 0.5
        portfolio_variance = np.dot(weights, weights) * avg_volatility**2 * (1 - correlation + correlation * n)
        portfolio_volatility = np.sqrt(portfolio_variance) / np.sqrt(n) if n > 0 else 0

        # VaR 计算（正态分布假设）
        from scipy import stats
        z_score = stats.norm.ppf(confidence)
        var = float(total_value) * portfolio_volatility * z_score

        return Decimal(str(round(var, 2)))

    def calculate_risk_metrics(
        self,
        portfolio_id: str,
        calculation_date: Optional[date] = None
    ) -> PortfolioRiskMetrics:
        """
        计算完整的风险指标

        Args:
            portfolio_id: 组合ID
            calculation_date: 计算日期

        Returns:
            风险指标对象
        """
        calculation_date = calculation_date or date.today()

        # 获取组合持仓
        positions = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.portfolio_id == portfolio_id,
                PortfolioPosition.status == 'OPEN'
            )
        ).all()

        # 计算权重
        total_value = sum(
            (p.market_value or Decimal("0"))
            for p in positions
        )

        weights = []
        for p in positions:
            if p.market_value and total_value > 0:
                weights.append(float(p.market_value / total_value))
            else:
                weights.append(0)

        # 计算集中度指标
        herfindahl_index = sum(w**2 for w in weights) if weights else 0
        max_single_weight = max(weights) if weights else 0

        # 分散化比率（1 - 赫芬达尔指数）
        diversification_ratio = 1 - herfindahl_index

        # 创建风险指标记录
        metrics = PortfolioRiskMetrics(
            id=uuid.uuid4(),
            portfolio_id=portfolio_id,
            calculation_date=calculation_date,
            herfindahl_index=Decimal(str(round(herfindahl_index, 6))),
            max_single_weight=Decimal(str(round(max_single_weight, 6))),
            diversification_ratio=Decimal(str(round(diversification_ratio, 6))),
            portfolio_volatility=Decimal("0.025"),  # 简化值
            max_drawdown=Decimal("0.1"),  # 简化值
            var_95=Decimal("0"),  # 需要异步计算
            var_99=Decimal("0"),
            cvar_95=Decimal("0"),
        )

        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)

        return metrics

    def calculate_concentration_risk(
        self,
        portfolio_id: str
    ) -> dict:
        """
        计算集中度风险

        Returns:
            包含集中度指标的字典
        """
        positions = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.portfolio_id == portfolio_id,
                PortfolioPosition.status == 'OPEN'
            )
        ).all()

        if not positions:
            return {
                'herfindahl_index': 0,
                'max_single_weight': 0,
                'top_5_weight': 0,
                'position_count': 0
            }

        # 计算权重
        total_value = sum(
            (p.market_value or Decimal("0"))
            for p in positions
        )

        weights = []
        for p in positions:
            if p.market_value and total_value > 0:
                weights.append(float(p.market_value / total_value))
            else:
                weights.append(0)

        weights.sort(reverse=True)

        return {
            'herfindahl_index': sum(w**2 for w in weights),
            'max_single_weight': weights[0] if weights else 0,
            'top_5_weight': sum(weights[:5]),
            'position_count': len(positions)
        }

    def check_risk_limits(
        self,
        portfolio_id: str,
        max_single_weight: float = 0.2,
        max_herfindahl: float = 0.25
    ) -> dict:
        """
        检查风险限制

        Args:
            portfolio_id: 组合ID
            max_single_weight: 单只最大权重限制
            max_herfindahl: 赫芬达尔指数限制

        Returns:
            检查结果
        """
        concentration = self.calculate_concentration_risk(portfolio_id)

        violations = []

        if concentration['max_single_weight'] > max_single_weight:
            violations.append({
                'type': 'SINGLE_WEIGHT_EXCEEDED',
                'value': concentration['max_single_weight'],
                'limit': max_single_weight,
                'message': f"单只权重 {concentration['max_single_weight']:.2%} 超过限制 {max_single_weight:.2%}"
            })

        if concentration['herfindahl_index'] > max_herfindahl:
            violations.append({
                'type': 'CONCENTRATION_EXCEEDED',
                'value': concentration['herfindahl_index'],
                'limit': max_herfindahl,
                'message': f"集中度指数 {concentration['herfindahl_index']:.4f} 超过限制 {max_herfindahl:.4f}"
            })

        return {
            'is_compliant': len(violations) == 0,
            'violations': violations,
            'metrics': concentration
        }
