/**
 * ==============================================
 * 公共格式化工具函数
 * ==============================================
 * 统一管理数字、金额、日期等格式化逻辑
 */

/**
 * 格式化数字，保留指定小数位
 * @param num 要格式化的数字
 * @param decimals 小数位数，默认为 2
 * @returns 格式化后的字符串
 */
export const formatNumber = (num: number, decimals: number = 2): string => {
  if (num === null || num === undefined || isNaN(num)) {
    return '-';
  }
  return num.toFixed(decimals);
};

/**
 * 格式化成交量/金额（转换为万/亿单位）
 * @param volume 成交量或金额
 * @returns 格式化后的字符串
 */
export const formatVolume = (volume: number): string => {
  if (volume === null || volume === undefined || isNaN(volume)) {
    return '-';
  }

  const absVolume = Math.abs(volume);
  const sign = volume < 0 ? '-' : '';

  if (absVolume >= 100000000) {
    return `${sign}${(absVolume / 100000000).toFixed(2)}亿`;
  } else if (absVolume >= 10000) {
    return `${sign}${(absVolume / 10000).toFixed(2)}万`;
  }
  return `${sign}${absVolume.toString()}`;
};

/**
 * 格式化价格（添加涨跌颜色前缀）
 * @param change 涨跌幅
 * @returns 格式化后的价格字符串
 */
export const formatPrice = (price: number, decimals: number = 2): string => {
  return formatNumber(price, decimals);
};

/**
 * 格式化涨跌幅（添加百分号）
 * @param changePct 涨跌幅
 * @param decimals 小数位数
 * @returns 格式化后的字符串
 */
export const formatChangePercent = (changePct: number, decimals: number = 2): string => {
  const prefix = changePct > 0 ? '+' : '';
  return `${prefix}${formatNumber(changePct, decimals)}%`;
};

/**
 * 格式化涨跌额（添加正负号）
 * @param change 涨跌额
 * @param decimals 小数位数
 * @returns 格式化后的字符串
 */
export const formatChange = (change: number, decimals: number = 2): string => {
  const prefix = change > 0 ? '+' : '';
  return `${prefix}${formatNumber(change, decimals)}`;
};

/**
 * 获取涨跌颜色
 * @param change 涨跌幅/涨跌额
 * @returns CSS 变量名
 */
export const getChangeColor = (change: number): string => {
  if (change > 0) return 'var(--color-up)';
  if (change < 0) return 'var(--color-down)';
  return 'var(--color-neutral)';
};

/**
 * 格式化日期时间
 * @param date 日期对象或时间戳
 * @param format 格式类型
 * @returns 格式化后的字符串
 */
export const formatDateTime = (
  date: Date | number | string,
  format: 'full' | 'date' | 'time' | 'datetime' = 'datetime'
): string => {
  const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;

  if (isNaN(d.getTime())) {
    return '-';
  }

  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');

  switch (format) {
    case 'date':
      return `${year}-${month}-${day}`;
    case 'time':
      return `${hours}:${minutes}:${seconds}`;
    case 'full':
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    case 'datetime':
    default:
      return `${month}-${day} ${hours}:${minutes}`;
  }
};

/**
 * 格式化货币金额
 * @param amount 金额
 * @param currency 货币符号
 * @returns 格式化后的字符串
 */
export const formatCurrency = (amount: number, currency: string = '¥'): string => {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '-';
  }

  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';

  if (absAmount >= 100000000) {
    return `${sign}${currency}${(absAmount / 100000000).toFixed(2)}亿`;
  } else if (absAmount >= 10000) {
    return `${sign}${currency}${(absAmount / 10000).toFixed(2)}万`;
  }
  return `${sign}${currency}${absAmount.toFixed(2)}`;
};

/**
 * 格式化百分比
 * @param value 数值（0-1 之间）
 * @param decimals 小数位数
 * @returns 格式化后的百分比字符串
 */
export const formatPercent = (value: number, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) {
    return '-';
  }
  return `${(value * 100).toFixed(decimals)}%`;
};

export default {
  formatNumber,
  formatVolume,
  formatPrice,
  formatChangePercent,
  formatChange,
  getChangeColor,
  formatDateTime,
  formatCurrency,
  formatPercent,
};
