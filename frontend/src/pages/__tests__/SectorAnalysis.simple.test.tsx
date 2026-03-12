/**
 * SectorAnalysis 组件测试 (简化版)
 */

import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SectorAnalysis from '../../pages/SectorAnalysis';

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

// Mock i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: 'zh_CN',
      changeLanguage: jest.fn(),
    },
  }),
  Trans: () => ({
    t: (key: string) => key,
  }),
}));

describe('SectorAnalysis Component', () => {
  it('应该正确渲染组件', () => {
    render(<SectorAnalysis />);

    expect(screen.getByText(/板块/)).toBeInTheDocument();
  });

  it('应该显示板块类型切换选项卡', async () => {
    render(<SectorAnalysis />);

    await waitFor(() => {
      expect(screen.getByText('行业板块')).toBeInTheDocument();
      expect(screen.getByText('概念板块')).toBeInTheDocument();
      expect(screen.getByText('地域板块')).toBeInTheDocument();
    });
  });

  it('应该显示搜索和刷新功能', async () => {
    render(<SectorAnalysis />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('搜索板块')).toBeInTheDocument();
      expect(screen.getByText('刷新')).toBeInTheDocument();
    });
  });
});
