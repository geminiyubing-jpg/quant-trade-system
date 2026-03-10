-- ==============================================
-- 投资组合模块 - 组合管理和风险分析
-- ==============================================
-- 版本: v2.1.0
-- 创建日期: 2026-03-10
-- 说明: 新增投资组合管理、持仓、风险指标和优化功能
-- ==============================================

-- ==============================================
-- 1. 创建枚举类型
-- ==============================================

-- 组合状态
CREATE TYPE portfolio_status AS ENUM (
    'ACTIVE',     -- 活跃
    'PAUSED',     -- 暂停
    'CLOSED'      -- 已关闭
);

-- 优化方法
CREATE TYPE optimization_method AS ENUM (
    'MEAN_VARIANCE',    -- 均值方差优化
    'RISK_PARITY',      -- 风险平价
    'MIN_VARIANCE',     -- 最小方差
    'MAX_SHARPE',       -- 最大夏普
    'EQUAL_WEIGHT',     -- 等权重
    'BLACK_LITTERMAN'   -- Black-Litterman 模型
);

-- ==============================================
-- 2. 投资组合表
-- ==============================================

CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- 组合配置
    benchmark_symbol VARCHAR(20) REFERENCES stocks(symbol), -- 基准指数
    base_currency VARCHAR(10) DEFAULT 'CNY',          -- 基础货币

    -- 资产配置目标
    target_allocation JSONB,                          -- 目标配置 {sector: ratio, ...}
    rebalance_threshold NUMERIC(5, 4) DEFAULT 0.05,   -- 再平衡阈值（5%偏离）
    rebalance_frequency VARCHAR(20) DEFAULT 'MONTHLY',-- 再平衡频率

    -- 状态
    status portfolio_status DEFAULT 'ACTIVE',
    execution_mode execution_mode DEFAULT 'PAPER',

    -- 统计信息
    total_value NUMERIC(30, 8) DEFAULT 0,             -- 总价值
    cash_balance NUMERIC(30, 8) DEFAULT 0,            -- 现金余额
    inception_date DATE,                              -- 成立日期

    -- 审计字段
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) REFERENCES users(id),
    updated_by VARCHAR(100) REFERENCES users(id),
    version INTEGER DEFAULT 1,

    CONSTRAINT ck_rebalance_threshold CHECK (rebalance_threshold >= 0 AND rebalance_threshold <= 1)
);

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolios_status ON portfolios(status);
CREATE INDEX idx_portfolios_execution_mode ON portfolios(execution_mode);

COMMENT ON TABLE portfolios IS '投资组合表 - 定义投资组合的基本信息';
COMMENT ON COLUMN portfolios.target_allocation IS '目标资产配置，JSON 格式如 {"科技": 0.3, "金融": 0.2}';
COMMENT ON COLUMN portfolios.rebalance_threshold IS '再平衡阈值，当偏离超过此比例时触发再平衡';

-- ==============================================
-- 3. 组合持仓表
-- ==============================================

CREATE TABLE IF NOT EXISTS portfolio_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id VARCHAR(100) NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL REFERENCES stocks(symbol),

    -- 持仓信息
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_cost NUMERIC(20, 8) NOT NULL DEFAULT 0,
    current_price NUMERIC(20, 8),
    market_value NUMERIC(30, 8),
    weight NUMERIC(8, 6),                             -- 当前权重
    target_weight NUMERIC(8, 6),                      -- 目标权重

    -- 盈亏
    unrealized_pnl NUMERIC(30, 8),
    realized_pnl NUMERIC(30, 8) DEFAULT 0,

    -- 行业分类
    sector VARCHAR(50),
    industry VARCHAR(50),

    -- 时间
    opened_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'OPEN',                -- OPEN, CLOSED

    -- 审计字段
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,

    CONSTRAINT uk_portfolio_symbol UNIQUE(portfolio_id, symbol)
);

CREATE INDEX idx_portfolio_positions_portfolio_id ON portfolio_positions(portfolio_id);
CREATE INDEX idx_portfolio_positions_symbol ON portfolio_positions(symbol);
CREATE INDEX idx_portfolio_positions_status ON portfolio_positions(status);

COMMENT ON TABLE portfolio_positions IS '组合持仓表 - 记录投资组合中的持仓信息';
COMMENT ON COLUMN portfolio_positions.weight IS '当前权重 = 市值 / 组合总价值';
COMMENT ON COLUMN portfolio_positions.target_weight IS '目标权重，用于再平衡参考';

-- ==============================================
-- 4. 组合风险指标表
-- ==============================================

CREATE TABLE IF NOT EXISTS portfolio_risk_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id VARCHAR(100) NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    calculation_date DATE NOT NULL,

    -- VaR 指标
    var_95 NUMERIC(20, 8),                            -- 95% VaR（历史模拟法）
    var_99 NUMERIC(20, 8),                            -- 99% VaR
    cvar_95 NUMERIC(20, 8),                           -- 95% CVaR（条件 VaR / Expected Shortfall）

    -- 集中度风险
    herfindahl_index NUMERIC(10, 6),                  -- 赫芬达尔指数（衡量集中度）
    max_single_weight NUMERIC(8, 6),                  -- 最大单只权重
    top_5_weight NUMERIC(8, 6),                       -- 前5只权重
    top_10_weight NUMERIC(8, 6),                      -- 前10只权重

    -- 相关性风险
    avg_correlation NUMERIC(10, 6),                   -- 平均相关性
    diversification_ratio NUMERIC(10, 6),             -- 分散化比率

    -- 因子暴露
    beta_to_benchmark NUMERIC(10, 6),                 -- 对基准 Beta
    factor_exposures JSONB,                           -- 因子暴露 {factor: exposure}

    -- 流动性风险
    avg_turnover_days NUMERIC(10, 2),                 -- 平均换手天数
    illiquid_ratio NUMERIC(8, 6),                     -- 非流动性资产占比

    -- 波动率
    portfolio_volatility NUMERIC(10, 6),              -- 组合波动率
    tracking_error NUMERIC(10, 6),                    -- 跟踪误差

    -- 下行风险
    downside_risk NUMERIC(10, 6),                     -- 下行风险
    max_drawdown NUMERIC(10, 6),                      -- 最大回撤

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_portfolio_risk_metrics UNIQUE(portfolio_id, calculation_date)
);

