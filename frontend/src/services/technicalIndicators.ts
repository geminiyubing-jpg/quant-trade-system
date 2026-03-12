/**
 * 技术指标计算服务
 * Technical Indicators Service
 *
 * 提供完整的技术指标计算库
 * MACD, RSI, KDJ, BOLL, MA, VOL, OBV, ATR, CCI, WR 等
 */

// ==============================================
// 类型定义
// ==============================================

export interface KLineData {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  date?: string;
}

export interface IndicatorResult {
  values: number[];
  name: string;
  params: number[];
}

export interface MACDResult {
  dif: number[];
  dea: number[];
  macd: number[];
}

export interface BOLLResult {
  upper: number[];
  middle: number[];
  lower: number[];
}

export interface KDJResult {
  k: number[];
  d: number[];
  j: number[];
}

export interface IndicatorConfig {
  name: string;
  params: number[];
  color?: string;
  lineWidth?: number;
}

// ==============================================
// 基础工具函数
// ==============================================

/**
 * 计算 SMA (简单移动平均)
 */
function sma(data: number[], period: number): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN);
    } else {
      const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      result.push(sum / period);
    }
  }
  return result;
}

/**
 * 计算 EMA (指数移动平均)
 */
function ema(data: number[], period: number): number[] {
  const result: number[] = [];
  const multiplier = 2 / (period + 1);

  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      result.push(data[i]);
    } else {
      result.push((data[i] - result[i - 1]) * multiplier + result[i - 1]);
    }
  }
  return result;
}

/**
 * 计算 Highest
 */
function highest(data: number[], period: number): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN);
    } else {
      const slice = data.slice(i - period + 1, i + 1);
      result.push(Math.max(...slice.filter((v) => !isNaN(v))));
    }
  }
  return result;
}

/**
 * 计算 Lowest
 */
function lowest(data: number[], period: number): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN);
    } else {
      const slice = data.slice(i - period + 1, i + 1);
      result.push(Math.min(...slice.filter((v) => !isNaN(v))));
    }
  }
  return result;
}

/**
 * 计算 Standard Deviation
 */
function stdDev(data: number[], period: number): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN);
    } else {
      const slice = data.slice(i - period + 1, i + 1);
      const mean = slice.reduce((a, b) => a + b, 0) / period;
      const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period;
      result.push(Math.sqrt(variance));
    }
  }
  return result;
}

// ==============================================
// 技术指标计算
// ==============================================

/**
 * 计算 MA (移动平均线)
 * @param closes 收盘价数组
 * @param periods 周期数组，如 [5, 10, 20, 60]
 */
export function calculateMA(closes: number[], periods: number[] = [5, 10, 20, 60]): Record<string, number[]> {
  const result: Record<string, number[]> = {};

  periods.forEach((period) => {
    result[`MA${period}`] = sma(closes, period);
  });

  return result;
}

/**
 * 计算 EMA (指数移动平均线)
 */
export function calculateEMA(closes: number[], periods: number[] = [12, 26]): Record<string, number[]> {
  const result: Record<string, number[]> = {};

  periods.forEach((period) => {
    result[`EMA${period}`] = ema(closes, period);
  });

  return result;
}

/**
 * 计算 MACD
 * @param closes 收盘价数组
 * @param fastPeriod 快线周期，默认 12
 * @param slowPeriod 慢线周期，默认 26
 * @param signalPeriod 信号线周期，默认 9
 */
export function calculateMACD(
  closes: number[],
  fastPeriod = 12,
  slowPeriod = 26,
  signalPeriod = 9
): MACDResult {
  const fastEMA = ema(closes, fastPeriod);
  const slowEMA = ema(closes, slowPeriod);

  const dif = fastEMA.map((fast, i) => fast - slowEMA[i]);
  const dea = ema(dif, signalPeriod);
  const macd = dif.map((d, i) => (d - dea[i]) * 2);

  return { dif, dea, macd };
}

/**
 * 计算 RSI (相对强弱指标)
 * @param closes 收盘价数组
 * @param periods 周期数组，默认 [6, 12, 24]
 */
export function calculateRSI(closes: number[], periods: number[] = [6, 12, 24]): Record<string, number[]> {
  const result: Record<string, number[]> = {};
  const changes: number[] = [];

  for (let i = 1; i < closes.length; i++) {
    changes.push(closes[i] - closes[i - 1]);
  }

  periods.forEach((period) => {
    const rsiValues: number[] = [NaN];

    for (let i = 1; i < closes.length; i++) {
      if (i < period) {
        rsiValues.push(NaN);
        continue;
      }

      const slice = changes.slice(i - period, i);
      const gains = slice.filter((c) => c > 0).reduce((sum, c) => sum + c, 0);
      const losses = Math.abs(slice.filter((c) => c < 0).reduce((sum, c) => sum + c, 0));

      if (losses === 0) {
        rsiValues.push(100);
      } else {
        const rs = gains / losses;
        rsiValues.push(100 - 100 / (1 + rs));
      }
    }

    result[`RSI${period}`] = rsiValues;
  });

  return result;
}

/**
 * 计算 KDJ
 * @param klines K线数据
 * @param n K 周期，默认 9
 * @param m1 D 周期，默认 3
 * @param m2 J 周期，默认 3
 */
export function calculateKDJ(
  klines: KLineData[],
  n = 9,
  m1 = 3,
  m2 = 3
): KDJResult {
  const highs = klines.map((k) => k.high);
  const lows = klines.map((k) => k.low);
  const closes = klines.map((k) => k.close);

  const highestN = highest(highs, n);
  const lowestN = lowest(lows, n);

  const rsv = closes.map((c, i) => {
    const h = highestN[i];
    const l = lowestN[i];
    if (isNaN(h) || isNaN(l) || h === l) return 50;
    return ((c - l) / (h - l)) * 100;
  });

  const k: number[] = [50];
  const d: number[] = [50];

  for (let i = 1; i < rsv.length; i++) {
    k.push((k[i - 1] * (m1 - 1) + rsv[i]) / m1);
    d.push((d[i - 1] * (m2 - 1) + k[i]) / m2);
  }

  const j = k.map((kv, i) => 3 * kv - 2 * d[i]);

  return { k, d, j };
}

