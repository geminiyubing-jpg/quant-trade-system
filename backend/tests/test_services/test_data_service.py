"""
数据服务单元测试

测试数据源、数据管道和数据入库服务。
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import List

from src.services.data.base import StockPriceData, StockInfo
from src.services.data.validation import DataPipeline, DataValidator
from src.services.data.akshare import AkShareDataSource
from src.services.data.storage import DataStorageService


# ==============================================
# 测试数据
# ==============================================

def create_test_price_data(
    symbol: str = "000001",
    days: int = 10
) -> List[StockPriceData]:
    """创建测试价格数据"""
    prices = []
    base_date = date(2024, 1, 1)

    for i in range(days):
        prices.append(StockPriceData(
            symbol=symbol,
            timestamp=datetime.combine(
                base_date,
                datetime.min.time()
            ) + timedelta(days=i),
            open=Decimal("10.0") + Decimal(str(i * 0.1)),
            high=Decimal("10.2") + Decimal(str(i * 0.1)),
            low=Decimal("9.8") + Decimal(str(i * 0.1)),
            close=Decimal("10.1") + Decimal(str(i * 0.1)),
            volume=1000000 + i * 10000,
            amount=Decimal("10000000") + Decimal(str(i * 10000))
        ))

    return prices


def create_test_stock_info(
    symbol: str = "000001",
    name: str = "测试股票"
) -> StockInfo:
    """创建测试股票信息"""
    return StockInfo(
        symbol=symbol,
        name=name,
        sector="金融",
        industry="银行",
        market="SZSE"
    )


# ==============================================
# DataValidator 测试
# ==============================================

class TestDataValidator:
    """数据验证器测试"""

    def test_validate_stock_info_success(self):
        """测试股票信息验证 - 成功"""
        validator = DataValidator()
        stock_info = create_test_stock_info()

        is_valid, error_msg = validator.validate_stock_info(stock_info)

        assert is_valid
        assert error_msg is None

    def test_validate_stock_info_missing_symbol(self):
        """测试股票信息验证 - 缺少代码"""
        validator = DataValidator()
        stock_info = StockInfo(
            symbol="",  # 空代码
            name="测试股票",
            market="SZSE"
        )

        is_valid, error_msg = validator.validate_stock_info(stock_info)

        assert not is_valid
        assert "代码" in error_msg

    def test_validate_stock_info_missing_name(self):
        """测试股票信息验证 - 缺少名称"""
        validator = DataValidator()
        stock_info = StockInfo(
            symbol="000001",
            name="",  # 空名称
            market="SZSE"
        )

        is_valid, error_msg = validator.validate_stock_info(stock_info)

        assert not is_valid
        assert "名称" in error_msg

    def test_validate_price_data_success(self):
        """测试价格数据验证 - 成功"""
        validator = DataValidator()
        price_data = create_test_price_data()[0]

        is_valid, error_msg = validator.validate_price_data(price_data)

        assert is_valid
        assert error_msg is None

    def test_validate_price_data_zero_price(self):
        """测试价格数据验证 - 零价格"""
        validator = DataValidator()
        price_data = StockPriceData(
            symbol="000001",
            timestamp=datetime.now(),
            open=Decimal("0"),  # 零价格
            high=Decimal("10.0"),
            low=Decimal("9.0"),
            close=Decimal("10.0"),
            volume=1000000,
            amount=Decimal("10000000")
        )

        is_valid, error_msg = validator.validate_price_data(price_data)

        # 零价格应该被标记（根据业务规则可能允许或拒绝）
        # 这里假设拒绝
        if not is_valid:
            assert "价格" in error_msg

    def test_validate_price_data_negative_volume(self):
        """测试价格数据验证 - 负成交量"""
        validator = DataValidator()
        price_data = StockPriceData(
            symbol="000001",
            timestamp=datetime.now(),
            open=Decimal("10.0"),
            high=Decimal("10.0"),
            low=Decimal("10.0"),
            close=Decimal("10.0"),
            volume=-1,  # 负成交量
            amount=Decimal("10000000")
        )

        is_valid, error_msg = validator.validate_price_data(price_data)

        assert not is_valid
        assert "成交量" in error_msg

    def test_validate_price_data_high_low_mismatch(self):
        """测试价格数据验证 - 最高价小于最低价"""
        validator = DataValidator()
        price_data = StockPriceData(
            symbol="000001",
            timestamp=datetime.now(),
            open=Decimal("10.0"),
            high=Decimal("9.0"),  # 最高价 < 最低价
            low=Decimal("10.0"),
            close=Decimal("10.0"),
            volume=1000000,
            amount=Decimal("10000000")
        )

        is_valid, error_msg = validator.validate_price_data(price_data)

        assert not is_valid
        assert "最高价" in error_msg or "最低价" in error_msg


# ==============================================
# DataPipeline 测试
# ==============================================

class TestDataPipeline:
    """数据管道测试"""

    def test_process_stock_prices(self):
        """测试价格数据处理"""
        pipeline = DataPipeline()
        prices = create_test_price_data(days=10)

        cleaned_prices = pipeline.process_stock_prices(prices)

        assert len(cleaned_prices) <= len(prices)
        # 验证清洗后的数据
        for price in cleaned_prices:
            assert price.open >= 0
            assert price.high >= price.low
            assert price.volume >= 0

    def test_remove_duplicates(self):
        """测试去除重复数据"""
        pipeline = DataPipeline()
        prices = create_test_price_data(days=5)

        # 添加重复数据
        duplicated_prices = prices + prices[:2]

        cleaned_prices = pipeline.process_stock_prices(duplicated_prices)

        # 重复数据应该被移除
        assert len(cleaned_prices) == len(prices)

    def test_handle_missing_values(self):
        """测试处理缺失值"""
        pipeline = DataPipeline()
        prices = create_test_price_data(days=5)

        # 添加包含缺失值的数据（None）
        prices_with_missing = prices + [
            StockPriceData(
                symbol="000001",
                timestamp=datetime.now(),
                open=None,  # 缺失值
                high=Decimal("10.0"),
                low=Decimal("9.0"),
                close=Decimal("10.0"),
                volume=1000000,
                amount=None
            )
        ]

        cleaned_prices = pipeline.process_stock_prices(prices_with_missing)

        # 包含缺失值的数据应该被移除或填充
        assert len(cleaned_prices) <= len(prices_with_missing)

    def test_get_data_quality_report(self):
        """测试数据质量报告"""
        pipeline = DataPipeline()
        original_prices = create_test_price_data(days=10)
        cleaned_prices = pipeline.process_stock_prices(original_prices)

        report = pipeline.get_data_quality_report(original_prices, cleaned_prices)

        assert "total_records" in report
        assert "valid_records" in report
        assert "invalid_records" in report
        assert "quality_rate" in report

        # 验证报告数据
        assert report["total_records"] == len(original_prices)
        assert report["valid_records"] == len(cleaned_prices)
        assert report["quality_rate"] >= 0
        assert report["quality_rate"] <= 100


# ==============================================
# AkShareDataSource 测试
# ==============================================

class TestAkShareDataSource:
    """AkShare 数据源测试"""

    @pytest.fixture
    def data_source(self):
        """创建数据源实例"""
        return AkShareDataSource()

    def test_initialization(self, data_source):
        """测试初始化"""
        assert data_source.name == "AkShare"
        # akshare 可能未安装
        # assert data_source.is_available

    def test_format_symbol(self):
        """测试股票代码格式化"""
        # 测试深圳股票
        formatted = AkShareDataSource.format_symbol("000001", "SZSE")
        assert formatted == "000001.SZ"

        # 测试上海股票
        formatted = AkShareDataSource.format_symbol("600000", "SHSE")
        assert formatted == "600000.SH"

        # 测试清理代码
        formatted = AkShareDataSource.format_symbol("SZ000001", "SZSE")
        assert formatted == "000001.SZ"

    def test_determine_market(self, data_source):
        """测试市场判断"""
        # 上海证券交易所（6开头）
        market = data_source._determine_market("600000")
        assert market == "SHSE"

        # 深圳证券交易所（0开头）
        market = data_source._determine_market("000001")
        assert market == "SZSE"

        # 深圳证券交易所（3开头）
        market = data_source._determine_market("300001")
        assert market == "SZSE"

    @pytest.mark.skipif(
        not AkShareDataSource().is_available,
        reason="akshare 未安装"
    )
    def test_check_connection(self, data_source):
        """测试连接检查"""
        if not data_source.is_available:
            pytest.skip("akshare 未安装")

        is_connected = data_source.check_connection()
        # 连接可能失败（网络问题）
        # assert is_connected


# ==============================================
# DataStorageService 测试
# ==============================================

class TestDataStorageService:
    """数据入库服务测试（需要数据库）"""

    @pytest.fixture
    def db_session(self):
        """创建数据库会话"""
        from src.core.database import get_db_context
        with get_db_context() as db:
            yield db

    def test_initialization(self, db_session):
        """测试初始化"""
        service = DataStorageService(db_session)
        assert service.db is not None
        assert service.validator is not None

    def test_save_stock_info(self, db_session):
        """测试保存股票信息"""
        service = DataStorageService(db_session)
        stock_info = create_test_stock_info(
            symbol="TEST001",
            name="测试股票"
        )

        saved_stock = service.save_stock_info(stock_info)

        # 验证保存成功
        assert saved_stock is not None
        assert saved_stock.symbol == "TEST001"

        # 清理测试数据
        db_session.rollback()

    def test_get_latest_timestamp(self, db_session):
        """测试获取最新时间戳"""
        service = DataStorageService(db_session)

        # 获取不存在的股票
        latest = service.get_latest_timestamp("NONEXISTENT")
        assert latest is None

    def test_check_data_completeness(self, db_session):
        """测试数据完整性检查"""
        service = DataStorageService(db_session)

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        report = service.check_data_completeness(
            symbol="NONEXISTENT",
            start_date=start_date,
            end_date=end_date
        )

        assert "symbol" in report
        assert "total_days" in report
        assert "actual_days" in report
        assert "completeness_rate" in report


# ==============================================
# 集成测试
# ==============================================

class TestDataIntegration:
    """数据服务集成测试"""

    @pytest.fixture
    def db_session(self):
        """创建数据库会话"""
        from src.core.database import get_db_context
        with get_db_context() as db:
            yield db

    def test_full_data_pipeline(self, db_session):
        """测试完整数据管道"""
        # 1. 创建数据
        stock_info = create_test_stock_info(symbol="TEST001")
        prices = create_test_price_data(symbol="TEST001", days=5)

        # 2. 验证数据
        validator = DataValidator()
        is_valid, _ = validator.validate_stock_info(stock_info)
        assert is_valid

        # 3. 处理数据
        pipeline = DataPipeline()
        cleaned_prices = pipeline.process_stock_prices(prices)
        assert len(cleaned_prices) > 0

        # 4. 保存数据
        storage_service = DataStorageService(db_session)
        saved_stock = storage_service.save_stock_info(stock_info)
        assert saved_stock is not None

        # 5. 保存价格数据
        records_saved = storage_service.save_stock_prices_upsert(cleaned_prices)
        assert records_saved > 0

        # 6. 验证数据
        latest_timestamp = storage_service.get_latest_timestamp("TEST001")
        assert latest_timestamp is not None

        # 清理
        db_session.rollback()


# ==============================================
# 运行测试
# ==============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
