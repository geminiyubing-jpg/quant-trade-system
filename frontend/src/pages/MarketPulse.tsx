/**
 * MarketPulse - 市场动态页面
 *
 * 功能：
 * - 全球金融市场实时数据展示
 * - 分类展示各类指数、商品、外汇
 * - 实时数据自动更新
 * - 深色主题高信息密度设计
 * - 支持 OpenBB 数据源
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, RefreshCw } from 'lucide-react';
import { message } from 'antd';
import { useTranslation } from 'react-i18next';
import TopNav from '../components/market-pulse/TopNav';
import MarketCard from '../components/market-pulse/MarketCard';
import SectionHeader from '../components/market-pulse/SectionHeader';
import GlobalHeatmap from '../components/market-pulse/GlobalHeatmap';
import MarketDetailModal from '../components/market-pulse/MarketDetailModal';
import WatchlistManageModal from '../components/market-pulse/WatchlistManageModal';
import {
  generateInitialData,
  simulatePriceUpdate,
  MarketCategory,
  MarketItem,
} from '../data/marketPulseData';
import {
  fetchHeatmapData,
  fetchOpenBBQuotes,
  fetchOpenBBStatus,
  HeatmapItem,
} from '../services/marketPulse';
import '../components/market-pulse/MarketPulse.css';

// 默认热力图数据
const DEFAULT_HEATMAP: HeatmapItem[] = [
  { name: '日本', asset: 'nikkei', change_percent: 1.43 },
  { name: '沪深', asset: 'shanghai', change_percent: 0.77 },
  { name: '香港', asset: 'hsi', change_percent: -0.74 },
  { name: '美国', asset: 'dow', change_percent: -0.14 },
  { name: '欧洲', asset: 'dax', change_percent: -0.68 },
  { name: '黄金', asset: 'gold', change_percent: 0.53 },
  { name: '原油', asset: 'oil', change_percent: 1.59 },
  { name: '比特币', asset: 'btc', change_percent: 1.73 },
];

const MarketPulse: React.FC = () => {
  const { t } = useTranslation();

  // 市场数据状态
  const [marketData, setMarketData] = useState<MarketCategory[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapItem[]>(DEFAULT_HEATMAP);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // 弹窗状态
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState<MarketItem | null>(null);
  const [watchlistModalVisible, setWatchlistModalVisible] = useState(false);
  const [watchlistItems, setWatchlistItems] = useState<MarketItem[]>([]);

  // 自选股ID集合（用于快速判断是否已关注）
  const watchlistIds = useMemo(() => new Set(watchlistItems.map(item => item.id)), [watchlistItems]);

  // 加载所有数据
  const loadAllData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);

    try {
      // 加载热力图数据
      const heatmap = await fetchHeatmapData();

      if (heatmap.length > 0) {
        setHeatmapData(heatmap);
      }

      // 如果是首次加载，初始化卡片数据
      if (marketData.length === 0) {
        const initialData = generateInitialData();
        setMarketData(initialData);
      }

      // 尝试从 OpenBB 获取美股数据
      try {
        const openbbStatus = await fetchOpenBBStatus();
        if (openbbStatus?.is_connected && openbbStatus?.providers?.equity) {
          // 获取美股指数报价
          const usSymbols = ['^DJI', '^GSPC', '^IXIC', '^N225', '^GDAXI'];
          const quotes = await fetchOpenBBQuotes(usSymbols);

          // 更新市场数据中的美股部分
          if (Object.keys(quotes).length > 0) {
            setMarketData((prevData) => {
              return prevData.map((category) => {
                if (category.id === 'watchlist' || category.id === 'global') {
                  return {
                    ...category,
                    items: category.items.map((item) => {
                      const symbol = item.id === 'dow' ? '^DJI' :
                                     item.id === 'sp500' ? '^GSPC' :
                                     item.id === 'nasdaq' ? '^IXIC' :
                                     item.id === 'nikkei' ? '^N225' :
                                     item.id === 'dax' ? '^GDAXI' : null;

                      if (symbol && quotes[symbol]) {
                        const quote = quotes[symbol];
                        return {
                          ...item,
                          price: quote.price || item.price,
                          change: quote.change || item.change,
                          changePercent: quote.change_percent || item.changePercent,
                          provider: quote.provider,
                        };
                      }
                      return item;
                    }),
                  };
                }
                return category;
              });
            });
          }
        }
      } catch (openbbError) {
        console.log('OpenBB 数据获取失败，使用模拟数据:', openbbError);
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error('加载数据失败:', error);
      // 使用模拟数据作为后备
      if (marketData.length === 0) {
        setMarketData(generateInitialData());
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [marketData.length]);

  // 初始化数据
  useEffect(() => {
    loadAllData();
  }, []);

  // 定时刷新数据（每30秒）
  useEffect(() => {
    const refreshInterval = setInterval(() => {
      loadAllData();
    }, 30000);

    return () => clearInterval(refreshInterval);
  }, [loadAllData]);

  // 卡片数据实时更新模拟（本地微调）
  useEffect(() => {
    if (loading || marketData.length === 0) return;

    const updateInterval = setInterval(() => {
      setMarketData((prevData) => {
        return prevData.map((category) => ({
          ...category,
          items: category.items.map((item) => {
            if (Math.random() < 0.3) {
              return simulatePriceUpdate(item);
            }
            return item;
          }),
        }));
      });
    }, 2000 + Math.random() * 1000);

    return () => clearInterval(updateInterval);
  }, [loading, marketData.length]);

  // 过滤数据
  const filteredData = useMemo(() => {
    let data = marketData;

    // 按标签过滤
    if (activeTab !== 'all') {
      if (activeTab === 'watchlist') {
        data = data.filter((cat) => cat.id === 'watchlist');
      } else {
        data = data.filter((cat) => cat.id === activeTab);
      }
    }

    // 按搜索词过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      data = data
        .map((cat) => ({
          ...cat,
          items: cat.items.filter(
            (item) =>
              item.name.toLowerCase().includes(query) ||
              (item.nameEn && item.nameEn.toLowerCase().includes(query)) ||
              item.id.toLowerCase().includes(query)
          ),
        }))
        .filter((cat) => cat.items.length > 0);
    }

    return data;
  }, [marketData, activeTab, searchQuery]);

  // 处理标签切换
  const handleTabChange = useCallback((tabId: string) => {
    setActiveTab(tabId);
  }, []);

  // 处理搜索
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  // 处理卡片点击 - 打开详情弹窗
  const handleCardClick = useCallback((item: MarketItem) => {
    setSelectedItem(item);
    setDetailModalVisible(true);
  }, []);

  // 处理更多按钮点击 - 显示提示
  const handleMoreClick = useCallback((categoryId: string) => {
    const categoryKey = `marketPulse.categoryNames.${categoryId}`;
    message.info(`${t('marketPulse.section.more')} ${t(categoryKey)} ${t('common.loading').replace('...', '')}`);
  }, [t]);

  // 处理管理按钮点击 - 打开自选管理弹窗
  const handleManageClick = useCallback(() => {
    setWatchlistModalVisible(true);
  }, []);

  // 添加到自选
  const handleAddToWatchlist = useCallback((item: MarketItem) => {
    if (!watchlistIds.has(item.id)) {
      setWatchlistItems(prev => [...prev, item]);
    }
  }, [watchlistIds]);

  // 从自选移除
  const handleRemoveFromWatchlist = useCallback((itemId: string) => {
    setWatchlistItems(prev => prev.filter(item => item.id !== itemId));
  }, []);

  // 手动刷新
  const handleRefresh = useCallback(() => {
    loadAllData(true);
  }, [loadAllData]);

  // 加载状态
  if (loading) {
    return (
      <div className="market-pulse">
        <div className="loading-container">
          <div className="loading-spinner" />
          <p className="loading-text">{t('marketPulse.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="market-pulse">
      {/* 顶部导航 */}
      <TopNav
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onSearch={handleSearch}
      />

      {/* 状态栏 */}
      {lastUpdate && (
        <div className="status-bar">
          <span className="last-update">
            {t('marketPulse.lastUpdate')}: {lastUpdate.toLocaleTimeString()}
          </span>
          <button
            className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={14} />
          </button>
        </div>
      )}

      {/* 全球资产热力图 */}
      {activeTab === 'all' && !searchQuery && (
        <GlobalHeatmap data={heatmapData.map(item => ({
          name: item.name,
          value: 0,
          changePercent: item.change_percent,
        }))} />
      )}

      {/* 市场数据分组 */}
      <AnimatePresence mode="wait">
        {filteredData.length === 0 ? (
          <motion.div
            key="empty"
            className="empty-state"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Activity size={48} className="empty-icon" />
            <p className="empty-text">
              {searchQuery ? t('marketPulse.noMatch') : t('marketPulse.noData')}
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="content"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {filteredData.map((category, categoryIndex) => (
              <motion.section
                key={category.id}
                className="market-section"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: categoryIndex * 0.1 }}
              >
                <SectionHeader
                  title={category.name}
                  showManage={category.id === 'watchlist'}
                  onMoreClick={() => handleMoreClick(category.id)}
                  onManageClick={handleManageClick}
                />
                <div className="market-cards-grid">
                  {category.items.map((item, itemIndex) => (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: categoryIndex * 0.1 + itemIndex * 0.03 }}
                    >
                      <MarketCard
                        item={item}
                        onClick={() => handleCardClick(item)}
                      />
                    </motion.div>
                  ))}
                </div>
              </motion.section>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 市场详情弹窗 */}
      <MarketDetailModal
        visible={detailModalVisible}
        item={selectedItem}
        onClose={() => setDetailModalVisible(false)}
        onAddToWatchlist={handleAddToWatchlist}
        onRemoveFromWatchlist={handleRemoveFromWatchlist}
        isWatched={selectedItem ? watchlistIds.has(selectedItem.id) : false}
      />

      {/* 自选管理弹窗 */}
      <WatchlistManageModal
        visible={watchlistModalVisible}
        allCategories={marketData}
        watchlistItems={watchlistItems}
        onClose={() => setWatchlistModalVisible(false)}
        onAddItem={handleAddToWatchlist}
        onRemoveItem={handleRemoveFromWatchlist}
      />
    </div>
  );
};

export default MarketPulse;
