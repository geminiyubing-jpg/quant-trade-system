/**
 * WatchlistManageModal - 自选股管理弹窗
 * 支持添加、移除、排序自选市场项
 */

import React, { useState, useMemo } from 'react';
import { Modal, Input, Button, Tag, message, Empty, Tabs, Tooltip } from 'antd';
import {
  StarFilled,
  SearchOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { MarketItem, MarketCategory, COLOR_CONFIG, formatPrice, formatChangePercent } from '../../data/marketPulseData';

interface WatchlistManageModalProps {
  visible: boolean;
  allCategories: MarketCategory[];
  watchlistItems: MarketItem[];
  onClose: () => void;
  onAddItem: (item: MarketItem) => void;
  onRemoveItem: (itemId: string) => void;
  onReorder?: (items: MarketItem[]) => void;
}

const WatchlistManageModal: React.FC<WatchlistManageModalProps> = ({
  visible,
  allCategories,
  watchlistItems,
  onClose,
  onAddItem,
  onRemoveItem,
}) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('my-watchlist');
  const [searchQuery, setSearchQuery] = useState('');

  // 获取所有可添加的项目（排除已在自选中的）
  const allAvailableItems = useMemo(() => {
    const watchlistIds = new Set(watchlistItems.map(item => item.id));
    const items: MarketItem[] = [];

    allCategories.forEach(category => {
      if (category.id !== 'watchlist') {
        category.items.forEach(item => {
          if (!watchlistIds.has(item.id)) {
            items.push(item);
          }
        });
      }
    });

    return items;
  }, [allCategories, watchlistItems]);

  // 过滤可添加项目
  const filteredAvailableItems = useMemo(() => {
    if (!searchQuery.trim()) return allAvailableItems;

    const query = searchQuery.toLowerCase();
    return allAvailableItems.filter(item =>
      item.name.toLowerCase().includes(query) ||
      (item.nameEn && item.nameEn.toLowerCase().includes(query)) ||
      item.id.toLowerCase().includes(query)
    );
  }, [allAvailableItems, searchQuery]);

  // 渲染项目行
  const renderItemRow = (item: MarketItem, isInWatchlist: boolean) => {
    const isUp = item.changePercent >= 0;
    const changeColor = isUp ? COLOR_CONFIG.up : COLOR_CONFIG.down;

    return (
      <motion.div
        key={item.id}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '12px 16px',
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '8px',
          marginBottom: '8px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        {/* 名称 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: '#e0e0e0', fontWeight: 500 }}>{item.name}</span>
            {item.nameEn && (
              <span style={{ color: '#a0a0a0', fontSize: '12px' }}>{item.nameEn}</span>
            )}
            {item.exchange && (
              <Tag style={{
                background: 'rgba(0, 212, 255, 0.1)',
                border: '1px solid rgba(0, 212, 255, 0.3)',
                color: '#00d4ff',
                fontSize: '10px',
                padding: '0 4px',
                margin: 0,
              }}>
                {item.exchange}
              </Tag>
            )}
          </div>
        </div>

        {/* 价格 */}
        <div style={{ width: 120, textAlign: 'right' }}>
          <span style={{ color: '#e0e0e0', fontFamily: '"JetBrains Mono", monospace' }}>
            {formatPrice(item.price, item.category)}
          </span>
        </div>

        {/* 涨跌幅 */}
        <div style={{ width: 100, textAlign: 'right' }}>
          <span style={{ color: changeColor, fontFamily: '"JetBrains Mono", monospace' }}>
            {formatChangePercent(item.changePercent)}
          </span>
        </div>

        {/* 操作按钮 */}
        <div style={{ width: 60, textAlign: 'center' }}>
          {isInWatchlist ? (
            <Tooltip title={t('marketPulse.watchlist.removeFromWatchlist')}>
              <Button
                type="text"
                danger
                size="small"
                icon={<StarFilled style={{ color: '#f5c842' }} />}
                onClick={() => {
                  onRemoveItem(item.id);
                  message.success(t('marketPulse.detail.removedFromWatchlist', { name: item.name }));
                }}
              />
            </Tooltip>
          ) : (
            <Tooltip title={t('marketPulse.watchlist.addToWatchlist')}>
              <Button
                type="text"
                size="small"
                icon={<PlusOutlined style={{ color: '#00d4ff' }} />}
                onClick={() => {
                  onAddItem(item);
                  message.success(t('marketPulse.detail.addedToWatchlist', { name: item.name }));
                }}
              />
            </Tooltip>
          )}
        </div>
      </motion.div>
    );
  };

  const tabItems = [
    {
      key: 'my-watchlist',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <StarFilled style={{ color: '#f5c842' }} />
          {t('marketPulse.watchlist.myWatchlist')} ({watchlistItems.length})
        </span>
      ),
      children: (
        <div style={{ maxHeight: '400px', overflow: 'auto' }}>
          <AnimatePresence>
            {watchlistItems.length === 0 ? (
              <Empty
                description={<span style={{ color: '#a0a0a0' }}>{t('marketPulse.watchlist.noWatchlist')}</span>}
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              watchlistItems.map(item => renderItemRow(item, true))
            )}
          </AnimatePresence>
        </div>
      ),
    },
    {
      key: 'add-items',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <PlusOutlined />
          {t('marketPulse.watchlist.addItem')}
        </span>
      ),
      children: (
        <div>
          {/* 搜索框 */}
          <Input
            placeholder={t('marketPulse.watchlist.searchPlaceholder')}
            prefix={<SearchOutlined style={{ color: '#a0a0a0' }} />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              marginBottom: 16,
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
            }}
            allowClear
          />

          {/* 可添加列表 */}
          <div style={{ maxHeight: '350px', overflow: 'auto' }}>
            <AnimatePresence>
              {filteredAvailableItems.length === 0 ? (
                <Empty
                  description={<span style={{ color: '#a0a0a0' }}>
                    {searchQuery ? t('marketPulse.watchlist.noMatch') : t('marketPulse.watchlist.noAvailable')}
                  </span>}
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ) : (
                filteredAvailableItems.map(item => renderItemRow(item, false))
              )}
            </AnimatePresence>
          </div>
        </div>
      ),
    },
  ];

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <StarFilled style={{ color: '#f5c842' }} />
          <span style={{ color: '#f5c842' }}>{t('marketPulse.watchlist.title')}</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#a0a0a0', fontSize: '12px' }}>
            {t('marketPulse.watchlist.tip')}
          </span>
          <Button type="primary" onClick={onClose}>
            {t('marketPulse.watchlist.done')}
          </Button>
        </div>
      }
      width={700}
      centered
      className="watchlist-manage-modal"
      styles={{
        body: { padding: '16px 24px', maxHeight: '60vh', overflow: 'auto' },
      }}
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </motion.div>

      <style>{`
        .watchlist-manage-modal .ant-modal-content {
          background: rgba(13, 20, 24, 0.98) !important;
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 12px;
        }

        .watchlist-manage-modal .ant-modal-header {
          background: transparent !important;
          border-bottom: 1px solid rgba(0, 212, 255, 0.1);
        }

        .watchlist-manage-modal .ant-modal-title {
          color: #f5c842 !important;
        }

        .watchlist-manage-modal .ant-modal-close {
          color: #a0a0a0;
        }

        .watchlist-manage-modal .ant-modal-close:hover {
          color: #00d4ff;
        }

        .watchlist-manage-modal .ant-tabs-tab {
          color: #a0a0a0 !important;
        }

        .watchlist-manage-modal .ant-tabs-tab-active {
          color: #00d4ff !important;
        }

        .watchlist-manage-modal .ant-tabs-ink-bar {
          background: #00d4ff !important;
        }

        .watchlist-manage-modal .ant-input {
          background: rgba(0, 0, 0, 0.3) !important;
          border-color: rgba(255, 255, 255, 0.1) !important;
          color: #e0e0e0 !important;
        }

        .watchlist-manage-modal .ant-input::placeholder {
          color: #a0a0a0 !important;
        }

        .watchlist-manage-modal .ant-empty-description {
          color: #a0a0a0;
        }

        .watchlist-manage-modal .ant-btn-primary {
          background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
          border: none;
        }

        /* 滚动条样式 */
        .watchlist-manage-modal ::-webkit-scrollbar {
          width: 6px;
        }

        .watchlist-manage-modal ::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 3px;
        }

        .watchlist-manage-modal ::-webkit-scrollbar-thumb {
          background: rgba(0, 212, 255, 0.3);
          border-radius: 3px;
        }

        .watchlist-manage-modal ::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 212, 255, 0.5);
        }
      `}</style>
    </Modal>
  );
};

export default WatchlistManageModal;
