-- ============================================================================
-- Quant-Trade System - 市场动态模块数据库表
-- 版本: v2.5.0
-- 创建日期: 2026-03-11
-- 描述: AI美林时钟 + 宏观分析 + 新闻情感分析 数据存储
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. 美林时钟判断结果表
-- ============================================================================

CREATE TABLE IF NOT EXISTS merrill_clock_judgments (
    judgment_id VARCHAR(50) PRIMARY KEY,
    country VARCHAR(20) NOT NULL,
    phase VARCHAR(20) NOT NULL,              -- recession/recovery/overheat/stagflation
    confidence DECIMAL(5,4),                  -- 置信度 0-1
    growth_score DECIMAL(5,4),                -- 增长得分 -1到1
    inflation_score DECIMAL(5,4),             -- 通胀得分 -1到1
    indicators_used JSONB,                    -- 使用的指标列表
    reasoning TEXT,                           -- AI推理过程
    alternative_phases JSONB,                 -- 备选阶段及概率
    judgment_time TIMESTAMP NOT NULL,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE merrill_clock_judgments IS '美林时钟周期判断结果';
COMMENT ON COLUMN merrill_clock_judgments.phase IS '经济周期阶段: recession(衰退)/recovery(复苏)/overheat(过热)/stagflation(滞胀)';

-- ============================================================================
-- 2. 资产配置推荐表
-- ============================================================================

CREATE TABLE IF NOT EXISTS asset_allocations (
    allocation_id VARCHAR(50) PRIMARY KEY,
    judgment_id VARCHAR(50) REFERENCES merrill_clock_judgments(judgment_id),
    phase VARCHAR(20) NOT NULL,
    country VARCHAR(20) NOT NULL,
    equities_weight DECIMAL(5,4),             -- 股票权重
    bonds_weight DECIMAL(5,4),                -- 债券权重
    commodities_weight DECIMAL(5,4),          -- 商品权重
    cash_weight DECIMAL(5,4),                 -- 现金权重
    sector_recommendations JSONB,             -- 行业推荐
    risk_level VARCHAR(20),                   -- low/medium/high
    expected_return DECIMAL(8,4),             -- 预期收益
    expected_volatility DECIMAL(8,4),         -- 预期波动率
    rebalance_frequency VARCHAR(20),          -- 再平衡频率
    rationale TEXT,                           -- 配置理由
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE asset_allocations IS '基于美林时钟的资产配置推荐';

-- ============================================================================
-- 3. 宏观指标数据表
-- ============================================================================

CREATE TABLE IF NOT EXISTS macro_indicators (
    id SERIAL PRIMARY KEY,
    indicator_id VARCHAR(50) NOT NULL,
    country VARCHAR(20) NOT NULL,
    series_id VARCHAR(100),                   -- 数据源序列ID
    name VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    category VARCHAR(50),                     -- growth/inflation/employment/monetary
    current_value DECIMAL(15,4),
    previous_value DECIMAL(15,4),
    yoy_change DECIMAL(8,4),                  -- 同比变化
    mom_change DECIMAL(8,4),                  -- 环比变化
    trend VARCHAR(20),                        -- upward/downward/stable
    data_date DATE NOT NULL,
    frequency VARCHAR(20),                    -- daily/weekly/monthly/quarterly
    source VARCHAR(50),                       -- FRED/BLS/NBS/ECI
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(indicator_id, data_date, country)
);

COMMENT ON TABLE macro_indicators IS '宏观经济指标数据';

-- ============================================================================
-- 4. 新闻情感分析结果表
-- ============================================================================

CREATE TABLE IF NOT EXISTS news_sentiment (
    sentiment_id VARCHAR(50) PRIMARY KEY,
    source VARCHAR(100),                      -- 新闻来源
    title TEXT,
    content TEXT,
    summary TEXT,
    sentiment_score DECIMAL(5,4),             -- 情感得分 -1到1
    sentiment_label VARCHAR(20),              -- positive/negative/neutral
    confidence DECIMAL(5,4),
    topics JSONB,                             -- 提取的主题
    entities JSONB,                           -- 提取的实体
    events JSONB,                             -- 提取的事件
    impact_level VARCHAR(20),                 -- high/medium/low
    affected_assets JSONB,                    -- 受影响的资产
    published_at TIMESTAMP,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE news_sentiment IS '财经新闻情感分析结果';

-- ============================================================================
-- 5. 市场实时数据表
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_quotes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(30) NOT NULL,
    name VARCHAR(100),
    asset_class VARCHAR(20),                  -- equity/bond/future/forex/commodity
    market VARCHAR(20),                       -- US/CN/EU/HK
    exchange VARCHAR(30),
    price DECIMAL(15,4),
    change DECIMAL(15,4),
    change_percent DECIMAL(8,4),
    volume BIGINT,
    turnover DECIMAL(18,2),
    high DECIMAL(15,4),
    low DECIMAL(15,4),
    open DECIMAL(15,4),
    previous_close DECIMAL(15,4),
    bid DECIMAL(15,4),
    ask DECIMAL(15,4),
    market_status VARCHAR(20),                -- open/closed/pre_market/after_hours
    quote_time TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, quote_time)
);

COMMENT ON TABLE market_quotes IS '全球市场实时行情数据';

-- ============================================================================
-- 6. AI Agent 执行日志表
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_execution_log (
    log_id VARCHAR(50) PRIMARY KEY,
    agent_type VARCHAR(50),                   -- macro_agent/strategy_agent/risk_agent
    query TEXT,
    response TEXT,
    tools_used JSONB,                         -- 使用的工具列表
    intermediate_steps JSONB,                 -- 中间步骤
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    model_name VARCHAR(50),
    status VARCHAR(20),                       -- success/failed/timeout
    error_message TEXT,
    user_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE agent_execution_log IS 'AI Agent执行日志';

-- ============================================================================
-- 7. 市场摘要表
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_summaries (
    id SERIAL PRIMARY KEY,
    market VARCHAR(20) NOT NULL,
    market_date DATE NOT NULL,
    main_index VARCHAR(30),
    index_value DECIMAL(15,4),
    index_change DECIMAL(8,4),
    advancing INTEGER,                        -- 上涨家数
    declining INTEGER,                        -- 下跌家数
    unchanged INTEGER,
    total_volume BIGINT,
    total_turnover DECIMAL(20,2),
    market_breadth DECIMAL(5,4),              -- 市场宽度
    sentiment_index DECIMAL(5,4),             -- 情绪指数
    volatility_index DECIMAL(8,4),            -- 波动率指数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market, market_date)
);

COMMENT ON TABLE market_summaries IS '每日市场摘要统计';

-- ============================================================================
-- 8. 资金流向表
-- ============================================================================

CREATE TABLE IF NOT EXISTS capital_flow (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    market VARCHAR(20) NOT NULL,
    symbol VARCHAR(30),
    main_inflow DECIMAL(18,2),                -- 主力流入
    main_outflow DECIMAL(18,2),               -- 主力流出
    main_net DECIMAL(18,2),                   -- 主力净流入
    retail_inflow DECIMAL(18,2),              -- 散户流入
    retail_outflow DECIMAL(18,2),             -- 散户流出
    retail_net DECIMAL(18,2),                 -- 散户净流入
    north_inflow DECIMAL(18,2),               -- 北向资金流入 (A股)
    north_outflow DECIMAL(18,2),              -- 北向资金流出
    north_net DECIMAL(18,2),                  -- 北向资金净流入
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, market, symbol)
);

