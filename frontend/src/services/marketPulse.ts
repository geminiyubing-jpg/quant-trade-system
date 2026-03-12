/**
 * Market Pulse 实时数据服务
 * 负责获取和更新全球市场数据
 */

import { get } from './api';
import { openbbService, EquityQuote } from './openbb';

// OpenBB 股票代码映射（用于获取美股指数数据）
const OPENBB_SYMBOL_MAP: Record<string, string> = {
  // 美股指数
  'dow': '^DJI',
  'nasdaq': '^IXIC',
  'sp500': '^GSPC',
  // 亚洲指数
  'nikkei': '^N225',
  'hsi': '^HSI',
  'hstech': '^HSCE',
  'shanghai': '000001.SS',
  'shenzhen': '399001.SZ',
  'chinext': '399006.SZ',
  'kospi': '^KS11',
  'asx': '^AXJO',
  'nifty50': '^NSEI',
  // 欧洲指数
  'dax': '^GDAXI',
  'ftse': '^FTSE',
  'cac40': '^FCHI',
  'ftsea50': 'XIN9.FGI',
  // 美洲指数
  'tsx': '^GSPTSE',
  'bovespa': '^BVSP',
  // 商品
  'gold': 'GC=F',
  'silver': 'SI=F',
  'oil': 'CL=F',
  'brent': 'BZ=F',
  'copper': 'HG=F',
  'naturalgas': 'NG=F',
  'wheat': 'ZW=F',
  // 外汇
  'usdcny': 'CNY=X',
  'usdjpy': 'JPY=X',
  'eurusd': 'EURUSD=X',
  'gbpusd': 'GBPUSD=X',
  // 债券收益率
  'us10y': '^TNX',
  'us2y': '^FVX',
  // 加密货币
  'btc': 'BTC-USD',
  'eth': 'ETH-USD',
  'bnb': 'BNB-USD',
  'sol': 'SOL-USD',
  'xrp': 'XRP-USD',
  'doge': 'DOGE-USD',
};

// 导出映射供其他组件使用
export const getOpenBBSymbol = (id: string): string | undefined => OPENBB_SYMBOL_MAP[id];

// 全球指数行情类型
export interface GlobalIndexQuote {
  id: string;
  name: string;
  name_en: string;
  price: number;
  change: number;
  change_percent: number;
  region: string;
  coordinates: [number, number];
  currency: string;
  timestamp: string;
}

// 热力图数据类型
export interface HeatmapItem {
  name: string;
  asset: string;
  change_percent: number;
  amount?: number;
}

// 板块热力图数据类型
export interface SectorHeatmapItem {
  name: string;
  change_percent: number;
  amount: number;
  stocks_count?: number;
  top_stock?: string;
  top_stock_change?: number;
}

// 生成模拟板块热力图数据
const generateMockSectorHeatmap = (): SectorHeatmapItem[] => {
  return [
    { name: '白酒', change_percent: 2.35, amount: 568.5, stocks_count: 18, top_stock: '贵州茅台', top_stock_change: 2.86 },
    { name: '新能源', change_percent: 1.92, amount: 856.3, stocks_count: 45, top_stock: '宁德时代', top_stock_change: 3.12 },
    { name: '半导体', change_percent: 1.56, amount: 425.6, stocks_count: 52, top_stock: '中芯国际', top_stock_change: 2.15 },
    { name: '医药', change_percent: 0.85, amount: 356.2, stocks_count: 78, top_stock: '恒瑞医药', top_stock_change: 1.52 },
    { name: '银行', change_percent: -0.35, amount: 289.5, stocks_count: 42, top_stock: '招商银行', top_stock_change: 0.42 },
    { name: '地产', change_percent: -1.25, amount: 198.6, stocks_count: 65, top_stock: '万科A', top_stock_change: -0.85 },
    { name: '军工', change_percent: 0.68, amount: 156.3, stocks_count: 38, top_stock: '中航沈飞', top_stock_change: 1.25 },
    { name: '有色', change_percent: -0.52, amount: 178.9, stocks_count: 35, top_stock: '紫金矿业', top_stock_change: 0.35 },
    { name: '汽车', change_percent: 1.15, amount: 325.6, stocks_count: 28, top_stock: '比亚迪', top_stock_change: 3.74 },
    { name: '计算机', change_percent: 0.92, amount: 412.5, stocks_count: 85, top_stock: '科大讯飞', top_stock_change: 1.86 },
    { name: '电力', change_percent: 0.45, amount: 145.2, stocks_count: 32, top_stock: '长江电力', top_stock_change: 0.68 },
    { name: '保险', change_percent: -0.28, amount: 98.5, stocks_count: 8, top_stock: '中国平安', top_stock_change: 2.05 },
  ];
};

