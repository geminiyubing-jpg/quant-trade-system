/**
 * 键盘快捷键配置
 */

export interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  description: string;
  action: () => void;
}

export interface ShortcutGroup {
  name: string;
  shortcuts: ShortcutConfig[];
}

// 快捷键配置
export const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    name: '通用',
    shortcuts: [
      {
        key: 'k',
        ctrl: true,
        description: '打开搜索/命令面板',
        action: () => {
          window.dispatchEvent(new CustomEvent('shortcut:search'));
        },
      },
      {
        key: 'Escape',
        description: '关闭弹窗/取消操作',
        action: () => {
          window.dispatchEvent(new CustomEvent('shortcut:escape'));
        },
      },
    ],
  },
  {
    name: '自选股',
    shortcuts: [
      {
        key: 'd',
        ctrl: true,
        description: '添加当前股票到自选',
        action: () => {
          window.dispatchEvent(new CustomEvent('shortcut:addToWatchlist'));
        },
      },
    ],
  },
  {
    name: '导出',
    shortcuts: [
      {
        key: 'e',
        ctrl: true,
        description: '导出当前视图',
        action: () => {
          window.dispatchEvent(new CustomEvent('shortcut:export'));
        },
      },
    ],
  },
  {
    name: '导航',
    shortcuts: [
      {
        key: 'ArrowUp',
        description: '向上移动选中行',
        action: () => {
          window.dispatchEvent(new CustomEvent('shortcut:navigate', { detail: { direction: 'up' } }));
        },
      },
      {
        key: 'ArrowDown',
        description: '向下移动选中行',
        action: () => {
          window.dispatchEvent(new CustomEvent('shortcut:navigate', { detail: { direction: 'down' } }));
        },
      },
      {
        key: 'Enter',
        description: '打开股票详情',
        action: () => {
          window.dispatchEvent(new CustomEvent('shortcut:openDetail'));
        },
      },
    ],
  },
];

/**
 * 检查快捷键是否匹配
 */
export const matchShortcut = (
  event: KeyboardEvent,
  config: ShortcutConfig
): boolean => {
  const keyMatch = event.key.toLowerCase() === config.key.toLowerCase();
  const ctrlMatch = config.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
  const shiftMatch = config.shift ? event.shiftKey : !event.shiftKey;
  const altMatch = config.alt ? event.altKey : !event.altKey;

  return keyMatch && ctrlMatch && shiftMatch && altMatch;
};

/**
 * 获取快捷键显示文本
 */
export const getShortcutText = (config: ShortcutConfig): string => {
  const parts: string[] = [];

  if (config.ctrl) {
    parts.push(navigator.platform.includes('Mac') ? '⌘' : 'Ctrl');
  }
  if (config.shift) {
    parts.push('Shift');
  }
  if (config.alt) {
    parts.push(navigator.platform.includes('Mac') ? '⌥' : 'Alt');
  }

  // 特殊键名映射
  const keyNames: Record<string, string> = {
    ArrowUp: '↑',
    ArrowDown: '↓',
    ArrowLeft: '←',
    ArrowRight: '→',
    Escape: 'Esc',
    Enter: '↵',
    Space: '空格',
  };

  parts.push(keyNames[config.key] || config.key.toUpperCase());

  return parts.join(' + ');
};

/**
 * 获取所有快捷键列表（用于帮助面板）
 */
export const getAllShortcuts = (): { key: string; description: string }[] => {
  const result: { key: string; description: string }[] = [];

  SHORTCUT_GROUPS.forEach((group) => {
    group.shortcuts.forEach((shortcut) => {
      result.push({
        key: getShortcutText(shortcut),
        description: shortcut.description,
      });
    });
  });

  return result;
};

/**
 * 格式化快捷键帮助文本
 */
export const formatShortcutsHelp = (): string => {
  const lines: string[] = ['键盘快捷键帮助', '=' .repeat(20)];

  SHORTCUT_GROUPS.forEach((group) => {
    lines.push(`\n【${group.name}】`);
    group.shortcuts.forEach((shortcut) => {
      lines.push(`  ${getShortcutText(shortcut)} - ${shortcut.description}`);
    });
  });

  return lines.join('\n');
};
