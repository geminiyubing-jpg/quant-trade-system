/**
 * 回测 API 服务
 *
 * 封装 /api/v1/backtest/* 端点
 */

import { get, post, del } from './api';
import type {
  BacktestResult,
  BacktestListResponse,
  CreateBacktestRequest,
  FactorAnalysis,
  AttributionAnalysis,
  ExtendedMetrics,
} from '../types/backtest';

const API_PREFIX = '/api/v1/backtest';
const ANALYSIS_PREFIX = '/api/v1/backtest-analysis';

// ==============================================
// 回测管理
// ==============================================

/**
 * 运行回测
 */
export async function runBacktest(request: CreateBacktestRequest): Promise<BacktestResult> {
  return post<BacktestResult>(`${API_PREFIX}/run`, request);
}

/**
 * 获取回测结果列表
 */
export async function getBacktestResults(params?: {
  strategy_id?: string;
  status?: string;
  skip?: number;
  limit?: number;
}): Promise<BacktestListResponse> {
  const query = new URLSearchParams();
  if (params?.strategy_id) query.append('strategy_id', params.strategy_id);
  if (params?.status) query.append('status', params.status);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get<BacktestListResponse>(`${API_PREFIX}/results${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取单个回测结果
 */
export async function getBacktestResult(backtestId: string): Promise<BacktestResult> {
  return get<BacktestResult>(`${API_PREFIX}/${backtestId}`);
}

/**
 * 获取回测交易记录
 */
export async function getBacktestTrades(backtestId: string): Promise<{
  total: number;
  items: Array<{
    trade_id: string;
    symbol: string;
    side: string;
    quantity: number;
    price: number;
    amount: number;
    commission: number;
    timestamp: string;
    pnl?: number;
  }>;
}> {
  return get(`${API_PREFIX}/${backtestId}/trades`);
}

/**
 * 获取权益曲线
 */
export async function getEquityCurve(backtestId: string): Promise<{
  equity_curve: Array<{
    date: string;
    equity: number;
    drawdown: number;
    return_pct: number;
  }>;
}> {
  return get(`${API_PREFIX}/${backtestId}/equity-curve`);
}

/**
 * 获取扩展指标
 */
export async function getExtendedMetrics(backtestId: string): Promise<ExtendedMetrics> {
  return get<ExtendedMetrics>(`${API_PREFIX}/${backtestId}/metrics`);
}

/**
 * 删除回测结果
 */
export async function deleteBacktest(backtestId: string): Promise<void> {
  return del<void>(`${API_PREFIX}/${backtestId}`);
}

/**
 * 停止运行中的回测
 */
export async function stopBacktest(backtestId: string): Promise<void> {
  return post<void>(`${API_PREFIX}/${backtestId}/stop`);
}

// ==============================================
// 回测验证
// ==============================================

export interface ValidationRequest {
  backtest_id: string;
  equity_curve?: number[];
  daily_returns?: number[];
  trades?: Array<{
    symbol: string;
    side: string;
    quantity: number;
    price: number;
    timestamp: string;
    pnl?: number;
  }>;
}

export interface ValidationResult {
  backtest_id: string;
  overall_status: 'passed' | 'warning' | 'failed' | 'critical';
  overall_score: number;
  summary: {
    total_validations: number;
    passed: number;
    warnings: number;
    failed: number;
    critical: number;
  };
  validation_results: Array<{
    category: string;
    status: string;
    score: number;
    message: string;
    details: Record<string, unknown>;
    recommendations: string[];
  }>;
}

/**
 * 执行回测验证
 */
export async function validateBacktest(request: ValidationRequest): Promise<ValidationResult> {
  return post<ValidationResult>(`${ANALYSIS_PREFIX}/validate`, request);
}

/**
 * 获取验证报告
 */
export async function getValidationReport(backtestId: string): Promise<ValidationResult> {
  return get<ValidationResult>(`${ANALYSIS_PREFIX}/validate/${backtestId}`);
}

// ==============================================
// 风险分析
// ==============================================

export interface RiskAnalysisRequest {
  daily_returns: number[];
  positions?: Record<string, number>;
  benchmark_returns?: number[];
  factor_exposures?: Record<string, number>;
}

export interface RiskAnalysisResult {
  var_result: {
    var_95: number;
    var_99: number;
    cvar_95: number;
    cvar_99: number;
    method: string;
    daily_var: number;
    annual_var: number;
  };
  stress_tests: Array<{
    scenario_name: string;
    description: string;
    portfolio_impact: number;
    worst_case_impact: number;
    recovery_days: number;
  }>;
  risk_decomposition: {
    total_risk: number;
    systematic_risk: number;
    idiosyncratic_risk: number;
    concentration_risk: number;
    factor_contributions: Record<string, number>;
  };
  downside_risk: {
    downside_deviation: number;
    max_drawdown: number;
    max_drawdown_duration: number;
    recovery_factor: number;
    pain_index: number;
  };
  volatility_analysis: {
    total_volatility: number;
    upside_volatility: number;
    downside_volatility: number;
    volatility_ratio: number;
  };
  risk_summary: {
    key_metrics: Record<string, string>;
    risk_breakdown: Record<string, string>;
    worst_case_scenario: {
      name: string;
      impact: string;
    } | null;
    risk_alerts: string[];
  };
  risk_rating: 'Low' | 'Medium' | 'High' | 'Critical';
}

/**
 * 执行风险分析
 */
export async function analyzeRisk(request: RiskAnalysisRequest): Promise<RiskAnalysisResult> {
  return post<RiskAnalysisResult>(`${ANALYSIS_PREFIX}/risk-analysis`, request);
}

/**
 * 获取风险分析结果
 */
export async function getRiskAnalysis(backtestId: string): Promise<Partial<RiskAnalysisResult>> {
  return get<Partial<RiskAnalysisResult>>(`${ANALYSIS_PREFIX}/risk-analysis/${backtestId}`);
}

// ==============================================
// 因子分析
// ==============================================

/**
 * 执行因子分析
 */
export async function runFactorAnalysis(backtestId: string, params: {
  factor_name: string;
  signals: Array<{ date: string; symbol: string; signal_value: number; return: number }>;
  returns: Array<{ date: string; symbol: string; return: number }>;
}): Promise<FactorAnalysis> {
  return post<FactorAnalysis>(`${ANALYSIS_PREFIX}/results/${backtestId}/factor-analysis`, params);
}

/**
 * 获取因子分析结果
 */
export async function getFactorAnalysis(backtestId: string): Promise<FactorAnalysis[]> {
  return get<FactorAnalysis[]>(`${ANALYSIS_PREFIX}/results/${backtestId}/factor-analysis`);
}

// ==============================================
// 归因分析
// ==============================================

/**
 * 执行归因分析
 */
export async function runAttributionAnalysis(backtestId: string, params: {
  benchmark_symbol?: string;
  portfolio_weights: Array<{ date: string; symbol: string; weight: number }>;
  benchmark_weights: Array<{ date: string; symbol: string; weight: number }>;
  returns_data: Array<{ date: string; symbol: string; return: number }>;
}): Promise<AttributionAnalysis> {
  return post<AttributionAnalysis>(`${ANALYSIS_PREFIX}/results/${backtestId}/attribution`, params);
}

/**
 * 获取归因分析结果
 */
export async function getAttributionAnalysis(backtestId: string): Promise<AttributionAnalysis | null> {
  return get<AttributionAnalysis | null>(`${ANALYSIS_PREFIX}/results/${backtestId}/attribution`);
}

// 导出服务对象
export const backtestService = {
  // 回测管理
  runBacktest,
  getBacktestResults,
  getBacktestResult,
  getBacktestTrades,
  getEquityCurve,
  getExtendedMetrics,
  deleteBacktest,
  stopBacktest,
  // 回测验证
  validateBacktest,
  getValidationReport,
  // 风险分析
  analyzeRisk,
  getRiskAnalysis,
  // 因子分析
  runFactorAnalysis,
  getFactorAnalysis,
  // 归因分析
  runAttributionAnalysis,
  getAttributionAnalysis,
};

export default backtestService;
