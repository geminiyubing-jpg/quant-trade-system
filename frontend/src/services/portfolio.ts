/**
 * 投资组合 API 服务
 *
 * 封装 /api/v1/portfolios/* 端点
 */

import { get, post, put, del } from './api';
import type {
  Portfolio,
  PortfolioListResponse,
  PortfolioCreate,
  PortfolioUpdate,
  PositionListResponse,
  RiskMetrics,
  OptimizationResult,
  OptimizationListResponse,
  OptimizeRequest,
  PerformanceMetrics,
  CustomBenchmark,
  AttributionResult,
} from '../types/portfolio';

const API_PREFIX = '/api/v1/portfolios';

// ==============================================
// 投资组合管理
// ==============================================

/**
 * 获取投资组合列表
 */
export async function listPortfolios(): Promise<PortfolioListResponse> {
  return get<PortfolioListResponse>(API_PREFIX);
}

/**
 * 获取单个投资组合
 */
export async function getPortfolio(portfolioId: string): Promise<Portfolio> {
  return get<Portfolio>(`${API_PREFIX}/${portfolioId}`);
}

/**
 * 创建投资组合
 */
export async function createPortfolio(data: PortfolioCreate): Promise<Portfolio> {
  return post<Portfolio>(API_PREFIX, data);
}

/**
 * 更新投资组合
 */
export async function updatePortfolio(portfolioId: string, data: PortfolioUpdate): Promise<Portfolio> {
  return put<Portfolio>(`${API_PREFIX}/${portfolioId}`, data);
}

/**
 * 删除投资组合
 */
export async function deletePortfolio(portfolioId: string): Promise<void> {
  return del<void>(`${API_PREFIX}/${portfolioId}`);
}

// ==============================================
// 持仓管理
// ==============================================

/**
 * 获取组合持仓
 */
export async function getPositions(portfolioId: string): Promise<PositionListResponse> {
  return get<PositionListResponse>(`${API_PREFIX}/${portfolioId}/positions`);
}

// ==============================================
// 风险分析
// ==============================================

/**
 * 获取风险指标
 */
export async function getRiskMetrics(portfolioId: string): Promise<RiskMetrics> {
  return get<RiskMetrics>(`${API_PREFIX}/${portfolioId}/risk`);
}

// ==============================================
// 组合优化
// ==============================================

/**
 * 执行组合优化
 */
export async function optimizePortfolio(portfolioId: string, request: OptimizeRequest): Promise<OptimizationResult> {
  return post<OptimizationResult>(`${API_PREFIX}/${portfolioId}/optimize`, request);
}

/**
 * 获取优化历史
 */
export async function getOptimizationHistory(portfolioId: string): Promise<OptimizationListResponse> {
  return get<OptimizationListResponse>(`${API_PREFIX}/${portfolioId}/optimizations`);
}

/**
 * 执行再平衡
 */
export async function rebalancePortfolio(portfolioId: string): Promise<{
  success: boolean;
  message: string;
  trades: Array<{
    symbol: string;
    action: string;
    quantity: number;
  }>;
}> {
  return post(`${API_PREFIX}/${portfolioId}/rebalance`);
}

// ==============================================
// 绩效分析
// ==============================================

/**
 * 获取绩效指标
 */
export async function getPerformanceMetrics(
  portfolioId: string,
  startDate?: string,
  endDate?: string,
  benchmarkId?: string
): Promise<PerformanceMetrics> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (benchmarkId) params.append('benchmark_id', benchmarkId);
  const query = params.toString() ? `?${params.toString()}` : '';
  return get<PerformanceMetrics>(`${API_PREFIX}/${portfolioId}/performance${query}`);
}

/**
 * 创建自定义基准
 */
export async function createBenchmark(
  portfolioId: string,
  data: {
    name: string;
    description?: string;
    composition: Array<{ symbol: string; weight: number }>;
    rebalance_frequency?: string;
  }
): Promise<CustomBenchmark> {
  return post<CustomBenchmark>(`${API_PREFIX}/${portfolioId}/benchmarks`, data);
}

/**
 * 获取自定义基准列表
 */
export async function getBenchmarks(portfolioId: string): Promise<CustomBenchmark[]> {
  return get<CustomBenchmark[]>(`${API_PREFIX}/${portfolioId}/benchmarks`);
}

/**
 * 计算归因分析
 */
export async function calculateAttribution(
  portfolioId: string,
  startDate: string,
  endDate: string,
  benchmarkId?: string
): Promise<AttributionResult> {
  return post<AttributionResult>(`${API_PREFIX}/${portfolioId}/attribution`, {
    start_date: startDate,
    end_date: endDate,
    benchmark_id: benchmarkId,
  });
}

// 导出服务对象
export const portfolioService = {
  // 组合管理
  listPortfolios,
  getPortfolio,
  createPortfolio,
  updatePortfolio,
  deletePortfolio,
  // 持仓
  getPositions,
  // 风险
  getRiskMetrics,
  // 优化
  optimizePortfolio,
  getOptimizationHistory,
  rebalancePortfolio,
  // 绩效分析
  getPerformanceMetrics,
  createBenchmark,
  getBenchmarks,
  calculateAttribution,
};

export default portfolioService;
