/**
 * 交易模式API服务
 * 
 * 负责与后端API交互，管理交易模式的切换和状态
 */

import { notification } from 'antd';

// 交易模式类型
export type TradingMode = 'PAPER' | 'LIVE';

// 模式切换请求参数
export interface TradingModeSwitchRequest {
  mode: TradingMode;
  password?: string;
  confirm: boolean;
}

// 模式切换响应
export interface TradingModeSwitchResponse {
  success: boolean;
  mode: TradingMode;
  message: string;
  previous_mode: TradingMode;
}

// 模式状态响应
export interface TradingModeStatus {
  current_mode: TradingMode;
  can_switch_to_live: boolean;
  requirements: string[];
  warning_message?: string;
}

// API基础URL配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1/trading';

/**
 * 通用API请求函数
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // 发送cookies
    ...options,
  };
  
  try {
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      
      throw new Error(errorData.detail || 'API请求失败');
    }
    
    return await response.json();
  } catch (error) {
    // 记录错误并抛出
    console.error('API request failed:', error);
    throw error;
  }
}

/**
 * 获取当前交易模式
 */
export async function getTradingModeStatus(): Promise<TradingModeStatus> {
  return apiRequest<TradingModeStatus>('/mode');
}

/**
 * 切换交易模式
 *
 * @param mode - 目标模式（PAPER 或 LIVE）
 * @param password - 实盘模式密码（可选）
 * @returns 切换结果
 */
export async function switchTradingMode(
  mode: TradingMode,
  password?: string
): Promise<TradingModeSwitchResponse> {
  try {
    const response = await apiRequest<TradingModeSwitchResponse>('/mode/switch', {
      method: 'POST',
      body: JSON.stringify({
        mode,
        password,
        confirm: true,
      } as TradingModeSwitchRequest),
    });
    
    // 显示成功通知
    notification.success({
      message: response.message,
      description: '交易模式已切换',
      placement: 'topRight',
    });
    
    return response;
  } catch (error: unknown) {
    // 显示错误通知
    const errorMessage = error instanceof Error ? error.message : '切换失败';
    
    notification.error({
      message: '交易模式切换失败',
      description: errorMessage,
      placement: 'topRight',
    });
    
    throw error;
  }
}

/**
 * 检查是否可以切换到实盘模式
 */
export async function canSwitchToLive(): Promise<boolean> {
  try {
    const status = await getTradingModeStatus();
    return status.can_switch_to_live;
  } catch {
    return false;
  }
}
