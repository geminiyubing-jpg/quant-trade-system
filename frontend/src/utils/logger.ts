/**
 * ==============================================
 * 日志工具 - 统一管理前端日志输出
 * ==============================================
 * 根据环境变量控制日志级别
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'none';

interface LoggerConfig {
  level: LogLevel;
  enableInProduction: boolean;
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  none: 4,
};

class Logger {
  private static instance: Logger;
  private config: LoggerConfig;

  private constructor() {
    this.config = {
      level: process.env.NODE_ENV === 'production' ? 'warn' : 'debug',
      enableInProduction: false,
    };
  }

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private shouldLog(level: LogLevel): boolean {
    if (process.env.NODE_ENV === 'production' && !this.config.enableInProduction) {
      return level === 'error';
    }
    return LOG_LEVELS[level] >= LOG_LEVELS[this.config.level];
  }

  debug(...args: unknown[]): void {
    if (this.shouldLog('debug')) {
      console.log('[DEBUG]', ...args);
    }
  }

  info(...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.log('[INFO]', ...args);
    }
  }

  warn(...args: unknown[]): void {
    if (this.shouldLog('warn')) {
      console.warn('[WARN]', ...args);
    }
  }

  error(...args: unknown[]): void {
    if (this.shouldLog('error')) {
      console.error('[ERROR]', ...args);
    }
  }

  success(...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.log('%c[SUCCESS]', 'color: green', ...args);
    }
  }
}

export const logger = Logger.getInstance();
export default logger;
