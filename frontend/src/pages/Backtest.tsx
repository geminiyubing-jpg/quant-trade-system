/**
 * 策略回测页面 - 增强版
 * 功能：回测配置、因子分析、归因分析、高级绩效指标
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Form, Select, DatePicker, Button, Table, Statistic, Row, Col,
  Progress, Tag, Divider, Tabs, message, Tooltip, Descriptions,
  Empty, Alert, InputNumber, Typography, Spin, Space
} from 'antd';
import {
  PlayCircleOutlined, BarChartOutlined, InfoCircleOutlined,
  ExperimentOutlined, DashboardOutlined, StockOutlined, FundOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

// 导入服务和类型
import backtestService from '../services/backtest';
import type {
  BacktestResult,
  CreateBacktestRequest,
} from '../types/backtest';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;
const { Text, Title } = Typography;

// 因子分析结果
interface FactorAnalysis {
  factor_name: string;
  ic: number;
  ic_ir: number;
  ic_positive_ratio: number;
  factor_return: number;
  turnover: number;
  monotonicity: number;
}

// 归因分析结果
interface AttributionAnalysis {
  total_return: number;
  benchmark_return: number;
  active_return: number;
  allocation_effect: number;
  selection_effect: number;
  interaction_effect: number;
  timing_effect: number;
}

// 扩展绩效指标
interface ExtendedMetrics {
  sortino_ratio: number;
  calmar_ratio: number;
  information_ratio: number;
  treynor_ratio: number;
  alpha: number;
  beta: number;
  tracking_error: number;
  downside_risk: number;
  var_95: number;
  cvar_95: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  avg_holding_period: number;
}

// 扩展的回测结果（包含分析数据）
interface ExtendedBacktestResult extends BacktestResult {
  // 驼峰命名别名（用于兼容）
  strategyName?: string;
  startDate?: string;
  endDate?: string;
  initialCapital?: number;
  finalCapital?: number;
  totalReturn?: number;
  annualReturn?: number;
  maxDrawdown?: number;
  sharpeRatio?: number;
  winRate?: number;
  profitFactor?: number;
  totalTrades?: number;
  createdAt?: string;
  // 分析数据
  factorAnalysis?: FactorAnalysis[];
  attribution?: AttributionAnalysis;
  extendedMetrics?: ExtendedMetrics;
}

const Backtest: React.FC = () => {
  const [form] = Form.useForm();
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ExtendedBacktestResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<ExtendedBacktestResult | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  // 保留用于未来扩展的 trades 和 equityCurve 数据
  const [_trades, setTrades] = useState<unknown[]>([]);
  const [_equityCurve, setEquityCurve] = useState<unknown[]>([]);

  // 加载回测结果列表
  const loadResults = useCallback(async () => {
    setLoading(true);
    try {
      const res = await backtestService.getBacktestResults({ limit: 20 });
      const extendedResults: ExtendedBacktestResult[] = (res.items || []).map(r => ({
        ...r,
        strategyName: r.strategy_name,
        startDate: r.start_date,
        endDate: r.end_date,
        initialCapital: r.initial_capital,
        finalCapital: r.final_capital,
        totalReturn: r.total_return,
        annualReturn: r.annual_return,
        maxDrawdown: r.max_drawdown,
        sharpeRatio: r.sharpe_ratio,
        winRate: r.win_rate,
        profitFactor: r.profit_factor,
        totalTrades: r.total_trades,
        createdAt: r.created_at,
      }));
      setResults(extendedResults);
      if (extendedResults.length > 0 && !selectedResult) {
        setSelectedResult(extendedResults[0]);
      }
    } catch (error) {
      console.error('加载回测结果失败:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [selectedResult]);

  useEffect(() => {
    loadResults();
  }, [loadResults]);

  // 加载选中结果的详细数据
  const loadResultDetails = useCallback(async () => {
    if (!selectedResult) return;

    setLoading(true);
    try {
      const [tradesRes, curveRes] = await Promise.allSettled([
        backtestService.getBacktestTrades(selectedResult.backtest_id),
        backtestService.getEquityCurve(selectedResult.backtest_id),
      ]);

      if (tradesRes.status === 'fulfilled') {
        // 使用类型断言处理返回值
        const tradesData = tradesRes.value as { items?: unknown[] };
        setTrades(tradesData.items || []);
      } else {
        setTrades([]);
      }

      if (curveRes.status === 'fulfilled') {
        // equityCurve 返回的是 { equity_curve: [...] } 结构
        const curveData = curveRes.value as { equity_curve?: unknown[] };
        setEquityCurve(curveData.equity_curve || []);
      } else {
        setEquityCurve([]);
      }
    } catch (error) {
      console.error('加载详情失败:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedResult]);

  useEffect(() => {
    if (selectedResult) {
      loadResultDetails();
    }
  }, [selectedResult, loadResultDetails]);

  // 运行回测
  const runBacktest = async () => {
    try {
      const values = await form.validateFields();
      setRunning(true);
      setProgress(0);

      const request: CreateBacktestRequest = {
        strategy_id: values.strategy,
        strategy_name: values.strategy === 'ma_cross' ? '均线突破策略' :
                       values.strategy === 'rsi_reversion' ? 'RSI均值回归' : '动量突破策略',
        symbols: values.symbols || ['000001.SZ'],
        start_date: values.dateRange[0].format('YYYY-MM-DD'),
        end_date: values.dateRange[1].format('YYYY-MM-DD'),
        initial_capital: values.initialCapital || 1000000,
        commission_rate: values.commission || 0.0003,
        benchmark_symbol: '000300.SH',
      };

      // 模拟进度
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 500);

      await backtestService.runBacktest(request);

      clearInterval(progressInterval);
      setProgress(100);

      message.success('回测完成');
      loadResults();
    } catch (error) {
      console.error('回测失败:', error);
      message.error('回测执行失败');
    } finally {
      setRunning(false);
      setProgress(0);
    }
  };

  // 停止回测
  const stopBacktest = async () => {
    if (!selectedResult) return;
    try {
      await backtestService.stopBacktest(selectedResult.backtest_id);
      message.success('回测已停止');
      loadResults();
    } catch (error) {
      console.error('停止回测失败:', error);
    }
  };

  // 执行因子分析
  const runFactorAnalysis = async () => {
    if (!selectedResult) return;
    message.loading('正在执行因子分析...', 0);
    try {
      await backtestService.runFactorAnalysis(selectedResult.backtest_id, {
        factor_name: '综合因子',
        signals: [],
        returns: [],
      });
      message.destroy();
      message.success('因子分析完成');
      loadResultDetails();
    } catch (error) {
      message.destroy();
      console.error('因子分析失败:', error);
      message.error('因子分析执行失败');
    }
  };

  // 执行归因分析
  const runAttribution = async () => {
    if (!selectedResult) return;
    message.loading('正在执行归因分析...', 0);
    try {
      await backtestService.runAttributionAnalysis(selectedResult.backtest_id, {
        benchmark_symbol: '000300.SH',
        portfolio_weights: [],
        benchmark_weights: [],
        returns_data: [],
      });
      message.destroy();
      message.success('归因分析完成');
      loadResultDetails();
    } catch (error) {
      message.destroy();
      console.error('归因分析失败:', error);
      message.error('归因分析执行失败');
    }
  };

  // 因子分析表格列
  const factorColumns: ColumnsType<FactorAnalysis> = [
    { title: '因子名称', dataIndex: 'factor_name', key: 'factor_name' },
    {
      title: 'IC', dataIndex: 'ic', key: 'ic',
      render: (v) => <span style={{ color: v >= 0.03 ? '#52c41a' : v >= 0 ? '#faad14' : '#ff4d4f' }}>{v.toFixed(3)}</span>
    },
    {
      title: 'IC_IR', dataIndex: 'ic_ir', key: 'ic_ir',
      render: (v) => <span style={{ color: v >= 2 ? '#52c41a' : v >= 1 ? '#faad14' : '#ff4d4f' }}>{v.toFixed(2)}</span>
    },
    {
      title: 'IC正值占比', dataIndex: 'ic_positive_ratio', key: 'ic_positive_ratio',
      render: (v) => <Progress percent={v * 100} size="small" style={{ width: 80 }} />
    },
    {
      title: '因子收益', dataIndex: 'factor_return', key: 'factor_return',
      render: (v) => <span style={{ color: v >= 0 ? '#ff4d4f' : '#52c41a' }}>{(v * 100).toFixed(1)}%</span>
    },
    { title: '换手率', dataIndex: 'turnover', key: 'turnover', render: (v) => `${(v * 100).toFixed(0)}%` },
  ];

  // 结果表格列
  const resultColumns: ColumnsType<ExtendedBacktestResult> = [
    {
      title: '策略名称', dataIndex: 'strategyName', key: 'strategyName',
      render: (v, r) => <a onClick={() => setSelectedResult(r)}>{v || r.strategy_name}</a>
    },
    {
      title: '回测周期', key: 'period',
      render: (_, r) => `${r.start_date} ~ ${r.end_date}`
    },
    {
      title: '总收益', dataIndex: 'total_return', key: 'total_return',
      render: (v) => {
        const val = v;
        return <span style={{ color: val >= 0 ? '#ff4d4f' : '#52c41a', fontWeight: 'bold' }}>{val >= 0 ? '+' : ''}{Number(val).toFixed(1)}%</span>;
      }
    },
    {
      title: '夏普', dataIndex: 'sharpe_ratio', key: 'sharpe_ratio',
      render: (v) => {
        const val = v;
        return <Tag color={val >= 1 ? 'green' : val >= 0.5 ? 'orange' : 'red'}>{Number(val).toFixed(2)}</Tag>;
      }
    },
    {
      title: '最大回撤', dataIndex: 'max_drawdown', key: 'max_drawdown',
      render: (v) => {
        const val = v;
        return <span style={{ color: '#ff4d4f' }}>-{Number(val).toFixed(1)}%</span>;
      }
    },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (v) => <Tag color={v === 'completed' ? 'success' : v === 'running' ? 'processing' : 'default'}>{v === 'completed' ? '完成' : v === 'running' ? '运行中' : '待执行'}</Tag>
    },
    {
      title: '操作', key: 'action',
      render: (_, r) => (
        <Space>
          <Button type="link" size="small" onClick={() => setSelectedResult(r)}>详情</Button>
          {r.status === 'running' && (
            <Button type="link" size="small" danger onClick={stopBacktest}>停止</Button>
          )}
        </Space>
      )
    },
  ];

  return (
    <div className="backtest-page">
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}><ExperimentOutlined style={{ marginRight: 8, color: 'var(--bb-accent-primary)' }} />策略回测</Title>
            <Text type="secondary">回测验证 · 因子分析 · 归因分析 · 风险度量</Text>
          </Col>
          <Col>
            <Button icon={<ReloadOutlined />} onClick={loadResults} loading={loading}>刷新</Button>
          </Col>
        </Row>
      </div>

      <Row gutter={24}>
        {/* 左侧：配置 */}
        <Col xs={24} lg={6}>
          <Card title="回测配置" size="small">
            <Form form={form} layout="vertical" size="small" initialValues={{ strategy: 'ma_cross', initialCapital: 1000000, commission: 0.0003 }}>
              <Form.Item name="strategy" label="选择策略" rules={[{ required: true }]}>
                <Select>
                  <Option value="ma_cross">均线突破策略</Option>
                  <Option value="rsi_reversion">RSI均值回归</Option>
                  <Option value="momentum">动量突破策略</Option>
                </Select>
              </Form.Item>
              <Form.Item name="dateRange" label="回测周期" rules={[{ required: true }]}>
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="symbols" label="交易标的">
                <Select mode="tags" placeholder="输入股票代码">
                  <Option value="000001.SZ">000001.SZ</Option>
                  <Option value="600000.SH">600000.SH</Option>
                </Select>
              </Form.Item>
              <Row gutter={8}>
                <Col span={12}>
                  <Form.Item name="initialCapital" label="初始资金">
                    <InputNumber style={{ width: '100%' }} min={10000} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={<span>手续费 <Tooltip title="双边费率"><InfoCircleOutlined /></Tooltip></span>} name="commission">
                    <InputNumber style={{ width: '100%' }} min={0} max={0.01} step={0.0001} />
                  </Form.Item>
                </Col>
              </Row>
              <Divider />
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={runBacktest} loading={running} block>
                运行回测
              </Button>
              {running && <Progress percent={progress} status="active" style={{ marginTop: 12 }} />}
            </Form>
          </Card>
        </Col>

        {/* 右侧：结果 */}
        <Col xs={24} lg={18}>
          <Spin spinning={loading}>
            {selectedResult ? (
              <Tabs activeKey={activeTab} onChange={setActiveTab}>
                {/* 概览 */}
                <TabPane tab={<span><DashboardOutlined /> 概览</span>} key="overview">
                  <Row gutter={[16, 16]}>
                    {[
                      { label: '总收益', value: selectedResult.total_return, suffix: '%', color: (selectedResult.total_return || 0) >= 0 ? '#ff4d4f' : '#52c41a' },
                      { label: '年化收益', value: selectedResult.annual_return, suffix: '%', color: (selectedResult.annual_return || 0) >= 0 ? '#ff4d4f' : '#52c41a' },
                      { label: '夏普比率', value: selectedResult.sharpe_ratio, suffix: '', color: (selectedResult.sharpe_ratio || 0) >= 1 ? '#52c41a' : '#faad14' },
                      { label: '最大回撤', value: selectedResult.max_drawdown, suffix: '%', color: '#ff4d4f' },
                    ].map((item, i) => (
                      <Col xs={12} sm={6} key={i}>
                        <Card size="small">
                          <Statistic
                            title={item.label}
                            value={item.value || 0}
                            precision={2}
                            suffix={item.suffix}
                            valueStyle={{ color: item.color }}
                          />
                        </Card>
                      </Col>
                    ))}
                  </Row>
                  <Card title="高级指标" size="small" style={{ marginTop: 16 }}>
                    {selectedResult.extendedMetrics ? (
                      <Row gutter={[16, 16]}>
                        {[
                          { label: 'Sortino比率', value: selectedResult.extendedMetrics.sortino_ratio },
                          { label: 'Calmar比率', value: selectedResult.extendedMetrics.calmar_ratio },
                          { label: '信息比率', value: selectedResult.extendedMetrics.information_ratio },
                          { label: 'Alpha', value: selectedResult.extendedMetrics.alpha, suffix: '%' },
                          { label: 'Beta', value: selectedResult.extendedMetrics.beta },
                          { label: '跟踪误差', value: selectedResult.extendedMetrics.tracking_error, suffix: '%' },
                          { label: '下行风险', value: selectedResult.extendedMetrics.downside_risk, suffix: '%' },
                          { label: '95% VaR', value: selectedResult.extendedMetrics.var_95, suffix: '%' },
                        ].map((item, i) => (
                          <Col xs={12} sm={6} key={i}>
                            <Statistic title={item.label} value={item.value || 0} precision={2} suffix={item.suffix} />
                          </Col>
                        ))}
                      </Row>
                    ) : (
                      <Empty description="暂无扩展指标数据" />
                    )}
                  </Card>
                </TabPane>

                {/* 因子分析 */}
                <TabPane tab={<span><StockOutlined /> 因子分析</span>} key="factor">
                  <Card size="small" extra={<Button type="primary" size="small" onClick={runFactorAnalysis}>执行分析</Button>}>
                    <Alert message="因子分析评估策略信号对股票未来收益的预测能力，IC>0.03 且 IC_IR>2 表示因子有效" type="info" showIcon style={{ marginBottom: 16 }} />
                    {selectedResult.factorAnalysis && selectedResult.factorAnalysis.length > 0 ? (
                      <Table columns={factorColumns} dataSource={selectedResult.factorAnalysis} rowKey="factor_name" pagination={false} size="small" />
                    ) : (
                      <Empty description="暂无因子分析数据，请点击执行分析" />
                    )}
                  </Card>
                </TabPane>

                {/* 归因分析 */}
                <TabPane tab={<span><FundOutlined /> 归因分析</span>} key="attribution">
                  <Card size="small" extra={<Button type="primary" size="small" onClick={runAttribution}>执行分析</Button>}>
                    {selectedResult.attribution ? (
                      <>
                        <Row gutter={16} style={{ marginBottom: 16 }}>
                          <Col span={6}><Statistic title="总收益" value={selectedResult.attribution.total_return} suffix="%" valueStyle={{ color: '#ff4d4f' }} /></Col>
                          <Col span={6}><Statistic title="基准收益" value={selectedResult.attribution.benchmark_return} suffix="%" /></Col>
                          <Col span={6}><Statistic title="主动收益" value={selectedResult.attribution.active_return} suffix="%" valueStyle={{ color: '#52c41a' }} /></Col>
                          <Col span={6}><Statistic title="配置效应" value={selectedResult.attribution.allocation_effect} suffix="%" /></Col>
                        </Row>
                        <Row gutter={16}>
                          <Col span={6}><Statistic title="选股效应" value={selectedResult.attribution.selection_effect} suffix="%" valueStyle={{ color: '#52c41a' }} /></Col>
                          <Col span={6}><Statistic title="交互效应" value={selectedResult.attribution.interaction_effect} suffix="%" /></Col>
                          <Col span={6}><Statistic title="择时效应" value={selectedResult.attribution.timing_effect} suffix="%" /></Col>
                        </Row>
                        <Divider />
                        <Descriptions column={2} size="small">
                          <Descriptions.Item label="配置效应说明">行业/资产配置带来的超额收益</Descriptions.Item>
                          <Descriptions.Item label="选股效应说明">行业内选股能力带来的超额收益</Descriptions.Item>
                        </Descriptions>
                      </>
                    ) : (
                      <Empty description="暂无归因分析数据，请点击执行分析" />
                    )}
                  </Card>
                </TabPane>

                {/* 历史记录 */}
                <TabPane tab={<span><BarChartOutlined /> 历史记录</span>} key="history">
                  <Table columns={resultColumns} dataSource={results} rowKey="backtest_id" pagination={{ pageSize: 5 }} size="small"
                    locale={{ emptyText: <Empty description="暂无回测记录" /> }}
                  />
                </TabPane>
              </Tabs>
            ) : (
              <Card>
                <Empty description="请选择一个回测结果查看详情，或运行新的回测" />
              </Card>
            )}
          </Spin>
        </Col>
      </Row>
    </div>
  );
};

export default Backtest;
