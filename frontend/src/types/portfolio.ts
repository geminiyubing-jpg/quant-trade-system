/**
 * 投资组合相关类型定义
 */

// 投资组合状态
export type PortfolioStatus = 'ACTIVE' | 'PAUSED' | 'CLOSED';

// 优化方法
export type OptimizationMethod =
  | 'MEAN_VARIANCE'
  | 'RISK_PARITY'
  | 'MIN_VARIANCE'
  | 'MAX_SHARPE'
  | 'EQUAL_WEIGHT'
  | 'BLACK_LITTERMAN';

// 投资组合
export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  benchmark_symbol?: string;
  target_allocation?: Record<string, number>;
  rebalance_threshold: number;
  rebalance_frequency: string;
  execution_mode: string;
  initial_capital?: number;
  base_currency: string;
  status: PortfolioStatus;
  total_value: number;
  cash_balance: number;
  inception_date?: string;
  created_at: string;
  updated_at: string;
}

// 投资组合列表响应
export interface PortfolioListResponse {
  total: number;
  items: Portfolio[];
}

// 创建投资组合请求
export interface PortfolioCreate {
  name: string;
  description?: string;
  benchmark_symbol?: string;
  target_allocation?: Record<string, number>;
  rebalance_threshold?: number;
  rebalance_frequency?: string;
  execution_mode?: string;
  initial_capital?: number;
}

// 更新投资组合请求
export interface PortfolioUpdate {
  name?: string;
  description?: string;
  benchmark_symbol?: string;
  target_allocation?: Record<string, number>;
  rebalance_threshold?: number;
  rebalance_frequency?: string;
  status?: PortfolioStatus;
}

// 组合持仓
export interface PortfolioPosition {
  id: string;
  portfolio_id: string;
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_price?: number;
  market_value?: number;
  weight?: number;
  target_weight?: number;
  unrealized_pnl?: number;
  realized_pnl?: number;
  sector?: string;
  industry?: string;
  status: string;
}

// 持仓列表响应
export interface PositionListResponse {
  total: number;
  items: PortfolioPosition[];
}

// 风险指标
export interface RiskMetrics {
  id: string;
  portfolio_id: string;
  calculation_date: string;
  var_95?: number;
  var_99?: number;
  cvar_95?: number;
  herfindahl_index?: number;
  max_single_weight?: number;
  top_5_weight?: number;
  top_10_weight?: number;
  diversification_ratio?: number;
  beta_to_benchmark?: number;
  portfolio_volatility?: number;
  max_drawdown?: number;
  created_at: string;
}

// 优化结果
export interface OptimizationResult {
  id: string;
  portfolio_id: string;
  optimization_method: OptimizationMethod;
  current_weights?: Record<string, number>;
  optimal_weights?: Record<string, number>;
  expected_return?: number;
  expected_risk?: number;
  expected_sharpe?: number;
  rebalance_trades?: Array<{
    symbol: string;
    action: string;
    quantity: number;
  }>;
  estimated_transaction_cost?: number;
  status: string;
}

// 优化历史列表响应
export interface OptimizationListResponse {
  total: number;
  items: OptimizationResult[];
}

// 优化请求
export interface OptimizeRequest {
  method: OptimizationMethod;
  constraints?: {
    max_weight?: number;
    min_weight?: number;
    sector_limits?: Record<string, number>;
  };
}

// 绩效指标
export interface PerformanceMetrics {
  portfolio_id: string;
  calculation_date: string;
  start_date: string;
  end_date: string;
  // 收益指标
  total_return: number;
  annualized_return: number;
  benchmark_return?: number;
  // 风险指标
  annualized_volatility: number;
  downside_volatility?: number;
  max_drawdown: number;
  // 风险调整收益
  sharpe_ratio: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  information_ratio?: number;
  treynor_ratio?: number;
  // Alpha/Beta
  alpha?: number;
  beta?: number;
  // 其他
  win_rate?: number;
  profit_loss_ratio?: number;
}

// 自定义基准
export interface CustomBenchmark {
  id: string;
  portfolio_id: string;
  name: string;
  description?: string;
  composition: Array<{
    symbol: string;
    weight: number;
  }>;
  rebalance_frequency: string;
  created_at: string;
}

// 归因分析结果
export interface AttributionResult {
  portfolio_id: string;
  period_start: string;
  period_end: string;
  total_return: number;
  benchmark_return: number;
  active_return: number;
  allocation_effect: number;
  selection_effect: number;
  interaction_effect: number;
  sector_attribution?: Array<{
    sector: string;
    allocation: number;
    selection: number;
    interaction: number;
    total: number;
  }>;
}
