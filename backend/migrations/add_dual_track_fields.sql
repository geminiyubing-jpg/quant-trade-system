-- ==============================================
-- Quant-Trade System - 双轨运行机制数据库迁移
-- ==============================================
-- 版本: v2.5.0
-- 日期: 2026-03-08
-- 描述: 添加 user_id 和 execution_mode 字段，实现 paper/live 双轨隔离
--
-- 修改表:
--   1. positions - 添加 user_id, execution_mode
--   2. orders - 添加 user_id, execution_mode
--   3. strategy_instances - 添加 execution_mode
--
-- 注意: 此迁移应该在生产环境执行前充分测试！
-- ==============================================

BEGIN;

-- ==============================================
-- 1. positions 表迁移
-- ==============================================

-- 添加 user_id 字段
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);

-- 添加 execution_mode 字段
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(10)
DEFAULT 'PAPER'
CHECK (execution_mode IN ('PAPER', 'LIVE'));

-- 添加索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_positions_user_mode
ON positions(user_id, execution_mode);

CREATE INDEX IF NOT EXISTS idx_positions_execution_mode
ON positions(execution_mode);

-- 添加注释
COMMENT ON COLUMN positions.user_id IS '用户 ID，用于双轨隔离';
COMMENT ON COLUMN positions.execution_mode IS '执行模式：PAPER(模拟), LIVE(实盘)';

-- ==============================================
-- 2. orders 表迁移
-- ==============================================

-- 添加 user_id 字段
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);

-- 添加 execution_mode 字段
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(10)
DEFAULT 'PAPER'
CHECK (execution_mode IN ('PAPER', 'LIVE'));

-- 添加索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_orders_user_mode
ON orders(user_id, execution_mode);

CREATE INDEX IF NOT EXISTS idx_orders_execution_mode
ON orders(execution_mode);

-- 添加注释
COMMENT ON COLUMN orders.user_id IS '用户 ID，用于双轨隔离';
COMMENT ON COLUMN orders.execution_mode IS '执行模式：PAPER(模拟), LIVE(实盘)';

-- ==============================================
-- 3. strategy_instances 表迁移
-- ==============================================

-- 添加 execution_mode 字段
ALTER TABLE strategy_instances
ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(10)
DEFAULT 'PAPER'
CHECK (execution_mode IN ('PAPER', 'LIVE'));

-- 添加索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_strategy_instances_user_mode
ON strategy_instances(created_by, execution_mode);

CREATE INDEX IF NOT EXISTS idx_strategy_instances_execution_mode
ON strategy_instances(execution_mode);

-- 添加注释
COMMENT ON COLUMN strategy_instances.execution_mode IS '执行模式：PAPER(模拟), LIVE(实盘)';

-- ==============================================
-- 4. 数据迁移
-- ==============================================

-- 更新现有 strategy_instances 的 execution_mode
-- 所有现有策略默认为 PAPER 模式
UPDATE strategy_instances
SET execution_mode = 'PAPER'
WHERE execution_mode IS NULL;

-- 注意: 由于 positions 和 orders 表当前为空，不需要数据迁移
-- 如果表中有数据，可以使用以下 SQL 进行迁移（根据需要调整）:

/*
-- 迁移 positions 表（从 strategy_instances 获取 user_id 和 execution_mode）
UPDATE positions p
SET
    user_id = si.created_by,
    execution_mode = si.execution_mode
FROM strategy_instances si
WHERE p.strategy_id = si.id
  AND p.user_id IS NULL;

-- 迁移 orders 表（从 strategy_instances 获取 user_id 和 execution_mode）
UPDATE orders o
SET
    user_id = si.created_by,
    execution_mode = si.execution_mode
FROM strategy_instances si
WHERE o.strategy_id = si.id
  AND o.user_id IS NULL;
*/

-- ==============================================
-- 5. 验证迁移结果
-- ==============================================

-- 验证 positions 表结构
DO $$
DECLARE
    col_exists INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_exists
    FROM information_schema.columns
    WHERE table_name = 'positions'
      AND column_name IN ('user_id', 'execution_mode');

    IF col_exists = 2 THEN
        RAISE NOTICE '✅ positions 表迁移成功';
    ELSE
        RAISE EXCEPTION '❌ positions 表迁移失败';
    END IF;
END $$;

-- 验证 orders 表结构
DO $$
DECLARE
    col_exists INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_exists
    FROM information_schema.columns
    WHERE table_name = 'orders'
      AND column_name IN ('user_id', 'execution_mode');

    IF col_exists = 2 THEN
        RAISE NOTICE '✅ orders 表迁移成功';
    ELSE
        RAISE EXCEPTION '❌ orders 表迁移失败';
    END IF;
END $$;

-- 验证 strategy_instances 表结构
DO $$
DECLARE
    col_exists INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_exists
    FROM information_schema.columns
    WHERE table_name = 'strategy_instances'
      AND column_name = 'execution_mode';

    IF col_exists = 1 THEN
        RAISE NOTICE '✅ strategy_instances 表迁移成功';
    ELSE
        RAISE EXCEPTION '❌ strategy_instances 表迁移失败';
    END IF;
END $$;

COMMIT;

-- ==============================================
-- 6. 迁移后检查
-- ==============================================

-- 检查表结构
\d positions

\d orders

\d strategy_instances

-- 检查索引
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('positions', 'orders', 'strategy_instances')
  AND indexname LIKE '%execution_mode%' OR indexname LIKE '%user_mode%'
ORDER BY tablename, indexname;

-- ==============================================
-- 迁移完成！
-- ==============================================
