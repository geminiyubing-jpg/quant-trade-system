-- ============================================================================
-- Quant-Trade System - 性能优化索引
-- 版本: v1.0.0
-- 创建日期: 2026-03-11
-- 描述: 为常用查询添加复合索引，提升查询性能
-- ============================================================================

-- 开始事务
BEGIN;

-- ============================================================================
-- 1. 用户相关索引
-- ============================================================================

-- 用户登录查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_status
ON users(email, status) WHERE status = 'ACTIVE';

-- 用户会话查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_user_expires
ON user_sessions(user_id, expires_at DESC);

-- ============================================================================
-- 2. 策略相关索引
-- ============================================================================

-- 策略版本查询（按策略ID和时间）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategy_versions_strategy_created
ON strategy_versions(strategy_id, created_at DESC);

-- 策略版本查询（按状态）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategy_versions_status
ON strategy_versions(status, created_at DESC) WHERE status = 'ACTIVE';

-- 策略配置查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategy_configs_strategy_version
ON strategy_configs(strategy_id, version_id);

-- 策略审计日志
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategy_audit_strategy_time
ON strategy_audit_log(strategy_id, created_at DESC);

-- ============================================================================
-- 3. 订单和交易相关索引
-- ============================================================================

-- 订单查询（按用户和状态）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_status
ON orders(user_id, status, created_at DESC);

-- 订单查询（按策略）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_strategy_created
ON orders(strategy_id, created_at DESC);

-- 订单查询（按股票代码）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_symbol_status
ON orders(symbol, status, created_at DESC);

-- 订单查询（按执行模式）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_execution_mode
ON orders(execution_mode, status, created_at DESC);

-- 成交记录查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fills_order_created
ON fills(order_id, created_at DESC);

-- 成交记录统计（按日期）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fills_user_date
ON fills(user_id, DATE(created_at));

-- 交易日历查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trading_calendar_date
ON trading_calendar(trade_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trading_calendar_month
ON trading_calendar(EXTRACT(YEAR FROM trade_date), EXTRACT(MONTH FROM trade_date));

-- 日交易统计
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_daily_trade_stats_user_date
ON daily_trade_stats(user_id, trade_date DESC);

-- ============================================================================
-- 4. 回测相关索引
-- ============================================================================

-- 回测任务查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backtests_strategy_status
ON backtests(strategy_id, status, created_at DESC);

-- 回测任务查询（按用户）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backtests_user_created
ON backtests(user_id, created_at DESC);

-- 回测结果查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backtest_results_backtest
ON backtest_results(backtest_id, trade_date);

-- 因子分析结果
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_factor_analyses_backtest
ON factor_analyses(backtest_id);

-- 归因分析结果
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attribution_analyses_backtest
ON attribution_analyses(backtest_id);

-- ============================================================================
-- 5. 投资组合相关索引
-- ============================================================================

-- 组合查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolios_user_status
ON portfolios(user_id, status, updated_at DESC);

-- 持仓查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_positions_portfolio
ON portfolio_positions(portfolio_id, symbol);

-- 持仓历史
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_positions_date
ON portfolio_positions(portfolio_id, as_of_date DESC);

-- 组合风险指标
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_risk_metrics_date
ON portfolio_risk_metrics(portfolio_id, calculated_at DESC);

-- 组合优化记录
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_optimizations_date
ON portfolio_optimizations(portfolio_id, created_at DESC);

-- ============================================================================
-- 6. 行情数据索引
-- ============================================================================

-- 股票行情（按代码和日期）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stock_quotes_symbol_date
ON stock_quotes(symbol, trade_date DESC);

-- 实时行情缓存
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_realtime_quotes_symbol
ON realtime_quotes(symbol, updated_at DESC);

-- 自选股查询
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_watchlists_user
ON watchlists(user_id, created_at DESC);

-- 自选股项目
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_watchlist_stocks_watchlist
ON watchlist_stocks(watchlist_id, symbol);

-- 价格预警
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_price_alerts_user_status
ON price_alerts(user_id, status, created_at DESC);

-- 价格预警触发检查
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_price_alerts_symbol_status
ON price_alerts(symbol, status) WHERE status = 'ACTIVE';

-- ============================================================================
-- 7. 风控相关索引
-- ============================================================================

-- 风控规则
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_risk_rules_user_status
ON risk_rules(user_id, status, updated_at DESC);

-- 风控事件
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_risk_events_user_time
ON risk_events(user_id, created_at DESC);

-- 风控事件（按严重程度）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_risk_events_severity
ON risk_events(severity, created_at DESC) WHERE severity IN ('HIGH', 'CRITICAL');

-- 持仓限制
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_position_limits_user
ON position_limits(user_id, effective_date DESC);

-- 止损订单
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stop_loss_orders_status
ON stop_loss_orders(status, created_at DESC);

-- ============================================================================
-- 8. 数据管理相关索引
-- ============================================================================

-- 数据导入任务
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_import_jobs_status
ON data_import_jobs(status, created_at DESC);

-- 数据质量报告
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_quality_reports_date
ON data_quality_reports(report_date DESC);

-- ETL 任务
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_etl_tasks_status
ON etl_tasks(status, scheduled_at);

-- ============================================================================
-- 9. AI 和分析相关索引
-- ============================================================================

-- AI 分析结果
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analysis_user_type
ON ai_analyses(user_id, analysis_type, created_at DESC);

-- 模型配置
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_model_configs_type_status
ON model_configs(model_type, status);

-- ============================================================================
-- 10. 审计日志索引
-- ============================================================================

-- 操作日志
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_time
ON audit_logs(user_id, created_at DESC);

-- 操作日志（按操作类型）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_action
ON audit_logs(action, created_at DESC);

-- 系统日志
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_logs_level_time
ON system_logs(level, created_at DESC) WHERE level IN ('ERROR', 'WARNING');

-- ============================================================================
-- 11. 部分索引（优化特定查询）
-- ============================================================================

-- 活跃订单（常用查询）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_active
ON orders(user_id, created_at DESC)
WHERE status IN ('PENDING', 'SUBMITTED', 'PARTIAL_FILLED');

-- 待处理回测任务
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backtests_pending
ON backtests(created_at)
WHERE status = 'PENDING';

-- 活跃预警
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_active
ON price_alerts(symbol, target_price)
WHERE status = 'ACTIVE';

-- 未读通知
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_unread
ON notifications(user_id, created_at DESC)
WHERE read_at IS NULL;

-- 提交事务
COMMIT;

-- ============================================================================
-- 分析表（更新统计信息）
-- ============================================================================

ANALYZE users;
ANALYZE strategy_versions;
ANALYZE orders;
ANALYZE fills;
ANALYZE backtests;
ANALYZE portfolios;
ANALYZE portfolio_positions;
ANALYZE stock_quotes;
ANALYZE watchlists;
ANALYZE price_alerts;
ANALYZE risk_events;

-- ============================================================================
-- 验证索引创建
-- ============================================================================

DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%';

    RAISE NOTICE '性能优化索引创建完成，共 % 个自定义索引', index_count;
END $$;
