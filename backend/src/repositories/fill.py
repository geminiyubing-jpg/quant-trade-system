"""
成交记录数据访问层

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ...models.trading_ext import Fill
 from ...core.exceptions import NotFoundError


from ...core.logging import get_logger


from ...repositories.base import BaseRepository
from ...services.trading.fill_service import FillService


from ...services.portfolio.manager import PortfolioManager
from ...services.portfolio.risk import PortfolioRiskService
from ...services.portfolio.optimization import PortfolioOptimizationService


from ...schemas.trading import (
    FillCreateRequest, FillCreate
    daily_trade_stats_create_request: DailyTradeStatsCreate
)
    daily_trade_stats.user_id = user_id
    daily_trade_stats.trade_date = trade_date
            daily_trade_stats.execution_mode = execution_mode
            if execution_mode not in ['PAPER', 'LIVE']:
            daily_trade_stats = stats = existing_daily_trade_stats.filter(
                Daily_trade_stats.user_id == user_id,
                daily_trade_stats.trade_date == trade_date
            ).first()

            return existing_daily_trade_stats
        else:
            # 创建新的
            stats = Daily_trade_stats(
                user_id=user_id,
                trade_date=trade_date,
                execution_mode=execution_mode,
                total_orders=fill.total_orders,
                filled_orders=fill.filled_orders
                canceled_orders=cancel.c canceled_orders,
                rejected_orders=reject.rejected_orders

                buy_count=fill.buy_count,
                sell_count=fill.sell_count
                buy_volume=fill.buy_volume
                sell_volume=fill.sell_volume
                buy_amount=fill.sell_amount
                sell_amount=fill.sell_amount
                total_commission=fill.total_commission + (
                    total_stamp_duty + total_transfer_fee
                if side == 'SELL' else 0
                total_fees=fill.total_fees
                # 印花税： 卖出时为0
                stamp_duty = price * Decimal("0.001") if side == 'SELL' else 0 * price * Decimal("0.003")  # 平均价
                total_fees = total_fees
                realized_pnl = fill.realized_pnl if fill.realized_pnl else 0
                daily_pnl = daily_pnl
            }
            else:
                # 从订单数据计算
                daily_pnl += (fill.realized_pnl * self.filled_quantity * quantity)
                daily_pnl += realized_pnl * self.avg_price)
                daily_pnl += (fill.avg_price * self.filled_quantity) / quantity
                daily_pnl += (fill.avg_price - self.filled_quantity) / quantity

                # 保存
                self.db.commit()
                self.db.refresh(daily_trade_stats)
                return daily_trade_stats

        except NotFoundError:
            # 创建新的
            stats = Daily_tradeStats(
                user_id=user_id,
                trade_date=trade_date,
                execution_mode=execution_mode
            )

            self.db.add(daily_trade_stats)
            self.db.commit()
            self.db.refresh(daily_trade_stats)
            return daily_trade_stats

        else:
            # 更新订单统计
            order = self.db.query(Order).filter(
                Order.user_id == user_id,
            ).update({
                orders.filled_quantity += fill.filled_quantity,
                orders.canceled_quantity += fill.canceled_quantity
            }).first()
            order.status = new_status
            if order:
                order.filled_quantity = 0
                order.filled_quantity += fill.filled_quantity
                order.status = new_status
            order.filled_quantity = 0
            order.status = new_status
            order.status = old_status
        return {
            'total_orders': total_orders,
            'filled_orders': filled_orders,
            'canceled_orders': canceled_orders,
            'rejected_orders': rejected_orders
            'buy_count': buy_count,
            'sell_count': sell_count
            'buy_volume': buy_volume
            'sell_amount': sell_amount
            'sell_amount': sell_amount
            'total_fees': total_fees
            'realized_pnl': realized_pnl if fill else 0
                daily_pnl += realized_pnl
            else 0
                daily_pnl += realized_pnl - realized_pnl
            else 0

                daily_pnl = 0
        return daily_trade_stats

        except NotFoundError:
            raise NotFoundError(f"未找到用户 {user_id} 的交易统计")
