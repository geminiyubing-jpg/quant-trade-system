/**
 * 自选股面板
 * Watchlist Panel
 *
 * 集成实时行情数据
 */
import React, { useState, useEffect } from 'react';
import { List, Spin, Empty, Button, message } from 'antd';
import { StarOutlined, StarFilled, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { WatchlistPanelConfig } from '../../../types/workspace';
import { useRealtimeQuote } from '../../../hooks/useRealtimeQuote';
import { Quote } from '../../../services/marketData';

interface WatchlistPanelProps {
  config?: WatchlistPanelConfig;
}

interface WatchlistItem {
  code: string;
  name: string;
  isFavorite: boolean;
}

const DEFAULT_WATCHLIST: WatchlistItem[] = [
  { code: '600519.SH', name: '贵州茅台', isFavorite: true },
  { code: '600036.SH', name: '招商银行', isFavorite: true },
  { code: '000001.SZ', name: '平安银行', isFavorite: true },
  { code: '000858.SZ', name: '五粮液', isFavorite: true },
  { code: '601318.SH', name: '中国平安', isFavorite: true },
  { code: '002594.SZ', name: '比亚迪', isFavorite: true },
];

const WatchlistPanel: React.FC<WatchlistPanelProps> = ({ config: _config }) => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [symbols, setSymbols] = useState<string[]>([]);

  // 从 localStorage 加载自选股
  useEffect(() => {
    const loadWatchlist = () => {
      try {
        const saved = localStorage.getItem('workspace_watchlist');
        if (saved) {
          const parsed = JSON.parse(saved);
          setWatchlist(parsed);
          setSymbols(parsed.map((item: WatchlistItem) => item.code));
        } else {
          // 使用默认自选股
          setWatchlist(DEFAULT_WATCHLIST);
          setSymbols(DEFAULT_WATCHLIST.map((item) => item.code));
          // 保存到 localStorage
          localStorage.setItem('workspace_watchlist', JSON.stringify(DEFAULT_WATCHLIST));
        }
      } catch (error) {
        console.error('Failed to load watchlist:', error);
        setWatchlist(DEFAULT_WATCHLIST);
        setSymbols(DEFAULT_WATCHLIST.map((item) => item.code));
      }
    };

    loadWatchlist();
  }, []);

  // 保存自选股到 localStorage
  const saveWatchlist = (list: WatchlistItem[]) => {
    localStorage.setItem('workspace_watchlist', JSON.stringify(list));
  };

  // 获取实时行情
  const { quotes, loading, connected } = useRealtimeQuote({
    symbols,
    enabled: symbols.length > 0,
    refreshInterval: 5000, // 5秒刷新一次
  });

  // 切换收藏状态
  const toggleFavorite = (code: string) => {
    setWatchlist((prev) => {
      const updated = prev.map((item) =>
        item.code === code ? { ...item, isFavorite: !item.isFavorite } : item
      );
      saveWatchlist(updated);
      return updated;
    });
  };

  // 移除股票
  const removeStock = (code: string) => {
    setWatchlist((prev) => {
      const updated = prev.filter((item) => item.code !== code);
      saveWatchlist(updated);
      setSymbols(updated.map((item) => item.code));
      return updated;
    });
    message.success('已从自选股移除');
  };

  // 添加股票（简单实现，实际项目中应该有搜索功能）
  const addStock = () => {
    message.info('请通过搜索添加股票');
  };

  // 合并行情数据和自选股信息
  const getWatchlistWithQuote = (): (WatchlistItem & { quote?: Quote })[] => {
    return watchlist.map((item) => ({
      ...item,
      quote: quotes[item.code],
    }));
  };

  // 格式化涨跌幅
  const formatChange = (quote: Quote): { text: string; color: string } => {
    const change = quote.change_percent;
    const color = change >= 0 ? '#FF4D4D' : '#00D26A';
    const text = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    return { text, color };
  };

  const watchlistWithQuote = getWatchlistWithQuote();

  return (
    <div className="watchlist-panel">
      <div className="panel-toolbar">
        <span className="toolbar-title">
          自选股 ({watchlist.length})
          {connected && <span className="live-indicator" title="实时连接中">●</span>}
        </span>
        <Button
          type="text"
          size="small"
          icon={<PlusOutlined />}
          onClick={addStock}
        />
      </div>
      <div className="watchlist-container">
        {loading && watchlist.length === 0 ? (
          <div className="loading-center"><Spin /></div>
        ) : watchlist.length === 0 ? (
          <Empty
            description="暂无自选股"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={watchlistWithQuote}
            renderItem={(item) => {
              const quote = item.quote;
              const changeInfo = quote ? formatChange(quote) : null;

              return (
                <List.Item className="watchlist-item">
                  <div className="item-left">
                    <Button
                      type="text"
                      size="small"
                      className="star-btn"
                      icon={item.isFavorite ? <StarFilled style={{ color: '#FFD700' }} /> : <StarOutlined />}
                      onClick={() => toggleFavorite(item.code)}
                    />
                    <div className="stock-info">
                      <span className="stock-name">{item.name}</span>
                      <span className="stock-code">{item.code}</span>
                    </div>
                  </div>
                  <div className="item-right">
                    {quote ? (
                      <div className="price-info">
                        <span className={`price ${quote.change >= 0 ? 'up' : 'down'}`}>
                          {quote.price.toFixed(2)}
                        </span>
                        <span
                          className={`change ${quote.change >= 0 ? 'up' : 'down'}`}
                          style={changeInfo ? { color: changeInfo.color } : {}}
                        >
                          {changeInfo?.text || '--'}
                        </span>
                      </div>
                    ) : (
                      <div className="price-info">
                        <span className="price">--</span>
                        <span className="change">--</span>
                      </div>
                    )}
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => removeStock(item.code)}
                    />
                  </div>
                </List.Item>
              );
            }}
          />
        )}
      </div>
    </div>
  );
};

export default WatchlistPanel;
