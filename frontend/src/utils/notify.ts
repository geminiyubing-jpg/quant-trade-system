/**
 * 统一消息通知 API
 * 提供简洁的通知方法，减少重复代码
 */

import { message, Modal } from 'antd';
import notificationService from '../services/notification';

// 默认持续时间
const DEFAULT_DURATION = {
  success: 3,
  error: 5,
  warning: 4,
  info: 3,
  loading: 0,
};

/**
 * 统一消息通知对象
 *
 * @example
 * import { notify } from '@/utils/notify';
 *
 * notify.success('操作成功');
 * notify.error('操作失败', 10); // 显示10秒
 * notify.apiError(error, '加载数据');
 */
export const notify = {
  /** 成功消息 */
  success: (content: string, duration?: number) => {
    return message.success(content, duration ?? DEFAULT_DURATION.success);
  },

  /** 错误消息 */
  error: (content: string, duration?: number) => {
    return message.error(content, duration ?? DEFAULT_DURATION.error);
  },

  /** 警告消息 */
  warning: (content: string, duration?: number) => {
    return message.warning(content, duration ?? DEFAULT_DURATION.warning);
  },

  /** 信息消息 */
  info: (content: string, duration?: number) => {
    return message.info(content, duration ?? DEFAULT_DURATION.info);
  },

  /** 加载消息 */
  loading: (content: string, duration?: number) => {
    return message.loading(content, duration ?? DEFAULT_DURATION.loading);
  },

  /**
   * API 错误处理
   * 统一处理 API 调用失败的错误消息
   */
  apiError: (error: unknown, operation: string = '操作') => {
    const errorMsg = error instanceof Error ? error.message : String(error);
    return message.error(`${operation}失败: ${errorMsg}`, DEFAULT_DURATION.error);
  },

  /**
   * 显示通知弹窗
   */
  show: (options: {
    title: string;
    body: string;
    type?: 'success' | 'warning' | 'error' | 'info';
    duration?: number;
  }) => {
    return notificationService.show({
      title: options.title,
      body: options.body,
      type: options.type ?? 'info',
      duration: options.duration,
    });
  },

  /**
   * 带确认的删除提示
   */
  confirmDelete: (itemName: string, onConfirm: () => void) => {
    Modal.confirm({
      title: `确认删除`,
      content: `确定要删除 "${itemName}" 吗？此操作不可撤销。`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: onConfirm,
    });
  },
};

/**
 * 操作结果提示
 * 用于统一处理异步操作的结果
 *
 * @example
 * const result = await withNotify(
 *   () => api.post('/orders', data),
 *   '创建订单'
 * );
 */
export async function withNotify<T>(
  operation: () => Promise<T>,
  operationName: string,
  options: {
    successMsg?: string;
    errorMsg?: string;
    showSuccess?: boolean;
    showError?: boolean;
  } = {}
): Promise<T | null> {
  const {
    successMsg = `${operationName}成功`,
    showSuccess = true,
    showError = true,
  } = options;

  try {
    const result = await operation();
    if (showSuccess) {
      notify.success(successMsg);
    }
    return result;
  } catch (error) {
    if (showError) {
      notify.apiError(error, operationName);
    }
    return null;
  }
}

export default notify;
