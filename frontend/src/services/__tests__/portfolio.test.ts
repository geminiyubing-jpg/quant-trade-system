/**
 * 投资组合服务单元测试
 */

import { portfolioService } from '../portfolio';
import { get, post, put, del } from '../api';

// Mock API 函数
jest.mock('../api');

const mockGet = get as jest.MockedFunction<typeof get>;
const mockPost = post as jest.MockedFunction<typeof post>;
const mockPut = put as jest.MockedFunction<typeof put>;
const mockDel = del as jest.MockedFunction<typeof del>;

describe('Portfolio Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('listPortfolios', () => {
    it('应该成功获取投资组合列表', async () => {
      const mockResponse = {
        items: [
          { id: '1', name: '组合1', total_value: 1000000 },
          { id: '2', name: '组合2', total_value: 2000000 },
        ],
        total: 2,
      };

      mockGet.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.listPortfolios();

      expect(mockGet).toHaveBeenCalledWith('/api/v1/portfolios');
      expect(result.items).toHaveLength(2);
      expect(result.total).toBe(2);
    });

    it('应该处理空列表', async () => {
      mockGet.mockResolvedValueOnce({ items: [], total: 0 });

      const result = await portfolioService.listPortfolios();

      expect(result.items).toHaveLength(0);
      expect(result.total).toBe(0);
    });
  });

  describe('getPortfolio', () => {
    it('应该成功获取单个投资组合', async () => {
      const mockPortfolio = {
        id: '1',
        name: '测试组合',
        total_value: 1000000,
        cash_balance: 100000,
      };

      mockGet.mockResolvedValueOnce(mockPortfolio);

      const result = await portfolioService.getPortfolio('1');

      expect(mockGet).toHaveBeenCalledWith('/api/v1/portfolios/1');
      expect(result.name).toBe('测试组合');
    });
  });

  describe('createPortfolio', () => {
    it('应该成功创建投资组合', async () => {
      const createData = {
        name: '新组合',
        description: '测试描述',
        initial_capital: 100000,
      };

      const mockResponse = {
        id: '3',
        ...createData,
        total_value: 100000,
        cash_balance: 100000,
      };

      mockPost.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.createPortfolio(createData);

      expect(mockPost).toHaveBeenCalledWith('/api/v1/portfolios', createData);
      expect(result.id).toBe('3');
      expect(result.name).toBe('新组合');
    });
  });

  describe('updatePortfolio', () => {
    it('应该成功更新投资组合', async () => {
      const updateData = {
        name: '更新后的组合',
      };

      const mockResponse = {
        id: '1',
        name: '更新后的组合',
        total_value: 1000000,
      };

      mockPut.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.updatePortfolio('1', updateData);

      expect(mockPut).toHaveBeenCalledWith('/api/v1/portfolios/1', updateData);
      expect(result.name).toBe('更新后的组合');
    });
  });

  describe('deletePortfolio', () => {
    it('应该成功删除投资组合', async () => {
      mockDel.mockResolvedValueOnce(undefined);

      await portfolioService.deletePortfolio('1');

      expect(mockDel).toHaveBeenCalledWith('/api/v1/portfolios/1');
    });
  });

  describe('getPositions', () => {
    it('应该成功获取持仓列表', async () => {
      const mockResponse = {
        items: [
          {
            id: '1',
            symbol: '600519.SH',
            name: '贵州茅台',
            quantity: 100,
            avg_cost: 1800,
            current_price: 1850,
            market_value: 185000,
            weight: 0.15,
          },
        ],
        total: 1,
      };

      mockGet.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.getPositions('1');

      expect(mockGet).toHaveBeenCalledWith('/api/v1/portfolios/1/positions');
      expect(result.items).toHaveLength(1);
      expect(result.items[0].symbol).toBe('600519.SH');
    });
  });

  describe('getRiskMetrics', () => {
    it('应该成功获取风险指标', async () => {
      const mockResponse = {
        id: '1',
        portfolio_id: '1',
        var_95: 3.5,
        var_99: 5.2,
        cvar_95: 4.1,
        portfolio_volatility: 15.5,
        max_drawdown: 12.3,
      };

      mockGet.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.getRiskMetrics('1');

      expect(mockGet).toHaveBeenCalledWith('/api/v1/portfolios/1/risk');
      expect(result.var_95).toBe(3.5);
    });
  });

  describe('optimizePortfolio', () => {
    it('应该成功执行组合优化', async () => {
      const optimizeRequest = {
        method: 'MEAN_VARIANCE',
        constraints: {
          max_weight: 0.2,
          min_weight: 0,
        },
      };

      const mockResponse = {
        id: 'opt-1',
        portfolio_id: '1',
        optimization_method: 'MEAN_VARIANCE',
        expected_return: 15.5,
        expected_risk: 12.3,
        expected_sharpe: 1.26,
        optimal_weights: {
          '600519.SH': 0.15,
          '000858.SZ': 0.12,
        },
        status: 'PENDING',
      };

      mockPost.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.optimizePortfolio('1', optimizeRequest);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/portfolios/1/optimize',
        optimizeRequest
      );
      expect(result.expected_sharpe).toBe(1.26);
    });
  });

  describe('getPerformanceMetrics', () => {
    it('应该成功获取绩效指标', async () => {
      const mockResponse = {
        portfolio_id: '1',
        total_return: 25.5,
        annualized_return: 18.3,
        benchmark_return: 12.0,
        sharpe_ratio: 1.35,
        max_drawdown: -8.5,
        win_rate: 0.65,
      };

      mockGet.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.getPerformanceMetrics(
        '1',
        '2025-01-01',
        '2025-12-31'
      );

      expect(mockGet).toHaveBeenCalledWith(
        '/api/v1/portfolios/1/performance?start_date=2025-01-01&end_date=2025-12-31'
      );
      expect(result.sharpe_ratio).toBe(1.35);
    });

    it('应该支持自定义基准', async () => {
      const mockResponse = {
        portfolio_id: '1',
        total_return: 25.5,
        alpha: 3.5,
      };

      mockGet.mockResolvedValueOnce(mockResponse);

      await portfolioService.getPerformanceMetrics(
        '1',
        '2025-01-01',
        '2025-12-31',
        'benchmark-1'
      );

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('benchmark_id=benchmark-1')
      );
    });
  });

  describe('rebalancePortfolio', () => {
    it('应该成功执行再平衡', async () => {
      const mockResponse = {
        success: true,
        message: '再平衡完成',
        trades: [
          { symbol: '600519.SH', action: 'BUY', quantity: 50 },
          { symbol: '000858.SZ', action: 'SELL', quantity: 30 },
        ],
      };

      mockPost.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.rebalancePortfolio('1');

      expect(mockPost).toHaveBeenCalledWith('/api/v1/portfolios/1/rebalance');
      expect(result.trades).toHaveLength(2);
    });
  });

  describe('createBenchmark', () => {
    it('应该成功创建自定义基准', async () => {
      const benchmarkData = {
        name: '我的基准',
        composition: [
          { symbol: '600519.SH', weight: 0.3 },
          { symbol: '000858.SZ', weight: 0.3 },
          { symbol: '601318.SH', weight: 0.4 },
        ],
      };

      const mockResponse = {
        id: 'bm-1',
        portfolio_id: '1',
        ...benchmarkData,
        created_at: '2025-03-11T00:00:00',
      };

      mockPost.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.createBenchmark('1', benchmarkData);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/portfolios/1/benchmarks',
        benchmarkData
      );
      expect(result.id).toBe('bm-1');
    });
  });

  describe('getBenchmarks', () => {
    it('应该成功获取基准列表', async () => {
      const mockResponse = [
        {
          id: 'bm-1',
          name: '基准1',
          composition: [],
        },
        {
          id: 'bm-2',
          name: '基准2',
          composition: [],
        },
      ];

      mockGet.mockResolvedValueOnce(mockResponse);

      const result = await portfolioService.getBenchmarks('1');

      expect(mockGet).toHaveBeenCalledWith('/api/v1/portfolios/1/benchmarks');
      expect(result).toHaveLength(2);
    });
  });
});
