/**
 * ==============================================
 * 主题上下文 - 白天/夜晚模式
 * ==============================================
 * 支持自动切换（根据系统时间）和手动切换
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

// 主题类型
export type ThemeMode = 'light' | 'dark';
export type ThemeSource = 'auto' | 'manual';

interface ThemeContextType {
  // 当前主题
  theme: ThemeMode;
  // 主题来源
  source: ThemeSource;
  // 切换主题
  toggleTheme: () => void;
  // 设置主题
  setTheme: (theme: ThemeMode) => void;
  // 设置自动模式
  setAutoMode: () => void;
  // 是否是自动模式
  isAutoMode: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// 根据时间判断应该使用哪个主题
const getThemeByTime = (): ThemeMode => {
  const hour = new Date().getHours();
  // 6:00 - 18:00 为白天模式，18:00 - 6:00 为夜晚模式
  return hour >= 6 && hour < 18 ? 'light' : 'dark';
};

// 主题配置
const themeConfig = {
  light: {
    // 背景色 - 精致的灰白色系，专业金融感
    '--bg-primary': '#f8fafc',
    '--bg-secondary': '#ffffff',
    '--bg-card': '#ffffff',
    '--bg-table': '#fafbfc',
    '--bg-input': '#ffffff',
    // Header 和 Sidebar 背景 - 深沉优雅的蓝色系
    '--bg-header': '#1e3a5f',           // 深蓝色背景
    '--bg-header-border': '#2d4a6f',    // 深蓝色边框
    '--bg-sidebar': '#1e3a5f',          // 深蓝色侧边栏
    '--bg-sidebar-hover': '#2d4a6f',    // 侧边栏悬停
    '--bg-sidebar-active': '#3d5a7f',   // 侧边栏激活
    // 文字色 - 高对比度深色系（优化对比度）
    '--text-primary': '#0f172a',        // 主文字 - 深黑
    '--text-secondary': '#334155',      // 次要文字 - 深灰（从 #475569 调深）
    '--text-muted': '#64748b',          // 弱化文字 - 中灰（从 #94a3b8 调深）
    // 强调色 - 协调的蓝色系 + 金色点缀
    '--accent-gold': '#d97706',
    '--accent-blue': '#0284c7',
    '--accent-cyan': '#0891b2',
    '--accent-primary': '#0284c7',
    '--accent-secondary': '#0369a1',
    // 状态色 - 红涨绿跌（中国市场习惯）
    '--color-up': '#dc2626',      // 红色 - 涨
    '--color-down': '#16a34a',    // 绿色 - 跌
    '--color-neutral': '#6b7280',
    // 边框色 - 精致边框
    '--border-color': '#e2e8f0',
    '--border-light': '#f1f5f9',
    '--border-focus': '#0284c7',
    // 网格背景
    '--grid-color': 'rgba(148, 163, 184, 0.08)',
    // 阴影系统 - 多层次精致阴影
    '--shadow-color': 'rgba(15, 23, 42, 0.08)',
    '--shadow-sm': '0 1px 2px rgba(15, 23, 42, 0.04)',
    '--shadow-md': '0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -1px rgba(15, 23, 42, 0.04)',
    '--shadow-lg': '0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -2px rgba(15, 23, 42, 0.04)',
    '--shadow-xl': '0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 10px 10px -5px rgba(15, 23, 42, 0.04)',
    // 交互状态
    '--hover-bg': '#f1f5f9',
    '--hover-bg-deep': '#e2e8f0',
    '--active-bg': '#e0f2fe',
    // 卡片样式
    '--card-shadow': '0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)',
    '--card-shadow-hover': '0 10px 20px -5px rgba(15, 23, 42, 0.1), 0 4px 6px -2px rgba(15, 23, 42, 0.04)',
    '--card-border': '1px solid #e2e8f0',
    '--card-radius': '12px',
    // 表格样式
    '--table-row-hover': '#f8fafc',
    '--table-row-up': 'rgba(220, 38, 38, 0.08)',     // 红色背景 - 涨
    '--table-row-down': 'rgba(22, 163, 74, 0.08)',   // 绿色背景 - 跌
    '--table-header-bg': '#f1f5f9',                  // 表头背景（从 #f8fafc 调深）
    // 输入框样式
    '--input-focus-border': '#0284c7',
    '--input-focus-shadow': '0 0 0 3px rgba(2, 132, 199, 0.15)',
    // 按钮样式
    '--button-primary-bg': '#0284c7',
    '--button-primary-hover': '#0369a1',
    '--button-primary-shadow': '0 2px 4px rgba(2, 132, 199, 0.2)',
    // 标签样式
    '--tag-bg': '#f1f5f9',
    '--tag-border': '#e2e8f0',
    // 统计数字
    '--statistic-title': '#475569',                  // 统计标题（从 #64748b 调深）
    // 渐变背景
    '--gradient-primary': 'linear-gradient(135deg, #f8fafc 0%, #ffffff 50%, #f1f5f9 100%)',
    '--gradient-header': 'linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%)',
    // 光晕效果
    '--glow-blue': '0 0 20px rgba(2, 132, 199, 0.15)',
    '--glow-gold': '0 0 20px rgba(217, 119, 6, 0.15)',
  },
  dark: {
    // 背景色 - 彭博终端纯黑风格
    '--bg-primary': '#000000',
    '--bg-secondary': '#0a0a0a',
    '--bg-card': 'rgba(10, 10, 10, 0.95)',
    '--bg-table': 'rgba(0, 0, 0, 0.3)',
    '--bg-input': 'rgba(255, 107, 0, 0.05)',
    // Header 和 Sidebar 背景 - 彭博橙主题
    '--bg-header': '#0a0a0a',
    '--bg-header-border': 'rgba(255, 107, 0, 0.3)',
    '--bg-sidebar': '#0a0a0a',
    '--bg-sidebar-hover': 'rgba(255, 107, 0, 0.1)',
    '--bg-sidebar-active': 'rgba(255, 107, 0, 0.15)',
    // 文字色
    '--text-primary': '#f0f0f0',
    '--text-secondary': '#a0a0a0',
    '--text-muted': '#666666',
    // 强调色 - 彭博橙 + 青色
    '--accent-gold': '#ff6b00',
    '--accent-blue': '#00d4ff',
    '--accent-cyan': '#00ffcc',
    '--accent-primary': '#ff6b00',
    '--accent-secondary': '#ff8533',
    // 状态色 - 红涨绿跌（中国市场习惯）
    '--color-up': '#ff4757',      // 红色 - 涨
    '--color-down': '#00d26a',    // 绿色 - 跌
    '--color-neutral': '#a0a0a0',
    // 边框色
    '--border-color': 'rgba(255, 107, 0, 0.2)',
    '--border-light': 'rgba(255, 107, 0, 0.1)',
    '--border-focus': '#ff6b00',
    // 网格背景
    '--grid-color': 'rgba(255, 107, 0, 0.03)',
    // 阴影系统
    '--shadow-color': 'rgba(0, 0, 0, 0.8)',
    '--shadow-sm': '0 1px 2px rgba(0, 0, 0, 0.5)',
    '--shadow-md': '0 4px 6px -1px rgba(0, 0, 0, 0.6)',
    '--shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.7)',
    '--shadow-xl': '0 20px 25px -5px rgba(0, 0, 0, 0.8)',
    // 交互状态
    '--hover-bg': 'rgba(255, 107, 0, 0.08)',
    '--hover-bg-deep': 'rgba(255, 107, 0, 0.12)',
    '--active-bg': 'rgba(255, 107, 0, 0.15)',
    // 卡片样式
    '--card-shadow': '0 4px 20px rgba(0, 0, 0, 0.6), 0 0 1px rgba(255, 107, 0, 0.2)',
    '--card-shadow-hover': '0 8px 30px rgba(0, 0, 0, 0.7), 0 0 2px rgba(255, 107, 0, 0.4)',
    '--card-border': '1px solid rgba(255, 107, 0, 0.2)',
    '--card-radius': '8px',
    // 表格样式
    '--table-row-hover': 'rgba(255, 107, 0, 0.05)',
    '--table-row-up': 'rgba(255, 215, 0, 0.08)',
    '--table-row-down': 'rgba(255, 71, 87, 0.08)',
    '--table-header-bg': 'rgba(255, 107, 0, 0.05)',
    // 输入框样式
    '--input-focus-border': '#ff6b00',
    '--input-focus-shadow': '0 0 0 2px rgba(255, 107, 0, 0.2)',
    // 按钮样式
    '--button-primary-bg': '#ff6b00',
    '--button-primary-hover': '#ff8533',
    '--button-primary-shadow': '0 2px 8px rgba(255, 107, 0, 0.4)',
    // 标签样式
    '--tag-bg': 'rgba(255, 107, 0, 0.1)',
    '--tag-border': 'rgba(255, 107, 0, 0.3)',
    // 统计数字
    '--statistic-title': '#a0a0a0',
    // 渐变背景
    '--gradient-primary': 'linear-gradient(135deg, #000000 0%, #0a0a0a 50%, #0d0d0d 100%)',
    '--gradient-header': 'linear-gradient(135deg, #0a0a0a 0%, #141414 100%)',
    // 光晕效果
    '--glow-orange': '0 0 20px rgba(255, 107, 0, 0.3)',
    '--glow-gold': '0 0 20px rgba(255, 215, 0, 0.3)',
    '--glow-cyan': '0 0 20px rgba(0, 212, 255, 0.3)',
  },
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // 从 localStorage 读取设置
  const getInitialTheme = (): ThemeMode => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') {
      return saved;
    }
    return getThemeByTime();
  };

  const getInitialSource = (): ThemeSource => {
    const saved = localStorage.getItem('theme_source');
    if (saved === 'manual') {
      return 'manual';
    }
    return 'auto';
  };

  const [theme, setThemeState] = useState<ThemeMode>(getInitialTheme);
  const [source, setSourceState] = useState<ThemeSource>(getInitialSource);

  // 应用主题到 CSS 变量
  const applyTheme = useCallback((newTheme: ThemeMode) => {
    const root = document.documentElement;
    const config = themeConfig[newTheme];

    Object.entries(config).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });

    // 设置 data 属性用于 CSS 选择器
    root.setAttribute('data-theme', newTheme);
  }, []);

  // 设置主题
  const setTheme = useCallback((newTheme: ThemeMode) => {
    setThemeState(newTheme);
    setSourceState('manual');
    localStorage.setItem('theme', newTheme);
    localStorage.setItem('theme_source', 'manual');
    applyTheme(newTheme);
  }, [applyTheme]);

  // 设置自动模式
  const setAutoMode = useCallback(() => {
    setSourceState('auto');
    localStorage.setItem('theme_source', 'auto');
    const autoTheme = getThemeByTime();
    setThemeState(autoTheme);
    applyTheme(autoTheme);
  }, [applyTheme]);

  // 切换主题
  const toggleTheme = useCallback(() => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  }, [theme, setTheme]);

  // 初始化主题
  useEffect(() => {
    if (source === 'auto') {
      applyTheme(getThemeByTime());
    } else {
      applyTheme(theme);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 自动模式下，每小时检查一次时间
  useEffect(() => {
    if (source !== 'auto') return;

    const checkAndApply = () => {
      const autoTheme = getThemeByTime();
      if (autoTheme !== theme) {
        setThemeState(autoTheme);
        applyTheme(autoTheme);
      }
    };

    // 每分钟检查一次
    const interval = setInterval(checkAndApply, 60000);

    // 在整点时也检查
    const now = new Date();
    const msToNextMinute = (60 - now.getSeconds()) * 1000;
    const timeout = setTimeout(() => {
      checkAndApply();
    }, msToNextMinute);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [source, theme, applyTheme]);

  const value: ThemeContextType = {
    theme,
    source,
    toggleTheme,
    setTheme,
    setAutoMode,
    isAutoMode: source === 'auto',
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeContext;
