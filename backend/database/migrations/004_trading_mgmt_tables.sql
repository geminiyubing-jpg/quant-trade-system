-- ==============================================
-- 交易管理模块 - 成交记录和交易日历
-- ==============================================
-- 版本: v2.1.0
-- 创建日期: 2026-03-10
-- 说明: 添加成交记录、交易日历和交易统计功能
-- ==============================================

-- ==============================================
-- 1. 成交记录表
-- ==============================================

CREATE TABLE IF NOT EXISTS fills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id VARCHAR(50) NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    strategy_id VARCHAR(100) REFERENCES strategies(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL REFERENCES stocks(symbol),
    execution_mode execution_mode NOT NULL,           -- 继承订单的执行模式

    -- 成交信息
    fill_id VARCHAR(50) UNIQUE,                       -- 成交 ID（交易所返回）
    side order_side NOT NULL,                         -- 买卖方向
    quantity INTEGER NOT NULL,                        -- 成交数量
    price NUMERIC(20, 8) NOT NULL,                    -- 成交价格
    fill_amount NUMERIC(30, 8),                       -- 成交金额

    -- 费用明细
    commission NUMERIC(20, 8) DEFAULT 0,              -- 佣金
    stamp_duty NUMERIC(20, 8) DEFAULT 0,              -- 印花税（仅卖出）
    transfer_fee NUMERIC(20, 8) DEFAULT 0,            -- 过户费
    total_fees NUMERIC(20, 8) DEFAULT 0,              -- 总费用

    -- 时间
    fill_time TIMESTAMPTZ NOT NULL,                   -- 成交时间
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT ck_fills_quantity_positive CHECK (quantity > 0),
    CONSTRAINT ck_fills_price_positive CHECK (price > 0),
    CONSTRAINT ck_fills_fill_amount_positive CHECK (fill_amount IS NULL OR fill_amount > 0)
);

CREATE INDEX idx_fills_order_id ON fills(order_id);
CREATE INDEX idx_fills_user_id ON fills(user_id);
CREATE INDEX idx_fills_symbol ON fills(symbol);
CREATE INDEX idx_fills_execution_mode ON fills(execution_mode);
CREATE INDEX idx_fills_fill_time ON fills(fill_time DESC);
CREATE INDEX idx_fills_strategy_id ON fills(strategy_id);

COMMENT ON TABLE fills IS '成交记录表 - 存储订单的成交明细';
COMMENT ON COLUMN fills.fill_id IS '交易所返回的成交编号';
COMMENT ON COLUMN fills.stamp_duty IS '印花税，A股市场仅卖出时收取（0.1%）';
COMMENT ON COLUMN fills.transfer_fee IS '过户费，沪市股票收取';

-- ==============================================
-- 2. 交易日历表
-- ==============================================

CREATE TABLE IF NOT EXISTS trading_calendar (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,                  -- 交易日期
    market VARCHAR(20) NOT NULL DEFAULT 'A-SHARE',    -- 市场（A-SHARE, HK, US）

    -- 交易状态
    is_trading_day BOOLEAN NOT NULL,                  -- 是否交易日
    is_half_day BOOLEAN DEFAULT false,                -- 是否半天交易日

    -- 时间信息
    open_time TIME,                                   -- 开盘时间
    close_time TIME,                                  -- 收盘时间
    lunch_start TIME,                                 -- 午休开始（A股：11:30）
    lunch_end TIME,                                   -- 午休结束（A股：13:00）

    -- 特殊标记
    is_month_end BOOLEAN DEFAULT false,               -- 是否月末
    is_quarter_end BOOLEAN DEFAULT false,             -- 是否季末
    is_year_end BOOLEAN DEFAULT false,                -- 是否年末
    holiday_name VARCHAR(100),                        -- 节假日名称（如非交易日）

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_trading_calendar_date_market UNIQUE(trade_date, market)
);

CREATE INDEX idx_trading_calendar_trade_date ON trading_calendar(trade_date);
CREATE INDEX idx_trading_calendar_is_trading_day ON trading_calendar(is_trading_day);
CREATE INDEX idx_trading_calendar_market ON trading_calendar(market);

COMMENT ON TABLE trading_calendar IS '交易日历表 - 记录市场交易日和非交易日';
COMMENT ON COLUMN trading_calendar.is_half_day IS '是否为半天交易日（如节假日前最后一个交易日）';

-- ==============================================
-- 3. 交易统计日报表
-- ==============================================

