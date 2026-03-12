/**
 * MarketCard - 市场数据卡片组件
 * 显示单个指数/商品的价格、涨跌幅和迷你走势图
 */

import React, { memo, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import {
  LineChart,
  Line,
  ResponsiveContainer,
  YAxis,
} from 'recharts';
import { MarketItem, COLOR_CONFIG, formatPrice, formatChangePercent } from '../../data/marketPulseData';

interface MarketCardProps {
  item: MarketItem;
  onClick?: () => void;
}

// 数字闪烁动画组件
const AnimatedValue: React.FC<{
  value: number;
  formatFn: (v: number) => string;
  isUp: boolean;
}> = memo(({ value, formatFn, isUp }) => {
  const [flash, setFlash] = useState(false);
  const [prevValue, setPrevValue] = useState(value);

  useEffect(() => {
    if (Math.abs(value - prevValue) > 0.0001) {
      setFlash(true);
      const timer = setTimeout(() => setFlash(false), 300);
      setPrevValue(value);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [value, prevValue]);

  const color = isUp ? COLOR_CONFIG.up : COLOR_CONFIG.down;

  return (
    <AnimatePresence>
      <motion.span
        className="animated-value"
        style={{ color }}
        initial={flash ? { opacity: 0.5 } : false}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {formatFn(value)}
      </motion.span>
    </AnimatePresence>
  );
});

AnimatedValue.displayName = 'AnimatedValue';

const MarketCard: React.FC<MarketCardProps> = memo(({ item, onClick }) => {
  const isUp = item.changePercent >= 0;
  const changeColor = isUp ? COLOR_CONFIG.up : COLOR_CONFIG.down;
  const TrendIcon = isUp ? TrendingUp : TrendingDown;

  // 为图表准备数据
  const chartData = item.sparklineData.map((price, index) => ({
    price,
    index,
  }));

  // 计算图表Y轴范围
  const minPrice = Math.min(...item.sparklineData);
  const maxPrice = Math.max(...item.sparklineData);
  const priceRange = maxPrice - minPrice;
  const yAxisDomain = [
    minPrice - priceRange * 0.1,
    maxPrice + priceRange * 0.1,
  ];

  return (
    <motion.div
      className="market-card"
      onClick={onClick}
      whileHover={{ y: -4, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
    >
      <div className="market-card-header">
        <div className="market-card-title">
          <span className="market-card-name">{item.name}</span>
          {item.nameEn && (
            <span className="market-card-name-en">{item.nameEn}</span>
          )}
        </div>
        {item.exchange && (
          <span className="market-card-exchange">{item.exchange}</span>
        )}
      </div>

      <div className="market-card-price">
        <AnimatedValue
          value={item.price}
          formatFn={(v) => formatPrice(v, item.category)}
          isUp={isUp}
        />
        {item.unit && <span className="market-card-unit">{item.unit}</span>}
      </div>

      <div className="market-card-change" style={{ color: changeColor }}>
        <TrendIcon size={14} />
        <AnimatedValue
          value={item.change}
          formatFn={(v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}`}
          isUp={isUp}
        />
        <AnimatedValue
          value={item.changePercent}
          formatFn={formatChangePercent}
          isUp={isUp}
        />
      </div>

      <div className="market-card-chart">
        <ResponsiveContainer width="100%" height={60}>
          <LineChart data={chartData}>
            <YAxis domain={yAxisDomain} hide />
            <Line
              type="monotone"
              dataKey="price"
              stroke={changeColor}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
});

MarketCard.displayName = 'MarketCard';

export default MarketCard;
