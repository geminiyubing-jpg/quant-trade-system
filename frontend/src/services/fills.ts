/**
 * 成交记录 API 服务
 *
 * 封装 /api/v1/fills/* 端点
 */

import { get, post } from './api';
import type { Fill, FillListResponse, ExecutionMode } from '../types/trading';

const API_PREFIX = '/api/v1/fills';

/**
 * 获取成交记录列表
 */
export async function getFills(params?: {
  symbol?: string;
  order_id?: string;
  execution_mode?: ExecutionMode;
  skip?: number;
  limit?: number;
}): Promise<FillListResponse> {
  const query = new URLSearchParams();
  if (params?.symbol) query.append('symbol', params.symbol);
  if (params?.order_id) query.append('order_id', params.order_id);
  if (params?.execution_mode) query.append('execution_mode', params.execution_mode);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get<FillListResponse>(`${API_PREFIX}${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取单个成交记录
 */
export async function getFill(fillId: string): Promise<Fill> {
  return get<Fill>(`${API_PREFIX}/${fillId}`);
}

/**
 * 获取订单的所有成交记录
 */
export async function getFillsByOrder(orderId: string): Promise<FillListResponse> {
  return get<FillListResponse>(`${API_PREFIX}/order/${orderId}`);
}

/**
 * 创建成交记录（通常由系统调用）
 */
export async function createFill(fill: {
  order_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  execution_mode: ExecutionMode;
}): Promise<Fill> {
  return post<Fill>(`${API_PREFIX}`, fill);
}

// 导出服务对象
export const fillsService = {
  getFills,
  getFill,
  getFillsByOrder,
  createFill,
};

export default fillsService;
