"""
投资组合管理服务

提供组合管理、持仓管理、风险度量和组合优化功能。
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
import uuid
import numpy as np

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ...models import (
    Portfolio, PortfolioPosition, PortfolioRiskMetrics, PortfolioOptimization,
    PortfolioStatus, OptimizationMethod
)
from ...models.portfolio import portfolio_status_enum, optimization_method_enum


class PortfolioManager:
    """投资组合管理器"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 组合管理 ====================

    def create_portfolio(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        benchmark_symbol: Optional[str] = None,
        execution_mode: str = "PAPER",
        target_allocation: Optional[Dict] = None,
        rebalance_threshold: Decimal = Decimal("0.05"),
        rebalance_frequency: str = "MONTHLY"
    ) -> Portfolio:
        """创建投资组合"""
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description,
            benchmark_symbol=benchmark_symbol,
            execution_mode=execution_mode,
            target_allocation=target_allocation or {},
            rebalance_threshold=rebalance_threshold,
            rebalance_frequency=rebalance_frequency,
            status='ACTIVE',
            inception_date=date.today()
        )

        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)

        return portfolio

    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """获取投资组合"""
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def get_portfolios_by_user(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Portfolio]:
        """获取用户的投资组合列表"""
        query = self.db.query(Portfolio).filter(Portfolio.user_id == user_id)

        if status:
            query = query.filter(Portfolio.status == status)

        return query.order_by(desc(Portfolio.created_at)).all()

    def update_portfolio(
        self,
        portfolio_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Portfolio]:
        """更新投资组合"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None

        for key, value in updates.items():
            if hasattr(portfolio, key):
                setattr(portfolio, key, value)

        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def delete_portfolio(self, portfolio_id: str) -> bool:
        """删除投资组合"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return False

        self.db.delete(portfolio)
        self.db.commit()
        return True

    def update_portfolio_status(
        self,
        portfolio_id: str,
        status: str
    ) -> Optional[Portfolio]:
        """更新组合状态"""
        return self.update_portfolio(portfolio_id, {'status': status})

    # ==================== 持仓管理 ====================

    def get_positions(self, portfolio_id: str) -> List[PortfolioPosition]:
        """获取组合持仓"""
        return self.db.query(PortfolioPosition).filter(
            PortfolioPosition.portfolio_id == portfolio_id
        ).all()

    def get_position(
        self,
        portfolio_id: str,
        symbol: str
    ) -> Optional[PortfolioPosition]:
        """获取指定股票的持仓"""
        return self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.portfolio_id == portfolio_id,
                PortfolioPosition.symbol == symbol
            )
        ).first()

    def update_position(
        self,
        portfolio_id: str,
        symbol: str,
        quantity: int,
        price: Decimal,
        sector: Optional[str] = None,
        industry: Optional[str] = None
    ) -> PortfolioPosition:
        """更新持仓"""
        position = self.get_position(portfolio_id, symbol)

        if position:
            # 更新现有持仓
            if quantity > 0:
                # 计算新的平均成本
                total_cost = position.avg_cost * position.quantity + price * (quantity - position.quantity)
                position.quantity = quantity
                position.avg_cost = total_cost / quantity if quantity > 0 else Decimal("0")

            position.current_price = price
            position.market_value = price * quantity
            if position.avg_cost > 0:
                position.unrealized_pnl = (price - position.avg_cost) * quantity

            if sector:
                position.sector = sector
            if industry:
                position.industry = industry
        else:
            # 创建新持仓
            position = PortfolioPosition(
                portfolio_id=portfolio_id,
                symbol=symbol,
                quantity=quantity,
                avg_cost=price,
                current_price=price,
                market_value=price * quantity,
                sector=sector,
                industry=industry,
                opened_at=datetime.utcnow(),
                status='OPEN'
            )
            self.db.add(position)

        self.db.commit()
        self.db.refresh(position)

        # 更新组合总价值
        self._update_portfolio_value(portfolio_id)

        return position

    def close_position(
        self,
        portfolio_id: str,
        symbol: str,
        close_price: Decimal
    ) -> Optional[PortfolioPosition]:
        """平仓"""
        position = self.get_position(portfolio_id, symbol)
        if not position:
            return None

        # 计算已实现盈亏
        position.realized_pnl = (close_price - position.avg_cost) * position.quantity
        position.quantity = 0
        position.market_value = Decimal("0")
        position.unrealized_pnl = Decimal("0")
        position.current_price = close_price
        position.closed_at = datetime.utcnow()
        position.status = 'CLOSED'

        self.db.commit()
        self.db.refresh(position)

        # 更新组合总价值
        self._update_portfolio_value(portfolio_id)

        return position

    # ==================== 风险计算 ====================

    def calculate_risk_metrics(
        self,
        portfolio_id: str,
        calculation_date: Optional[date] = None
    ) -> PortfolioRiskMetrics:
        """
        计算组合风险指标

        Args:
            portfolio_id: 组合ID
            calculation_date: 计算日期

        Returns:
            PortfolioRiskMetrics: 风险指标
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError("Portfolio not found")

        calculation_date = calculation_date or date.today()
        positions = self.get_positions(portfolio_id)

        if not positions:
            return PortfolioRiskMetrics(
                portfolio_id=portfolio_id,
                calculation_date=calculation_date
            )

        # 计算权重
        total_value = sum(p.market_value or 0 for p in positions)
        weights = [(p.market_value / total_value) if total_value > 0 else 0 for p in positions]

        # 计算集中度指标
        herfindahl_index = sum(w ** 2 for w in weights)
        max_single_weight = max(weights) if weights else 0
        sorted_weights = sorted(weights, reverse=True)
        top_5_weight = sum(sorted_weights[:5])
        top_10_weight = sum(sorted_weights[:10])

        # 计算 VaR（简化实现）
        var_95 = total_value * Decimal("0.02")  # 假设 2% 的日 VaR
        var_99 = total_value * Decimal("0.03")  # 假设 3% 的日 VaR
        cvar_95 = total_value * Decimal("0.025")  # 假设 2.5% 的日 CVaR

        # 计算分散化比率
        diversification_ratio = Decimal("1") / Decimal(str(herfindahl_index)) if herfindahl_index > 0 else 1

        # 创建风险指标
        metrics = PortfolioRiskMetrics(
            portfolio_id=portfolio_id,
            calculation_date=calculation_date,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            herfindahl_index=Decimal(str(round(herfindahl_index, 6))),
            max_single_weight=Decimal(str(round(max_single_weight, 6))),
            top_5_weight=Decimal(str(round(top_5_weight, 6))),
            top_10_weight=Decimal(str(round(top_10_weight, 6))),
            diversification_ratio=diversification_ratio,
            portfolio_volatility=Decimal("0.15"),  # 简化实现
            max_drawdown=Decimal("0.10")  # 简化实现
        )

        # 检查是否已存在
        existing = self.db.query(PortfolioRiskMetrics).filter(
            and_(
                PortfolioRiskMetrics.portfolio_id == portfolio_id,
                PortfolioRiskMetrics.calculation_date == calculation_date
            )
        ).first()

        if existing:
            for key, value in metrics.to_dict().items():
                if hasattr(existing, key) and key not in ['id', 'created_at']:
                    setattr(existing, key, value)
            metrics = existing
        else:
            self.db.add(metrics)

        self.db.commit()
        self.db.refresh(metrics)
        return metrics

    def get_risk_metrics(
        self,
        portfolio_id: str,
        limit: int = 30
    ) -> List[PortfolioRiskMetrics]:
        """获取风险指标历史"""
        return self.db.query(PortfolioRiskMetrics).filter(
            PortfolioRiskMetrics.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioRiskMetrics.calculation_date)).limit(limit).all()

    def calculate_var(
        self,
        portfolio_id: str,
        confidence: float = 0.95
    ) -> Dict[str, Any]:
        """计算 VaR"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return {'error': 'Portfolio not found'}

        # 简化实现
        total_value = portfolio.total_value or Decimal("0")

        if confidence == 0.95:
            var = total_value * Decimal("0.02")
        elif confidence == 0.99:
            var = total_value * Decimal("0.03")
        else:
            var = total_value * Decimal("0.025")

        return {
            'portfolio_id': str(portfolio_id),
            'confidence': confidence,
            'var': float(var),
            'total_value': float(total_value),
            'var_percentage': float(var / total_value) if total_value > 0 else 0
        }

    def calculate_concentration(self, portfolio_id: str) -> Dict[str, Any]:
        """计算集中度"""
        positions = self.get_positions(portfolio_id)

        if not positions:
            return {'herfindahl_index': 0, 'max_weight': 0}

        total_value = sum(p.market_value or 0 for p in positions)
        weights = [(p.market_value / total_value) if total_value > 0 else 0 for p in positions]

        herfindahl_index = sum(w ** 2 for w in weights)

        # 按行业分组
        sector_weights = {}
        for p in positions:
            sector = p.sector or 'Unknown'
            sector_weights[sector] = sector_weights.get(sector, 0) + (p.market_value / total_value if total_value > 0 else 0)

        return {
            'herfindahl_index': round(herfindahl_index, 4),
            'max_weight': round(max(weights) if weights else 0, 4),
            'positions_count': len(positions),
            'sector_concentration': {k: round(v, 4) for k, v in sector_weights.items()}
        }

    # ==================== 组合优化 ====================

    def optimize_portfolio(
        self,
        portfolio_id: str,
        method: str = "MEAN_VARIANCE",
        constraints: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> PortfolioOptimization:
        """
        执行组合优化

        Args:
            portfolio_id: 组合ID
            method: 优化方法
            constraints: 约束条件
            created_by: 创建者ID

        Returns:
            PortfolioOptimization: 优化结果
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError("Portfolio not found")

        positions = self.get_positions(portfolio_id)

        # 获取当前权重
        total_value = sum(p.market_value or 0 for p in positions)
        current_weights = {
            p.symbol: float(p.market_value / total_value) if total_value > 0 else 0
            for p in positions
        }

        # 执行优化（简化实现）
        if method == "EQUAL_WEIGHT":
            optimal_weights = self._equal_weight_optimization(list(current_weights.keys()))
        elif method == "MIN_VARIANCE":
            optimal_weights = self._min_variance_optimization(current_weights)
        else:  # MEAN_VARIANCE
            optimal_weights = self._mean_variance_optimization(current_weights)

        # 计算调仓建议
        rebalance_trades = self._calculate_rebalance_trades(
            current_weights, optimal_weights, total_value
        )

        # 创建优化记录
        optimization = PortfolioOptimization(
            portfolio_id=portfolio_id,
            optimization_method=method,
            constraints=constraints or {},
            current_weights=current_weights,
            optimal_weights=optimal_weights,
            expected_return=Decimal("0.10"),  # 简化实现
            expected_risk=Decimal("0.15"),    # 简化实现
            expected_sharpe=Decimal("0.67"),  # 简化实现
            rebalance_trades=rebalance_trades,
            estimated_transaction_cost=Decimal(str(total_value * Decimal("0.002"))),  # 0.2% 成本
            status='PENDING',
            created_by=created_by
        )

        self.db.add(optimization)
        self.db.commit()
        self.db.refresh(optimization)

        return optimization

    def get_optimizations(
        self,
        portfolio_id: str,
        limit: int = 10
    ) -> List[PortfolioOptimization]:
        """获取优化历史"""
        return self.db.query(PortfolioOptimization).filter(
            PortfolioOptimization.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioOptimization.created_at)).limit(limit).all()

    def apply_optimization(self, optimization_id: str) -> bool:
        """应用优化结果"""
        optimization = self.db.query(PortfolioOptimization).filter(
            PortfolioOptimization.id == optimization_id
        ).first()

        if not optimization or optimization.status != 'PENDING':
            return False

        # 应用权重（简化实现）
        optimization.status = 'APPLIED'
        optimization.applied_at = datetime.utcnow()

        self.db.commit()
        return True

    # ==================== 辅助方法 ====================

    def _update_portfolio_value(self, portfolio_id: str) -> None:
        """更新组合总价值"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return

        positions = self.get_positions(portfolio_id)
        total_value = sum(p.market_value or 0 for p in positions)

        portfolio.total_value = total_value
        self.db.commit()

    def _equal_weight_optimization(self, symbols: List[str]) -> Dict[str, float]:
        """等权重优化"""
        n = len(symbols)
        weight = 1.0 / n if n > 0 else 0
        return {symbol: weight for symbol in symbols}

    def _min_variance_optimization(self, current_weights: Dict[str, float]) -> Dict[str, float]:
        """最小方差优化（简化实现）"""
        # 简化实现：返回等权重
        return self._equal_weight_optimization(list(current_weights.keys()))

    def _mean_variance_optimization(self, current_weights: Dict[str, float]) -> Dict[str, float]:
        """均值方差优化（简化实现）"""
        # 简化实现：返回等权重
        return self._equal_weight_optimization(list(current_weights.keys()))

    def _calculate_rebalance_trades(
        self,
        current_weights: Dict[str, float],
        optimal_weights: Dict[str, float],
        total_value: Decimal
    ) -> List[Dict]:
        """计算调仓建议"""
        trades = []
        all_symbols = set(current_weights.keys()) | set(optimal_weights.keys())

        for symbol in all_symbols:
            current = current_weights.get(symbol, 0)
            optimal = optimal_weights.get(symbol, 0)
            change = optimal - current

            if abs(change) > 0.001:  # 忽略微小变化
                trades.append({
                    'symbol': symbol,
                    'action': 'BUY' if change > 0 else 'SELL',
                    'weight_change': round(change, 4),
                    'estimated_amount': float(total_value * abs(Decimal(str(change))))
                })

        return trades
