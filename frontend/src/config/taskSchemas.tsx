/**
 * 任务类型配置 Schema
 *
 * 定义各 ETL 任务类型的表单配置，用于智能任务向导动态渲染表单
 */

import React from 'react';
import {
  LineChartOutlined,
  InfoCircleOutlined,
  CalculatorOutlined,
  StockOutlined,
  SettingOutlined,
} from '@ant-design/icons';

// ==============================================
// 类型定义
// ==============================================

/** 字段类型 */
export type FieldType =
  | 'stock_selector'   // 股票选择器
  | 'date_range'       // 日期范围
  | 'select'           // 下拉选择
  | 'radio'            // 单选
  | 'checkbox_group'   // 多选组
  | 'input'            // 文本输入
  | 'number';          // 数字输入

/** 字段配置 */
export interface FieldConfig {
  name: string;
  type: FieldType;
  label: string;
  placeholder?: string;
  required?: boolean;
  default?: any;
  options?: string[] | { label: string; value: string }[];
  mode?: 'single' | 'multiple';
  min?: number;
  max?: number;
  tooltip?: string;
}

/** 任务类型配置 */
export interface TaskTypeConfig {
  type: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  color: string;
  fields: FieldConfig[];
  defaultSchedule?: string;
}

// ==============================================
// 任务类型配置
// ==============================================

