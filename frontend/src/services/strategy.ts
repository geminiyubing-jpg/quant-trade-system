/**
 * 策略管理 API 服务
 *
 * 封装 /api/v1/strategies/* 端点
 */

import { get, post, put, del } from './api';

const API_PREFIX = '/api/v1/strategies';

// 策略状态
export type StrategyStatus = 'running' | 'paused' | 'stopped';

// 执行模式
export type ExecutionMode = 'PAPER' | 'LIVE';

// 策略类型
export type StrategyType = 'trend' | 'mean_reversion' | 'momentum' | 'arbitrage' | 'custom';

// 策略
export interface Strategy {
  id: string;
  name: string;
  description?: string;
  type: StrategyType;
  status: StrategyStatus;
  execution_mode: ExecutionMode;
  created_at: string;
  updated_at: string;
  metrics?: {
    sharpe: number;
    max_drawdown: number;
    annual_return: number;
    win_rate: number;
  };
}

// 策略列表响应
export interface StrategyListResponse {
  total: number;
  items: Strategy[];
}

// 创建策略请求
export interface StrategyCreate {
  name: string;
  description?: string;
  type: StrategyType;
  execution_mode?: ExecutionMode;
}

// 更新策略请求
export interface StrategyUpdate {
  name?: string;
  description?: string;
  type?: StrategyType;
  status?: StrategyStatus;
}

// 策略版本
export interface StrategyVersion {
  id: string;
  strategy_id: string;
  version_number: string;
  change_type: 'MAJOR' | 'MINOR' | 'PATCH';
  change_log: string;
  code?: string;
  parameters?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  created_by: string;
}

// 版本列表响应
export interface VersionListResponse {
  total: number;
  items: StrategyVersion[];
}

// 创建版本请求
export interface VersionCreate {
  code?: string;
  parameters?: Record<string, any>;
  change_log: string;
  change_type?: 'MAJOR' | 'MINOR' | 'PATCH';
}

// 策略配置
export interface StrategyConfig {
  id: string;
  strategy_id: string;
  symbols: string[];
  market?: string;
  allocation_ratio: number;
  max_position_count: number;
  max_single_position_ratio?: number;
  stop_loss_ratio?: number;
  take_profit_ratio?: number;
  max_drawdown_limit?: number;
  daily_loss_limit?: number;
  execution_mode: ExecutionMode;
  auto_rebalance?: boolean;
  is_active: boolean;
}

// 更新配置请求
export interface ConfigUpdate {
  symbols?: string[];
  allocation_ratio?: number;
  max_position_count?: number;
  stop_loss_ratio?: number;
  take_profit_ratio?: number;
  execution_mode?: string;
}

// 审计日志
export interface AuditLog {
  id: string;
  strategy_id: string;
  action_type: string;
  action_description: string;
  old_value?: any;
  new_value?: any;
  created_at: string;
  user_id: string;
}

// 审计日志列表响应
export interface AuditLogListResponse {
  total: number;
  items: AuditLog[];
}

// ==============================================
// 策略管理
// ==============================================

/**
 * 获取策略列表
 */
export async function getStrategies(params?: {
  status?: StrategyStatus;
  type?: StrategyType;
  skip?: number;
  limit?: number;
}): Promise<StrategyListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status', params.status);
  if (params?.type) query.append('type', params.type);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get<StrategyListResponse>(`${API_PREFIX}${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取策略详情
 */
export async function getStrategy(strategyId: string): Promise<Strategy> {
  return get<Strategy>(`${API_PREFIX}/${strategyId}`);
}

/**
 * 创建策略
 */
export async function createStrategy(data: StrategyCreate): Promise<Strategy> {
  return post<Strategy>(API_PREFIX, data);
}

/**
 * 更新策略
 */
export async function updateStrategy(strategyId: string, data: StrategyUpdate): Promise<Strategy> {
  return put<Strategy>(`${API_PREFIX}/${strategyId}`, data);
}

/**
 * 删除策略
 */
export async function deleteStrategy(strategyId: string): Promise<void> {
  return del<void>(`${API_PREFIX}/${strategyId}`);
}

/**
 * 激活策略
 */
export async function activateStrategy(strategyId: string): Promise<Strategy> {
  return post<Strategy>(`${API_PREFIX}/${strategyId}/activate`);
}

/**
 * 停用策略
 */
export async function deactivateStrategy(strategyId: string): Promise<Strategy> {
  return post<Strategy>(`${API_PREFIX}/${strategyId}/deactivate`);
}

// ==============================================
// 版本管理
// ==============================================

/**
 * 获取策略版本列表
 */
export async function getVersions(strategyId: string): Promise<VersionListResponse> {
  return get<VersionListResponse>(`${API_PREFIX}/${strategyId}/versions`);
}

/**
 * 创建策略版本
 */
export async function createVersion(strategyId: string, data: VersionCreate): Promise<StrategyVersion> {
  return post<StrategyVersion>(`${API_PREFIX}/${strategyId}/versions`, data);
}

/**
 * 激活版本
 */
export async function activateVersion(strategyId: string, versionId: string): Promise<StrategyVersion> {
  return post<StrategyVersion>(`${API_PREFIX}/${strategyId}/versions/${versionId}/activate`);
}

// ==============================================
// 配置管理
// ==============================================

/**
 * 获取策略配置
 */
export async function getConfig(strategyId: string): Promise<StrategyConfig> {
  return get<StrategyConfig>(`${API_PREFIX}/${strategyId}/config`);
}

/**
 * 更新策略配置
 */
export async function updateConfig(strategyId: string, data: ConfigUpdate): Promise<StrategyConfig> {
  return put<StrategyConfig>(`${API_PREFIX}/${strategyId}/config`, data);
}

// ==============================================
// 审计日志
// ==============================================

/**
 * 获取审计日志
 */
export async function getAuditLogs(strategyId: string): Promise<AuditLogListResponse> {
  return get<AuditLogListResponse>(`${API_PREFIX}/${strategyId}/audit-logs`);
}

// 导出服务对象
export const strategyService = {
  // 策略管理
  getStrategies,
  getStrategy,
  createStrategy,
  updateStrategy,
  deleteStrategy,
  activateStrategy,
  deactivateStrategy,
  // 版本管理
  getVersions,
  createVersion,
  activateVersion,
  // 配置管理
  getConfig,
  updateConfig,
  // 审计日志
  getAuditLogs,
};

export default strategyService;
