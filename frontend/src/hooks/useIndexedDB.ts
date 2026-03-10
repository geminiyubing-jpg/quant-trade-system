/**
 * ==============================================
 * IndexedDB Hook
 * ==============================================
 * 在组件中方便地使用 IndexedDB 缓存
 */

import { useState, useEffect, useCallback } from 'react';
import indexedDB, {
  CachedQuote,
  PriceHistoryRecord,
} from '../services/indexedDB';

interface UseIndexedDBReturn {
  // 状态
  loading: boolean;
  error: Error | null;
  stats: {
    quotesCount: number;
    historyCount: number;
    symbolsCount: number;
  };

  // 行情缓存操作
  cacheQuote: (quote: CachedQuote) => Promise<void>;
  cacheQuotes: (quotes: CachedQuote[]) => Promise<void>;
  getCachedQuote: (symbol: string) => Promise<CachedQuote | undefined>;
  getQuoteHistory: (symbol: string, limit?: number) => Promise<CachedQuote[]>;

  // 价格历史操作
  addPriceHistory: (record: Omit<PriceHistoryRecord, 'id' | 'createdAt'>) => Promise<void>;
  getPriceHistory: (symbol: string, limit?: number) => Promise<PriceHistoryRecord[]>;

  // 缓存管理
  clearAllCache: () => Promise<void>;
  clearSymbolCache: (symbol: string) => Promise<void>;
  cleanupOldData: (daysToKeep?: number) => Promise<number>;
  refreshStats: () => Promise<void>;
}

/**
 * IndexedDB Hook
 */
export const useIndexedDB = (): UseIndexedDBReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [stats, setStats] = useState({
    quotesCount: 0,
    historyCount: 0,
    symbolsCount: 0,
  });

  // 刷新统计信息
  const refreshStats = useCallback(async () => {
    try {
      const newStats = await indexedDB.getCacheStats();
      setStats(newStats);
    } catch (err) {
      console.error('刷新缓存统计失败:', err);
    }
  }, []);

  // 初始化时获取统计信息
  useEffect(() => {
    refreshStats();
  }, [refreshStats]);

  // 缓存单个行情
  const handleCacheQuote = useCallback(async (quote: CachedQuote) => {
    setLoading(true);
    setError(null);
    try {
      await indexedDB.cacheQuote(quote);
      await refreshStats();
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [refreshStats]);

  // 批量缓存行情
  const handleCacheQuotes = useCallback(async (quotes: CachedQuote[]) => {
    setLoading(true);
    setError(null);
    try {
      await indexedDB.cacheQuotes(quotes);
      await refreshStats();
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [refreshStats]);

  // 获取缓存的行情
  const handleGetCachedQuote = useCallback(async (symbol: string) => {
    try {
      return await indexedDB.getCachedQuote(symbol);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      return undefined;
    }
  }, []);

  // 获取行情历史
  const handleGetQuoteHistory = useCallback(async (symbol: string, limit?: number) => {
    try {
      return await indexedDB.getQuoteHistory(symbol, limit);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      return [];
    }
  }, []);

  // 添加价格历史
  const handleAddPriceHistory = useCallback(
    async (record: Omit<PriceHistoryRecord, 'id' | 'createdAt'>) => {
      try {
        await indexedDB.addPriceHistory(record);
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
      }
    },
    []
  );

  // 获取价格历史
  const handleGetPriceHistory = useCallback(async (symbol: string, limit?: number) => {
    try {
      return await indexedDB.getPriceHistory(symbol, limit);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      return [];
    }
  }, []);

  // 清除所有缓存
  const handleClearAllCache = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await indexedDB.clearAllCache();
      await refreshStats();
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [refreshStats]);

  // 清除指定股票缓存
  const handleClearSymbolCache = useCallback(async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      await indexedDB.clearSymbolCache(symbol);
      await refreshStats();
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [refreshStats]);

  // 清理过期数据
  const handleCleanupOldData = useCallback(async (daysToKeep?: number) => {
    setLoading(true);
    setError(null);
    try {
      const deleted = await indexedDB.cleanupOldData(daysToKeep);
      await refreshStats();
      return deleted;
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      return 0;
    } finally {
      setLoading(false);
    }
  }, [refreshStats]);

  return {
    loading,
    error,
    stats,
    cacheQuote: handleCacheQuote,
    cacheQuotes: handleCacheQuotes,
    getCachedQuote: handleGetCachedQuote,
    getQuoteHistory: handleGetQuoteHistory,
    addPriceHistory: handleAddPriceHistory,
    getPriceHistory: handleGetPriceHistory,
    clearAllCache: handleClearAllCache,
    clearSymbolCache: handleClearSymbolCache,
    cleanupOldData: handleCleanupOldData,
    refreshStats,
  };
};

export default useIndexedDB;
