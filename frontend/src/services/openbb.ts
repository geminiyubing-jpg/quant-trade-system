/**
 * OpenBB Platform 服务
 *
 * 提供访问 OpenBB Platform 数据的 API 接口
 * 包括：股票数据、宏观经济、技术分析等
 */

import { get } from './api';

// ==============================================
// 类型定义
// ==============================================

export interface EquityQuote {
  symbol: string;
  price: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
  change?: number;
  change_percent?: number;
  previous_close?: number;
  provider: string;
}

export interface HistoricalPrice {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adj_close?: number;
  provider?: string;
}

export interface HistoricalPriceResponse {
  symbol: string;
  data: HistoricalPrice[];
  provider: string;
  count: number;
}

export interface FundamentalsResponse {
  symbol: string;
  statement_type: string;
  period: string;
  data: Record<string, unknown>[];
  provider: string;
}

export interface MacroIndicatorResponse {
  indicator: string;
  data: Record<string, unknown>[];
  provider: string;
  count: number;
}

export interface TechnicalIndicatorData {
  symbol: string;
  indicator: string;
  timestamp: string;
  [key: string]: string | number;
}

export interface TechnicalIndicatorResponse {
  symbol: string;
  indicators: string[];
  data: TechnicalIndicatorData[];
  provider: string;
  count: number;
}

export interface OpenBBStatus {
  name: string;
  description: string;
  is_connected: boolean;
  supported_types: string[];
  providers: {
    equity: boolean;
    economy: boolean;
    technical: boolean;
  };
}

export interface ProvidersList {
  equity: {
    free: string[];
    paid: string[];
  };
  economy: {
    free: string[];
    paid: string[];
  };
  news: {
    paid: string[];
  };
}

// ==============================================
// API 服务
// ==============================================

const BASE_URL = '/api/v1/openbb';

export const openbbService = {
  // ==============================================
  // 股票数据
  // ==============================================

  /**
   * 获取股票实时报价
   */
  getEquityQuote: async (symbol: string, provider?: string): Promise<EquityQuote> => {
    const params = provider ? `?provider=${provider}` : '';
    return get<EquityQuote>(`${BASE_URL}/equity/quote/${symbol}${params}`);
  },

  /**
   * 获取股票历史价格
   */
  getEquityHistorical: async (
    symbol: string,
    startDate?: string,
    endDate?: string,
    provider?: string
  ): Promise<HistoricalPriceResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (provider) params.append('provider', provider);
    const queryString = params.toString();
    return get<HistoricalPriceResponse>(
      `${BASE_URL}/equity/historical/${symbol}${queryString ? `?${queryString}` : ''}`
    );
  },

  /**
   * 获取股票基本面数据
   */
  getEquityFundamentals: async (
    symbol: string,
    statementType: 'balance' | 'income' | 'cash' = 'balance',
    period: 'annual' | 'quarterly' = 'annual',
    provider?: string
  ): Promise<FundamentalsResponse> => {
    const params = new URLSearchParams();
    params.append('statement_type', statementType);
    params.append('period', period);
    if (provider) params.append('provider', provider);
    return get<FundamentalsResponse>(
      `${BASE_URL}/equity/fundamentals/${symbol}?${params.toString()}`
    );
  },

  /**
   * 获取股票估值指标
   */
  getEquityValuation: async (symbol: string, provider?: string): Promise<Record<string, unknown>> => {
    const params = provider ? `?provider=${provider}` : '';
    return get<Record<string, unknown>>(`${BASE_URL}/equity/valuation/${symbol}${params}`);
  },

  // ==============================================
  // 宏观经济数据
  // ==============================================

  /**
   * 获取宏观经济指标
   *
   * 常用指标:
   * - GDP: 国内生产总值
   * - CPI: 消费者物价指数
   * - UNRATE: 失业率
   * - FEDFUNDS: 联邦基金利率
   * - DGS10: 10年期国债收益率
   */
  getMacroIndicator: async (
    indicator: string,
    startDate?: string,
    endDate?: string,
    provider?: string
  ): Promise<MacroIndicatorResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (provider) params.append('provider', provider);
    const queryString = params.toString();
    return get<MacroIndicatorResponse>(
      `${BASE_URL}/economy/macro/${indicator}${queryString ? `?${queryString}` : ''}`
    );
  },

  /**
   * 获取美国国债收益率
   */
  getTreasuryRates: async (
    startDate?: string,
    endDate?: string,
    provider?: string
  ): Promise<{ data: Record<string, unknown>[]; provider: string; count: number }> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (provider) params.append('provider', provider);
    const queryString = params.toString();
    return get(`${BASE_URL}/economy/treasury${queryString ? `?${queryString}` : ''}`);
  },

  // ==============================================
  // 技术分析
  // ==============================================

  /**
   * 获取技术指标
   *
   * 支持的指标:
   * - rsi: 相对强弱指数
   * - macd: 异同移动平均线
   * - bbands: 布林带
   * - sma: 简单移动平均
   * - ema: 指数移动平均
   * - atr: 平均真实波幅
   * - adx: 平均趋向指数
   * - stoch: 随机指标
   */
  getTechnicalIndicators: async (
    symbol: string,
    indicators: string[] = ['rsi', 'macd'],
    startDate?: string,
    endDate?: string,
    provider?: string
  ): Promise<TechnicalIndicatorResponse> => {
    const params = new URLSearchParams();
    params.append('indicators', indicators.join(','));
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (provider) params.append('provider', provider);
    return get<TechnicalIndicatorResponse>(
      `${BASE_URL}/technical/indicators/${symbol}?${params.toString()}`
    );
  },

  /**
   * 获取 RSI 指标
   */
  getRSI: async (
    symbol: string,
    length: number = 14,
    startDate?: string,
    endDate?: string
  ): Promise<{
    symbol: string;
    indicator: string;
    length: number;
    data: TechnicalIndicatorData[];
    count: number;
  }> => {
    const params = new URLSearchParams();
    params.append('length', length.toString());
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return get(`${BASE_URL}/technical/rsi/${symbol}?${params.toString()}`);
  },

  /**
   * 获取 MACD 指标
   */
  getMACD: async (
    symbol: string,
    fast: number = 12,
    slow: number = 26,
    signal: number = 9,
    startDate?: string,
    endDate?: string
  ): Promise<{
    symbol: string;
    indicator: string;
    parameters: { fast: number; slow: number; signal: number };
    data: TechnicalIndicatorData[];
    count: number;
  }> => {
    const params = new URLSearchParams();
    params.append('fast', fast.toString());
    params.append('slow', slow.toString());
    params.append('signal', signal.toString());
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return get(`${BASE_URL}/technical/macd/${symbol}?${params.toString()}`);
  },

  // ==============================================
  // 系统状态
  // ==============================================

  /**
   * 获取 OpenBB 服务状态
   */
  getStatus: async (): Promise<OpenBBStatus> => {
    return get<OpenBBStatus>(`${BASE_URL}/status`);
  },

  /**
   * 获取支持的提供商列表
   */
  getProviders: async (): Promise<ProvidersList> => {
    return get<ProvidersList>(`${BASE_URL}/providers`);
  },
};

export default openbbService;
