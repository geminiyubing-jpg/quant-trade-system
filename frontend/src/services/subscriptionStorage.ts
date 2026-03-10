/**
 * ==============================================
 * 订阅持久化服务
 * ==============================================
 * 将 WebSocket 订阅保存到 localStorage，刷新页面后自动恢复
 */

const STORAGE_KEY = 'quant_trade_ws_subscriptions';
const MAX_SUBSCRIPTIONS = 100;

export interface SubscriptionData {
  symbols: string[];
  lastUpdated: string;
}

/**
 * 保存订阅到 localStorage
 */
export const saveSubscriptions = (symbols: string[]): void => {
  try {
    const data: SubscriptionData = {
      symbols: symbols.slice(0, MAX_SUBSCRIPTIONS),
      lastUpdated: new Date().toISOString(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    console.log(`💾 已保存 ${symbols.length} 个订阅到 localStorage`);
  } catch (error) {
    console.error('❌ 保存订阅失败:', error);
  }
};

/**
 * 从 localStorage 加载订阅
 */
export const loadSubscriptions = (): string[] => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) {
      return [];
    }

    const data: SubscriptionData = JSON.parse(saved);
    const symbols = data.symbols || [];

    if (symbols.length > 0) {
      console.log(`📂 从 localStorage 加载 ${symbols.length} 个订阅`);
      console.log(`📅 上次更新: ${data.lastUpdated}`);
    }

    return symbols;
  } catch (error) {
    console.error('❌ 加载订阅失败:', error);
    return [];
  }
};

/**
 * 清除保存的订阅
 */
export const clearSubscriptions = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY);
    console.log('🗑️ 已清除保存的订阅');
  } catch (error) {
    console.error('❌ 清除订阅失败:', error);
  }
};

/**
 * 添加单个订阅
 */
export const addSubscription = (symbol: string): void => {
  const symbols = loadSubscriptions();
  if (!symbols.includes(symbol)) {
    symbols.push(symbol);
    saveSubscriptions(symbols);
  }
};

/**
 * 移除单个订阅
 */
export const removeSubscription = (symbol: string): void => {
  const symbols = loadSubscriptions();
  const index = symbols.indexOf(symbol);
  if (index > -1) {
    symbols.splice(index, 1);
    saveSubscriptions(symbols);
  }
};

/**
 * 批量添加订阅
 */
export const addSubscriptions = (newSymbols: string[]): void => {
  const symbols = loadSubscriptions();
  let changed = false;

  newSymbols.forEach((s) => {
    if (!symbols.includes(s) && symbols.length < MAX_SUBSCRIPTIONS) {
      symbols.push(s);
      changed = true;
    }
  });

  if (changed) {
    saveSubscriptions(symbols);
  }
};

/**
 * 批量移除订阅
 */
export const removeSubscriptions = (symbolsToRemove: string[]): void => {
  const symbols = loadSubscriptions();
  const newSymbols = symbols.filter((s) => !symbolsToRemove.includes(s));

  if (newSymbols.length !== symbols.length) {
    saveSubscriptions(newSymbols);
  }
};

export default {
  saveSubscriptions,
  loadSubscriptions,
  clearSubscriptions,
  addSubscription,
  removeSubscription,
  addSubscriptions,
  removeSubscriptions,
};
