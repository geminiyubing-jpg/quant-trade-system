/**
 * Market Pulse - 市场动态模拟数据
 * 包含全球金融市场指数、商品、外汇等实时数据
 */

// 颜色配置：红涨绿跌（中国惯例）或 绿涨红跌（国际惯例）
export const COLOR_CONFIG = {
  mode: 'cn' as 'cn' | 'us', // 'cn' = 红涨绿跌, 'us' = 绿涨红跌
  up: '#ef4444',    // 上涨颜色
  down: '#22c55e',  // 下跌颜色
  neutral: '#6b7280', // 中性颜色
};

// 生成随机历史数据用于迷你图表
const generateSparklineData = (basePrice: number, points: number = 24): number[] => {
  const data: number[] = [];
  let currentPrice = basePrice;
  for (let i = 0; i < points; i++) {
    const change = (Math.random() - 0.5) * basePrice * 0.02;
    currentPrice = Math.max(basePrice * 0.9, Math.min(basePrice * 1.1, currentPrice + change));
    data.push(currentPrice);
  }
  return data;
};

// 市场卡片数据类型
export interface MarketItem {
  id: string;
  name: string;
  nameEn?: string;
  price: number;
  change: number;
  changePercent: number;
  sparklineData: number[];
  category: string;
  exchange?: string;
  unit?: string;
}

// 市场分类类型
export interface MarketCategory {
  id: string;
  name: string;
  items: MarketItem[];
}

