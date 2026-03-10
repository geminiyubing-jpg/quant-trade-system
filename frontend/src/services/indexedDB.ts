/**
 * ==============================================
 * IndexedDB 缓存服务
 * ==============================================
 * 使用 Dexie.js 封装 IndexedDB，用于缓存历史行情数据
 */

import Dexie, { Table } from 'dexie';

// 行情数据接口
export interface CachedQuote {
  symbol: string;
  timestamp: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change: number;
  changePercent: number;
}

// 价格历史记录接口
export interface PriceHistoryRecord {
  id?: number;
  symbol: string;
  timestamp: string;
  price: number;
  volume: number;
  createdAt: Date;
}

// 同步状态接口
export interface SyncStatus {
  key: string;
  lastSync: string;
  symbol?: string;
}

// 数据库类
class QuantTradeDatabase extends Dexie {
  quotes!: Table<CachedQuote>;
  priceHistory!: Table<PriceHistoryRecord>;
  syncStatus!: Table<SyncStatus>;

  constructor() {
    super('QuantTradeCache');

    this.version(1).stores({
      // 使用复合主键 [symbol+timestamp]
      quotes: '[symbol+timestamp], symbol, timestamp',
      priceHistory: '++id, [symbol+timestamp], symbol, timestamp, createdAt',
      syncStatus: 'key, lastSync, symbol',
    });

    console.log('📦 IndexedDB 数据库已初始化');
  }
}

// 创建数据库实例
const db = new QuantTradeDatabase();

/**
 * 缓存行情数据
 */
export const cacheQuote = async (quote: CachedQuote): Promise<void> => {
  try {
    await db.quotes.put(quote);
  } catch (error) {
    console.error('❌ 缓存行情失败:', error);
  }
};

/**
 * 批量缓存行情数据
 */
export const cacheQuotes = async (quotes: CachedQuote[]): Promise<void> => {
  try {
    await db.quotes.bulkPut(quotes);
    console.log(`📦 已缓存 ${quotes.length} 条行情数据`);
  } catch (error) {
    console.error('❌ 批量缓存行情失败:', error);
  }
};

/**
 * 获取缓存的行情数据
 */
export const getCachedQuote = async (symbol: string): Promise<CachedQuote | undefined> => {
  try {
    const quotes = await db.quotes
      .where('symbol')
      .equals(symbol)
      .reverse()
      .sortBy('timestamp');
    return quotes[0];
  } catch (error) {
    console.error('❌ 获取缓存行情失败:', error);
    return undefined;
  }
};

/**
 * 获取某股票的历史行情
 */
export const getQuoteHistory = async (
  symbol: string,
  limit: number = 100
): Promise<CachedQuote[]> => {
  try {
    const quotes = await db.quotes
      .where('symbol')
      .equals(symbol)
      .reverse()
      .limit(limit)
      .toArray();
    return quotes;
  } catch (error) {
    console.error('❌ 获取历史行情失败:', error);
    return [];
  }
};

/**
 * 添加价格历史记录
 */
export const addPriceHistory = async (record: Omit<PriceHistoryRecord, 'id' | 'createdAt'>): Promise<void> => {
  try {
    await db.priceHistory.add({
      ...record,
      createdAt: new Date(),
    });
  } catch (error) {
    // 忽略重复键错误
    if (!String(error).includes('ConstraintError')) {
      console.error('❌ 添加价格历史失败:', error);
    }
  }
};

/**
 * 获取价格历史记录
 */
export const getPriceHistory = async (
  symbol: string,
  limit: number = 100
): Promise<PriceHistoryRecord[]> => {
  try {
    const history = await db.priceHistory
      .where('symbol')
      .equals(symbol)
      .reverse()
      .limit(limit)
      .toArray();
    return history;
  } catch (error) {
    console.error('❌ 获取价格历史失败:', error);
    return [];
  }
};

/**
 * 更新同步状态
 */
export const updateSyncStatus = async (key: string, symbol?: string): Promise<void> => {
  try {
    await db.syncStatus.put({
      key,
      lastSync: new Date().toISOString(),
      symbol,
    });
  } catch (error) {
    console.error('❌ 更新同步状态失败:', error);
  }
};

/**
 * 获取同步状态
 */
export const getSyncStatus = async (key: string): Promise<SyncStatus | undefined> => {
  try {
    return await db.syncStatus.get(key);
  } catch (error) {
    console.error('❌ 获取同步状态失败:', error);
    return undefined;
  }
};

/**
 * 清除所有缓存数据
 */
export const clearAllCache = async (): Promise<void> => {
  try {
    await Promise.all([
      db.quotes.clear(),
      db.priceHistory.clear(),
      db.syncStatus.clear(),
    ]);
    console.log('🗑️ 已清除所有缓存数据');
  } catch (error) {
    console.error('❌ 清除缓存失败:', error);
  }
};

/**
 * 清除某股票的缓存
 */
export const clearSymbolCache = async (symbol: string): Promise<void> => {
  try {
    await Promise.all([
      db.quotes.where('symbol').equals(symbol).delete(),
      db.priceHistory.where('symbol').equals(symbol).delete(),
    ]);
    console.log(`🗑️ 已清除 ${symbol} 的缓存数据`);
  } catch (error) {
    console.error('❌ 清除股票缓存失败:', error);
  }
};

/**
 * 获取缓存统计信息
 */
export const getCacheStats = async (): Promise<{
  quotesCount: number;
  historyCount: number;
  symbolsCount: number;
}> => {
  try {
    const [quotesCount, historyCount] = await Promise.all([
      db.quotes.count(),
      db.priceHistory.count(),
    ]);

    // 获取不重复的股票数量
    const symbols = await db.quotes.toArray();
    const uniqueSymbols = new Set(symbols.map((q) => q.symbol));

    return {
      quotesCount,
      historyCount,
      symbolsCount: uniqueSymbols.size,
    };
  } catch (error) {
    console.error('❌ 获取缓存统计失败:', error);
    return {
      quotesCount: 0,
      historyCount: 0,
      symbolsCount: 0,
    };
  }
};

/**
 * 清理过期数据（保留最近 N 天）
 */
export const cleanupOldData = async (daysToKeep: number = 7): Promise<number> => {
  try {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
    const cutoffTimestamp = cutoffDate.toISOString();

    const deletedQuotes = await db.quotes
      .where('timestamp')
      .below(cutoffTimestamp)
      .delete();

    const deletedHistory = await db.priceHistory
      .where('createdAt')
      .below(cutoffDate)
      .delete();

    const totalDeleted = deletedQuotes + deletedHistory;
    if (totalDeleted > 0) {
      console.log(`🧹 已清理 ${totalDeleted} 条过期数据`);
    }

    return totalDeleted;
  } catch (error) {
    console.error('❌ 清理过期数据失败:', error);
    return 0;
  }
};

export default {
  cacheQuote,
  cacheQuotes,
  getCachedQuote,
  getQuoteHistory,
  addPriceHistory,
  getPriceHistory,
  updateSyncStatus,
  getSyncStatus,
  clearAllCache,
  clearSymbolCache,
  getCacheStats,
  cleanupOldData,
};
