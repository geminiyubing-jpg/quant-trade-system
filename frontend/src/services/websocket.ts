/**
 * ==============================================
 * WebSocket 实时行情服务
 * ==============================================
 */

import store from '../store';
import { marketDataActions } from '../store/slices/marketDataSlice';
import authService from './auth';
import subscriptionStorage from './subscriptionStorage';
import { message } from 'antd';
import logger from '../utils/logger';

interface WebSocketMessage {
  type: string;
  data?: any;
  symbols?: string[];
  message?: string;
  code?: number;
}

interface WebSocketConfig {
  url: string;
  token?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private manualClose = false;
  private subscriptions: Set<string> = new Set();

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...config,
    };
  }

  /**
   * 连接 WebSocket
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      logger.warn('WebSocket 已连接');
      return;
    }

    try {
      // 获取 Token
      let token = this.config.token || this.getToken();

      // 开发环境：如果没有 Token，自动登录获取
      if (!token && process.env.NODE_ENV === 'development') {
        logger.warn('未找到 Token，尝试自动登录...');
        this.autoLoginAndConnect();
        return;
      }

      if (!token) {
        logger.error('未找到 Token，无法连接 WebSocket');
        logger.error('请先登录系统，或者在浏览器控制台运行登录命令');
        return;
      }

      // 构建 WebSocket URL
      const wsUrl = `${this.config.url}?token=${token}`;
      logger.info(`正在连接 WebSocket: ${wsUrl}`);

      this.ws = new WebSocket(wsUrl);

      // 连接成功
      this.ws.onopen = () => {
        logger.success('WebSocket 连接成功');
        this.reconnectAttempts = 0;

        // 启动心跳
        this.startHeartbeat();

        // 延迟发送订阅请求，确保连接完全建立
        setTimeout(() => {
          // 首先从 localStorage 加载保存的订阅
          const savedSubscriptions = subscriptionStorage.loadSubscriptions();
          if (savedSubscriptions.length > 0) {
            savedSubscriptions.forEach((s) => this.subscriptions.add(s));
            logger.debug(`从 localStorage 恢复 ${savedSubscriptions.length} 个订阅`);
          }

          if (this.subscriptions.size > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
            const pendingSubscriptions = Array.from(this.subscriptions);
            logger.info(`自动恢复 ${pendingSubscriptions.length} 个订阅:`, pendingSubscriptions);

            // 发送订阅请求
            const message: WebSocketMessage = {
              type: 'subscribe',
              symbols: pendingSubscriptions,
            };
            this.ws.send(JSON.stringify(message));
            logger.debug('已发送恢复订阅请求');
          }
        }, 100);
      };

      // 接收消息
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          logger.error('解析 WebSocket 消息失败:', error);
        }
      };

      // 连接关闭
      this.ws.onclose = (event) => {
        logger.info(`WebSocket 连接关闭: code=${event.code}, reason=${event.reason}`);
        this.stopHeartbeat();

        // 如果不是手动关闭，尝试重连
        if (!this.manualClose) {
          this.scheduleReconnect();
        }
      };

      // 连接错误
      this.ws.onerror = (error) => {
        logger.error('WebSocket 连接错误:', error);
      };
    } catch (error) {
      logger.error('创建 WebSocket 连接失败:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.manualClose = true;

    // 停止心跳
    this.stopHeartbeat();

    // 清除重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // 关闭连接
    if (this.ws) {
      this.ws.close(1000, 'User disconnected');
      this.ws = null;
    }

    logger.info('WebSocket 已断开连接');
  }

  /**
   * 订阅行情
   */
  subscribe(symbols: string[]): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      logger.warn('WebSocket 未连接，订阅请求已排队，连接后将自动订阅');
      // 保存订阅请求，连接后自动订阅
      symbols.forEach((symbol) => this.subscriptions.add(symbol));
      // 持久化到 localStorage
      subscriptionStorage.addSubscriptions(symbols);
      return false;  // 返回 false 表示未立即发送
    }

    const message: WebSocketMessage = {
      type: 'subscribe',
      symbols,
    };

    this.ws.send(JSON.stringify(message));
    logger.debug('订阅行情:', symbols);

    // 保存订阅
    symbols.forEach((symbol) => this.subscriptions.add(symbol));
    // 持久化到 localStorage
    subscriptionStorage.addSubscriptions(symbols);
    return true;  // 返回 true 表示已立即发送
  }

  /**
   * 取消订阅
   */
  unsubscribe(symbols: string[]): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      logger.warn('WebSocket 未连接');
      return;
    }

    const message: WebSocketMessage = {
      type: 'unsubscribe',
      symbols,
    };

    this.ws.send(JSON.stringify(message));
    logger.debug('取消订阅:', symbols);

    // 移除订阅
    symbols.forEach((symbol) => this.subscriptions.delete(symbol));
    // 从 localStorage 移除
    subscriptionStorage.removeSubscriptions(symbols);
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'connected':
        logger.success('WebSocket 已连接:', message.data);
        break;

      case 'quote':
        // 更新 Redux Store
        if (message.data) {
          store.dispatch(marketDataActions.updateQuote(message.data));
          logger.debug('收到行情:', message.data.symbol, message.data.price);
        }
        break;

      case 'subscribed':
        logger.debug('订阅成功:', message.data);
        break;

      case 'unsubscribed':
        logger.debug('取消订阅成功:', message.data);
        break;

      case 'pong':
        logger.debug('收到心跳响应');
        break;

      case 'error':
        logger.error('WebSocket 错误:', message.message, message.code);
        break;

      case 'alert_triggered':
        // 处理预警触发通知
        this.handleAlertTriggered(message.data);
        break;

      default:
        logger.warn('未知消息类型:', message.type);
    }
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        const message: WebSocketMessage = { type: 'ping' };
        this.ws.send(JSON.stringify(message));
      }
    }, this.config.heartbeatInterval);

    logger.debug('心跳已启动');
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
      logger.debug('心跳已停止');
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 10)) {
      logger.error('已达到最大重连次数，停止重连');
      return;
    }

    if (this.reconnectTimer) {
      return; // 已经在重连中
    }

    const delay = (this.config.reconnectInterval || 5000) * Math.pow(1.5, this.reconnectAttempts);
    logger.info(`${delay / 1000} 秒后尝试重连 (${this.reconnectAttempts + 1}/${this.config.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * 获取 Token
   */
  private getToken(): string | null {
    try {
      // 优先使用 authService 获取 Token
      const token = authService.getAccessToken();
      if (token) {
        // 检查 Token 是否即将过期，如果是则尝试刷新
        if (authService.isTokenExpiringSoon()) {
          console.log('🔄 Token 即将过期，尝试刷新...');
          authService.refreshToken();
        }
        return token;
      }

      // 兼容旧代码：从 localStorage 获取 Token
      const authState = localStorage.getItem('auth');
      if (authState) {
        const auth = JSON.parse(authState);
        return auth.accessToken || null;
      }

      // 尝试从另一个可能的 key 获取
      const fallbackToken = localStorage.getItem('token');
      if (fallbackToken) {
        return fallbackToken;
      }

      logger.warn('未找到认证 Token');
      return null;
    } catch (error) {
      logger.error('获取 Token 失败:', error);
      return null;
    }
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 自动登录并连接（开发环境）
   */
  private async autoLoginAndConnect(): Promise<void> {
    try {
      logger.info('正在自动登录...');
      const success = await authService.autoLogin();

      if (success) {
        // 重新连接
        this.config.token = authService.getAccessToken() || undefined;
        this.connect();
      } else {
        logger.error('自动登录失败');
        logger.error('请手动登录系统，或者检查后端是否运行');
      }
    } catch (error) {
      logger.error('自动登录错误:', error);
      logger.error('请手动登录系统，或者检查后端是否运行');
    }
  }

  /**
   * 获取当前订阅
   */
  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }

  /**
   * 清除所有订阅
   */
  clearAllSubscriptions(): void {
    // 取消所有订阅
    if (this.subscriptions.size > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
      const symbols = Array.from(this.subscriptions);
      this.unsubscribe(symbols);
    }

    // 清空内存中的订阅
    this.subscriptions.clear();
    // 清除 localStorage
    subscriptionStorage.clearSubscriptions();
    logger.info('已清除所有订阅');
  }

  /**
   * 处理预警触发通知
   */
  private handleAlertTriggered(data: any): void {
    logger.info('收到预警触发通知:', data);
    // 触发自定义事件，让 UI 组件可以响应
    window.dispatchEvent(
      new CustomEvent('alertTriggered', {
        detail: {
          alertId: data.alert_id,
          symbol: data.symbol,
          alertType: data.alert_type,
          targetValue: data.target_value,
          currentPrice: data.current_price,
          message: data.message,
          triggeredAt: data.triggered_at,
        },
      })
    );
    // 也可以通过消息提示用户
    message.warning({
      content: `预警触发: ${data.symbol} ${data.message}`,
      duration: 5,
    });
  }
}

// 创建全局 WebSocket 服务实例
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api/v1/ws/market';
export const websocketService = new WebSocketService({ url: WS_URL });

export default websocketService;