// API 响应类型
interface GlobalIndicesResponse {
  indices: GlobalIndexQuote[];
  total: number;
  last_update: string;
}

interface HeatmapResponse {
  success: boolean;
  data: HeatmapItem[];
  timestamp: string;
}

/**
 * 获取全球市场指数
 */
export const fetchGlobalIndices = async (): Promise<GlobalIndexQuote[]> => {
  try {
    const response = await get<GlobalIndicesResponse>('/api/v1/market-dynamics/global-indices', false);
    return response.indices || [];
  } catch (error) {
    console.log('使用模拟市场数据');
    // 返回模拟数据作为后备
    return generateMockIndices();
  }
};

/**
 * 获取热力图数据
 */
export const fetchHeatmapData = async (): Promise<HeatmapItem[]> => {
  try {
    const response = await get<HeatmapResponse>('/api/v1/market-dynamics/heatmap', false);
    return response.data || [];
  } catch (error) {
    console.log('使用模拟热力图数据');
    // 返回模拟数据作为后备
    return generateMockHeatmap();
  }
};

/**
 * 获取板块热力图数据
 */
export const fetchSectorHeatmap = async (): Promise<SectorHeatmapItem[]> => {
  try {
    const response = await get<{ success: boolean; data: SectorHeatmapItem[] }>(
      '/api/v1/market-dynamics/sector-heatmap',
      false
    );
    return response.data || [];
  } catch (error) {
    console.log('使用模拟板块热力图数据');
    // 返回模拟数据作为后备
    return generateMockSectorHeatmap();
  }
};

/**
 * 使用 OpenBB 获取美股/国际指数实时报价
 *
 * @param symbol 股票代码（如 AAPL, ^DJI, ^GSPC）
 */
export const fetchOpenBBQuote = async (symbol: string): Promise<EquityQuote | null> => {
  try {
    const quote = await openbbService.getEquityQuote(symbol);
    return quote;
  } catch (error) {
    console.log(`OpenBB 获取 ${symbol} 报价失败:`, error);
    return null;
  }
};

/**
 * 批量获取多个股票/指数的实时报价
 *
 * @param symbols 股票代码列表
 */
export const fetchOpenBBQuotes = async (symbols: string[]): Promise<Record<string, EquityQuote>> => {
  const results: Record<string, EquityQuote> = {};

  // 并行获取所有报价
  const promises = symbols.map(async (symbol) => {
    const quote = await fetchOpenBBQuote(symbol);
    if (quote) {
      results[symbol] = quote;
    }
  });

  await Promise.all(promises);
  return results;
};

/**
 * 获取 OpenBB 服务状态
 */
export const fetchOpenBBStatus = async () => {
  try {
    const status = await openbbService.getStatus();
    return status;
  } catch (error) {
    console.log('OpenBB 服务不可用');
    return null;
  }
};

/**
 * 将 OpenBB 报价转换为 MarketItem 格式
 */
export const convertOpenBBToMarketItem = (
  id: string,
  name: string,
  nameEn: string,
  quote: EquityQuote,
  category: string
) => {
  return {
    id,
    name,
    nameEn,
    price: quote.price || 0,
    change: quote.change || 0,
    changePercent: quote.change_percent || 0,
    sparklineData: [], // OpenBB 不提供迷你图数据，由前端生成
    category,
    provider: quote.provider,
  };
};

/**
 * 生成模拟指数数据（后备）
 */
