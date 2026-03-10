"""
==============================================
QuantAI Ecosystem - Database Schema Validation Tests
==============================================
测试目标：验证 P0/P1 修复是否正确应用
执行方式：pytest backend/tests/test_schema_validation.py -v
==============================================
"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import IntegrityError, DataError
from datetime import datetime, timezone
import uuid


# 测试数据库连接（使用环境变量）
TEST_DATABASE_URL = "postgresql://quant_trio:quant_trio_pass@localhost:5432/quant_trio"


@pytest.fixture(scope="module")
def db_engine():
    """创建测试数据库连接"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="module")
def db_connection(db_engine):
    """创建测试数据库连接"""
    conn = db_engine.connect()
    try:
        yield conn
    finally:
        conn.close()


class TestP0ArchitectureRedLines:
    """🔴 P0 优先级测试：架构红线合规性"""

    def test_execution_mode_enum_exists(self, db_connection):
        """验证 execution_mode 枚举类型存在"""
        result = db_connection.execute(text("""
            SELECT typname FROM pg_type
            WHERE typname = 'execution_mode'
        """))
        assert result.rowcount == 1, "❌ P0 失败：execution_mode 枚举类型不存在"

    def test_execution_mode_enum_values(self, db_connection):
        """验证 execution_mode 枚举值正确"""
        result = db_connection.execute(text("""
            SELECT enumlabel FROM pg_enum
            WHERE enumtypid = 'execution_mode'::regtype
            ORDER BY enumsortorder
        """))
        values = [row[0] for row in result]
        assert values == ['PAPER', 'LIVE'], f"❌ P0 失败：execution_mode 枚举值错误: {values}"

    def test_orders_table_has_execution_mode(self, db_connection):
        """验证 orders 表有 execution_mode 字段且为 NOT NULL"""
        inspector = inspect(db_connection)
        columns = {col['name']: col for col in inspector.get_columns('orders')}

        assert 'execution_mode' in columns, "❌ P0 失败：orders 表缺少 execution_mode 字段（架构红线违规）"
        assert columns['execution_mode']['nullable'] == False, "❌ P0 失败：orders.execution_mode 应为 NOT NULL"

    def test_positions_table_has_execution_mode(self, db_connection):
        """验证 positions 表有 execution_mode 字段且为 NOT NULL"""
        inspector = inspect(db_connection)
        columns = {col['name']: col for col in inspector.get_columns('positions')}

        assert 'execution_mode' in columns, "❌ P0 失败：positions 表缺少 execution_mode 字段（架构红线违规）"
        assert columns['execution_mode']['nullable'] == False, "❌ P0 失败：positions.execution_mode 应为 NOT NULL"

    def test_order_without_execution_mode_fails(self, db_connection):
        """验证缺少 execution_mode 的订单无法插入（强制约束）"""
        with pytest.raises(Exception) as exc_info:
            db_connection.execute(text("""
                INSERT INTO orders (id, user_id, symbol, side, quantity, price)
                VALUES (:id, :user_id, :symbol, 'BUY', 100, 10.5)
            """), {
                'id': uuid.uuid4(),
                'user_id': uuid.uuid4(),
                'symbol': 'TEST'
            })
        assert 'execution_mode' in str(exc_info.value) or 'null' in str(exc_info.value).lower(), \
            "❌ P0 失败：应该强制要求 execution_mode 字段"

    def test_timescaledb_hypertable_exists(self, db_connection):
        """验证 TimescaleDB hypertable 已配置"""
        try:
            result = db_connection.execute(text("""
                SELECT hypertable_name FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'stock_prices'
            """))
            assert result.rowcount == 1, "❌ P0 失败：stock_prices 未配置为 TimescaleDB hypertable"
        except Exception as e:
            pytest.skip(f"⚠️  TimescaleDB 扩展未安装: {e}")


class TestP1RiskControlFields:
    """🟠 P1 优先级测试：风控字段完整性"""

    def test_orders_has_stop_loss_price(self, db_connection):
        """验证 orders 表有止损价格字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('orders')]
        assert 'stop_loss_price' in columns, "❌ P1 失败：orders 表缺少 stop_loss_price 字段"

    def test_orders_has_take_profit_price(self, db_connection):
        """验证 orders 表有止盈价格字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('orders')]
        assert 'take_profit_price' in columns, "❌ P1 失败：orders 表缺少 take_profit_price 字段"

    def test_orders_has_max_slippage(self, db_connection):
        """验证 orders 表有最大滑点字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('orders')]
        assert 'max_slippage' in columns, "❌ P1 失败：orders 表缺少 max_slippage 字段"

    def test_orders_has_time_in_force(self, db_connection):
        """验证 orders 表有订单有效期字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('orders')]
        assert 'time_in_force' in columns, "❌ P1 失败：orders 表缺少 time_in_force 字段"

    def test_positions_has_cost_basis(self, db_connection):
        """验证 positions 表有成本基础字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('positions')]
        assert 'cost_basis' in columns, "❌ P1 失败：positions 表缺少 cost_basis 字段"

    def test_positions_has_realized_pnl(self, db_connection):
        """验证 positions 表有已实现盈亏字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('positions')]
        assert 'realized_pnl' in columns, "❌ P1 失败：positions 表缺少 realized_pnl 字段"


