-- ==============================================
-- Quant-Trade System 数据库迁移
-- 版本: 004
-- 描述: 添加自选股和价格预警表
-- 日期: 2026-03-09
-- ==============================================

-- 启用 UUID 扩展（如果未启用）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================
-- 自选股分组表
-- ==============================================
CREATE TABLE IF NOT EXISTS watchlist_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT watchlist_groups_unique UNIQUE(user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_groups_user_id ON watchlist_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_groups_sort ON watchlist_groups(user_id, sort_order);

-- ==============================================
-- 自选股项目表
-- ==============================================
CREATE TABLE IF NOT EXISTS watchlist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES watchlist_groups(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL REFERENCES stocks(symbol) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT watchlist_items_unique UNIQUE(user_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_items_user_id ON watchlist_items(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_group_id ON watchlist_items(group_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_symbol ON watchlist_items(symbol);

-- ==============================================
-- 价格预警表
-- ==============================================
CREATE TYPE alert_type AS ENUM (
    'PRICE_ABOVE',
    'PRICE_BELOW',
    'CHANGE_PCT_ABOVE',
    'CHANGE_PCT_BELOW',
    'VOLUME_ABOVE',
    'VOLUME_BELOW'
);

CREATE TABLE IF NOT EXISTS price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL REFERENCES stocks(symbol) ON DELETE CASCADE,
    alert_type alert_type NOT NULL,
    target_value NUMERIC(20, 8) NOT NULL,
    current_price NUMERIC(20, 8),
    is_active BOOLEAN DEFAULT TRUE,
    is_triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMPTZ,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_price_alerts_user_id ON price_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_price_alerts_symbol ON price_alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_price_alerts_active ON price_alerts(is_active, is_triggered);
CREATE INDEX IF NOT EXISTS idx_price_alerts_check ON price_alerts(is_active, is_triggered, symbol);

-- ==============================================
-- 预警历史表
-- ==============================================
CREATE TABLE IF NOT EXISTS alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_id UUID REFERENCES price_alerts(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    alert_type alert_type NOT NULL,
    target_value NUMERIC(20, 8) NOT NULL,
    actual_value NUMERIC(20, 8) NOT NULL,
    triggered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alert_history_user_id ON alert_history(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_symbol ON alert_history(symbol);
CREATE INDEX IF NOT EXISTS idx_alert_history_triggered_at ON alert_history(triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_history_ack ON alert_history(user_id, acknowledged);

-- ==============================================
-- 更新触发器（自动更新 updated_at）
-- ==============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 watchlist_groups 添加触发器
DROP TRIGGER IF EXISTS update_watchlist_groups_updated_at ON watchlist_groups;
CREATE TRIGGER update_watchlist_groups_updated_at
    BEFORE UPDATE ON watchlist_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为 watchlist_items 添加触发器
DROP TRIGGER IF EXISTS update_watchlist_items_updated_at ON watchlist_items;
CREATE TRIGGER update_watchlist_items_updated_at
    BEFORE UPDATE ON watchlist_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为 price_alerts 添加触发器
DROP TRIGGER IF EXISTS update_price_alerts_updated_at ON price_alerts;
CREATE TRIGGER update_price_alerts_updated_at
    BEFORE UPDATE ON price_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- 迁移记录
-- ==============================================
INSERT INTO migrations (version, description, applied_at)
VALUES (
    '004',
    '添加自选股和价格预警表',
    CURRENT_TIMESTAMP
) ON CONFLICT (version) DO NOTHING;

-- ==============================================
-- 完成
-- ==============================================
-- 迁移完成消息
DO $$
BEGIN
    RAISE NOTICE '迁移 004 完成: 自选股和价格预警表已创建';
END
$$;
