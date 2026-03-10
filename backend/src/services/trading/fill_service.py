"""
成交记录和交易日历服务

提供成交管理、交易日历和交易统计功能。
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from ...models import Fill, TradingCalendar, DailyTradeStats, Order


class FillService:
    """成交服务 - 处理成交记录和交易日历"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 成交管理 ====================

    def record_fill(
        self,
        order_id: str,
        user_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal,
        execution_mode: str = "PAPER",
        strategy_id: Optional[str] = None,
        fill_id: Optional[str] = None,
        commission: Decimal = Decimal("0"),
        stamp_duty: Decimal = Decimal("0"),
        transfer_fee: Decimal = Decimal("0"),
        fill_time: Optional[datetime] = None
    ) -> Fill:
        """
        记录成交

        Args:
            order_id: 订单ID
            user_id: 用户ID
            symbol: 股票代码
            side: 买卖方向
            quantity: 成交数量
            price: 成交价格
            execution_mode: 执行模式
            strategy_id: 策略ID
            fill_id: 交易所成交ID
            commission: 佣金
            stamp_duty: 印花税
            transfer_fee: 过户费
            fill_time: 成交时间

        Returns:
            Fill: 成交记录
        """
        fill_amount = price * quantity
        total_fees = commission + stamp_duty + transfer_fee

        fill = Fill(
            order_id=order_id,
            user_id=user_id,
            strategy_id=strategy_id,
            symbol=symbol,
            execution_mode=execution_mode,
            fill_id=fill_id or f"FILL-{uuid.uuid4().hex[:12].upper()}",
            side=side,
            quantity=quantity,
            price=price,
            fill_amount=fill_amount,
            commission=commission,
            stamp_duty=stamp_duty,
            transfer_fee=transfer_fee,
            total_fees=total_fees,
            fill_time=fill_time or datetime.utcnow()
        )

        self.db.add(fill)
        self.db.commit()
        self.db.refresh(fill)

        # 更新日统计
        self._update_daily_stats(fill)

        return fill

    def get_fill(self, fill_id: str) -> Optional[Fill]:
        """获取成交记录"""
        return self.db.query(Fill).filter(Fill.id == fill_id).first()

    def get_fills_by_order(self, order_id: str) -> List[Fill]:
        """获取订单的所有成交"""
        return self.db.query(Fill).filter(
            Fill.order_id == order_id
        ).order_by(Fill.fill_time).all()

    def get_fills_by_user(
        self,
        user_id: str,
        execution_mode: Optional[str] = None,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Fill]:
        """获取用户的成交记录"""
        query = self.db.query(Fill).filter(Fill.user_id == user_id)

        if execution_mode:
            query = query.filter(Fill.execution_mode == execution_mode)
        if symbol:
            query = query.filter(Fill.symbol == symbol)
        if start_time:
            query = query.filter(Fill.fill_time >= start_time)
        if end_time:
            query = query.filter(Fill.fill_time <= end_time)

        return query.order_by(desc(Fill.fill_time)).limit(limit).all()

    def get_fills_by_strategy(
        self,
        strategy_id: str,
        start_time: Optional[datetime] = None
    ) -> List[Fill]:
        """获取策略的成交记录"""
        query = self.db.query(Fill).filter(Fill.strategy_id == strategy_id)

        if start_time:
            query = query.filter(Fill.fill_time >= start_time)

        return query.order_by(Fill.fill_time).all()

    # ==================== 交易日历 ====================

    def is_trading_day(self, check_date: date, market: str = "A-SHARE") -> bool:
        """判断是否为交易日"""
        calendar = self.db.query(TradingCalendar).filter(
            and_(
                TradingCalendar.trade_date == check_date,
                TradingCalendar.market == market
            )
        ).first()

        return calendar.is_trading_day if calendar else False

    def get_trading_days(
        self,
        start_date: date,
        end_date: date,
        market: str = "A-SHARE"
    ) -> List[date]:
        """获取日期范围内的交易日列表"""
        calendars = self.db.query(TradingCalendar).filter(
            and_(
                TradingCalendar.trade_date >= start_date,
                TradingCalendar.trade_date <= end_date,
                TradingCalendar.market == market,
                TradingCalendar.is_trading_day == True
            )
        ).order_by(TradingCalendar.trade_date).all()

        return [c.trade_date for c in calendars]

    def get_next_trading_day(self, check_date: date, market: str = "A-SHARE") -> Optional[date]:
        """获取下一个交易日"""
        calendar = self.db.query(TradingCalendar).filter(
            and_(
                TradingCalendar.trade_date > check_date,
                TradingCalendar.market == market,
                TradingCalendar.is_trading_day == True
            )
        ).order_by(TradingCalendar.trade_date).first()

        return calendar.trade_date if calendar else None

    def get_previous_trading_day(self, check_date: date, market: str = "A-SHARE") -> Optional[date]:
        """获取上一个交易日"""
        calendar = self.db.query(TradingCalendar).filter(
            and_(
                TradingCalendar.trade_date < check_date,
                TradingCalendar.market == market,
                TradingCalendar.is_trading_day == True
            )
        ).order_by(desc(TradingCalendar.trade_date)).first()

        return calendar.trade_date if calendar else None

    def get_trading_hours(
        self,
        check_date: date,
        market: str = "A-SHARE"
    ) -> Optional[Dict[str, Any]]:
        """获取交易时间"""
        calendar = self.db.query(TradingCalendar).filter(
            and_(
                TradingCalendar.trade_date == check_date,
                TradingCalendar.market == market
            )
        ).first()

        if not calendar:
            return None

        return {
            'is_trading_day': calendar.is_trading_day,
            'is_half_day': calendar.is_half_day,
            'open_time': calendar.open_time.isoformat() if calendar.open_time else None,
            'close_time': calendar.close_time.isoformat() if calendar.close_time else None,
            'lunch_start': calendar.lunch_start.isoformat() if calendar.lunch_start else None,
            'lunch_end': calendar.lunch_end.isoformat() if calendar.lunch_end else None,
        }

    def init_trading_calendar(
        self,
        year: int,
        market: str = "A-SHARE"
    ) -> int:
        """
        初始化交易日历（简化实现，实际应从外部数据源获取）

        Args:
            year: 年份
            market: 市场

        Returns:
            int: 插入的记录数
        """
        from datetime import timedelta

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        current_date = start_date
        count = 0

        while current_date <= end_date:
            # 排除周末
            is_trading = current_date.weekday() < 5

            # 检查是否已存在
            existing = self.db.query(TradingCalendar).filter(
                and_(
                    TradingCalendar.trade_date == current_date,
                    TradingCalendar.market == market
                )
            ).first()

            if not existing:
                calendar = TradingCalendar(
                    trade_date=current_date,
                    market=market,
                    is_trading_day=is_trading,
                    open_time=datetime.strptime("09:30", "%H:%M").time() if is_trading else None,
                    close_time=datetime.strptime("15:00", "%H:%M").time() if is_trading else None,
                    lunch_start=datetime.strptime("11:30", "%H:%M").time() if is_trading else None,
                    lunch_end=datetime.strptime("13:00", "%H:%M").time() if is_trading else None,
                    is_month_end=current_date.day >= 28,
                    is_quarter_end=current_date.month in [3, 6, 9, 12] and current_date.day >= 28,
                    is_year_end=current_date.month == 12 and current_date.day >= 28
                )
                self.db.add(calendar)
                count += 1

            current_date += timedelta(days=1)

        self.db.commit()
        return count

    # ==================== 交易统计 ====================

    def calculate_daily_stats(
        self,
        user_id: str,
        stats_date: date,
        execution_mode: str
    ) -> DailyTradeStats:
        """
        计算日交易统计

        Args:
            user_id: 用户ID
            stats_date: 统计日期
            execution_mode: 执行模式

        Returns:
            DailyTradeStats: 统计结果
        """
        # 查询当日成交
        start_time = datetime.combine(stats_date, datetime.min.time())
        end_time = datetime.combine(stats_date, datetime.max.time())

        fills = self.db.query(Fill).filter(
            and_(
                Fill.user_id == user_id,
                Fill.execution_mode == execution_mode,
                Fill.fill_time >= start_time,
                Fill.fill_time <= end_time
            )
        ).all()

        # 计算统计
        buy_fills = [f for f in fills if f.side == 'BUY']
        sell_fills = [f for f in fills if f.side == 'SELL']

        stats = DailyTradeStats(
            user_id=user_id,
            trade_date=stats_date,
            execution_mode=execution_mode,
            filled_orders=len(set(f.order_id for f in fills)),
            buy_count=len(buy_fills),
            sell_count=len(sell_fills),
            buy_volume=sum(f.quantity for f in buy_fills),
            sell_volume=sum(f.quantity for f in sell_fills),
            buy_amount=sum(f.fill_amount for f in buy_fills) if buy_fills else Decimal("0"),
            sell_amount=sum(f.fill_amount for f in sell_fills) if sell_fills else Decimal("0"),
            total_commission=sum(f.commission for f in fills),
            total_stamp_duty=sum(f.stamp_duty for f in fills),
            total_transfer_fee=sum(f.transfer_fee for f in fills),
            total_fees=sum(f.total_fees for f in fills)
        )

        # 检查是否已存在
        existing = self.db.query(DailyTradeStats).filter(
            and_(
                DailyTradeStats.user_id == user_id,
                DailyTradeStats.trade_date == stats_date,
                DailyTradeStats.execution_mode == execution_mode
            )
        ).first()

        if existing:
            # 更新
            for key, value in stats.to_dict().items():
                if hasattr(existing, key) and key not in ['id', 'created_at']:
                    setattr(existing, key, value)
            stats = existing
        else:
            self.db.add(stats)

        self.db.commit()
        self.db.refresh(stats)
        return stats

    def get_trade_stats(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        execution_mode: Optional[str] = None
    ) -> List[DailyTradeStats]:
        """获取交易统计"""
        query = self.db.query(DailyTradeStats).filter(
            and_(
                DailyTradeStats.user_id == user_id,
                DailyTradeStats.trade_date >= start_date,
                DailyTradeStats.trade_date <= end_date
            )
        )

        if execution_mode:
            query = query.filter(DailyTradeStats.execution_mode == execution_mode)

        return query.order_by(DailyTradeStats.trade_date).all()

    def get_trade_summary(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        execution_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取交易汇总"""
        stats = self.get_trade_stats(user_id, start_date, end_date, execution_mode)

        if not stats:
            return {
                'total_trades': 0,
                'total_buy_amount': 0,
                'total_sell_amount': 0,
                'total_fees': 0,
                'total_realized_pnl': 0
            }

        return {
            'total_trades': sum(s.filled_orders for s in stats),
            'total_buy_count': sum(s.buy_count for s in stats),
            'total_sell_count': sum(s.sell_count for s in stats),
            'total_buy_amount': float(sum(s.buy_amount for s in stats)),
            'total_sell_amount': float(sum(s.sell_amount for s in stats)),
            'total_fees': float(sum(s.total_fees for s in stats)),
            'total_realized_pnl': float(sum(s.realized_pnl for s in stats)),
            'trading_days': len(stats)
        }

    # ==================== 辅助方法 ====================

    def _update_daily_stats(self, fill: Fill) -> None:
        """更新日统计"""
        stats_date = fill.fill_time.date()
        try:
            self.calculate_daily_stats(
                user_id=str(fill.user_id),
                stats_date=stats_date,
                execution_mode=fill.execution_mode
            )
        except Exception as e:
            # 记录但不影响主流程
            print(f"Failed to update daily stats: {e}")