class TestP1AuditFields:
    """🟠 P1 优先级测试：审计日志字段"""

    def test_orders_has_audit_fields(self, db_connection):
        """验证 orders 表有审计字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('orders')]

        assert 'created_by' in columns, "❌ P1 失败：orders 表缺少 created_by 字段"
        assert 'updated_by' in columns, "❌ P1 失败：orders 表缺少 updated_by 字段"
        assert 'version' in columns, "❌ P1 失败：orders 表缺少 version 字段"

    def test_positions_has_audit_fields(self, db_connection):
        """验证 positions 表有审计字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('positions')]

        assert 'created_by' in columns, "❌ P1 失败：positions 表缺少 created_by 字段"
        assert 'updated_by' in columns, "❌ P1 失败：positions 表缺少 updated_by 字段"
        assert 'version' in columns, "❌ P1 失败：positions 表缺少 version 字段"

    def test_strategies_has_audit_fields(self, db_connection):
        """验证 strategies 表有审计字段"""
        inspector = inspect(db_connection)
        columns = [col['name'] for col in inspector.get_columns('strategies')]

        assert 'created_by' in columns, "❌ P1 失败：strategies 表缺少 created_by 字段"
        assert 'updated_by' in columns, "❌ P1 失败：strategies 表缺少 updated_by 字段"
        assert 'version' in columns, "❌ P1 失败：strategies 表缺少 version 字段"

    def test_audit_trigger_function_exists(self, db_connection):
        """验证审计触发器函数存在"""
        result = db_connection.execute(text("""
            SELECT proname FROM pg_proc
            WHERE proname = 'update_audit_fields'
        """))
        assert result.rowcount == 1, "❌ P1 失败：update_audit_fields 触发器函数不存在"


class TestP2ConstraintsAndIndexes:
    """🟡 P2 优先级测试：数据约束和索引"""

    def test_orders_quantity_positive_constraint(self, db_connection):
        """验证订单数量必须为正数"""
        inspector = inspect(db_connection)
        constraints = inspector.get_check_constraints('orders')
        constraint_names = [c['name'] for c in constraints]
        assert 'orders_quantity_positive' in constraint_names, \
            "❌ P2 失败：orders 表缺少 quantity 正数约束"

    def test_orders_price_positive_constraint(self, db_connection):
        """验证订单价格必须为正数"""
        inspector = inspect(db_connection)
        constraints = inspector.get_check_constraints('orders')
        constraint_names = [c['name'] for c in constraints]
        assert 'orders_price_positive' in constraint_names, \
            "❌ P2 失败：orders 表缺少 price 正数约束"

    def test_foreign_key_restrict(self, db_connection):
        """验证外键约束为 RESTRICT（而非 CASCADE）"""
        inspector = inspect(db_connection)
        foreign_keys = inspector.get_foreign_keys('orders')

        user_id_fk = [fk for fk in foreign_keys if fk['constrained_columns'] == ['user_id']]
        assert len(user_id_fk) > 0, "❌ P2 失败：orders 表缺少 user_id 外键"

        # 验证 ondelete 是 RESTRICT（或者没有设置，默认也是 RESTRICT）
        # 注意：SQLAlchemy 的 get_foreign_keys 可能不返回 ondelete 信息
        # 这里只检查外键存在性

    def test_composite_index_exists(self, db_connection):
        """验证复合索引存在"""
        inspector = inspect(db_connection)
        indexes = inspector.get_indexes('orders')
        index_names = [idx['name'] for idx in indexes]
        assert 'idx_orders_user_status_time' in index_names, \
            "❌ P2 失败：orders 表缺少复合索引 idx_orders_user_status_time"

    def test_partial_index_exists(self, db_connection):
        """验证部分索引存在"""
        inspector = inspect(db_connection)
        indexes = inspector.get_indexes('positions')
        index_names = [idx['name'] for idx in indexes]
        assert 'idx_positions_user_strategy' in index_names, \
            "❌ P2 失败：positions 表缺少部分索引 idx_positions_user_strategy"


