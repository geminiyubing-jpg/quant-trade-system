"""
ETL（数据提取、转换、加载）测试

测试数据获取、清洗、验证和入库流程。
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from src.services.data.base import StockPriceData, StockInfo
from src.services.data.validation import DataValidator, DataCleaner, DataPipeline
from src.services.data.yahoo_finance import YahooFinanceDataSource
from src.services.data.akshare import AkShareDataSource


# ==============================================
# 数据验证测试
# ==============================================

class TestDataValidator:
    """数据验证器测试"""

    def test_validate_valid_stock_price(self):
        """测试验证有效的股票价格数据"""
        price_data = StockPriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("152.00"),
            volume=1000000,
            amount=Decimal("152000000")
        )

        validator = DataValidator()
        is_valid, error_msg = validator.validate_stock_price(price_data)

        assert is_valid is True
        assert error_msg is None

    def test_validate_invalid_price_range(self):
        """测试验证无效的价格范围"""
        price_data = StockPriceData(
            symbol="TEST",
            timestamp=datetime.now(),
            open=Decimal("0.001"),  # 低于最小价格
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("152.00"),
            volume=1000000,
            amount=Decimal("152000000")
        )

        validator = DataValidator()
        is_valid, error_msg = validator.validate_stock_price(price_data)

        assert is_valid is False
        assert "价格超出范围" in error_msg

    def test_validate_invalid_ohlc_relation(self):
        """测试验证无效的 OHLC 关系"""
        price_data = StockPriceData(
            symbol="TEST",
            timestamp=datetime.now(),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("160.00"),  # 收盘价高于最高价
            volume=1000000,
            amount=Decimal("152000000")
        )

        validator = DataValidator()
        is_valid, error_msg = validator.validate_stock_price(price_data)

        assert is_valid is False
        assert "收盘价不在最低-最高价范围内" in error_msg


# ==============================================
# 数据清洗测试
# ==============================================

class TestDataCleaner:
    """数据清洗器测试"""

    def test_clean_stock_prices(self):
        """测试清洗股票价格数据"""
        # 混合有效和无效数据
        prices = [
            # 有效数据
            StockPriceData(
                symbol="AAPL",
                timestamp=datetime.now(),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
            # 无效数据（价格为负）
            StockPriceData(
                symbol="TEST",
                timestamp=datetime.now(),
                open=Decimal("-1.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
        ]

        cleaner = DataCleaner()
        cleaned_prices = cleaner.clean_stock_prices(prices)

        assert len(cleaned_prices) == 1  # 只保留有效数据
        assert cleaned_prices[0].symbol == "AAPL"

    def test_deduplicate_prices(self):
        """测试去重价格数据"""
        now = datetime.now()
        prices = [
            StockPriceData(
                symbol="AAPL",
                timestamp=now,
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
            # 重复数据
            StockPriceData(
                symbol="AAPL",
                timestamp=now,
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
        ]

        cleaner = DataCleaner()
        unique_prices = cleaner.deduplicate_prices(prices)

        assert len(unique_prices) == 1  # 去重后只有 1 条

    def test_sort_prices(self):
        """测试排序价格数据"""
        prices = [
            StockPriceData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 3),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
            StockPriceData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 1),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
        ]

        cleaner = DataCleaner()
        sorted_prices = cleaner.sort_prices(prices)

        assert sorted_prices[0].timestamp == datetime(2024, 1, 1)
        assert sorted_prices[1].timestamp == datetime(2024, 1, 3)


# ==============================================
# 数据处理管道测试
# ==============================================

class TestDataPipeline:
    """数据处理管道测试"""

    def test_process_stock_prices(self):
        """测试完整的股票价格处理流程"""
        # 原始数据（包含有效和无效数据）
        prices = [
            # 有效数据
            StockPriceData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 1),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
            # 无效数据（价格为负）
            StockPriceData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 2),
                open=Decimal("-1.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
            # 有效数据
            StockPriceData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 3),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
        ]

        pipeline = DataPipeline()
        processed_prices = pipeline.process_stock_prices(prices)

        # 验证结果
        assert len(processed_prices) == 2  # 只有 2 条有效数据
        assert processed_prices[0].timestamp == datetime(2024, 1, 1)
        assert processed_prices[1].timestamp == datetime(2024, 1, 3)

    def test_get_data_quality_report(self):
        """测试生成数据质量报告"""
        original_prices = [
            StockPriceData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 1),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
            StockPriceData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 2),
                open=Decimal("-1.00"),  # 无效数据
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("152.00"),
                volume=1000000,
                amount=Decimal("152000000")
            ),
        ]

        processed_prices = [original_prices[0]]  # 只有 1 条有效数据

        pipeline = DataPipeline()
        report = pipeline.get_data_quality_report(original_prices, processed_prices)

        assert report["original_count"] == 2
        assert report["processed_count"] == 1
        assert report["removed_count"] == 1
        assert report["quality_rate"] == 50.0
        assert report["status"] == "FAIL"  # 质量率 < 80%


# ==============================================
# Yahoo Finance 数据源测试
# ==============================================

class TestYahooFinanceDataSource:
    """Yahoo Finance 数据源测试"""

    def test_check_connection(self):
        """测试检查连接（需要网络）"""
        source = YahooFinanceDataSource()

        if not source.is_available:
            pytest.skip("yfinance 未安装")

        is_connected = source.check_connection()

        # 验证返回布尔值
        assert isinstance(is_connected, bool)

    def test_format_symbol(self):
        """测试格式化股票代码"""
        symbol = YahooFinanceDataSource.format_symbol("aapl", market="US")
        assert symbol == "AAPL"

        symbol = YahooFinanceDataSource.format_symbol("700.HK", market="HKEX")
        assert symbol == "0700.HK"


# ==============================================
# AkShare 数据源测试
# ==============================================

class TestAkShareDataSource:
    """AkShare 数据源测试"""

    def test_determine_market(self):
        """测试确定市场"""
        source = AkShareDataSource()

        # 上海证券交易所
        assert source._determine_market("600000") == "SHSE"
        # 深圳证券交易所
        assert source._determine_market("000001") == "SZSE"
        assert source._determine_market("300001") == "SZSE"

    def test_format_symbol(self):
        """测试格式化股票代码"""
        symbol = AkShareDataSource.format_symbol("000001", market="SZSE")
        assert symbol == "000001.SZ"

        symbol = AkShareDataSource.format_symbol("600000", market="SHSE")
        assert symbol == "600000.SH"
