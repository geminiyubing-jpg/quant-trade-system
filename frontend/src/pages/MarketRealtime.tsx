/**
 * ==============================================
 * 实时行情页面 - Bloomberg Terminal 深色主题
 * ==============================================
 * 专业金融交易终端风格
 * 深色背景 + 金色/绿色/深蓝配色
 */

import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { Table, Tag, Card, Space, Button, Input, message, Spin, Typography, Row, Col, Statistic, Tooltip } from 'antd';
import { ThunderboltOutlined, SyncOutlined, PlusOutlined, MinusOutlined, InfoCircleOutlined, ImportOutlined, StarOutlined, StarFilled, BellOutlined } from '@ant-design/icons';
import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import websocketService from '../services/websocket';
import { selectQuotes } from '../store/slices/marketDataSlice';
import type { RootState } from '../store';
import type { Quote } from '../types/market';
import StockDetailModal from '../components/StockDetailModal';
import BatchImportModal from '../components/BatchImportModal';
import PriceAlertModal from '../components/PriceAlertModal';
import ExportButton from '../components/common/ExportButton';
import { usePriceHistory } from '../hooks/usePriceHistory';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import watchlistService from '../services/watchlist';
import logger from '../utils/logger';

const { Title, Text } = Typography;

// 价格闪烁类型
type FlashType = 'up' | 'down' | 'none';