CREATE INDEX idx_portfolio_risk_metrics_portfolio_id ON portfolio_risk_metrics(portfolio_id);
CREATE INDEX idx_portfolio_risk_metrics_calculation_date ON portfolio_risk_metrics(calculation_date);

COMMENT ON TABLE portfolio_risk_metrics IS '组合风险指标表 - 存储组合的风险分析结果';
COMMENT ON COLUMN portfolio_risk_metrics.var_95 IS '95% 置信度下的在险价值';
COMMENT ON COLUMN portfolio_risk_metrics.cvar_95 IS '95% 条件在险价值，即损失超过 VaR 时的平均损失';
COMMENT ON COLUMN portfolio_risk_metrics.herfindahl_index IS '赫芬达尔指数，Σ(w_i)^2，衡量持仓集中度，1/N 表示完全分散';

-- ==============================================
-- 5. 组合优化记录表
-- ==============================================

CREATE TABLE IF NOT EXISTS portfolio_optimizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id VARCHAR(100) NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,

    -- 优化配置
    optimization_method optimization_method NOT NULL, -- 优化方法
    objective_function TEXT,                          -- 目标函数描述
    constraints JSONB,                                -- 约束条件 {max_weight, min_weight, sector_limits}

    -- 优化结果
    current_weights JSONB,                            -- 当前权重 {symbol: weight}
    optimal_weights JSONB,                            -- 最优权重 {symbol: weight}
    expected_return NUMERIC(10, 6),                   -- 预期收益
    expected_risk NUMERIC(10, 6),                     -- 预期风险
    expected_sharpe NUMERIC(10, 6),                   -- 预期夏普比率

    -- 调仓建议
    rebalance_trades JSONB,                           -- 调仓建议 [{symbol, action, quantity, weight_change}]
    estimated_transaction_cost NUMERIC(20, 8),        -- 预计交易成本

    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING',             -- PENDING, APPLIED, REJECTED
    applied_at TIMESTAMPTZ,

    -- 审计
    created_by VARCHAR(100) REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_portfolio_optimizations_portfolio_id ON portfolio_optimizations(portfolio_id);
CREATE INDEX idx_portfolio_optimizations_method ON portfolio_optimizations(optimization_method);
CREATE INDEX idx_portfolio_optimizations_status ON portfolio_optimizations(status);

COMMENT ON TABLE portfolio_optimizations IS '组合优化记录表 - 存储组合优化的结果和建议';
COMMENT ON COLUMN portfolio_optimizations.optimization_method IS '优化方法：均值方差、风险平价、最小方差等';
COMMENT ON COLUMN portfolio_optimizations.rebalance_trades IS '调仓建议列表，包含需要买卖的股票和数量';

-- ==============================================
-- 6. 为新表添加审计触发器
-- ==============================================

-- 为 portfolios 表创建审计触发器
DROP TRIGGER IF EXISTS portfolios_audit_trigger ON portfolios;
CREATE TRIGGER portfolios_audit_trigger
    BEFORE UPDATE ON portfolios
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_fields();

-- 为 portfolio_positions 表创建审计触发器
DROP TRIGGER IF EXISTS portfolio_positions_audit_trigger ON portfolio_positions;
CREATE TRIGGER portfolio_positions_audit_trigger
    BEFORE UPDATE ON portfolio_positions
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_fields();

-- ==============================================
-- 7. 创建组合视图
-- ==============================================

-- 组合概览视图
CREATE OR REPLACE VIEW v_portfolio_overview AS
SELECT
    p.id as portfolio_id,
    p.user_id,
    p.name as portfolio_name,
    p.status,
    p.execution_mode,
    p.total_value,
    p.cash_balance,
    p.benchmark_symbol,
    COUNT(pp.id) as position_count,
    SUM(pp.market_value) as positions_market_value,
    SUM(pp.unrealized_pnl) as total_unrealized_pnl,
    MAX(pp.updated_at) as last_position_update
FROM portfolios p
LEFT JOIN portfolio_positions pp ON p.id = pp.portfolio_id AND pp.status = 'OPEN'
GROUP BY p.id, p.user_id, p.name, p.status, p.execution_mode, p.total_value, p.cash_balance, p.benchmark_symbol;

-- ==============================================
-- 8. 完成提示
-- ==============================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE '投资组合模块迁移完成！';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ 已创建表: portfolios, portfolio_positions, portfolio_risk_metrics, portfolio_optimizations';
    RAISE NOTICE '✅ 已创建枚举: portfolio_status, optimization_method';
    RAISE NOTICE '✅ 已创建视图: v_portfolio_overview';
    RAISE NOTICE '============================================';
END $$;
