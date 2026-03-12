"""
成交记录数据访问层
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ...models.trading_ext import Fill
from ...core.exceptions import NotFoundError
from ...core.logging import get_logger
from ...repositories.base import BaseRepository

logger = get_logger(__name__)


class FillRepository(BaseRepository[Fill, Fill]):
    """成交记录数据访问"""

    def get_by_order(self, order_id: str) -> List[Fill]:
        """获取订单的所有成交记录"""
        return self.db.query(Fill).filter(
            Fill.order_id == order_id
        ).order_by(desc(Fill.filled_at)).all()

    def get_by_user(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Fill]:
        """获取用户的成交记录"""
        query = self.db.query(Fill).filter(
            Fill.user_id == user_id
        )

        if start_date:
            query = query.filter(Fill.filled_at >= start_date)
        if end_date:
            query = query.filter(Fill.filled_at <= end_date)

        return query.order_by(desc(Fill.filled_at)).limit(limit).all()

    def get_by_symbol(
        self,
        symbol: str,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Fill]:
        """获取股票的成交记录"""
        query = self.db.query(Fill).filter(
            Fill.symbol == symbol
        )

        if user_id:
            query = query.filter(Fill.user_id == user_id)

        return query.order_by(desc(Fill.filled_at)).limit(limit).all()

    def get_daily_fills(
        self,
        user_id: str,
        trade_date: datetime
    ) -> List[Fill]:
        """获取用户某日的所有成交记录"""
        start = trade_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = trade_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        return self.db.query(Fill).filter(
            Fill.user_id == user_id,
            Fill.filled_at >= start,
            Fill.filled_at <= end
        ).order_by(desc(Fill.filled_at)).all()

    def create_fill(self, fill: Fill) -> Fill:
        """创建成交记录"""
        self.db.add(fill)
        self.db.commit()
        self.db.refresh(fill)
        return fill

    def get_fill_stats(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取成交统计"""
        query = self.db.query(Fill).filter(Fill.user_id == user_id)

        if start_date:
            query = query.filter(Fill.filled_at >= start_date)
        if end_date:
            query = query.filter(Fill.filled_at <= end_date)

        fills = query.all()

        if not fills:
            return {
                'total_count': 0,
                'buy_count': 0,
                'sell_count': 0,
                'total_volume': 0,
                'total_amount': Decimal('0'),
                'total_commission': Decimal('0'),
                'realized_pnl': Decimal('0'),
            }

        buy_count = sum(1 for f in fills if f.side == 'BUY')
        sell_count = sum(1 for f in fills if f.side == 'SELL')
        total_volume = sum(f.filled_quantity for f in fills)
        total_amount = sum(f.filled_quantity * f.avg_price for f in fills)
        total_commission = sum(f.commission or Decimal('0') for f in fills)
        realized_pnl = sum(f.realized_pnl or Decimal('0') for f in fills)

        return {
            'total_count': len(fills),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'total_volume': total_volume,
            'total_amount': total_amount,
            'total_commission': total_commission,
            'realized_pnl': realized_pnl,
        }
