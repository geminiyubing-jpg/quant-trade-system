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
  return post<FactorAnalysis>(`${API_PREFIX}/${backtestId}/analysis/factor`, params);
}

/**
 * 获取因子分析结果
 */
export async function getFactorAnalysis(backtestId: string): Promise<FactorAnalysis> {
  return get<FactorAnalysis>(`${API_PREFIX}/${backtestId}/analysis/factor`);
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
  return post<AttributionAnalysis>(`${API_PREFIX}/${backtestId}/analysis/attribution`, params);
}

/**
 * 获取归因分析结果
 */
export async function getAttributionAnalysis(backtestId: string): Promise<AttributionAnalysis> {
  return get<AttributionAnalysis>(`${API_PREFIX}/${backtestId}/analysis/attribution`);
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
  // 因子分析
  runFactorAnalysis,
  getFactorAnalysis,
  // 归因分析
  runAttributionAnalysis,
  getAttributionAnalysis,
};

export default backtestService;
