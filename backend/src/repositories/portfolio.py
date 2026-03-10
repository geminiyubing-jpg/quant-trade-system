"""
投资组合数据访问层
"""

from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import logging

from src.models.portfolio import (
    Portfolio, PortfolioPosition, PortfolioRiskMetrics, PortfolioOptimization
)

logger = logging.getLogger(__name__)


class PortfolioRepository:
    """投资组合数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, user_id: str, include_closed: bool = False) -> List[Portfolio]:
        """获取用户的所有组合"""
        query = self.db.query(Portfolio).filter(Portfolio.user_id == user_id)
        if not include_closed:
            query = query.filter(Portfolio.status != 'CLOSED')
        return query.order_by(desc(Portfolio.created_at)).all()

    def get_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        """获取组合详情"""
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def create(self, portfolio: Portfolio) -> Portfolio:
        """创建组合"""
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def update(self, portfolio: Portfolio) -> Portfolio:
        """更新组合"""
        self.db.merge(portfolio)
        self.db.commit()
        return portfolio

    def delete(self, portfolio_id: str) -> bool:
        """删除组合"""
        portfolio = self.get_by_id(portfolio_id)
        if not portfolio:
            return False
        self.db.delete(portfolio)
        self.db.commit()
        return True

    def get_total_value(self, portfolio_id: str) -> Decimal:
        """获取组合总价值"""
        positions = self.db.query(PortfolioPosition).filter(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.status == 'OPEN'
        ).all()
        total_value = sum(p.market_value or 0 for p in positions if p.market_value)
        return Decimal(str(total_value)) if total_value else Decimal("0")


class PortfolioPositionRepository:
    """组合持仓数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_portfolio(self, portfolio_id: str, include_closed: bool = False) -> List[PortfolioPosition]:
        """获取组合的所有持仓"""
        query = self.db.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == portfolio_id)
        if not include_closed:
            query = query.filter(PortfolioPosition.status == 'OPEN')
        return query.all()

    def get_by_symbol(self, portfolio_id: str, symbol: str) -> Optional[PortfolioPosition]:
        """获取特定股票的持仓"""
        return self.db.query(PortfolioPosition).filter(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.symbol == symbol
        ).first()

    def calculate_weights(self, portfolio_id: str) -> Dict[str, float]:
        """计算持仓权重"""
        positions = self.get_by_portfolio(portfolio_id)
        total_value = sum(p.market_value or 0 for p in positions if p.market_value)
        weights = {}
        for pos in positions:
            if pos.market_value and total_value > 0:
                weights[pos.symbol] = float(pos.market_value) / float(total_value)
            else:
                weights[pos.symbol] = 0.0
        return weights


class PortfolioRiskMetricsRepository:
    """组合风险指标数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_latest(self, portfolio_id: str) -> Optional[PortfolioRiskMetrics]:
        """获取最新风险指标"""
        return self.db.query(PortfolioRiskMetrics).filter(
            PortfolioRiskMetrics.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioRiskMetrics.calculation_date)).first()

    def get_history(self, portfolio_id: str, limit: int = 30) -> List[PortfolioRiskMetrics]:
        """获取历史风险指标"""
        return self.db.query(PortfolioRiskMetrics).filter(
            PortfolioRiskMetrics.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioRiskMetrics.calculation_date)).limit(limit).all()


class PortfolioOptimizationRepository:
    """组合优化记录数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_portfolio(self, portfolio_id: str, limit: int = 10) -> List[PortfolioOptimization]:
        """获取组合的优化历史"""
        return self.db.query(PortfolioOptimization).filter(
            PortfolioOptimization.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioOptimization.created_at)).limit(limit).all()
