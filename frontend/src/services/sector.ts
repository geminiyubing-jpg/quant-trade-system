/**
 * 板块分析服务 API
 *
 * 封装 /api/v1/data/sectors/* 端点
 */

import { get } from './api';

const API_PREFIX = '/api/v1/data/sectors';

// 板块类型
export type SectorType = 'industry' | 'concept' | 'region';

// 板块数据
export interface SectorData {
  name: string;
  code: string;
  type: SectorType;
  change_pct?: number;
  volume?: number;
  amount?: number;
  turnover_rate?: number;
  leading_stock?: string;
  leading_stock_change?: number;
  stock_count?: number;
  up_count?: number;
  down_count?: number;
}

// 板块成分股
export interface SectorStock {
  symbol: string;
  name: string;
  price?: number;
  change_pct?: number;
  volume?: number;
  amount?: number;
  turnover_rate?: number;
  pe_ratio?: number;
  market_cap?: number;
}

// 板块统计
export interface SectorStats {
  total: number;
  up: number;
  down: number;
  flat: number;
  best: SectorData | null;
  worst: SectorData | null;
}

// 板块资金流向
export interface SectorFlow {
  sector_code: string;
  sector_name: string;
  main_inflow: number;
  main_outflow: number;
  net_inflow: number;
  retail_inflow: number;
  retail_outflow: number;
  date: string;
}

// 板块轮动数据
export interface SectorRotation {
  date: string;
  sectors: Array<{
    code: string;
    name: string;
    rank: number;
    prev_rank: number;
    momentum: number;
  }>;
}

// ==============================================
// 板块数据
// ==============================================

/**
 * 获取板块统计概览
 */
export async function getSectorOverview(sectorType: SectorType): Promise<{
  success: boolean;
  data: SectorData[];
  summary: SectorStats;
}> {
  return get(`${API_PREFIX}/stats/overview?sector_type=${sectorType}`);
}

/**
 * 获取板块列表
 */
export async function getSectors(params?: {
  sector_type?: SectorType;
  sort_by?: 'change_pct' | 'amount' | 'turnover_rate';
  order?: 'asc' | 'desc';
  limit?: number;
}): Promise<{
  total: number;
  items: SectorData[];
}> {
  const query = new URLSearchParams();
  if (params?.sector_type) query.append('sector_type', params.sector_type);
  if (params?.sort_by) query.append('sort_by', params.sort_by);
  if (params?.order) query.append('order', params.order);
  if (params?.limit) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${API_PREFIX}${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取板块详情
 */
export async function getSectorDetail(sectorCode: string): Promise<SectorData> {
  return get(`${API_PREFIX}/${sectorCode}`);
}

/**
 * 获取板块成分股
 */
export async function getSectorStocks(sectorCode: string, params?: {
  sort_by?: 'change_pct' | 'amount' | 'market_cap';
  order?: 'asc' | 'desc';
  limit?: number;
}): Promise<{
  total: number;
  items: SectorStock[];
}> {
  const query = new URLSearchParams();
  if (params?.sort_by) query.append('sort_by', params.sort_by);
  if (params?.order) query.append('order', params.order);
  if (params?.limit) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${API_PREFIX}/${sectorCode}/stocks${queryString ? `?${queryString}` : ''}`);
}

// ==============================================
// 资金流向
// ==============================================

/**
 * 获取板块资金流向
 */
export async function getSectorFlows(params?: {
  sector_type?: SectorType;
  date?: string;
  limit?: number;
}): Promise<{
  total: number;
  items: SectorFlow[];
}> {
  const query = new URLSearchParams();
  if (params?.sector_type) query.append('sector_type', params.sector_type);
  if (params?.date) query.append('date', params.date);
  if (params?.limit) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${API_PREFIX}/flows${queryString ? `?${queryString}` : ''}`);
}

// ==============================================
// 板块轮动
// ==============================================

/**
 * 获取板块轮动数据
 */
export async function getSectorRotation(params?: {
  sector_type?: SectorType;
  start_date?: string;
  end_date?: string;
}): Promise<{
  total: number;
  items: SectorRotation[];
}> {
  const query = new URLSearchParams();
  if (params?.sector_type) query.append('sector_type', params.sector_type);
  if (params?.start_date) query.append('start_date', params.start_date);
  if (params?.end_date) query.append('end_date', params.end_date);

  const queryString = query.toString();
  return get(`${API_PREFIX}/rotation${queryString ? `?${queryString}` : ''}`);
}

// 导出服务对象
export const sectorService = {
  // 板块数据
  getSectorOverview,
  getSectors,
  getSectorDetail,
  getSectorStocks,
  // 资金流向
  getSectorFlows,
  // 板块轮动
  getSectorRotation,
};

export default sectorService;