const generateMockIndices = (): GlobalIndexQuote[] => {
  const now = new Date().toISOString();

  const indices = [
    // 亚洲
    { id: 'shanghai', name: '上证指数', name_en: 'SSE Composite', price: 3065.42, change_percent: 0.77, region: 'asia', coordinates: [121.4737, 31.2304] as [number, number], currency: 'CNY' },
    { id: 'shenzhen', name: '深证成指', name_en: 'SZSE Component', price: 9342.18, change_percent: 0.94, region: 'asia', coordinates: [114.0579, 22.5431] as [number, number], currency: 'CNY' },
    { id: 'hsi', name: '恒生指数', name_en: 'Hang Seng', price: 16725.80, change_percent: -0.74, region: 'asia', coordinates: [114.1694, 22.3193] as [number, number], currency: 'HKD' },
    { id: 'nikkei', name: '日经225', name_en: 'Nikkei 225', price: 40168.07, change_percent: 1.43, region: 'asia', coordinates: [139.6917, 35.6895] as [number, number], currency: 'JPY' },
    { id: 'kospi', name: '韩国KOSPI', name_en: 'KOSPI', price: 2745.32, change_percent: -0.67, region: 'asia', coordinates: [126.9780, 37.5665] as [number, number], currency: 'KRW' },
    // 欧洲
    { id: 'ftse', name: '富时100', name_en: 'FTSE 100', price: 8165.42, change_percent: -0.39, region: 'europe', coordinates: [-0.1276, 51.5074] as [number, number], currency: 'GBP' },
    { id: 'dax', name: '德国DAX', name_en: 'DAX', price: 18425.67, change_percent: -0.68, region: 'europe', coordinates: [8.6821, 50.1109] as [number, number], currency: 'EUR' },
    { id: 'cac', name: '法国CAC40', name_en: 'CAC 40', price: 8156.42, change_percent: 0.56, region: 'europe', coordinates: [2.3522, 48.8566] as [number, number], currency: 'EUR' },
    // 美洲
    { id: 'dow', name: '道琼斯', name_en: 'Dow Jones', price: 39150.33, change_percent: -0.14, region: 'americas', coordinates: [-74.0060, 40.7128] as [number, number], currency: 'USD' },
    { id: 'nasdaq', name: '纳斯达克', name_en: 'NASDAQ', price: 16742.50, change_percent: 0.76, region: 'americas', coordinates: [-122.4194, 37.7749] as [number, number], currency: 'USD' },
    { id: 'sp500', name: '标普500', name_en: 'S&P 500', price: 5234.18, change_percent: 0.41, region: 'americas', coordinates: [-87.6298, 41.8781] as [number, number], currency: 'USD' },
    // 大洋洲
    { id: 'asx', name: '澳洲ASX200', name_en: 'ASX 200', price: 7845.32, change_percent: 0.42, region: 'oceania', coordinates: [151.2093, -33.8688] as [number, number], currency: 'AUD' },
  ];

  return indices.map((index) => ({
    ...index,
    change: index.price * index.change_percent / 100,
    timestamp: now,
  }));
};

/**
 * 生成模拟热力图数据（后备）
 */
const generateMockHeatmap = (): HeatmapItem[] => {
  return [
    { name: '日本', asset: 'nikkei', change_percent: 1.43 },
    { name: '沪深', asset: 'shanghai', change_percent: 0.77 },
    { name: '香港', asset: 'hsi', change_percent: -0.74 },
    { name: '美国', asset: 'dow', change_percent: -0.14 },
    { name: '欧洲', asset: 'dax', change_percent: -0.68 },
    { name: '黄金', asset: 'gold', change_percent: 0.53 },
    { name: '原油', asset: 'oil', change_percent: 1.59 },
    { name: '比特币', asset: 'btc', change_percent: 1.73 },
  ];
};

/**
 * 将 GlobalIndexQuote 转换为 GlobalMarketLocation
 */
export const convertToMarketLocation = (quote: GlobalIndexQuote) => ({
  id: quote.id,
  name: quote.name,
  indexName: quote.name_en,
  indexCode: quote.id.toUpperCase(),
  coordinates: quote.coordinates,
  price: quote.price,
  changePercent: quote.change_percent,
  region: quote.region as 'asia' | 'europe' | 'americas' | 'oceania',
  timezone: '',
  isOpen: false,
});
