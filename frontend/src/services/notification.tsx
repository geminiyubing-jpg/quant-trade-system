/**
 * 通知服务 - 处理浏览器推送通知、声音提醒
 */

import React from 'react';
import { notification, message } from 'antd';

export interface NotificationOptions {
  title: string;
  body: string;
  type?: 'success' | 'warning' | 'error' | 'info';
  duration?: number;
  sound?: boolean;
  onClick?: () => void;
}

export interface AlertNotificationOptions extends NotificationOptions {
  symbol: string;
  alertId: string;
  alertType: 'price_above' | 'price_below';
  targetPrice?: number;
}

type NotificationType = 'success' | 'warning' | 'error' | 'info';

// 通知类型配置
const NOTIFICATION_CONFIG: Record<NotificationType, {
  icon: string;
  className: string;
  style: React.CSSProperties;
  duration: number;
}> = {
  success: {
    icon: '✅',
    className: 'ant-notification-success',
    style: { backgroundColor: '#f6ffed', borderColor: '#b7eb8f' },
    duration: 4,
  },
  warning: {
    icon: '⚠️',
    className: 'ant-notification-warning',
    style: { backgroundColor: '#fffbe6', borderColor: '#faad14' },
    duration: 5,
  },
  error: {
    icon: '❌',
    className: 'ant-notification-error',
    style: { backgroundColor: '#fff1f0', borderColor: '#ff4d4f' },
    duration: 0,
  },
  info: {
    icon: 'ℹ️',
    className: 'ant-notification-info',
    style: { backgroundColor: '#e6f7ff', borderColor: '#1890ff' },
    duration: 5,
  },
};

class NotificationService {
  private permission: NotificationPermission | null = null;
  private sounds: Record<NotificationType, HTMLAudioElement | null> = {
    success: null,
    warning: null,
    error: null,
    info: null,
  };

  constructor() {
    this.checkPermission();
    this.initSounds();
  }

  /**
   * 检查浏览器通知权限
   */
  async checkPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return 'denied';
    }

    const perm = Notification.permission;
    if (perm === 'granted') {
      this.permission = 'granted';
      return 'granted';
    }

    if (perm === 'denied') {
      this.permission = 'denied';
      return 'denied';
    }

    // 默认权限，请求授权
    const result = await Notification.requestPermission();
    this.permission = result;
    return result;
  }

  /**
   * 初始化音效
   */
  private initSounds(): void {
    try {
      this.sounds = {
        success: new Audio('/sounds/success.mp3'),
        warning: new Audio('/sounds/warning.mp3'),
        error: new Audio('/sounds/error.mp3'),
        info: new Audio('/sounds/info.mp3'),
      };
    } catch (e) {
      console.warn('Failed to initialize sounds:', e);
    }
  }

  /**
   * 显示通知
   */
  async show(options: NotificationOptions): Promise<void> {
    const type = options.type || 'info';
    const config = NOTIFICATION_CONFIG[type];

    // 使用 Ant Design notification
    notification.open({
      message: options.title,
      description: options.body,
      icon: <span>{config.icon}</span>,
      duration: options.duration || config.duration,
      style: config.style,
    });

    // 播放声音
    if (options.sound !== false) {
      this.playSound(type);
    }

    // 发送浏览器通知
    if (this.permission === 'granted') {
      await this.showBrowserNotification(options);
    }
  }

  /**
   * 显示预警通知
   */
  async showAlert(options: AlertNotificationOptions): Promise<void> {
    const title = options.alertType === 'price_above'
      ? `📈 ${options.symbol} 价格突破提醒`
      : `📉 ${options.symbol} 价格跌破提醒`;

    const body = options.targetPrice
      ? `当前价格已${options.alertType === 'price_above' ? '高于' : '低于'}设定的预警价 ¥${options.targetPrice}`
      : `价格已触达预警条件`;

    await this.show({
      type: options.alertType === 'price_above' ? 'success' : 'warning',
      title,
      body,
      sound: true,
      duration: 10,
    });
  }

  /**
   * 显示成功消息
   */
  success(content: string, duration?: number): void {
    message.success(content, duration);
  }

  /**
   * 显示错误消息
   */
  error(content: string, duration?: number): void {
    message.error(content, duration);
  }

  /**
   * 显示警告消息
   */
  warning(content: string, duration?: number): void {
    message.warning(content, duration);
  }

  /**
   * 显示信息消息
   */
  info(content: string, duration?: number): void {
    message.info(content, duration);
  }

  /**
   * 播放声音
   */
  private playSound(type: NotificationType): void {
    const audio = this.sounds[type];
    if (audio) {
      audio.currentTime = 0;
      audio.volume = 0.5;
      audio.play().catch((e) => console.warn('Failed to play sound:', e));
    }
  }

  /**
   * 显示浏览器通知
   */
  private async showBrowserNotification(options: NotificationOptions): Promise<void> {
    if (this.permission !== 'granted') return;

    const browserNotification = new Notification(options.title, {
      body: options.body,
      icon: '/logo192.png',
      tag: 'quant-trade-alert',
      requireInteraction: false,
    });

    browserNotification.onclick = () => {
      window.focus();
      browserNotification.close();
      options.onClick?.();
    };

    // 自动关闭
    setTimeout(() => browserNotification.close(), 10000);
  }
}

// 单例实例
export const notificationService = new NotificationService();
export default notificationService;
