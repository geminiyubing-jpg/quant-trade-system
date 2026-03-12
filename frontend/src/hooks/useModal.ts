/**
 * useModal Hook
 * 统一的弹窗状态管理，减少重复代码
 */

import { useState, useCallback } from 'react';

interface UseModalReturn<T = unknown> {
  /** 是否可见 */
  visible: boolean;
  /** 显示弹窗 */
  show: () => void;
  /** 隐藏弹窗 */
  hide: () => void;
  /** 切换显示状态 */
  toggle: () => void;
  /** 显示弹窗并传递数据 */
  showWithData: (data: T) => void;
  /** 获取存储的数据 */
  getData: () => T | null;
  /** 存储的数据 */
  data: T | null;
}

/**
 * 弹窗状态管理 Hook
 *
 * @example
 * // 基础用法
 * const modal = useModal();
 * <Modal open={modal.visible} onCancel={modal.hide} />
 * <Button onClick={modal.show}>打开</Button>
 *
 * @example
 * // 带数据传递
 * const modal = useModal<{ id: string }>();
 * modal.showWithData({ id: '123' });
 * // 在弹窗中获取数据
 * const data = modal.getData();
 */
export function useModal<T = unknown>(): UseModalReturn<T> {
  const [visible, setVisible] = useState(false);
  const [data, setData] = useState<T | null>(null);

  const show = useCallback(() => {
    setVisible(true);
  }, []);

  const hide = useCallback(() => {
    setVisible(false);
  }, []);

  const toggle = useCallback(() => {
    setVisible((prev) => !prev);
  }, []);

  const showWithData = useCallback((newData: T) => {
    setData(newData);
    setVisible(true);
  }, []);

  const getData = useCallback((): T | null => {
    return data;
  }, [data]);

  return {
    visible,
    show,
    hide,
    toggle,
    showWithData,
    getData,
    data,
  };
}

/**
 * 多弹窗状态管理 Hook
 *
 * @example
 * const modals = useModals(['create', 'edit', 'delete'] as const);
 * modals.create.show();
 * modals.edit.showWithData({ id: '123' });
 */
export function useModals<K extends string>(
  keys: readonly K[]
): Record<K, UseModalReturn> {
  const result = {} as Record<K, UseModalReturn>;

  for (const key of keys) {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    result[key] = useModal();
  }

  return result;
}

export default useModal;
