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
  source_type: 'akshare' | 'tushare' | 'eastmoney' | 'openbb' | 'yahoo_finance' | 'custom';
  config: Record<string, any>;
  is_active: boolean;
  last_sync?: string;
  created_at: string;
  // OpenBB 专用配置
  providers?: {
    equity?: string;      // 股票数据提供商
    economy?: string;     // 宏观经济数据提供商
    technical?: string;   // 技术分析提供商
  };
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
  report_id: string;
  report_time: string;
  overall_score: number;
  overall_level: string;
  metrics: Array<{
    type: string;
    score: number;
    level: string;
    details: Record<string, unknown>;
  }>;
  recommendations: string[];
  alerts: Array<Record<string, unknown>>;
}

// 数据质量详细报告（用于数据管理页面）
export interface QualityReportDetail {
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
    examples: unknown[];
  }>;
  created_at: string;
}

// 数据质量报告列表响应
export interface QualityReportListResponse {
  total: number;
  items: QualityReportDetail[];
}

// 数据质量告警
export interface QualityAlert {
  alert_id: string;
  alert_type: string;
  severity: string;
  message: string;
  source?: string;
  timestamp: string;
  acknowledged: boolean;
}

// 数据质量摘要
export interface QualitySummary {
  overall_score: number;
  overall_level: string;
  metric_count: number;
  alert_count: number;
  last_update: string;
}

/**
 * 获取数据质量报告
 */
export async function getQualityReport(): Promise<QualityReport> {
  return get(`${QUALITY_PREFIX}/report`);
}

/**
 * 获取数据质量报告列表
 */
export async function getQualityReports(params?: {
  data_type?: string;
  skip?: number;
  limit?: number;
}): Promise<QualityReportListResponse> {
  const query = new URLSearchParams();
  if (params?.data_type) query.append('data_type', params.data_type);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${QUALITY_PREFIX}/reports${queryString ? `?${queryString}` : ''}`);
}

/**
 * 运行数据质量检查
 */
export async function runQualityCheck(params: {
  data_type: string;
  table_name?: string;
}): Promise<{ task_id: string; status: string }> {
  return post(`${QUALITY_PREFIX}/check`, params);
}

/**
 * 获取数据质量摘要
 */
export async function getQualitySummary(): Promise<QualitySummary> {
  return get(`${QUALITY_PREFIX}/summary`);
}

/**
 * 获取数据质量告警列表
 */
export async function getQualityAlerts(params?: {
  severity?: string;
  acknowledged?: boolean;
  limit?: number;
}): Promise<QualityAlert[]> {
  const query = new URLSearchParams();
  if (params?.severity) query.append('severity', params.severity);
  if (params?.acknowledged !== undefined) query.append('acknowledged', String(params.acknowledged));
  if (params?.limit) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${QUALITY_PREFIX}/alerts${queryString ? `?${queryString}` : ''}`);
}

/**
 * 确认告警
 */
export async function acknowledgeAlert(alertId: string): Promise<{ success: boolean; message: string }> {
  return post(`${QUALITY_PREFIX}/alerts/${alertId}/acknowledge`);
}

/**
 * 获取指标历史
 */
