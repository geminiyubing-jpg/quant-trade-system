/**
 * Portfolio Page - 投资组合管理页面
 *
 * 功能：
 * - 组合管理
 * - 持仓管理
 * - 风险度量 (VaR, CVaR, 集中度, 相关性)
 * - 组合优化 (均值方差, 风险平价, 最大夏普)
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card, Tabs, Table, Button, Tag, Space, Statistic, Row, Col,
  Select, Form, InputNumber, message, Modal, Progress, Descriptions,
  Divider, Typography, Empty, Spin, Tooltip,
  Input, Alert
} from 'antd';
import {
  PieChartOutlined, PlusOutlined, SafetyOutlined,
  ThunderboltOutlined,
  FileTextOutlined, HistoryOutlined, CalculatorOutlined,
  ReloadOutlined, LineChartOutlined, TrophyOutlined, RiseOutlined, FallOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

// 导入服务和类型
import portfolioService from '../services/portfolio';
import type {
  Portfolio,
  PortfolioCreate,
  PortfolioPosition,
  RiskMetrics,
  OptimizationResult,
  OptimizationMethod,
  PerformanceMetrics,
} from '../types/portfolio';

const { TabPane } = Tabs;
const { Option } = Select;
const { Text, Title } = Typography;

const PortfolioPage: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [optimizations, setOptimizations] = useState<OptimizationResult[]>([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [optimizeModalVisible, setOptimizeModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();
  const [optimizeForm] = Form.useForm();

  // 绩效分析状态
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [performanceLoading, setPerformanceLoading] = useState(false);
  const [performanceDateRange] = useState({
    start_date: dayjs().subtract(1, 'year').format('YYYY-MM-DD'),
    end_date: dayjs().format('YYYY-MM-DD'),
  });

  // 加载投资组合列表
  const loadPortfolios = useCallback(async () => {
    setLoading(true);
    try {
      const res = await portfolioService.listPortfolios();
      setPortfolios(res.items || []);
      if (res.items && res.items.length > 0 && !selectedPortfolio) {
        setSelectedPortfolio(res.items[0]);
      }
    } catch (error) {
      console.error('加载投资组合失败:', error);
      setPortfolios([]);
    } finally {
      setLoading(false);
    }
  }, [selectedPortfolio]);

  // 加载选中组合的详细数据
  const loadPortfolioDetails = useCallback(async () => {
    if (!selectedPortfolio) return;

    setLoading(true);
    try {
      const [positionsRes, riskRes, optRes] = await Promise.allSettled([
        portfolioService.getPositions(selectedPortfolio.id),
        portfolioService.getRiskMetrics(selectedPortfolio.id),
        portfolioService.getOptimizationHistory(selectedPortfolio.id),
      ]);

      if (positionsRes.status === 'fulfilled') {
        setPositions(positionsRes.value.items || []);
      } else {
        console.error('加载持仓失败:', positionsRes.reason);
        setPositions([]);
      }

      if (riskRes.status === 'fulfilled') {
        setRiskMetrics(riskRes.value);
      } else {
        console.error('加载风险指标失败:', riskRes.reason);
        setRiskMetrics(null);
      }

      if (optRes.status === 'fulfilled') {
        setOptimizations(optRes.value.items || []);
      } else {
        console.error('加载优化历史失败:', optRes.reason);
        setOptimizations([]);
      }
    } catch (error) {
      console.error('加载组合详情失败:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedPortfolio]);

  useEffect(() => {
    loadPortfolios();
  }, [loadPortfolios]);

  useEffect(() => {
    if (selectedPortfolio) {
      loadPortfolioDetails();
    }
  }, [selectedPortfolio, loadPortfolioDetails]);

  // 加载绩效分析数据
  const loadPerformanceMetrics = useCallback(async () => {
    if (!selectedPortfolio) return;

    setPerformanceLoading(true);
    try {
      const metrics = await portfolioService.getPerformanceMetrics(
        selectedPortfolio.id,
        performanceDateRange.start_date,
        performanceDateRange.end_date
      );
      setPerformanceMetrics(metrics);
    } catch (error) {
      console.error('加载绩效数据失败:', error);
      setPerformanceMetrics(null);
    } finally {
      setPerformanceLoading(false);
    }
  }, [selectedPortfolio, performanceDateRange]);

  useEffect(() => {
    if (activeTab === 'performance' && selectedPortfolio) {
      loadPerformanceMetrics();
    }
  }, [activeTab, selectedPortfolio, loadPerformanceMetrics]);

  // 当前组合的持仓
  const portfolioPositions = useMemo(() =>
    positions.filter(p => p.portfolio_id === selectedPortfolio?.id),
    [positions, selectedPortfolio]
  );

  // 创建组合
  const handleCreatePortfolio = async (values: PortfolioCreate) => {
    setSubmitting(true);
    try {
      await portfolioService.createPortfolio(values);
      message.success('组合创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      loadPortfolios();
    } catch (error) {
      console.error('创建组合失败:', error);
    } finally {
      setSubmitting(false);
    }
  };

  // 执行优化
  const handleOptimize = async (values: { method: OptimizationMethod; max_weight?: number; min_weight?: number }) => {
    if (!selectedPortfolio) return;

    setSubmitting(true);
    try {
      await portfolioService.optimizePortfolio(selectedPortfolio.id, {
        method: values.method,
        constraints: {
          max_weight: values.max_weight,
          min_weight: values.min_weight,
        },
      });
      message.success('组合优化完成');
      setOptimizeModalVisible(false);
      loadPortfolioDetails();
    } catch (error) {
      console.error('优化失败:', error);
    } finally {
      setSubmitting(false);
    }
  };

  // 应用优化方案
  const handleApplyOptimization = (_optId: string) => {
    Modal.confirm({
      title: '应用优化方案',
      content: '确定要应用此优化方案吗？将生成相应的调仓订单。',
      onOk: async () => {
        try {
          if (selectedPortfolio) {
            await portfolioService.rebalancePortfolio(selectedPortfolio.id);
            message.success('优化方案已应用，调仓订单已生成');
            loadPortfolioDetails();
          }
        } catch (error) {
          console.error('应用优化失败:', error);
        }
      },
    });
  };

  // 持仓表格列
  const positionColumns: ColumnsType<PortfolioPosition> = [
    { title: '股票代码', dataIndex: 'symbol', key: 'symbol' },
    { title: '持仓数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '成本价', dataIndex: 'avg_cost', key: 'avg_cost', render: (v) => `¥${Number(v).toFixed(2)}` },
    { title: '现价', dataIndex: 'current_price', key: 'current_price', render: (v) => v ? `¥${Number(v).toFixed(2)}` : '-' },
    { title: '市值', dataIndex: 'market_value', key: 'market_value', render: (v) => v ? `¥${Number(v).toLocaleString()}` : '-' },
    {
      title: '权重', dataIndex: 'weight', key: 'weight',
      render: (v, r) => (
        <Tooltip title={`目标权重: ${((r.target_weight || 0) * 100).toFixed(1)}%`}>
          <Progress
            percent={(v || 0) * 100}
            size="small"
            style={{ width: 80 }}
            strokeColor={Math.abs((v || 0) - (r.target_weight || 0)) > 0.05 ? '#faad14' : '#52c41a'}
          />
        </Tooltip>
      )
    },
    { title: '行业', dataIndex: 'sector', key: 'sector', render: (v) => v ? <Tag>{v}</Tag> : '-' },
    {
      title: '浮动盈亏', dataIndex: 'unrealized_pnl', key: 'unrealized_pnl',
      render: (v) => v !== undefined && v !== null
        ? <span style={{ color: v >= 0 ? '#ff4d4f' : '#52c41a' }}>{v >= 0 ? '+' : ''}¥{Number(v).toLocaleString()}</span>
        : '-'
    },
  ];

  // 优化记录表格列
  const optColumns: ColumnsType<OptimizationResult> = [
    {
      title: '优化方法', dataIndex: 'optimization_method', key: 'optimization_method',
      render: (v) => {
        const map: Record<string, string> = {
          MEAN_VARIANCE: '均值方差',
          RISK_PARITY: '风险平价',
          MIN_VARIANCE: '最小方差',
          MAX_SHARPE: '最大夏普',
          EQUAL_WEIGHT: '等权重',
          BLACK_LITTERMAN: 'Black-Litterman',
        };
        return <Tag color="blue">{map[v] || v}</Tag>;
      }
    },
    { title: '预期收益', dataIndex: 'expected_return', key: 'expected_return', render: (v) => v !== undefined ? `${Number(v).toFixed(1)}%` : '-' },
    { title: '预期风险', dataIndex: 'expected_risk', key: 'expected_risk', render: (v) => v !== undefined ? `${Number(v).toFixed(1)}%` : '-' },
    { title: '预期夏普', dataIndex: 'expected_sharpe', key: 'expected_sharpe', render: (v) => v !== undefined ? Number(v).toFixed(2) : '-' },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (v) => {
        const map: Record<string, { color: string; text: string }> = {
          PENDING: { color: 'orange', text: '待应用' },
          APPLIED: { color: 'green', text: '已应用' },
          REJECTED: { color: 'red', text: '已拒绝' },
        };
        const s = map[v] || { color: 'default', text: v };
        return <Tag color={s.color}>{s.text}</Tag>;
      }
    },
    {
      title: '操作', key: 'action',
      render: (_, r) => r.status === 'PENDING' && (
        <Space>
          <Button type="link" size="small" onClick={() => handleApplyOptimization(r.id)}>应用</Button>
          <Button type="link" size="small">详情</Button>
        </Space>
      )
    },
  ];

  // 计算行业分布
  const sectorDistribution = useMemo(() => {
    const sectors: Record<string, number> = {};
    portfolioPositions.forEach(p => {
      if (p.sector) {
        sectors[p.sector] = (sectors[p.sector] || 0) + (p.weight || 0);
      }
    });
    return Object.entries(sectors).sort((a, b) => b[1] - a[1]);
  }, [portfolioPositions]);

  const sectorColors = ['#1890ff', '#52c41a', '#722ed1', '#fa8c16', '#eb2f96', '#13c2c2'];

  if (portfolios.length === 0 && !loading) {
    return (
      <div className="portfolio-page">
        <div style={{ marginBottom: 24 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={3} style={{ margin: 0 }}><PieChartOutlined style={{ marginRight: 8, color: 'var(--bb-accent-primary)' }} />投资组合</Title>
              <Text type="secondary">组合管理 · 风险度量 · 组合优化</Text>
            </Col>
            <Col>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>创建组合</Button>
            </Col>
          </Row>
        </div>
        <Card>
          <Empty description="暂无投资组合，请先创建一个组合">
            <Button type="primary" onClick={() => setCreateModalVisible(true)}>创建组合</Button>
          </Empty>
        </Card>

        {/* 创建组合弹窗 */}
        <Modal
          title="创建投资组合"
          open={createModalVisible}
          onCancel={() => setCreateModalVisible(false)}
          onOk={() => form.submit()}
          confirmLoading={submitting}
          width={600}
        >
          <Form form={form} layout="vertical" onFinish={handleCreatePortfolio}>
            <Form.Item label="组合名称" name="name" rules={[{ required: true, message: '请输入组合名称' }]}>
              <Input placeholder="例如：核心价值组合" />
            </Form.Item>
            <Form.Item label="组合描述" name="description">
              <Input.TextArea rows={2} />
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="基准指数" name="benchmark_symbol">
                  <Select placeholder="请选择">
                    <Option value="000300.SH">沪深300</Option>
                    <Option value="000905.SH">中证500</Option>
                    <Option value="399006.SZ">创业板指</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="初始资金" name="initial_capital">
                  <InputNumber style={{ width: '100%' }} min={10000} placeholder="10000" />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Modal>
      </div>
    );
  }

  return (
    <div className="portfolio-page">
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}><PieChartOutlined style={{ marginRight: 8, color: 'var(--bb-accent-primary)' }} />投资组合</Title>
            <Text type="secondary">组合管理 · 风险度量 · 组合优化</Text>
          </Col>
          <Col>
            <Space>
              <Select
                value={selectedPortfolio?.id}
                onChange={(v) => setSelectedPortfolio(portfolios.find(p => p.id === v) || null)}
                style={{ width: 200 }}
                placeholder="选择组合"
              >
                {portfolios.map(p => <Option key={p.id} value={p.id}>{p.name}</Option>)}
              </Select>
              <Button icon={<ReloadOutlined />} onClick={loadPortfolioDetails} loading={loading}>刷新</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>创建组合</Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* 组合概览 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={4}><Statistic title="组合名称" value={selectedPortfolio?.name || '-'} valueStyle={{ fontSize: 16 }} /></Col>
          <Col span={4}><Statistic title="总市值" value={selectedPortfolio?.total_value || 0} prefix="¥" /></Col>
          <Col span={4}><Statistic title="现金余额" value={selectedPortfolio?.cash_balance || 0} prefix="¥" /></Col>
          <Col span={4}>
            <Statistic
              title="状态"
              value={selectedPortfolio?.status === 'ACTIVE' ? '活跃' : selectedPortfolio?.status === 'PAUSED' ? '暂停' : '已关闭'}
              valueStyle={{ color: selectedPortfolio?.status === 'ACTIVE' ? '#52c41a' : selectedPortfolio?.status === 'PAUSED' ? '#faad14' : '#999' }}
            />
          </Col>
          <Col span={4}><Statistic title="基准指数" value={selectedPortfolio?.benchmark_symbol || '-'} /></Col>
          <Col span={4}><Statistic title="成立日期" value={selectedPortfolio?.inception_date ? dayjs(selectedPortfolio.inception_date).format('YYYY-MM-DD') : '-'} /></Col>
        </Row>
      </Card>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 概览 */}
        <TabPane tab={<span><FileTextOutlined /> 概览</span>} key="overview">
          <Row gutter={16}>
            <Col span={16}>
              <Card title="持仓列表" extra={<Button type="link">导出</Button>}>
                <Spin spinning={loading}>
                  <Table
                    columns={positionColumns}
                    dataSource={portfolioPositions}
                    rowKey="id"
                    pagination={false}
                    locale={{ emptyText: <Empty description="暂无持仓数据" /> }}
                  />
                </Spin>
              </Card>
            </Col>
            <Col span={8}>
              <Card title="行业分布">
                {sectorDistribution.length > 0 ? (
                  sectorDistribution.map(([sector, weight], i) => (
                    <div key={sector} style={{ marginBottom: 12 }}>
                      <Text>{sector}</Text>
                      <Progress
                        percent={weight * 100}
                        size="small"
                        strokeColor={sectorColors[i % sectorColors.length]}
                      />
                    </div>
                  ))
                ) : (
                  <Empty description="暂无行业数据" />
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* 风险分析 */}
        <TabPane tab={<span><SafetyOutlined /> 风险分析</span>} key="risk">
          <Spin spinning={loading}>
            <Alert message="风险指标每日更新，基于历史数据计算，仅供参考" type="info" showIcon style={{ marginBottom: 16 }} />
            {riskMetrics ? (
              <Row gutter={[16, 16]}>
                {/* VaR 指标 */}
                <Col span={24}>
                  <Card title="VaR 风险价值" size="small">
                    <Row gutter={16}>
                      <Col span={6}>
                        <Statistic title="95% VaR" value={riskMetrics.var_95 || 0} suffix="%" valueStyle={{ color: '#faad14' }}
                          prefix={<Tooltip title="95%置信度下，单日最大预期损失"><SafetyOutlined /></Tooltip>} />
                      </Col>
                      <Col span={6}>
                        <Statistic title="99% VaR" value={riskMetrics.var_99 || 0} suffix="%" valueStyle={{ color: '#ff4d4f' }} />
                      </Col>
                      <Col span={6}>
                        <Statistic title="95% CVaR" value={riskMetrics.cvar_95 || 0} suffix="%" valueStyle={{ color: '#ff4d4f' }}
                          prefix={<Tooltip title="条件VaR，损失超过VaR时的平均损失"><SafetyOutlined /></Tooltip>} />
                      </Col>
                      <Col span={6}>
                        <Statistic title="组合波动率" value={riskMetrics.portfolio_volatility || 0} suffix="%" />
                      </Col>
                    </Row>
                  </Card>
                </Col>

                {/* 集中度风险 */}
                <Col span={12}>
                  <Card title="集中度风险" size="small">
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="赫芬达尔指数">{(riskMetrics.herfindahl_index || 0).toFixed(3)} <Text type="secondary">(1/N=完全分散)</Text></Descriptions.Item>
                      <Descriptions.Item label="最大单只权重">{((riskMetrics.max_single_weight || 0) * 100).toFixed(1)}%</Descriptions.Item>
                      <Descriptions.Item label="前5大权重">{((riskMetrics.top_5_weight || 0) * 100).toFixed(1)}%</Descriptions.Item>
                    </Descriptions>
                  </Card>
                </Col>

                {/* 其他风险指标 */}
                <Col span={12}>
                  <Card title="其他风险指标" size="small">
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="分散化比率">{(riskMetrics.diversification_ratio || 0).toFixed(2)}</Descriptions.Item>
                      <Descriptions.Item label="Beta">{(riskMetrics.beta_to_benchmark || 0).toFixed(2)}</Descriptions.Item>
                      <Descriptions.Item label="最大回撤">{(riskMetrics.max_drawdown || 0).toFixed(1)}%</Descriptions.Item>
                    </Descriptions>
                  </Card>
                </Col>
              </Row>
            ) : (
              <Card>
                <Empty description="暂无风险指标数据" />
              </Card>
            )}
          </Spin>
        </TabPane>

        {/* 组合优化 */}
        <TabPane tab={<span><ThunderboltOutlined /> 组合优化</span>} key="optimization">
          <Card extra={<Button type="primary" icon={<CalculatorOutlined />} onClick={() => setOptimizeModalVisible(true)}>执行优化</Button>}>
            <Spin spinning={loading}>
              <Table
                columns={optColumns}
                dataSource={optimizations}
                rowKey="id"
                pagination={false}
                locale={{ emptyText: <Empty description="暂无优化记录" /> }}
              />
            </Spin>
          </Card>
        </TabPane>

        {/* 优化历史 */}
        <TabPane tab={<span><HistoryOutlined /> 优化历史</span>} key="history">
          <Card>
            <Spin spinning={loading}>
              <Table
                columns={optColumns}
                dataSource={optimizations}
                rowKey="id"
                locale={{ emptyText: <Empty description="暂无优化历史" /> }}
              />
            </Spin>
          </Card>
        </TabPane>

        {/* 绩效分析 */}
        <TabPane tab={<span><LineChartOutlined /> 绩效分析</span>} key="performance">
          <Spin spinning={performanceLoading}>
            <Alert
              message="绩效指标基于历史数据计算，仅供参考，不构成投资建议"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            {performanceMetrics ? (
              <Row gutter={[16, 16]}>
                {/* 收益指标 */}
                <Col span={24}>
                  <Card title="收益指标" size="small" extra={<TrophyOutlined style={{ color: '#faad14' }} />}>
                    <Row gutter={16}>
                      <Col span={6}>
                        <Statistic
                          title="总收益率"
                          value={performanceMetrics.total_return || 0}
                          suffix="%"
                          valueStyle={{ color: (performanceMetrics.total_return || 0) >= 0 ? '#ff4d4f' : '#52c41a', fontSize: 24 }}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="年化收益"
                          value={performanceMetrics.annualized_return || 0}
                          suffix="%"
                          valueStyle={{ color: (performanceMetrics.annualized_return || 0) >= 0 ? '#ff4d4f' : '#52c41a' }}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="基准收益"
                          value={performanceMetrics.benchmark_return || 0}
                          suffix="%"
                          prefix={(performanceMetrics.benchmark_return || 0) >= (performanceMetrics.annualized_return || 0) ? <FallOutlined /> : <RiseOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="超额收益"
                          value={((performanceMetrics.annualized_return || 0) - (performanceMetrics.benchmark_return || 0))}
                          suffix="%"
                          valueStyle={{ color: ((performanceMetrics.annualized_return || 0) - (performanceMetrics.benchmark_return || 0)) >= 0 ? '#ff4d4f' : '#52c41a' }}
                        />
                      </Col>
                    </Row>
                  </Card>
                </Col>

                {/* 风险调整收益 */}
                <Col span={24}>
                  <Card title="风险调整收益" size="small">
                    <Row gutter={16}>
                      <Col span={4}>
                        <Statistic
                          title="夏普比率"
                          value={performanceMetrics.sharpe_ratio || 0}
                          precision={2}
                          valueStyle={{ color: (performanceMetrics.sharpe_ratio || 0) >= 1 ? '#52c41a' : (performanceMetrics.sharpe_ratio || 0) >= 0.5 ? '#faad14' : '#ff4d4f' }}
                        />
                      </Col>
                      <Col span={4}>
                        <Statistic title="索提诺比率" value={performanceMetrics.sortino_ratio || 0} precision={2} />
                      </Col>
                      <Col span={4}>
                        <Statistic title="卡尔马比率" value={performanceMetrics.calmar_ratio || 0} precision={2} />
                      </Col>
                      <Col span={4}>
                        <Statistic title="信息比率" value={performanceMetrics.information_ratio || 0} precision={2} />
                      </Col>
                      <Col span={4}>
                        <Statistic title="特雷诺比率" value={performanceMetrics.treynor_ratio || 0} precision={2} />
                      </Col>
                      <Col span={4}>
                        <Statistic
                          title="Alpha"
                          value={performanceMetrics.alpha || 0}
                          suffix="%"
                          valueStyle={{ color: (performanceMetrics.alpha || 0) >= 0 ? '#ff4d4f' : '#52c41a' }}
                        />
                      </Col>
                    </Row>
                  </Card>
                </Col>

                {/* 风险指标 */}
                <Col span={12}>
                  <Card title="风险指标" size="small">
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="年化波动率">{(performanceMetrics.annualized_volatility || 0).toFixed(2)}%</Descriptions.Item>
                      <Descriptions.Item label="下行波动率">{(performanceMetrics.downside_volatility || 0).toFixed(2)}%</Descriptions.Item>
                      <Descriptions.Item label="最大回撤">
                        <Text type="danger">{(performanceMetrics.max_drawdown || 0).toFixed(2)}%</Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="Beta">{(performanceMetrics.beta || 0).toFixed(2)}</Descriptions.Item>
                    </Descriptions>
                  </Card>
                </Col>

                {/* 交易统计 */}
                <Col span={12}>
                  <Card title="交易统计" size="small">
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="胜率">{((performanceMetrics.win_rate || 0) * 100).toFixed(1)}%</Descriptions.Item>
                      <Descriptions.Item label="盈亏比">{(performanceMetrics.profit_loss_ratio || 0).toFixed(2)}</Descriptions.Item>
                      <Descriptions.Item label="分析区间">
                        {performanceDateRange.start_date} ~ {performanceDateRange.end_date}
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>
                </Col>
              </Row>
            ) : (
              <Card>
                <Empty description="暂无绩效数据，请选择分析区间后点击刷新" />
              </Card>
            )}
          </Spin>
        </TabPane>
      </Tabs>

      {/* 创建组合弹窗 */}
      <Modal
        title="创建投资组合"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={submitting}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreatePortfolio}>
          <Form.Item label="组合名称" name="name" rules={[{ required: true, message: '请输入组合名称' }]}>
            <Input placeholder="例如：核心价值组合" />
          </Form.Item>
          <Form.Item label="组合描述" name="description">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="基准指数" name="benchmark_symbol">
                <Select placeholder="请选择">
                  <Option value="000300.SH">沪深300</Option>
                  <Option value="000905.SH">中证500</Option>
                  <Option value="399006.SZ">创业板指</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="初始资金" name="initial_capital">
                <InputNumber style={{ width: '100%' }} min={10000} placeholder="10000" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 执行优化弹窗 */}
      <Modal
        title="执行组合优化"
        open={optimizeModalVisible}
        onCancel={() => setOptimizeModalVisible(false)}
        onOk={() => optimizeForm.submit()}
        confirmLoading={submitting}
        width={600}
      >
        <Form form={optimizeForm} layout="vertical" onFinish={handleOptimize}>
          <Form.Item label="优化方法" name="method" rules={[{ required: true }]} initialValue="MEAN_VARIANCE">
            <Select>
              <Option value="MEAN_VARIANCE">均值方差优化</Option>
              <Option value="RISK_PARITY">风险平价</Option>
              <Option value="MIN_VARIANCE">最小方差</Option>
              <Option value="MAX_SHARPE">最大夏普比率</Option>
              <Option value="EQUAL_WEIGHT">等权重</Option>
            </Select>
          </Form.Item>
          <Divider>约束条件</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="单只最大权重" name="max_weight" initialValue={0.2}>
                <InputNumber min={0.01} max={1} step={0.05} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="单只最小权重" name="min_weight" initialValue={0}>
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Alert message="优化将基于历史数据计算最优权重配置，结果仅供参考" type="info" showIcon />
        </Form>
      </Modal>
    </div>
  );
};

export default PortfolioPage;
