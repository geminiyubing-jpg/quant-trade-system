/**
 * 统一市场数据服务
 * Unified Market Data Service
 *
 * 整合所有市场数据 API 调用
 */
import { get } from './api';

const API_PREFIX = '/api/v1/data';

// ==============================================
// 类型定义
// ==============================================

export interface StockInfo {
  symbol: string;
  name: string;
  industry?: string;
  market?: string;
  list_date?: string;
}

export interface Quote {
  symbol: string;
  name: string;
  price: number;
  open: number;
  high: number;
  low: number;
  pre_close: number;
  volume: number;
  amount: number;
  change: number;
  change_percent: number;
  turnover_rate?: number;
  pe_ttm?: number;
  pb?: number;
  total_mv?: number;
  circ_mv?: number;
  timestamp: string;
}

export interface KLineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  change?: number;
  change_percent?: number;
  turnover?: number;
}

export interface StockListParams {
  page?: number;
  page_size?: number;
  industry?: string;
  market?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface StockListResponse {
  items: StockInfo[];
  total: number;
  page: number;
  page_size: number;
}

// ==============================================
// API 函数
// ==============================================

/**
 * 获取股票列表
 */
export async function getStockList(params: StockListParams = {}): Promise<StockListResponse> {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', String(params.page));
  if (params.page_size) queryParams.append('page_size', String(params.page_size));
  if (params.industry) queryParams.append('industry', params.industry);
  if (params.market) queryParams.append('market', params.market);
  if (params.sort_by) queryParams.append('sort_by', params.sort_by);
  if (params.sort_order) queryParams.append('sort_order', params.sort_order);

  const response = await get<{ success: boolean; data: StockListResponse }>(
    `${API_PREFIX}/stocks?${queryParams.toString()}`
  );
  return response.data;
}

/**
 * 获取单个股票详情
 */
export async function getStockDetail(symbol: string): Promise<StockInfo & { quote?: Quote }> {
  const response = await get<{ success: boolean; data: StockInfo & { quote?: Quote } }>(
    `${API_PREFIX}/stocks/${symbol}`
  );
  return response.data;
}

/**
 * 获取 K 线数据
 */
export async function getKLineData(
  symbol: string,
  period: 'daily' | 'weekly' | 'monthly' = 'daily',
  start_date?: string,
  end_date?: string
): Promise<KLineData[]> {
  const queryParams = new URLSearchParams();
  queryParams.append('period', period);
  if (start_date) queryParams.append('start_date', start_date);
  if (end_date) queryParams.append('end_date', end_date);

  const response = await get<{ success: boolean; data: KLineData[] }>(
    `${API_PREFIX}/kline/${symbol}?${queryParams.toString()}`
  );
  return response.data || [];
}

/**
 * 获取实时行情
 */
export async function getQuote(symbol: string): Promise<Quote> {
  const response = await get<{ success: boolean; data: Quote }>(
    `${API_PREFIX}/quote/${symbol}`
  );
  return response.data;
}

/**
 * 批量获取行情
 */
export async function getQuotes(symbols: string[]): Promise<Quote[]> {
  const response = await get<{ success: boolean; data: Quote[] }>(
    `${API_PREFIX}/quotes?symbols=${symbols.join(',')}`
  );
  return response.data || [];
}

// ==============================================
// 数据转换工具
// ==============================================

/**
 * 转换 K 线数据为 ECharts 格式
 */
export function klineToECharts(data: KLineData[]): {
  kline: [string, string, string, string][];
  volumes: [number, number, number][];
  dates: string[];
} {
  const kline: [string, string, string, string][] = [];
  const volumes: [number, number, number][] = [];
  const dates: string[] = [];

  data.forEach((item, index) => {
    dates.push(item.date);
    kline.push([
      String(item.open),
      String(item.close),
      String(item.low),
      String(item.high),
    ]);
    volumes.push([
      index,
      item.volume,
      item.close >= (data[index - 1]?.close || item.open) ? 1 : -1,
    ]);
  });

  return { kline, volumes, dates };
}

/**
 * 格式化数字
 */
export function formatNumber(num: number, decimals = 2): string {
  if (num >= 100000000) {
    return (num / 100000000).toFixed(decimals) + '亿';
  }
  if (num >= 10000) {
    return (num / 10000).toFixed(decimals) + '万';
  }
  return num.toFixed(decimals);
}

/**
 * 格式化涨跌幅
 */
export function formatChangePercent(percent: number): string {
  const prefix = percent >= 0 ? '+' : '';
  return `${prefix}${percent.toFixed(2)}%`;
}

// ==============================================
// 导出服务对象
// ==============================================

export const marketDataService = {
  getStockList,
  getStockDetail,
  getKLineData,
  getQuote,
  getQuotes,
  klineToECharts,
  formatNumber,
  formatChangePercent,
};

export default marketDataService;
