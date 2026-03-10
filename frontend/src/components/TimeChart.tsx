/**
 * ==============================================
 * 分时图组件
 * ==============================================
 */

import React, { useMemo, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import { Button, Space } from 'antd';
import { ZoomInOutlined, ZoomOutOutlined, ReloadOutlined } from '@ant-design/icons';
import type { Quote } from '../types/market';

interface TimeChartProps {
  data: Quote[];
  symbol?: string;
}

interface ChartData {
  time: string;
  price: number;
  avgPrice: number;
  volume: number;
  timestamp: number;
}

const TimeChart: React.FC<TimeChartProps> = ({ data, symbol }) => {
  const { t } = useTranslation();
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  // 转换数据格式并计算均价
  const chartData: ChartData[] = useMemo(() => {
    if (data.length === 0) return [];

    // 计算累计成交额和累计成交量
    let totalAmount = 0;
    let totalVolume = 0;

    return data.map((quote) => {
      totalAmount += quote.amount * 10000; // amount 单位是万元
      totalVolume += quote.volume;

      // 均价 = 累计成交额 / 累计成交量
      const avgPrice = totalVolume > 0 ? totalAmount / totalVolume : quote.price;

      return {
        time: new Date(quote.timestamp).toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit',
        }),
        price: quote.price,
        avgPrice: avgPrice,
        volume: quote.volume,
        timestamp: new Date(quote.timestamp).getTime(),
      };
    });
  }, [data]);

  // 如果数据太少，不显示图表
  if (chartData.length < 2) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
        {t('realtime.noChartData')}
      </div>
    );
  }

  // 计算价格范围，用于 Y 轴缩放
  const prices = chartData.map((d) => d.price);
  const avgPrices = chartData.map((d) => d.avgPrice);
  const allPrices = [...prices, ...avgPrices];
  const minPrice = Math.min(...allPrices);
  const maxPrice = Math.max(...allPrices);
  const priceRange = maxPrice - minPrice;
  const yMin = minPrice - priceRange * 0.1;
  const yMax = maxPrice + priceRange * 0.1;

  // 获取昨日收盘价（用于分时图基准线）
  const prevClose = data[0]?.prev_close || data[0]?.open || chartData[0].price;

  // 获取股票名称
  const stockName = data.length > 0 ? data[0].name : symbol || '';

  // 缩放控制
  const handleZoomIn = () => {
    setZoomLevel((prev) => Math.min(prev * 1.2, 5));
  };

  const handleZoomOut = () => {
    setZoomLevel((prev) => Math.max(prev / 1.2, 0.5));
  };

  const handleReset = () => {
    setZoomLevel(1);
  };

  // 计算显示的数据范围
  const displayDataCount = Math.floor(chartData.length / zoomLevel);
  const displayData = chartData.slice(-displayDataCount);

  return (
    <div style={{ width: '100%', height: '500px' }}>
      {/* 标题和控制按钮 */}
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>
          {stockName} {t('realtime.timeChart')}
        </h3>
        <Space>
          <Button
            size="small"
            icon={<ZoomInOutlined />}
            onClick={handleZoomIn}
            title="放大"
          />
          <Button
            size="small"
            icon={<ZoomOutOutlined />}
            onClick={handleZoomOut}
            title="缩小"
          />
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={handleReset}
            title="重置"
          />
        </Space>
      </div>

      {/* 图表 */}
      <ResponsiveContainer width="100%" height="90%">
        <AreaChart
          data={displayData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="time"
            stroke="#666"
            style={{ fontSize: '12px' }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[yMin, yMax]}
            stroke="#666"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `¥${value.toFixed(2)}`}
            orientation="right"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
            formatter={(value: any, name: any) => {
              const label = name === 'price' ? t('realtime.price') : '均价';
              return [`¥${Number(value).toFixed(2)}`, label];
            }}
            labelFormatter={(label: any) => `${t('realtime.time')}: ${label}`}
          />
          <Legend />
          <ReferenceLine
            y={prevClose}
            stroke="#999"
            strokeDasharray="3 3"
            label={{ value: '昨收', position: 'insideTopRight', fill: '#999' }}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#1890ff"
            fill="url(#colorPrice)"
            strokeWidth={2}
            name="price"
          />
          <Area
            type="monotone"
            dataKey="avgPrice"
            stroke="#ff7300"
            fill="transparent"
            strokeWidth={1.5}
            strokeDasharray="5 5"
            name="avgPrice"
          />
          <Brush
            dataKey="time"
            height={30}
            stroke="#1890ff"
            startIndex={Math.max(0, displayData.length - 50)}
          />
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#1890ff" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#1890ff" stopOpacity={0} />
            </linearGradient>
          </defs>
        </AreaChart>
      </ResponsiveContainer>

      {/* 图例说明 */}
      <div style={{ marginTop: '8px', textAlign: 'center', fontSize: '12px', color: '#999' }}>
        <span style={{ marginRight: '20px' }}>
          <span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#1890ff', marginRight: '5px' }}></span>
          {t('realtime.price')}
        </span>
        <span>
          <span style={{ display: 'inline-block', width: '20px', height: '2px', backgroundColor: '#ff7300', borderStyle: 'dashed', marginRight: '5px' }}></span>
          均价
        </span>
      </div>
    </div>
  );
};

export default TimeChart;
