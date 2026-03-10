/**
 * ==============================================
 * 股票详情弹窗组件
 * ==============================================
 * 显示股票完整信息、K线图、分时图等
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Modal, Tabs, Row, Col, Statistic, Tag, Spin, message, Button, Space } from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  MinusOutlined,
  SyncOutlined,
  StarOutlined,
  StarFilled,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import CandlestickChart from './CandlestickChart';
import TimeChart from './TimeChart';
import PriceChart from './PriceChart';
import type { Quote } from '../types/market';

interface StockDetailModalProps {
  visible: boolean;
  quote: Quote | null;
  priceHistory: Quote[];
  onClose: () => void;
}

const StockDetailModal: React.FC<StockDetailModalProps> = ({
  visible,
  quote,
  priceHistory,
  onClose,
}) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('kline');
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(false);

  // 检查是否收藏
  useEffect(() => {
    if (quote?.symbol) {
      const favorites = JSON.parse(localStorage.getItem('stock_favorites') || '[]');
      setIsFavorite(favorites.includes(quote.symbol));
    }
  }, [quote?.symbol]);

  // 切换收藏状态
  const toggleFavorite = () => {
    if (!quote?.symbol) return;

    const favorites = JSON.parse(localStorage.getItem('stock_favorites') || '[]');
    let newFavorites: string[];

    if (isFavorite) {
      newFavorites = favorites.filter((s: string) => s !== quote.symbol);
      message.success(t('realtime.removeFavorite'));
    } else {
      newFavorites = [...favorites, quote.symbol];
      message.success(t('realtime.addFavorite'));
    }

    localStorage.setItem('stock_favorites', JSON.stringify(newFavorites));
    setIsFavorite(!isFavorite);
  };

  // 计算涨跌状态
  const getChangeStatus = useMemo(() => {
    if (!quote) return { type: 'neutral', icon: <MinusOutlined />, color: '#a0a0a0' };

    if (quote.change > 0) {
      return { type: 'rise', icon: <RiseOutlined />, color: '#f5c842' };
    } else if (quote.change < 0) {
      return { type: 'fall', icon: <FallOutlined />, color: '#ff4d4f' };
    }
    return { type: 'neutral', icon: <MinusOutlined />, color: '#a0a0a0' };
  }, [quote]);

  // 格式化数字
  const formatNumber = (num: number | undefined, decimals: number = 2): string => {
    if (num === undefined || num === null) return '-';
    return num.toFixed(decimals);
  };

  // 格式化成交量
  const formatVolume = (volume: number | undefined): string => {
    if (volume === undefined || volume === null) return '-';
    if (volume >= 100000000) {
      return `${(volume / 100000000).toFixed(2)}亿`;
    } else if (volume >= 10000) {
      return `${(volume / 10000).toFixed(2)}万`;
    }
    return volume.toString();
  };

  if (!quote) return null;

  const tabItems = [
    {
      key: 'kline',
      label: t('realtime.klineChart'),
      children: (
        <div style={{ height: '500px' }}>
          <CandlestickChart symbol={quote.symbol} stockName={quote.name} />
        </div>
      ),
    },
    {
      key: 'time',
      label: t('realtime.timeChart'),
      children: (
        <div style={{ height: '500px' }}>
          {priceHistory.length > 1 ? (
            <TimeChart data={priceHistory} symbol={quote.symbol} />
          ) : (
            <div style={{ textAlign: 'center', padding: '100px 0', color: '#999' }}>
              {t('realtime.noTimeChartData')}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'price',
      label: t('realtime.priceChart'),
      children: (
        <div style={{ height: '400px' }}>
          {priceHistory.length > 1 ? (
            <PriceChart data={priceHistory} symbol={quote.symbol} />
          ) : (
            <div style={{ textAlign: 'center', padding: '100px 0', color: '#999' }}>
              {t('realtime.noChartData')}
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: '#f5c842', fontSize: '18px', fontWeight: 600 }}>
              {quote.name || quote.symbol}
            </span>
            <Tag
              style={{
                background: `${getChangeStatus.color}20`,
                border: `1px solid ${getChangeStatus.color}`,
                color: getChangeStatus.color,
              }}
            >
              {getChangeStatus.icon} {quote.change >= 0 ? '+' : ''}{formatNumber(quote.change)} ({quote.change_pct >= 0 ? '+' : ''}{formatNumber(quote.change_pct)}%)
            </Tag>
            <Tag style={{ background: 'rgba(0, 212, 255, 0.1)', border: '1px solid #00d4ff', color: '#00d4ff' }}>
              {quote.symbol}
            </Tag>
          </div>
          <Space>
            <Button
              type="text"
              size="small"
              icon={isFavorite ? <StarFilled style={{ color: '#f5c842' }} /> : <StarOutlined />}
              onClick={toggleFavorite}
              title={isFavorite ? t('realtime.removeFavorite') : t('realtime.addFavorite')}
            />
            <Button
              type="text"
              size="small"
              icon={<SyncOutlined />}
              onClick={() => {
                setLoading(true);
                setTimeout(() => setLoading(false), 500);
              }}
              title={t('realtime.refresh')}
            />
          </Space>
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1000}
      centered
      className="stock-detail-modal"
      styles={{
        body: { padding: '24px', maxHeight: '80vh', overflow: 'auto' },
      }}
    >
      <Spin spinning={loading}>
        {/* 核心指标 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col span={4}>
            <div
              style={{
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #00d4ff',
              }}
            >
              <Statistic
                title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('realtime.price')}</span>}
                value={quote.price}
                precision={2}
                valueStyle={{ color: getChangeStatus.color, fontSize: '20px', fontFamily: '"JetBrains Mono", monospace' }}
                suffix="¥"
              />
            </div>
          </Col>
          <Col span={4}>
            <div
              style={{
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #f5c842',
              }}
            >
              <Statistic
                title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('realtime.high')}</span>}
                value={quote.high || '-'}
                precision={2}
                valueStyle={{ color: '#f5c842', fontSize: '20px', fontFamily: '"JetBrains Mono", monospace' }}
                suffix={quote.high ? '¥' : ''}
              />
            </div>
          </Col>
          <Col span={4}>
            <div
              style={{
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #ff4d4f',
              }}
            >
              <Statistic
                title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('realtime.low')}</span>}
                value={quote.low || '-'}
                precision={2}
                valueStyle={{ color: '#ff4d4f', fontSize: '20px', fontFamily: '"JetBrains Mono", monospace' }}
                suffix={quote.low ? '¥' : ''}
              />
            </div>
          </Col>
          <Col span={4}>
            <div
              style={{
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #b0b0b0',
              }}
            >
              <Statistic
                title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('realtime.open')}</span>}
                value={quote.open || '-'}
                precision={2}
                valueStyle={{ color: '#e0e0e0', fontSize: '20px', fontFamily: '"JetBrains Mono", monospace' }}
                suffix={quote.open ? '¥' : ''}
              />
            </div>
          </Col>
          <Col span={4}>
            <div
              style={{
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #808080',
              }}
            >
              <Statistic
                title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('realtime.prevClose')}</span>}
                value={quote.prev_close || '-'}
                precision={2}
                valueStyle={{ color: '#808080', fontSize: '20px', fontFamily: '"JetBrains Mono", monospace' }}
                suffix={quote.prev_close ? '¥' : ''}
              />
            </div>
          </Col>
          <Col span={4}>
            <div
              style={{
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #1890ff',
              }}
            >
              <Statistic
                title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('realtime.volume')}</span>}
                value={formatVolume(quote.volume)}
                valueStyle={{ color: '#1890ff', fontSize: '20px', fontFamily: '"JetBrains Mono", monospace' }}
              />
            </div>
          </Col>
        </Row>

        {/* 更多指标 */}
        <Row gutter={[16, 8]} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('realtime.amount')}</div>
            <div style={{ color: '#e0e0e0', fontFamily: '"JetBrains Mono", monospace' }}>
              {formatVolume((quote.amount || 0) * 10000)}
            </div>
          </Col>
          <Col span={6}>
            <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('realtime.turnoverRate')}</div>
            <div style={{ color: '#e0e0e0', fontFamily: '"JetBrains Mono", monospace' }}>
              {quote.turnover_rate !== undefined ? `${quote.turnover_rate.toFixed(2)}%` : '-'}
            </div>
          </Col>
          <Col span={6}>
            <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('realtime.peRatio')}</div>
            <div style={{ color: '#e0e0e0', fontFamily: '"JetBrains Mono", monospace' }}>
              {quote.pe_ratio !== undefined ? quote.pe_ratio.toFixed(2) : '-'}
            </div>
          </Col>
          <Col span={6}>
            <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('realtime.amplitude')}</div>
            <div style={{ color: '#e0e0e0', fontFamily: '"JetBrains Mono", monospace' }}>
              {quote.amplitude !== undefined ? `${quote.amplitude.toFixed(2)}%` : '-'}
            </div>
          </Col>
          <Col span={6}>
            <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('realtime.bidPrice')}</div>
            <div style={{ color: '#00d4ff', fontFamily: '"JetBrains Mono", monospace' }}>
              {quote.bid_price ? formatNumber(quote.bid_price) : '-'}
            </div>
          </Col>
          <Col span={6}>
            <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('realtime.askPrice')}</div>
            <div style={{ color: '#00d4ff', fontFamily: '"JetBrains Mono", monospace' }}>
              {quote.ask_price ? formatNumber(quote.ask_price) : '-'}
            </div>
          </Col>
        </Row>

        {/* 图表标签页 */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          style={{ marginTop: '16px' }}
        />
      </Spin>

      <style>{`
        .stock-detail-modal .ant-modal-content {
          background: rgba(13, 20, 24, 0.98) !important;
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 12px;
        }

        .stock-detail-modal .ant-modal-header {
          background: transparent !important;
          border-bottom: 1px solid rgba(0, 212, 255, 0.1);
        }

        .stock-detail-modal .ant-modal-title {
          color: #f5c842 !important;
        }

        .stock-detail-modal .ant-modal-close {
          color: #a0a0a0;
        }

        .stock-detail-modal .ant-modal-close:hover {
          color: #00d4ff;
        }

        .stock-detail-modal .ant-tabs-tab {
          color: #a0a0a0 !important;
        }

        .stock-detail-modal .ant-tabs-tab-active {
          color: #00d4ff !important;
        }

        .stock-detail-modal .ant-tabs-ink-bar {
          background: #00d4ff !important;
        }

        .stock-detail-modal .ant-statistic-title {
          color: #a0a0a0 !important;
        }
      `}</style>
    </Modal>
  );
};

export default StockDetailModal;
