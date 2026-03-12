/**
 * MarketDetailModal - 市场详情弹窗
 * 显示指数/商品的详细信息、历史走势图
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Modal, Tabs, Row, Col, Statistic, Tag, message, Button, Space } from 'antd';
import {
  StarOutlined,
  StarFilled,
  BellOutlined,
  LineChartOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Area,
  AreaChart,
  CartesianGrid,
} from 'recharts';
import { MarketItem, COLOR_CONFIG, formatPrice, formatChangePercent } from '../../data/marketPulseData';

interface MarketDetailModalProps {
  visible: boolean;
  item: MarketItem | null;
  onClose: () => void;
  onAddToWatchlist?: (item: MarketItem) => void;
  onRemoveFromWatchlist?: (itemId: string) => void;
  isWatched?: boolean;
}

// 生成扩展历史数据
const generateExtendedHistory = (basePrice: number, points: number = 48): number[] => {
  const data: number[] = [];
  let currentPrice = basePrice;
  for (let i = 0; i < points; i++) {
    const change = (Math.random() - 0.5) * basePrice * 0.015;
    currentPrice = Math.max(basePrice * 0.85, Math.min(basePrice * 1.15, currentPrice + change));
    data.push(currentPrice);
  }
  return data;
};

// 自定义 Tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'rgba(0, 0, 0, 0.9)',
        border: '1px solid rgba(0, 212, 255, 0.3)',
        borderRadius: '8px',
        padding: '8px 12px',
        color: '#e0e0e0',
      }}>
        <div style={{ fontSize: '12px', color: '#a0a0a0' }}>时间: {payload[0].payload.time}</div>
        <div style={{ fontSize: '14px', fontWeight: 600, color: payload[0].color }}>
          价格: {formatPrice(payload[0].value)}
        </div>
      </div>
    );
  }
  return null;
};

const MarketDetailModal: React.FC<MarketDetailModalProps> = ({
  visible,
  item,
  onClose,
  onAddToWatchlist,
  onRemoveFromWatchlist,
  isWatched = false,
}) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('overview');
  const [watched, setWatched] = useState(isWatched);
  const [extendedData, setExtendedData] = useState<{ time: string; price: number }[]>([]);

  // 初始化数据
  useEffect(() => {
    if (item) {
      // 生成扩展历史数据
      const history = generateExtendedHistory(item.price, 48);
      const now = new Date();
      const data = history.map((price, index) => {
        const time = new Date(now.getTime() - (47 - index) * 30 * 60000);
        return {
          time: `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`,
          price,
        };
      });
      setExtendedData(data);
      setWatched(isWatched);
    }
  }, [item, isWatched]);

  // 切换收藏状态
  const toggleWatch = () => {
    if (!item) return;

    if (watched) {
      onRemoveFromWatchlist?.(item.id);
      message.success(t('marketPulse.detail.removedFromWatchlist', { name: item.name }));
    } else {
      onAddToWatchlist?.(item);
      message.success(t('marketPulse.detail.addedToWatchlist', { name: item.name }));
    }
    setWatched(!watched);
  };

  // 设置价格提醒
  const handleSetAlert = () => {
    if (!item) return;
    message.info(t('marketPulse.detail.alertDeveloping', { name: item.name }));
  };

  const isUp = item ? item.changePercent >= 0 : false;
  const changeColor = isUp ? COLOR_CONFIG.up : COLOR_CONFIG.down;

  // 计算统计数据
  const stats = useMemo(() => {
    if (!item || extendedData.length === 0) return null;

    const prices = extendedData.map(d => d.price);
    const high = Math.max(...prices);
    const low = Math.min(...prices);
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    const volatility = ((high - low) / avg * 100).toFixed(2);

    return { high, low, avg, volatility };
  }, [item, extendedData]);

  if (!item) return null;

  const tabItems = [
    {
      key: 'overview',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <InfoCircleOutlined />
          {t('marketPulse.detail.overview')}
        </span>
      ),
      children: (
        <div style={{ padding: '16px 0' }}>
          {/* 核心指标 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <div style={{
                padding: '16px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #00d4ff',
              }}>
                <Statistic
                  title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('marketPulse.detail.currentPrice')}</span>}
                  value={item.price}
                  precision={2}
                  valueStyle={{ color: changeColor, fontSize: '24px', fontFamily: '"JetBrains Mono", monospace' }}
                  suffix={item.unit || ''}
                />
              </div>
            </Col>
            <Col span={6}>
              <div style={{
                padding: '16px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: `3px solid ${isUp ? '#ef4444' : '#22c55e'}`,
              }}>
                <Statistic
                  title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('marketPulse.detail.changePercent')}</span>}
                  value={item.changePercent}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: changeColor, fontSize: '24px', fontFamily: '"JetBrains Mono", monospace' }}
                />
              </div>
            </Col>
            <Col span={6}>
              <div style={{
                padding: '16px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #f5c842',
              }}>
                <Statistic
                  title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('marketPulse.detail.todayHigh')}</span>}
                  value={stats?.high || item.price}
                  precision={2}
                  valueStyle={{ color: '#f5c842', fontSize: '24px', fontFamily: '"JetBrains Mono", monospace' }}
                />
              </div>
            </Col>
            <Col span={6}>
              <div style={{
                padding: '16px',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '8px',
                borderLeft: '3px solid #ff4d4f',
              }}>
                <Statistic
                  title={<span style={{ color: '#a0a0a0', fontSize: '12px' }}>{t('marketPulse.detail.todayLow')}</span>}
                  value={stats?.low || item.price}
                  precision={2}
                  valueStyle={{ color: '#ff4d4f', fontSize: '24px', fontFamily: '"JetBrains Mono", monospace' }}
                />
              </div>
            </Col>
          </Row>

          {/* 详细信息 */}
          <Row gutter={[24, 16]}>
            <Col span={8}>
              <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('marketPulse.detail.exchange')}</div>
              <div style={{ color: '#e0e0e0', fontFamily: '"JetBrains Mono", monospace' }}>
                {item.exchange || '-'}
              </div>
            </Col>
            <Col span={8}>
              <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('marketPulse.detail.volatility')}</div>
              <div style={{ color: '#e0e0e0', fontFamily: '"JetBrains Mono", monospace' }}>
                {stats?.volatility || '-'}%
              </div>
            </Col>
            <Col span={8}>
              <div style={{ color: '#a0a0a0', fontSize: '12px', marginBottom: '4px' }}>{t('marketPulse.detail.changePoints')}</div>
              <div style={{ color: changeColor, fontFamily: '"JetBrains Mono", monospace' }}>
                {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)}
              </div>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'chart',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <LineChartOutlined />
          {t('marketPulse.detail.chart')}
        </span>
      ),
      children: (
        <div style={{ height: '400px', padding: '16px 0' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={extendedData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={changeColor} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={changeColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="time"
                stroke="#a0a0a0"
                tick={{ fill: '#a0a0a0', fontSize: 11 }}
                interval="preserveStartEnd"
              />
              <YAxis
                stroke="#a0a0a0"
                tick={{ fill: '#a0a0a0', fontSize: 11 }}
                domain={['auto', 'auto']}
                tickFormatter={(v) => v.toFixed(2)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="price"
                stroke={changeColor}
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorPrice)"
              />
            </AreaChart>
          </ResponsiveContainer>
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
              {item.name}
            </span>
            {item.nameEn && (
              <span style={{ color: '#a0a0a0', fontSize: '14px' }}>
                {item.nameEn}
              </span>
            )}
            <Tag
              style={{
                background: `${changeColor}20`,
                border: `1px solid ${changeColor}`,
                color: changeColor,
              }}
            >
              {formatChangePercent(item.changePercent)}
            </Tag>
            {item.exchange && (
              <Tag style={{ background: 'rgba(0, 212, 255, 0.1)', border: '1px solid #00d4ff', color: '#00d4ff' }}>
                {item.exchange}
              </Tag>
            )}
          </div>
          <Space>
            <Button
              type="text"
              size="small"
              icon={watched ? <StarFilled style={{ color: '#f5c842' }} /> : <StarOutlined />}
              onClick={toggleWatch}
              title={watched ? t('marketPulse.detail.removeWatch') : t('marketPulse.detail.addWatch')}
            >
              {watched ? t('marketPulse.detail.watched') : t('marketPulse.detail.watch')}
            </Button>
            <Button
              type="text"
              size="small"
              icon={<BellOutlined />}
              onClick={handleSetAlert}
              title={t('marketPulse.detail.setAlert')}
            >
              {t('marketPulse.detail.alert')}
            </Button>
          </Space>
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      centered
      className="market-detail-modal"
      styles={{
        body: { padding: '24px', maxHeight: '70vh', overflow: 'auto' },
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          style={{ marginTop: '8px' }}
        />
      </motion.div>

      <style>{`
        .market-detail-modal .ant-modal-content {
          background: rgba(13, 20, 24, 0.98) !important;
          border: 1px solid rgba(0, 212, 255, 0.2);
          border-radius: 12px;
        }

        .market-detail-modal .ant-modal-header {
          background: transparent !important;
          border-bottom: 1px solid rgba(0, 212, 255, 0.1);
        }

        .market-detail-modal .ant-modal-title {
          color: #f5c842 !important;
        }

        .market-detail-modal .ant-modal-close {
          color: #a0a0a0;
        }

        .market-detail-modal .ant-modal-close:hover {
          color: #00d4ff;
        }

        .market-detail-modal .ant-tabs-tab {
          color: #a0a0a0 !important;
        }

        .market-detail-modal .ant-tabs-tab-active {
          color: #00d4ff !important;
        }

        .market-detail-modal .ant-tabs-ink-bar {
          background: #00d4ff !important;
        }

        .market-detail-modal .ant-statistic-title {
          color: #a0a0a0 !important;
        }

        .market-detail-modal .recharts-cartesian-axis-tick-value {
          fill: #a0a0a0;
        }
      `}</style>
    </Modal>
  );
};

export default MarketDetailModal;
