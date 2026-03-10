/**
 * AI 服务 API
 *
 * 封装 /api/v1/ai/* 端点
 */

import { get, post } from './api';

const API_PREFIX = '/api/v1/ai';

// AI 服务状态
export interface AIServiceStatus {
  glm5_available: boolean;
  mcp_tools_count: number;
  mcp_tools: string[];
  status: string;
}

// 策略生成请求
export interface StrategyGenerateRequest {
  description: string;
  strategy_type?: string;
  risk_level?: 'low' | 'medium' | 'high';
}

// 策略生成响应
export interface StrategyGenerateResponse {
  success: boolean;
  code: string;
  explanation: string;
  parameters: Record<string, any>;
}

// 智能选股请求
export interface StockPickingRequest {
  market?: string;
  industry?: string;
  min_market_cap?: number;
  max_market_cap?: number;
  min_pe?: number;
  max_pe?: number;
  min_roe?: number;
  additional_filters?: Record<string, any>;
}

// 智能选股响应
export interface StockPickingResponse {
  success: boolean;
  stocks: Array<{
    symbol: string;
    name: string;
    score: number;
    reasons: string[];
  }>;
  total: number;
}

// 市场分析请求
export interface MarketAnalysisRequest {
  analysis_type: 'sentiment' | 'anomaly' | 'trend';
  symbols?: string[];
  date_range?: {
    start: string;
    end: string;
  };
}

// 市场分析响应
export interface MarketAnalysisResponse {
  success: boolean;
  analysis: string;
  insights: string[];
  recommendations: string[];
}

// AI 设置
export interface AISettings {
  api_key?: string;
  api_url: string;
  model: string;
  temperature?: number;
  max_tokens?: number;
}

// ==============================================
// AI 服务状态
// ==============================================

/**
 * 获取 AI 服务状态
 */
export async function getAIStatus(): Promise<AIServiceStatus> {
  return get<AIServiceStatus>(`${API_PREFIX}/status`);
}

// ==============================================
// 策略生成
// ==============================================

/**
 * 生成策略代码
 */
export async function generateStrategy(request: StrategyGenerateRequest): Promise<StrategyGenerateResponse> {
  return post<StrategyGenerateResponse>(`${API_PREFIX}/generate-strategy`, request);
}

// ==============================================
// 智能选股
// ==============================================

/**
 * 智能选股
 */
export async function pickStocks(request: StockPickingRequest): Promise<StockPickingResponse> {
  return post<StockPickingResponse>(`${API_PREFIX}/pick-stocks`, request);
}

// ==============================================
// 市场分析
// ==============================================

/**
 * 市场分析
 */
export async function analyzeMarket(request: MarketAnalysisRequest): Promise<MarketAnalysisResponse> {
  return post<MarketAnalysisResponse>(`${API_PREFIX}/analyze-market`, request);
}

// ==============================================
// AI 设置
// ==============================================

/**
 * 获取 AI 设置
 */
export async function getAISettings(): Promise<AISettings> {
  return get<AISettings>(`${API_PREFIX}/settings`);
}

/**
 * 更新 AI 设置
 */
export async function updateAISettings(settings: Partial<AISettings>): Promise<{ success: boolean }> {
  return post<{ success: boolean }>(`${API_PREFIX}/settings`, settings);
}

// 导出服务对象
export const aiService = {
  // 服务状态
  getAIStatus,
  // 策略生成
  generateStrategy,
  // 智能选股
  pickStocks,
  // 市场分析
  analyzeMarket,
  // 设置
  getAISettings,
  updateAISettings,
};

export default aiService;
