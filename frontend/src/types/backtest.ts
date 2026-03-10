/**
 * 回测相关类型定义
 */

// 回测状态
export type BacktestStatus = 'completed' | 'running' | 'failed' | 'pending';

// 回测结果
export interface BacktestResult {
  backtest_id: string;
  strategy_id: string;
  strategy_name: string;
  symbols: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  annual_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  status: BacktestStatus;
  created_at: string;
  benchmark_symbol?: string;
  trades?: Trade[];
  equity_curve?: EquityCurvePoint[];
  metrics?: BacktestMetrics;
}

// 交易记录
export interface Trade {
  trade_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  amount: number;
  commission: number;
  timestamp: string;
  pnl?: number;
}

// 权益曲线点
export interface EquityCurvePoint {
  date: string;
  equity: number;
  drawdown: number;
  return_pct: number;
}

// 回测指标
export interface BacktestMetrics {
  total_return: number;
  annual_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  avg_trade_return?: number;
  avg_trade_duration?: number;
  volatility?: number;
  information_ratio?: number;
  alpha?: number;
  beta?: number;
  tracking_error?: number;
}

// 创建回测请求
export interface CreateBacktestRequest {
  strategy_id: string;
  strategy_name: string;
  symbols: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission_rate?: number;
  slippage_rate?: number;
  benchmark_symbol?: string;
}

// 回测列表响应
export interface BacktestListResponse {
  total: number;
  items: BacktestResult[];
}

// 因子分析结果
export interface FactorAnalysis {
  id: string;
  backtest_result_id: string;
  factor_name: string;
  ic_mean?: number;
  ic_std?: number;
  ic_ir?: number;
  ic_t_stat?: number;
  ic_positive_ratio?: number;
  factor_return?: number;
  factor_volatility?: number;
  avg_turnover?: number;
  long_short_return?: number;
  created_at: string;
}

// 归因分析结果
export interface AttributionAnalysis {
  id: string;
  backtest_result_id: string;
  benchmark_symbol?: string;
  allocation_effect?: number;
  selection_effect?: number;
  interaction_effect?: number;
  total_active_return?: number;
  benchmark_return?: number;
  created_at: string;
}

// 扩展指标
export interface ExtendedMetrics {
  sortino_ratio?: number;
  calmar_ratio?: number;
  treynor_ratio?: number;
  information_ratio?: number;
  alpha?: number;
  beta?: number;
  tracking_error?: number;
  downside_deviation?: number;
  max_consecutive_losses?: number;
  profit_factor?: number;
  avg_holding_days?: number;
  recovery_factor?: number;
  avg_turnover_rate?: number;
}
