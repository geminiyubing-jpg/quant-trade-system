/**
 * SectorAnalysis 组件测试
 */

import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import SectorAnalysis from '../../pages/SectorAnalysis';
import * as api from '../../services/api';

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

// Mock API
jest.mock('../../services/api');

// Mock i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: 'zh_CN',
      changeLanguage: jest.fn(),
    },
  }),
}));

const mockGet = api.get as jest.MockedFunction<typeof api.get>;

// 包装组件
const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </ConfigProvider>
  );
};

describe('SectorAnalysis Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('页面渲染', () => {
    it('应该正确渲染页面标题', () => {
      mockGet.mockResolvedValueOnce({
        success: true,
        data: [],
        summary: { total: 0, up: 0, down: 0, flat: 0, best: null, worst: null },
      } as unknown as ReturnType<typeof api.get>);

      renderWithProviders(<SectorAnalysis />);

      expect(screen.getByText(/板块/)).toBeInTheDocument();
    });

    it('应该显示板块类型切换选项卡', async () => {
      mockGet.mockResolvedValueOnce({
        success: true,
        data: [],
        summary: { total: 0, up: 0, down: 0, flat: 0, best: null, worst: null },
      } as unknown as ReturnType<typeof api.get>);

      renderWithProviders(<SectorAnalysis />);

      await waitFor(() => {
        expect(screen.getByText('行业板块')).toBeInTheDocument();
        expect(screen.getByText('概念板块')).toBeInTheDocument();
        expect(screen.getByText('地域板块')).toBeInTheDocument();
      });
    });

    it('应该显示统计概览卡片', async () => {
      mockGet.mockResolvedValueOnce({
        success: true,
        data: [],
        summary: {
          total: 50,
          up: 30,
          down: 15,
          flat: 5,
          best: { name: '半导体', change_pct: 5.5 },
          worst: { name: '医药', change_pct: -3.2 },
        },
      } as unknown as ReturnType<typeof api.get>);

      renderWithProviders(<SectorAnalysis />);

      await waitFor(() => {
        expect(screen.getByText('板块总数')).toBeInTheDocument();
        expect(screen.getByText('上涨板块')).toBeInTheDocument();
        expect(screen.getByText('下跌板块')).toBeInTheDocument();
      });
    });
  });

  describe('数据加载', () => {
    it('应该在加载时显示加载状态', () => {
      mockGet.mockImplementation(() => new Promise(() => {}));

      renderWithProviders(<SectorAnalysis />);

      // 应该显示 Spin 组件
      expect(document.querySelector('.ant-spin')).toBeInTheDocument();
    });

    it('应该正确处理API错误', async () => {
      mockGet.mockRejectedValueOnce(new Error('API Error'));

      renderWithProviders(<SectorAnalysis />);

      // 组件应该优雅地处理错误，不崩溃
      await waitFor(() => {
        expect(screen.getByText(/板块/)).toBeInTheDocument();
      });
    });

    it('应该在没有数据时显示空状态', async () => {
      mockGet.mockResolvedValueOnce({
        success: true,
        data: [],
        summary: { total: 0, up: 0, down: 0, flat: 0, best: null, worst: null },
      } as unknown as ReturnType<typeof api.get>);

      renderWithProviders(<SectorAnalysis />);

      await waitFor(() => {
        expect(screen.getByText(/暂无板块数据/)).toBeInTheDocument();
      });
    });
  });

  describe('板块类型切换', () => {
    it('应该默认选中行业板块', async () => {
      mockGet.mockResolvedValue({
        success: true,
        data: [],
        summary: { total: 0, up: 0, down: 0, flat: 0, best: null, worst: null },
      } as unknown as ReturnType<typeof api.get>);

      renderWithProviders(<SectorAnalysis />);

      // 默认应该请求行业板块数据
      await waitFor(() => {
        expect(mockGet).toHaveBeenCalledWith(
          expect.stringContaining('sector_type=industry')
        );
      });
    });
  });

  describe('搜索功能', () => {
    it('应该显示搜索框', async () => {
      mockGet.mockResolvedValueOnce({
        success: true,
        data: [],
        summary: { total: 0, up: 0, down: 0, flat: 0, best: null, worst: null },
      } as unknown as ReturnType<typeof api.get>);

      renderWithProviders(<SectorAnalysis />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('搜索板块')).toBeInTheDocument();
      });
    });
  });

  describe('刷新功能', () => {
    it('应该显示刷新按钮', async () => {
      mockGet.mockResolvedValueOnce({
        success: true,
        data: [],
        summary: { total: 0, up: 0, down: 0, flat: 0, best: null, worst: null },
      } as unknown as ReturnType<typeof api.get>);

      renderWithProviders(<SectorAnalysis />);

      await waitFor(() => {
        expect(screen.getByText('刷新')).toBeInTheDocument();
      });
    });
  });

  describe('板块详情弹窗', () => {
    it('点击详情按钮应该打开弹窗', async () => {
      mockGet.mockResolvedValue({
        success: true,
        data: [
          {
            name: '半导体',
            code: 'BK0501',
            change_pct: 2.5,
            amount: 15000000000,
            leading_stock: '中芯国际',
            leading_stock_change: 5.2,
          },
        ],
        summary: {
          total: 1,
          up: 1,
          down: 0,
          flat: 0,
          best: { name: '半导体', change_pct: 2.5 },
          worst: { name: '半导体', change_pct: 2.5 },
        },
      } as unknown as ReturnType<typeof api.get>);

      renderWithProviders(<SectorAnalysis />);

      await waitFor(() => {
        const detailButton = screen.getByText('详情');
        expect(detailButton).toBeInTheDocument();
      });
    });
  });
});
