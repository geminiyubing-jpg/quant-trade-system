/**
 * 数据管理服务 API
 *
 * 封装数据管理相关端点：ETL、数据引擎、数据质量
 */

import { get, post, del } from './api';

// ==============================================
// 数据 ETL
// ==============================================

const ETL_PREFIX = '/api/v1/data-etl';

// ETL 任务状态
export type ETLTaskStatus = 'pending' | 'running' | 'completed' | 'failed';

// ETL 任务
export interface ETLTask {
  id: string;
  name: string;
  task_type: 'stock_daily' | 'stock_info' | 'factor' | 'index' | 'custom';
  status: ETLTaskStatus;
  config: Record<string, any>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  records_processed?: number;
  records_failed?: number;
  error_message?: string;
}

// ETL 任务列表响应
export interface ETLTaskListResponse {
  total: number;
  items: ETLTask[];
}

// 创建 ETL 任务请求
export interface ETLTaskCreate {
  name: string;
  task_type: ETLTask['task_type'];
  config: Record<string, any>;
  schedule?: string;
}

/**
 * 获取 ETL 任务列表
 */
export async function getETLTasks(params?: {
  status?: ETLTaskStatus;
  task_type?: ETLTask['task_type'];
  skip?: number;
  limit?: number;
}): Promise<ETLTaskListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status', params.status);
  if (params?.task_type) query.append('task_type', params.task_type);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${ETL_PREFIX}/tasks${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取 ETL 任务详情
 */
export async function getETLTask(taskId: string): Promise<ETLTask> {
  return get(`${ETL_PREFIX}/tasks/${taskId}`);
}

/**
 * 创建 ETL 任务
 */
export async function createETLTask(data: ETLTaskCreate): Promise<ETLTask> {
  return post(`${ETL_PREFIX}/tasks`, data);
}

/**
 * 启动 ETL 任务
 */
export async function startETLTask(taskId: string): Promise<{ success: boolean }> {
  return post(`${ETL_PREFIX}/tasks/${taskId}/start`);
}

/**
 * 停止 ETL 任务
 */
export async function stopETLTask(taskId: string): Promise<{ success: boolean }> {
  return post(`${ETL_PREFIX}/tasks/${taskId}/stop`);
}

/**
 * 删除 ETL 任务
 */
export async function deleteETLTask(taskId: string): Promise<void> {
  return del(`${ETL_PREFIX}/tasks/${taskId}`);
}

// ==============================================
// 数据引擎
// ==============================================

const ENGINE_PREFIX = '/api/v1/data-engine';

// 数据源配置
export interface DataSource {
  id: string;
  name: string;
  source_type: 'akshare' | 'tushare' | 'eastmoney' | 'custom';
  config: Record<string, any>;
  is_active: boolean;
  last_sync?: string;
  created_at: string;
}

// 数据同步任务
export interface SyncTask {
  id: string;
  source_id: string;
  data_type: string;
  symbols?: string[];
  start_date?: string;
  end_date?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  created_at: string;
  completed_at?: string;
}

/**
 * 获取数据源列表
 */
export async function getDataSources(): Promise<{
  total: number;
  items: DataSource[];
}> {
  return get(`${ENGINE_PREFIX}/sources`);
}

/**
 * 创建数据同步任务
 */
export async function createSyncTask(data: {
  source_id: string;
  data_type: string;
  symbols?: string[];
  start_date?: string;
  end_date?: string;
}): Promise<SyncTask> {
  return post(`${ENGINE_PREFIX}/sync`, data);
}

/**
 * 获取同步任务状态
 */
export async function getSyncTaskStatus(taskId: string): Promise<SyncTask> {
  return get(`${ENGINE_PREFIX}/sync/${taskId}`);
}

// ==============================================
// 数据质量
// ==============================================

const QUALITY_PREFIX = '/api/v1/data-quality';

// 数据质量报告
export interface QualityReport {
  id: string;
  data_type: string;
  table_name: string;
  check_date: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  missing_rate: number;
  duplicate_rate: number;
  issues: Array<{
    field: string;
    issue_type: string;
    count: number;
    examples: any[];
  }>;
  created_at: string;
}

// 数据质量规则
export interface QualityRule {
  id: string;
  name: string;
  data_type: string;
  field: string;
  rule_type: 'not_null' | 'range' | 'format' | 'unique' | 'custom';
  rule_config: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

/**
 * 获取数据质量报告
 */
export async function getQualityReports(params?: {
  data_type?: string;
  start_date?: string;
  end_date?: string;
}): Promise<{
  total: number;
  items: QualityReport[];
}> {
  const query = new URLSearchParams();
  if (params?.data_type) query.append('data_type', params.data_type);
  if (params?.start_date) query.append('start_date', params.start_date);
  if (params?.end_date) query.append('end_date', params.end_date);

  const queryString = query.toString();
  return get(`${QUALITY_PREFIX}/reports${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取数据质量规则列表
 */
export async function getQualityRules(): Promise<{
  total: number;
  items: QualityRule[];
}> {
  return get(`${QUALITY_PREFIX}/rules`);
}

/**
 * 创建数据质量规则
 */
export async function createQualityRule(data: Omit<QualityRule, 'id' | 'created_at'>): Promise<QualityRule> {
  return post(`${QUALITY_PREFIX}/rules`, data);
}

/**
 * 运行数据质量检查
 */
export async function runQualityCheck(data: {
  data_type: string;
  table_name?: string;
}): Promise<{ task_id: string; status: string }> {
  return post(`${QUALITY_PREFIX}/check`, data);
}

// ==============================================
// 综合导出
// ==============================================

export const dataService = {
  // ETL 任务
  getETLTasks,
  getETLTask,
  createETLTask,
  startETLTask,
  stopETLTask,
  deleteETLTask,
  // 数据引擎
  getDataSources,
  createSyncTask,
  getSyncTaskStatus,
  // 数据质量
  getQualityReports,
  getQualityRules,
  createQualityRule,
  runQualityCheck,
};

export default dataService;
