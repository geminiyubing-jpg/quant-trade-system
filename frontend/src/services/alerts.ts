/**
 * 价格预警 API 服务
 */

import { notification } from 'antd';
import type {
  PriceAlert,
  AlertHistory,
  PriceAlertListResponse,
  AlertHistoryListResponse,
  PriceAlertCreate,
  PriceAlertUpdate,
  AlertSettings,
  AlertSettingsUpdate,
  UnreadCountResponse,
} from '../types/alert';

// API 基础配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1/alerts';

/**
 * 通用 API 请求函数
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;

  // 获取 Token
  const authState = localStorage.getItem('auth');
  let token = '';
  if (authState) {
    try {
      const auth = JSON.parse(authState);
      token = auth.accessToken || '';
    } catch {
      // ignore
    }
  }

  const defaultOptions: RequestInit = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  };

  try {
    const response = await fetch(url, defaultOptions);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new Error(errorData.detail || 'API 请求失败');
    }

    // 204 No Content
    if (response.status === 204) {
      return undefined as unknown as T;
    }

    return await response.json();
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '操作失败';
    notification.error({
      message: '预警操作失败',
      description: errorMessage,
      placement: 'topRight',
    });
    throw error;
  }
}

// ==============================================
// 价格预警 API
// ==============================================

/**
 * 获取预警列表
 */
export const getAlerts = async (params?: {
  is_active?: boolean;
  symbol?: string;
}): Promise<PriceAlertListResponse> => {
  const searchParams = new URLSearchParams();
  if (params?.is_active !== undefined) {
    searchParams.append('is_active', String(params.is_active));
  }
  if (params?.symbol) {
    searchParams.append('symbol', params.symbol);
  }
  const queryString = searchParams.toString();
  return apiRequest<PriceAlertListResponse>(`/${queryString ? `?${queryString}` : ''}`);
};

/**
 * 创建预警
 */
export const createAlert = async (data: PriceAlertCreate): Promise<PriceAlert> => {
  return apiRequest<PriceAlert>('', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * 更新预警
 */
export const updateAlert = async (alertId: string, data: PriceAlertUpdate): Promise<PriceAlert> => {
  return apiRequest<PriceAlert>(`/${alertId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
};

/**
 * 删除预警
 */
export const deleteAlert = async (alertId: string): Promise<void> => {
  return apiRequest<void>(`/${alertId}`, {
    method: 'DELETE',
  });
};

// ==============================================
// 预警历史 API
// ==============================================

/**
 * 获取预警历史
 */
export const getHistory = async (params?: {
  symbol?: string;
  acknowledged?: boolean;
  limit?: number;
}): Promise<AlertHistoryListResponse> => {
  const searchParams = new URLSearchParams();
  if (params?.symbol) {
    searchParams.append('symbol', params.symbol);
  }
  if (params?.acknowledged !== undefined) {
    searchParams.append('acknowledged', String(params.acknowledged));
  }
  if (params?.limit) {
    searchParams.append('limit', String(params.limit));
  }
  const queryString = searchParams.toString();
  return apiRequest<AlertHistoryListResponse>(`/history${queryString ? `?${queryString}` : ''}`);
};

/**
 * 确认预警历史
 */
export const acknowledgeHistory = async (historyId: string, acknowledged: boolean = true): Promise<AlertHistory> => {
  return apiRequest<AlertHistory>(`/history/${historyId}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ acknowledged }),
  });
};

// ==============================================
// 预警设置 API
// ==============================================

/**
 * 获取预警设置
 */
export const getSettings = async (): Promise<AlertSettings> => {
  return apiRequest<AlertSettings>('/settings');
};

/**
 * 更新预警设置
 */
export const updateSettings = async (data: AlertSettingsUpdate): Promise<AlertSettings> => {
  return apiRequest<AlertSettings>('/settings', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
};

// ==============================================
// 未读数量 API
// ==============================================

/**
 * 获取未确认预警数量
 */
export const getUnreadCount = async (): Promise<number> => {
  const response = await apiRequest<UnreadCountResponse>('/unread-count');
  return response.count;
};

export default {
  getAlerts,
  createAlert,
  updateAlert,
  deleteAlert,
  getHistory,
  acknowledgeHistory,
  getSettings,
  updateSettings,
  getUnreadCount,
};
