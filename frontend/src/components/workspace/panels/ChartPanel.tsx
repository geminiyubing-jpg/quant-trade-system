/**
 * K线图表面板
 * Chart Panel - Candlestick/Line Charts
 *
 * 集成真实 K 线数据和技术指标
 * 使用 useECharts hook 安全管理 ECharts 实例
 */
import React, { useEffect, useState, useMemo, useId } from 'react';
import { Select, Spin } from 'antd';
import * as echarts from 'echarts';
import { ChartPanelConfig } from '../../../types/workspace';
import { getKLineData, KLineData } from '../../../services/marketData';
import {
  calculateBOLL,
  calculateMA,
  calculateVOLMA,
} from '../../../services/technicalIndicators';
import useECharts from '../../../hooks/useECharts';

interface ChartPanelProps {
  config?: ChartPanelConfig;
}

// 可选指标配置
const AVAILABLE_INDICATORS = [
  { value: 'ma', label: 'MA均线' },
  { value: 'boll', label: 'BOLL布林带' },
  { value: 'macd', label: 'MACD' },
  { value: 'kdj', label: 'KDJ' },
  { value: 'rsi', label: 'RSI' },
  { value: 'vol_ma', label: '成交量均线' },
];

// 生成模拟 K 线数据（API 不可用时使用）
const generateMockKLineData = (): KLineData[] => {
  const data: KLineData[] = [];
  let basePrice = 10 + Math.random() * 50;
  const now = new Date();

  for (let i = 60; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);

    const open = basePrice;
    const change = (Math.random() - 0.5) * 2;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * 0.5;
    const low = Math.min(open, close) - Math.random() * 0.5;
    const volume = Math.floor(Math.random() * 1000000) + 500000;

    data.push({
      date: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume,
      amount: volume * close,
      change_percent: (change / open) * 100,
    });

    basePrice = close;
  }

  return data;
};