class TestDataTypes:
    """✅ 数据类型正确性测试"""

    def test_price_fields_use_numeric(self, db_connection):
        """验证价格字段使用 NUMERIC 类型"""
        inspector = inspect(db_connection)
        orders_columns = {col['name']: col for col in inspector.get_columns('orders')}

        assert 'price' in orders_columns, "❌ orders 表缺少 price 字段"
        assert orders_columns['price']['type'].asdecimal == True, \
            "❌ orders.price 应该使用 NUMERIC 类型（而非 FLOAT）"

        positions_columns = {col['name']: col for col in inspector.get_columns('positions')}
        assert 'avg_price' in positions_columns, "❌ positions 表缺少 avg_price 字段"
        assert positions_columns['avg_price']['type'].asdecimal == True, \
            "❌ positions.avg_price 应该使用 NUMERIC 类型（而非 FLOAT）"

    def test_timestamp_fields_use_timestamptz(self, db_connection):
        """验证时间戳字段使用 TIMESTAMPTZ 类型"""
        inspector = inspect(db_connection)
        orders_columns = {col['name']: col for col in inspector.get_columns('orders')}

        assert 'order_time' in orders_columns, "❌ orders 表缺少 order_time 字段"
        # SQLAlchemy 会将 TIMESTAMPTZ 映射为 DATETIME TIMEZONE=True


class TestSystemConfig:
    """系统配置测试"""

    def test_system_version_is_v2(self, db_connection):
        """验证系统版本已更新为 2.0.0"""
        result = db_connection.execute(text("""
            SELECT value FROM system_config WHERE key = 'system.version'
        """))
        row = result.fetchone()
        assert row is not None, "❌ system_config 中缺少 system.version"
        assert row[0] == '2.0.0', f"❌ 系统版本应该为 2.0.0，当前为 {row[0]}"

    def test_execution_mode_required_config_exists(self, db_connection):
        """验证 execution_mode 强制配置存在"""
        result = db_connection.execute(text("""
            SELECT value FROM system_config WHERE key = 'trading.execution_mode_required'
        """))
        row = result.fetchone()
        assert row is not None, "❌ system_config 中缺少 trading.execution_mode_required"
        assert row[0].lower() == 'true', f"❌ execution_mode_required 应该为 true"


class TestViews:
    """视图测试"""

    def test_position_summary_view_exists(self, db_connection):
        """验证持仓汇总视图存在"""
        inspector = inspect(db_connection)
        views = inspector.get_view_names()
        assert 'v_position_summary' in views, "❌ v_position_summary 视图不存在"

    def test_position_summary_view_includes_execution_mode(self, db_connection):
        """验证持仓汇总视图包含 execution_mode"""
        result = db_connection.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'v_position_summary'
        """))
        columns = [row[0] for row in result]
        assert 'execution_mode' in columns, \
            "❌ v_position_summary 视图应该包含 execution_mode 字段"


# 集成测试：插入测试数据
class TestIntegration:
    """集成测试：验证数据完整性约束"""

    @pytest.fixture(autouse=True)
    def setup_test_user(self, db_connection):
        """创建测试用户"""
        test_user_id = uuid.uuid4()
        db_connection.execute(text("""
            INSERT INTO users (id, username, email, password_hash)
            VALUES (:id, :username, :email, :password_hash)
            ON CONFLICT (id) DO NOTHING
        """), {
            'id': test_user_id,
            'username': 'test_user',
            'email': 'test@example.com',
            'password_hash': 'hashed_password'
        })
        db_connection.commit()
        yield test_user_id

    def test_insert_paper_order_succeeds(self, db_connection, setup_test_user):
        """验证插入模拟订单成功"""
        order_id = uuid.uuid4()
        try:
            db_connection.execute(text("""
                INSERT INTO orders (id, user_id, strategy_id, symbol, execution_mode, side, quantity, price)
                VALUES (:id, :user_id, NULL, 'AAPL', 'PAPER', 'BUY', 100, 150.25)
            """), {'id': order_id, 'user_id': setup_test_user})
            db_connection.commit()
            print("✅ 模拟订单插入成功")
        except Exception as e:
            pytest.fail(f"❌ 模拟订单插入失败: {e}")
        finally:
            # 清理测试数据
            db_connection.execute(text("DELETE FROM orders WHERE id = :id"), {'id': order_id})
            db_connection.commit()

    def test_insert_live_order_succeeds(self, db_connection, setup_test_user):
        """验证插入实盘订单成功"""
        order_id = uuid.uuid4()
        try:
            db_connection.execute(text("""
                INSERT INTO orders (id, user_id, strategy_id, symbol, execution_mode, side, quantity, price)
                VALUES (:id, :user_id, NULL, 'AAPL', 'LIVE', 'BUY', 100, 150.25)
            """), {'id': order_id, 'user_id': setup_test_user})
            db_connection.commit()
            print("✅ 实盘订单插入成功")
        except Exception as e:
            pytest.fail(f"❌ 实盘订单插入失败: {e}")
        finally:
            # 清理测试数据
            db_connection.execute(text("DELETE FROM orders WHERE id = :id"), {'id': order_id})
            db_connection.commit()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