// 生成初始市场数据
export const generateInitialData = (): MarketCategory[] => {
  const categories: MarketCategory[] = [
    {
      id: 'watchlist',
      name: '常用指数',
      items: [
        {
          id: 'gold',
          name: '纽约黄金',
          nameEn: 'Gold',
          price: 2342.50,
          change: 12.30,
          changePercent: 0.53,
          sparklineData: generateSparklineData(2342.50),
          category: 'watchlist',
          unit: 'USD/oz',
        },
        {
          id: 'dxy',
          name: '美元指数',
          nameEn: 'DXY',
          price: 104.25,
          change: -0.15,
          changePercent: -0.14,
          sparklineData: generateSparklineData(104.25),
          category: 'watchlist',
        },
        {
          id: 'nasdaq',
          name: '纳斯达克',
          nameEn: 'NASDAQ',
          price: 16742.50,
          change: 125.80,
          changePercent: 0.76,
          sparklineData: generateSparklineData(16742.50),
          category: 'watchlist',
          exchange: 'NASDAQ',
        },
        {
          id: 'dow',
          name: '道琼斯',
          nameEn: 'Dow Jones',
          price: 39150.33,
          change: -56.74,
          changePercent: -0.14,
          sparklineData: generateSparklineData(39150.33),
          category: 'watchlist',
          exchange: 'NYSE',
        },
        {
          id: 'sp500',
          name: '标普500',
          nameEn: 'S&P 500',
          price: 5234.18,
          change: 21.45,
          changePercent: 0.41,
          sparklineData: generateSparklineData(5234.18),
          category: 'watchlist',
          exchange: 'NYSE',
        },
      ],
    },
    {
      id: 'cn-hk',
      name: 'A股/港股',
      items: [
        {
          id: 'shanghai',
          name: '上证指数',
          nameEn: 'SSE Composite',
          price: 3065.42,
          change: 23.56,
          changePercent: 0.77,
          sparklineData: generateSparklineData(3065.42),
          category: 'cn-hk',
          exchange: 'SSE',
        },
        {
          id: 'shenzhen',
          name: '深证成指',
          nameEn: 'SZSE Component',
          price: 9342.18,
          change: 87.32,
          changePercent: 0.94,
          sparklineData: generateSparklineData(9342.18),
          category: 'cn-hk',
          exchange: 'SZSE',
        },
        {
          id: 'chinext',
          name: '创业板指',
          nameEn: 'ChiNext',
          price: 1823.65,
          change: 25.43,
          changePercent: 1.41,
          sparklineData: generateSparklineData(1823.65),
          category: 'cn-hk',
          exchange: 'SZSE',
        },
        {
          id: 'hsi',
          name: '恒生指数',
          nameEn: 'HSI',
          price: 16725.80,
          change: -125.45,
          changePercent: -0.74,
          sparklineData: generateSparklineData(16725.80),
          category: 'cn-hk',
          exchange: 'HKEX',
        },
        {
          id: 'hstech',
          name: '恒生科技',
          nameEn: 'Hang Seng Tech',
          price: 3542.18,
          change: 45.67,
          changePercent: 1.31,
          sparklineData: generateSparklineData(3542.18),
          category: 'cn-hk',
          exchange: 'HKEX',
        },
      ],
    },
    {
      id: 'forex-commodities',
      name: '外汇/商品',
      items: [
        {
          id: 'usdcny',
          name: '美元/人民币',
          nameEn: 'USD/CNY',
          price: 7.2456,
          change: 0.0123,
          changePercent: 0.17,
          sparklineData: generateSparklineData(7.2456),
          category: 'forex-commodities',
        },
        {
          id: 'usdjpy',
          name: '美元/日元',
          nameEn: 'USD/JPY',
          price: 149.85,
          change: -0.45,
          changePercent: -0.30,
          sparklineData: generateSparklineData(149.85),
          category: 'forex-commodities',
        },
        {
          id: 'eurusd',
          name: '欧元/美元',
          nameEn: 'EUR/USD',
          price: 1.0845,
          change: 0.0023,
          changePercent: 0.21,
          sparklineData: generateSparklineData(1.0845),
          category: 'forex-commodities',
        },
        {
          id: 'gbpusd',
          name: '英镑/美元',
          nameEn: 'GBP/USD',
          price: 1.2634,
          change: 0.0045,
          changePercent: 0.36,
          sparklineData: generateSparklineData(1.2634),
          category: 'forex-commodities',
        },
        {
          id: 'oil',
          name: '纽约原油',
          nameEn: 'WTI Crude',
          price: 78.45,
          change: 1.23,
          changePercent: 1.59,
          sparklineData: generateSparklineData(78.45),
          category: 'forex-commodities',
          unit: 'USD/bbl',
        },
        {
          id: 'brent',
          name: '布伦特原油',
          nameEn: 'Brent Crude',
          price: 82.56,
          change: 1.12,
          changePercent: 1.37,
          sparklineData: generateSparklineData(82.56),
          category: 'forex-commodities',
          unit: 'USD/bbl',
        },
        {
          id: 'silver',
          name: '白银',
          nameEn: 'Silver',
          price: 27.85,
          change: -0.32,
          changePercent: -1.14,
          sparklineData: generateSparklineData(27.85),
          category: 'forex-commodities',
          unit: 'USD/oz',
        },
        {
          id: 'copper',
          name: '铜',
          nameEn: 'Copper',
          price: 4.23,
          change: 0.05,
          changePercent: 1.19,
          sparklineData: generateSparklineData(4.23),
          category: 'forex-commodities',
          unit: 'USD/lb',
        },
        {
          id: 'naturalgas',
          name: '天然气',
          nameEn: 'Natural Gas',
          price: 1.76,
          change: -0.08,
          changePercent: -4.35,
          sparklineData: generateSparklineData(1.76),
          category: 'forex-commodities',
          unit: 'USD/MMBtu',
        },
        {
          id: 'wheat',
          name: '小麦',
          nameEn: 'Wheat',
          price: 5.82,
          change: 0.12,
          changePercent: 2.11,
          sparklineData: generateSparklineData(5.82),
          category: 'forex-commodities',
          unit: 'USD/bu',
        },
      ],
    },
    {
      id: 'ftse',
      name: '富时指数',
      items: [
        {
          id: 'ftsea50',
          name: '富时中国A50',
          nameEn: 'FTSE China A50',
          price: 12456.32,
          change: 145.67,
          changePercent: 1.18,
          sparklineData: generateSparklineData(12456.32),
          category: 'ftse',
          exchange: 'SGX',
        },
        {
          id: 'ftse100',
          name: '富时100',
          nameEn: 'FTSE 100',
          price: 8165.42,
          change: -32.18,
          changePercent: -0.39,
          sparklineData: generateSparklineData(8165.42),
          category: 'ftse',
          exchange: 'LSE',
        },
      ],
    },
    {
      id: 'msci',
      name: 'MSCI 指数',
      items: [
        {
          id: 'msciworld',
          name: 'MSCI 全球',
          nameEn: 'MSCI World',
          price: 3425.67,
          change: 18.92,
          changePercent: 0.56,
          sparklineData: generateSparklineData(3425.67),
          category: 'msci',
        },
        {
          id: 'msciemerging',
          name: 'MSCI 新兴市场',
          nameEn: 'MSCI Emerging',
          price: 1124.85,
          change: -8.45,
          changePercent: -0.75,
          sparklineData: generateSparklineData(1124.85),
          category: 'msci',
        },
        {
          id: 'mscichina',
          name: 'MSCI 中国',
          nameEn: 'MSCI China',
          price: 65.42,
          change: 1.23,
          changePercent: 1.92,
          sparklineData: generateSparklineData(65.42),
          category: 'msci',
        },
      ],
    },
    {
      id: 'global',
      name: '全球指数',
      items: [
        {
          id: 'nikkei',
          name: '日经225',
          nameEn: 'Nikkei 225',
          price: 40168.07,
          change: 567.89,
          changePercent: 1.43,
          sparklineData: generateSparklineData(40168.07),
          category: 'global',
          exchange: 'TSE',
        },
        {
          id: 'dax',
          name: '德国DAX',
          nameEn: 'DAX',
          price: 18425.67,
          change: -125.34,
          changePercent: -0.68,
          sparklineData: generateSparklineData(18425.67),
          category: 'global',
          exchange: 'XETRA',
        },
        {
          id: 'cac40',
          name: '法国CAC40',
          nameEn: 'CAC 40',
          price: 8156.42,
          change: 45.23,
          changePercent: 0.56,
          sparklineData: generateSparklineData(8156.42),
          category: 'global',
          exchange: 'Euronext',
        },
        {
          id: 'kosp200',
          name: '韩国KOSPI',
          nameEn: 'KOSPI',
          price: 2745.32,
          change: -18.56,
          changePercent: -0.67,
          sparklineData: generateSparklineData(2745.32),
          category: 'global',
          exchange: 'KRX',
        },
        {
          id: 'ftse100',
          name: '富时100',
          nameEn: 'FTSE 100',
          price: 8165.42,
          change: -32.18,
          changePercent: -0.39,
          sparklineData: generateSparklineData(8165.42),
          category: 'global',
          exchange: 'LSE',
        },
        {
          id: 'nifty50',
          name: '印度Nifty50',
          nameEn: 'Nifty 50',
          price: 22456.78,
          change: 123.45,
          changePercent: 0.55,
          sparklineData: generateSparklineData(22456.78),
          category: 'global',
          exchange: 'NSE',
        },
        {
          id: 'asx200',
          name: '澳洲ASX200',
          nameEn: 'ASX 200',
          price: 7845.32,
          change: 32.67,
          changePercent: 0.42,
          sparklineData: generateSparklineData(7845.32),
          category: 'global',
          exchange: 'ASX',
        },
        {
          id: 'tsx',
          name: '加拿大S&P/TSX',
          nameEn: 'S&P/TSX',
          price: 21845.67,
          change: 61.23,
          changePercent: 0.28,
          sparklineData: generateSparklineData(21845.67),
          category: 'global',
          exchange: 'TSX',
        },
        {
          id: 'bovespa',
          name: '巴西BOVESPA',
          nameEn: 'BOVESPA',
          price: 128456.32,
          change: 1082.45,
          changePercent: 0.85,
          sparklineData: generateSparklineData(128456.32),
          category: 'global',
          exchange: 'B3',
        },
      ],
    },
    {
      id: 'crypto',
      name: '数字货币',
      items: [
        {
          id: 'btc',
          name: '比特币',
          nameEn: 'Bitcoin',
          price: 72456.32,
          change: 1234.56,
          changePercent: 1.73,
          sparklineData: generateSparklineData(72456.32),
          category: 'crypto',
        },
        {
          id: 'eth',
          name: '以太坊',
          nameEn: 'Ethereum',
          price: 3456.78,
          change: -45.32,
          changePercent: -1.29,
          sparklineData: generateSparklineData(3456.78),
          category: 'crypto',
        },
        {
          id: 'bnb',
          name: '币安币',
          nameEn: 'BNB',
          price: 567.89,
          change: 12.34,
          changePercent: 2.22,
          sparklineData: generateSparklineData(567.89),
          category: 'crypto',
        },
        {
          id: 'sol',
          name: 'Solana',
          nameEn: 'Solana',
          price: 145.67,
          change: 8.45,
          changePercent: 6.16,
          sparklineData: generateSparklineData(145.67),
          category: 'crypto',
        },
        {
          id: 'xrp',
          name: '瑞波币',
          nameEn: 'XRP',
          price: 0.5234,
          change: -0.0123,
          changePercent: -2.30,
          sparklineData: generateSparklineData(0.5234),
          category: 'crypto',
        },
        {
          id: 'doge',
          name: '狗狗币',
          nameEn: 'Dogecoin',
          price: 0.1245,
          change: 0.0089,
          changePercent: 7.71,
          sparklineData: generateSparklineData(0.1245),
          category: 'crypto',
        },
      ],
    },
    {
      id: 'bonds',
      name: '债券收益率',
      items: [
        {
          id: 'us10y',
          name: '美国10年期国债',
          nameEn: 'US 10Y Treasury',
          price: 4.245,
          change: 0.023,
          changePercent: 0.54,
          sparklineData: generateSparklineData(4.245),
          category: 'bonds',
          unit: '%',
        },
        {
          id: 'us2y',
          name: '美国2年期国债',
          nameEn: 'US 2Y Treasury',
          price: 4.567,
          change: -0.015,
          changePercent: -0.33,
          sparklineData: generateSparklineData(4.567),
          category: 'bonds',
          unit: '%',
        },
        {
          id: 'de10y',
          name: '德国10年期国债',
          nameEn: 'German 10Y Bund',
          price: 2.456,
          change: 0.034,
          changePercent: 1.40,
          sparklineData: generateSparklineData(2.456),
          category: 'bonds',
          unit: '%',
        },
        {
          id: 'jp10y',
          name: '日本10年期国债',
          nameEn: 'Japan 10Y JGB',
          price: 0.785,
          change: 0.012,
          changePercent: 1.55,
          sparklineData: generateSparklineData(0.785),
          category: 'bonds',
          unit: '%',
        },
        {
          id: 'cn10y',
          name: '中国10年期国债',
          nameEn: 'China 10Y Bond',
          price: 2.324,
          change: -0.008,
          changePercent: -0.34,
          sparklineData: generateSparklineData(2.324),
          category: 'bonds',
          unit: '%',
        },
      ],
    },
  ];

  return categories;
};

