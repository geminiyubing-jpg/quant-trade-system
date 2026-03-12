/**
 * GlobalMarketMap - 全球金融市场地图组件（精简版）
 * 在世界地图上显示主要金融市场的实时股指
 */

import React, { memo, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from 'react-simple-maps';
import { COLOR_CONFIG, GlobalMarketLocation } from '../../data/marketPulseData';

// 世界地图 TopoJSON 数据 URL
const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';

interface GlobalMarketMapProps {
  markets: GlobalMarketLocation[];
  onMarketClick?: (market: GlobalMarketLocation) => void;
}

// 获取涨跌颜色
const getChangeColor = (changePercent: number): string => {
  if (changePercent > 0) return COLOR_CONFIG.up;
  if (changePercent < 0) return COLOR_CONFIG.down;
  return COLOR_CONFIG.neutral;
};

// 格式化涨跌幅
const formatChange = (percent: number): string => {
  const sign = percent >= 0 ? '+' : '';
  return `${sign}${percent.toFixed(2)}%`;
};

const GlobalMarketMap: React.FC<GlobalMarketMapProps> = memo(({
  markets,
  onMarketClick,
}) => {
  const [hoveredMarket, setHoveredMarket] = useState<string | null>(null);

  // 按区域分组市场并计算统计
  const marketsByRegion = useMemo(() => {
    const grouped: Record<string, GlobalMarketLocation[]> = {
      asia: [],
      europe: [],
      americas: [],
      oceania: [],
    };
    markets.forEach((market) => {
      if (grouped[market.region]) {
        grouped[market.region].push(market);
      }
    });
    return grouped;
  }, [markets]);

  return (
    <motion.div
      className="global-market-map"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* 标题栏 */}
      <div className="map-header">
        <h3>🌍 全球市场</h3>
        <div className="map-legend">
          <span className="legend-item up"><span className="legend-dot" />涨</span>
          <span className="legend-item down"><span className="legend-dot" />跌</span>
        </div>
      </div>

      {/* 地图容器 - 精简版 */}
      <div className="map-container-compact">
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            scale: 110,
            center: [10, 20],
          }}
          style={{ width: '100%', height: '100%' }}
        >
          {/* 世界地图背景 */}
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="#1e293b"
                  stroke="#334155"
                  strokeWidth={0.3}
                  style={{
                    default: { outline: 'none' },
                    hover: { fill: '#263548', outline: 'none' },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>

          {/* 市场标记点 - 精简版 */}
          {markets.map((market) => {
            const color = getChangeColor(market.changePercent);
            const isUp = market.changePercent >= 0;
            const isHovered = hoveredMarket === market.id;

            return (
              <g key={market.id}>
                <Marker
                  coordinates={market.coordinates}
                  onMouseEnter={() => setHoveredMarket(market.id)}
                  onMouseLeave={() => setHoveredMarket(null)}
                  onClick={() => onMarketClick?.(market)}
                >
                  {/* 脉冲动画 */}
                  <motion.circle
                    cx={0}
                    cy={0}
                    r={4}
                    fill={color}
                    fillOpacity={0.3}
                    animate={{ r: [3, 6, 3], fillOpacity: [0.4, 0.1, 0.4] }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                  />
                  {/* 市场点 */}
                  <circle
                    cx={0}
                    cy={0}
                    r={3}
                    fill={color}
                    stroke="#0f172a"
                    strokeWidth={1}
                  />
                </Marker>

                {/* 悬浮提示 */}
                <AnimatePresence>
                  {isHovered && (
                    <Marker coordinates={market.coordinates}>
                      <foreignObject
                        x={10}
                        y={-30}
                        width={120}
                        height={50}
                        style={{ overflow: 'visible' }}
                      >
                        <motion.div
                          className="market-tooltip"
                          initial={{ opacity: 0, scale: 0.8, y: 5 }}
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.8, y: 5 }}
                          transition={{ duration: 0.15 }}
                        >
                          <div className="tooltip-header">
                            <span className="tooltip-name">{market.name}</span>
                            <span className="tooltip-arrow" style={{ color }}>
                              {isUp ? '▲' : '▼'}
                            </span>
                          </div>
                          <div className="tooltip-index">{market.indexName}</div>
                          <div className="tooltip-change" style={{ color }}>
                            {formatChange(market.changePercent)}
                          </div>
                        </motion.div>
                      </foreignObject>
                    </Marker>
                  )}
                </AnimatePresence>
              </g>
            );
          })}
        </ComposableMap>
      </div>

      {/* 区域统计 - 紧凑布局 */}
      <div className="region-stats-compact">
        {Object.entries(marketsByRegion).map(([region, regionMarkets]) => {
          if (regionMarkets.length === 0) return null;

          const avgChange = regionMarkets.reduce((sum, m) => sum + m.changePercent, 0) / regionMarkets.length;
          const upCount = regionMarkets.filter((m) => m.changePercent > 0).length;

          const regionNames: Record<string, string> = {
            asia: '🌏 亚太',
            europe: '🌍 欧洲',
            americas: '🌎 美洲',
            oceania: '🌏 大洋洲',
          };

          return (
            <div key={region} className="region-stat-item">
              <span className="region-name">{regionNames[region]}</span>
              <span className="region-change" style={{ color: getChangeColor(avgChange) }}>
                {formatChange(avgChange)}
              </span>
              <span className="region-count">{upCount}/{regionMarkets.length}</span>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
});

GlobalMarketMap.displayName = 'GlobalMarketMap';

export default GlobalMarketMap;
