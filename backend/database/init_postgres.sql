-- ==============================================
-- QuantAI Ecosystem - PostgreSQL 初始化脚本
-- ==============================================
-- 版本: v2.0.0
-- 创建日期: 2026-03-08
-- 团队: Quant Core Team
-- 修复: P0 架构红线违规（execution_mode）+ P1 风控/审计字段
-- ==============================================

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID 生成
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- 全文搜索
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN 索引支持
CREATE EXTENSION IF NOT EXISTS timescaledb;      -- 时序数据库（TimescaleDB）

-- ==============================================
-- 创建枚举类型
-- ==============================================

-- 订单状态
CREATE TYPE order_status AS ENUM (
    'PENDING',      -- 待成交
    'PARTIAL',      -- 部分成交
    'FILLED',       -- 已成交
    'CANCELED',     -- 已撤销
    'REJECTED'      -- 已拒绝
);

-- 订单方向
CREATE TYPE order_side AS ENUM (
    'BUY',          -- 买入
    'SELL'          -- 卖出
);

-- 策略状态
CREATE TYPE strategy_status AS ENUM (
    'DRAFT',        -- 草稿
    'ACTIVE',       -- 运行中
    'PAUSED',       -- 暂停
    'ARCHIVED'      -- 已归档
);

-- 回测状态
CREATE TYPE backtest_status AS ENUM (
    'PENDING',      -- 待运行
    'RUNNING',      -- 运行中
    'COMPLETED',    -- 已完成
    'FAILED'        -- 失败
);

-- 执行模式（架构红线：强制隔离模拟/实盘）
CREATE TYPE execution_mode AS ENUM (
    'PAPER',        -- 模拟交易
    'LIVE'          -- 实盘交易
);

-- ==============================================
-- 创建用户和认证表
-- ==============================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    -- 审计字段
    created_by UUID DEFAULT uuid_generate_v4(),
    updated_by UUID,
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- ==============================================
-- 创建市场数据表
-- ==============================================

-- 股票基本信息表
CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sector VARCHAR(50),
    industry VARCHAR(50),
    market VARCHAR(20),  -- SZSE, SHSE, HKEX, US
    list_date DATE,
    delist_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stocks_sector ON stocks(sector);
CREATE INDEX idx_stocks_market ON stocks(market);

-- 实时行情表（时序数据）
CREATE TABLE IF NOT EXISTS stock_prices (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES stocks(symbol) ON DELETE CASCADE,
    price_close NUMERIC(20, 8) NOT NULL,      -- 收盘价（使用高精度 NUMERIC）
    price_open NUMERIC(20, 8),               -- 开盘价
    price_high NUMERIC(20, 8),               -- 最高价
    price_low NUMERIC(20, 8),                -- 最低价
    volume BIGINT,                            -- 成交量
    amount NUMERIC(30, 8),                    -- 成交额
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp),

    -- 数据约束
    CONSTRAINT stock_prices_close_positive CHECK (price_close > 0),
    CONSTRAINT stock_prices_open_positive CHECK (price_open IS NULL OR price_open > 0),
    CONSTRAINT stock_prices_high_valid CHECK (price_high IS NULL OR price_high >= price_close),
    CONSTRAINT stock_prices_low_valid CHECK (price_low IS NULL OR price_low <= price_close),
    CONSTRAINT stock_prices_volume_positive CHECK (volume IS NULL OR volume >= 0)
);

-- 基础索引
CREATE INDEX idx_stock_prices_symbol_timestamp ON stock_prices(symbol, timestamp DESC);

-- 🟡 P2 性能优化：复合索引和部分索引
CREATE INDEX idx_orders_user_status_time ON orders(user_id, status, order_time DESC);
CREATE INDEX idx_positions_user_strategy ON positions(user_id, strategy_id) WHERE quantity > 0;

-- ==============================================
-- 创建策略表
-- ==============================================

CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status strategy_status DEFAULT 'DRAFT',
    code TEXT,                                -- 策略代码
    parameters JSONB,                         -- 策略参数
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    -- 审计字段
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_status ON strategies(status);

-- ==============================================
-- 创建回测表
-- ==============================================

CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,
    status backtest_status DEFAULT 'PENDING',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital NUMERIC(30, 8) NOT NULL,  -- 初始资金（使用 NUMERIC）
    final_capital NUMERIC(30, 8),             -- 最终资金
    total_return NUMERIC(10, 6),               -- 总收益率
    max_drawdown NUMERIC(10, 6),              -- 最大回撤
    sharpe_ratio NUMERIC(10, 6),              -- 夏普比率
    results JSONB,                            -- 回测结果
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    -- 审计字段
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1,
    -- 数据约束
    CONSTRAINT backtest_date_valid CHECK (end_date >= start_date),
    CONSTRAINT backtest_capital_positive CHECK (initial_capital > 0)
);

CREATE INDEX idx_backtests_strategy_id ON backtests(strategy_id);
CREATE INDEX idx_backtests_user_id ON backtests(user_id);
CREATE INDEX idx_backtests_status ON backtests(status);

-- ==============================================
-- 创建交易表
-- ==============================================

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL REFERENCES stocks(symbol),
    execution_mode execution_mode NOT NULL,    -- 🔴 P0 架构红线：强制隔离模拟/实盘
    side order_side NOT NULL,
    quantity INTEGER NOT NULL,
    price NUMERIC(20, 8) NOT NULL,              -- 价格（使用 NUMERIC）
    status order_status DEFAULT 'PENDING',
    filled_quantity INTEGER DEFAULT 0,
    filled_amount NUMERIC(30, 8),
    commission NUMERIC(20, 8) DEFAULT 0,       -- 佣金（使用 NUMERIC）

    -- 🟠 P1 风控字段
    stop_loss_price NUMERIC(20, 8),            -- 止损价格
    take_profit_price NUMERIC(20, 8),          -- 止盈价格
    max_slippage NUMERIC(10, 6) DEFAULT 0.001, -- 最大滑点容忍度（默认 0.1%）
    time_in_force VARCHAR(10) DEFAULT 'DAY'    -- 订单有效期：DAY, GTC, IOC, FOK
        CHECK (time_in_force IN ('DAY', 'GTC', 'IOC', 'FOK')),

    order_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- 🟠 P1 审计字段
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1,

    -- 🟡 P2 数据约束
    CONSTRAINT orders_quantity_positive CHECK (quantity > 0),
    CONSTRAINT orders_price_positive CHECK (price > 0),
    CONSTRAINT orders_filled_quantity_valid CHECK (filled_quantity >= 0 AND filled_quantity <= quantity),
    CONSTRAINT orders_stop_loss_valid CHECK (stop_loss_price IS NULL OR stop_loss_price > 0),
    CONSTRAINT orders_take_profit_valid CHECK (take_profit_price IS NULL OR take_profit_price > 0)
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_order_time ON orders(order_time DESC);

-- ==============================================
-- 创建持仓表
-- ==============================================

CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL REFERENCES stocks(symbol),
    execution_mode execution_mode NOT NULL,    -- 🔴 P0 架构红线：强制隔离模拟/实盘
    quantity INTEGER NOT NULL,
    avg_price NUMERIC(20, 8) NOT NULL,         -- 平均成本（使用 NUMERIC）
    current_price NUMERIC(20, 8),              -- 当前价格
    market_value NUMERIC(30, 8),               -- 市值
    unrealized_pnl NUMERIC(30, 8),             -- 浮动盈亏

    -- 🟠 P1 额外的风控和会计字段
    cost_basis NUMERIC(30, 8),                 -- 成本基础（总投入）
    realized_pnl NUMERIC(30, 8) DEFAULT 0,     -- 已实现盈亏
    max_quantity_limit INTEGER,                -- 最大持仓限制

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- 🟠 P1 审计字段
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1,

    -- 🟡 P2 数据约束
    CONSTRAINT positions_cost_basis_positive CHECK (cost_basis IS NULL OR cost_basis >= 0),
    CONSTRAINT positions_market_value_positive CHECK (market_value IS NULL OR market_value >= 0),
    CONSTRAINT positions_unique_per_mode UNIQUE(user_id, strategy_id, symbol, execution_mode)
);

CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- ==============================================
-- 创建风险监控表
-- ==============================================

CREATE TABLE IF NOT EXISTS risk_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,            -- 告警类型
    severity VARCHAR(20) NOT NULL,              -- 严重程度：INFO, WARNING, CRITICAL
    message TEXT NOT NULL,
    details JSONB,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_alerts_user_id ON risk_alerts(user_id);
CREATE INDEX idx_risk_alerts_created_at ON risk_alerts(created_at DESC);

-- ==============================================
-- 创建系统配置表
-- ==============================================

CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- 插入初始配置数据
-- ==============================================

