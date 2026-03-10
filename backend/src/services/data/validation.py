"""
数据清洗和验证模块

提供数据质量检查、清洗和验证功能。
"""

from typing import List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import logging

from .base import StockPriceData, StockInfo, DataValidationError

logger = logging.getLogger(__name__)


class DataValidator:
    """
    数据验证器

    验证数据是否符合业务规则和质量标准。
    """

    # 价格验证范围（避免异常数据）
    MIN_PRICE = Decimal("0.01")  # 最小价格（1分）
    MAX_PRICE = Decimal("1000000")  # 最大价格（100万）

    # 成交量验证范围
    MIN_VOLUME = 0
    MAX_VOLUME = 10**12  # 最大成交量（1万亿）

    # 日期验证范围
    MIN_DATE = date(1990, 1, 1)  # A股最早上市日期
    MAX_DATE = date.today()

    @classmethod
    def validate_stock_price(cls, price_data: StockPriceData) -> Tuple[bool, Optional[str]]:
        """
        验证股票价格数据

        Args:
            price_data: 股票价格数据

        Returns:
            (是否有效, 错误信息)
        """
        # 验证股票代码
        if not price_data.symbol or len(price_data.symbol) > 20:
            return False, "股票代码无效"

        # 验证时间戳
        if not isinstance(price_data.timestamp, datetime):
            return False, "时间戳格式错误"

        price_date = price_data.timestamp.date()
        if price_date < cls.MIN_DATE or price_date > cls.MAX_DATE:
            return False, f"日期超出范围 ({price_date})"

        # 验证价格
        for field_name, value in [
            ("open", price_data.open),
            ("high", price_data.high),
            ("low", price_data.low),
            ("close", price_data.close)
        ]:
            if not isinstance(value, Decimal):
                try:
                    Decimal(str(value))
                except (InvalidOperation, ValueError):
                    return False, f"{field_name} 价格类型错误"

            if value < cls.MIN_PRICE or value > cls.MAX_PRICE:
                return False, f"{field_name} 价格超出范围 ({value})"

        # 验证价格逻辑关系
        if price_data.high < price_data.low:
            return False, f"最高价不能低于最低价 (high={price_data.high}, low={price_data.low})"

        if price_data.close < 0 or price_data.open < 0:
            return False, "价格不能为负数"

        # 验证 OHLC 逻辑
        if not (price_data.low <= price_data.close <= price_data.high):
            return False, f"收盘价不在最低-最高价范围内 (close={price_data.close}, low={price_data.low}, high={price_data.high})"

        if not (price_data.low <= price_data.open <= price_data.high):
            return False, f"开盘价不在最低-最高价范围内 (open={price_data.open}, low={price_data.low}, high={price_data.high})"

        # 验证成交量
        if not isinstance(price_data.volume, int):
            return False, "成交量类型错误"

        if price_data.volume < cls.MIN_VOLUME or price_data.volume > cls.MAX_VOLUME:
            return False, f"成交量超出范围 ({price_data.volume})"

        # 验证成交额（如果提供）
        if price_data.amount is not None:
            if not isinstance(price_data.amount, Decimal):
                return False, "成交额类型错误"

            if price_data.amount < 0:
                return False, "成交额不能为负数"

        return True, None

    @classmethod
    def validate_stock_info(cls, stock_info: StockInfo) -> Tuple[bool, Optional[str]]:
        """
        验证股票基本信息

        Args:
            stock_info: 股票基本信息

        Returns:
            (是否有效, 错误信息)
        """
        # 验证股票代码
        if not stock_info.symbol or len(stock_info.symbol) > 20:
            return False, "股票代码无效"

        # 验证股票名称
        if not stock_info.name or len(stock_info.name) > 100:
            return False, "股票名称无效"

        # 验证市场代码
        valid_markets = ["SHSE", "SZSE", "HKEX", "US", "TSX", "LSE", "FSE", "EPA"]
        if stock_info.market and stock_info.market not in valid_markets:
            return False, f"无效的市场代码 ({stock_info.market})"

        # 验证上市日期
        if stock_info.list_date:
            if stock_info.list_date < cls.MIN_DATE or stock_info.list_date > cls.MAX_DATE:
                return False, f"上市日期超出范围 ({stock_info.list_date})"

        return True, None


