/**
 * ==============================================
 * 技术指标计算工具
 * ==============================================
 */

export interface KLineData {
  date: string;
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
}

export interface IndicatorData {
  date: string;
  ma5?: number;
  ma10?: number;
  ma20?: number;
  ma60?: number;
  ema12?: number;
  ema26?: number;
  macd?: number;
  signal?: number;
  histogram?: number;
  // KDJ 指标
  k?: number;
  d?: number;
  j?: number;
  // RSI 指标
  rsi6?: number;
  rsi12?: number;
  rsi24?: number;
  // BOLL 指标
  bollUpper?: number;
  bollMiddle?: number;
  bollLower?: number;
}

/**
 * 计算 MA (移动平均线)
 */
export function calculateMA(data: KLineData[], period: number): (number | null)[] {
  const result: (number | null)[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      result.push(sum / period);
    }
  }

  return result;
}

/**
 * 计算 EMA (指数移动平均线)
 */
export function calculateEMA(data: KLineData[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  const multiplier = 2 / (period + 1);

  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      result.push(data[0].close);
    } else {
      const prevEma = result[i - 1];
      if (prevEma !== null) {
        result.push((data[i].close - prevEma) * multiplier + prevEma);
      } else {
        result.push(data[i].close);
      }
    }
  }

  return result;
}

/**
 * 计算 MACD 指标
 */
export function calculateMACD(
  data: KLineData[],
  shortPeriod: number = 12,
  longPeriod: number = 26,
  signalPeriod: number = 9
): { macd: (number | null)[]; signal: (number | null)[]; histogram: (number | null)[] } {
  const emaShort = calculateEMA(data, shortPeriod);
  const emaLong = calculateEMA(data, longPeriod);

  // 计算 DIF (MACD 线)
  const dif: (number | null)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (emaShort[i] === null || emaLong[i] === null) {
      dif.push(null);
    } else {
      dif.push(emaShort[i]! - emaLong[i]!);
    }
  }

  // 计算信号线 (DEA)
  const signal: (number | null)[] = [];
  const multiplier = 2 / (signalPeriod + 1);

  for (let i = 0; i < data.length; i++) {
    if (dif[i] === null) {
      signal.push(null);
    } else if (i === 0 || signal[i - 1] === null) {
      signal.push(dif[i]);
    } else {
      signal.push((dif[i]! - signal[i - 1]!) * multiplier + signal[i - 1]!);
    }
  }

  // 计算柱状图
  const histogram: (number | null)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (dif[i] === null || signal[i] === null) {
      histogram.push(null);
    } else {
      histogram.push(dif[i]! - signal[i]!);
    }
  }

  return { macd: dif, signal, histogram };
}

/**
 * 计算 KDJ 指标
 * K = 100 * (C - Ln) / (Hn - Ln)
 * D = MA(K, 3)
 * J = 3 * K - 2 * D
 */
export function calculateKDJ(
  data: KLineData[],
  n: number = 9,
  m1: number = 3,
  _m2: number = 3
): { k: (number | null)[]; d: (number | null)[]; j: (number | null)[] } {
  const k: (number | null)[] = [];
  const d: (number | null)[] = [];
  const j: (number | null)[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < n - 1) {
      k.push(null);
      d.push(null);
      j.push(null);
      continue;
    }

    // 计算 n 日内的最高价和最低价
    let highestHigh = data[i].high;
    let lowestLow = data[i].low;
    for (let j = 1; j < n; j++) {
      highestHigh = Math.max(highestHigh, data[i - j].high);
      lowestLow = Math.min(lowestLow, data[i - j].low);
    }

    // 计算 RSV
    const rsv = highestHigh === lowestLow ? 50 : (data[i].close - lowestLow) / (highestHigh - lowestLow) * 100;

    // 计算 K 值（使用平滑移动平均）
    if (i === n - 1) {
      k.push(50);
    } else {
      const prevK = k[i - 1] ?? 50;
      k.push((2 / 3) * prevK + (1 / 3) * rsv);
    }

    // 计算 D 值
    if (i < n - 1 + m1 - 1) {
      d.push(null);
    } else {
      let sum = 0;
      let validCount = 0;
      for (let j = 0; j < m1; j++) {
        const kVal = k[i - j];
        if (kVal !== null) {
          sum += kVal;
          validCount++;
        }
      }
      d.push(validCount > 0 ? sum / validCount : null);
    }

    // 计算 J 值
    if (k[i] !== null && d[i] !== null) {
      j.push(3 * k[i]! - 2 * d[i]!);
    } else {
      j.push(null);
    }
  }

  return { k, d, j };
}

