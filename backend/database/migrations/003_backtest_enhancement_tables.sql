-- ==============================================
-- 回测增强模块 - 因子分析和归因分析
-- ==============================================
-- 版本: v2.1.0
-- 创建日期: 2026-03-10
-- 说明: 添加因子分析、归因分析和扩展绩效指标
-- ==============================================

-- ==============================================
-- 1. 创建回测结果表（如果不存在）
-- ==============================================
-- 注意：如果已有 backtest_results 表，请跳过此部分

CREATE TABLE IF NOT EXISTS backtest_results (
    id BIGSERIAL PRIMARY KEY,
    backtest_id UUID NOT NULL REFERENCES backtests(id) ON DELETE CASCADE,

    -- 基础绩效指标
    total_return NUMERIC(10, 6),                      -- 总收益率
    annual_return NUMERIC(10, 6),                     -- 年化收益率
    benchmark_return NUMERIC(10, 6),                  -- 基准收益率
    excess_return NUMERIC(10, 6),                     -- 超额收益

    -- 风险指标
    volatility NUMERIC(10, 6),                        -- 波动率
    sharpe_ratio NUMERIC(10, 6),                      -- 夏普比率
    max_drawdown NUMERIC(10, 6),                      -- 最大回撤
    max_drawdown_duration INTEGER,                    -- 最大回撤持续天数

    -- 交易统计
    total_trades INTEGER DEFAULT 0,                   -- 总交易次数
    winning_trades INTEGER DEFAULT 0,                 -- 盈利次数
    losing_trades INTEGER DEFAULT 0,                  -- 亏损次数
    win_rate NUMERIC(5, 4),                           -- 胜率

    -- 曲线数据
    equity_curve JSONB,                               -- 资金曲线 [{date, value}]
    daily_returns JSONB,                              -- 日收益率 [{date, return}]
    drawdown_curve JSONB,                             -- 回撤曲线 [{date, drawdown}]
    trades JSONB,                                     -- 交易记录 [{date, symbol, side, price, quantity}]

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_backtest_results_backtest_id ON backtest_results(backtest_id);

-- ==============================================
-- 2. 因子分析表
-- ==============================================

CREATE TABLE IF NOT EXISTS factor_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_result_id BIGINT NOT NULL REFERENCES backtest_results(id) ON DELETE CASCADE,

    -- 因子名称
    factor_name VARCHAR(100),                         -- 因子名称

    -- IC 分析
    ic_mean NUMERIC(10, 6),                           -- IC 均值
    ic_std NUMERIC(10, 6),                            -- IC 标准差
    ic_ir NUMERIC(10, 6),                             -- IC 信息比率 (IC mean / IC std)
    ic_t_stat NUMERIC(10, 6),                         -- IC t 统计量
    ic_positive_ratio NUMERIC(5, 4),                  -- IC 正值比例

    -- 因子收益分析
    factor_return NUMERIC(10, 6),                     -- 因子收益
    factor_volatility NUMERIC(10, 6),                 -- 因子波动率
    factor_t_stat NUMERIC(10, 6),                     -- 因子收益 t 统计量

    -- 换手率分析
    avg_turnover NUMERIC(10, 6),                      -- 平均换手率
    turnover_cost NUMERIC(20, 8),                     -- 换手成本

    -- 分组分析
    group_returns JSONB,                              -- 分组收益 [{group, return}]
    long_short_return NUMERIC(10, 6),                 -- 多空收益（做多 top 组，做空 bottom 组）

    -- 时间序列
    ic_series JSONB,                                  -- IC 时间序列 [{date, ic}]
    factor_return_series JSONB,                       -- 因子收益时间序列 [{date, return}]

    -- 因子相关性
    correlation_matrix JSONB,                         -- 与其他因子的相关性 {factor_name: correlation}

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_factor_analyses_backtest_result_id ON factor_analyses(backtest_result_id);
CREATE INDEX idx_factor_analyses_factor_name ON factor_analyses(factor_name);

COMMENT ON TABLE factor_analyses IS '因子分析结果表 - 存储回测的因子分析结果';
COMMENT ON COLUMN factor_analyses.ic_mean IS '信息系数均值，衡量因子预测能力';
COMMENT ON COLUMN factor_analyses.ic_ir IS 'IC 信息比率，IC 均值 / IC 标准差，衡量因子稳定性';
COMMENT ON COLUMN factor_analyses.long_short_return IS '多空收益，做多因子值最高组，做空因子值最低组的收益';

-- ==============================================
-- 3. 归因分析表
-- ==============================================

CREATE TABLE IF NOT EXISTS attribution_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_result_id BIGINT NOT NULL REFERENCES backtest_results(id) ON DELETE CASCADE,

    -- Brinson 归因模型
    allocation_effect NUMERIC(10, 6),                 -- 配置效应（资产配置贡献）
    selection_effect NUMERIC(10, 6),                  -- 选股效应（证券选择贡献）
    interaction_effect NUMERIC(10, 6),                -- 交互效应（配置和选择的交互）
    total_active_return NUMERIC(10, 6),               -- 总主动收益

    -- 行业归因
    industry_attribution JSONB,                       -- 行业归因详情 [{industry, allocation, selection, total}]

    -- 风险因子归因（如 Barra 模型）
    risk_factor_attribution JSONB,                    -- 风险因子归因 [{factor, exposure, return}]

    -- 基准信息
    benchmark_symbol VARCHAR(20),                     -- 基准代码（如 000300.SH）
    benchmark_return NUMERIC(10, 6),                  -- 基准收益率

    -- 时间序列归因
    monthly_attribution JSONB,                        -- 月度归因 [{month, allocation, selection, interaction}]

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attribution_analyses_backtest_result_id ON attribution_analyses(backtest_result_id);

COMMENT ON TABLE attribution_analyses IS '归因分析结果表 - 存储回测的绩效归因分析';
COMMENT ON COLUMN attribution_analyses.allocation_effect IS '配置效应，资产配置决策对收益的贡献';
COMMENT ON COLUMN attribution_analyses.selection_effect IS '选股效应，证券选择决策对收益的贡献';
COMMENT ON COLUMN attribution_analyses.interaction_effect IS '交互效应，配置和选择共同作用产生的收益';

-- ==============================================
-- 4. 扩展回测指标表
-- ==============================================

CREATE TABLE IF NOT EXISTS backtest_metrics_extended (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_result_id BIGINT NOT NULL REFERENCES backtest_results(id) ON DELETE CASCADE,

    -- 风险调整收益指标
    sortino_ratio NUMERIC(10, 6),                     -- Sortino 比率（只考虑下行风险）
    calmar_ratio NUMERIC(10, 6),                      -- Calmar 比率（年化收益 / 最大回撤）
    treynor_ratio NUMERIC(10, 6),                     -- Treynor 比率（超额收益 / Beta）
    information_ratio NUMERIC(10, 6),                 -- 信息比率（超额收益 / 跟踪误差）

    -- Alpha/Beta
    alpha NUMERIC(10, 6),                             -- Alpha（超额收益）
    beta NUMERIC(10, 6),                              -- Beta（系统风险暴露）
    tracking_error NUMERIC(10, 6),                    -- 跟踪误差

    -- 下行风险
    downside_deviation NUMERIC(10, 6),                -- 下行偏差（负收益的标准差）
    max_consecutive_losses INTEGER,                    -- 最大连续亏损次数
    max_consecutive_loss_amount NUMERIC(20, 8),       -- 最大连续亏损金额

    -- 交易质量
    profit_factor NUMERIC(10, 6),                     -- 盈亏比（总盈利 / 总亏损）
    payoff_ratio NUMERIC(10, 6),                      -- 平均盈利 / 平均亏损
    risk_reward_ratio NUMERIC(10, 6),                 -- 风险回报比

    -- 持仓分析
    avg_holding_days NUMERIC(10, 2),                  -- 平均持仓天数
    max_holding_days INTEGER,                         -- 最大持仓天数
    min_holding_days INTEGER,                         -- 最小持仓天数

    -- 回撤分析
    avg_drawdown NUMERIC(10, 6),                      -- 平均回撤
    drawdown_duration_avg NUMERIC(10, 2),             -- 平均回撤持续时间（天）
    recovery_factor NUMERIC(10, 6),                   -- 恢复因子（总收益 / 最大回撤）

    -- 波动率分析
    upside_volatility NUMERIC(10, 6),                 -- 上行波动率
    downside_volatility NUMERIC(10, 6),               -- 下行波动率

    -- 换手率
    avg_turnover_rate NUMERIC(10, 6),                 -- 平均换手率
    total_turnover_cost NUMERIC(20, 8),               -- 总换手成本

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_backtest_metrics_extended UNIQUE(backtest_result_id)
);

CREATE INDEX idx_backtest_metrics_extended_backtest_result_id ON backtest_metrics_extended(backtest_result_id);

COMMENT ON TABLE backtest_metrics_extended IS '扩展回测指标表 - 存储更详细的绩效指标';
COMMENT ON COLUMN backtest_metrics_extended.sortino_ratio IS 'Sortino 比率，只考虑下行风险的夏普比率变体';
COMMENT ON COLUMN backtest_metrics_extended.calmar_ratio IS 'Calmar 比率，年化收益除以最大回撤的绝对值';
COMMENT ON COLUMN backtest_metrics_extended.information_ratio IS '信息比率，超额收益除以跟踪误差';

-- ==============================================
-- 5. 完成提示
-- ==============================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE '回测增强模块迁移完成！';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ 已创建表: backtest_results, factor_analyses, attribution_analyses, backtest_metrics_extended';
    RAISE NOTICE '============================================';
END $$;
