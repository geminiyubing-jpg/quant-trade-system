"""
数据入库服务

将清洗后的数据高效写入 TimescaleDB。
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from ...core.database import get_db_context
from ...models.stock import Stock, StockPrice
from .base import StockPriceData, StockInfo
from .validation import DataValidator

logger = logging.getLogger(__name__)


class DataStorageService:
    """
    数据入库服务

    负责将数据写入 TimescaleDB，支持批量插入和性能优化。
    """

    def __init__(self, db: Session):
        """
        初始化数据入库服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.validator = DataValidator()

    def save_stock_info(self, stock_info: StockInfo) -> Optional[Stock]:
        """
        保存股票基本信息

        Args:
            stock_info: 股票基本信息

        Returns:
            保存的股票模型或 None
        """
        try:
            # 验证数据
            is_valid, error_msg = self.validator.validate_stock_info(stock_info)
            if not is_valid:
                logger.error(f"股票信息验证失败: {error_msg}")
                return None

            # 检查是否已存在
            existing_stock = self.db.query(Stock).filter(
                Stock.symbol == stock_info.symbol
            ).first()

            if existing_stock:
                # 更新现有记录
                existing_stock.name = stock_info.name
                existing_stock.sector = stock_info.sector
                existing_stock.industry = stock_info.industry
                existing_stock.market = stock_info.market
                existing_stock.list_date = stock_info.list_date
                self.db.commit()
                logger.info(f"更新股票信息: {stock_info.symbol}")
                return existing_stock
            else:
                # 创建新记录
                new_stock = Stock(
                    symbol=stock_info.symbol,
                    name=stock_info.name,
                    sector=stock_info.sector,
                    industry=stock_info.industry,
                    market=stock_info.market,
                    list_date=stock_info.list_date,
                    is_active=True
                )
                self.db.add(new_stock)
                self.db.commit()
                logger.info(f"创建股票信息: {stock_info.symbol}")
                return new_stock

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存股票信息失败 ({stock_info.symbol}): {e}")
            return None

    def save_stock_prices_bulk(
        self,
        prices: List[StockPriceData],
        batch_size: int = 1000
    ) -> int:
        """
        批量保存股票价格数据（性能优化）

        Args:
            prices: 价格数据列表
            batch_size: 批量大小

        Returns:
            成功插入的记录数
        """
        if not prices:
            return 0

        inserted_count = 0

        try:
            # 分批处理
            for i in range(0, len(prices), batch_size):
                batch = prices[i:i + batch_size]

                # 使用批量插入（性能优化）
                inserted = self._insert_batch(batch)
                inserted_count += inserted

            logger.info(f"批量插入完成: {inserted_count}/{len(prices)} 条记录")
            return inserted_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"批量插入失败: {e}")
            return inserted_count

    def _insert_batch(self, batch: List[StockPriceData]) -> int:
        """
        插入一批数据

        Args:
            batch: 一批价格数据

        Returns:
            成功插入的记录数
        """
        inserted_count = 0

        for price_data in batch:
            try:
                # 检查是否已存在（基于 symbol + timestamp）
                existing = self.db.query(StockPrice).filter(
                    StockPrice.symbol == price_data.symbol,
                    StockPrice.timestamp == price_data.timestamp
                ).first()

                if existing:
                    # 更新现有记录
                    existing.price_open = price_data.open
                    existing.price_high = price_data.high
                    existing.price_low = price_data.low
                    existing.price_close = price_data.close
                    existing.volume = price_data.volume
                    existing.amount = price_data.amount
                else:
                    # 插入新记录
                    new_price = StockPrice(
                        symbol=price_data.symbol,
                        price_open=price_data.open,
                        price_high=price_data.high,
                        price_low=price_data.low,
                        price_close=price_data.close,
                        volume=price_data.volume,
                        amount=price_data.amount,
                        timestamp=price_data.timestamp
                    )
                    self.db.add(new_price)
                    inserted_count += 1

            except Exception as e:
                logger.warning(f"插入数据失败 ({price_data.symbol}): {e}")
                continue

        # 提交事务
        self.db.commit()
        return inserted_count

    def save_stock_prices_upsert(
        self,
        prices: List[StockPriceData]
    ) -> int:
        """
        保存或更新价格数据（使用 ON CONFLICT）

        Args:
            prices: 价格数据列表

        Returns:
            成功插入/更新的记录数
        """
        if not prices:
            return 0

        try:
            # 使用原生 SQL 的 UPSERT 语句（性能最优）
            # 注意：TimescaleDB 支持 PostgreSQL 的 ON CONFLICT 语法
            success_count = 0

            for price_data in prices:
                try:
                    # 构造 UPSERT SQL
                    sql = text("""
                        INSERT INTO stock_prices (
                            symbol, price_close, price_open, price_high, price_low,
                            volume, amount, timestamp, created_at
                        ) VALUES (
                            :symbol, :close, :open, :high, :low,
                            :volume, :amount, :timestamp, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (symbol, timestamp) DO UPDATE SET
                            price_close = EXCLUDED.price_close,
                            price_open = EXCLUDED.price_open,
                            price_high = EXCLUDED.price_high,
                            price_low = EXCLUDED.price_low,
                            volume = EXCLUDED.volume,
                            amount = EXCLUDED.amount,
                            updated_at = CURRENT_TIMESTAMP
                    """)

                    self.db.execute(sql, {
                        "symbol": price_data.symbol,
                        "close": str(price_data.close),
                        "open": str(price_data.open),
                        "high": str(price_data.high),
                        "low": str(price_data.low),
                        "volume": price_data.volume,
                        "amount": str(price_data.amount) if price_data.amount else None,
                        "timestamp": price_data.timestamp
                    })

                    success_count += 1

                except Exception as e:
                    logger.warning(f"UPSERT 失败 ({price_data.symbol}): {e}")
                    continue

            self.db.commit()
            logger.info(f"UPSERT 完成: {success_count}/{len(prices)} 条记录")
            return success_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"UPSERT 批量操作失败: {e}")
            return 0

    def get_latest_timestamp(self, symbol: str) -> Optional[datetime]:
        """
        获取指定股票的最新时间戳

        Args:
            symbol: 股票代码

        Returns:
            最新时间戳或 None
        """
        try:
            latest = self.db.query(StockPrice).filter(
                StockPrice.symbol == symbol
            ).order_by(StockPrice.timestamp.desc()).first()

            if latest:
                return latest.timestamp
            return None

        except Exception as e:
            logger.error(f"查询最新时间戳失败 ({symbol}): {e}")
            return None

    def check_data_completeness(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        检查数据完整性

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据完整性报告
        """
        try:
            # 查询时间范围内的数据
            prices = self.db.query(StockPrice).filter(
                StockPrice.symbol == symbol,
                StockPrice.timestamp >= start_date,
                StockPrice.timestamp <= end_date
            ).all()

            total_days = (end_date - start_date).days + 1
            actual_days = len(prices)
            missing_days = total_days - actual_days
            completeness_rate = (actual_days / total_days * 100) if total_days > 0 else 0

            return {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "total_days": total_days,
                "actual_days": actual_days,
                "missing_days": missing_days,
                "completeness_rate": round(completeness_rate, 2),
                "status": "PASS" if completeness_rate >= 95 else "WARNING"
            }

        except Exception as e:
            logger.error(f"检查数据完整性失败 ({symbol}): {e}")
            return {
                "symbol": symbol,
                "status": "ERROR",
                "error": str(e)
            }

    def delete_old_data(
        self,
        symbol: str,
        before_date: datetime
    ) -> int:
        """
        删除指定日期之前的数据（数据清理）

        Args:
            symbol: 股票代码
            before_date: 删除此日期之前的数据

        Returns:
            删除的记录数
        """
        try:
            deleted = self.db.query(StockPrice).filter(
                StockPrice.symbol == symbol,
                StockPrice.timestamp < before_date
            ).delete()

            self.db.commit()
            logger.info(f"删除旧数据: {symbol} - {deleted} 条记录")
            return deleted

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除旧数据失败 ({symbol}): {e}")
            return 0


# ==============================================
# 便捷函数
# ==============================================

def save_prices_to_db(prices: List[StockPriceData]) -> int:
    """
    将价格数据保存到数据库（便捷函数）

    Args:
        prices: 价格数据列表

    Returns:
        成功保存的记录数
    """
    with get_db_context() as db:
        storage_service = DataStorageService(db)
        return storage_service.save_stock_prices_upsert(prices)