CREATE TABLE IF NOT EXISTS daily_trade_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    trade_date DATE NOT NULL,
    execution_mode execution_mode NOT NULL,           -- 执行模式隔离

    -- 订单统计
    total_orders INTEGER DEFAULT 0,                   -- 总订单数
    filled_orders INTEGER DEFAULT 0,                  -- 成交订单数
    canceled_orders INTEGER DEFAULT 0,                -- 撤销订单数
    rejected_orders INTEGER DEFAULT 0,                -- 拒绝订单数

    -- 成交统计
    buy_count INTEGER DEFAULT 0,                      -- 买入次数
    sell_count INTEGER DEFAULT 0,                     -- 卖出次数
    buy_volume BIGINT DEFAULT 0,                      -- 买入股数
    sell_volume BIGINT DEFAULT 0,                     -- 卖出股数
    buy_amount NUMERIC(30, 8) DEFAULT 0,              -- 买入金额
    sell_amount NUMERIC(30, 8) DEFAULT 0,             -- 卖出金额

    -- 费用统计
    total_commission NUMERIC(20, 8) DEFAULT 0,        -- 总佣金
    total_stamp_duty NUMERIC(20, 8) DEFAULT 0,        -- 总印花税
    total_transfer_fee NUMERIC(20, 8) DEFAULT 0,      -- 总过户费
    total_fees NUMERIC(20, 8) DEFAULT 0,              -- 总费用

    -- 盈亏统计
    realized_pnl NUMERIC(30, 8) DEFAULT 0,            -- 已实现盈亏
    daily_pnl NUMERIC(30, 8) DEFAULT 0,               -- 当日盈亏（已实现 + 浮动）

    -- 持仓统计
    position_count INTEGER DEFAULT 0,                 -- 持仓数量
    total_market_value NUMERIC(30, 8) DEFAULT 0,      -- 总市值
    total_unrealized_pnl NUMERIC(30, 8) DEFAULT 0,    -- 总浮动盈亏

    -- 账户统计
    cash_balance NUMERIC(30, 8),                      -- 现金余额
    total_equity NUMERIC(30, 8),                      -- 总权益

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_daily_trade_stats UNIQUE(user_id, trade_date, execution_mode)
);

CREATE INDEX idx_daily_trade_stats_user_id ON daily_trade_stats(user_id);
CREATE INDEX idx_daily_trade_stats_trade_date ON daily_trade_stats(trade_date);
CREATE INDEX idx_daily_trade_stats_execution_mode ON daily_trade_stats(execution_mode);

COMMENT ON TABLE daily_trade_stats IS '交易统计日报表 - 记录每日交易汇总数据';
COMMENT ON COLUMN daily_trade_stats.daily_pnl IS '当日盈亏，包含已实现盈亏和浮动盈亏变化';

-- ==============================================
-- 4. 为 daily_trade_stats 添加审计触发器
-- ==============================================

DROP TRIGGER IF EXISTS daily_trade_stats_audit_trigger ON daily_trade_stats;
CREATE TRIGGER daily_trade_stats_audit_trigger
    BEFORE UPDATE ON daily_trade_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_fields();

-- ==============================================
-- 5. 插入示例交易日历数据（2026年A股）
-- ==============================================

-- 插入2026年3月的交易日数据
INSERT INTO trading_calendar (trade_date, market, is_trading_day, open_time, close_time, lunch_start, lunch_end, is_month_end, is_quarter_end)
SELECT
    d::date,
    'A-SHARE',
    EXTRACT(DOW FROM d) NOT IN (0, 6),  -- 排除周末
    '09:30'::time,
    '15:00'::time,
    '11:30'::time,
    '13:00'::time,
    EXTRACT(DAY FROM d) = (DATE_TRUNC('MONTH', d) + INTERVAL '1 MONTH - 1 DAY')::date::day,
    EXTRACT(MONTH FROM d) IN (3, 6, 9, 12) AND EXTRACT(DAY FROM d) = (DATE_TRUNC('MONTH', d) + INTERVAL '1 MONTH - 1 DAY')::date::day
FROM generate_series('2026-03-01'::date, '2026-03-31'::date, '1 day'::interval) AS d
ON CONFLICT (trade_date, market) DO NOTHING;

-- ==============================================
-- 6. 完成提示
-- ==============================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE '交易管理模块迁移完成！';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ 已创建表: fills, trading_calendar, daily_trade_stats';
    RAISE NOTICE '✅ 已插入 2026年3月 交易日历数据';
    RAISE NOTICE '============================================';
END $$;
