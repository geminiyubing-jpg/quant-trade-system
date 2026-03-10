/**
 * Trading Page - 交易页面 (增强版)
 *
 * 功能：
 * - 订单管理
 * - 成交记录
 * - 交易日历
 * - 交易统计
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Tabs, Table, Button, Tag, Space, Statistic, Row, Col,
  Select, Form, InputNumber, message, Spin, Modal, Calendar,
  Badge, Descriptions, Divider, Typography,
  Empty
} from 'antd';
import {
  PlusOutlined, SwapOutlined, CheckCircleOutlined,
  CalendarOutlined, BarChartOutlined, FileTextOutlined, ThunderboltOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useTradingMode } from '../contexts/TradingModeContext';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';

// 导入服务
import tradingService from '../services/trading';
import fillsService from '../services/fills';
import { get } from '../services/api';

// 导入类型
import type {
  Order,
  OrderCreate,
  Position,
  Fill,
  ExecutionMode,
} from '../types/trading';

const { TabPane } = Tabs;
const { Option } = Select;
const { Text, Title } = Typography;

// 交易日历
interface TradingDay {
  date: string;
  is_trading_day: boolean;
  is_half_day: boolean;
  open_time?: string;
  close_time?: string;
  holiday_name?: string;
}

// 交易统计
interface DailyStats {
  date: string;
  total_orders: number;
  filled_orders: number;
  buy_count: number;
  sell_count: number;
  buy_amount: number;
  sell_amount: number;
  total_commission: number;
  total_stamp_duty: number;
  realized_pnl: number;
  daily_pnl: number;
}

const Trading: React.FC = () => {
  useTranslation();
  const { mode, isPaperTrading } = useTradingMode();

  const [activeTab, setActiveTab] = useState('orders');
  const [orders, setOrders] = useState<Order[]>([]);
  const [fills, setFills] = useState<Fill[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [tradingDays, setTradingDays] = useState<TradingDay[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOrderVisible, setCreateOrderVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());

  const [form] = Form.useForm();

  // 加载数据
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // 并行加载所有数据
      const [ordersRes, fillsRes, positionsRes, tradingDaysRes, statsRes] = await Promise.allSettled([
        // 订单列表
        tradingService.getOrders({ execution_mode: mode as ExecutionMode, limit: 100 }),
        // 成交记录
        fillsService.getFills({ execution_mode: mode as ExecutionMode, limit: 100 }),
        // 持仓列表
        tradingService.getPositions({ execution_mode: mode as ExecutionMode }),
        // 交易日历
        get<{ items: TradingDay[] }>('/api/v1/trading-calendar/days?start_date=2026-03-01&end_date=2026-03-31'),
        // 交易统计
        get<{ items: DailyStats[] }>('/api/v1/trade-stats/daily?execution_mode=' + mode),
      ]);

      // 处理订单数据
      if (ordersRes.status === 'fulfilled') {
        setOrders(ordersRes.value.items || []);
      } else {
        console.error('加载订单失败:', ordersRes.reason);
        setOrders([]);
      }

      // 处理成交数据
      if (fillsRes.status === 'fulfilled') {
        setFills(fillsRes.value.items || []);
      } else {
        console.error('加载成交记录失败:', fillsRes.reason);
        setFills([]);
      }

      // 处理持仓数据
      if (positionsRes.status === 'fulfilled') {
        setPositions(positionsRes.value.items || []);
      } else {
        console.error('加载持仓失败:', positionsRes.reason);
        setPositions([]);
      }

      // 处理交易日历数据
      if (tradingDaysRes.status === 'fulfilled') {
        setTradingDays(tradingDaysRes.value.items || []);
      } else {
        console.error('加载交易日历失败:', tradingDaysRes.reason);
        // 使用本地生成作为备用
        setTradingDays(generateLocalTradingDays());
      }

      // 处理交易统计数据
      if (statsRes.status === 'fulfilled') {
        setDailyStats(statsRes.value.items || []);
      } else {
        console.error('加载交易统计失败:', statsRes.reason);
        setDailyStats([]);
      }

    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  }, [mode]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 创建订单
  const handleCreateOrder = async (values: any) => {
    setSubmitting(true);
    try {
      const orderData: OrderCreate = {
        symbol: values.symbol,
        side: values.side,
        order_type: values.order_type || 'LIMIT',
        quantity: values.quantity,
        price: values.price || 0,
        execution_mode: mode as ExecutionMode,
      };

      await tradingService.createOrder(orderData);
      message.success('订单创建成功');
      setCreateOrderVisible(false);
      form.resetFields();
      loadData();
    } catch (error) {
      console.error('创建订单失败:', error);
      // 错误信息已在 apiRequest 中处理
    } finally {
      setSubmitting(false);
    }
  };

  // 撤销订单
  const handleCancelOrder = async (orderId: string) => {
    try {
      await tradingService.cancelOrder(orderId);
      message.success('订单已撤销');
      loadData();
    } catch (error) {
      console.error('撤销订单失败:', error);
    }
  };

  // 订单表格列
  const orderColumns: ColumnsType<Order> = [
    { title: '订单ID', dataIndex: 'id', key: 'id', width: 80, ellipsis: true },
    { title: '股票代码', dataIndex: 'symbol', key: 'symbol' },
    {
      title: '方向', dataIndex: 'side', key: 'side',
      render: (side) => <Tag color={side === 'BUY' ? 'green' : 'red'}>{side === 'BUY' ? '买入' : '卖出'}</Tag>
    },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '价格', dataIndex: 'price', key: 'price', render: (v) => `¥${Number(v).toFixed(2)}` },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (status) => {
        const map: Record<string, { color: string; text: string }> = {
          PENDING: { color: 'blue', text: '待成交' },
          PARTIAL: { color: 'orange', text: '部分成交' },
          FILLED: { color: 'green', text: '已成交' },
          CANCELED: { color: 'default', text: '已撤销' },
          REJECTED: { color: 'red', text: '已拒绝' },
        };
        const s = map[status] || { color: 'default', text: status };
        return <Tag color={s.color}>{s.text}</Tag>;
      }
    },
    {
      title: '下单时间', dataIndex: 'create_time', key: 'create_time',
      render: (v) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    {
      title: '操作', key: 'action',
      render: (_, record) => (
        record.status === 'PENDING' && (
          <Button type="link" danger size="small" onClick={() => handleCancelOrder(record.id)}>
            撤销
          </Button>
        )
      )
    },
  ];

  // 成交记录表格列
  const fillColumns: ColumnsType<Fill> = [
    { title: '成交ID', dataIndex: 'id', key: 'id', width: 100, ellipsis: true },
    { title: '订单ID', dataIndex: 'order_id', key: 'order_id', width: 80, ellipsis: true },
    { title: '股票代码', dataIndex: 'symbol', key: 'symbol' },
    {
      title: '方向', dataIndex: 'side', key: 'side',
      render: (side) => <Tag color={side === 'BUY' ? 'green' : 'red'}>{side === 'BUY' ? '买入' : '卖出'}</Tag>
    },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '价格', dataIndex: 'price', key: 'price', render: (v) => `¥${Number(v).toFixed(2)}` },
    { title: '成交金额', dataIndex: 'fill_amount', key: 'fill_amount', render: (v) => `¥${Number(v).toFixed(2)}` },
    {
      title: '佣金', dataIndex: 'commission', key: 'commission',
      render: (v) => <span style={{ color: '#faad14' }}>¥{Number(v).toFixed(2)}</span>
    },
    {
      title: '印花税', dataIndex: 'stamp_duty', key: 'stamp_duty',
      render: (v) => <span style={{ color: '#faad14' }}>¥{Number(v).toFixed(2)}</span>
    },
    {
      title: '总费用', dataIndex: 'total_fees', key: 'total_fees',
      render: (v) => <span style={{ color: '#ff4d4f' }}>¥{Number(v).toFixed(2)}</span>
    },
    {
      title: '成交时间', dataIndex: 'fill_time', key: 'fill_time', width: 160,
      render: (v) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
  ];

  // 交易统计表格列
  const statsColumns: ColumnsType<DailyStats> = [
    { title: '日期', dataIndex: 'date', key: 'date' },
    { title: '总订单', dataIndex: 'total_orders', key: 'total_orders' },
    { title: '成交订单', dataIndex: 'filled_orders', key: 'filled_orders' },
    { title: '买入次数', dataIndex: 'buy_count', key: 'buy_count' },
    { title: '卖出次数', dataIndex: 'sell_count', key: 'sell_count' },
    {
      title: '买入金额', dataIndex: 'buy_amount', key: 'buy_amount',
      render: (v) => `¥${Number(v).toLocaleString()}`
    },
    {
      title: '卖出金额', dataIndex: 'sell_amount', key: 'sell_amount',
      render: (v) => `¥${Number(v).toLocaleString()}`
    },
    {
      title: '总佣金', dataIndex: 'total_commission', key: 'total_commission',
      render: (v) => <span style={{ color: '#faad14' }}>¥{Number(v).toFixed(2)}</span>
    },
    {
      title: '日盈亏', dataIndex: 'daily_pnl', key: 'daily_pnl',
      render: (v) => <span style={{ color: v >= 0 ? '#ff4d4f' : '#52c41a' }}>{v >= 0 ? '+' : ''}¥{Number(v).toFixed(2)}</span>
    },
  ];

  // 日历单元格渲染
  const dateCellRender = (date: Dayjs) => {
    const dateStr = date.format('YYYY-MM-DD');
    const day = tradingDays.find(d => d.date === dateStr);
    if (!day) return null;

    return (
      <div style={{ padding: '4px 0' }}>
        {day.is_trading_day ? (
          <Badge status="success" text={<span style={{ fontSize: 12 }}>交易日</span>} />
        ) : day.holiday_name ? (
          <Badge status="error" text={<span style={{ fontSize: 12 }}>{day.holiday_name}</span>} />
        ) : (
          <Badge status="default" text={<span style={{ fontSize: 12, color: '#999' }}>休市</span>} />
        )}
      </div>
    );
  };

  return (
    <div className="trading-page">
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}><ThunderboltOutlined style={{ marginRight: 8, color: 'var(--bb-accent-primary)' }} />交易管理</Title>
            <Text type="secondary">订单管理 · 成交记录 · 交易日历 · 交易统计</Text>
          </Col>
          <Col>
            <Space>
              <span>当前模式：</span>
              <Tag color={isPaperTrading ? 'green' : 'red'} style={{ fontSize: 14 }}>
                {isPaperTrading ? '🧪 模拟交易' : '⚡ 实盘交易'}
              </Tag>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOrderVisible(true)}>创建订单</Button>
              <Button icon={<SwapOutlined />} onClick={loadData} loading={loading}>刷新</Button>
            </Space>
          </Col>
        </Row>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 订单管理 */}
        <TabPane tab={<span><FileTextOutlined /> 订单管理</span>} key="orders">
          <Spin spinning={loading}>
            <Table columns={orderColumns} dataSource={orders} rowKey="id" pagination={{ pageSize: 10 }}
              locale={{ emptyText: <Empty description="暂无订单数据" /> }}
            />
          </Spin>
        </TabPane>

        {/* 成交记录 */}
        <TabPane tab={<span><CheckCircleOutlined /> 成交记录</span>} key="fills">
          <Spin spinning={loading}>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={4}><Statistic title="今日成交" value={fills.length} suffix="笔" /></Col>
                <Col span={4}><Statistic title="买入金额" value={fills.filter(f => f.side === 'BUY').reduce((s, f) => s + (f.fill_amount || 0), 0)} prefix="¥" /></Col>
                <Col span={4}><Statistic title="卖出金额" value={fills.filter(f => f.side === 'SELL').reduce((s, f) => s + (f.fill_amount || 0), 0)} prefix="¥" /></Col>
                <Col span={4}><Statistic title="总佣金" value={fills.reduce((s, f) => s + (f.commission || 0), 0)} prefix="¥" precision={2} valueStyle={{ color: '#faad14' }} /></Col>
                <Col span={4}><Statistic title="总印花税" value={fills.reduce((s, f) => s + (f.stamp_duty || 0), 0)} prefix="¥" precision={2} valueStyle={{ color: '#faad14' }} /></Col>
                <Col span={4}><Statistic title="总费用" value={fills.reduce((s, f) => s + (f.total_fees || 0), 0)} prefix="¥" precision={2} valueStyle={{ color: '#ff4d4f' }} /></Col>
              </Row>
            </Card>
            <Table columns={fillColumns} dataSource={fills} rowKey="id" pagination={{ pageSize: 10 }} scroll={{ x: 1200 }}
              locale={{ emptyText: <Empty description="暂无成交记录" /> }}
            />
          </Spin>
        </TabPane>

        {/* 交易日历 */}
        <TabPane tab={<span><CalendarOutlined /> 交易日历</span>} key="calendar">
          <Row gutter={24}>
            <Col span={18}>
              <Card>
                <Calendar
                  value={selectedDate}
                  onSelect={setSelectedDate}
                  cellRender={(date) => dateCellRender(date)}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card title="交易日详情" size="small">
                {(() => {
                  const dateStr = selectedDate.format('YYYY-MM-DD');
                  const day = tradingDays.find(d => d.date === dateStr);
                  if (!day) return <Empty description="暂无数据" />;
                  return (
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="日期">{day.date}</Descriptions.Item>
                      <Descriptions.Item label="状态">
                        <Tag color={day.is_trading_day ? 'green' : 'red'}>
                          {day.is_trading_day ? '交易日' : day.holiday_name || '休市'}
                        </Tag>
                      </Descriptions.Item>
                      {day.is_trading_day && (
                        <>
                          <Descriptions.Item label="开盘时间">{day.open_time}</Descriptions.Item>
                          <Descriptions.Item label="收盘时间">{day.close_time}</Descriptions.Item>
                        </>
                      )}
                    </Descriptions>
                  );
                })()}
              </Card>
              <Divider />
              <Card title="本月统计" size="small">
                <Statistic title="交易日" value={tradingDays.filter(d => d.is_trading_day && d.date.startsWith(selectedDate.format('YYYY-MM'))).length} suffix="天" />
                <Divider />
                <Statistic title="休市日" value={tradingDays.filter(d => !d.is_trading_day && d.date.startsWith(selectedDate.format('YYYY-MM'))).length} suffix="天" />
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* 交易统计 */}
        <TabPane tab={<span><BarChartOutlined /> 交易统计</span>} key="stats">
          <Spin spinning={loading}>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                {[
                  { label: '总订单数', value: dailyStats.reduce((s, d) => s + d.total_orders, 0) },
                  { label: '成交订单', value: dailyStats.reduce((s, d) => s + d.filled_orders, 0) },
                  { label: '买入次数', value: dailyStats.reduce((s, d) => s + d.buy_count, 0) },
                  { label: '卖出次数', value: dailyStats.reduce((s, d) => s + d.sell_count, 0) },
                  { label: '累计盈亏', value: dailyStats.reduce((s, d) => s + d.daily_pnl, 0), prefix: '¥' },
                  { label: '累计佣金', value: dailyStats.reduce((s, d) => s + d.total_commission, 0), prefix: '¥' },
                ].map((item, i) => (
                  <Col span={4} key={i}>
                    <Statistic title={item.label} value={item.value} prefix={item.prefix} precision={item.prefix ? 2 : 0} />
                  </Col>
                ))}
              </Row>
            </Card>
            <Table columns={statsColumns} dataSource={dailyStats} rowKey="date" pagination={{ pageSize: 10 }}
              locale={{ emptyText: <Empty description="暂无统计数据" /> }}
            />
          </Spin>
        </TabPane>

        {/* 持仓管理 */}
        <TabPane tab={<span><HistoryOutlined /> 持仓管理</span>} key="positions">
          <Spin spinning={loading}>
            <Table
              columns={[
                { title: '股票代码', dataIndex: 'symbol' },
                { title: '持仓数量', dataIndex: 'quantity' },
                { title: '成本价', dataIndex: 'avg_price', render: (v) => `¥${Number(v).toFixed(2)}` },
                { title: '现价', dataIndex: 'current_price', render: (v) => v ? `¥${Number(v).toFixed(2)}` : '-' },
                { title: '市值', dataIndex: 'market_value', render: (v) => v ? `¥${Number(v).toFixed(2)}` : '-' },
                {
                  title: '浮动盈亏', dataIndex: 'unrealized_pnl',
                  render: (v) => v !== undefined && v !== null
                    ? <span style={{ color: v >= 0 ? '#ff4d4f' : '#52c41a' }}>{v >= 0 ? '+' : ''}¥{Number(v).toFixed(2)}</span>
                    : '-'
                },
              ]}
              dataSource={positions}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: <Empty description="暂无持仓数据" /> }}
            />
          </Spin>
        </TabPane>
      </Tabs>

      {/* 创建订单弹窗 */}
      <Modal
        title="创建订单"
        open={createOrderVisible}
        onCancel={() => setCreateOrderVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={submitting}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateOrder}>
          <Form.Item label="股票代码" name="symbol" rules={[{ required: true, message: '请输入股票代码' }]}>
            <input placeholder="例如: 000001.SZ" style={{ width: '100%', padding: '4px 11px', border: '1px solid #d9d9d9', borderRadius: 6 }} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="交易方向" name="side" rules={[{ required: true, message: '请选择交易方向' }]}>
                <Select placeholder="请选择">
                  <Option value="BUY">买入</Option>
                  <Option value="SELL">卖出</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="订单类型" name="order_type" initialValue="LIMIT">
                <Select>
                  <Option value="LIMIT">限价单</Option>
                  <Option value="MARKET">市价单</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="数量" name="quantity" rules={[{ required: true, message: '请输入数量' }]}>
                <InputNumber min={100} step={100} style={{ width: '100%' }} placeholder="100股起" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="价格" name="price">
                <InputNumber min={0} step={0.01} precision={2} style={{ width: '100%' }} placeholder="限价单必填" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

// 本地生成交易日历备用
const generateLocalTradingDays = (): TradingDay[] => {
  const days: TradingDay[] = [];
  const now = dayjs();
  const startOfMonth = now.startOf('month');
  const endOfMonth = now.endOf('month');

  for (let i = 0; i <= endOfMonth.diff(startOfMonth, 'day'); i++) {
    const date = startOfMonth.add(i, 'day');
    const dayOfWeek = date.day();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    days.push({
      date: date.format('YYYY-MM-DD'),
      is_trading_day: !isWeekend,
      is_half_day: false,
      open_time: isWeekend ? undefined : '09:30',
      close_time: isWeekend ? undefined : '15:00',
      holiday_name: undefined,
    });
  }
  return days;
};

export default Trading;
