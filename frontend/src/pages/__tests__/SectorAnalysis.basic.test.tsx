/**
 * SectorAnalysis 基础测试 (不依赖 matchMedia)
 */

import React from 'react';

// 简单的 mock，防止 matchMedia 错误
jest.mock('react-responsive', () => ({
  useMediaQuery: jest.fn().mockReturnValue({
    isDesktop: true,
    isMobile: true,
  }),
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
