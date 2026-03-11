/**
 * 策略注册表 API 服务
 *
 * 提供策略注册、发现、实例化等功能的 API 调用
 */

import { get, post, put, del } from './api';

// 策略元数据
export interface StrategyMetadata {
  strategy_id: string;
  name: string;
  version: string;
  author: string;
  description: string;
  category: string;
  frequency: string;
  status: string;
  tags: string[];
  params_schema: Record<string, any>;
  default_params: Record<string, any>;
  min_history_bars: number;
  supported_markets: string[];
  risk_level: string;
}

// 策略实例
export interface StrategyInstance {
  instance_id: string;
  name: string;
  status: string;
  parameters: Record<string, any>;
  strategy_id?: string;
  created_at?: string;
}

// 创建实例请求
export interface CreateInstanceRequest {
  strategy_id: string;
  instance_id?: string;
  params?: Record<string, any>;
  initial_capital?: number;
  execution_mode?: 'PAPER' | 'LIVE';
}

// API 响应类型
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  meta?: Record<string, any>;
}

// 获取策略列表
export async function getStrategies(params?: {
  category?: string;
  status?: string;
  frequency?: string;
  tags?: string;
}): Promise<{ data: StrategyMetadata[]; meta: { total: number } }> {
  const queryParams = new URLSearchParams();
  if (params?.category && params.category !== 'all') queryParams.append('category', params.category);
  if (params?.status && params.status !== 'all') queryParams.append('status', params.status);
  if (params?.frequency && params.frequency !== 'all') queryParams.append('frequency', params.frequency);
  if (params?.tags) queryParams.append('tags', params.tags);
  const query = queryParams.toString();

  try {
    const response = await get<ApiResponse<StrategyMetadata[]>>(`/api/v1/strategy-registry/${query ? '?' + query : ''}`);
    const meta = response.meta as { total?: number } | undefined;
    return {
      data: response.data || [],
      meta: { total: meta?.total ?? (response.data || []).length }
    };
  } catch (error) {
    console.error('获取策略列表失败:', error);
    return { data: [], meta: { total: 0 } };
  }
}

// 获取单个策略
export async function getStrategy(strategyId: string): Promise<StrategyMetadata> {
  const response = await get<ApiResponse<StrategyMetadata>>(`/api/v1/strategy-registry/${strategyId}`);
  return response.data;
}

// 获取策略分类
export async function getCategories(): Promise<string[]> {
  try {
    const response = await get<ApiResponse<string[]>>('/api/v1/strategy-registry/registry/categories');
    return response.data || [];
  } catch (error) {
    console.error('获取分类失败:', error);
    return [];
  }
}

// 获取所有标签
export async function getTags(): Promise<string[]> {
  try {
    const response = await get<ApiResponse<string[]>>('/api/v1/strategy-registry/registry/tags');
    return response.data || [];
  } catch (error) {
    console.error('获取标签失败:', error);
    return [];
  }
}

// 按状态获取策略
export async function getStrategiesByStatus(status: string): Promise<StrategyMetadata[]> {
  const response = await get<ApiResponse<StrategyMetadata[]>>(`/api/v1/strategy-registry/by-status/${status}`);
  return response.data || [];
}

// 更新策略状态
export async function updateStrategyStatus(
  strategyId: string,
  status: string
): Promise<void> {
  await put(`/api/v1/strategy-registry/${strategyId}/status`, { status });
}

// 更新策略配置
export async function updateStrategyConfig(
  strategyId: string,
  params: Record<string, any>
): Promise<void> {
  await put(`/api/v1/strategy-registry/${strategyId}/config`, { params });
}

// 获取所有策略实例
export async function getInstances(): Promise<StrategyInstance[]> {
  try {
    const response = await get<ApiResponse<StrategyInstance[]>>('/api/v1/strategy-registry/instances/');
    return response.data || [];
  } catch (error) {
    console.error('获取实例列表失败:', error);
    return [];
  }
}

// 获取单个实例
export async function getInstance(instanceId: string): Promise<StrategyInstance> {
  const response = await get<ApiResponse<StrategyInstance>>(`/api/v1/strategy-registry/instances/${instanceId}`);
  return response.data;
}

// 创建策略实例
export async function createInstance(
  request: CreateInstanceRequest
): Promise<{ instance_id: string; strategy_id: string }> {
  const response = await post<ApiResponse<{ instance_id: string; strategy_id: string }>>(
    '/api/v1/strategy-registry/instances',
    request
  );
  return response.data;
}

// 移除策略实例
export async function removeInstance(instanceId: string): Promise<void> {
  await del(`/api/v1/strategy-registry/instances/${instanceId}`);
}

// 获取注册表状态
export async function getRegistryStatus(): Promise<{
  total_strategies: number;
  total_instances: number;
}> {
  try {
    const response = await get<ApiResponse<{
      total_strategies: number;
      total_instances: number;
    }>>('/api/v1/strategy-registry/registry/status');
    return response.data || { total_strategies: 0, total_instances: 0 };
  } catch (error) {
    console.error('获取注册表状态失败:', error);
    return { total_strategies: 0, total_instances: 0 };
  }
}

// 扫描目录注册策略
export async function scanStrategies(
  directory: string,
  recursive: boolean = true
): Promise<{ registered_count: number }> {
  const response = await post<ApiResponse<{ registered_count: number }>>(
    '/api/v1/strategy-registry/scan',
    { directory, recursive }
  );
  return response.data || { registered_count: 0 };
}

// 注销策略
export async function unregisterStrategy(strategyId: string): Promise<void> {
  await del(`/api/v1/strategy-registry/${strategyId}`);
}

const strategyRegistryService = {
  getStrategies,
  getStrategy,
  getCategories,
  getTags,
  getStrategiesByStatus,
  updateStrategyStatus,
  updateStrategyConfig,
  getInstances,
  getInstance,
  createInstance,
  removeInstance,
  getRegistryStatus,
  scanStrategies,
  unregisterStrategy,
};

export default strategyRegistryService;
