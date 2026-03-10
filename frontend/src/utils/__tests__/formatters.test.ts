/**
 * 格式化工具函数单元测试
 */

import {
  formatNumber,
  formatVolume,
  formatChangePercent,
  formatChange,
  getChangeColor,
  formatDateTime,
  formatCurrency,
  formatPercent,
} from '../formatters';

describe('formatters', () => {
  describe('formatNumber', () => {
    it('应该正确格式化正数', () => {
      expect(formatNumber(123.456)).toBe('123.46');
      expect(formatNumber(123.456, 0)).toBe('123');
      expect(formatNumber(123.456, 4)).toBe('123.4560');
    });

    it('应该正确格式化负数', () => {
      expect(formatNumber(-123.456)).toBe('-123.46');
    });

    it('应该处理 null 和 undefined', () => {
      expect(formatNumber(null as unknown as number)).toBe('-');
      expect(formatNumber(undefined as unknown as number)).toBe('-');
      expect(formatNumber(NaN)).toBe('-');
    });
  });

  describe('formatVolume', () => {
    it('应该正确格式化亿级别', () => {
      expect(formatVolume(150000000)).toBe('1.50亿');
      expect(formatVolume(100000000)).toBe('1.00亿');
    });

    it('应该正确格式化万级别', () => {
      expect(formatVolume(15000)).toBe('1.50万');
      expect(formatVolume(10000)).toBe('1.00万');
    });

    it('应该正确格式化小数值', () => {
      expect(formatVolume(9999)).toBe('9999');
      expect(formatVolume(1000)).toBe('1000');
    });

    it('应该正确处理负数', () => {
      expect(formatVolume(-150000000)).toBe('-1.50亿');
      expect(formatVolume(-15000)).toBe('-1.50万');
    });

    it('应该处理 null 和 undefined', () => {
      expect(formatVolume(null as unknown as number)).toBe('-');
      expect(formatVolume(undefined as unknown as number)).toBe('-');
    });
  });

  describe('formatChangePercent', () => {
    it('应该为正数添加加号', () => {
      expect(formatChangePercent(5.5)).toBe('+5.50%');
      expect(formatChangePercent(0.01)).toBe('+0.01%');
    });

    it('应该为负数保持减号', () => {
      expect(formatChangePercent(-5.5)).toBe('-5.50%');
    });

    it('应该正确处理零', () => {
      expect(formatChangePercent(0)).toBe('0.00%');
    });
  });

  describe('formatChange', () => {
    it('应该为正数添加加号', () => {
      expect(formatChange(5.5)).toBe('+5.50');
    });

    it('应该为负数保持减号', () => {
      expect(formatChange(-5.5)).toBe('-5.50');
    });

    it('应该正确处理零', () => {
      expect(formatChange(0)).toBe('0.00');
    });
  });

  describe('getChangeColor', () => {
    it('应该为正数返回上涨颜色', () => {
      expect(getChangeColor(0.01)).toBe('var(--color-up)');
      expect(getChangeColor(100)).toBe('var(--color-up)');
    });

    it('应该为负数返回下跌颜色', () => {
      expect(getChangeColor(-0.01)).toBe('var(--color-down)');
      expect(getChangeColor(-100)).toBe('var(--color-down)');
    });

    it('应该为零返回中性颜色', () => {
      expect(getChangeColor(0)).toBe('var(--color-neutral)');
    });
  });

  describe('formatDateTime', () => {
    const testDate = new Date(2024, 0, 15, 10, 30, 45); // 2024-01-15 10:30:45

    it('应该正确格式化完整日期时间', () => {
      expect(formatDateTime(testDate, 'full')).toBe('2024-01-15 10:30:45');
    });

    it('应该正确格式化日期', () => {
      expect(formatDateTime(testDate, 'date')).toBe('2024-01-15');
    });

    it('应该正确格式化时间', () => {
      expect(formatDateTime(testDate, 'time')).toBe('10:30:45');
    });

    it('应该正确格式化日期时间（默认）', () => {
      expect(formatDateTime(testDate, 'datetime')).toBe('01-15 10:30');
    });

    it('应该处理无效日期', () => {
      expect(formatDateTime('invalid')).toBe('-');
      expect(formatDateTime(NaN)).toBe('-');
    });
  });

  describe('formatCurrency', () => {
    it('应该正确格式化亿级别金额', () => {
      expect(formatCurrency(150000000)).toBe('¥1.50亿');
    });

    it('应该正确格式化万级别金额', () => {
      expect(formatCurrency(15000)).toBe('¥1.50万');
    });

    it('应该正确格式化小金额', () => {
      expect(formatCurrency(1000)).toBe('¥1000.00');
    });

    it('应该支持自定义货币符号', () => {
      expect(formatCurrency(15000, '$')).toBe('$1.50万');
    });
  });

  describe('formatPercent', () => {
    it('应该正确格式化百分比', () => {
      expect(formatPercent(0.5)).toBe('50.00%');
      expect(formatPercent(0.1234, 4)).toBe('12.3400%');
    });

    it('应该处理 null 和 undefined', () => {
      expect(formatPercent(null as unknown as number)).toBe('-');
      expect(formatPercent(undefined as unknown as number)).toBe('-');
    });
  });
});
