/**
 * ==============================================
 * 价格曲线图组件
 * ==============================================
 */

import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTranslation } from 'react-i18next';
import type { Quote } from '../types/market';

interface PriceChartProps {
  data: Quote[];
  symbol?: string;
}

interface ChartData {
  time: string;
  price: number;
}

const PriceChart: React.FC<PriceChartProps> = ({ data, symbol }) => {
  const { t } = useTranslation();

  // 转换数据格式
  const chartData: ChartData[] = useMemo(() => {
    return data.map((quote) => ({
      time: new Date(quote.timestamp).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
      price: quote.price,
    }));
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
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;
  const yMin = minPrice - priceRange * 0.1;
  const yMax = maxPrice + priceRange * 0.1;

  // 获取股票名称
  const stockName = data.length > 0 ? data[0].name : symbol || '';

  return (
    <div style={{ width: '100%', height: '400px' }}>
      <h3 style={{ marginBottom: '16px', textAlign: 'center' }}>
        {stockName} {t('realtime.priceChart')}
      </h3>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="time"
            stroke="#666"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => value}
          />
          <YAxis
            domain={[yMin, yMax]}
            stroke="#666"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `¥${value.toFixed(2)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
            formatter={(value: any) => [`¥${Number(value).toFixed(2)}`, t('realtime.price')]}
            labelFormatter={(label: any) => `${t('realtime.time')}: ${label}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#1890ff"
            strokeWidth={2}
            dot={{ fill: '#1890ff', r: 4 }}
            activeDot={{ r: 6 }}
            name={t('realtime.price')}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PriceChart;