const ChartPanel: React.FC<ChartPanelProps> = ({ config }) => {
  // 使用唯一 ID 确保组件实例唯一性
  const instanceId = useId();

  const [loading, setLoading] = useState(true);
  const [symbol, setSymbol] = useState(config?.symbol || '000001.SZ');
  const [chartType, setChartType] = useState(config?.chartType || 'candlestick');
  const [indicator, setIndicator] = useState<string>('ma');
  const [klineData, setKlineData] = useState<KLineData[]>([]);

  // 使用自定义 hook 管理 ECharts 实例
  const { chartRef, chart, isReady } = useECharts({ theme: 'dark' });

  // 加载 K 线数据
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const data = await getKLineData(symbol, 'daily');
        if (data && data.length > 0) {
          setKlineData(data);
        } else {
          setKlineData(generateMockKLineData());
        }
      } catch {
        setKlineData(generateMockKLineData());
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [symbol]);

  // 构建图表配置
  const chartOption = useMemo(() => {
    if (klineData.length === 0) return null;

    const dates = klineData.map((d) => d.date);
    const klineValues = klineData.map((d) => [d.open, d.close, d.low, d.high]);
    const volumes = klineData.map((d, i) => [i, d.volume, d.close >= d.open ? 1 : -1]);
    const closes = klineData.map((d) => d.close);

    // 计算技术指标
    const maData = calculateMA(closes, [5, 10, 20, 60]);
    const bollData = calculateBOLL(closes, 20, 2);
    const volMAData = calculateVOLMA(klineData.map((d) => d.volume), [5, 10]);

    // 基础配置
    const baseOption: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      animation: false,
      legend: {
        data: chartType === 'candlestick' ? ['K线', '成交量'] : ['价格', '成交量'],
        top: 0,
        textStyle: { color: '#8B949E', fontSize: 11 },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(22, 27, 34, 0.95)',
        borderColor: '#30363D',
        textStyle: { color: '#E6EDF3', fontSize: 12 },
        formatter: (params: any) => {
          const dataIndex = params[0].dataIndex;
          const item = klineData[dataIndex];
          if (!item) return '';
          const changePercent = item.change_percent || ((item.close - item.open) / item.open * 100);
          const color = item.close >= item.open ? '#FF4D4D' : '#00D26A';
          return `
            <div style="padding: 8px;">
              <div style="font-weight: bold; margin-bottom: 8px;">${item.date}</div>
              <div>开盘: ${item.open.toFixed(2)}</div>
              <div>收盘: <span style="color: ${color}">${item.close.toFixed(2)}</span></div>
              <div>最高: ${item.high.toFixed(2)}</div>
              <div>最低: ${item.low.toFixed(2)}</div>
              <div>涨跌: <span style="color: ${color}">${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%</span></div>
              <div>成交量: ${(item.volume / 10000).toFixed(0)}万</div>
            </div>
          `;
        },
      },
      axisPointer: {
        link: [{ xAxisIndex: 'all' }],
      },
      grid: [
        { left: '10%', right: '8%', height: '50%', top: '12%' },
        { left: '10%', right: '8%', top: '68%', height: '16%' },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#30363D' } },
          axisLabel: { color: '#8B949E', fontSize: 10 },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#30363D' } },
          axisLabel: { show: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
      ],
      yAxis: [
        {
          scale: true,
          axisLine: { lineStyle: { color: '#30363D' } },
          axisLabel: { color: '#8B949E', fontSize: 10 },
          splitLine: { lineStyle: { color: '#21262D' } },
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLine: { lineStyle: { color: '#30363D' } },
          axisLabel: { color: '#8B949E', fontSize: 10, formatter: (val: number) => (val / 10000).toFixed(0) + '万' },
          splitLine: { lineStyle: { color: '#21262D' } },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 50,
          end: 100,
        },
      ],
    };

    // 根据指标类型添加系列
    const series: echarts.SeriesOption[] = [];

    // K 线或折线
    if (chartType === 'candlestick') {
      series.push({
        name: 'K线',
        type: 'candlestick',
        data: klineValues,
        itemStyle: {
          color: '#FF4D4D',
          color0: '#00D26A',
          borderColor: '#FF4D4D',
          borderColor0: '#00D26A',
        },
      });
    } else {
      series.push({
        name: '价格',
        type: 'line',
        data: closes,
        smooth: true,
        lineStyle: { color: '#FF6B00', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 107, 0, 0.3)' },
            { offset: 1, color: 'rgba(255, 107, 0, 0.05)' },
          ]),
        },
      });
    }

    // 添加指标
    if (indicator === 'ma') {
      const maColors = ['#FFB6C1', '#87CEEB', '#90EE90', '#DDA0DD'];
      Object.entries(maData).forEach(([key, values], index) => {
        series.push({
          name: key,
          type: 'line',
          data: values,
          smooth: true,
          lineStyle: { width: 1, color: maColors[index % maColors.length] },
          symbol: 'none',
        });
      });
    } else if (indicator === 'boll') {
      series.push(
        { name: 'BOLL上', type: 'line', data: bollData.upper, smooth: true, lineStyle: { width: 1, color: '#FFB6C1' }, symbol: 'none' },
        { name: 'BOLL中', type: 'line', data: bollData.middle, smooth: true, lineStyle: { width: 1, color: '#FFD700' }, symbol: 'none' },
        { name: 'BOLL下', type: 'line', data: bollData.lower, smooth: true, lineStyle: { width: 1, color: '#87CEEB' }, symbol: 'none' }
      );
    }

    // 成交量
    series.push({
      name: '成交量',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: volumes.map((v: any[]) => ({
        value: v[1],
        itemStyle: { color: v[2] > 0 ? 'rgba(255, 77, 77, 0.8)' : 'rgba(0, 210, 106, 0.8)' },
      })),
    });

    // 成交量均线
    if (indicator === 'vol_ma') {
      series.push(
        { name: 'VOL_MA5', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: volMAData['VOL_MA5'], smooth: true, lineStyle: { width: 1, color: '#FFB6C1' }, symbol: 'none' },
        { name: 'VOL_MA10', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: volMAData['VOL_MA10'], smooth: true, lineStyle: { width: 1, color: '#87CEEB' }, symbol: 'none' }
      );
    }

    return { ...baseOption, series };
  }, [klineData, chartType, indicator]);

  // 更新图表配置
  useEffect(() => {
    if (!chart || !isReady || !chartOption || chart.isDisposed()) return;

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      chart.setOption(chartOption as any, true);
    } catch {
      // 忽略设置选项错误
    }
  }, [chart, chartOption, isReady]);

  return (
    <div className="chart-panel" data-instance-id={instanceId}>
      <div className="panel-toolbar">
        <Select
          value={symbol}
          onChange={setSymbol}
          size="small"
          style={{ width: 100 }}
          options={[
            { value: '000001.SZ', label: '平安银行' },
            { value: '000002.SZ', label: '万科A' },
            { value: '600519.SH', label: '贵州茅台' },
            { value: '600036.SH', label: '招商银行' },
            { value: '002594.SZ', label: '比亚迪' },
            { value: '300750.SZ', label: '宁德时代' },
          ]}
        />
        <Select
          value={chartType}
          onChange={setChartType}
          size="small"
          style={{ width: 80 }}
          options={[
            { value: 'candlestick', label: 'K线' },
            { value: 'line', label: '折线' },
          ]}
        />
        <Select
          value={indicator}
          onChange={setIndicator}
          size="small"
          style={{ width: 100 }}
          options={AVAILABLE_INDICATORS}
        />
      </div>
      {/* ECharts 容器 - 不要在此 div 内放置任何 React 子元素 */}
      <div className="chart-container-wrapper">
        {loading && (
          <div className="chart-loading">
            <Spin />
          </div>
        )}
        <div
          className="chart-container"
          ref={chartRef}
          style={{ width: '100%', height: '100%', display: loading ? 'none' : 'block' }}
        />
      </div>
    </div>
  );
};

export default ChartPanel;