COMMENT ON TABLE capital_flow IS '资金流向数据';

-- ============================================================================
-- 9. 经济事件日历表
-- ============================================================================

CREATE TABLE IF NOT EXISTS economic_calendar (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_time TIME,
    country VARCHAR(20) NOT NULL,
    event_type VARCHAR(50),                   -- earnings/unlock/ipo/economic/dividend
    event_name VARCHAR(200),
    importance VARCHAR(10),                   -- high/normal/low
    symbol VARCHAR(30),
    previous_value DECIMAL(15,4),
    forecast_value DECIMAL(15,4),
    actual_value DECIMAL(15,4),
    description TEXT,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE economic_calendar IS '经济事件日历';

-- ============================================================================
-- 索引优化
-- ============================================================================

-- 美林时钟索引
CREATE INDEX IF NOT EXISTS idx_mc_judgments_country ON merrill_clock_judgments(country);
CREATE INDEX IF NOT EXISTS idx_mc_judgments_phase ON merrill_clock_judgments(phase);
CREATE INDEX IF NOT EXISTS idx_mc_judgments_time ON merrill_clock_judgments(judgment_time DESC);

-- 资产配置索引
CREATE INDEX IF NOT EXISTS idx_alloc_phase ON asset_allocations(phase);
CREATE INDEX IF NOT EXISTS idx_alloc_country ON asset_allocations(country);

-- 宏观指标索引
CREATE INDEX IF NOT EXISTS idx_macro_country ON macro_indicators(country);
CREATE INDEX IF NOT EXISTS idx_macro_category ON macro_indicators(category);
CREATE INDEX IF NOT EXISTS idx_macro_date ON macro_indicators(data_date DESC);

-- 新闻情感索引
CREATE INDEX IF NOT EXISTS idx_news_sentiment_score ON news_sentiment(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_sentiment(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_impact ON news_sentiment(impact_level);

-- 市场行情索引
CREATE INDEX IF NOT EXISTS idx_quotes_symbol ON market_quotes(symbol);
CREATE INDEX IF NOT EXISTS idx_quotes_asset_class ON market_quotes(asset_class);
CREATE INDEX IF NOT EXISTS idx_quotes_market ON market_quotes(market);
CREATE INDEX IF NOT EXISTS idx_quotes_time ON market_quotes(quote_time DESC);

-- Agent日志索引
CREATE INDEX IF NOT EXISTS idx_agent_type ON agent_execution_log(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_timestamp ON agent_execution_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_status ON agent_execution_log(status);

-- 资金流向索引
CREATE INDEX IF NOT EXISTS idx_capital_date ON capital_flow(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_capital_market ON capital_flow(market);

-- 事件日历索引
CREATE INDEX IF NOT EXISTS idx_calendar_date ON economic_calendar(event_date);
CREATE INDEX IF NOT EXISTS idx_calendar_country ON economic_calendar(country);
CREATE INDEX IF NOT EXISTS idx_calendar_type ON economic_calendar(event_type);

COMMIT;

-- ============================================================================
-- 验证
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'merrill_clock_judgments',
        'asset_allocations',
        'macro_indicators',
        'news_sentiment',
        'market_quotes',
        'agent_execution_log',
        'market_summaries',
        'capital_flow',
        'economic_calendar'
    );

    RAISE NOTICE '市场动态模块数据表创建完成，共 % 张表', table_count;
END $$;
