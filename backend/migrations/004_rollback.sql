-- ==============================================
-- Quant-Trade System 数据库回滚
-- 版本: 004
-- 描述: 回滚自选股和价格预警表
-- 日期: 2026-03-09
-- ==============================================

-- 删除触发器
DROP TRIGGER IF EXISTS update_watchlist_groups_updated_at ON watchlist_groups;
DROP TRIGGER IF EXISTS update_watchlist_items_updated_at ON watchlist_items;
DROP TRIGGER IF EXISTS update_price_alerts_updated_at ON price_alerts;

-- 删除表（注意顺序，先删除有外键依赖的表）
DROP TABLE IF EXISTS alert_history CASCADE;
DROP TABLE IF EXISTS price_alerts CASCADE;
DROP TABLE IF EXISTS watchlist_items CASCADE;
DROP TABLE IF EXISTS watchlist_groups CASCADE;

-- 删除枚举类型
DROP TYPE IF EXISTS alert_type CASCADE;

-- 删除迁移记录
DELETE FROM migrations WHERE version = '004';

-- 完成消息
DO $$
BEGIN
    RAISE NOTICE '回滚 004 完成: 自选股和价格预警表已删除';
END
$$;
