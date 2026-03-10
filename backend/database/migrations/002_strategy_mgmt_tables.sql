-- ==============================================
-- 策略管理模块 - 版本控制和审计日志
-- ==============================================
-- 版本: v2.1.0
-- 创建日期: 2026-03-10
-- 说明: 添加策略版本控制、配置管理和审计日志功能
-- ==============================================

-- ==============================================
-- 1. 创建枚举类型
-- ==============================================

-- 变更类型
CREATE TYPE change_type AS ENUM (
    'MAJOR',    -- 主版本（不兼容的 API 变更）
    'MINOR',    -- 次版本（向后兼容的功能新增）
    'PATCH'     -- 补丁版本（向后兼容的问题修复）
);

-- 审计动作类型
CREATE TYPE action_type AS ENUM (
    'CREATE',             -- 创建
    'UPDATE',             -- 更新
    'DELETE',             -- 删除
    'STATUS_CHANGE',      -- 状态变更
    'PARAM_CHANGE',       -- 参数变更
    'VERSION_PUBLISH',    -- 版本发布
    'VERSION_ROLLBACK'    -- 版本回滚
);

-- ==============================================
-- 2. 策略版本控制表
-- ==============================================

CREATE TABLE IF NOT EXISTS strategy_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id VARCHAR(100) NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,              -- 语义化版本 (e.g., "1.0.0")
    version_code_hash VARCHAR(64),                    -- 代码哈希 (SHA-256)
    code TEXT,                                        -- 策略代码快照
    parameters JSONB,                                 -- 参数快照
    change_log TEXT,                                  -- 变更日志
    change_type change_type NOT NULL DEFAULT 'PATCH', -- 变更类型
    is_active BOOLEAN DEFAULT false,                  -- 是否当前激活版本
    created_by VARCHAR(100) REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_strategy_version UNIQUE(strategy_id, version_number),
    CONSTRAINT ck_version_number_format CHECK (version_number ~ '^\d+\.\d+\.\d+$')
);

CREATE INDEX idx_strategy_versions_strategy_id ON strategy_versions(strategy_id);
CREATE INDEX idx_strategy_versions_created_at ON strategy_versions(created_at DESC);
CREATE INDEX idx_strategy_versions_is_active ON strategy_versions(is_active) WHERE is_active = true;

COMMENT ON TABLE strategy_versions IS '策略版本控制表 - 存储策略的历史版本';
COMMENT ON COLUMN strategy_versions.version_number IS '语义化版本号，格式：主版本.次版本.补丁 (如 1.0.0)';
COMMENT ON COLUMN strategy_versions.version_code_hash IS '策略代码的 SHA-256 哈希值，用于快速比对代码变化';
COMMENT ON COLUMN strategy_versions.is_active IS '是否为当前激活的版本，每个策略只能有一个激活版本';

-- ==============================================
-- 3. 策略配置表
-- ==============================================

CREATE TABLE IF NOT EXISTS strategy_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id VARCHAR(100) NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    -- 市场标的配置
    symbols JSONB NOT NULL DEFAULT '[]',              -- 股票代码列表 ["000001.SZ", "600000.SH"]
    market VARCHAR(20),                               -- 市场 (SHSE, SZSE)

    -- 资金分配
    allocation_ratio NUMERIC(5, 4) DEFAULT 1.0,       -- 资金分配比例 (0-1)
    max_position_count INTEGER DEFAULT 10,            -- 最大持仓数
    max_single_position_ratio NUMERIC(5, 4) DEFAULT 0.2, -- 单仓上限 (0-1)

    -- 风险限制
    stop_loss_ratio NUMERIC(5, 4),                    -- 止损比例 (如 0.05 表示 5%)
    take_profit_ratio NUMERIC(5, 4),                  -- 止盈比例
    max_drawdown_limit NUMERIC(5, 4) DEFAULT 0.2,     -- 最大回撤限制
    daily_loss_limit NUMERIC(5, 4) DEFAULT 0.05,      -- 单日亏损限制

    -- 执行配置
    execution_mode execution_mode DEFAULT 'PAPER',    -- 执行模式
    auto_rebalance BOOLEAN DEFAULT false,             -- 自动再平衡
    rebalance_frequency VARCHAR(20),                  -- 再平衡频率 (DAILY, WEEKLY, MONTHLY)

    -- 时间配置
    effective_date DATE,                              -- 生效日期
    expiry_date DATE,                                 -- 过期日期

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,

    CONSTRAINT ck_allocation_ratio CHECK (allocation_ratio > 0 AND allocation_ratio <= 1),
    CONSTRAINT ck_max_single_position CHECK (max_single_position_ratio > 0 AND max_single_position_ratio <= 1),
    CONSTRAINT ck_stop_loss_ratio CHECK (stop_loss_ratio IS NULL OR (stop_loss_ratio > 0 AND stop_loss_ratio < 1)),
    CONSTRAINT ck_take_profit_ratio CHECK (take_profit_ratio IS NULL OR take_profit_ratio > 0)
);

CREATE INDEX idx_strategy_configs_strategy_id ON strategy_configs(strategy_id);
CREATE INDEX idx_strategy_configs_user_id ON strategy_configs(user_id);
CREATE INDEX idx_strategy_configs_is_active ON strategy_configs(is_active) WHERE is_active = true;

COMMENT ON TABLE strategy_configs IS '策略配置表 - 存储策略的运行时配置';
COMMENT ON COLUMN strategy_configs.symbols IS 'JSON 数组，存储策略交易的股票代码列表';
COMMENT ON COLUMN strategy_configs.allocation_ratio IS '资金分配比例，1.0 表示使用全部可用资金';

-- ==============================================
-- 4. 策略审计日志表
-- ==============================================

CREATE TABLE IF NOT EXISTS strategy_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id VARCHAR(100) NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    -- 审计信息
    action_type action_type NOT NULL,                 -- 操作类型
    action_description TEXT,                          -- 操作描述

    -- 变更详情
    old_value JSONB,                                  -- 变更前的值
    new_value JSONB,                                  -- 变更后的值
    changed_fields TEXT[],                            -- 变更的字段列表

    -- 上下文信息
    ip_address VARCHAR(45),                           -- IP 地址
    user_agent TEXT,                                  -- 用户代理
    session_id UUID,                                  -- 会话 ID

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategy_audit_log_strategy_id ON strategy_audit_log(strategy_id);
CREATE INDEX idx_strategy_audit_log_user_id ON strategy_audit_log(user_id);
CREATE INDEX idx_strategy_audit_log_created_at ON strategy_audit_log(created_at DESC);
CREATE INDEX idx_strategy_audit_log_action_type ON strategy_audit_log(action_type);

COMMENT ON TABLE strategy_audit_log IS '策略审计日志表 - 记录策略的所有操作历史';
COMMENT ON COLUMN strategy_audit_log.changed_fields IS '变更的字段名称数组';

-- ==============================================
-- 5. 为新表添加审计触发器
-- ==============================================

-- 为 strategy_configs 表创建审计触发器
DROP TRIGGER IF EXISTS strategy_configs_audit_trigger ON strategy_configs;
CREATE TRIGGER strategy_configs_audit_trigger
    BEFORE UPDATE ON strategy_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_fields();

-- ==============================================
-- 6. 完成提示
-- ==============================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE '策略管理模块迁移完成！';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ 已创建表: strategy_versions, strategy_configs, strategy_audit_log';
    RAISE NOTICE '✅ 已创建枚举: change_type, action_type';
    RAISE NOTICE '============================================';
END $$;