const MarketRealtime: React.FC = () => {
  const { t } = useTranslation();
  const quotes = useSelector((state: RootState) => selectQuotes(state));
  const [connected, setConnected] = useState(false);
  const [subscribedSymbols, setSubscribedSymbols] = useState<string[]>([]);
  const [inputSymbol, setInputSymbol] = useState('');

  // 价格闪烁状态
  const [flashStates, setFlashStates] = useState<Record<string, FlashType>>({});
  const [prevPrices, setPrevPrices] = useState<Record<string, number>>({});

  // 图表相关状态
  const [stockDetailVisible, setStockDetailVisible] = useState(false);
  const [batchImportVisible, setBatchImportVisible] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  // 预警弹窗状态
  const [alertModalVisible, setAlertModalVisible] = useState(false);
  const [alertSymbol, setAlertSymbol] = useState<string>('');
  const [alertQuote, setAlertQuote] = useState<Quote | null>(null);

  // 选中行状态（用于导出和快捷操作）
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [currentHighlightRow, setCurrentHighlightRow] = useState<number>(-1);

  // 自选股状态
  const [watchlistSymbols, setWatchlistSymbols] = useState<Set<string>>(new Set());

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys as string[]);
    },
  };

  // 使用 price history hook
  const { getHistory } = usePriceHistory(quotes, subscribedSymbols);

  // 加载自选股列表
  useEffect(() => {
    const loadWatchlist = async () => {
      try {
        const response = await watchlistService.getItems();
        const symbols = new Set(response.items.map((item) => item.symbol));
        setWatchlistSymbols(symbols);
      } catch (error) {
        logger.error('加载自选股失败:', error);
      }
    };
    loadWatchlist();
  }, []);

  // 键盘快捷键处理
  const handleKeyboardSearch = useCallback(() => {
    const input = document.querySelector('.symbol-input input') as HTMLInputElement;
    if (input) {
      input.focus();
      input.select();
    }
  }, []);

  const handleKeyboardExport = useCallback(() => {
    // 触发导出
    const exportBtn = document.querySelector('.export-btn-enhanced') as HTMLElement;
    if (exportBtn) {
      exportBtn.click();
    }
  }, []);

  const handleKeyboardEscape = useCallback(() => {
    if (stockDetailVisible) {
      setStockDetailVisible(false);
    } else if (batchImportVisible) {
      setBatchImportVisible(false);
    }
  }, [stockDetailVisible, batchImportVisible]);

  const handleKeyboardNavigate = useCallback((direction: 'up' | 'down') => {
    const quoteList = Object.values(quotes).filter((quote) => subscribedSymbols.includes(quote.symbol));
    if (quoteList.length === 0) return;

    if (direction === 'up') {
      setCurrentHighlightRow((prev) => (prev > 0 ? prev - 1 : quoteList.length - 1));
    } else {
      setCurrentHighlightRow((prev) => (prev < quoteList.length - 1 ? prev + 1 : 0));
    }
  }, [quotes, subscribedSymbols]);

  const handleKeyboardOpenDetail = useCallback(() => {
    const quoteList = Object.values(quotes).filter((quote) => subscribedSymbols.includes(quote.symbol));
    if (quoteList.length > 0 && currentHighlightRow >= 0 && currentHighlightRow < quoteList.length) {
      const symbol = quoteList[currentHighlightRow].symbol;
      setSelectedSymbol(symbol);
      setStockDetailVisible(true);
    }
  }, [quotes, subscribedSymbols, currentHighlightRow]);

  const handleKeyboardAddToWatchlist = useCallback(async () => {
    const quoteList = Object.values(quotes).filter((quote) => subscribedSymbols.includes(quote.symbol));
    if (quoteList.length > 0 && currentHighlightRow >= 0 && currentHighlightRow < quoteList.length) {
      const symbol = quoteList[currentHighlightRow].symbol;
      await handleToggleWatchlist(symbol);
    }
  }, [quotes, subscribedSymbols, currentHighlightRow]);

  // 注册键盘快捷键
  useKeyboardShortcuts({
    'ctrl+k': handleKeyboardSearch,
    'ctrl+e': handleKeyboardExport,
    'escape': handleKeyboardEscape,
    'arrowup': () => handleKeyboardNavigate('up'),
    'arrowdown': () => handleKeyboardNavigate('down'),
    'enter': handleKeyboardOpenDetail,
    'ctrl+d': handleKeyboardAddToWatchlist,
  });

  // 使用 ref 存储定时器，避免闭包问题
  const flashTimersRef = useRef<Record<string, NodeJS.Timeout>>({});

  // 初始化连接
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
      // 清除所有闪烁定时器
      // eslint-disable-next-line react-hooks/exhaustive-deps
      Object.values(flashTimersRef.current).forEach((timer) => clearTimeout(timer));
    };
  }, []);

  // 检测价格变化并触发闪烁
  useEffect(() => {
    const quoteList = Object.values(quotes).filter((quote) =>
      subscribedSymbols.includes(quote.symbol)
    );

    quoteList.forEach((quote) => {
      const prevPrice = prevPrices[quote.symbol];
      const currentPrice = quote.price;

      // 如果价格发生变化
      if (prevPrice !== undefined && prevPrice !== currentPrice) {
        const flashType: FlashType = currentPrice > prevPrice ? 'up' : 'down';

        // 清除之前的定时器
        if (flashTimersRef.current[quote.symbol]) {
          clearTimeout(flashTimersRef.current[quote.symbol]);
        }

        // 设置闪烁状态
        setFlashStates((prev) => ({
          ...prev,
          [quote.symbol]: flashType,
        }));

        // 800ms 后清除闪烁效果
        flashTimersRef.current[quote.symbol] = setTimeout(() => {
          setFlashStates((prev) => ({
            ...prev,
            [quote.symbol]: 'none',
          }));
        }, 800);
      }

      // 更新上一次价格
      setPrevPrices((prev) => ({
        ...prev,
        [quote.symbol]: currentPrice,
      }));
    });
  }, [quotes, subscribedSymbols, prevPrices]);

  const handleSubscribe = () => {
    logger.debug('点击订阅按钮');
    logger.debug('输入的股票代码:', inputSymbol);
    logger.debug('WebSocket 连接状态:', websocketService.isConnected());

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

    logger.debug('准备订阅:', [inputSymbol]);
    logger.debug('当前订阅列表:', subscribedSymbols);

    try {
      // 调用订阅服务
      const sentImmediately = websocketService.subscribe([inputSymbol]);

      // 无论是否立即发送，都更新前端状态
      setSubscribedSymbols([...subscribedSymbols, inputSymbol]);
      setInputSymbol('');

      if (sentImmediately) {
        message.success(`${t('realtime.subscribeSuccess')} ${inputSymbol}`);
        logger.debug('订阅请求已立即发送');
      } else {
        message.info(`${t('realtime.subscribeSuccess')} ${inputSymbol} (WebSocket 连接中...)`);
        logger.debug('订阅请求已排队，WebSocket 连接后将自动订阅');
      }
    } catch (error) {
      logger.error('订阅失败:', error);
      message.error(`订阅失败: ${error}`);
    }
  };

  const handleUnsubscribe = useCallback((symbol: string) => {
    websocketService.unsubscribe([symbol]);
    setSubscribedSymbols((prev) => prev.filter((s) => s !== symbol));
    message.info(`${t('realtime.unsubscribeSuccess')} ${symbol}`);
  }, [t]);

  // 显示股票详情弹窗
  const handleShowStockDetail = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
    setStockDetailVisible(true);
  }, []);

  // 关闭股票详情弹窗
  const handleCloseStockDetail = () => {
    setStockDetailVisible(false);
    setSelectedSymbol(null);
  };

  // 显示预警设置弹窗
  const handleShowAlertModal = useCallback((symbol: string) => {
    setAlertSymbol(symbol);
    setAlertQuote(quotes[symbol] || null);
    setAlertModalVisible(true);
  }, [quotes]);

  // 关闭预警设置弹窗
  const handleCloseAlertModal = () => {
    setAlertModalVisible(false);
    setAlertSymbol('');
    setAlertQuote(null);
  };

  // 批量导入股票代码
  const handleBatchImport = (symbols: string[]) => {
    websocketService.subscribe(symbols);
    setSubscribedSymbols((prev) => [...prev, ...symbols]);
  };

  // 切换自选股状态
  const handleToggleWatchlist = useCallback(async (symbol: string) => {
    try {
      const isInWatchlist = watchlistSymbols.has(symbol);
      if (isInWatchlist) {
        await watchlistService.removeItem(symbol);
        setWatchlistSymbols((prev) => {
          const newSet = new Set(prev);
          newSet.delete(symbol);
          return newSet;
        });
        message.success(`${symbol} 已从自选移除`);
      } else {
        await watchlistService.addItem({ symbol });
        setWatchlistSymbols((prev) => new Set([...prev, symbol]));
        message.success(`${symbol} 已添加到自选`);
      }
    } catch (error) {
      logger.error('自选股操作失败:', error);
    }
  }, [watchlistSymbols]);

  // 双击打开股票详情
  const handleRowDoubleClick = (record: Quote) => {
    setSelectedSymbol(record.symbol);
    setStockDetailVisible(true);
  };

  const formatNumber = (num: number, decimals: number = 2): string => {
    return num.toFixed(decimals);
  };

  const formatVolume = (volume: number): string => {
    if (volume >= 100000000) {
      return `${(volume / 100000000).toFixed(2)}亿`;
    } else if (volume >= 10000) {
      return `${(volume / 10000).toFixed(2)}万`;
    }
    return volume.toString();
  };

  const getChangeColor = useCallback((change: number): string => {
    if (change > 0) return 'var(--bb-up, var(--color-up))';
    if (change < 0) return 'var(--bb-down, var(--color-down))';
    return 'var(--bb-neutral, var(--color-neutral))';
  }, []);

  // 使用 useMemo 缓存 columns 配置
  const columns = useMemo(() => [
    {
      title: t('realtime.symbol'),
      dataIndex: 'symbol',
      key: 'symbol',
      width: 110,
      render: (symbol: string) => (
        <Text strong style={{ color: 'var(--accent-blue)', fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}>
          {symbol}
        </Text>
      ),
    },
    {
      title: t('realtime.name'),
      dataIndex: 'name',
      key: 'name',
      width: 100,
      ellipsis: true,
      render: (name: string) => <Text style={{ color: 'var(--text-primary)' }}>{name}</Text>,
    },
    {
      title: t('realtime.price'),
      dataIndex: 'price',
      key: 'price',
      width: 90,
      render: (price: number, record: Quote) => {
        const flashType = flashStates[record.symbol] || 'none';
        return (
          <Text
            style={{ color: getChangeColor(record.change), fontWeight: 'bold', fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
            className={`price-flash-${flashType}`}
          >
            {formatNumber(price)}
          </Text>
        );
      },
      sorter: (a: Quote, b: Quote) => a.price - b.price,
    },
    {
      title: t('realtime.change'),
      dataIndex: 'change',
      key: 'change',
      width: 80,
      render: (change: number) => (
        <Text style={{ color: getChangeColor(change), fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}>
          {change > 0 ? '+' : ''}{formatNumber(change)}
        </Text>
      ),
    },
    {
      title: t('realtime.changePercent'),
      dataIndex: 'change_pct',
      key: 'change_pct',
      width: 90,
      render: (change_pct: number) => (
        <Text style={{ color: getChangeColor(change_pct), fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}>
          {change_pct > 0 ? '+' : ''}{formatNumber(change_pct)}%
        </Text>
      ),
      sorter: (a: Quote, b: Quote) => a.change_pct - b.change_pct,
    },
    {
      title: t('realtime.volume'),
      dataIndex: 'volume',
      key: 'volume',
      width: 100,
      render: (volume: number) => (
        <Text style={{ color: 'var(--text-secondary)', fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}>
          {formatVolume(volume)}
        </Text>
      ),
      sorter: (a: Quote, b: Quote) => a.volume - b.volume,
    },
    {
      title: t('realtime.amount'),
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount: number) => (
        <Text style={{ color: 'var(--text-secondary)', fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}>
          {formatVolume(amount * 10000)}
        </Text>
      ),
      sorter: (a: Quote, b: Quote) => a.amount - b.amount,
    },
    {
      title: t('realtime.action'),
      key: 'action',
      width: 200,
      render: (_: any, record: Quote) => {
        const isWatchlist = watchlistSymbols.has(record.symbol);
        return (
          <Space size="small">
            <Tooltip title={isWatchlist ? '从自选移除' : '添加到自选'}>
              <Button
                type="link"
                size="small"
                icon={isWatchlist ? <StarFilled style={{ color: '#fadb14' }} /> : <StarOutlined style={{ color: '#666' }} />}
                onClick={() => handleToggleWatchlist(record.symbol)}
              />
            </Tooltip>
            <Tooltip title={t('alerts.setAlert')}>
              <Button
                type="link"
                size="small"
                icon={<BellOutlined />}
                onClick={() => handleShowAlertModal(record.symbol)}
                style={{ color: 'var(--accent-blue)' }}
              />
            </Tooltip>
            <Button
              type="link"
              size="small"
              icon={<InfoCircleOutlined />}
              onClick={() => handleShowStockDetail(record.symbol)}
              style={{ color: 'var(--accent-gold)' }}
            >
              {t('realtime.stockDetail')}
            </Button>
            <Button
              type="link"
              danger
              size="small"
              icon={<MinusOutlined />}
              onClick={() => handleUnsubscribe(record.symbol)}
              style={{ color: 'var(--color-down)' }}
            />
          </Space>
        );
      },
    },
  ], [t, flashStates, watchlistSymbols, getChangeColor, handleToggleWatchlist, handleShowAlertModal, handleShowStockDetail, handleUnsubscribe]);

  // 使用 useMemo 缓存过滤后的行情列表
  const quoteList = useMemo(() =>
    Object.values(quotes).filter((quote) => subscribedSymbols.includes(quote.symbol)),
    [quotes, subscribedSymbols]
  );

  // 使用 useMemo 缓存统计数据
  const stats = useMemo(() => {
    const total = quoteList.length;
    const rising = quoteList.filter((q) => q.change > 0).length;
    const falling = quoteList.filter((q) => q.change < 0).length;
    const flat = quoteList.filter((q) => q.change === 0).length;
    return { total, rising, falling, flat };
  }, [quoteList]);

  const { total: totalStocks, rising: risingStocks, falling: fallingStocks, flat: flatStocks } = stats;

  return (
    <div className="market-realtime-container">
      {/* 网格背景 */}
      <div className="grid-background" />

      <Card className="market-card">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 标题栏 */}
          <Row justify="space-between" align="middle" className="header-row">
            <Col>
              <Space>
                <Title level={3} style={{ margin: 0, color: 'var(--accent-gold)', fontWeight: 700, letterSpacing: '1px' }}>
                  <ThunderboltOutlined /> {t('realtime.title')}
                </Title>
                <Tag
                  className={`connection-tag ${connected ? 'connected' : 'disconnected'}`}
                >
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
                  className="symbol-input"
                  style={{
                    width: 200,
                  }}
                  maxLength={20}
                />
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleSubscribe}
                  className="action-button subscribe-btn"
                >
                  {t('realtime.subscribe')}
                </Button>
                <Button
                  icon={<ImportOutlined />}
                  onClick={() => setBatchImportVisible(true)}
                  className="action-button batch-import-btn"
                >
                  {t('realtime.batchImport')}
                </Button>
                <ExportButton
                  data={quoteList.map((q) => ({
                    symbol: q.symbol,
                    name: q.name,
                    price: q.price,
                    change: q.change,
                    changePercent: q.change_pct,
                    volume: q.volume,
                    high: q.high,
                    low: q.low,
                    open: q.open,
                  }))}
                  selectedKeys={selectedRowKeys}
                  getRowKey={(item) => item.symbol}
                  filename={`market_data_${new Date().toISOString().split('T')[0]}`}
                  type="market"
                  className="action-button export-btn-enhanced"
                  onExportComplete={(format, count) => {
                    message.success(`成功导出 ${count} 条数据为 ${format.toUpperCase()}`);
                  }}
                />
                <Button
                  icon={<SyncOutlined />}
                  onClick={() => window.location.reload()}
                  className="action-button refresh-btn"
                >
                  {t('realtime.refresh')}
                </Button>
              </Space>
            </Col>
          </Row>

          {/* 统计数据 */}
          <Row gutter={16} className="stats-row">
            <Col span={6}>
              <div className="stat-card stat-total">
                <Statistic
                  title={t('realtime.stats.total')}
                  value={totalStocks}
                  suffix={t('realtime.stats.unit')}
                  valueStyle={{ color: 'var(--accent-blue)', fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
                />
              </div>
            </Col>
            <Col span={6}>
              <div className="stat-card stat-rising">
                <Statistic
                  title={t('realtime.stats.rising')}
                  value={risingStocks}
                  suffix={t('realtime.stats.unit')}
                  valueStyle={{ color: 'var(--color-up)', fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
                />
              </div>
            </Col>
            <Col span={6}>
              <div className="stat-card stat-falling">
                <Statistic
                  title={t('realtime.stats.falling')}
                  value={fallingStocks}
                  suffix={t('realtime.stats.unit')}
                  valueStyle={{ color: 'var(--color-down)', fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
                />
              </div>
            </Col>
            <Col span={6}>
              <div className="stat-card stat-flat">
                <Statistic
                  title={t('realtime.stats.flat')}
                  value={flatStocks}
                  suffix={t('realtime.stats.unit')}
                  valueStyle={{ color: 'var(--color-neutral)', fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
                />
              </div>
            </Col>
          </Row>

          {/* 行情表格 */}
          {connected ? (
            <div className="table-wrapper">
              <Table
                columns={columns}
                dataSource={quoteList}
                rowKey="symbol"
                rowSelection={rowSelection}
                onRow={(record) => ({
                  onDoubleClick: () => handleRowDoubleClick(record),
                  onClick: () => {
                    const index = quoteList.findIndex((q) => q.symbol === record.symbol);
                    setCurrentHighlightRow(index);
                  },
                })}
                pagination={{ pageSize: 20, showSizeChanger: true, showQuickJumper: true }}
                size="small"
                className="market-table"
                rowClassName={(record, index) => {
                  let classes = [];
                  if (record.change > 0) classes.push('row-rising');
                  if (record.change < 0) classes.push('row-falling');
                  if (index === currentHighlightRow) classes.push('row-highlighted');
                  return classes.join(' ');
                }}
              />
            </div>
          ) : (
            <div className="loading-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
              <Spin size="large" />
              <span style={{ color: '#666' }}>{t('realtime.connecting')}</span>
            </div>
          )}
        </Space>
      </Card>

      {/* 股票详情弹窗 */}
      <StockDetailModal
        visible={stockDetailVisible}
        quote={selectedSymbol ? quotes[selectedSymbol] || null : null}
        priceHistory={selectedSymbol ? getHistory(selectedSymbol) : []}
        onClose={handleCloseStockDetail}
      />

      {/* 批量导入弹窗 */}
      <BatchImportModal
        visible={batchImportVisible}
        existingSymbols={subscribedSymbols}
        onImport={handleBatchImport}
        onClose={() => setBatchImportVisible(false)}
        maxSymbols={100}
      />

      {/* 价格预警弹窗 */}
      <PriceAlertModal
        visible={alertModalVisible}
        symbol={alertSymbol}
        quote={alertQuote}
        onClose={handleCloseAlertModal}
      />

      <style>{`
        .market-realtime-container {
          position: relative;
          padding: 24px;
          min-height: 100vh;
          background: var(--bg-primary);
          font-family: 'Inter, -apple-system, BlinkMacSystem, "Segoe UI", Roboto, sans-serif;
          transition: background 0.3s ease;
        }

        /* 浅色主题特殊背景 */
        [data-theme="light"] .market-realtime-container {
          background: linear-gradient(135deg, #f8f9fb 0%, #ffffff 50%, #f1f5f9 100%);
        }

        /* 深色主题特殊背景 */
        [data-theme="dark"] .market-realtime-container {
          background: linear-gradient(135deg, #0a1214 0%, #0d1f2a 50%, #1a1e2a 100%);
        }

        /* 网格背景 */
        .grid-background {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-image:
            linear-gradient(var(--grid-color) 1px, transparent 1px),
            linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
          background-size: 50px 50px;
          pointer-events: none;
          z-index: 0;
        }

        /* 卡片样式 */
        .market-card {
          background: var(--bg-card) !important;
          border: 1px solid var(--border-color) !important;
          border-radius: 12px;
          box-shadow: var(--card-shadow);
          backdrop-filter: blur(10px);
          transition: all 0.3s ease;
        }

        /* 标题行 */
        .header-row {
          margin-bottom: 20px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--border-light);
        }

        /* 连接状态标签 */
        .connection-tag {
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 1px;
          animation: pulse-glow 2s infinite;
        }

        .connection-tag.connected {
          animation: pulse-glow-green 2s infinite;
        }

        @keyframes pulse-glow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }

        [data-theme="light"] .connection-tag {
          background: rgba(220, 38, 38, 0.1);
          border: 1px solid var(--color-down);
          color: var(--color-down);
        }

        [data-theme="light"] .connection-tag.connected {
          background: rgba(5, 150, 105, 0.1);
          border: 1px solid var(--color-up);
          color: var(--color-up);
        }

        [data-theme="dark"] .connection-tag {
          background: rgba(255, 77, 79, 0.15);
          border: 1px solid #ff4d4f;
          color: #ff4d4f;
        }

        [data-theme="dark"] .connection-tag.connected {
          background: rgba(245, 200, 66, 0.15);
          border: 1px solid #f5c842;
          color: #f5c842;
        }

        @keyframes pulse-glow-green {
          0%, 100% { box-shadow: 0 0 5px var(--color-up); }
          50% { box-shadow: 0 0 10px var(--color-up); }
        }

        /* 输入框样式 */
        .symbol-input::placeholder {
          color: var(--text-muted);
        }

        .symbol-input:focus {
          border-color: var(--input-focus-border) !important;
          box-shadow: 0 0 0 2px var(--border-color);
        }

        /* 按钮样式 */
        .action-button {
          font-weight: 600;
          letter-spacing: 0.5px;
          transition: all 0.2s ease;
        }

        .subscribe-btn {
          background: var(--button-primary-bg) !important;
          border: none !important;
          color: white !important;
        }

        .subscribe-btn:hover {
          background: var(--button-primary-hover) !important;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px var(--shadow-color);
        }

        .refresh-btn, .batch-import-btn, .export-btn {
          background: var(--hover-bg) !important;
          border: 1px solid var(--border-color) !important;
          color: var(--text-primary) !important;
        }

        .refresh-btn:hover, .batch-import-btn:hover, .export-btn:hover {
          background: var(--border-light) !important;
          border-color: var(--accent-blue) !important;
        }

        /* 统计卡片 */
        .stats-row {
          margin-bottom: 24px;
        }

        .stat-card {
          padding: 16px;
          border-radius: 12px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-light);
          transition: all 0.3s ease;
          box-shadow: 0 1px 3px var(--shadow-color);
        }

        .stat-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px var(--shadow-color);
        }

        .stat-card.stat-total {
          border-left: 3px solid var(--accent-blue);
        }

        .stat-card.stat-rising {
          border-left: 3px solid var(--color-up);
        }

        .stat-card.stat-falling {
          border-left: 3px solid var(--color-down);
        }

        .stat-card.stat-flat {
          border-left: 3px solid var(--color-neutral);
        }

        /* 表格容器 */
        .table-wrapper {
          background: var(--bg-table);
          border-radius: 12px;
          overflow: hidden;
          border: 1px solid var(--border-light);
        }

        /* 表格样式 */
        .market-table .ant-table {
          background: transparent !important;
        }

        .market-table .ant-table-thead > tr > th {
          background: var(--hover-bg) !important;
          color: var(--accent-blue) !important;
          font-weight: 600;
          text-transform: uppercase;
          font-size: 11px;
          letter-spacing: 0.5px;
          border-bottom: 1px solid var(--border-color) !important;
        }

        .market-table .ant-table-tbody > tr > td {
          background: transparent !important;
          border-bottom: 1px solid var(--border-light) !important;
        }

        .market-table .ant-table-tbody > tr:hover > td {
          background: var(--table-row-hover) !important;
        }

        .market-table .ant-pagination {
          background: transparent !important;
        }

        .market-table .ant-pagination-item {
          background: var(--bg-secondary) !important;
          border: 1px solid var(--border-color) !important;
        }

        .market-table .ant-pagination-item a {
          color: var(--text-secondary) !important;
        }

        .market-table .ant-pagination-item-active {
          background: var(--hover-bg) !important;
          border-color: var(--accent-blue) !important;
        }

        .market-table .ant-pagination-item-active a {
          color: var(--accent-blue) !important;
        }

        /* 行背景 */
        .row-rising {
          background-color: var(--table-row-up) !important;
        }

        .row-falling {
          background-color: var(--table-row-down) !important;
        }

        .row-highlighted {
          background-color: rgba(250, 219, 20, 0.15) !important;
          outline: 1px solid var(--accent-gold);
          outline-offset: -1px;
        }

        /* 价格闪烁动画 */
        @keyframes flashUp {
          0% { background-color: transparent; }
          25% { background-color: var(--table-row-up); }
          50% { background-color: var(--table-row-up); }
          100% { background-color: transparent; }
        }

        @keyframes flashDown {
          0% { background-color: transparent; }
          25% { background-color: var(--table-row-down); }
          50% { background-color: var(--table-row-down); }
          100% { background-color: transparent; }
        }

        .price-flash-up {
          animation: flashUp 0.8s ease-out;
          border-radius: 4px;
          padding: 2px 6px;
        }

        .price-flash-down {
          animation: flashDown 0.8s ease-out;
          border-radius: 4px;
          padding: 2px 6px;
        }

        /* 加载容器 */
        .loading-container {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 400px;
          background: var(--bg-table);
          border-radius: 12px;
        }

        .loading-container .ant-spin-text {
          color: var(--accent-blue);
        }

        /* 图表弹窗 */
        .chart-modal .ant-modal-content {
          background: var(--bg-card) !important;
          border: 1px solid var(--border-color);
          border-radius: 12px;
        }

        .chart-modal .ant-modal-header {
          background: transparent !important;
          border-bottom: 1px solid var(--border-light);
        }

        .chart-modal .ant-modal-title {
          color: var(--accent-gold) !important;
          font-weight: 600;
        }

        .chart-modal .ant-modal-close {
          color: var(--text-muted);
        }

        .chart-modal .ant-modal-close:hover {
          color: var(--accent-blue);
        }

        /* 响应式布局 */
        @media (max-width: 1200px) {
          .market-table {
            font-size: 12px;
          }
        }

        @media (max-width: 768px) {
          .market-realtime-container {
            padding: 16px;
          }

          .header-row {
            flex-direction: column;
            gap: 16px;
          }

          .stats-row .stat-card {
            margin-bottom: 12px;
          }

          .ant-statistic-title {
            font-size: 11px;
          }

          .ant-statistic-content {
            font-size: 16px;
          }
        }

        /* 滚动条样式 */
        .market-table::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }

        .market-table::-webkit-scrollbar-track {
          background: var(--bg-secondary);
          border-radius: 4px;
        }

        .market-table::-webkit-scrollbar-thumb {
          background: var(--border-color);
          border-radius: 4px;
        }

        .market-table::-webkit-scrollbar-thumb:hover {
          background: var(--accent-blue);
        }
      `}</style>
    </div>
  );
};

export default MarketRealtime;
