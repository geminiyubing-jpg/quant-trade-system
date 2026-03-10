/**
 * 统一 API 工具
 *
 * 提供通用的 API 请求封装，包括：
 * - Token 自动注入
 * - 错误处理
 * - 响应解析
 */

import { notification } from 'antd';

// API 基础配置
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * 通用 API 请求函数
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  showErrorNotification: boolean = true
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

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
    if (showErrorNotification) {
      notification.error({
        message: '请求失败',
        description: errorMessage,
        placement: 'topRight',
      });
    }
    throw error;
  }
}

/**
 * GET 请求
 */
export async function get<T>(endpoint: string, showErrorNotification: boolean = true): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'GET' }, showErrorNotification);
}

/**
 * POST 请求
 */
export async function post<T>(
  endpoint: string,
  data?: unknown,
  showErrorNotification: boolean = true
): Promise<T> {
  return apiRequest<T>(
    endpoint,
    {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    },
    showErrorNotification
  );
}

/**
 * PUT 请求
 */
export async function put<T>(
  endpoint: string,
  data?: unknown,
  showErrorNotification: boolean = true
): Promise<T> {
  return apiRequest<T>(
    endpoint,
    {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    },
    showErrorNotification
  );
}

/**
 * DELETE 请求
 */
export async function del<T>(endpoint: string, showErrorNotification: boolean = true): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'DELETE' }, showErrorNotification);
}
