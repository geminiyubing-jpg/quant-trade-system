"""
SQLAlchemy 模型验证测试

测试所有模型是否符合数据库 Schema v2.0.0 的要求。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from decimal import Decimal

from src.models import (
    Base,
    User,
    Order,
    Position,
    Strategy,
    Backtest,
    RiskAlert,
)


# ==============================================
# 测试配置
# ==============================================

# 使用内存 SQLite 数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.close()


# ==============================================
# 用户模型测试
# ==============================================

class TestUserModel:
    """用户模型测试"""

    def test_create_user(self, db_session):
        """测试创建用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$test_hash",
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.version == 1

    def test_user_unique_constraints(self, db_session):
        """测试用户唯一约束"""
        user1 = User(
            username="testuser",
            email="test@example.com",
            password_hash="$2b$12$test_hash"
        )
        db_session.add(user1)
        db_session.commit()

        # 测试用户名重复
        user2 = User(
            username="testuser",
            email="test2@example.com",
            password_hash="$2b$12$test_hash"
        )
        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


# ==============================================
# 订单模型测试（P0 架构红线）
# ==============================================

class TestOrderModel:
    """订单模型测试"""

    def test_create_order_with_execution_mode(self, db_session):
        """测试创建订单（包含 execution_mode）"""
        # 🔴 P0 架构红线：execution_mode 必须存在
        order = Order(
            user_id="test-user-id",
            symbol="000001.SZ",
            execution_mode="PAPER",  # P0 架构红线
            side="BUY",
            quantity=100,
            price=Decimal("10.50")
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.id is not None
        assert order.execution_mode == "PAPER"
        assert order.status == "PENDING"
        assert order.quantity == 100
        assert order.price == Decimal("10.50")

    def test_order_risk_control_fields(self, db_session):
        """测试订单风控字段（P1 优先级）"""
        # 🟠 P1 风控字段：止损/止盈/滑点/有效期
        order = Order(
            user_id="test-user-id",
            symbol="000001.SZ",
            execution_mode="PAPER",
            side="BUY",
            quantity=100,
            price=Decimal("10.50"),
            stop_loss_price=Decimal("10.00"),  # P1 风控字段
            take_profit_price=Decimal("11.00"),  # P1 风控字段
            max_slippage=Decimal("0.002"),  # P1 风控字段
            time_in_force="GTC"  # P1 风控字段
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.stop_loss_price == Decimal("10.00")
        assert order.take_profit_price == Decimal("11.00")
        assert order.max_slippage == Decimal("0.002")
        assert order.time_in_force == "GTC"

    def test_order_audit_fields(self, db_session):
        """测试订单审计字段（P1 优先级）"""
        # 🟠 P1 审计字段：created_by/updated_by/version
        order = Order(
            user_id="test-user-id",
            symbol="000001.SZ",
            execution_mode="PAPER",
            side="BUY",
            quantity=100,
            price=Decimal("10.50"),
            created_by="creator-id",
            updated_by="updater-id",
            version=1
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.created_by == "creator-id"
        assert order.updated_by == "updater-id"
        assert order.version == 1


# ==============================================
# 持仓模型测试（P0 架构红线）
# ==============================================

class TestPositionModel:
    """持仓模型测试"""

    def test_create_position_with_execution_mode(self, db_session):
        """测试创建持仓（包含 execution_mode）"""
        # 🔴 P0 架构红线：execution_mode 必须存在
        position = Position(
            user_id="test-user-id",
            symbol="000001.SZ",
            execution_mode="PAPER",  # P0 架构红线
            quantity=100,
            avg_price=Decimal("10.50"),
            current_price=Decimal("11.00"),
            market_value=Decimal("1100.00"),
            unrealized_pnl=Decimal("50.00")
        )
        db_session.add(position)
        db_session.commit()
        db_session.refresh(position)

        assert position.id is not None
        assert position.execution_mode == "PAPER"
        assert position.quantity == 100
        assert position.avg_price == Decimal("10.50")

    def test_position_accounting_fields(self, db_session):
        """测试持仓会计字段（P1 优先级）"""
        # 🟠 P1 会计字段：成本基础/已实现盈亏/最大持仓限制
        position = Position(
            user_id="test-user-id",
            symbol="000001.SZ",
            execution_mode="PAPER",
            quantity=100,
            avg_price=Decimal("10.50"),
            cost_basis=Decimal("1050.00"),  # P1 会计字段
            realized_pnl=Decimal("100.00"),  # P1 会计字段
            max_quantity_limit=1000  # P1 会计字段
        )
        db_session.add(position)
        db_session.commit()
        db_session.refresh(position)

        assert position.cost_basis == Decimal("1050.00")
        assert position.realized_pnl == Decimal("100.00")
        assert position.max_quantity_limit == 1000


# ==============================================
# 策略和回测模型测试
# ==============================================

class TestStrategyModel:
    """策略模型测试"""

    def test_create_strategy(self, db_session):
        """测试创建策略"""
        strategy = Strategy(
            user_id="test-user-id",
            name="测试策略",
            description="这是一个测试策略",
            status="DRAFT",
            code="def strategy():\n    pass",
            parameters={"param1": 100, "param2": 0.5}
        )
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)

        assert strategy.id is not None
        assert strategy.name == "测试策略"
        assert strategy.status == "DRAFT"
        assert strategy.version == 1


class TestBacktestModel:
    """回测模型测试"""

    def test_create_backtest(self, db_session):
        """测试创建回测"""
        backtest = Backtest(
            strategy_id="test-strategy-id",
            user_id="test-user-id",
            name="测试回测",
            status="PENDING",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=Decimal("100000.00")
        )
        db_session.add(backtest)
        db_session.commit()
        db_session.refresh(backtest)

        assert backtest.id is not None
        assert backtest.initial_capital == Decimal("100000.00")
        assert backtest.status == "PENDING"


# ==============================================
# 风险告警模型测试
# ==============================================

class TestRiskAlertModel:
    """风险告警模型测试"""

    def test_create_risk_alert(self, db_session):
        """测试创建风险告警"""
        alert = RiskAlert(
            user_id="test-user-id",
            alert_type="POSITION_LIMIT",
            severity="WARNING",
            message="持仓超过限制",
            details={"symbol": "000001.SZ", "quantity": 1500, "limit": 1000}
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        assert alert.id is not None
        assert alert.alert_type == "POSITION_LIMIT"
        assert alert.severity == "WARNING"
        assert alert.is_resolved is False


# ==============================================
# 数值精度测试（P2 优先级）
# ==============================================

class TestNumericPrecision:
    """数值精度测试"""

    def test_price_decimal_precision(self, db_session):
        """测试价格精度（NUMERIC(20, 8)）"""
        # 测试高精度价格
        order = Order(
            user_id="test-user-id",
            symbol="000001.SZ",
            execution_mode="PAPER",
            side="BUY",
            quantity=100,
            price=Decimal("10.12345678")  # 8 位小数
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        assert order.price == Decimal("10.12345678")

    def test_amount_decimal_precision(self, db_session):
        """测试金额精度（NUMERIC(30, 8)）"""
        # 测试大金额
        position = Position(
            user_id="test-user-id",
            symbol="000001.SZ",
            execution_mode="PAPER",
            quantity=1000000,
            avg_price=Decimal("100.12345678"),
            market_value=Decimal("100123456.78")
        )
        db_session.add(position)
        db_session.commit()
        db_session.refresh(position)

        assert position.market_value == Decimal("100123456.78")
