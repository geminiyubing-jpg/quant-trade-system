/**
 * 自选股相关类型定义
 */

export interface WatchlistGroup {
  id: string;
  user_id: string;
  name: string;
  sort_order: number;
  is_default: boolean;
  item_count: number;
  created_at: string;
  updated_at: string;
}

export interface WatchlistItem {
  id: string;
  user_id: string;
  group_id: string | null;
  symbol: string;
  sort_order: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
  stock_name?: string;
  stock_market?: string;
}

export interface WatchlistItemWithQuote extends WatchlistItem {
  price?: number;
  change?: number;
  change_percent?: number;
  volume?: number;
  high?: number;
  low?: number;
  open?: number;
}

export interface WatchlistGroupListResponse {
  total: number;
  items: WatchlistGroup[];
}

export interface WatchlistItemListResponse {
  total: number;
  items: WatchlistItem[];
}

export interface WatchlistItemWithQuoteListResponse {
  total: number;
  items: WatchlistItemWithQuote[];
}

export interface WatchlistGroupCreate {
  name: string;
  sort_order?: number;
}

export interface WatchlistGroupUpdate {
  name?: string;
  sort_order?: number;
}

export interface WatchlistItemCreate {
  symbol: string;
  group_id?: string;
  notes?: string;
}

export interface WatchlistItemUpdate {
  group_id?: string | null;
  notes?: string;
  sort_order?: number;
}

export interface BatchAddItemsRequest {
  symbols: string[];
  group_id?: string;
}

export interface BatchRemoveItemsRequest {
  symbols: string[];
}

export interface BatchMoveItemsRequest {
  symbols: string[];
  group_id: string | null;
}

export interface BatchOperationResponse {
  success: boolean;
  added: number;
  removed: number;
  failed: string[];
  message: string;
}
