/**
 * ==============================================
 * K 线图组件 (蜡烛图)
 * ==============================================
 * 支持: 日K/周K/月K 切换
 * 成交量副图
 * 技术指标: MA、EMA、MACD
 * 实时更新: 监听 Redux 实时行情数据
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import { Radio, Space, Button, Spin, message, Select, Tag } from 'antd';
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useSelector } from 'react-redux';
import type { KLineData, IndicatorData } from '../utils/technicalIndicators';
import {
  calculateAllIndicators,
  formatVolume,
  formatPrice,
} from '../utils/technicalIndicators';
import { selectQuoteBySymbol } from '../store/slices/marketDataSlice';
import dayjs from 'dayjs';

interface CandlestickChartProps {
  symbol: string;
  stockName?: string;
}

type PeriodType = 'daily' | 'weekly' | 'monthly';
type IndicatorType = 'ma' | 'ema' | 'macd' | 'kdj' | 'rsi' | 'boll' | 'none';

interface ChartData extends KLineData, IndicatorData {
  color: string;
  change: number;
  changePct: number;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({ symbol, stockName }) => {
  const { t } = useTranslation();
  const [period, setPeriod] = useState<PeriodType>('daily');
  const [indicator, setIndicator] = useState<IndicatorType>('ma');
  const [loading, setLoading] = useState(false);
  const [rawData, setRawData] = useState<KLineData[]>([]);
  const [zoomLevel, setZoomLevel] = useState(1);

  // 获取实时行情数据
  const realtimeQuote = useSelector(selectQuoteBySymbol(symbol));

  // 获取 K 线数据
  const fetchKLineData = async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:8000/api/v1/data/kline/${symbol}?period=${period}&days=120`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const result = await response.json();
      if (result.success && result.data) {
        setRawData(result.data);
      } else {
        message.warning(result.message || t('realtime.noChartData'));
      }
    } catch (error) {
      console.error('获取K线数据失败:', error);
      message.error(t('realtime.noChartData'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKLineData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, period]);

  // 实时更新最后一根 K 线
  useEffect(() => {
    if (!realtimeQuote || rawData.length === 0 || period !== 'daily') return;

    const today = dayjs().format('YYYY-MM-DD');
    const lastCandle = rawData[rawData.length - 1];

    // 检查是否是当天的 K 线
    if (lastCandle.date === today || lastCandle.date === dayjs(lastCandle.date).format('YYYY-MM-DD')) {
      const currentPrice = realtimeQuote.price;
      const high = realtimeQuote.high || Math.max(lastCandle.high, currentPrice);
      const low = realtimeQuote.low || Math.min(lastCandle.low, currentPrice);

      // 更新最后一根 K 线
      setRawData(prev => {
        const updated = [...prev];
        const last = { ...updated[updated.length - 1] };
        last.close = currentPrice;
        last.high = Math.max(last.high, high);
        last.low = Math.min(last.low, low);
        // 累加成交量（如果有的话）
        if (realtimeQuote.volume && last.volume) {
          last.volume = Math.max(last.volume, realtimeQuote.volume);
        }
        updated[updated.length - 1] = last;
        return updated;
      });
    }
  }, [realtimeQuote, period, rawData.length]);

  // 计算指标数据
  const chartData: ChartData[] = useMemo(() => {
    if (rawData.length === 0) return [];
    const dataWithIndicators = calculateAllIndicators(rawData);
    return dataWithIndicators.map((item, index) => {
      const prevClose = index > 0 ? rawData[index - 1].close : item.open;
      const change = item.close - prevClose;
      const changePct = (change / prevClose) * 100;
      return {
        ...item,
        color: item.close >= item.open ? '#f5c842' : '#ff4d4f',
        change,
        changePct,
      };
    });
  }, [rawData]);

  // 缩放后的数据
  const displayData = useMemo(() => {
    const displayCount = Math.floor(chartData.length / zoomLevel);
    return chartData.slice(-displayCount);
  }, [chartData, zoomLevel]);

  // 价格范围
  const priceDomain = useMemo(() => {
    if (displayData.length === 0) return [0, 100];
    const prices = displayData.flatMap((d) => [d.high, d.low]);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const padding = (max - min) * 0.1;
    return [Math.max(0, min - padding), max + padding];
  }, [displayData]);

  // 成交量范围
  const volumeDomain = useMemo(() => {
    if (displayData.length === 0) return [0, 1000000];
    const volumes = displayData.map((d) => d.volume);
    return [0, Math.max(...volumes) * 1.1];
  }, [displayData]);

  // MACD 范围
  const macdDomain = useMemo(() => {
    if (displayData.length === 0) return [-1, 1];
    const histograms = displayData.map((d) => d.histogram ?? 0);
    const macdValues = displayData.flatMap((d) => [d.macd ?? 0, d.signal ?? 0]);
    const allValues = [...histograms, ...macdValues];
    const maxAbs = Math.max(...allValues.map(Math.abs), 0.01);
    return [-maxAbs * 1.2, maxAbs * 1.2];
  }, [displayData]);

  // 缩放控制
  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev * 1.3, 5));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev / 1.3, 0.5));
  const handleReset = () => {
    setZoomLevel(1);
    fetchKLineData();
  };

  // 自定义 Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const data = payload[0].payload;
    return (
      <div
        style={{
          backgroundColor: 'rgba(13, 20, 24, 0.95)',
          border: '1px solid rgba(0, 212, 255, 0.3)',
          borderRadius: '8px',
          padding: '12px 16px',
          color: '#e0e0e0',
          fontSize: '12px',
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
        }}
      >
        <div style={{ marginBottom: '8px', color: '#f5c842', fontWeight: 'bold' }}>
          {data.date}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 16px' }}>
          <span style={{ color: '#a0a0a0' }}>开盘:</span>
          <span style={{ color: '#00d4ff' }}>{formatPrice(data.open)}</span>
          <span style={{ color: '#a0a0a0' }}>收盘:</span>
          <span style={{ color: data.color }}>{formatPrice(data.close)}</span>
          <span style={{ color: '#a0a0a0' }}>最高:</span>
          <span style={{ color: '#f5c842' }}>{formatPrice(data.high)}</span>
          <span style={{ color: '#a0a0a0' }}>最低:</span>
          <span style={{ color: '#ff4d4f' }}>{formatPrice(data.low)}</span>
          <span style={{ color: '#a0a0a0' }}>涨跌:</span>
          <span style={{ color: data.change >= 0 ? '#f5c842' : '#ff4d4f' }}>
            {data.change >= 0 ? '+' : ''}{formatPrice(data.change)} ({data.changePct >= 0 ? '+' : ''}{data.changePct.toFixed(2)}%)
          </span>
          <span style={{ color: '#a0a0a0' }}>成交量:</span>
          <span style={{ color: '#b0b0b0' }}>{formatVolume(data.volume)}</span>
        </div>
        {indicator === 'ma' && (
          <div style={{ marginTop: '8px', borderTop: '1px solid rgba(0, 212, 255, 0.2)', paddingTop: '8px' }}>
            <span style={{ color: '#1890ff' }}>MA5: {data.ma5?.toFixed(2) || '-'}</span>
            {' | '}
            <span style={{ color: '#ff7300' }}>MA10: {data.ma10?.toFixed(2) || '-'}</span>
            {' | '}
            <span style={{ color: '#52c41a' }}>MA20: {data.ma20?.toFixed(2) || '-'}</span>
          </div>
        )}
        {indicator === 'macd' && (
          <div style={{ marginTop: '8px', borderTop: '1px solid rgba(0, 212, 255, 0.2)', paddingTop: '8px' }}>
            <span style={{ color: '#1890ff' }}>MACD: {data.macd?.toFixed(4) || '-'}</span>
            {' | '}
            <span style={{ color: '#ff7300' }}>Signal: {data.signal?.toFixed(4) || '-'}</span>
          </div>
        )}
        {indicator === 'kdj' && (
          <div style={{ marginTop: '8px', borderTop: '1px solid rgba(0, 212, 255, 0.2)', paddingTop: '8px' }}>
            <span style={{ color: '#1890ff' }}>K: {data.k?.toFixed(2) || '-'}</span>
            {' | '}
            <span style={{ color: '#ff7300' }}>D: {data.d?.toFixed(2) || '-'}</span>
            {' | '}
            <span style={{ color: '#52c41a' }}>J: {data.j?.toFixed(2) || '-'}</span>
          </div>
        )}
        {indicator === 'rsi' && (
          <div style={{ marginTop: '8px', borderTop: '1px solid rgba(0, 212, 255, 0.2)', paddingTop: '8px' }}>
            <span style={{ color: '#1890ff' }}>RSI6: {data.rsi6?.toFixed(2) || '-'}</span>
            {' | '}
            <span style={{ color: '#ff7300' }}>RSI12: {data.rsi12?.toFixed(2) || '-'}</span>
            {' | '}
            <span style={{ color: '#52c41a' }}>RSI24: {data.rsi24?.toFixed(2) || '-'}</span>
          </div>
        )}
        {indicator === 'boll' && (
          <div style={{ marginTop: '8px', borderTop: '1px solid rgba(0, 212, 255, 0.2)', paddingTop: '8px' }}>
            <span style={{ color: '#1890ff' }}>BOLL上: {data.bollUpper?.toFixed(2) || '-'}</span>
            {' | '}
            <span style={{ color: '#f5c842' }}>BOLL中: {data.bollMiddle?.toFixed(2) || '-'}</span>
            {' | '}
            <span style={{ color: '#ff7300' }}>BOLL下: {data.bollLower?.toFixed(2) || '-'}</span>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, color: '#666' }}>{t('common.loading')}</div>
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
        {t('realtime.noChartData')}
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      {/* 控制栏 */}
      <div
        style={{
          marginBottom: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h3 style={{ margin: 0, color: '#f5c842' }}>
            {stockName || symbol} {t('realtime.klineChart')}
          </h3>
          {/* 实时价格标签 */}
          {realtimeQuote && (
            <Space size="small">
              <Tag color={realtimeQuote.change >= 0 ? 'red' : 'green'}>
                ¥{formatPrice(realtimeQuote.price)}
              </Tag>
              <span style={{
                color: realtimeQuote.change >= 0 ? '#ff4d4f' : '#52c41a',
                fontSize: '12px'
              }}>
                {realtimeQuote.change >= 0 ? '+' : ''}{formatPrice(realtimeQuote.change)}
                ({realtimeQuote.change >= 0 ? '+' : ''}{(realtimeQuote.change_pct || 0).toFixed(2)}%)
              </span>
            </Space>
          )}
          {/* 周期选择 */}
          <Radio.Group
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            buttonStyle="solid"
            size="small"
          >
            <Radio.Button value="daily">{t('realtime.daily')}</Radio.Button>
            <Radio.Button value="weekly">{t('realtime.weekly')}</Radio.Button>
            <Radio.Button value="monthly">{t('realtime.monthly')}</Radio.Button>
          </Radio.Group>
        </div>

        <Space>
          {/* 指标选择 */}
          <Select
            value={indicator}
            onChange={setIndicator}
            size="small"
            style={{ width: 100 }}
            options={[
              { value: 'ma', label: 'MA' },
              { value: 'ema', label: 'EMA' },
              { value: 'macd', label: 'MACD' },
              { value: 'kdj', label: 'KDJ' },
              { value: 'rsi', label: 'RSI' },
              { value: 'boll', label: 'BOLL' },
              { value: 'none', label: t('realtime.noIndicator') },
            ]}
          />
          {/* 缩放按钮 */}
          <Button size="small" icon={<ZoomInOutlined />} onClick={handleZoomIn} title={t('realtime.zoomIn')} />
          <Button size="small" icon={<ZoomOutOutlined />} onClick={handleZoomOut} title={t('realtime.zoomOut')} />
          <Button size="small" icon={<ReloadOutlined />} onClick={handleReset} title={t('realtime.reset')} />
        </Space>
      </div>

      {/* K线图 */}
      <div style={{ height: indicator === 'macd' ? '300px' : '400px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={displayData} margin={{ top: 10, right: 60, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 212, 255, 0.1)" />
            <XAxis
              dataKey="date"
              stroke="#666"
              style={{ fontSize: '11px' }}
              tickFormatter={(value) => value.slice(5)}
              interval="preserveStartEnd"
            />
            <YAxis
              yAxisId="price"
              domain={priceDomain}
              stroke="#666"
              style={{ fontSize: '11px' }}
              tickFormatter={(value) => formatPrice(value)}
              orientation="right"
            />
            <YAxis
              yAxisId="volume"
              domain={volumeDomain}
              orientation="left"
              hide
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '12px' }}
              formatter={(value) => <span style={{ color: '#e0e0e0' }}>{value}</span>}
            />

            {/* 成交量柱状图 */}
            <Bar
              yAxisId="volume"
              dataKey="volume"
              fill="rgba(0, 212, 255, 0.3)"
              barSize={4}
              name={t('realtime.volume')}
            />

            {/* MA 均线 */}
            {indicator === 'ma' && (
              <>
                <Line yAxisId="price" type="monotone" dataKey="ma5" stroke="#1890ff" strokeWidth={1} dot={false} name="MA5" />
                <Line yAxisId="price" type="monotone" dataKey="ma10" stroke="#ff7300" strokeWidth={1} dot={false} name="MA10" />
                <Line yAxisId="price" type="monotone" dataKey="ma20" stroke="#52c41a" strokeWidth={1} dot={false} name="MA20" />
              </>
            )}

            {/* EMA 均线 */}
            {indicator === 'ema' && (
              <>
                <Line yAxisId="price" type="monotone" dataKey="ema12" stroke="#1890ff" strokeWidth={1} dot={false} name="EMA12" />
                <Line yAxisId="price" type="monotone" dataKey="ema26" stroke="#ff7300" strokeWidth={1} dot={false} name="EMA26" />
              </>
            )}

            {/* BOLL 布林带 */}
            {indicator === 'boll' && (
              <>
                <Line yAxisId="price" type="monotone" dataKey="bollUpper" stroke="#1890ff" strokeWidth={1} dot={false} name="BOLL上轨" />
                <Line yAxisId="price" type="monotone" dataKey="bollMiddle" stroke="#f5c842" strokeWidth={1} dot={false} name="BOLL中轨" />
                <Line yAxisId="price" type="monotone" dataKey="bollLower" stroke="#ff7300" strokeWidth={1} dot={false} name="BOLL下轨" />
              </>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* MACD 图表 */}
      {indicator === 'macd' && (
        <div style={{ height: '150px', marginTop: '10px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={displayData} margin={{ top: 5, right: 60, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 212, 255, 0.1)" />
              <XAxis
                dataKey="date"
                stroke="#666"
                style={{ fontSize: '10px' }}
                tickFormatter={(value) => value.slice(5)}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={macdDomain}
                stroke="#666"
                style={{ fontSize: '10px' }}
                tickFormatter={(value) => value.toFixed(2)}
                orientation="right"
              />
              <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
              <Bar dataKey="histogram" fill="rgba(0, 212, 255, 0.5)" barSize={3} name="Histogram" />
              <Line type="monotone" dataKey="macd" stroke="#1890ff" strokeWidth={1} dot={false} name="MACD" />
              <Line type="monotone" dataKey="signal" stroke="#ff7300" strokeWidth={1} dot={false} name="Signal" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* KDJ 图表 */}
      {indicator === 'kdj' && (
        <div style={{ height: '150px', marginTop: '10px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={displayData} margin={{ top: 5, right: 60, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 212, 255, 0.1)" />
              <XAxis
                dataKey="date"
                stroke="#666"
                style={{ fontSize: '10px' }}
                tickFormatter={(value) => value.slice(5)}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, 100]}
                stroke="#666"
                style={{ fontSize: '10px' }}
                orientation="right"
              />
              <ReferenceLine y={50} stroke="#666" strokeDasharray="3 3" />
              <ReferenceLine y={80} stroke="#ff4d4f" strokeDasharray="3 3" />
              <ReferenceLine y={20} stroke="#52c41a" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="k" stroke="#1890ff" strokeWidth={1} dot={false} name="K" />
              <Line type="monotone" dataKey="d" stroke="#ff7300" strokeWidth={1} dot={false} name="D" />
              <Line type="monotone" dataKey="j" stroke="#52c41a" strokeWidth={1} dot={false} name="J" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* RSI 图表 */}
      {indicator === 'rsi' && (
        <div style={{ height: '150px', marginTop: '10px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={displayData} margin={{ top: 5, right: 60, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 212, 255, 0.1)" />
              <XAxis
                dataKey="date"
                stroke="#666"
                style={{ fontSize: '10px' }}
                tickFormatter={(value) => value.slice(5)}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, 100]}
                stroke="#666"
                style={{ fontSize: '10px' }}
                orientation="right"
              />
              <ReferenceLine y={50} stroke="#666" strokeDasharray="3 3" />
              <ReferenceLine y={70} stroke="#ff4d4f" strokeDasharray="3 3" />
              <ReferenceLine y={30} stroke="#52c41a" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="rsi6" stroke="#1890ff" strokeWidth={1} dot={false} name="RSI6" />
              <Line type="monotone" dataKey="rsi12" stroke="#ff7300" strokeWidth={1} dot={false} name="RSI12" />
              <Line type="monotone" dataKey="rsi24" stroke="#52c41a" strokeWidth={1} dot={false} name="RSI24" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* BOLL 图表 - 在主图上显示 */}
      {indicator === 'boll' && (
        <div style={{ height: '0px' }} />
      )}

      {/* 图例说明 */}
      <div style={{ marginTop: '12px', textAlign: 'center', fontSize: '11px', color: '#a0a0a0' }}>
        {indicator === 'ma' && (
          <>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#1890ff', marginRight: '5px' }}></span>MA5</span>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#ff7300', marginRight: '5px' }}></span>MA10</span>
            <span><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#52c41a', marginRight: '5px' }}></span>MA20</span>
          </>
        )}
        {indicator === 'ema' && (
          <>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#1890ff', marginRight: '5px' }}></span>EMA12</span>
            <span><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#ff7300', marginRight: '5px' }}></span>EMA26</span>
          </>
        )}
        {indicator === 'macd' && (
          <>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#1890ff', marginRight: '5px' }}></span>MACD</span>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#ff7300', marginRight: '5px' }}></span>Signal</span>
            <span><span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: 'rgba(0, 212, 255, 0.5)', marginRight: '5px' }}></span>Histogram</span>
          </>
        )}
        {indicator === 'kdj' && (
          <>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#1890ff', marginRight: '5px' }}></span>K</span>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#ff7300', marginRight: '5px' }}></span>D</span>
            <span><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#52c41a', marginRight: '5px' }}></span>J</span>
          </>
        )}
        {indicator === 'rsi' && (
          <>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#1890ff', marginRight: '5px' }}></span>RSI6</span>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#ff7300', marginRight: '5px' }}></span>RSI12</span>
            <span><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#52c41a', marginRight: '5px' }}></span>RSI24</span>
          </>
        )}
        {indicator === 'boll' && (
          <>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#1890ff', marginRight: '5px' }}></span>BOLL上轨</span>
            <span style={{ marginRight: '20px' }}><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#f5c842', marginRight: '5px' }}></span>BOLL中轨</span>
            <span><span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#ff7300', marginRight: '5px' }}></span>BOLL下轨</span>
          </>
        )}
      </div>
    </div>
  );
};

export default CandlestickChart;
