/**
 * ==============================================
 * 价格历史数据 Hook
 * ==============================================
 */

import { useState, useEffect, useRef } from 'react';
import type { Quote } from '../types/market';

interface PriceHistory {
  [symbol: string]: Quote[];
}

const MAX_HISTORY_LENGTH = 100; // 每个股票最多保存100条历史数据

export const usePriceHistory = (quotes: Record<string, Quote>, subscribedSymbols: string[]) => {
  const [priceHistory, setPriceHistory] = useState<PriceHistory>({});
  const initializedRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    // 初始化每个订阅股票的历史数据
    subscribedSymbols.forEach((symbol) => {
      if (!initializedRef.current.has(symbol)) {
        initializedRef.current.add(symbol);
        setPriceHistory((prev) => ({
          ...prev,
          [symbol]: [],
        }));
      }
    });
  }, [subscribedSymbols]);

  useEffect(() => {
    // 当收到新的行情数据时，更新所有股票的历史记录
    Object.values(quotes).forEach((quote) => {
      if (!quote.symbol) return;

      const symbol = quote.symbol;

      setPriceHistory((prev) => {
        const history = prev[symbol] || [];

        // 避免重复数据（相同时间戳）
        const lastQuote = history[history.length - 1];
        if (lastQuote && lastQuote.timestamp === quote.timestamp) {
          return prev;
        }

        // 添加新数据并限制长度
        const newHistory = [...history, quote];

        // 保留最新的 MAX_HISTORY_LENGTH 条数据
        const limitedHistory =
          newHistory.length > MAX_HISTORY_LENGTH
            ? newHistory.slice(newHistory.length - MAX_HISTORY_LENGTH)
            : newHistory;

        return {
          ...prev,
          [symbol]: limitedHistory,
        };
      });
    });
  }, [quotes]);

  // 获取指定股票的历史数据
  const getHistory = (symbol: string): Quote[] => {
    return priceHistory[symbol] || [];
  };

  // 清除指定股票的历史数据
  const clearHistory = (symbol: string) => {
    setPriceHistory((prev) => {
      const { [symbol]: _, ...rest } = prev;
      return rest;
    });
    initializedRef.current.delete(symbol);
  };

  // 清除所有历史数据
  const clearAllHistory = () => {
    setPriceHistory({});
    initializedRef.current.clear();
  };

  return {
    priceHistory,
    getHistory,
    clearHistory,
    clearAllHistory,
  };
};
