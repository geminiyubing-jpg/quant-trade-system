-- ==============================================
-- Quant-Trade System - 双轨运行机制回滚脚本
-- ==============================================
-- 版本: v2.5.0
-- 日期: 2026-03-08
-- 描述: 回滚双轨字段迁移（紧急情况使用）
--
-- 警告: 此操作会删除 user_id 和 execution_mode 字段！
--       请确保在执行前已备份数据库！
-- ==============================================

BEGIN;

-- ==============================================
-- 1. 删除 positions 表字段
-- ==============================================

DROP INDEX IF EXISTS idx_positions_user_mode;
DROP INDEX IF EXISTS idx_positions_execution_mode;

ALTER TABLE positions
DROP COLUMN IF EXISTS user_id;

ALTER TABLE positions
DROP COLUMN IF EXISTS execution_mode;

-- ==============================================
-- 2. 删除 orders 表字段
-- ==============================================

DROP INDEX IF EXISTS idx_orders_user_mode;
DROP INDEX IF EXISTS idx_orders_execution_mode;

ALTER TABLE orders
DROP COLUMN IF EXISTS user_id;

ALTER TABLE orders
DROP COLUMN IF EXISTS execution_mode;

-- ==============================================
-- 3. 删除 strategy_instances 表字段
-- ==============================================

DROP INDEX IF EXISTS idx_strategy_instances_user_mode;
DROP INDEX IF EXISTS idx_strategy_instances_execution_mode;

ALTER TABLE strategy_instances
DROP COLUMN IF EXISTS execution_mode;

COMMIT;

-- ==============================================
-- 回滚完成！
-- ==============================================
