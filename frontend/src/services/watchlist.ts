/**
 * 自选股 API 服务
 */

import { notification } from 'antd';
import type {
  WatchlistGroup,
  WatchlistItem,
  WatchlistGroupListResponse,
  WatchlistItemListResponse,
  WatchlistGroupCreate,
  WatchlistGroupUpdate,
  WatchlistItemCreate,
  WatchlistItemUpdate,
  BatchAddItemsRequest,
  BatchRemoveItemsRequest,
  BatchMoveItemsRequest,
  BatchOperationResponse,
} from '../types/watchlist';

// API 基础配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1/watchlist';

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
      message: '自选股操作失败',
      description: errorMessage,
      placement: 'topRight',
    });
    throw error;
  }
}

// ==============================================
// 分组 API
// ==============================================

/**
 * 获取所有分组
 */
export const getGroups = async (): Promise<WatchlistGroupListResponse> => {
  return apiRequest<WatchlistGroupListResponse>('/groups');
};

/**
 * 创建分组
 */
export const createGroup = async (data: WatchlistGroupCreate): Promise<WatchlistGroup> => {
  return apiRequest<WatchlistGroup>('/groups', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * 更新分组
 */
export const updateGroup = async (groupId: string, data: WatchlistGroupUpdate): Promise<WatchlistGroup> => {
  return apiRequest<WatchlistGroup>(`/groups/${groupId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
};

/**
 * 删除分组
 */
export const deleteGroup = async (groupId: string): Promise<void> => {
  return apiRequest<void>(`/groups/${groupId}`, {
    method: 'DELETE',
  });
};

// ==============================================
// 自选股项目 API
// ==============================================

/**
 * 获取自选股列表
 */
export const getItems = async (groupId?: string): Promise<WatchlistItemListResponse> => {
  const params = groupId ? `?group_id=${groupId}` : '';
  return apiRequest<WatchlistItemListResponse>(`/items${params}`);
};

/**
 * 添加自选股
 */
export const addItem = async (data: WatchlistItemCreate): Promise<WatchlistItem> => {
  return apiRequest<WatchlistItem>('/items', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * 更新自选股
 */
export const updateItem = async (symbol: string, data: WatchlistItemUpdate): Promise<WatchlistItem> => {
  return apiRequest<WatchlistItem>(`/items/${symbol}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
};

/**
 * 移除自选股
 */
export const removeItem = async (symbol: string): Promise<void> => {
  return apiRequest<void>(`/items/${symbol}`, {
    method: 'DELETE',
  });
};

// ==============================================
// 批量操作 API
// ==============================================

/**
 * 批量添加自选股
 */
export const batchAddItems = async (data: BatchAddItemsRequest): Promise<BatchOperationResponse> => {
  return apiRequest<BatchOperationResponse>('/items/batch/add', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * 批量移除自选股
 */
export const batchRemoveItems = async (data: BatchRemoveItemsRequest): Promise<BatchOperationResponse> => {
  return apiRequest<BatchOperationResponse>('/items/batch/remove', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * 批量移动自选股
 */
export const batchMoveItems = async (data: BatchMoveItemsRequest): Promise<BatchOperationResponse> => {
  return apiRequest<BatchOperationResponse>('/items/batch/move', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

// ==============================================
// 便捷方法
// ==============================================

/**
 * 检查股票是否在自选中
 */
export const isInWatchlist = async (symbol: string): Promise<boolean> => {
  try {
    const response = await getItems();
    return response.items.some((item) => item.symbol === symbol);
  } catch {
    return false;
  }
};

/**
 * 切换自选状态
 */
export const toggleWatchlist = async (symbol: string, groupId?: string): Promise<boolean> => {
  try {
    const response = await getItems();
    const exists = response.items.find((item) => item.symbol === symbol);

    if (exists) {
      await removeItem(symbol);
      notification.success({
        message: '已从自选移除',
        description: `${symbol} 已从自选股列表移除`,
        placement: 'topRight',
      });
      return false;
    } else {
      await addItem({ symbol, group_id: groupId });
      notification.success({
        message: '已添加到自选',
        description: `${symbol} 已添加到自选股列表`,
        placement: 'topRight',
      });
      return true;
    }
  } catch (error) {
    console.error('切换自选状态失败:', error);
    throw error;
  }
};

export default {
  // 分组
  getGroups,
  createGroup,
  updateGroup,
  deleteGroup,
  // 项目
  getItems,
  addItem,
  updateItem,
  removeItem,
  // 批量操作
  batchAddItems,
  batchRemoveItems,
  batchMoveItems,
  // 便捷方法
  isInWatchlist,
  toggleWatchlist,
};
