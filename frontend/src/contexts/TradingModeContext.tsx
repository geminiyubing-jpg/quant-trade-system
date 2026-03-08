/**
 * TradingModeContext - 交易模式上下文
 *
 * 管理全局交易模式状态（PAPER/LIVE）
 * 支持模式切换、持久化存储、API对接、组件间共享
 */

import React, { useContext, useState, useEffect, ReactNode } from 'react';
import * as tradingModeApi from '../services/tradingMode';

export type TradingMode = 'PAPER' | 'LIVE';

interface TradingModeContextType {
  mode: TradingMode;
  setMode: (mode: TradingMode) => Promise<void>;
  toggleMode: () => Promise<void>;
  isPaperTrading: boolean;
  isLiveTrading: boolean;
  isLoading: boolean;
}

// 创建 Context
const TradingModeContext = React.createContext<TradingModeContextType | undefined>(undefined);

const STORAGE_KEY = 'quant_trade_trading_mode';

export const TradingModeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [mode, setModeState] = useState<TradingMode>(() => {
    // 从 localStorage 读取保存的模式，默认为 PAPER
    const savedMode = localStorage.getItem(STORAGE_KEY);
    return (savedMode === 'LIVE' || savedMode === 'PAPER') ? savedMode : 'PAPER';
  });

  const [isLoading, setIsLoading] = useState(false);

  // 组件挂载时，从后端API同步模式
  useEffect(() => {
    const syncModeFromBackend = async () => {
      try {
        const status = await tradingModeApi.getTradingModeStatus();
        const backendMode = status.current_mode;

        // 如果后端模式与本地不一致，以后端为准
        if (backendMode !== mode) {
          setModeState(backendMode);
          localStorage.setItem(STORAGE_KEY, backendMode);
        }
      } catch (error) {
        console.error('Failed to sync mode from backend:', error);
        // 如果后端不可用，继续使用本地存储的模式
      }
    };

    syncModeFromBackend();
  }, []); // 只在组件挂载时执行一次

  // 更新模式并同步到后端和本地存储
  const setMode = async (newMode: TradingMode) => {
    setIsLoading(true);

    try {
      // 先调用后端API切换模式
      await tradingModeApi.switchTradingMode(newMode);

      // 后端成功后，更新本地状态
      setModeState(newMode);
      localStorage.setItem(STORAGE_KEY, newMode);
    } catch (error) {
      console.error('Failed to switch mode via API:', error);

      // 如果后端调用失败，询问用户是否仅更新本地状态
      // 实际实现中可以显示确认对话框
      const shouldUpdateLocal = window.confirm(
        '后端API调用失败，是否仅更新本地显示模式？（此操作不会持久到服务器）'
      );

      if (shouldUpdateLocal) {
        setModeState(newMode);
        localStorage.setItem(STORAGE_KEY, newMode);
      } else {
        throw error;
      }
    } finally {
      setIsLoading(false);
    }
  };

  // 切换模式
  const toggleMode = async () => {
    const newMode = mode === 'PAPER' ? 'LIVE' : 'PAPER';
    await setMode(newMode);
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
        isLoading,
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
