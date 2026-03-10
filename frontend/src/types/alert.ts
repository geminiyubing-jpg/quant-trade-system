/**
 * 价格预警相关类型定义
 */

export enum AlertType {
  PRICE_ABOVE = 'PRICE_ABOVE',
  PRICE_BELOW = 'PRICE_BELOW',
  CHANGE_PCT_ABOVE = 'CHANGE_PCT_ABOVE',
  CHANGE_PCT_BELOW = 'CHANGE_PCT_BELOW',
  VOLUME_ABOVE = 'VOLUME_ABOVE',
  VOLUME_BELOW = 'VOLUME_BELOW',
}

export const AlertTypeLabels: Record<AlertType, string> = {
  [AlertType.PRICE_ABOVE]: '价格高于',
  [AlertType.PRICE_BELOW]: '价格低于',
  [AlertType.CHANGE_PCT_ABOVE]: '涨幅高于',
  [AlertType.CHANGE_PCT_BELOW]: '跌幅低于',
  [AlertType.VOLUME_ABOVE]: '成交量高于',
  [AlertType.VOLUME_BELOW]: '成交量低于',
};

export interface PriceAlert {
  id: string;
  user_id: string;
  symbol: string;
  alert_type: AlertType;
  target_value: number;
  current_price?: number;
  is_active: boolean;
  is_triggered: boolean;
  triggered_at?: string;
  notification_sent: boolean;
  created_at: string;
  updated_at: string;
  stock_name?: string;
}

export interface AlertHistory {
  id: string;
  user_id: string;
  alert_id?: string;
  symbol: string;
  alert_type: AlertType;
  target_value: number;
  actual_value: number;
  triggered_at: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  stock_name?: string;
}

export interface PriceAlertListResponse {
  total: number;
  items: PriceAlert[];
}

export interface AlertHistoryListResponse {
  total: number;
  items: AlertHistory[];
}

export interface PriceAlertCreate {
  symbol: string;
  alert_type: AlertType;
  target_value: number;
}

export interface PriceAlertUpdate {
  target_value?: number;
  is_active?: boolean;
}

export interface AlertSettings {
  sound_enabled: boolean;
  browser_notification: boolean;
  email_notification: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
}

export interface AlertSettingsUpdate {
  sound_enabled?: boolean;
  browser_notification?: boolean;
  email_notification?: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
}

export interface AlertTriggeredMessage {
  alert_id: string;
  symbol: string;
  alert_type: AlertType;
  target_value: number;
  actual_value: number;
  triggered_at: string;
  stock_name?: string;
  message: string;
}

export interface UnreadCountResponse {
  count: number;
}