class DataCleaner:
    """
    数据清洗器

    清洗和标准化数据。
    """

    @classmethod
    def clean_stock_prices(cls, prices: List[StockPriceData]) -> List[StockPriceData]:
        """
        清洗股票价格数据列表

        Args:
            prices: 原始价格数据列表

        Returns:
            清洗后的价格数据列表
        """
        cleaned_prices = []
        validator = DataValidator()

        for price in prices:
            # 验证数据
            is_valid, error_msg = validator.validate_stock_price(price)

            if not is_valid:
                logger.debug(f"清洗无效数据: {price.symbol} - {error_msg}")
                continue

            # 清洗数据
            try:
                cleaned_price = cls._clean_price_data(price)
                cleaned_prices.append(cleaned_price)
            except Exception as e:
                logger.warning(f"清洗 {price.symbol} 数据失败: {e}")
                continue

        logger.info(f"数据清洗完成: 原始 {len(prices)} 条 → 有效 {len(cleaned_prices)} 条")
        return cleaned_prices

    @classmethod
    def _clean_price_data(cls, price: StockPriceData) -> StockPriceData:
        """
        清洗单条价格数据

        Args:
            price: 原始价格数据

        Returns:
            清洗后的价格数据
        """
        # 标准化股票代码
        symbol = price.symbol.upper().strip()

        # 确保价格精度（最多8位小数）
        def quantize_price(value: Decimal) -> Decimal:
            return value.quantize(Decimal("0.00000001"))

        # 清洗时间戳（去除时区信息，统一使用 UTC）
        timestamp = price.timestamp
        if timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)

        # 构造清洗后的数据
        cleaned_price = StockPriceData(
            symbol=symbol,
            timestamp=timestamp,
            open=quantize_price(price.open),
            high=quantize_price(price.high),
            low=quantize_price(price.low),
            close=quantize_price(price.close),
            volume=price.volume,
            amount=price.amount.quantize(Decimal("0.00000001")) if price.amount else None
        )

        return cleaned_price

    @classmethod
    def deduplicate_prices(cls, prices: List[StockPriceData]) -> List[StockPriceData]:
        """
        去重价格数据（基于 symbol + timestamp）

        Args:
            prices: 价格数据列表

        Returns:
            去重后的价格数据列表
        """
        seen = set()
        unique_prices = []

        for price in prices:
            key = (price.symbol, price.timestamp)

            if key not in seen:
                seen.add(key)
                unique_prices.append(price)
            else:
                logger.debug(f"发现重复数据: {price.symbol} - {price.timestamp}")

        logger.info(f"去重完成: 原始 {len(prices)} 条 → 去重 {len(unique_prices)} 条")
        return unique_prices

    @classmethod
    def sort_prices(cls, prices: List[StockPriceData]) -> List[StockPriceData]:
        """
        按时间戳排序价格数据

        Args:
            prices: 价格数据列表

        Returns:
            排序后的价格数据列表
        """
        return sorted(prices, key=lambda p: (p.symbol, p.timestamp))


class DataPipeline:
    """
    数据处理管道

    整合验证、清洗、去重、排序等功能。
    """

    def __init__(self):
        """初始化数据管道"""
        self.validator = DataValidator()
        self.cleaner = DataCleaner()

    def process_stock_prices(
        self,
        prices: List[StockPriceData],
        validate: bool = True,
        clean: bool = True,
        deduplicate: bool = True,
        sort: bool = True
    ) -> List[StockPriceData]:
        """
        处理股票价格数据

        Args:
            prices: 原始价格数据列表
            validate: 是否验证数据
            clean: 是否清洗数据
            deduplicate: 是否去重
            sort: 是否排序

        Returns:
            处理后的价格数据列表
        """
        logger.info(f"开始处理数据: {len(prices)} 条")
        processed_prices = prices

        # 1. 验证数据
        if validate:
            valid_prices = []
            for price in processed_prices:
                is_valid, error_msg = self.validator.validate_stock_price(price)
                if is_valid:
                    valid_prices.append(price)
                else:
                    logger.debug(f"验证失败: {price.symbol} - {error_msg}")

            logger.info(f"验证完成: {len(processed_prices)} → {len(valid_prices)} 条有效")
            processed_prices = valid_prices

        # 2. 清洗数据
        if clean:
            processed_prices = self.cleaner.clean_stock_prices(processed_prices)

        # 3. 去重
        if deduplicate:
            processed_prices = self.cleaner.deduplicate_prices(processed_prices)

        # 4. 排序
        if sort:
            processed_prices = self.cleaner.sort_prices(processed_prices)

        logger.info(f"数据处理完成: 最终 {len(processed_prices)} 条")
        return processed_prices

    def get_data_quality_report(self, original: List[StockPriceData], processed: List[StockPriceData]) -> dict:
        """
        生成数据质量报告

        Args:
            original: 原始数据
            processed: 处理后数据

        Returns:
            数据质量报告
        """
        original_count = len(original)
        processed_count = len(processed)
        removed_count = original_count - processed_count
        quality_rate = (processed_count / original_count * 100) if original_count > 0 else 0

        return {
            "original_count": original_count,
            "processed_count": processed_count,
            "removed_count": removed_count,
            "quality_rate": round(quality_rate, 2),
            "status": "PASS" if quality_rate >= 95 else "WARNING" if quality_rate >= 80 else "FAIL"
        }


# ==============================================
# 便捷函数
# ==============================================

def validate_and_clean_prices(prices: List[StockPriceData]) -> List[StockPriceData]:
    """
    验证并清洗价格数据

    Args:
        prices: 原始价格数据列表

    Returns:
        清洗后的价格数据列表
    """
    pipeline = DataPipeline()
    return pipeline.process_stock_prices(prices)