// 模拟实时数据更新
export const simulatePriceUpdate = (item: MarketItem): MarketItem => {
  const volatility = item.category === 'crypto' ? 0.005 : 0.001;
  const priceChange = (Math.random() - 0.5) * item.price * volatility;
  const newPrice = item.price + priceChange;
  const newChange = item.change + priceChange;
  const newChangePercent = (newChange / (item.price - item.change)) * 100;

  // 更新 sparkline 数据
  const newSparkline = [...item.sparklineData.slice(1), newPrice];

  return {
    ...item,
    price: newPrice,
    change: newChange,
    changePercent: newChangePercent,
    sparklineData: newSparkline,
  };
};

// 全球资产热力图数据
export interface HeatmapItem {
  name: string;
  value: number;
  changePercent: number;
}

export const globalHeatmapData: HeatmapItem[] = [
  { name: '日本', value: 40168, changePercent: 1.43 },
  { name: '沪深', value: 3065, changePercent: 0.77 },
  { name: '香港', value: 16726, changePercent: -0.74 },
  { name: '美国', value: 39150, changePercent: -0.14 },
  { name: '欧洲', value: 18426, changePercent: -0.68 },
  { name: '黄金', value: 2342, changePercent: 0.53 },
  { name: '原油', value: 78, changePercent: 1.59 },
  { name: '比特币', value: 72456, changePercent: 1.73 },
];