/**
 * 计算 RSI 指标
 * RSI = 100 - 100 / (1 + RS)
 * RS = 平均上涨幅度 / 平均下跌幅度
 */
export function calculateRSI(
  data: KLineData[],
  periods: number[] = [6, 12, 24]
): { [key: string]: (number | null)[] } {
  const result: { [key: string]: (number | null)[] } = {};

  for (const period of periods) {
    const rsi: (number | null)[] = [];
    let avgGain = 0;
    let avgLoss = 0;

    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        rsi.push(null);
        continue;
      }

      const change = data[i].close - data[i - 1].close;
      const gain = change > 0 ? change : 0;
      const loss = change < 0 ? -change : 0;

      if (i < period) {
        // 累积初始数据
        avgGain += gain;
        avgLoss += loss;
        rsi.push(null);
      } else if (i === period) {
        // 首次计算 RSI
        avgGain += gain;
        avgLoss += loss;
        avgGain /= period;
        avgLoss /= period;

        const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
        rsi.push(100 - 100 / (1 + rs));
      } else {
        // 使用平滑平均
        avgGain = (avgGain * (period - 1) + gain) / period;
        avgLoss = (avgLoss * (period - 1) + loss) / period;

        const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
        rsi.push(100 - 100 / (1 + rs));
      }
    }

    result[`rsi${period}`] = rsi;
  }

  return result;
}

/**
 * 计算 BOLL 指标（布林带）
 * 中轨 = N 日移动平均线
 * 上轨 = 中轨 + K × N 日标准差
 * 下轨 = 中轨 - K × N 日标准差
 */
export function calculateBOLL(
  data: KLineData[],
  n: number = 20,
  k: number = 2
): { upper: (number | null)[]; middle: (number | null)[]; lower: (number | null)[] } {
  const upper: (number | null)[] = [];
  const middle: (number | null)[] = [];
  const lower: (number | null)[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < n - 1) {
      upper.push(null);
      middle.push(null);
      lower.push(null);
      continue;
    }

    // 计算中轨（N 日移动平均）
    let sum = 0;
    for (let j = 0; j < n; j++) {
      sum += data[i - j].close;
    }
    const mid = sum / n;
    middle.push(mid);

    // 计算标准差
    let variance = 0;
    for (let j = 0; j < n; j++) {
      variance += Math.pow(data[i - j].close - mid, 2);
    }
    const stdDev = Math.sqrt(variance / n);

    // 计算上下轨
    upper.push(mid + k * stdDev);
    lower.push(mid - k * stdDev);
  }

  return { upper, middle, lower };
}

/**
 * 计算所有指标
 */
export function calculateAllIndicators(data: KLineData[]): (KLineData & IndicatorData)[] {
  if (data.length === 0) return [];

  const ma5 = calculateMA(data, 5);
  const ma10 = calculateMA(data, 10);
  const ma20 = calculateMA(data, 20);
  const ma60 = calculateMA(data, 60);
  const { macd, signal, histogram } = calculateMACD(data);
  const { k, d, j } = calculateKDJ(data);
  const rsi = calculateRSI(data, [6, 12, 24]);
  const { upper, middle, lower } = calculateBOLL(data);

  return data.map((item, index) => ({
    ...item,
    ma5: ma5[index] ?? undefined,
    ma10: ma10[index] ?? undefined,
    ma20: ma20[index] ?? undefined,
    ma60: ma60[index] ?? undefined,
    macd: macd[index] ?? undefined,
    signal: signal[index] ?? undefined,
    histogram: histogram[index] ?? undefined,
    k: k[index] ?? undefined,
    d: d[index] ?? undefined,
    j: j[index] ?? undefined,
    rsi6: rsi.rsi6[index] ?? undefined,
    rsi12: rsi.rsi12[index] ?? undefined,
    rsi24: rsi.rsi24[index] ?? undefined,
    bollUpper: upper[index] ?? undefined,
    bollMiddle: middle[index] ?? undefined,
    bollLower: lower[index] ?? undefined,
  }));
}

/**
 * 格式化成交量
 */
export function formatVolume(volume: number): string {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(2)}亿`;
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(2)}万`;
  }
  return volume.toString();
}

/**
 * 格式化价格
 */
export function formatPrice(price: number, decimals: number = 2): string {
  return price.toFixed(decimals);
}
