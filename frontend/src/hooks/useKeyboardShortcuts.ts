/**
 * 键盘快捷键 Hook
 */

import { useEffect, useCallback, useRef } from 'react';
import { SHORTCUT_GROUPS, matchShortcut, ShortcutConfig } from '../utils/keyboardShortcuts';

type ShortcutHandler = () => void;

interface UseKeyboardShortcutsOptions {
  /** 是否启用 */
  enabled?: boolean;
  /** 目标元素（默认为 document） */
  target?: HTMLElement | null;
}

/**
 * 全局键盘快捷键 Hook
 */
export const useKeyboardShortcuts = (
  handlers: Record<string, ShortcutHandler>,
  options: UseKeyboardShortcutsOptions = {}
): void => {
  const { enabled = true, target = null } = options;
  const handlersRef = useRef(handlers);

  // 更新 handlers ref
  useEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);

  // 键盘事件处理
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // 忽略输入框中的快捷键（除了 Escape）
      const target = event.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;

      // 遍历所有快捷键配置
      for (const group of SHORTCUT_GROUPS) {
        for (const config of group.shortcuts) {
          if (matchShortcut(event, config)) {
            // 在输入框中只允许 Escape
            if (isInput && config.key !== 'Escape') {
              continue;
            }

            // 查找对应的处理器
            const handlerKey = getHandlerKey(config);
            const handler = handlersRef.current[handlerKey];

            if (handler) {
              event.preventDefault();
              event.stopPropagation();
              handler();
              return;
            }

            // 如果没有自定义处理器，执行默认动作
            config.action();
            return;
          }
        }
      }
    },
    [enabled]
  );

  useEffect(() => {
    const targetElement = target || document;
    targetElement.addEventListener('keydown', handleKeyDown as EventListener);

    return () => {
      targetElement.removeEventListener('keydown', handleKeyDown as EventListener);
    };
  }, [handleKeyDown, target]);
};

/**
 * 获取处理器键名
 */
const getHandlerKey = (config: ShortcutConfig): string => {
  const parts: string[] = [];
  if (config.ctrl) parts.push('ctrl');
  if (config.shift) parts.push('shift');
  if (config.alt) parts.push('alt');
  parts.push(config.key.toLowerCase());
  return parts.join('+');
};

/**
 * 单个快捷键 Hook
 */
export const useShortcut = (
  key: string,
  callback: ShortcutHandler,
  options: {
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
    enabled?: boolean;
  } = {}
): void => {
  const { ctrl = false, shift = false, alt = false, enabled = true } = options;

  const handler = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      const keyMatch = event.key.toLowerCase() === key.toLowerCase();
      const ctrlMatch = ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
      const shiftMatch = shift ? event.shiftKey : !event.shiftKey;
      const altMatch = alt ? event.altKey : !event.altKey;

      if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
        // 忽略输入框中的快捷键
        const target = event.target as HTMLElement;
        const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;

        if (!isInput || key === 'Escape') {
          event.preventDefault();
          callback();
        }
      }
    },
    [key, ctrl, shift, alt, enabled, callback]
  );

  useEffect(() => {
    document.addEventListener('keydown', handler as EventListener);
    return () => {
      document.removeEventListener('keydown', handler as EventListener);
    };
  }, [handler]);
};

export default useKeyboardShortcuts;