// 分类标签
export const categoryTabs = [
  { id: 'all', name: '全部', icon: 'Globe' },
  { id: 'watchlist', name: '自选', icon: 'Star' },
  { id: 'cn-hk', name: 'A股/港股', icon: 'Building2' },
  { id: 'forex-commodities', name: '外汇/商品', icon: 'Coins' },
  { id: 'global', name: '环球', icon: 'Globe2' },
  { id: 'crypto', name: '数字货币', icon: 'Bitcoin' },
  { id: 'bonds', name: '债券', icon: 'TrendingUp' },
];

// 格式化价格
export const formatPrice = (price: number, category?: string): string => {
  if (category === 'crypto' && price > 1000) {
    return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (price >= 1000) {
    return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (price >= 100) {
    return price.toFixed(2);
  }
  if (price >= 10) {
    return price.toFixed(3);
  }
  return price.toFixed(4);
};

// 格式化涨跌幅
export const formatChangePercent = (percent: number): string => {
  const sign = percent >= 0 ? '+' : '';
  return `${sign}${percent.toFixed(2)}%`;
};

// 全球金融市场地理位置数据
// 坐标格式: [经度, 纬度]
export interface GlobalMarketLocation {
  id: string;
  name: string;
  indexName: string;
  indexCode: string;
  coordinates: [number, number];
  price: number;
  changePercent: number;
  region: 'asia' | 'europe' | 'americas' | 'oceania';
  timezone: string;
  isOpen: boolean;
}

// 生成全球市场位置数据
export const generateGlobalMarketLocations = (): GlobalMarketLocation[] => {
  const now = new Date();
  const utcHour = now.getUTCHours();

  return [
    // 亚洲市场
    {
      id: 'shanghai',
      name: '上海',
      indexName: '上证指数',
      indexCode: 'SSE',
      coordinates: [121.4737, 31.2304],
      price: 3065.42,
      changePercent: 0.77,
      region: 'asia',
      timezone: 'CST (UTC+8)',
      isOpen: utcHour >= 1 && utcHour < 7, // 9:00-15:00 CST
    },
    {
      id: 'shenzhen',
      name: '深圳',
      indexName: '深证成指',
      indexCode: 'SZSE',
      coordinates: [114.0579, 22.5431],
      price: 9342.18,
      changePercent: 0.94,
      region: 'asia',
      timezone: 'CST (UTC+8)',
      isOpen: utcHour >= 1 && utcHour < 7,
    },
    {
      id: 'hongkong',
      name: '香港',
      indexName: '恒生指数',
      indexCode: 'HSI',
      coordinates: [114.1694, 22.3193],
      price: 16725.80,
      changePercent: -0.74,
      region: 'asia',
      timezone: 'HKT (UTC+8)',
      isOpen: utcHour >= 1 && utcHour < 8, // 9:30-16:00 HKT
    },
    {
      id: 'tokyo',
      name: '东京',
      indexName: '日经225',
      indexCode: 'NI225',
      coordinates: [139.6917, 35.6895],
      price: 40168.07,
      changePercent: 1.43,
      region: 'asia',
      timezone: 'JST (UTC+9)',
      isOpen: utcHour >= 0 && utcHour < 6, // 9:00-15:00 JST
    },
    {
      id: 'seoul',
      name: '首尔',
      indexName: 'KOSPI',
      indexCode: 'KS11',
      coordinates: [126.9780, 37.5665],
      price: 2745.32,
      changePercent: -0.67,
      region: 'asia',
      timezone: 'KST (UTC+9)',
      isOpen: utcHour >= 0 && utcHour < 6,
    },
    {
      id: 'singapore',
      name: '新加坡',
      indexName: '富时A50',
      indexCode: 'FTSEA50',
      coordinates: [103.8198, 1.3521],
      price: 12456.32,
      changePercent: 1.18,
      region: 'asia',
      timezone: 'SGT (UTC+8)',
      isOpen: utcHour >= 1 && utcHour < 10, // 9:00-18:00 SGT
    },
    {
      id: 'mumbai',
      name: '孟买',
      indexName: 'SENSEX',
      indexCode: 'BSESN',
      coordinates: [72.8777, 19.0760],
      price: 73542.50,
      changePercent: 0.45,
      region: 'asia',
      timezone: 'IST (UTC+5:30)',
      isOpen: utcHour >= 3.5 && utcHour < 10.5,
    },

    // 欧洲市场
    {
      id: 'london',
      name: '伦敦',
      indexName: '富时100',
      indexCode: 'FTSE',
      coordinates: [-0.1276, 51.5074],
      price: 8165.42,
      changePercent: -0.39,
      region: 'europe',
      timezone: 'GMT (UTC+0)',
      isOpen: utcHour >= 8 && utcHour < 16.5, // 8:00-16:30 GMT
    },
    {
      id: 'frankfurt',
      name: '法兰克福',
      indexName: '德国DAX',
      indexCode: 'DAX',
      coordinates: [8.6821, 50.1109],
      price: 18425.67,
      changePercent: -0.68,
      region: 'europe',
      timezone: 'CET (UTC+1)',
      isOpen: utcHour >= 7 && utcHour < 15.5,
    },
    {
      id: 'paris',
      name: '巴黎',
      indexName: 'CAC40',
      indexCode: 'CAC',
      coordinates: [2.3522, 48.8566],
      price: 8156.42,
      changePercent: 0.56,
      region: 'europe',
      timezone: 'CET (UTC+1)',
      isOpen: utcHour >= 7 && utcHour < 15.5,
    },
    {
      id: 'amsterdam',
      name: '阿姆斯特丹',
      indexName: 'AEX',
      indexCode: 'AEX',
      coordinates: [4.9041, 52.3676],
      price: 845.32,
      changePercent: 0.32,
      region: 'europe',
      timezone: 'CET (UTC+1)',
      isOpen: utcHour >= 7 && utcHour < 15.5,
    },

    // 美洲市场
    {
      id: 'newyork',
      name: '纽约',
      indexName: '道琼斯',
      indexCode: 'DJI',
      coordinates: [-74.0060, 40.7128],
      price: 39150.33,
      changePercent: -0.14,
      region: 'americas',
      timezone: 'EST (UTC-5)',
      isOpen: utcHour >= 14.5 && utcHour < 21, // 9:30-16:00 EST
    },
    {
      id: 'nasdaq',
      name: '纳斯达克',
      indexName: 'NASDAQ',
      indexCode: 'IXIC',
      coordinates: [-122.4194, 37.7749], // 实际在加州，但用纽约位置代表
      price: 16742.50,
      changePercent: 0.76,
      region: 'americas',
      timezone: 'EST (UTC-5)',
      isOpen: utcHour >= 14.5 && utcHour < 21,
    },
    {
      id: 'chicago',
      name: '芝加哥',
      indexName: 'S&P500',
      indexCode: 'SPX',
      coordinates: [-87.6298, 41.8781],
      price: 5234.18,
      changePercent: 0.41,
      region: 'americas',
      timezone: 'CST (UTC-6)',
      isOpen: utcHour >= 14.5 && utcHour < 21,
    },
    {
      id: 'toronto',
      name: '多伦多',
      indexName: 'TSX',
      indexCode: 'GSPTSE',
      coordinates: [-79.3832, 43.6532],
      price: 21845.67,
      changePercent: 0.28,
      region: 'americas',
      timezone: 'EST (UTC-5)',
      isOpen: utcHour >= 14.5 && utcHour < 21,
    },
    {
      id: 'saopaulo',
      name: '圣保罗',
      indexName: 'BOVESPA',
      indexCode: 'BVSP',
      coordinates: [-46.6333, -23.5505],
      price: 128456.32,
      changePercent: 0.85,
      region: 'americas',
      timezone: 'BRT (UTC-3)',
      isOpen: utcHour >= 13 && utcHour < 20,
    },

    // 大洋洲市场
    {
      id: 'sydney',
      name: '悉尼',
      indexName: 'ASX200',
      indexCode: 'AXJO',
      coordinates: [151.2093, -33.8688],
      price: 7845.32,
      changePercent: 0.42,
      region: 'oceania',
      timezone: 'AEST (UTC+10)',
      isOpen: utcHour >= 23 || utcHour < 6, // 10:00-16:00 AEST
    },
  ];
};

// 模拟全球市场数据更新
export const simulateGlobalMarketUpdate = (
  markets: GlobalMarketLocation[]
): GlobalMarketLocation[] => {
  return markets.map((market) => {
    // 随机微调价格
    const volatility = 0.002;
    const priceChange = (Math.random() - 0.5) * market.price * volatility;
    const newPrice = market.price + priceChange;
    const newChangePercent = market.changePercent + (Math.random() - 0.5) * 0.1;

    return {
      ...market,
      price: newPrice,
      changePercent: Math.max(-5, Math.min(5, newChangePercent)), // 限制在 ±5%
    };
  });
};
