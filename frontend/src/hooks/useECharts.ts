/**
 * ECharts 安全 Hook
 * Safe ECharts Hook for React 18+
 *
 * 解决 ECharts 与 React DOM 操作冲突的问题
 */
import { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';

interface UseEChartsOptions {
  theme?: string;
  onInit?: (chart: echarts.ECharts) => void;
  onDispose?: () => void;
}

interface UseEChartsReturn {
  chartRef: React.RefObject<HTMLDivElement>;
  chart: echarts.ECharts | null;
  isReady: boolean;
}

/**
 * 安全的 ECharts Hook
 *
 * 特点：
 * 1. 自动处理 React 18 严格模式的双次挂载
 * 2. 安全销毁图表实例，避免 DOM 操作冲突
 * 3. 支持响应式调整大小（窗口 + 容器）
 */
export function useECharts(options: UseEChartsOptions = {}): UseEChartsReturn {
  const { theme = 'dark', onInit, onDispose } = options;

  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const isInitializedRef = useRef(false);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const [isReady, setIsReady] = useState(false);

  // 初始化图表
  useEffect(() => {
    const container = chartRef.current;
    if (!container) return;

    // 防止重复初始化
    if (isInitializedRef.current) return;
    isInitializedRef.current = true;

    // 等待 DOM 完全挂载
    const initTimeout = setTimeout(() => {
      // 再次检查容器是否仍然存在
      if (!chartRef.current || !chartRef.current.isConnected) {
        isInitializedRef.current = false;
        return;
      }

      // 清理容器内的残留 DOM（ECharts 之前可能遗留的）
      const container = chartRef.current;
      if (container) {
        // 保存并恢复可能存在的子元素状态
        while (container.firstChild) {
          container.removeChild(container.firstChild);
        }
      }

      // 创建新实例
      try {
        chartInstance.current = echarts.init(container, theme);
        setIsReady(true);
        onInit?.(chartInstance.current);
      } catch (e) {
        console.error('Failed to initialize ECharts:', e);
        isInitializedRef.current = false;
      }
    }, 0);

    // 处理图表大小调整
    const handleResize = () => {
      const chart = chartInstance.current;
      if (chart && !chart.isDisposed()) {
        chart.resize();
      }
    };

    // 监听窗口大小变化
    window.addEventListener('resize', handleResize);

    // 使用 ResizeObserver 监听容器大小变化
    if (container && typeof ResizeObserver !== 'undefined') {
      resizeObserverRef.current = new ResizeObserver(() => {
        handleResize();
      });
      resizeObserverRef.current.observe(container);
    }

    return () => {
      clearTimeout(initTimeout);
      window.removeEventListener('resize', handleResize);

      // 清理 ResizeObserver
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
        resizeObserverRef.current = null;
      }

      // 安全销毁
      const chart = chartInstance.current;
      if (chart) {
        try {
          if (!chart.isDisposed()) {
            chart.dispose();
          }
        } catch {
          // 忽略销毁错误
        }
        chartInstance.current = null;
      }

      isInitializedRef.current = false;
      setIsReady(false);
      onDispose?.();
    };
  }, [theme, onInit, onDispose]);

  return {
    chartRef,
    chart: chartInstance.current,
    isReady,
  };
}

/**
 * 安全设置图表选项
 */
export function useChartOption(
  chart: echarts.ECharts | null,
  option: echarts.EChartsOption | null,
  notMerge: boolean = false
) {
  useEffect(() => {
    if (!chart || !option || chart.isDisposed()) return;

    try {
      // 使用 as any 绕过 ECharts 类型定义的兼容性问题
      chart.setOption(option as any, notMerge);
    } catch (e) {
      console.error('Failed to set chart option:', e);
    }
  }, [chart, option, notMerge]);
}

export default useECharts;
