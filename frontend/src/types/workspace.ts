/**
 * 工作区类型定义
 * Workspace Type Definitions
 */

// 面板类型枚举
export type PanelType =
  | 'chart'           // K线图/技术分析
  | 'table'           // 数据表格
  | 'news'            // 新闻资讯
  | 'watchlist'       // 自选股
  | 'capitalFlow'     // 资金流向
  | 'heatmap'         // 市场热力图
  | 'custom';         // 自定义

// 面板配置
export interface PanelConfig {
  id: string;
  type: PanelType;
  title: string;
  // react-grid-layout 尺寸
  layout: {
    x: number;
    y: number;
    w: number;
    h: number;
    minW?: number;
    minH?: number;
    maxW?: number;
    maxH?: number;
  };
  // 面板特定配置
  config?: Record<string, any>;
}

// 工作区配置
export interface WorkspaceConfig {
  id: string;
  name: string;
  description?: string;
  panels: PanelConfig[];
  isPreset?: boolean;       // 是否为预设模板
  createdAt: string;
  updatedAt: string;
}

// AI 消息
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  // 附加数据（如股票代码、图表等）
  attachments?: {
    type: 'stock' | 'chart' | 'data';
    value: string | any;
  }[];
}

// 预设模板
export interface WorkspaceTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  panels: Omit<PanelConfig, 'id'>[];
}

// 面板数据状态
export interface PanelDataState<T = any> {
  loading: boolean;
  error: string | null;
  data: T | null;
  lastUpdated: string | null;
}

// 图表面板配置
export interface ChartPanelConfig {
  symbol: string;
  chartType: 'candlestick' | 'line' | 'bar';
  indicators: string[];
  timeframe: '1m' | '5m' | '15m' | '30m' | '1h' | '1d' | '1w';
}

// 数据表格配置
export interface TablePanelConfig {
  dataType: 'stocks' | 'funds' | 'etf';
  columns: string[];
  filters?: Record<string, any>;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// 自选股配置
export interface WatchlistPanelConfig {
  watchlistId: string;
  showPrice: boolean;
  showChange: boolean;
  showVolume: boolean;
}

// 新闻配置
export interface NewsPanelConfig {
  sources: string[];
  keywords?: string[];
  maxItems: number;
}

// 资金流向配置
export interface CapitalFlowConfig {
  market: 'sh' | 'sz' | 'all';
  timeframe: '1d' | '5d' | '20d';
  topN: number;
}

// 市场热力图配置
export interface HeatmapConfig {
  market: 'a-share' | 'hk' | 'us';
  metric: 'change' | 'volume' | 'amount';
  groupBy: 'sector' | 'industry' | 'none';
}