/**
 * 计算 BOLL (布林带)
 * @param closes 收盘价数组
 * @param period 周期，默认 20
 * @param stdDevMultiplier 标准差倍数，默认 2
 */
export function calculateBOLL(
  closes: number[],
  period = 20,
  stdDevMultiplier = 2
): BOLLResult {
  const middle = sma(closes, period);
  const std = stdDev(closes, period);

  const upper = middle.map((m, i) => m + std[i] * stdDevMultiplier);
  const lower = middle.map((m, i) => m - std[i] * stdDevMultiplier);

  return { upper, middle, lower };
}

/**
 * 计算 ATR (真实波幅)
 * @param klines K线数据
 * @param period 周期，默认 14
 */
export function calculateATR(klines: KLineData[], period = 14): number[] {
  const trueRanges: number[] = [klines[0].high - klines[0].low];

  for (let i = 1; i < klines.length; i++) {
    const tr = Math.max(
      klines[i].high - klines[i].low,
      Math.abs(klines[i].high - klines[i - 1].close),
      Math.abs(klines[i].low - klines[i - 1].close)
    );
    trueRanges.push(tr);
  }

  return sma(trueRanges, period);
}

/**
 * 计算 OBV (能量潮)
 * @param klines K线数据
 */
export function calculateOBV(klines: KLineData[]): number[] {
  const obv: number[] = [0];

  for (let i = 1; i < klines.length; i++) {
    const prevClose = klines[i - 1].close;
    const currClose = klines[i].close;
    const volume = klines[i].volume;

    if (currClose > prevClose) {
      obv.push(obv[i - 1] + volume);
    } else if (currClose < prevClose) {
      obv.push(obv[i - 1] - volume);
    } else {
      obv.push(obv[i - 1]);
    }
  }

  return obv;
}

/**
 * 计算 CCI (顺势指标)
 * @param klines K线数据
 * @param period 周期，默认 14
 */
export function calculateCCI(klines: KLineData[], period = 14): number[] {
  const tp = klines.map((k) => (k.high + k.low + k.close) / 3);
  const smaTP = sma(tp, period);

  const cci: number[] = [];

  for (let i = 0; i < klines.length; i++) {
    if (i < period - 1) {
      cci.push(NaN);
      continue;
    }

    const slice = tp.slice(i - period + 1, i + 1);
    const mean = smaTP[i];
    const md =
      slice.reduce((sum, val) => sum + Math.abs(val - mean), 0) / period;

    if (md === 0) {
      cci.push(0);
    } else {
      cci.push((tp[i] - mean) / (0.015 * md));
    }
  }

  return cci;
}

/**
 * 计算 WR (威廉指标)
 * @param klines K线数据
 * @param period 周期，默认 14
 */
export function calculateWR(klines: KLineData[], period = 14): number[] {
  const highs = klines.map((k) => k.high);
  const lows = klines.map((k) => k.low);
  const closes = klines.map((k) => k.close);

  const highestN = highest(highs, period);
  const lowestN = lowest(lows, period);

  return closes.map((c, i) => {
    if (isNaN(highestN[i]) || isNaN(lowestN[i])) return NaN;
    const range = highestN[i] - lowestN[i];
    if (range === 0) return -50;
    return ((highestN[i] - c) / range) * -100;
  });
}

/**
 * 计算 VOL_MA (成交量均线)
 * @param volumes 成交量数组
 * @param periods 周期数组，默认 [5, 10]
 */
export function calculateVOLMA(volumes: number[], periods: number[] = [5, 10]): Record<string, number[]> {
  const result: Record<string, number[]> = {};

  periods.forEach((period) => {
    result[`VOL_MA${period}`] = sma(volumes, period);
  });

  return result;
}

// ==============================================
// 综合指标计算
// ==============================================

export interface AllIndicators {
  ma: Record<string, number[]>;
  ema: Record<string, number[]>;
  macd: MACDResult | null;
  rsi: Record<string, number[]>;
  kdj: KDJResult | null;
  boll: BOLLResult | null;
  atr: number[];
  obv: number[];
  cci: number[];
  wr: number[];
  volMa: Record<string, number[]>;
}

/**
 * 计算所有指标
 */
export function calculateAllIndicators(klines: KLineData[]): AllIndicators {
  const closes = klines.map((k) => k.close);
  const volumes = klines.map((k) => k.volume);

  return {
    ma: calculateMA(closes, [5, 10, 20, 60, 120, 250]),
    ema: calculateEMA(closes, [12, 26]),
    macd: calculateMACD(closes),
    rsi: calculateRSI(closes),
    kdj: calculateKDJ(klines),
    boll: calculateBOLL(closes),
    atr: calculateATR(klines),
    obv: calculateOBV(klines),
    cci: calculateCCI(klines),
    wr: calculateWR(klines),
    volMa: calculateVOLMA(volumes),
  };
}

// ==============================================
// 导出服务对象
// ==============================================

export const technicalIndicatorsService = {
  calculateMA,
  calculateEMA,
  calculateMACD,
  calculateRSI,
  calculateKDJ,
  calculateBOLL,
  calculateATR,
  calculateOBV,
  calculateCCI,
  calculateWR,
  calculateVOLMA,
  calculateAllIndicators,
};

export default technicalIndicatorsService;
