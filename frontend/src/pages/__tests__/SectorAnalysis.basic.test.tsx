/**
 * SectorAnalysis 基础测试 (不依赖 matchMedia)
 */

import '@testing-library/jest-dom';

// Mock window.matchMedia for Ant Design
const mockMatchMedia = (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: jest.fn(),
  removeListener: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
});

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: mockMatchMedia,
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

describe('SectorAnalysis Basic Tests', () => {
  // 测试基本功能而不依赖复杂的渲染逻辑
  it('应该正确导入 SectorAnalysis 组件', () => {
    // 基础验证：组件可以被导入
    const SectorAnalysis = require('../SectorAnalysis').default;
    expect(SectorAnalysis).toBeDefined();
  });

  it('应该有正确的组件名称', () => {
    const SectorAnalysis = require('../SectorAnalysis').default;
    expect(SectorAnalysis.displayName || SectorAnalysis.name).toBeTruthy();
  });
});
