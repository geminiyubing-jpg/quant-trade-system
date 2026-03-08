/**
 * Trading Page - 交易页面
 *
 * 功能：
 * - 显示订单列表（支持按模式过滤）
 * - 显示持仓列表（支持按模式过滤）
 * - 显示持仓汇总统计
 * - 创建订单表单
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Tag,
  Space,
  Statistic,
  Row,
  Col,
  Select,
  Form,
  InputNumber,
  message,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  SwapOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useTradingMode } from '../contexts/TradingModeContext';
import type { TradingMode } from '../contexts/TradingModeContext';

const { TabPane } = Tabs;
const { Option } = Select;

// 订单数据类型（模拟）
interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: 'PENDING' | 'PARTIAL' | 'FILLED' | 'CANCELED' | 'REJECTED';
  execution_mode: TradingMode;
  order_time: string;
}

// 持仓数据类型（模拟）
interface Position {
  id: string;
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  execution_mode: TradingMode;
}

// 持仓汇总类型
interface PositionSummary {
  total_market_value: number;
  total_unrealized_pnl: number;
  total_realized_pnl: number;
  position_count: number;
}

const Trading: React.FC = () => {
  const { t } = useTranslation();
  const { mode, isPaperTrading } = useTradingMode();

  // 状态
  const [activeTab, setActiveTab] = useState('orders');
  const [orderFilter, setOrderFilter] = useState<TradingMode | 'ALL'>(mode);
  const [positionFilter, setPositionFilter] = useState<TradingMode>(mode);
  const [orders, setOrders] = useState<Order[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [summary, setSummary] = useState<PositionSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [createOrderVisible, setCreateOrderVisible] = useState(false);

  // 表单实例
  const [form] = Form.useForm();

  // 加载数据
  useEffect(() => {
    loadData();
  }, [orderFilter, positionFilter]);

  // 模式切换时同步更新过滤器
  useEffect(() => {
    setOrderFilter(mode);
    setPositionFilter(mode);
  }, [mode]);

  const loadData = async () => {
    setLoading(true);
    try {
      // TODO: 替换为真实 API 调用
      // const ordersData = await tradingApi.getOrders(orderFilter);
      // const positionsData = await tradingApi.getPositions(positionFilter);
      // const summaryData = await tradingApi.getPositionSummary(positionFilter);

      // 模拟数据
      const mockOrders = generateMockOrders(orderFilter);
      const mockPositions = generateMockPositions(positionFilter);
      const mockSummary = generateMockSummary(positionFilter);

      setOrders(mockOrders);
      setPositions(mockPositions);
      setSummary(mockSummary);
    } catch (error) {
      message.error('加载数据失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 创建订单
  const handleCreateOrder = async (_values: any) => {
    try {
      // TODO: 调用真实 API
      // await tradingApi.createOrder({
      //   ...values,
      //   execution_mode: mode,
      // });

      message.success('订单创建成功');
      setCreateOrderVisible(false);
      form.resetFields();
      loadData();
    } catch (error) {
      message.error('订单创建失败');
    }
  };

  // 订单表格列
  const orderColumns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'BUY' ? 'green' : 'red'}>
          {side === 'BUY' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          PENDING: 'blue',
          PARTIAL: 'orange',
          FILLED: 'green',
          CANCELED: 'default',
          REJECTED: 'red',
        };
        const labelMap: Record<string, string> = {
          PENDING: '待成交',
          PARTIAL: '部分成交',
          FILLED: '已成交',
          CANCELED: '已撤销',
          REJECTED: '已拒绝',
        };
        return <Tag color={colorMap[status]}>{labelMap[status]}</Tag>;
      },
    },
    {
      title: '模式',
      dataIndex: 'execution_mode',
      key: 'execution_mode',
      render: (execMode: TradingMode) => (
        <Tag color={execMode === 'PAPER' ? 'green' : 'red'}>
          {execMode === 'PAPER' ? '🧪 模拟' : '⚡ 实盘'}
        </Tag>
      ),
    },
    {
      title: '下单时间',
      dataIndex: 'order_time',
      key: 'order_time',
    },
  ];

  // 持仓表格列
  const positionColumns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '持仓数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '成本价',
      dataIndex: 'avg_price',
      key: 'avg_price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '现价',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '市值',
      dataIndex: 'market_value',
      key: 'market_value',
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
    {
      title: '浮动盈亏',
      dataIndex: 'unrealized_pnl',
      key: 'unrealized_pnl',
      render: (pnl: number) => (
        <span style={{ color: pnl >= 0 ? '#ff4d4f' : '#52c41a' }}>
          {pnl >= 0 ? '+' : ''}¥{pnl.toFixed(2)}
        </span>
      ),
    },
    {
      title: '模式',
      dataIndex: 'execution_mode',
      key: 'execution_mode',
      render: (execMode: TradingMode) => (
        <Tag color={execMode === 'PAPER' ? 'green' : 'red'}>
          {execMode === 'PAPER' ? '🧪 模拟' : '⚡ 实盘'}
        </Tag>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h1>{t('trading.title')}</h1>
        <Space>
          <span>当前模式：</span>
          <Tag color={isPaperTrading ? 'green' : 'red'} style={{ fontSize: 14 }}>
            {isPaperTrading ? '🧪 模拟交易' : '⚡ 实盘交易'}
          </Tag>
        </Space>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 订单管理 */}
        <TabPane tab="订单管理" key="orders">
          <Card>
            <Space style={{ marginBottom: 16 }}>
              <span>模式过滤：</span>
              <Select
                value={orderFilter}
                onChange={setOrderFilter}
                style={{ width: 150 }}
              >
                <Option value="ALL">全部</Option>
                <Option value="PAPER">🧜 模拟交易</Option>
                <Option value="LIVE">⚡ 实盘交易</Option>
              </Select>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOrderVisible(true)}>
                创建订单
              </Button>
              <Button icon={<SwapOutlined />} onClick={loadData}>
                刷新
              </Button>
            </Space>

            <Spin spinning={loading}>
              <Table
                columns={orderColumns}
                dataSource={orders}
                rowKey="id"
                pagination={{ pageSize: 10 }}
              />
            </Spin>
          </Card>
        </TabPane>

        {/* 持仓管理 */}
        <TabPane tab="持仓管理" key="positions">
          <Card>
            <Space style={{ marginBottom: 16 }}>
              <span>模式过滤：</span>
              <Select
                value={positionFilter}
                onChange={setPositionFilter}
                style={{ width: 150 }}
              >
                <Option value="PAPER">🧜 模拟交易</Option>
                <Option value="LIVE">⚡ 实盘交易</Option>
              </Select>
              <Button icon={<SwapOutlined />} onClick={loadData}>
                刷新
              </Button>
            </Space>

            {summary && (
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                  <Statistic
                    title="总市值"
                    value={summary.total_market_value}
                    precision={2}
                    prefix="¥"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="浮动盈亏"
                    value={summary.total_unrealized_pnl}
                    precision={2}
                    prefix="¥"
                    valueStyle={{ color: summary.total_unrealized_pnl >= 0 ? '#ff4d4f' : '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="已实现盈亏"
                    value={summary.total_realized_pnl}
                    precision={2}
                    prefix="¥"
                    valueStyle={{ color: summary.total_realized_pnl >= 0 ? '#ff4d4f' : '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="持仓数量"
                    value={summary.position_count}
                    suffix="只"
                  />
                </Col>
              </Row>
            )}

            <Spin spinning={loading}>
              <Table
                columns={positionColumns}
                dataSource={positions}
                rowKey="id"
                pagination={{ pageSize: 10 }}
              />
            </Spin>
          </Card>
        </TabPane>
      </Tabs>

      {/* 创建订单对话框 */}
      {createOrderVisible && (
        <Card
          title="创建订单"
          style={{ marginTop: 16 }}
          extra={
            <Button onClick={() => setCreateOrderVisible(false)}>关闭</Button>
          }
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreateOrder}
          >
            <Form.Item
              label="股票代码"
              name="symbol"
              rules={[{ required: true, message: '请输入股票代码' }]}
            >
              <input placeholder="例如: 000001" />
            </Form.Item>

            <Form.Item
              label="交易方向"
              name="side"
              rules={[{ required: true, message: '请选择交易方向' }]}
            >
              <Select>
                <Option value="BUY">买入</Option>
                <Option value="SELL">卖出</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="数量"
              name="quantity"
              rules={[{ required: true, message: '请输入数量' }]}
            >
              <InputNumber min={100} step={100} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="价格"
              name="price"
              rules={[{ required: true, message: '请输入价格' }]}
            >
              <InputNumber min={0} step={0.01} precision={2} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit">
                  提交订单
                </Button>
                <Button onClick={() => form.resetFields()}>
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      )}
    </div>
  );
};

// 生成模拟订单数据
const generateMockOrders = (filter: TradingMode | 'ALL'): Order[] => {
  const allOrders: Order[] = [
    {
      id: '1',
      symbol: '000001',
      side: 'BUY',
      quantity: 1000,
      price: 15.50,
      status: 'FILLED',
      execution_mode: 'PAPER',
      order_time: '2026-03-08 10:30:00',
    },
    {
      id: '2',
      symbol: '000002',
      side: 'SELL',
      quantity: 500,
      price: 20.30,
      status: 'PENDING',
      execution_mode: 'PAPER',
      order_time: '2026-03-08 11:00:00',
    },
    {
      id: '3',
      symbol: '600000',
      side: 'BUY',
      quantity: 2000,
      price: 8.80,
      status: 'PARTIAL',
      execution_mode: 'LIVE',
      order_time: '2026-03-08 13:15:00',
    },
  ];

  if (filter === 'ALL') return allOrders;
  return allOrders.filter((o) => o.execution_mode === filter);
};

// 生成模拟持仓数据
const generateMockPositions = (filter: TradingMode): Position[] => {
  const allPositions: Position[] = [
    {
      id: '1',
      symbol: '000001',
      quantity: 1000,
      avg_price: 15.00,
      current_price: 15.50,
      market_value: 15500,
      unrealized_pnl: 500,
      execution_mode: 'PAPER',
    },
    {
      id: '2',
      symbol: '600000',
      quantity: 2000,
      avg_price: 8.50,
      current_price: 8.80,
      market_value: 17600,
      unrealized_pnl: 600,
      execution_mode: 'LIVE',
    },
  ];

  return allPositions.filter((p) => p.execution_mode === filter);
};

// 生成模拟汇总数据
const generateMockSummary = (filter: TradingMode): PositionSummary => {
  const summaries: Record<TradingMode, PositionSummary> = {
    PAPER: {
      total_market_value: 15500,
      total_unrealized_pnl: 500,
      total_realized_pnl: 1200,
      position_count: 1,
    },
    LIVE: {
      total_market_value: 17600,
      total_unrealized_pnl: 600,
      total_realized_pnl: 800,
      position_count: 1,
    },
  };

  return summaries[filter];
};

export default Trading;
