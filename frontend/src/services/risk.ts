/**
 * 风险控制服务 API
 *
 * 封装 /api/v1/risk/* 端点
 */

import { get, post, put, del } from './api';

const API_PREFIX = '/api/v1/risk';

// 风险规则类型
export type RiskRuleType = 'position_limit' | 'loss_limit' | 'exposure_limit' | 'custom';

// 风险规则状态
export type RiskRuleStatus = 'active' | 'inactive';

// 风险规则
export interface RiskRule {
  id: string;
  name: string;
  rule_type: RiskRuleType;
  description?: string;
  config: Record<string, any>;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: RiskRuleStatus;
  created_at: string;
  updated_at: string;
}

// 风险规则列表响应
export interface RiskRuleListResponse {
  total: number;
  items: RiskRule[];
}

// 创建风险规则请求
export interface RiskRuleCreate {
  name: string;
  rule_type: RiskRuleType;
  description?: string;
  config: Record<string, any>;
  severity?: RiskRule['severity'];
}

// 更新风险规则请求
export interface RiskRuleUpdate {
  name?: string;
  description?: string;
  config?: Record<string, any>;
  severity?: RiskRule['severity'];
  status?: RiskRuleStatus;
}

// 风险预警
export interface RiskAlert {
  id: string;
  rule_id: string;
  rule_name: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details: Record<string, any>;
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

// 风险预警列表响应
export interface RiskAlertListResponse {
  total: number;
  items: RiskAlert[];
}

// 风险指标
export interface RiskMetrics {
  var_95?: number;
  var_99?: number;
  cvar_95?: number;
  cvar_99?: number;
  max_drawdown?: number;
  volatility?: number;
  beta?: number;
  sharpe_ratio?: number;
  concentration_risk?: number;
  sector_concentration?: Record<string, number>;
  calculated_at: string;
}

// ==============================================
// 风险规则管理
// ==============================================

/**
 * 获取风险规则列表
 */
export async function getRiskRules(params?: {
  rule_type?: RiskRuleType;
  status?: RiskRuleStatus;
  skip?: number;
  limit?: number;
}): Promise<RiskRuleListResponse> {
  const query = new URLSearchParams();
  if (params?.rule_type) query.append('rule_type', params.rule_type);
  if (params?.status) query.append('status', params.status);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${API_PREFIX}/rules${queryString ? `?${queryString}` : ''}`);
}

/**
 * 获取风险规则详情
 */
export async function getRiskRule(ruleId: string): Promise<RiskRule> {
  return get(`${API_PREFIX}/rules/${ruleId}`);
}

/**
 * 创建风险规则
 */
export async function createRiskRule(data: RiskRuleCreate): Promise<RiskRule> {
  return post(`${API_PREFIX}/rules`, data);
}

/**
 * 更新风险规则
 */
export async function updateRiskRule(ruleId: string, data: RiskRuleUpdate): Promise<RiskRule> {
  return put(`${API_PREFIX}/rules/${ruleId}`, data);
}

/**
 * 删除风险规则
 */
export async function deleteRiskRule(ruleId: string): Promise<void> {
  return del(`${API_PREFIX}/rules/${ruleId}`);
}

/**
 * 激活风险规则
 */
export async function activateRiskRule(ruleId: string): Promise<RiskRule> {
  return post(`${API_PREFIX}/rules/${ruleId}/activate`);
}

/**
 * 停用风险规则
 */
export async function deactivateRiskRule(ruleId: string): Promise<RiskRule> {
  return post(`${API_PREFIX}/rules/${ruleId}/deactivate`);
}

// ==============================================
// 风险预警
// ==============================================

/**
 * 获取风险预警列表
 */
export async function getRiskAlerts(params?: {
  severity?: RiskAlert['severity'];
  status?: RiskAlert['status'];
  skip?: number;
  limit?: number;
}): Promise<RiskAlertListResponse> {
  const query = new URLSearchParams();
  if (params?.severity) query.append('severity', params.severity);
  if (params?.status) query.append('status', params.status);
  if (params?.skip !== undefined) query.append('skip', String(params.skip));
  if (params?.limit !== undefined) query.append('limit', String(params.limit));

  const queryString = query.toString();
  return get(`${API_PREFIX}/alerts${queryString ? `?${queryString}` : ''}`);
}

/**
 * 确认风险预警
 */
export async function acknowledgeAlert(alertId: string): Promise<RiskAlert> {
  return post(`${API_PREFIX}/alerts/${alertId}/acknowledge`);
}

/**
 * 解决风险预警
 */
export async function resolveAlert(alertId: string): Promise<RiskAlert> {
  return post(`${API_PREFIX}/alerts/${alertId}/resolve`);
}

// ==============================================
// 风险指标
// ==============================================

/**
 * 获取账户风险指标
 */
export async function getRiskMetrics(params?: {
  portfolio_id?: string;
  execution_mode?: 'PAPER' | 'LIVE';
}): Promise<RiskMetrics> {
  const query = new URLSearchParams();
  if (params?.portfolio_id) query.append('portfolio_id', params.portfolio_id);
  if (params?.execution_mode) query.append('execution_mode', params.execution_mode);

  const queryString = query.toString();
  return get(`${API_PREFIX}/metrics${queryString ? `?${queryString}` : ''}`);
}

/**
 * 计算风险指标
 */
export async function calculateRiskMetrics(data: {
  positions: Array<{ symbol: string; quantity: number; market_value: number }>;
  benchmark?: string;
}): Promise<RiskMetrics> {
  return post(`${API_PREFIX}/metrics/calculate`, data);
}

// ==============================================
// 风控检查
// ==============================================

/**
 * 执行风控检查
 */
export async function runRiskCheck(params?: {
  check_type?: 'pre_trade' | 'post_trade' | 'full';
}): Promise<{
  passed: boolean;
  checks: Array<{
    rule_name: string;
    passed: boolean;
    current_value: any;
    limit_value: any;
    message: string;
  }>;
}> {
  const query = new URLSearchParams();
  if (params?.check_type) query.append('check_type', params.check_type);

  const queryString = query.toString();
  return get(`${API_PREFIX}/check${queryString ? `?${queryString}` : ''}`);
}

// 导出服务对象
export const riskService = {
  // 风险规则
  getRiskRules,
  getRiskRule,
  createRiskRule,
  updateRiskRule,
  deleteRiskRule,
  activateRiskRule,
  deactivateRiskRule,
  // 风险预警
  getRiskAlerts,
  acknowledgeAlert,
  resolveAlert,
  // 风险指标
  getRiskMetrics,
  calculateRiskMetrics,
  // 风控检查
  runRiskCheck,
};

export default riskService;
