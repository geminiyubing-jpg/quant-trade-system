/**
 * 数据导出服务
 * 支持 CSV 和 Excel 格式导出
 */

import * as XLSX from 'xlsx';
import { message } from 'antd';

// ==============================================
// 类型定义
// ==============================================

export interface ExportOptions {
  filename?: string;
  sheetName?: string;
  includeHeaders?: boolean;
  dateFormat?: string;
}

export interface MarketDataExport {
  symbol: string;
  name?: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  timestamp?: string;
}

// ==============================================
// 工具函数
// ==============================================

/**
 * 转义 CSV 字段值
 */
const escapeCSVField = (value: unknown): string => {
  if (value === null || value === undefined) {
    return '';
  }
  const str = String(value);
  // 如果包含逗号、引号或换行符，需要用引号包裹
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
};

/**
 * 将对象数组转换为 CSV 字符串
 */
const objectsToCSV = <T extends Record<string, unknown>>(
  data: T[],
  includeHeaders: boolean = true
): string => {
  if (!data || data.length === 0) {
    return '';
  }

  const keys = Object.keys(data[0]);
  const lines: string[] = [];

  // 添加表头
  if (includeHeaders) {
    lines.push(keys.map(escapeCSVField).join(','));
  }

  // 添加数据行
  data.forEach((item) => {
    const values = keys.map((key) => escapeCSVField(item[key]));
    lines.push(values.join(','));
  });

  return lines.join('\n');
};

/**
 * 获取字符串显示宽度（中文字符算 2，其他算 1）
 */
const getStringWidth = (str: string): number => {
  let width = 0;
  for (const char of str) {
    width += char.charCodeAt(0) > 127 ? 2 : 1;
  }
  return width;
};

/**
 * 计算列宽
 */
const calculateColumnWidths = <T extends Record<string, unknown>>(data: T[]): number[] => {
  if (!data || data.length === 0) return [];

  const keys = Object.keys(data[0]);
  return keys.map((key) => {
    // 计算标题宽度
    let maxWidth = getStringWidth(key);

    // 计算数据最大宽度
    data.forEach((item) => {
      const value = String(item[key] ?? '');
      maxWidth = Math.max(maxWidth, getStringWidth(value));
    });

    return maxWidth;
  });
};

/**
 * 格式化成交量
 */
const formatVolume = (volume: number): string => {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(2)}亿`;
  }
  if (volume >= 10000) {
    return `${(volume / 10000).toFixed(2)}万`;
  }
  return String(volume);
};

/**
 * 下载 Blob
 */
const downloadBlob = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// ==============================================
// CSV 导出
// ==============================================

/**
 * 导出数据为 CSV 格式
 */
export const exportToCSV = <T extends Record<string, unknown>>(
  data: T[],
  options: ExportOptions = {}
): void => {
  if (!data || data.length === 0) {
    message.warning('没有数据可导出');
    return;
  }

  const {
    filename = `export_${Date.now()}`,
    includeHeaders = true,
  } = options;

  try {
    // 生成 CSV
    const csv = objectsToCSV(data, includeHeaders);

    // 添加 BOM 以支持中文
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });

    // 下载文件
    downloadBlob(blob, `${filename}.csv`);

    message.success(`已导出 ${data.length} 条数据到 CSV`);
  } catch (error) {
    console.error('CSV 导出失败:', error);
    message.error('CSV 导出失败');
  }
};

// ==============================================
// Excel 导出
// ==============================================

/**
 * 导出数据为 Excel 格式
 */
export const exportToExcel = <T extends Record<string, unknown>>(
  data: T[],
  options: ExportOptions = {}
): void => {
  if (!data || data.length === 0) {
    message.warning('没有数据可导出');
    return;
  }

  const {
    filename = `export_${Date.now()}`,
    sheetName = 'Sheet1',
    includeHeaders = true,
  } = options;

  try {
    // 创建工作簿
    const wb = XLSX.utils.book_new();

    // 创建工作表
    const ws = XLSX.utils.json_to_sheet(data, {
      header: includeHeaders ? undefined : [],
      skipHeader: !includeHeaders,
    });

    // 设置列宽
    const colWidths = calculateColumnWidths(data);
    ws['!cols'] = colWidths.map((w) => ({ wch: Math.min(w, 50) }));

    // 添加工作表到工作簿
    XLSX.utils.book_append_sheet(wb, ws, sheetName);

    // 导出文件
    XLSX.writeFile(wb, `${filename}.xlsx`);

    message.success(`已导出 ${data.length} 条数据到 Excel`);
  } catch (error) {
    console.error('Excel 导出失败:', error);
    message.error('Excel 导出失败');
  }
};

/**
 * 导出多个工作表到 Excel
 */
export const exportMultiSheetExcel = <T extends Record<string, unknown>>(
  sheets: { name: string; data: T[] }[],
  options: ExportOptions = {}
): void => {
  if (!sheets || sheets.length === 0) {
    message.warning('没有数据可导出');
    return;
  }

  const { filename = `export_${Date.now()}` } = options;

  try {
    const wb = XLSX.utils.book_new();

    sheets.forEach(({ name, data }) => {
      if (data && data.length > 0) {
        const ws = XLSX.utils.json_to_sheet(data);
        const colWidths = calculateColumnWidths(data);
        ws['!cols'] = colWidths.map((w) => ({ wch: Math.min(w, 50) }));
        XLSX.utils.book_append_sheet(wb, ws, name.substring(0, 31)); // Excel 限制 31 字符
      }
    });

    XLSX.writeFile(wb, `${filename}.xlsx`);

    const totalRows = sheets.reduce((sum, s) => sum + (s.data?.length || 0), 0);
    message.success(`已导出 ${totalRows} 条数据到 Excel`);
  } catch (error) {
    console.error('Excel 导出失败:', error);
    message.error('Excel 导出失败');
  }
};

// ==============================================
// 行情数据专用导出
// ==============================================

/**
 * 导出行情数据
 */
export const exportMarketData = (
  data: MarketDataExport[],
  format: 'csv' | 'excel' = 'excel',
  options: ExportOptions = {}
): void => {
  // 格式化数据
  const formattedData = data.map((item) => ({
    股票代码: item.symbol,
    股票名称: item.name || '-',
    最新价: item.price,
    涨跌额: item.change,
    涨跌幅: `${item.changePercent >= 0 ? '+' : ''}${item.changePercent.toFixed(2)}%`,
    成交量: formatVolume(item.volume),
    最高价: item.high,
    最低价: item.low,
    开盘价: item.open,
    时间: item.timestamp || new Date().toLocaleString('zh-CN'),
  }));

  const filename = options.filename || `market_data_${Date.now()}`;

  if (format === 'csv') {
    exportToCSV(formattedData, { ...options, filename });
  } else {
    exportToExcel(formattedData, { ...options, filename, sheetName: '行情数据' });
  }
};

/**
 * 导出选中的行情数据
 */
export const exportSelectedMarketData = (
  data: MarketDataExport[],
  selectedSymbols: string[],
  format: 'csv' | 'excel' = 'excel',
  options: ExportOptions = {}
): void => {
  const selectedData = data.filter((item) => selectedSymbols.includes(item.symbol));

  if (selectedData.length === 0) {
    message.warning('请先选择要导出的数据');
    return;
  }

  exportMarketData(selectedData, format, {
    ...options,
    filename: options.filename || `selected_stocks_${Date.now()}`,
  });
};

export default {
  exportToCSV,
  exportToExcel,
  exportMultiSheetExcel,
  exportMarketData,
  exportSelectedMarketData,
};
