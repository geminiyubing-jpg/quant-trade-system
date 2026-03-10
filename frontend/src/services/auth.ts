/**
 * ==============================================
 * 认证服务 - Token 自动刷新机制
 * ==============================================
 */

import logger from '../utils/logger';

interface UserInfo {
  id: string;
  username: string;
  email?: string;
  role?: string;
}

interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: number;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user?: UserInfo;
}

class AuthService {
  private static instance: AuthService;
  private refreshTimer: NodeJS.Timeout | null = null;
  private readonly TOKEN_KEY = 'auth';
  private readonly TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 分钟前刷新

  private constructor() {
    this.initAutoRefresh();
  }

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * 初始化自动刷新
   */
  private initAutoRefresh(): void {
    // 页面加载时检查 Token
    this.checkAndRefreshToken();

    // 定期检查 Token 状态（每分钟）
    setInterval(() => {
      this.checkAndRefreshToken();
    }, 60 * 1000);

    // 页面可见性变化时检查
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.checkAndRefreshToken();
      }
    });
  }

  /**
   * 获取存储的 Token
   */
  getTokens(): AuthTokens | null {
    try {
      const authData = localStorage.getItem(this.TOKEN_KEY);
      if (authData) {
        return JSON.parse(authData);
      }
      return null;
    } catch (error) {
      logger.error('获取 Token 失败:', error);
      return null;
    }
  }

  /**
   * 获取 Access Token
   */
  getAccessToken(): string | null {
    const tokens = this.getTokens();
    return tokens?.accessToken || null;
  }

  /**
   * 保存 Token
   */
  saveTokens(accessToken: string, refreshToken?: string): void {
    // 解析 JWT 获取过期时间
    const expiresAt = this.getTokenExpiration(accessToken);

    const authData: AuthTokens = {
      accessToken,
      refreshToken,
      expiresAt,
    };

    localStorage.setItem(this.TOKEN_KEY, JSON.stringify(authData));
    localStorage.setItem('token', accessToken); // 兼容旧代码

    logger.info('Token 已保存，过期时间:', new Date(expiresAt || 0).toLocaleString());

    // 设置自动刷新
    this.scheduleRefresh(expiresAt);
  }

  /**
   * 解析 JWT 获取过期时间
   */
  private getTokenExpiration(token: string): number | undefined {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp ? payload.exp * 1000 : undefined;
    } catch (error) {
      logger.error('解析 Token 失败:', error);
      return undefined;
    }
  }

  /**
   * 检查 Token 是否即将过期
   */
  isTokenExpiringSoon(): boolean {
    const tokens = this.getTokens();
    if (!tokens?.expiresAt) return true;

    const now = Date.now();
    return tokens.expiresAt - now < this.TOKEN_REFRESH_THRESHOLD;
  }

  /**
   * 检查 Token 是否已过期
   */
  isTokenExpired(): boolean {
    const tokens = this.getTokens();
    if (!tokens?.expiresAt) return true;

    return Date.now() >= tokens.expiresAt;
  }

  /**
   * 检查并刷新 Token
   */
  private async checkAndRefreshToken(): Promise<void> {
    const tokens = this.getTokens();

    if (!tokens?.accessToken) {
      logger.debug('未找到 Token');
      return;
    }

    if (this.isTokenExpiringSoon()) {
      logger.info('Token 即将过期，尝试刷新...');
      await this.refreshToken();
    }
  }

  /**
   * 安排自动刷新
   */
  private scheduleRefresh(expiresAt?: number): void {
    // 清除之前的定时器
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (!expiresAt) return;

    const now = Date.now();
    const refreshTime = expiresAt - this.TOKEN_REFRESH_THRESHOLD - now;

    if (refreshTime > 0) {
      logger.debug(`将在 ${Math.round(refreshTime / 1000 / 60)} 分钟后刷新 Token`);
      this.refreshTimer = setTimeout(() => {
        this.refreshToken();
      }, refreshTime);
    }
  }

  /**
   * 刷新 Token
   */
  async refreshToken(): Promise<boolean> {
    try {
      // 尝试使用刷新令牌
      const tokens = this.getTokens();

      if (tokens?.refreshToken) {
        const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: tokens.refreshToken }),
        });

        if (response.ok) {
          const data: LoginResponse = await response.json();
          this.saveTokens(data.access_token, tokens.refreshToken);
          logger.success('Token 刷新成功');
          return true;
        }
      }

      // 如果刷新令牌失败，尝试重新登录（开发环境）
      if (process.env.NODE_ENV === 'development') {
        return await this.autoLogin();
      }

      return false;
    } catch (error) {
      logger.error('Token 刷新失败:', error);
      return false;
    }
  }

  /**
   * 自动登录（开发环境）
   */
  async autoLogin(): Promise<boolean> {
    try {
      logger.info('尝试自动登录...');
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'test_user',
          password: 'testpass123',
        }),
      });

      if (!response.ok) {
        throw new Error('登录请求失败');
      }

      const data: LoginResponse = await response.json();

      if (data.access_token) {
        this.saveTokens(data.access_token);
        logger.success('自动登录成功！');
        return true;
      }

      return false;
    } catch (error) {
      logger.error('自动登录失败:', error);
      return false;
    }
  }

  /**
   * 登出
   */
  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem('token');
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    logger.info('已登出');
  }

  /**
   * 检查是否已登录
   */
  isAuthenticated(): boolean {
    const tokens = this.getTokens();
    if (!tokens?.accessToken) return false;

    // 检查是否过期
    if (tokens.expiresAt && Date.now() >= tokens.expiresAt) {
      return false;
    }

    return true;
  }
}

// 导出单例
export const authService = AuthService.getInstance();
export default authService;