export async function getMetricHistory(params?: {
  metric_type?: string;
  limit?: number;
}): Promise<Array<{
  type: string;
  score: number;
  level: string;
  timestamp: string;
  details: Record<string, unknown>;
}>> {
  const query = new URLSearchParams();
  if (params?.metric_type) query.append('metric_type', params.metric_type);
  if (params?.limit) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${QUALITY_PREFIX}/history${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取特定指标详情
 */
export async function getMetricDetail(metricType: string): Promise<{
  success: boolean;
  data: {
    type: string;
    score: number;
    level: string;
    details: Record<string, unknown>;
    timestamp: string;
  };
}> {
  return get(`${QUALITY_PREFIX}/metrics/${metricType}`);
}

/**
 * 检查数据完整性
 */
export async function checkCompleteness(params?: {
  table_name?: string;
  symbol?: string;
}): Promise<{
  success: boolean;
  data: {
    type: string;
    score: number;
    level: string;
    details: Record<string, unknown>;
  };
}> {
  const query = new URLSearchParams();
  if (params?.table_name) query.append('table_name', params.table_name);
  if (params?.symbol) query.append('symbol', params.symbol);

  const queryString = query.toString();
  return post(`${QUALITY_PREFIX}/check/completeness${queryString ? `?${queryString}` : ''}`);
}

/**
 * 检查数据准确性
 */
export async function checkAccuracy(params?: {
  table_name?: string;
  sample_size?: number;
}): Promise<{
  success: boolean;
  data: {
    type: string;
    score: number;
    level: string;
    details: Record<string, unknown>;
  };
}> {
  const query = new URLSearchParams();
  if (params?.table_name) query.append('table_name', params.table_name);
  if (params?.sample_size) query.append('sample_size', String(params.sample_size));

  const queryString = query.toString();
  return post(`${QUALITY_PREFIX}/check/accuracy${queryString ? `?${queryString}` : ''}`);
}

/**
 * 检查数据及时性
 */
export async function checkTimeliness(params?: {
  source_name?: string;
}): Promise<{
  success: boolean;
  data: {
    type: string;
    score: number;
    level: string;
    details: Record<string, unknown>;
  };
}> {
  const query = new URLSearchParams();
  if (params?.source_name) query.append('source_name', params.source_name);

  const queryString = query.toString();
  return post(`${QUALITY_PREFIX}/check/timeliness${queryString ? `?${queryString}` : ''}`);
}

/**
 * 同步数据源
 */
export async function syncDataSource(sourceId: string): Promise<{ success: boolean }> {
  return post(`${ENGINE_PREFIX}/sources/${sourceId}/sync`);
}

/**
 * 更新数据源配置
 */
export async function updateDataSource(
  sourceId: string,
  data: { name: string; config: Record<string, any> }
): Promise<DataSource> {
  return post(`${ENGINE_PREFIX}/sources/${sourceId}`, data);
}

// ==============================================
// OpenBB 数据源
// ==============================================

const OPENBB_PREFIX = '/api/v1/openbb';

// OpenBB 数据源状态
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

// OpenBB 提供商列表
export interface OpenBBProviders {
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

// OpenBB 股票报价
export interface OpenBBQuote {
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

// OpenBB 历史价格
export interface OpenBBHistoricalPrice {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adj_close?: number;
}

export interface OpenBBHistoricalResponse {
  symbol: string;
  data: OpenBBHistoricalPrice[];
  provider: string;
  count: number;
}

// OpenBB 宏观指标
export interface OpenBBMacroResponse {
  indicator: string;
  data: Record<string, unknown>[];
  provider: string;
  count: number;
}

// OpenBB 技术指标
export interface OpenBBTechnicalResponse {
  symbol: string;
  indicators: string[];
  data: Record<string, unknown>[];
  provider: string;
  count: number;
}

/**
 * 获取 OpenBB 服务状态
 */
export async function getOpenBBStatus(): Promise<OpenBBStatus> {
  return get(`${OPENBB_PREFIX}/status`);
}

/**
 * 获取 OpenBB 提供商列表
 */
export async function getOpenBBProviders(): Promise<OpenBBProviders> {
  return get(`${OPENBB_PREFIX}/providers`);
}

/**
 * 获取 OpenBB 股票报价
 */
export async function getOpenBBQuote(
  symbol: string,
  provider?: string
): Promise<OpenBBQuote> {
  const params = provider ? `?provider=${provider}` : '';
  return get(`${OPENBB_PREFIX}/equity/quote/${symbol}${params}`);
}

/**
 * 获取 OpenBB 历史价格
 */
export async function getOpenBBHistorical(
  symbol: string,
  startDate?: string,
  endDate?: string,
  provider?: string
): Promise<OpenBBHistoricalResponse> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (provider) params.append('provider', provider);
  const queryString = params.toString();
  return get(`${OPENBB_PREFIX}/equity/historical/${symbol}${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取 OpenBB 宏观经济指标
 */
export async function getOpenBBMacro(
  indicator: string,
  startDate?: string,
  endDate?: string,
  provider?: string
): Promise<OpenBBMacroResponse> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (provider) params.append('provider', provider);
  const queryString = params.toString();
  return get(`${OPENBB_PREFIX}/economy/macro/${indicator}${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取 OpenBB 技术指标
 */
export async function getOpenBBTechnical(
  symbol: string,
  indicators: string[],
  startDate?: string,
  endDate?: string,
  provider?: string
): Promise<OpenBBTechnicalResponse> {
  const params = new URLSearchParams();
  params.append('indicators', indicators.join(','));
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (provider) params.append('provider', provider);
  return get(`${OPENBB_PREFIX}/technical/indicators/${symbol}?${params.toString()}`);
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
  syncDataSource,
  updateDataSource,
  // 数据质量
  getQualityReport,
  getQualityReports,
  runQualityCheck,
  getQualitySummary,
  getQualityAlerts,
  acknowledgeAlert,
  getMetricHistory,
  getMetricDetail,
  checkCompleteness,
  checkAccuracy,
  checkTimeliness,
  // OpenBB 数据源
  getOpenBBStatus,
  getOpenBBProviders,
  getOpenBBQuote,
  getOpenBBHistorical,
  getOpenBBMacro,
  getOpenBBTechnical,
};

export default dataService;
