/**
 * Logging utility with production toggle
 * 
 * In production, only errors and warnings are logged.
 * In development, all logs including debug/info are shown.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  enabled: boolean;
  level: LogLevel;
  prefix: string;
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

// Check if we're in production mode
const isProduction = import.meta.env.PROD;

// Default configuration
const defaultConfig: LoggerConfig = {
  enabled: true,
  level: isProduction ? 'warn' : 'debug', // Only warn+ in production
  prefix: '[Nebula]',
};

class Logger {
  private config: LoggerConfig;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...defaultConfig, ...config };
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;
    return LOG_LEVELS[level] >= LOG_LEVELS[this.config.level];
  }

  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
    return `${this.config.prefix} [${timestamp}] [${level.toUpperCase()}] ${message}`;
  }

  debug(message: string, ...args: unknown[]): void {
    if (this.shouldLog('debug')) {
      console.log(this.formatMessage('debug', message), ...args);
    }
  }

  info(message: string, ...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.info(this.formatMessage('info', message), ...args);
    }
  }

  warn(message: string, ...args: unknown[]): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', message), ...args);
    }
  }

  error(message: string, ...args: unknown[]): void {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', message), ...args);
    }
  }

  // Create a child logger with a specific prefix
  createChild(prefix: string): Logger {
    return new Logger({
      ...this.config,
      prefix: `${this.config.prefix} [${prefix}]`,
    });
  }

  // Temporarily enable debug logging (useful for debugging in production)
  enableDebug(): void {
    this.config.level = 'debug';
  }

  // Disable all logging
  disable(): void {
    this.config.enabled = false;
  }

  // Enable logging
  enable(): void {
    this.config.enabled = true;
  }
}

// Export singleton instance
export const logger = new Logger();

// Export factory for creating component-specific loggers
export const createLogger = (componentName: string): Logger => {
  return logger.createChild(componentName);
};

// Audio-specific logger
export const audioLogger = logger.createChild('Audio');

// WebSocket-specific logger
export const wsLogger = logger.createChild('WebSocket');

// Meeting-specific logger
export const meetingLogger = logger.createChild('Meeting');

export default logger;


