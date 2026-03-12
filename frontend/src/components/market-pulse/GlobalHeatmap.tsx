/**
 * GlobalHeatmap - 全球资产热力图组件
 * 展示全球主要市场的表现对比
 */

import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { MapPin } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { HeatmapItem, COLOR_CONFIG } from '../../data/marketPulseData';

interface GlobalHeatmapProps {
  data: HeatmapItem[];
}

const GlobalHeatmap: React.FC<GlobalHeatmapProps> = memo(({ data }) => {
  const { t } = useTranslation();

  // 根据涨跌幅获取颜色
  const getHeatColor = (changePercent: number): string => {
    if (changePercent > 1) return COLOR_CONFIG.up;
    if (changePercent > 0) return `${COLOR_CONFIG.up}cc`;
    if (changePercent > -1) return `${COLOR_CONFIG.down}cc`;
    return COLOR_CONFIG.down;
  };

  // 获取进度条宽度
  const getBarWidth = (changePercent: number): number => {
    const maxPercent = 3;
    return Math.min(Math.abs(changePercent) / maxPercent * 100, 100);
  };

  return (
    <motion.div
      className="global-heatmap"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="heatmap-header">
        <MapPin size={18} />
        <h3>{t('marketPulse.heatmap.title')}</h3>
      </div>

      {/* 热力图网格 */}
      <div className="heatmap-grid">
        {data.map((item, index) => (
          <motion.div
            key={item.name}
            className="heatmap-item"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
          >
            <div className="heatmap-item-header">
              <span className="heatmap-name">{item.name}</span>
              <span
                className="heatmap-change"
                style={{ color: getHeatColor(item.changePercent) }}
              >
                {item.changePercent >= 0 ? '+' : ''}
                {item.changePercent.toFixed(2)}%
              </span>
            </div>
            <div className="heatmap-bar-container">
              <motion.div
                className="heatmap-bar"
                style={{
                  backgroundColor: getHeatColor(item.changePercent),
                  width: `${getBarWidth(item.changePercent)}%`,
                }}
                initial={{ width: 0 }}
                animate={{ width: `${getBarWidth(item.changePercent)}%` }}
                transition={{ delay: index * 0.05 + 0.2, duration: 0.5 }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* 图例 */}
      <div className="heatmap-legend">
        <div className="legend-item">
          <span className="legend-color up" />
          <span>{t('marketPulse.heatmap.up')}</span>
        </div>
        <div className="legend-item">
          <span className="legend-color down" />
          <span>{t('marketPulse.heatmap.down')}</span>
        </div>
      </div>
    </motion.div>
  );
});

GlobalHeatmap.displayName = 'GlobalHeatmap';

export default GlobalHeatmap;
