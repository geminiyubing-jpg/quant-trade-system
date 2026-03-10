# ==============================================
# QuantAI Ecosystem - Database Migration
# ==============================================
# Revision: v2.0.0-001
# Create Date: 2026-03-08
# Author: 角色 C (全栈高级开发工程师)
# Description: 初始化数据库 Schema（包含 P0/P1 修复）
# ==============================================
# 🔴 P0 修复：
#   - 添加 execution_mode 枚举类型（架构红线）
#   - orders 和 positions 表强制要求 execution_mode 字段
#   - 配置 TimescaleDB 时序数据分区
# 🟠 P1 修复：
#   - 添加风控字段（止损、止盈、滑点等）
#   - 添加审计日志字段（created_by, updated_by, version）
# 🟡 P2 修复：
#   - 添加复合索引和数据约束
#   - 修改外键约束为 RESTRICT
# ==============================================

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'v2_0_0_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """应用数据库升级：从空数据库到 v2.0.0"""

    # ==========================================
    # 启用 PostgreSQL 扩展
    # ==========================================
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')

    # ==========================================
    # 创建枚举类型
    # ==========================================
    order_status_enum = postgresql.ENUM(
        'PENDING', 'PARTIAL', 'FILLED', 'CANCELED', 'REJECTED',
        name='order_status'
    )
    order_status_enum.create(op.get_bind())

    order_side_enum = postgresql.ENUM(
        'BUY', 'SELL',
        name='order_side'
    )
    order_side_enum.create(op.get_bind())

    strategy_status_enum = postgresql.ENUM(
        'DRAFT', 'ACTIVE', 'PAUSED', 'ARCHIVED',
        name='strategy_status'
    )
    strategy_status_enum.create(op.get_bind())

    backtest_status_enum = postgresql.ENUM(
        'PENDING', 'RUNNING', 'COMPLETED', 'FAILED',
        name='backtest_status'
    )
    backtest_status_enum.create(op.get_bind())

    # 🔴 P0 修复：添加 execution_mode 枚举（架构红线）
    execution_mode_enum = postgresql.ENUM(
        'PAPER', 'LIVE',
        name='execution_mode'
    )
    execution_mode_enum.create(op.get_bind())

    # ==========================================
    # 创建用户表
    # ==========================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        # 🟠 P1 审计字段
        sa.Column('created_by', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.Column('version', sa.Integer(), default=1),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])

    # ==========================================
    # 创建股票表
    # ==========================================
    op.create_table(
        'stocks',
        sa.Column('symbol', sa.String(20), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('sector', sa.String(50)),
        sa.Column('industry', sa.String(50)),
        sa.Column('market', sa.String(20)),  # SZSE, SHSE, HKEX, US
        sa.Column('list_date', sa.Date()),
        sa.Column('delist_date', sa.Date()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_stocks_sector', 'stocks', ['sector'])
    op.create_index('idx_stocks_market', 'stocks', ['market'])

    # ==========================================
    # 创建行情表（时序数据）
    # ==========================================
    op.create_table(
        'stock_prices',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(20), sa.ForeignKey('stocks.symbol', ondelete='CASCADE'), nullable=False),
        sa.Column('price_close', postgresql.NUMERIC(20, 8), nullable=False),
        sa.Column('price_open', postgresql.NUMERIC(20, 8)),
        sa.Column('price_high', postgresql.NUMERIC(20, 8)),
        sa.Column('price_low', postgresql.NUMERIC(20, 8)),
        sa.Column('volume', sa.BigInteger()),
        sa.Column('amount', postgresql.NUMERIC(30, 8)),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('symbol', 'timestamp', name='uq_stock_prices_symbol_timestamp'),
        sa.CheckConstraint('price_close > 0', name='stock_prices_close_positive'),
        sa.CheckConstraint('price_open IS NULL OR price_open > 0', name='stock_prices_open_positive'),
        sa.CheckConstraint('price_high IS NULL OR price_high >= price_close', name='stock_prices_high_valid'),
        sa.CheckConstraint('price_low IS NULL OR price_low <= price_close', name='stock_prices_low_valid'),
        sa.CheckConstraint('volume IS NULL OR volume >= 0', name='stock_prices_volume_positive'),
    )
    op.create_index('idx_stock_prices_symbol_timestamp', 'stock_prices', ['symbol', sa.text('timestamp DESC')])

    # ==========================================
    # 🔴 P0 修复：配置 TimescaleDB hypertable
    # ==========================================
    try:
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM timescaledb_information.hypertables
                    WHERE hypertable_name = 'stock_prices'
                ) THEN
                    PERFORM create_hypertable('stock_prices', 'timestamp',
                        chunk_time_interval => INTERVAL '1 day'
                    );
                    PERFORM add_compression_policy('stock_prices', INTERVAL '3 months');
                    RAISE NOTICE '✅ TimescaleDB hypertable created for stock_prices';
                END IF;
            END $$;
        """)
    except Exception as e:
        # 如果 TimescaleDB 不可用，记录警告但不中断迁移
        print(f"⚠️  Warning: TimescaleDB configuration failed: {e}")
        print("⚠️  Continuing migration without TimescaleDB...")

    # ==========================================
    # 创建策略表
    # ==========================================
    op.create_table(
        'strategies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', strategy_status_enum, default='DRAFT'),
        sa.Column('code', sa.Text()),
        sa.Column('parameters', postgresql.JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        # 🟠 P1 审计字段
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('version', sa.Integer(), default=1),
    )
    op.create_index('idx_strategies_user_id', 'strategies', ['user_id'])
    op.create_index('idx_strategies_status', 'strategies', ['status'])

    # ==========================================
    # 创建回测表
    # ==========================================
    op.create_table(
        'backtests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('strategies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('status', backtest_status_enum, default='PENDING'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('initial_capital', postgresql.NUMERIC(30, 8), nullable=False),
        sa.Column('final_capital', postgresql.NUMERIC(30, 8)),
        sa.Column('total_return', postgresql.NUMERIC(10, 6)),
        sa.Column('max_drawdown', postgresql.NUMERIC(10, 6)),
        sa.Column('sharpe_ratio', postgresql.NUMERIC(10, 6)),
        sa.Column('results', postgresql.JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        # 🟠 P1 审计字段
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('version', sa.Integer(), default=1),
        sa.CheckConstraint('end_date >= start_date', name='backtest_date_valid'),
        sa.CheckConstraint('initial_capital > 0', name='backtest_capital_positive'),
    )
    op.create_index('idx_backtests_strategy_id', 'backtests', ['strategy_id'])
    op.create_index('idx_backtests_user_id', 'backtests', ['user_id'])
    op.create_index('idx_backtests_status', 'backtests', ['status'])

    # ==========================================
    # 创建订单表（包含 P0/P1 修复）
    # ==========================================
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('strategies.id', ondelete='SET NULL')),
        sa.Column('symbol', sa.String(20), sa.ForeignKey('stocks.symbol'), nullable=False),
        # 🔴 P0 架构红线：强制隔离模拟/实盘
        sa.Column('execution_mode', execution_mode_enum, nullable=False),
        sa.Column('side', order_side_enum, nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', postgresql.NUMERIC(20, 8), nullable=False),
        sa.Column('status', order_status_enum, default='PENDING'),
        sa.Column('filled_quantity', sa.Integer(), default=0),
        sa.Column('filled_amount', postgresql.NUMERIC(30, 8)),
        sa.Column('commission', postgresql.NUMERIC(20, 8), default=0),
        # 🟠 P1 风控字段
        sa.Column('stop_loss_price', postgresql.NUMERIC(20, 8)),
        sa.Column('take_profit_price', postgresql.NUMERIC(20, 8)),
        sa.Column('max_slippage', postgresql.NUMERIC(10, 6), default=0.001),
        sa.Column('time_in_force', sa.String(10), default='DAY'),
        sa.Column('order_time', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('update_time', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        # 🟠 P1 审计字段
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('version', sa.Integer(), default=1),
        # 🟡 P2 数据约束
        sa.CheckConstraint('quantity > 0', name='orders_quantity_positive'),
        sa.CheckConstraint('price > 0', name='orders_price_positive'),
        sa.CheckConstraint('filled_quantity >= 0 AND filled_quantity <= quantity', name='orders_filled_quantity_valid'),
        sa.CheckConstraint('stop_loss_price IS NULL OR stop_loss_price > 0', name='orders_stop_loss_valid'),
        sa.CheckConstraint('take_profit_price IS NULL OR take_profit_price > 0', name='orders_take_profit_valid'),
        sa.CheckConstraint("time_in_force IN ('DAY', 'GTC', 'IOC', 'FOK')", name='orders_time_in_force_valid'),
    )
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_symbol', 'orders', ['symbol'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_order_time', 'orders', [sa.text('order_time DESC')])
    # 🟡 P2 性能优化：复合索引
    op.create_index('idx_orders_user_status_time', 'orders', ['user_id', 'status', sa.text('order_time DESC')])

    # ==========================================
    # 创建持仓表（包含 P0/P1 修复）
    # ==========================================
    op.create_table(
        'positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('strategies.id', ondelete='SET NULL')),
        sa.Column('symbol', sa.String(20), sa.ForeignKey('stocks.symbol'), nullable=False),
        # 🔴 P0 架构红线：强制隔离模拟/实盘
        sa.Column('execution_mode', execution_mode_enum, nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('avg_price', postgresql.NUMERIC(20, 8), nullable=False),
        sa.Column('current_price', postgresql.NUMERIC(20, 8)),
        sa.Column('market_value', postgresql.NUMERIC(30, 8)),
        sa.Column('unrealized_pnl', postgresql.NUMERIC(30, 8)),
        # 🟠 P1 额外的风控和会计字段
        sa.Column('cost_basis', postgresql.NUMERIC(30, 8)),
        sa.Column('realized_pnl', postgresql.NUMERIC(30, 8), default=0),
        sa.Column('max_quantity_limit', sa.Integer()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
        # 🟠 P1 审计字段
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('version', sa.Integer(), default=1),
        # 🟡 P2 数据约束
        sa.CheckConstraint('cost_basis IS NULL OR cost_basis >= 0', name='positions_cost_basis_positive'),
        sa.CheckConstraint('market_value IS NULL OR market_value >= 0', name='positions_market_value_positive'),
    )
    op.create_index('idx_positions_user_id', 'positions', ['user_id'])
    op.create_index('idx_positions_symbol', 'positions', ['symbol'])
    # 🟡 P2 性能优化：部分索引（只索引非零持仓）
    op.create_index('idx_positions_user_strategy', 'positions', ['user_id', 'strategy_id'],
                    postgresql_where=sa.text('quantity > 0'))
    # 添加唯一约束（包含 execution_mode）
    op.create_unique_constraint('positions_unique_per_mode', 'positions',
                                 ['user_id', 'strategy_id', 'symbol', 'execution_mode'])

    # ==========================================
    # 创建风险告警表
    # ==========================================
    op.create_table(
        'risk_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB()),
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_risk_alerts_user_id', 'risk_alerts', ['user_id'])
    op.create_index('idx_risk_alerts_created_at', 'risk_alerts', [sa.text('created_at DESC')])

    # ==========================================
    # 创建系统配置表
    # ==========================================
    op.create_table(
        'system_config',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), default=sa.text('CURRENT_TIMESTAMP')),
    )

    # ==========================================
    # 插入初始配置数据
    # ==========================================
    op.execute("""
        INSERT INTO system_config (key, value, description) VALUES
            ('system.version', '2.0.0', '系统版本'),
            ('system.name', 'QuantAI Ecosystem', '系统名称'),
            ('trading.max_position_ratio', '0.3', '最大单仓比例'),
            ('trading.max_daily_loss_ratio', '0.05', '最大单日亏损比例'),
            ('trading.max_slippage_default', '0.001', '默认最大滑点（0.1%）'),
            ('trading.execution_mode_required', 'true', '强制要求 execution_mode 字段（架构红线）')
        ON CONFLICT (key) DO NOTHING;
    """)

    # ==========================================
    # 创建视图
    # ==========================================
    op.execute("""
        CREATE OR REPLACE VIEW v_position_summary AS
        SELECT
            user_id,
            strategy_id,
            symbol,
            execution_mode,
            SUM(quantity) as total_quantity,
            AVG(avg_price) as avg_cost,
            SUM(market_value) as total_market_value,
            SUM(unrealized_pnl) as total_unrealized_pnl
        FROM positions
        GROUP BY user_id, strategy_id, symbol, execution_mode;
    """)

    # ==========================================
    # 🟡 P2 审计触发器函数
    # ==========================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_audit_fields()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            NEW.updated_by = current_setting('app.current_user_id', true)::UUID;
            NEW.version = OLD.version + 1;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 为 orders 表创建审计触发器
    op.execute("""
        DROP TRIGGER IF EXISTS orders_audit_trigger ON orders;
        CREATE TRIGGER orders_audit_trigger
            BEFORE UPDATE ON orders
            FOR EACH ROW
            EXECUTE FUNCTION update_audit_fields();
    """)

    # 为 positions 表创建审计触发器
    op.execute("""
        DROP TRIGGER IF EXISTS positions_audit_trigger ON positions;
        CREATE TRIGGER positions_audit_trigger
            BEFORE UPDATE ON positions
            FOR EACH ROW
            EXECUTE FUNCTION update_audit_fields();
    """)

    # 为 strategies 表创建审计触发器
    op.execute("""
        DROP TRIGGER IF EXISTS strategies_audit_trigger ON strategies;
        CREATE TRIGGER strategies_audit_trigger
            BEFORE UPDATE ON strategies
            FOR EACH ROW
            EXECUTE FUNCTION update_audit_fields();
    """)

    # 为 backtests 表创建审计触发器
    op.execute("""
        DROP TRIGGER IF EXISTS backtests_audit_trigger ON backtests;
        CREATE TRIGGER backtests_audit_trigger
            BEFORE UPDATE ON backtests
            FOR EACH ROW
            EXECUTE FUNCTION update_audit_fields();
    """)


def downgrade():
    """回滚数据库升级：从 v2.0.0 回滚到空数据库"""

    # 删除触发器
    op.execute('DROP TRIGGER IF EXISTS orders_audit_trigger ON orders')
    op.execute('DROP TRIGGER IF EXISTS positions_audit_trigger ON positions')
    op.execute('DROP TRIGGER IF EXISTS strategies_audit_trigger ON strategies')
    op.execute('DROP TRIGGER IF EXISTS backtests_audit_trigger ON backtests')

    # 删除触发器函数
    op.execute('DROP FUNCTION IF EXISTS update_audit_fields()')

    # 删除视图
    op.execute('DROP VIEW IF EXISTS v_position_summary')

    # 删除表（按照依赖关系倒序）
    op.drop_table('system_config')
    op.drop_table('risk_alerts')
    op.drop_table('positions')
    op.drop_table('orders')
    op.drop_table('backtests')
    op.drop_table('strategies')
    op.drop_table('stock_prices')
    op.drop_table('stocks')
    op.drop_table('users')

    # 删除枚举类型
    postgresql.ENUM(name='execution_mode').drop(op.get_bind())
    postgresql.ENUM(name='backtest_status').drop(op.get_bind())
    postgresql.ENUM(name='strategy_status').drop(op.get_bind())
    postgresql.ENUM(name='order_side').drop(op.get_bind())
    postgresql.ENUM(name='order_status').drop(op.get_bind())

    # 删除扩展
    op.execute('DROP EXTENSION IF EXISTS timescaledb CASCADE')
    op.execute('DROP EXTENSION IF EXISTS btree_gin')
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
