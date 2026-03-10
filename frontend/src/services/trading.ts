/**
 * 交易 API 服务
 *
 * 封装 /api/v1/trading/* 端点
 */

import { get, post, put, del } from './api';
import type {
  Order,
  OrderListResponse,
  OrderCreate,
  OrderUpdate,
  Position,
  PositionListResponse,
  PositionSummary,
  TradingModeStatus,
  TradingModeSwitchRequest,
  TradingModeSwitchResponse,
  LiveTradingPasswordRequest,
  LiveTradingPasswordResponse,
  ExecutionMode,
} from '../types/trading';

const API_PREFIX = '/api/v1/trading';

// ==============================================
// 订单管理
// ==============================================

/**
 * 获取订单列表
 */
export async function getOrders(params?: {
  symbol?: string;
  status?: string;
  execution_mode?: ExecutionMode;
  skip?: number;
  limit?: number;
}): Promise<OrderListResponse> {
  const query = new URLSearchParams();
  if (params?.symbol) query.append('symbol', params.symbol);
  if (params?.status) query.append('status', params.status);
  if (params?.execution_mode) query.append('execution_mode', params.execution_mode);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get<OrderListResponse>(`${API_PREFIX}/orders${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取订单详情
 */
export async function getOrder(orderId: string): Promise<Order> {
  return get<Order>(`${API_PREFIX}/orders/${orderId}`);
}

/**
 * 创建订单
 */
export async function createOrder(order: OrderCreate): Promise<Order> {
  return post<Order>(`${API_PREFIX}/orders`, order);
}

/**
 * 更新订单
 */
export async function updateOrder(orderId: string, order: OrderUpdate): Promise<Order> {
  return put<Order>(`${API_PREFIX}/orders/${orderId}`, order);
}

/**
 * 取消订单
 */
export async function cancelOrder(orderId: string): Promise<void> {
  return del<void>(`${API_PREFIX}/orders/${orderId}`);
}

// ==============================================
// 持仓管理
// ==============================================

/**
 * 获取持仓列表
 */
export async function getPositions(params?: {
  execution_mode?: ExecutionMode;
}): Promise<PositionListResponse> {
  const query = new URLSearchParams();
  if (params?.execution_mode) query.append('execution_mode', params.execution_mode);

  const queryString = query.toString();
  return get<PositionListResponse>(`${API_PREFIX}/positions${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取单个持仓
 */
export async function getPosition(symbol: string, executionMode?: ExecutionMode): Promise<Position> {
  const query = new URLSearchParams();
  if (executionMode) query.append('execution_mode', executionMode);

  const queryString = query.toString();
  return get<Position>(`${API_PREFIX}/positions/${symbol}${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取持仓汇总
 */
export async function getPositionSummary(executionMode?: ExecutionMode): Promise<PositionSummary> {
  const query = new URLSearchParams();
  if (executionMode) query.append('execution_mode', executionMode);

  const queryString = query.toString();
  return get<PositionSummary>(`${API_PREFIX}/positions/summary${queryString ? `?${queryString}` : ''}`);
}

// ==============================================
// 交易模式
// ==============================================

/**
 * 获取当前交易模式状态
 */
export async function getTradingMode(): Promise<TradingModeStatus> {
  return get<TradingModeStatus>(`${API_PREFIX}/mode`);
}

/**
 * 切换交易模式
 */
export async function switchTradingMode(request: TradingModeSwitchRequest): Promise<TradingModeSwitchResponse> {
  return post<TradingModeSwitchResponse>(`${API_PREFIX}/mode/switch`, request);
}

/**
 * 设置实盘交易密码
 */
export async function setLiveTradingPassword(request: LiveTradingPasswordRequest): Promise<LiveTradingPasswordResponse> {
  return post<LiveTradingPasswordResponse>(`${API_PREFIX}/live-trading-password`, request);
}

// ==============================================
// 交易统计
// ==============================================

/**
 * 获取交易统计
 */
export async function getTradingStatistics(executionMode?: ExecutionMode): Promise<{
  total_orders: number;
  filled_orders: number;
  total_volume: number;
  total_amount: number;
}> {
  const query = new URLSearchParams();
  if (executionMode) query.append('execution_mode', executionMode);

  const queryString = query.toString();
  return get(`${API_PREFIX}/statistics${queryString ? `?${queryString}` : ''}`);
}

// 导出服务对象
export const tradingService = {
  // 订单
  getOrders,
  getOrder,
  createOrder,
  updateOrder,
  cancelOrder,
  // 持仓
  getPositions,
  getPosition,
  getPositionSummary,
  // 交易模式
  getTradingMode,
  switchTradingMode,
  setLiveTradingPassword,
  // 统计
  getTradingStatistics,
};

export default tradingService;
