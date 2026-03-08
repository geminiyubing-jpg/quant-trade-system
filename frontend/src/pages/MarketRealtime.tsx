/**
 * ==============================================
 * 实时行情页面
 * ==============================================
 */

import React, { useEffect, useState } from 'react';
import { Table, Tag, Card, Space, Button, Input, message, Spin, Typography, Row, Col, Statistic } from 'antd';
import { ThunderboltOutlined, SyncOutlined, PlusOutlined, MinusOutlined } from '@ant-design/icons';
import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import websocketService from '../services/websocket';
import { selectQuotes } from '../store/slices/marketDataSlice';
import type { RootState } from '../store';

const { Title, Text } = Typography;

interface Quote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  amount: number;
  bid_price?: number;
  ask_price?: number;
  high?: number;
  low?: number;
  open?: number;
  prev_close?: number;
  timestamp: string;
}

const MarketRealtime: React.FC = () => {
  const { t } = useTranslation();
  const quotes = useSelector((state: RootState) => selectQuotes(state));
  const [connected, setConnected] = useState(false);
  const [subscribedSymbols, setSubscribedSymbols] = useState<string[]>([]);
  const [inputSymbol, setInputSymbol] = useState('');

  useEffect(() => {
    // 连接 WebSocket
    websocketService.connect();
    setConnected(websocketService.isConnected());

    // 检查连接状态
    const checkConnection = setInterval(() => {
      setConnected(websocketService.isConnected());
    }, 1000);

    // 默认订阅几只股票
    const defaultSymbols = ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH'];
    websocketService.subscribe(defaultSymbols);
    setSubscribedSymbols(defaultSymbols);

    return () => {
      clearInterval(checkConnection);
      // 不在这里断开，让它在应用生命周期中保持连接
    };
  }, []);

  const handleSubscribe = () => {
    console.log('🔘 点击订阅按钮');
    console.log('📝 输入的股票代码:', inputSymbol);
    console.log('🔌 WebSocket 连接状态:', websocketService.isConnected());

    if (!inputSymbol.trim()) {
      message.warning(t('realtime.subscribeWarning'));
      return;
    }

    if (subscribedSymbols.includes(inputSymbol)) {
      message.warning(t('realtime.subscribeExist'));
      return;
    }

    if (subscribedSymbols.length >= 100) {
      message.error(t('realtime.subscribeLimit'));
      return;
    }

    console.log('📋 准备订阅:', [inputSymbol]);
    console.log('📋 当前订阅列表:', subscribedSymbols);

    try {
      // 调用订阅服务
      const sentImmediately = websocketService.subscribe([inputSymbol]);

      // 无论是否立即发送，都更新前端状态
      setSubscribedSymbols([...subscribedSymbols, inputSymbol]);
      setInputSymbol('');

      if (sentImmediately) {
        message.success(`${t('realtime.subscribeSuccess')} ${inputSymbol}`);
        console.log('✅ 订阅请求已立即发送');
      } else {
        message.info(`${t('realtime.subscribeSuccess')} ${inputSymbol} (WebSocket 连接中...)`);
        console.log('⏳ 订阅请求已排队，WebSocket 连接后将自动订阅');
      }
    } catch (error) {
      console.error('❌ 订阅失败:', error);
      message.error(`订阅失败: ${error}`);
    }
  };

  const handleUnsubscribe = (symbol: string) => {
    websocketService.unsubscribe([symbol]);
    setSubscribedSymbols(subscribedSymbols.filter((s) => s !== symbol));
    message.info(`${t('realtime.unsubscribeSuccess')} ${symbol}`);
  };

  const formatNumber = (num: number, decimals: number = 2): string => {
    return num.toFixed(decimals);
  };

  const formatVolume = (volume: number): string => {
    if (volume >= 100000000) {
      return `${(volume / 100000000).toFixed(2)} 亿`;
    } else if (volume >= 10000) {
      return `${(volume / 10000).toFixed(2)} 万`;
    }
    return volume.toString();
  };

  const getChangeColor = (change: number): string => {
    if (change > 0) return '#ff4d4f'; // 红色上涨
    if (change < 0) return '#52c41a'; // 绿色下跌
    return '#000000'; // 黑色不变
  };

  const columns = [
    {
      title: t('realtime.symbol'),
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
      fixed: 'left' as const,
      render: (symbol: string) => <Text strong>{symbol}</Text>,
    },
    {
      title: t('realtime.name'),
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: t('realtime.price'),
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price: number, record: Quote) => (
        <Text style={{ color: getChangeColor(record.change), fontWeight: 'bold' }}>
          {formatNumber(price)}
        </Text>
      ),
      sorter: (a: Quote, b: Quote) => a.price - b.price,
    },
    {
      title: t('realtime.change'),
      dataIndex: 'change',
      key: 'change',
      width: 100,
      render: (change: number) => (
        <Text style={{ color: getChangeColor(change) }}>{formatNumber(change)}</Text>
      ),
    },
    {
      title: t('realtime.changePercent'),
      dataIndex: 'change_pct',
      key: 'change_pct',
      width: 100,
      render: (change_pct: number) => (
        <Text style={{ color: getChangeColor(change_pct) }}>{formatNumber(change_pct)}%</Text>
      ),
      sorter: (a: Quote, b: Quote) => a.change_pct - b.change_pct,
    },
    {
      title: t('realtime.volume'),
      dataIndex: 'volume',
      key: 'volume',
      width: 120,
      render: (volume: number) => formatVolume(volume),
      sorter: (a: Quote, b: Quote) => a.volume - b.volume,
    },
    {
      title: t('realtime.amount'),
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number) => formatVolume(amount * 10000),
      sorter: (a: Quote, b: Quote) => a.amount - b.amount,
    },
    {
      title: t('realtime.bidPrice'),
      dataIndex: 'bid_price',
      key: 'bid_price',
      width: 100,
      render: (price?: number) => (price ? formatNumber(price) : '-'),
    },
    {
      title: t('realtime.askPrice'),
      dataIndex: 'ask_price',
      key: 'ask_price',
      width: 100,
      render: (price?: number) => (price ? formatNumber(price) : '-'),
    },
    {
      title: t('realtime.high'),
      dataIndex: 'high',
      key: 'high',
      width: 100,
      render: (price?: number) => (price ? formatNumber(price) : '-'),
    },
    {
      title: t('realtime.low'),
      dataIndex: 'low',
      key: 'low',
      width: 100,
      render: (price?: number) => (price ? formatNumber(price) : '-'),
    },
    {
      title: t('realtime.open'),
      dataIndex: 'open',
      key: 'open',
      width: 100,
      render: (price?: number) => (price ? formatNumber(price) : '-'),
    },
    {
      title: t('realtime.prevClose'),
      dataIndex: 'prev_close',
      key: 'prev_close',
      width: 100,
      render: (price?: number) => (price ? formatNumber(price) : '-'),
    },
    {
      title: t('realtime.action'),
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: Quote) => (
        <Button
          type="link"
          danger
          size="small"
          icon={<MinusOutlined />}
          onClick={() => handleUnsubscribe(record.symbol)}
        >
          {t('realtime.unsubscribe')}
        </Button>
      ),
    },
  ];

  const quoteList = Object.values(quotes).filter((quote) => subscribedSymbols.includes(quote.symbol));

  // 计算统计数据
  const totalStocks = quoteList.length;
  const risingStocks = quoteList.filter((q) => q.change > 0).length;
  const fallingStocks = quoteList.filter((q) => q.change < 0).length;
  const flatStocks = quoteList.filter((q) => q.change === 0).length;

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 标题栏 */}
          <Row justify="space-between" align="middle">
            <Col>
              <Space>
                <Title level={3} style={{ margin: 0 }}>
                  <ThunderboltOutlined /> {t('realtime.title')}
                </Title>
                <Tag color={connected ? 'green' : 'red'}>
                  {connected ? t('realtime.connected') : t('realtime.disconnected')}
                </Tag>
              </Space>
            </Col>
            <Col>
              <Space>
                <Input
                  placeholder={t('realtime.inputPlaceholder')}
                  value={inputSymbol}
                  onChange={(e) => setInputSymbol(e.target.value.toUpperCase())}
                  onPressEnter={handleSubscribe}
                  style={{ width: 200 }}
                  maxLength={20}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={handleSubscribe}>
                  {t('realtime.subscribe')}
                </Button>
                <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                  {t('realtime.refresh')}
                </Button>
              </Space>
            </Col>
          </Row>

          {/* 统计数据 */}
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title={t('realtime.stats.total')}
                value={totalStocks}
                suffix={t('realtime.stats.unit')}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={t('realtime.stats.rising')}
                value={risingStocks}
                suffix={t('realtime.stats.unit')}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={t('realtime.stats.falling')}
                value={fallingStocks}
                suffix={t('realtime.stats.unit')}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title={t('realtime.stats.flat')}
                value={flatStocks}
                suffix={t('realtime.stats.unit')}
              />
            </Col>
          </Row>

          {/* 行情表格 */}
          {connected ? (
            <Table
              columns={columns}
              dataSource={quoteList}
              rowKey="symbol"
              pagination={{ pageSize: 20 }}
              scroll={{ x: 1500 }}
              size="small"
              rowClassName={(record) => {
                if (record.change > 0) return 'row-rising';
                if (record.change < 0) return 'row-falling';
                return '';
              }}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '100px 0' }}>
              <Spin size="large" tip={t('realtime.connecting')} />
            </div>
          )}
        </Space>
      </Card>

      <style>{`
        .row-rising {
          background-color: rgba(255, 77, 79, 0.05);
        }
        .row-falling {
          background-color: rgba(82, 196, 26, 0.05);
        }
      `}</style>
    </div>
  );
};

export default MarketRealtime;