export const TASK_TYPE_CONFIGS: TaskTypeConfig[] = [
  {
    type: 'stock_daily',
    name: '股票日线数据',
    icon: <LineChartOutlined />,
    description: '下载股票的历史日线数据，包括开盘价、最高价、最低价、收盘价、成交量等',
    color: '#1890ff',
    fields: [
      {
        name: 'symbols',
        type: 'stock_selector',
        label: '股票代码',
        placeholder: '选择或输入股票代码',
        required: true,
        tooltip: '支持单个或批量选择股票',
      },
      {
        name: 'date_range',
        type: 'date_range',
        label: '日期范围',
        default: 'last_year',
        tooltip: '选择需要获取数据的日期范围',
      },
      {
        name: 'source',
        type: 'select',
        label: '数据源',
        options: [
          { label: '自动选择（推荐）', value: 'auto' },
          { label: 'AkShare', value: 'akshare' },
          { label: 'Tushare Pro', value: 'tushare' },
        ],
        default: 'auto',
        tooltip: 'A股推荐使用 AkShare，港股美股推荐 Yahoo Finance',
      },
    ],
    defaultSchedule: '0 18 * * 1-5', // 工作日 18:00
  },
  {
    type: 'stock_info',
    name: '股票基础信息',
    icon: <InfoCircleOutlined />,
    description: '更新股票的基础信息，包括股票名称、所属行业、市值、上市日期等',
    color: '#52c41a',
    fields: [
      {
        name: 'market',
        type: 'select',
        label: '目标市场',
        options: [
          { label: '全部市场', value: 'all' },
          { label: '沪市（上交所）', value: 'sh' },
          { label: '深市（深交所）', value: 'sz' },
          { label: '北交所', value: 'bj' },
        ],
        default: 'all',
      },
      {
        name: 'update_mode',
        type: 'radio',
        label: '更新模式',
        options: [
          { label: '增量更新（快）', value: 'incremental' },
          { label: '全量更新', value: 'full' },
        ],
        default: 'incremental',
        tooltip: '增量更新只处理新增股票，全量更新会重新获取所有数据',
      },
    ],
    defaultSchedule: '0 9 * * *', // 每日 9:00
  },
  {
    type: 'factor',
    name: '因子数据计算',
    icon: <CalculatorOutlined />,
    description: '计算技术分析因子和量化因子，包括动量、RSI、MACD、均线等',
    color: '#722ed1',
    fields: [
      {
        name: 'symbols',
        type: 'stock_selector',
        label: '股票代码',
        placeholder: '选择需要计算因子的股票',
        required: true,
      },
      {
        name: 'factors',
        type: 'checkbox_group',
        label: '因子类型',
        options: [
          { label: '动量因子 (Momentum)', value: 'momentum' },
          { label: '相对强弱指标 (RSI)', value: 'rsi' },
          { label: 'MACD 指标', value: 'macd' },
          { label: '均线系统 (MA)', value: 'ma' },
          { label: '波动率 (Volatility)', value: 'volatility' },
          { label: '成交量因子', value: 'volume' },
          { label: '布林带 (Bollinger)', value: 'bollinger' },
          { label: 'KDJ 指标', value: 'kdj' },
        ],
        required: true,
        tooltip: '选择需要计算的因子类型',
      },
      {
        name: 'date_range',
        type: 'date_range',
        label: '计算日期范围',
        default: 'last_year',
      },
    ],
  },
  {
    type: 'index',
    name: '指数数据',
    icon: <StockOutlined />,
    description: '下载市场指数的历史数据，包括上证指数、深证成指、创业板指等',
    color: '#fa8c16',
    fields: [
      {
        name: 'indices',
        type: 'select',
        label: '目标指数',
        mode: 'multiple',
        options: [
          { label: '上证指数 (000001.SH)', value: '000001.SH' },
          { label: '深证成指 (399001.SZ)', value: '399001.SZ' },
          { label: '创业板指 (399006.SZ)', value: '399006.SZ' },
          { label: '沪深300 (000300.SH)', value: '000300.SH' },
          { label: '中证500 (000905.SH)', value: '000905.SH' },
          { label: '中证1000 (000852.SH)', value: '000852.SH' },
          { label: '上证50 (000016.SH)', value: '000016.SH' },
          { label: '科创50 (000688.SH)', value: '000688.SH' },
          { label: '北证50 (899050.BJ)', value: '899050.BJ' },
        ],
        required: true,
        tooltip: '可多选需要下载的指数',
      },
      {
        name: 'date_range',
        type: 'date_range',
        label: '日期范围',
        default: 'last_year',
      },
      {
        name: 'source',
        type: 'select',
        label: '数据源',
        options: [
          { label: '自动选择（推荐）', value: 'auto' },
          { label: 'AkShare', value: 'akshare' },
        ],
        default: 'auto',
      },
    ],
    defaultSchedule: '0 18 * * 1-5',
  },
  {
    type: 'custom',
    name: '自定义任务',
    icon: <SettingOutlined />,
    description: '创建自定义数据任务，支持灵活的 JSON 配置',
    color: '#8c8c8c',
    fields: [
      {
        name: 'config',
        type: 'input',
        label: '任务配置 (JSON)',
        placeholder: '{"key": "value"}',
        required: true,
        tooltip: '输入自定义的 JSON 配置',
      },
    ],
  },
];

// ==============================================
// 快捷任务模板
// ==============================================

export interface QuickTemplate {
  key: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  taskType: string;
  config: Record<string, any>;
  schedule?: string;
}

export const QUICK_TEMPLATES: QuickTemplate[] = [
  {
    key: 'daily_sync',
    name: '每日数据同步',
    description: '每天收盘后自动同步股票日线数据',
    icon: <LineChartOutlined />,
    taskType: 'stock_daily',
    config: {
      date_range: 'today',
      source: 'auto',
    },
    schedule: '0 18 * * 1-5',
  },
  {
    key: 'full_market',
    name: '全市场日线更新',
    description: '获取全市场股票最近一个月的日线数据',
    icon: <StockOutlined />,
    taskType: 'stock_daily',
    config: {
      market: 'all',
      date_range: 'last_month',
      source: 'akshare',
    },
  },
  {
    key: 'factor_calc',
    name: '因子全量计算',
    description: '计算所有常用技术因子',
    icon: <CalculatorOutlined />,
    taskType: 'factor',
    config: {
      factors: ['momentum', 'rsi', 'macd', 'ma', 'volatility'],
      date_range: 'last_year',
    },
  },
  {
    key: 'index_sync',
    name: '主要指数同步',
    description: '同步上证、深证、创业板等主要指数数据',
    icon: <StockOutlined />,
    taskType: 'index',
    config: {
      indices: ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000905.SH'],
      date_range: 'last_year',
    },
    schedule: '0 18 * * 1-5',
  },
];

