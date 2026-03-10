/**
 * 交易相关类型定义
 */

// 订单状态
export type OrderStatus = 'PENDING' | 'PARTIAL' | 'FILLED' | 'CANCELED' | 'REJECTED';

// 订单方向
export type OrderSide = 'BUY' | 'SELL';

// 执行模式
export type ExecutionMode = 'PAPER' | 'LIVE';

// 订单有效期
export type TimeInForce = 'DAY' | 'GTC' | 'IOC' | 'FOK';

// 订单基础类型
export interface Order {
  id: string;
  symbol: string;
  side: OrderSide;
  order_type: string;
  quantity: number;
  price: number;
  execution_mode: ExecutionMode;
  status: OrderStatus;
  filled_quantity: number;
  avg_price: number;
  strategy_id?: string;
  user_id: string;
  create_time: string;
  update_time?: string;
  filled_time?: string;
}

// 订单列表响应
export interface OrderListResponse {
  total: number;
  items: Order[];
}

// 创建订单请求
export interface OrderCreate {
  symbol: string;
  side: OrderSide;
  order_type?: string;
  quantity: number;
  price: number;
  execution_mode: ExecutionMode;
  strategy_id?: string;
  stop_loss_price?: number;
  take_profit_price?: number;
  max_slippage?: number;
  time_in_force?: TimeInForce;
}

// 更新订单请求
export interface OrderUpdate {
  status?: OrderStatus;
  filled_quantity?: number;
  filled_amount?: number;
  commission?: number;
}

// 持仓类型
export interface Position {
  id: string;
  user_id: string;
  strategy_id?: string;
  symbol: string;
  execution_mode: ExecutionMode;
  quantity: number;
  avg_price: number;
  current_price?: number;
  market_value?: number;
  unrealized_pnl?: number;
  cost_basis?: number;
  realized_pnl: number;
  max_quantity_limit?: number;
  created_at: string;
  updated_at: string;
}

// 持仓列表响应
export interface PositionListResponse {
  total: number;
  items: Position[];
}

// 持仓汇总
export interface PositionSummary {
  total_market_value: number;
  total_unrealized_pnl: number;
  total_realized_pnl: number;
  position_count: number;
}

// 交易模式状态
export interface TradingModeStatus {
  current_mode: ExecutionMode;
  can_switch_to_live: boolean;
  requirements: string[];
  warning_message?: string;
}

// 交易模式切换请求
export interface TradingModeSwitchRequest {
  mode: ExecutionMode;
  password?: string;
  confirm: boolean;
}

// 交易模式切换响应
export interface TradingModeSwitchResponse {
  success: boolean;
  mode: ExecutionMode;
  message: string;
  previous_mode: ExecutionMode;
}

// 实盘交易密码请求
export interface LiveTradingPasswordRequest {
  password: string;
  confirm_password: string;
}

// 实盘交易密码响应
export interface LiveTradingPasswordResponse {
  success: boolean;
  message: string;
  has_password: boolean;
}

// 成交记录
export interface Fill {
  id: string;
  order_id: string;
  symbol: string;
  side: OrderSide;
  quantity: number;
  price: number;
  fill_amount: number;
  commission: number;
  stamp_duty: number;
  transfer_fee: number;
  total_fees: number;
  fill_time: string;
  execution_mode: ExecutionMode;
}

// 成交记录列表响应
export interface FillListResponse {
  total: number;
  items: Fill[];
}
