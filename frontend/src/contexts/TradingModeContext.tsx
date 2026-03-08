/**
 * TradingModeContext - 交易模式上下文
 *
 * 管理全局交易模式状态（PAPER/LIVE）
 * 支持模式切换、持久化存储、组件间共享
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';

export type TradingMode = 'PAPER' | 'LIVE';

interface TradingModeContextType {
  mode: TradingMode;
  setMode: (mode: TradingMode) => void;
  toggleMode: () => void;
  isPaperTrading: boolean;
  isLiveTrading: boolean;
}

const TradingModeContext = createContext<TradingModeContextType | undefined>(undefined);

const STORAGE_KEY = 'quant_trade_trading_mode';

export const TradingModeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [mode, setModeState] = useState<TradingMode>(() => {
    // 从 localStorage 读取保存的模式，默认为 PAPER
    const savedMode = localStorage.getItem(STORAGE_KEY);
    return (savedMode === 'LIVE' || savedMode === 'PAPER') ? savedMode : 'PAPER';
  });

  // 更新模式并持久化
  const setMode = (newMode: TradingMode) => {
    setModeState(newMode);
    localStorage.setItem(STORAGE_KEY, newMode);
  };

  // 切换模式
  const toggleMode = () => {
    setMode(mode === 'PAPER' ? 'LIVE' : 'PAPER');
  };

  // 便捷属性
  const isPaperTrading = mode === 'PAPER';
  const isLiveTrading = mode === 'LIVE';

  return (
    <TradingModeContext.Provider
      value={{
        mode,
        setMode,
        toggleMode,
        isPaperTrading,
        isLiveTrading,
      }}
    >
      {children}
    </TradingModeContext.Provider>
  );
};

// 自定义 Hook 方便使用
export const useTradingMode = (): TradingModeContextType => {
  const context = useContext(TradingModeContext);
  if (!context) {
    throw new Error('useTradingMode must be used within TradingModeProvider');
  }
  return context;
};
