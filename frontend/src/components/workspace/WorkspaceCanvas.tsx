/**
 * 工作区画布 - 面板网格布局
 * Workspace Canvas - Panel Grid Layout
 */
import React, { useCallback, useMemo, useRef, useEffect, useState } from 'react';
import GridLayout, { Layout, LayoutItem } from 'react-grid-layout';
import { verticalCompactor } from 'react-grid-layout';
import { CloseOutlined, SettingOutlined } from '@ant-design/icons';
import { PanelConfig } from '../../types/workspace';
import ChartPanel from './panels/ChartPanel';
import DataTablePanel from './panels/DataTablePanel';
import NewsPanel from './panels/NewsPanel';
import WatchlistPanel from './panels/WatchlistPanel';
import CapitalFlowPanel from './panels/CapitalFlowPanel';
import MarketHeatmapPanel from './panels/MarketHeatmapPanel';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

interface WorkspaceCanvasProps {
  panels: PanelConfig[];
  onLayoutChange: (panels: PanelConfig[]) => void;
  onRemovePanel: (panelId: string) => void;
}

const WorkspaceCanvas: React.FC<WorkspaceCanvasProps> = ({
  panels,
  onLayoutChange,
  onRemovePanel,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(1200);
  const [isReady, setIsReady] = useState(false);
  const isInitialMount = useRef(true);
  const prevPanelsLength = useRef(panels.length);
  const prevLayoutRef = useRef<Layout | null>(null);

  // 等待 DOM 准备就绪后再渲染 GridLayout
  useEffect(() => {
    const timer = requestAnimationFrame(() => {
      setIsReady(true);
    });
    return () => cancelAnimationFrame(timer);
  }, []);

  // 监听容器宽度变化
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // 将面板配置转换为 react-grid-layout 格式
  const layout = useMemo(() => {
    return panels.map(panel => ({
      i: panel.id,
      ...panel.layout,
    }));
  }, [panels]);

  // 生成稳定的 key，只在面板 ID 列表变化时改变
  const panelKey = useMemo(() => {
    return panels.map(p => p.id).join('-');
  }, [panels]);

  // 布局变化处理
  const handleLayoutChange = useCallback((newLayout: Layout) => {
    // 跳过初始挂载时的布局变化回调
    if (isInitialMount.current) {
      isInitialMount.current = false;
      prevLayoutRef.current = newLayout;
      return;
    }

    // 如果面板数量发生变化，跳过本次更新（由外部状态变化引起）
    if (newLayout.length !== prevPanelsLength.current) {
      prevPanelsLength.current = newLayout.length;
      prevLayoutRef.current = newLayout;
      return;
    }

    // 与上一次的布局比较，避免循环更新
    if (prevLayoutRef.current && newLayout.length === prevLayoutRef.current.length) {
      const layoutUnchanged = newLayout.every((item, index) => {
        const prevItem = prevLayoutRef.current![index];
        return (
          prevItem &&
          item.i === prevItem.i &&
          item.x === prevItem.x &&
          item.y === prevItem.y &&
          item.w === prevItem.w &&
          item.h === prevItem.h
        );
      });
      if (layoutUnchanged) {
        return;
      }
    }

    // 只在有实际变化时更新，避免不必要的重渲染
    const hasChanges = newLayout.some((item: LayoutItem) => {
      const panel = panels.find(p => p.id === item.i);
      if (!panel) return false;
      return (
        item.x !== panel.layout.x ||
        item.y !== panel.layout.y ||
        item.w !== panel.layout.w ||
        item.h !== panel.layout.h
      );
    });

    if (!hasChanges) {
      prevLayoutRef.current = newLayout;
      return;
    }

    prevLayoutRef.current = newLayout;

    const updatedPanels = panels.map(panel => {
      const layoutItem = newLayout.find((l: LayoutItem) => l.i === panel.id);
      if (layoutItem) {
        return {
          ...panel,
          layout: {
            x: layoutItem.x,
            y: layoutItem.y,
            w: layoutItem.w,
            h: layoutItem.h,
            minW: layoutItem.minW,
            minH: layoutItem.minH,
            maxW: layoutItem.maxW,
            maxH: layoutItem.maxH,
          },
        };
      }
      return panel;
    });
    onLayoutChange(updatedPanels);
  }, [panels, onLayoutChange]);

  // 渲染面板内容
  const renderPanelContent = useCallback((panel: PanelConfig) => {
    switch (panel.type) {
      case 'chart':
        return <ChartPanel config={panel.config as any} />;
      case 'table':
        return <DataTablePanel config={panel.config as any} />;
      case 'news':
        return <NewsPanel config={panel.config as any} />;
      case 'watchlist':
        return <WatchlistPanel config={panel.config as any} />;
      case 'capitalFlow':
        return <CapitalFlowPanel config={panel.config as any} />;
      case 'heatmap':
        return <MarketHeatmapPanel config={panel.config as any} />;
      default:
        return <div className="panel-placeholder">未知面板类型</div>;
    }
  }, []);

  // 获取面板图标
  const getPanelIcon = useCallback((type: PanelConfig['type']) => {
    const icons: Record<PanelConfig['type'], string> = {
      chart: '📊',
      table: '📋',
      news: '📰',
      watchlist: '⭐',
      capitalFlow: '💰',
      heatmap: '🗺️',
      custom: '⚙️',
    };
    return icons[type] || '📄';
  }, []);

  return (
    <div className="workspace-canvas" ref={containerRef}>
      {!isReady ? (
        <div style={{ padding: 20, color: '#8B949E' }}>加载中...</div>
      ) : (
        <GridLayout
          key={panelKey}
          className="layout"
          layout={layout}
          width={containerWidth}
          gridConfig={{
            cols: 12,
            rowHeight: 40,
            margin: [12, 12],
            containerPadding: [0, 0],
            maxRows: Infinity,
          }}
          dragConfig={{
            enabled: true,
            handle: '.panel-header',
          }}
          resizeConfig={{
            enabled: true,
          }}
          compactor={verticalCompactor}
          onLayoutChange={handleLayoutChange}
        >
          {panels.map(panel => (
            <div key={panel.id} className="workspace-panel">
              <div className="panel-header">
                <div className="panel-header-left">
                  <span className="panel-icon">{getPanelIcon(panel.type)}</span>
                  <span className="panel-title">{panel.title}</span>
                </div>
                <div className="panel-header-right">
                  <button className="panel-btn settings-btn" title="设置">
                    <SettingOutlined />
                  </button>
                  <button
                    className="panel-btn close-btn"
                    title="关闭"
                    onClick={() => onRemovePanel(panel.id)}
                  >
                    <CloseOutlined />
                  </button>
                </div>
              </div>
              <div className="panel-content">
                {renderPanelContent(panel)}
              </div>
            </div>
          ))}
        </GridLayout>
      )}
    </div>
  );
};

export default WorkspaceCanvas;