// ==============================================
// 辅助函数
// ==============================================

/** 根据类型获取任务配置 */
export function getTaskConfig(type: string): TaskTypeConfig | undefined {
  return TASK_TYPE_CONFIGS.find((config) => config.type === type);
}

/** 生成默认任务名称 */
export function generateTaskName(
  taskType: string,
  config: Record<string, any>
): string {
  const typeConfig = getTaskConfig(taskType);
  const typeName = typeConfig?.name || '任务';
  const date = new Date().toLocaleDateString('zh-CN');

  // 根据任务类型生成不同的名称
  switch (taskType) {
    case 'stock_daily': {
      const symbolCount = config.symbols?.length || 0;
      return `${typeName}_${symbolCount}只股票_${date}`;
    }
    case 'stock_info': {
      const market = config.market === 'all' ? '全市场' : config.market?.toUpperCase();
      return `${typeName}_${market}_${date}`;
    }
    case 'factor': {
      const factorCount = config.factors?.length || 0;
      return `${typeName}_${factorCount}个因子_${date}`;
    }
    case 'index': {
      const indexCount = config.indices?.length || 0;
      return `${typeName}_${indexCount}个指数_${date}`;
    }
    default:
      return `${typeName}_${date}`;
  }
}

/** 日期范围预设 */
export const DATE_RANGE_PRESETS = [
  { label: '今天', value: 'today' },
  { label: '最近一周', value: 'last_week' },
  { label: '最近一月', value: 'last_month' },
  { label: '最近三月', value: 'last_quarter' },
  { label: '最近半年', value: 'last_half_year' },
  { label: '最近一年', value: 'last_year' },
  { label: '最近三年', value: 'last_three_years' },
  { label: '全部历史', value: 'all' },
];

/** 根据预设值获取日期范围 */
export function getDateRangeFromPreset(preset: string): [string, string] {
  const today = new Date();
  const endDate = today.toISOString().split('T')[0];
  let startDate: string;

  switch (preset) {
    case 'today':
      startDate = endDate;
      break;
    case 'last_week': {
      const d = new Date(today);
      d.setDate(d.getDate() - 7);
      startDate = d.toISOString().split('T')[0];
      break;
    }
    case 'last_month': {
      const d = new Date(today);
      d.setMonth(d.getMonth() - 1);
      startDate = d.toISOString().split('T')[0];
      break;
    }
    case 'last_quarter': {
      const d = new Date(today);
      d.setMonth(d.getMonth() - 3);
      startDate = d.toISOString().split('T')[0];
      break;
    }
    case 'last_half_year': {
      const d = new Date(today);
      d.setMonth(d.getMonth() - 6);
      startDate = d.toISOString().split('T')[0];
      break;
    }
    case 'last_year': {
      const d = new Date(today);
      d.setFullYear(d.getFullYear() - 1);
      startDate = d.toISOString().split('T')[0];
      break;
    }
    case 'last_three_years': {
      const d = new Date(today);
      d.setFullYear(d.getFullYear() - 3);
      startDate = d.toISOString().split('T')[0];
      break;
    }
    case 'all': {
      startDate = '2000-01-01';
      break;
    }
    default:
      startDate = endDate;
  }

  return [startDate, endDate];
}

export default {
  TASK_TYPE_CONFIGS,
  QUICK_TEMPLATES,
  DATE_RANGE_PRESETS,
  getTaskConfig,
  generateTaskName,
  getDateRangeFromPreset,
};
