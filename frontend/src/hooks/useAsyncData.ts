/**
 * useAsyncData Hook
 * 统一的异步数据加载 Hook，减少重复代码
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { message } from 'antd';

interface AsyncDataState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface UseAsyncDataOptions<T> {
  /** 初始数据 */
  initialData?: T | null;
  /** 是否立即执行 */
  immediate?: boolean;
  /** 成功回调 */
  onSuccess?: (data: T) => void;
  /** 错误回调 */
  onError?: (error: Error) => void;
  /** 自定义错误消息 */
  errorMessage?: string;
  /** 是否显示错误提示 */
  showErrorToast?: boolean;
  /** 依赖项数组，变化时重新加载 */
  deps?: unknown[];
}

interface UseAsyncDataReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: () => Promise<T | null>;
  refetch: () => Promise<T | null>;
  setData: React.Dispatch<React.SetStateAction<T | null>>;
  reset: () => void;
}

/**
 * 异步数据加载 Hook
 *
 * @example
 * // 基础用法
 * const { data, loading, refetch } = useAsyncData(
 *   () => api.get('/portfolios'),
 *   []
 * );
 *
 * @example
 * // 带依赖项
 * const { data, loading } = useAsyncData(
 *   () => api.get(`/users/${userId}`),
 *   [userId]
 * );
 *
 * @example
 * // 手动触发
 * const { data, loading, execute } = useAsyncData(
 *   () => api.post('/orders', orderData),
 *   [],
 *   { immediate: false }
 * );
 */
export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options: UseAsyncDataOptions<T> = {}
): UseAsyncDataReturn<T> {
  const {
    initialData = null,
    immediate = true,
    onSuccess,
    onError,
    errorMessage = '加载失败',
    showErrorToast = true,
  } = options;

  const [state, setState] = useState<AsyncDataState<T>>({
    data: initialData,
    loading: immediate,
    error: null,
  });

  // 使用 ref 存储最新的 fetcher，避免闭包问题
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const execute = useCallback(async (): Promise<T | null> => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const result = await fetcherRef.current();
      setState({ data: result, loading: false, error: null });
      onSuccess?.(result);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setState((prev) => ({ ...prev, loading: false, error }));

      if (showErrorToast) {
        message.error(`${errorMessage}: ${error.message}`);
      }

      onError?.(error);
      return null;
    }
  }, [errorMessage, showErrorToast, onSuccess, onError]);

  const refetch = useCallback(async (): Promise<T | null> => {
    return execute();
  }, [execute]);

  const reset = useCallback(() => {
    setState({ data: initialData, loading: false, error: null });
  }, [initialData]);

  const setData = useCallback<React.Dispatch<React.SetStateAction<T | null>>>(
    (action) => {
      setState((prev) => ({
        ...prev,
        data: typeof action === 'function' ? (action as (prev: T | null) => T | null)(prev.data) : action,
      }));
    },
    []
  );

  // 自动执行
  useEffect(() => {
    if (immediate) {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return {
    ...state,
    execute,
    refetch,
    setData,
    reset,
  };
}

export default useAsyncData;
