/**
 * 实时行情 Hook
 * Realtime Quote Hook
 *
 * 使用 WebSocket 订阅实时行情数据
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import websocketService from '../services/websocket';
import { Quote, getQuotes } from '../services/marketData';

interface UseRealtimeQuoteOptions {
  symbols: string[];
  enabled?: boolean;
  refreshInterval?: number; // 轮询间隔（毫秒），作为 WebSocket 的后备方案
}

interface UseRealtimeQuoteReturn {
  quotes: Record<string, Quote>;
  loading: boolean;
  error: string | null;
  connected: boolean;
}

/**
 * 实时行情 Hook
 *
 * 优先使用 WebSocket，如果不可用则使用 HTTP 轮询
 */
export function useRealtimeQuote(options: UseRealtimeQuoteOptions): UseRealtimeQuoteReturn {
  const { symbols, enabled = true, refreshInterval = 5000 } = options;

  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  const prevSymbolsRef = useRef<string[]>([]);

  // 获取行情数据（HTTP 后备方案）
  const fetchQuotes = useCallback(async () => {
    if (!enabled || symbols.length === 0) return;

    try {
      const quoteList = await getQuotes(symbols);
      const quoteMap: Record<string, Quote> = {};
      quoteList.forEach((q) => {
        quoteMap[q.symbol] = q;
      });
      setQuotes(quoteMap);
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch quotes:', err);
      setError('获取行情数据失败');
    }
  }, [symbols, enabled]);

  // 处理 WebSocket 连接和订阅
  useEffect(() => {
    if (!enabled || symbols.length === 0) {
      setLoading(false);
      return;
    }

    // 检查 WebSocket 连接状态
    const isWsConnected = websocketService.isConnected();
    setConnected(isWsConnected);

    if (isWsConnected) {
      // 使用 WebSocket 订阅
      const newSymbols = symbols.filter((s) => !prevSymbolsRef.current.includes(s));
      const removedSymbols = prevSymbolsRef.current.filter((s) => !symbols.includes(s));

      if (newSymbols.length > 0) {
        websocketService.subscribe(newSymbols);
      }

      if (removedSymbols.length > 0) {
        websocketService.unsubscribe(removedSymbols);
      }

      prevSymbolsRef.current = symbols;
    } else {
      // WebSocket 不可用，使用 HTTP 轮询
      fetchQuotes();

      const intervalId = setInterval(fetchQuotes, refreshInterval);

      return () => {
        clearInterval(intervalId);
      };
    }

    return () => {
      // 组件卸载时取消订阅
      if (symbols.length > 0) {
        websocketService.unsubscribe(symbols);
      }
    };
  }, [symbols, enabled, fetchQuotes, refreshInterval]);

  // 监听 Redux store 中的行情更新
  useEffect(() => {
    if (!enabled || !connected) return;

    // 这里可以订阅 Redux store 的变化
    // 暂时使用简化实现
  }, [enabled, connected]);

  return {
    quotes,
    loading,
    error,
    connected,
  };
}

/**
 * 单个股票实时行情 Hook
 */
export function useSingleQuote(symbol: string | null, enabled = true) {
  const symbols = symbol ? [symbol] : [];
  const { quotes, loading, error, connected } = useRealtimeQuote({
    symbols,
    enabled: enabled && !!symbol,
  });

  return {
    quote: symbol ? quotes[symbol] : null,
    loading,
    error,
    connected,
  };
}

/**
 * 自选股实时行情 Hook
 */
export function useWatchlistQuotes(watchlistId?: string) {
  const [symbols, setSymbols] = useState<string[]>([]);

  // 从 localStorage 或 API 加载自选股列表
  useEffect(() => {
    const loadWatchlist = async () => {
      try {
        // 从 localStorage 获取
        const saved = localStorage.getItem('watchlist');
        if (saved) {
          const watchlist = JSON.parse(saved);
          const list = watchlistId
            ? watchlist.find((w: any) => w.id === watchlistId)
            : watchlist[0];
          if (list?.stocks) {
            setSymbols(list.stocks.map((s: any) => s.symbol || s));
          }
        }
      } catch (error) {
        console.error('Failed to load watchlist:', error);
      }
    };

    loadWatchlist();
  }, [watchlistId]);

  return useRealtimeQuote({ symbols });
}

export default useRealtimeQuote;
