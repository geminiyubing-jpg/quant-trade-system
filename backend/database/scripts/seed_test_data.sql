-- ============================================================
-- Quant-Trade System - 测试数据初始化 SQL 脚本
--
-- 用法:
--   psql -h localhost -U quant_trio -d quant_trio -f seed_test_data.sql
--
-- 或者使用环境变量:
--   psql $DATABASE_URL -f seed_test_data.sql
-- ============================================================

\echo '============================================================'
\echo '🌱 Quant-Trade System - 测试数据初始化'
\echo '============================================================'

-- ============================================================
-- 1. 清理现有测试数据（可选，取消注释以启用）
-- ============================================================
-- \echo '⚠️  清理现有测试数据...'
-- DELETE FROM backtest_results;
-- DELETE FROM backtest_jobs;
-- DELETE FROM orders;
-- DELETE FROM positions;
-- DELETE FROM backtests;
-- DELETE FROM strategies;
-- DELETE FROM stock_prices;
-- DELETE FROM stocks;
-- DELETE FROM users;

-- ============================================================
-- 2. 插入测试用户
-- ============================================================
\echo ''
\echo '👤 插入测试用户...'

-- 密码都是 'admin123', 'trader123', 'analyst123' (bcrypt hash)
INSERT INTO users (id, username, email, hashed_password, full_name, role, is_active, is_superuser, preferences)
VALUES
    ('test-user-001', 'admin', 'admin@quant-trade.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.aOy6.Xqt8F.qAu', '系统管理员', 'admin', true, true, '{}'),
    ('test-user-002', 'trader_zhang', 'zhang@quant-trade.com', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', '张三', 'trader', true, false, '{}'),
    ('test-user-003', 'analyst_li', 'li@quant-trade.com', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', '李四', 'analyst', true, false, '{}')
ON CONFLICT (username) DO NOTHING;

\echo '   ✅ 插入测试用户完成'

-- ============================================================
-- 3. 插入测试股票
-- ============================================================
\echo ''
\echo '📈 插入测试股票...'

INSERT INTO stocks (symbol, name, sector, industry, market, is_active) VALUES
    -- 金融
    ('000001.SZ', '平安银行', '金融', '银行', 'SZSE', true),
    ('600036.SH', '招商银行', '金融', '银行', 'SHSE', true),
    ('601318.SH', '中国平安', '金融', '保险', 'SHSE', true),
    ('600030.SH', '中信证券', '金融', '证券', 'SHSE', true),
    -- 科技
    ('000063.SZ', '中兴通讯', '科技', '通信设备', 'SZSE', true),
    ('002415.SZ', '海康威视', '科技', '电子设备', 'SZSE', true),
    ('300750.SZ', '宁德时代', '科技', '新能源', 'SZSE', true),
    ('688981.SH', '中芯国际', '科技', '半导体', 'SHSE', true),
    -- 消费
    ('000858.SZ', '五粮液', '消费', '白酒', 'SZSE', true),
    ('000568.SZ', '泸州老窖', '消费', '白酒', 'SZSE', true),
    ('600887.SH', '伊利股份', '消费', '食品饮料', 'SHSE', true),
    ('002304.SZ', '洋河股份', '消费', '白酒', 'SZSE', true),
    -- 医药
    ('000538.SZ', '云南白药', '医药', '中药', 'SZSE', true),
    ('600276.SH', '恒瑞医药', '医药', '化学制药', 'SHSE', true),
    ('300760.SZ', '迈瑞医疗', '医药', '医疗器械', 'SZSE', true),
    ('002007.SZ', '华兰生物', '医药', '生物制品', 'SZSE', true),
    -- 新能源
    ('600900.SH', '长江电力', '新能源', '电力', 'SHSE', true),
    ('601012.SH', '隆基绿能', '新能源', '光伏', 'SHSE', true),
    ('002594.SZ', '比亚迪', '新能源', '新能源汽车', 'SZSE', true),
    -- 地产
    ('000002.SZ', '万科A', '房地产', '房地产开发', 'SZSE', true),
    ('600048.SH', '保利发展', '房地产', '房地产开发', 'SHSE', true),
    -- 基准指数
    ('000001.SH', '上证指数', '指数', '宽基指数', 'SHSE', true),
    ('399001.SZ', '深证成指', '指数', '宽基指数', 'SZSE', true),
    ('000300.SH', '沪深300', '指数', '宽基指数', 'SHSE', true)
ON CONFLICT (symbol) DO NOTHING;

\echo '   ✅ 插入测试股票完成'

-- ============================================================
-- 4. 插入股票历史价格（最近60天）
-- ============================================================
\echo ''
\echo '📊 插入股票历史价格...'

-- 为每只股票生成60天的历史数据
-- 使用 generate_series 生成日期序列
DO $$
DECLARE
    stock_rec RECORD;
    base_price NUMERIC;
    current_price NUMERIC;
    day_offset INT;
    price_change NUMERIC;
    high_price NUMERIC;
    low_price NUMERIC;
    open_price NUMERIC;
    volume BIGINT;
    amount NUMERIC;
    price_date TIMESTAMP;
BEGIN
    FOR stock_rec IN SELECT symbol FROM stocks LOOP
        -- 设置基础价格
        CASE stock_rec.symbol
            WHEN '000001.SZ' THEN base_price := 12.50;
            WHEN '600036.SH' THEN base_price := 35.80;
            WHEN '601318.SH' THEN base_price := 48.20;
            WHEN '600030.SH' THEN base_price := 22.15;
            WHEN '000063.SZ' THEN base_price := 28.90;
            WHEN '002415.SZ' THEN base_price := 32.50;
            WHEN '300750.SZ' THEN base_price := 185.00;
            WHEN '688981.SH' THEN base_price := 52.30;
            WHEN '000858.SZ' THEN base_price := 158.00;
            WHEN '000568.SZ' THEN base_price := 185.50;
            WHEN '600887.SH' THEN base_price := 28.80;
            WHEN '002304.SZ' THEN base_price := 108.00;
            WHEN '000538.SZ' THEN base_price := 52.80;
            WHEN '600276.SH' THEN base_price := 42.50;
            WHEN '300760.SZ' THEN base_price := 295.00;
            WHEN '002007.SZ' THEN base_price := 25.60;
            WHEN '600900.SH' THEN base_price := 28.50;
            WHEN '601012.SH' THEN base_price := 25.80;
            WHEN '002594.SZ' THEN base_price := 268.00;
            WHEN '000002.SZ' THEN base_price := 8.50;
            WHEN '600048.SH' THEN base_price := 10.20;
            WHEN '000001.SH' THEN base_price := 3150.00;
            WHEN '399001.SZ' THEN base_price := 9850.00;
            WHEN '000300.SH' THEN base_price := 3680.00;
            ELSE base_price := 10.00;
        END CASE;

        current_price := base_price;

        -- 检查是否已有数据
        IF EXISTS (SELECT 1 FROM stock_prices WHERE symbol = stock_rec.symbol LIMIT 1) THEN
            CONTINUE;
        END IF;

        FOR day_offset IN 0..59 LOOP
            -- 随机波动 -3% 到 +3%
            price_change := (random() * 0.06 - 0.03);
            current_price := current_price * (1 + price_change);

            -- 确保价格为正
            IF current_price <= 0 THEN
                current_price := base_price * 0.5;
            END IF;

            -- 日内波动
            high_price := current_price * (1 + random() * 0.02);
            low_price := current_price * (1 - random() * 0.02);
            open_price := current_price * (1 + (random() - 0.5) * 0.02);

            -- 成交量
            volume := (500000 + floor(random() * 4500000))::BIGINT;
            amount := current_price * volume;

            -- 日期
            price_date := NOW() - INTERVAL '59 days' + (day_offset || ' days')::INTERVAL;

            -- 插入数据
            INSERT INTO stock_prices (symbol, price_open, price_close, price_high, price_low, volume, amount, timestamp)
            VALUES (stock_rec.symbol, ROUND(open_price, 2), ROUND(current_price, 2), ROUND(high_price, 2), ROUND(low_price, 2), volume, ROUND(amount, 2), price_date);
        END LOOP;
    END LOOP;
END $$;

\echo '   ✅ 插入股票历史价格完成'

-- ============================================================
-- 5. 插入测试策略
-- ============================================================
\echo ''
\echo '🧠 插入测试策略...'

INSERT INTO strategies (id, user_id, name, description, status, code, parameters, created_by, updated_by, version)
VALUES
    ('strategy-001'::uuid, 'test-user-002'::uuid, '双均线交叉策略', '基于5日和20日均线交叉的趋势跟踪策略，金叉买入，死叉卖出', 'ACTIVE',
     'def execute(context):
    short_ma = get_ma(context.symbol, 5)
    long_ma = get_ma(context.symbol, 20)
    if short_ma > long_ma and context.position == 0:
        buy(context.symbol, context.cash * 0.8)
    elif short_ma < long_ma and context.position > 0:
        sell(context.symbol, context.position)',
     '{"short_period": 5, "long_period": 20, "position_ratio": 0.8}'::jsonb,
     'test-user-002'::uuid, 'test-user-002'::uuid, 1),

    ('strategy-002'::uuid, 'test-user-002'::uuid, 'RSI超卖反弹策略', '利用RSI指标识别超卖反弹机会，RSI低于30买入，高于70卖出', 'ACTIVE',
     'def execute(context):
    rsi = get_rsi(context.symbol, 14)
    if rsi < 30 and context.position == 0:
        buy(context.symbol, context.cash * 0.6)
    elif rsi > 70 and context.position > 0:
        sell(context.symbol, context.position)',
     '{"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70}'::jsonb,
     'test-user-002'::uuid, 'test-user-002'::uuid, 1),

    ('strategy-003'::uuid, 'test-user-002'::uuid, '布林带突破策略', '基于布林带的突破策略，突破上轨买入，跌破下轨止损', 'DRAFT',
     'def execute(context):
    upper, middle, lower = get_bollinger(context.symbol, 20, 2)
    if context.close_price > upper and context.position == 0:
        buy(context.symbol, context.cash * 0.5)
    elif context.close_price < lower and context.position > 0:
        sell(context.symbol, context.position)',
     '{"period": 20, "std_dev": 2.0}'::jsonb,
     'test-user-002'::uuid, 'test-user-002'::uuid, 1),

    ('strategy-004'::uuid, 'test-user-002'::uuid, 'MACD趋势策略', '基于MACD指标的趋势跟踪策略，DIF上穿DEA买入', 'ACTIVE',
     'def execute(context):
    dif, dea, macd = get_macd(context.symbol, 12, 26, 9)
    if dif > dea and macd > 0 and context.position == 0:
        buy(context.symbol, context.cash * 0.7)
    elif dif < dea and context.position > 0:
        sell(context.symbol, context.position)',
     '{"fast_period": 12, "slow_period": 26, "signal_period": 9}'::jsonb,
     'test-user-002'::uuid, 'test-user-002'::uuid, 1),

    ('strategy-005'::uuid, 'test-user-002'::uuid, '多因子量化策略', '综合动量、价值、质量等多因子的选股策略', 'PAUSED',
     'def execute(context):
    factors = calc_factors(context.symbol)
    score = factors["momentum"] * 0.3 + factors["value"] * 0.25
    if score > 0.6 and context.position == 0:
        buy(context.symbol, context.cash * 0.8)
    elif score < 0.4 and context.position > 0:
        sell(context.symbol, context.position)',
     '{"factors": ["momentum", "value", "quality"], "weights": [0.3, 0.25, 0.25]}'::jsonb,
     'test-user-002'::uuid, 'test-user-002'::uuid, 1)
ON CONFLICT (id) DO NOTHING;

\echo '   ✅ 插入测试策略完成'

-- ============================================================
-- 6. 插入回测任务和结果
-- ============================================================
\echo ''
\echo '🔬 插入回测任务和结果...'

INSERT INTO backtest_jobs (id, strategy_id, name, status, config, result, progress, created_by, created_at, completed_at)
VALUES
    ('backtest-job-001', 'strategy-001', '双均线交叉策略 - 历史回测1', 'COMPLETED',
     '{"start_date": "2024-01-01", "end_date": "2024-12-31", "initial_capital": 1000000}'::jsonb,
     '{"total_return": 0.25, "sharpe_ratio": 1.5, "max_drawdown": 0.15}'::jsonb,
     100, 'test-user-002', NOW() - INTERVAL '10 days', NOW() - INTERVAL '9 days'),

    ('backtest-job-002', 'strategy-002', 'RSI超卖反弹策略 - 历史回测1', 'COMPLETED',
     '{"start_date": "2024-01-01", "end_date": "2024-12-31", "initial_capital": 1000000}'::jsonb,
     '{"total_return": 0.18, "sharpe_ratio": 1.2, "max_drawdown": 0.12}'::jsonb,
     100, 'test-user-002', NOW() - INTERVAL '8 days', NOW() - INTERVAL '7 days'),

    ('backtest-job-003', 'strategy-004', 'MACD趋势策略 - 历史回测1', 'COMPLETED',
     '{"start_date": "2024-01-01", "end_date": "2024-12-31", "initial_capital": 1000000}'::jsonb,
     '{"total_return": 0.32, "sharpe_ratio": 1.8, "max_drawdown": 0.18}'::jsonb,
     100, 'test-user-002', NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days')
ON CONFLICT (id) DO NOTHING;

-- 插入回测结果
INSERT INTO backtest_results (job_id, strategy_id, start_date, end_date, initial_capital, final_capital,
    total_return, annual_return, sharpe_ratio, sortino_ratio, max_drawdown,
    win_rate, total_trades, winning_trades, losing_trades, avg_trade, profit_factor, created_at)
VALUES
    ('backtest-job-001', 'strategy-001', '2024-01-01', '2024-12-31', 1000000, 1250000,
     0.25, 0.28, 1.5, 1.3, 0.15, 0.58, 45, 26, 19, 3500, 1.45, NOW()),
    ('backtest-job-002', 'strategy-002', '2024-01-01', '2024-12-31', 1000000, 1180000,
     0.18, 0.20, 1.2, 1.0, 0.12, 0.52, 38, 20, 18, 2800, 1.25, NOW()),
    ('backtest-job-003', 'strategy-004', '2024-01-01', '2024-12-31', 1000000, 1320000,
     0.32, 0.35, 1.8, 1.6, 0.18, 0.62, 52, 32, 20, 4200, 1.68, NOW());

\echo '   ✅ 插入回测任务和结果完成'

-- ============================================================
-- 7. 插入测试订单
-- ============================================================
\echo ''
\echo '📝 插入测试订单...'

INSERT INTO orders (id, strategy_id, ts_code, user_id, execution_mode, side, order_type, quantity, price, filled_quantity, avg_price, status, create_time, update_time)
VALUES
    ('order-0001', 'strategy-001', '000001.SZ', 'test-user-002', 'PAPER', 'BUY', 'LIMIT', 1000, 12.50, 1000, 12.50, 'FILLED', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days'),
    ('order-0002', 'strategy-001', '600036.SH', 'test-user-002', 'PAPER', 'BUY', 'LIMIT', 500, 35.80, 500, 35.80, 'FILLED', NOW() - INTERVAL '4 days', NOW() - INTERVAL '4 days'),
    ('order-0003', 'strategy-001', '000858.SZ', 'test-user-002', 'PAPER', 'BUY', 'LIMIT', 200, 158.00, 200, 158.00, 'FILLED', NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days'),
    ('order-0004', 'strategy-002', '002415.SZ', 'test-user-002', 'PAPER', 'BUY', 'LIMIT', 800, 32.50, 800, 32.50, 'FILLED', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),
    ('order-0005', 'strategy-002', '300750.SZ', 'test-user-002', 'PAPER', 'BUY', 'LIMIT', 100, 185.00, 100, 185.00, 'FILLED', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
    ('order-0006', 'strategy-001', '000001.SZ', 'test-user-002', 'PAPER', 'SELL', 'LIMIT', 500, 13.00, 0, NULL, 'PENDING', NOW(), NOW()),
    ('order-0007', 'strategy-004', '600030.SH', 'test-user-002', 'PAPER', 'BUY', 'MARKET', 1000, 22.00, 1000, 22.15, 'FILLED', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '6 hours'),
    ('order-0008', 'strategy-004', '601318.SH', 'test-user-002', 'PAPER', 'BUY', 'LIMIT', 300, 48.00, 150, 48.10, 'PARTIAL', NOW() - INTERVAL '3 hours', NOW()),
    ('order-0009', 'strategy-001', '600036.SH', 'test-user-002', 'PAPER', 'SELL', 'LIMIT', 200, 36.50, 0, NULL, 'CANCELED', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
    ('order-0010', 'strategy-002', '002415.SZ', 'test-user-002', 'PAPER', 'SELL', 'LIMIT', 400, 33.50, 0, NULL, 'PENDING', NOW(), NOW())
ON CONFLICT DO NOTHING;

\echo '   ✅ 插入测试订单完成'

-- ============================================================
-- 8. 插入测试持仓
-- ============================================================
\echo ''
\echo '💼 插入测试持仓...'

INSERT INTO positions (strategy_id, stock_symbol, user_id, execution_mode, quantity, avg_cost, current_price, market_value, unrealized_pnl, opened_at, status)
VALUES
    ('strategy-001', '000001.SZ', 'test-user-002', 'PAPER', 500, 12.50, 12.80, 6400, 150, NOW() - INTERVAL '5 days', 'open'),
    ('strategy-001', '600036.SH', 'test-user-002', 'PAPER', 500, 35.80, 36.20, 18100, 200, NOW() - INTERVAL '4 days', 'open'),
    ('strategy-001', '000858.SZ', 'test-user-002', 'PAPER', 200, 158.00, 162.50, 32500, 900, NOW() - INTERVAL '3 days', 'open'),
    ('strategy-002', '002415.SZ', 'test-user-002', 'PAPER', 800, 32.50, 31.80, 25440, -560, NOW() - INTERVAL '2 days', 'open'),
    ('strategy-002', '300750.SZ', 'test-user-002', 'PAPER', 100, 185.00, 192.50, 19250, 750, NOW() - INTERVAL '1 day', 'open'),
    ('strategy-004', '600030.SH', 'test-user-002', 'PAPER', 1000, 22.15, 22.50, 22500, 350, NOW() - INTERVAL '6 hours', 'open')
ON CONFLICT DO NOTHING;

\echo '   ✅ 插入测试持仓完成'

-- ============================================================
-- 9. 数据统计
-- ============================================================
\echo ''
\echo '🔍 测试数据统计:'
\echo '============================================================'

SELECT '   用户: ' || COUNT(*) || ' 条记录' as stat FROM users
UNION ALL
SELECT '   股票: ' || COUNT(*) || ' 条记录' FROM stocks
UNION ALL
SELECT '   股票价格: ' || COUNT(*) || ' 条记录' FROM stock_prices
UNION ALL
SELECT '   策略: ' || COUNT(*) || ' 条记录' FROM strategies
UNION ALL
SELECT '   回测任务: ' || COUNT(*) || ' 条记录' FROM backtest_jobs
UNION ALL
SELECT '   回测结果: ' || COUNT(*) || ' 条记录' FROM backtest_results
UNION ALL
SELECT '   订单: ' || COUNT(*) || ' 条记录' FROM orders
UNION ALL
SELECT '   持仓: ' || COUNT(*) || ' 条记录' FROM positions;

\echo ''
\echo '============================================================'
\echo '✅ 测试数据初始化完成！'
\echo '============================================================'
\echo ''
\echo '📋 测试账号信息:'
\echo '------------------------------------------------------------'
\echo '   用户名: admin       密码: admin123    角色: 管理员'
\echo '   用户名: trader_zhang 密码: trader123  角色: 交易员'
\echo '   用户名: analyst_li  密码: analyst123  角色: 分析师'
\echo '------------------------------------------------------------'
