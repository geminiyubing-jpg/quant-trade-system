/**
 * 市场热力图面板
 * Market Heatmap Panel
 *
 * 集成真实热力图 API
 * 使用 useECharts hook 安全管理 ECharts 实例
 */
import React, { useEffect, useState, useMemo, useId } from 'react';
import { Select, Spin } from 'antd';
import * as echarts from 'echarts';
import { HeatmapConfig } from '../../../types/workspace';
import { fetchHeatmapData, fetchSectorHeatmap, HeatmapItem, SectorHeatmapItem } from '../../../services/marketPulse';
import useECharts from '../../../hooks/useECharts';

interface MarketHeatmapPanelProps {
  config?: HeatmapConfig;
}

const MarketHeatmapPanel: React.FC<MarketHeatmapPanelProps> = ({ config }) => {
  // 使用唯一 ID 确保组件实例唯一性
  const instanceId = useId();

  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState<'change' | 'volume' | 'amount'>(config?.metric || 'change');
  const [heatmapData, setHeatmapData] = useState<HeatmapItem[]>([]);
  const [sectorData, setSectorData] = useState<SectorHeatmapItem[]>([]);

  // 使用自定义 hook 管理 ECharts 实例
  const { chartRef, chart, isReady } = useECharts({ theme: 'dark' });

  // 根据涨跌幅获取颜色
  const getColorByChange = (change: number): string => {
    if (change >= 2) return '#FF4D4D';
    if (change >= 1) return '#FF6B6B';
    if (change >= 0.5) return '#FF8585';
    if (change >= 0) return '#FFB0B0';
    if (change >= -0.5) return '#80D980';
    if (change >= -1) return '#4DBD4D';
    if (change >= -2) return '#1AA51A';
    return '#008C00';
  };

  // 构建图表配置
  const chartOption = useMemo((): echarts.EChartsOption | null => {
    if (sectorData.length === 0 && heatmapData.length === 0) return null;

    // 使用板块数据或普通热力图数据
    const chartData = sectorData.length > 0 ? sectorData : heatmapData;

    // 生成树形数据
    const treeData = chartData.map((item) => ({
      name: item.name,
      value: metric === 'change' ? item.change_percent : item.amount || 0,
      change: item.change_percent,
      amount: item.amount || 0,
      itemStyle: {
        color: getColorByChange(item.change_percent),
      },
    }));

    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        formatter: (params: any) => {
          const data = params.data;
          return `
            <div style="padding: 8px;">
              <div style="font-weight: bold; margin-bottom: 8px;">${data.name}</div>
              <div>涨跌幅: <span style="color: ${data.change >= 0 ? '#FF4D4D' : '#00D26A'}">${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%</span></div>
              ${data.amount ? `<div>成交额: ${data.amount.toFixed(1)}亿</div>` : ''}
            </div>
          `;
        },
        backgroundColor: 'rgba(22, 27, 34, 0.95)',
        borderColor: '#30363D',
        textStyle: { color: '#E6EDF3' },
      },
      series: [
        {
          type: 'treemap',
          data: treeData,
          width: '100%',
          height: '100%',
          roam: false,
          nodeClick: false,
          breadcrumb: { show: false },
          label: {
            show: true,
            formatter: (params: any) => {
              const data = params.data;
              return `${data.name}\n${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%`;
            },
            fontSize: 11,
            color: '#E6EDF3',
          },
          upperLabel: { show: false },
          itemStyle: {
            borderColor: '#21262D',
            borderWidth: 2,
            gapWidth: 2,
          },
          levels: [
            {
              itemStyle: {
                borderColor: '#21262D',
                borderWidth: 2,
                gapWidth: 2,
              },
            },
          ],
        },
      ],
    };
  }, [sectorData, heatmapData, metric]);

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

  // 加载热力图数据
  useEffect(() => {
    const loadHeatmapData = async () => {
      setLoading(true);
      try {
        // 尝试获取板块热力图数据
        const sectors = await fetchSectorHeatmap();
        if (sectors && sectors.length > 0) {
          setSectorData(sectors);
        } else {
          // 回退到普通热力图数据
          const heatmap = await fetchHeatmapData();
          setHeatmapData(heatmap);
        }
      } catch {
        // 使用空数据
        setHeatmapData([]);
      } finally {
        setLoading(false);
      }
    };

    loadHeatmapData();
  }, [metric]);

  return (
    <div className="heatmap-panel" data-instance-id={instanceId}>
      <div className="panel-toolbar">
        <span className="toolbar-title">板块热力图</span>
        <Select
          value={metric}
          onChange={setMetric}
          size="small"
          style={{ width: 80 }}
          options={[
            { value: 'change', label: '涨跌幅' },
            { value: 'amount', label: '成交额' },
          ]}
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

export default MarketHeatmapPanel;
