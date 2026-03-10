"""
交易 Repository
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import BaseRepository
from ..models.trading import Order, Position


class OrderRepository(BaseRepository[Order, Order, Order]):
    """订单 Repository"""

    def get_user_orders(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        execution_mode: Optional[str] = None
    ) -> List[Order]:
        """
        获取用户订单列表

        双轨隔离：根据 user_id 和 execution_mode 过滤订单

        Args:
            db: 数据库会话
            user_id: 用户 ID
            skip: 跳过记录数
            limit: 返回记录数
            execution_mode: 执行模式（PAPER/LIVE）

        Returns:
            订单实例列表
        """
        query = db.query(Order).filter(Order.user_id == user_id)
        if execution_mode:
            query = query.filter(Order.execution_mode == execution_mode)
        return query.order_by(Order.create_time.desc()).offset(skip).limit(limit).all()

    def get_pending_orders(
        self,
        db: Session,
        *,
        user_id: str,
        execution_mode: str
    ) -> List[Order]:
        """
        获取用户待成交订单

        双轨隔离：根据 user_id 和 execution_mode 过滤订单

        Args:
            db: 数据库会话
            user_id: 用户 ID
            execution_mode: 执行模式（PAPER/LIVE）

        Returns:
            订单实例列表
        """
        return db.query(Order).filter(
            and_(
                Order.user_id == user_id,
                Order.execution_mode == execution_mode,
                Order.status == 'PENDING'
            )
        ).all()

    def get_orders_by_symbol(
        self,
        db: Session,
        *,
        user_id: str,
        symbol: str,
        execution_mode: Optional[str] = None
    ) -> List[Order]:
        """
        获取用户某股票的订单列表

        双轨隔离：根据 user_id 和 execution_mode 过滤订单

        Args:
            db: 数据库会话
            user_id: 用户 ID
            symbol: 股票代码
            execution_mode: 执行模式（PAPER/LIVE）

        Returns:
            订单实例列表
        """
        query = db.query(Order).filter(
            and_(Order.user_id == user_id, Order.ts_code == symbol)
        )
        if execution_mode:
            query = query.filter(Order.execution_mode == execution_mode)
        return query.order_by(Order.create_time.desc()).all()


class PositionRepository(BaseRepository[Position, Position, Position]):
    """持仓 Repository - 适配数据库实际结构"""

    def get_user_positions(
        self,
        db: Session,
        *,
        user_id: str,
        execution_mode: str = 'PAPER',
        skip: int = 0,
        limit: int = 100
    ) -> List[Position]:
        """
        获取用户持仓列表

        双轨隔离：根据 user_id 和 execution_mode 过滤持仓

        Args:
            db: 数据库会话
            user_id: 用户 ID
            execution_mode: 执行模式（PAPER/LIVE）
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            持仓实例列表
        """
        return db.query(Position).filter(
            and_(
                Position.user_id == user_id,
                Position.execution_mode == execution_mode,
                Position.quantity != 0
            )
        ).offset(skip).limit(limit).all()

    def get_position_by_symbol(
        self,
        db: Session,
        *,
        user_id: str,
        symbol: str,
        execution_mode: str = 'PAPER'
    ) -> Optional[Position]:
        """
        获取用户某股票的持仓

        双轨隔离：根据 user_id 和 execution_mode 过滤持仓

        Args:
            db: 数据库会话
            user_id: 用户 ID
            symbol: 股票代码
            execution_mode: 执行模式（PAPER/LIVE）

        Returns:
            持仓实例或 None
        """
        return db.query(Position).filter(
            and_(
                Position.user_id == user_id,
                Position.stock_symbol == symbol,
                Position.execution_mode == execution_mode
            )
        ).first()

    def get_positions_by_strategy(
        self,
        db: Session,
        *,
        user_id: str,
        strategy_id: str,
        execution_mode: str = 'PAPER'
    ) -> List[Position]:
        """
        获取用户某策略的持仓列表

        双轨隔离：根据 user_id 和 execution_mode 过滤持仓

        Args:
            db: 数据库会话
            user_id: 用户 ID
            strategy_id: 策略 ID
            execution_mode: 执行模式（PAPER/LIVE）

        Returns:
            持仓实例列表
        """
        return db.query(Position).filter(
            and_(
                Position.user_id == user_id,
                Position.strategy_id == strategy_id,
                Position.execution_mode == execution_mode,
                Position.quantity != 0
            )
        ).all()
