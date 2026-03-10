/**
 * ==============================================
 * 市场数据类型定义
 * ==============================================
 */

export interface Quote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  amount: number;
  bid_price?: number;
  ask_price?: number;
  high?: number;
  low?: number;
  open?: number;
  prev_close?: number;
  timestamp: string;
  // 新增字段
  turnover_rate?: number;  // 换手率
  pe_ratio?: number;       // 市盈率
  amplitude?: number;      // 振幅
}