INSERT INTO system_config (key, value, description) VALUES
    ('system.version', '2.0.0', '系统版本'),
    ('system.name', 'QuantAI Ecosystem', '系统名称'),
    ('trading.max_position_ratio', '0.3', '最大单仓比例'),
    ('trading.max_daily_loss_ratio', '0.05', '最大单日亏损比例'),
    ('trading.max_slippage_default', '0.001', '默认最大滑点（0.1%）'),
    ('trading.execution_mode_required', 'true', '强制要求 execution_mode 字段（架构红线）')
ON CONFLICT (key) DO NOTHING;

-- ==============================================
-- 创建视图
-- ==============================================

-- 持仓汇总视图（按 execution_mode 分离）
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

-- ==============================================
-- 授权（根据需要）
-- ==============================================

-- 授予应用用户必要的权限
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quant_trade_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quant_trade_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO quant_trade_user;

-- ==============================================
-- 🟡 P2 审计触发器函数（自动更新 updated_at, updated_by, version）
-- ==============================================

CREATE OR REPLACE FUNCTION update_audit_fields()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.updated_by = current_setting('app.current_user_id', true)::UUID;
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为 orders 表创建审计触发器
DROP TRIGGER IF EXISTS orders_audit_trigger ON orders;
CREATE TRIGGER orders_audit_trigger
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_fields();

-- 为 positions 表创建审计触发器
DROP TRIGGER IF EXISTS positions_audit_trigger ON positions;
CREATE TRIGGER positions_audit_trigger
    BEFORE UPDATE ON positions
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_fields();

-- 为 strategies 表创建审计触发器
DROP TRIGGER IF EXISTS strategies_audit_trigger ON strategies;
CREATE TRIGGER strategies_audit_trigger
    BEFORE UPDATE ON strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_fields();

-- 为 backtests 表创建审计触发器
DROP TRIGGER IF EXISTS backtests_audit_trigger ON backtests;
CREATE TRIGGER backtests_audit_trigger
    BEFORE UPDATE ON backtests
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_fields();

-- ==============================================
-- 🔴 P0 TimescaleDB 配置（时序数据分区）
-- ==============================================

-- 将 stock_prices 表转换为 TimescaleDB hypertable
-- 只有在表不是 hypertable 的情况下才执行
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables
        WHERE hypertable_name = 'stock_prices'
    ) THEN
        PERFORMANCE SAFE CREATE_HYPERTABLE('stock_prices', 'timestamp',
            chunk_time_interval => INTERVAL '1 day'
        );

        -- 设置自动压缩策略（3 个月前的数据自动压缩）
        PERFORM add_compression_policy('stock_prices',
            INTERVAL '3 months'
        );

        -- 设置数据保留策略（保留 2 年数据，自动删除更旧的数据）
        -- PERFORM add_retention_policy('stock_prices',
        --     INTERVAL '2 years'
        -- );

        RAISE NOTICE '✅ TimescaleDB hypertable created for stock_prices';
    ELSE
        RAISE NOTICE 'ℹ️  stock_prices is already a hypertable';
    END IF;
END $$;

-- 创建连续聚合视图（可选：按小时/日聚合 OHLCV）
-- MATERIALIZED VIEW v_stock_prices_1hour
-- WITH (timescaledb.continuous) AS
-- SELECT
--     time_bucket('1 hour', timestamp) AS bucket,
--     symbol,
--     first(price_close, timestamp) AS open,
--     max(price_high) AS high,
--     min(price_low) AS low,
--     last(price_close, timestamp) AS close,
--     sum(volume) AS volume
-- FROM stock_prices
-- GROUP BY bucket, symbol;

-- ==============================================
-- 完成提示
-- ==============================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'QuantAI Ecosystem v2.0.0 数据库初始化完成！';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ 已创建表: users, stocks, stock_prices';
    RAISE NOTICE '✅          strategies, backtests, orders';
    RAISE NOTICE '✅          positions, risk_alerts, system_config';
    RAISE NOTICE '';
    RAISE NOTICE '🔴 P0 修复：execution_mode 字段已添加（架构红线）';
    RAISE NOTICE '🔴 P0 修复：TimescaleDB hypertable 已配置';
    RAISE NOTICE '🟠 P1 修复：风控字段已添加（止损/止盈/滑点）';
    RAISE NOTICE '🟠 P1 修复：审计日志字段已添加';
    RAISE NOTICE '🟡 P2 修复：复合索引和数据约束已添加';
    RAISE NOTICE '============================================';
END $$;
