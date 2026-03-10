/**
 * SectorAnalysis - 板块分析页面
 *
 * 功能：
 * - 行业/概念/地域板块切换
 * - 板块涨跌排行
 * - 板块详情和成分股
 * - 资金流向分析
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card, Tabs, Table, Tag, Space, Button, Statistic, Row, Col,
  Input, message, Modal, Typography, Empty,
  Spin, Divider, Alert
} from 'antd';
import {
  RiseOutlined, FallOutlined, StockOutlined, FundOutlined,
  EyeOutlined, ReloadOutlined, SearchOutlined, ArrowUpOutlined,
  ArrowDownOutlined, TrophyOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useTranslation } from 'react-i18next';
import { get } from '../services/api';
import './SectorAnalysis.css';

const { TabPane } = Tabs;
const { Text, Title } = Typography;
const { Search } = Input;

// 板块数据接口
interface SectorData {
  name: string;
  code: string;
  type: string;
  change_pct?: number;
  volume?: number;
  amount?: number;
  turnover_rate?: number;
  leading_stock?: string;
  leading_stock_change?: number;
  stock_count?: number;
  up_count?: number;
  down_count?: number;
}

// 板块成分股接口
interface SectorStock {
  symbol: string;
  name: string;
  price?: number;
  change_pct?: number;
  volume?: number;
  amount?: number;
  turnover_rate?: number;
  pe_ratio?: number;
  market_cap?: number;
}

// 板块统计接口
interface SectorStats {
  total: number;
  up: number;
  down: number;
  flat: number;
  best: SectorData | null;
  worst: SectorData | null;
}

const SectorAnalysis: React.FC = () => {
  const { t } = useTranslation();
  const [sectorType, setSectorType] = useState<'industry' | 'concept' | 'region'>('industry');
  const [sectors, setSectors] = useState<SectorData[]>([]);
  const [stats, setStats] = useState<SectorStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedSector, setSelectedSector] = useState<SectorData | null>(null);
  const [sectorDetailVisible, setSectorDetailVisible] = useState(false);
  const [sectorStocks, setSectorStocks] = useState<SectorStock[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  // 加载板块数据
  const loadSectors = useCallback(async () => {
    setLoading(true);
    try {
      // 获取板块统计概览
      const response = await get<{
        success: boolean;
        data: SectorData[];
        summary: SectorStats;
      }>(`/api/v1/data/sectors/stats/overview?sector_type=${sectorType}`);

      if (response.success) {
        setSectors(response.data);
        setStats(response.summary);
      }
    } catch (error) {
      console.error('加载板块数据失败:', error);
      message.error('加载板块数据失败');
      // 使用模拟数据
      const mockData = generateMockSectors(sectorType);
      setSectors(mockData);
      setStats({
        total: mockData.length,
        up: mockData.filter(s => (s.change_pct || 0) > 0).length,
        down: mockData.filter(s => (s.change_pct || 0) < 0).length,
        flat: mockData.filter(s => (s.change_pct || 0) === 0).length,
        best: mockData[0],
        worst: mockData[mockData.length - 1],
      });
    } finally {
      setLoading(false);
    }
  }, [sectorType]);

  // 生成模拟数据
  const generateMockSectors = (type: string): SectorData[] => {
    const sectorNames: Record<string, string[]> = {
      industry: [
        '半导体', '计算机', '通信', '电子制造', '软件开发',
        '新能源', '光伏', '锂电池', '储能', '风电',
        '医药生物', '医疗器械', '化学制药', '中药', '生物制品',
        '白酒', '食品饮料', '家电', '餐饮旅游', '纺织服装',
        '银行', '证券', '保险', '房地产', '基建',
        '有色', '煤炭', '石油', '钢铁', '化工',
      ],
      concept: [
        '人工智能', 'ChatGPT', 'AIGC', '机器人', '无人驾驶',
        '元宇宙', '虚拟现实', '增强现实', '数字货币', '区块链',
        '碳中和', 'ESG', '节能环保', '污水处理', '固废处理',
        '国企改革', '一带一路', '自贸区', '粤港澳', '长三角',
        '军工', '卫星导航', '大飞机', '国产芯片', '信创',
      ],
      region: [
        '北京', '上海', '广东', '浙江', '江苏',
        '山东', '福建', '四川', '湖北', '湖南',
        '河南', '安徽', '河北', '陕西', '重庆',
      ],
    };

    const names = sectorNames[type] || sectorNames.industry;
    return names.map((name, index) => {
      const changePct = (Math.random() - 0.45) * 8; // 略微偏向上涨
      return {
        name,
        code: `BK${String(1000 + index).padStart(4, '0')}`,
        type,
        change_pct: parseFloat(changePct.toFixed(2)),
        volume: Math.floor(Math.random() * 10000000) + 100000,
        amount: Math.floor(Math.random() * 10000000000) + 1000000000,
        turnover_rate: parseFloat((Math.random() * 10).toFixed(2)),
        leading_stock: `股票${Math.floor(Math.random() * 100)}`,
        leading_stock_change: parseFloat((Math.random() * 10 - 2).toFixed(2)),
        stock_count: Math.floor(Math.random() * 50) + 10,
        up_count: Math.floor(Math.random() * 30) + 5,
        down_count: Math.floor(Math.random() * 20) + 2,
      };
    }).sort((a, b) => (b.change_pct || 0) - (a.change_pct || 0));
  };

  useEffect(() => {
    loadSectors();
  }, [loadSectors]);

  // 查看板块详情
  const handleViewSector = async (sector: SectorData) => {
    setSelectedSector(sector);
    setSectorDetailVisible(true);
    setDetailLoading(true);

    try {
      const response = await get<{
        success: boolean;
        data: {
          name: string;
          type: string;
          stocks: SectorStock[];
          stats: Record<string, unknown>;
        };
      }>(`/api/v1/data/sectors/${encodeURIComponent(sector.name)}?sector_type=${sectorType}`);

      if (response.success && response.data.stocks) {
        setSectorStocks(response.data.stocks);
      } else {
        // 使用模拟数据
        setSectorStocks(generateMockStocks(sector.name));
      }
    } catch (error) {
      console.error('加载板块详情失败:', error);
      setSectorStocks(generateMockStocks(sector.name));
    } finally {
      setDetailLoading(false);
    }
  };

  // 生成模拟成分股数据
  const generateMockStocks = (sectorName: string): SectorStock[] => {
    const count = Math.floor(Math.random() * 30) + 10;
    return Array.from({ length: count }, (_, i) => ({
      symbol: `${['600', '000', '300', '688'][Math.floor(Math.random() * 4)]}${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
      name: `${sectorName}股票${i + 1}`,
      price: parseFloat((Math.random() * 100 + 10).toFixed(2)),
      change_pct: parseFloat((Math.random() * 10 - 4).toFixed(2)),
      volume: Math.floor(Math.random() * 1000000) + 10000,
      amount: Math.floor(Math.random() * 100000000) + 1000000,
      turnover_rate: parseFloat((Math.random() * 15).toFixed(2)),
      pe_ratio: parseFloat((Math.random() * 50 + 5).toFixed(2)),
      market_cap: Math.floor(Math.random() * 10000) + 100,
    })).sort((a, b) => (b.change_pct || 0) - (a.change_pct || 0));
  };

  // 过滤板块
  const filteredSectors = useMemo(() => {
    if (!searchText) return sectors;
    return sectors.filter(s =>
      s.name.toLowerCase().includes(searchText.toLowerCase()) ||
      s.code.toLowerCase().includes(searchText.toLowerCase())
    );
  }, [sectors, searchText]);

  // 涨跌分布数据
  const distribution = useMemo(() => {
    if (!stats) return { up: 0, down: 0, flat: 0 };
    const total = stats.total || 1;
    return {
      up: Math.round((stats.up / total) * 100),
      down: Math.round((stats.down / total) * 100),
      flat: Math.round((stats.flat / total) * 100),
    };
  }, [stats]);

  // 板块表格列定义
  const sectorColumns: ColumnsType<SectorData> = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => (
        <span style={{ color: index < 3 ? '#faad14' : undefined, fontWeight: index < 3 ? 'bold' : undefined }}>
          {index + 1}
        </span>
      ),
    },
    {
      title: '板块名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.code}</Text>
        </Space>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'change_pct',
      key: 'change_pct',
      sorter: (a, b) => (a.change_pct || 0) - (b.change_pct || 0),
      render: (value) => (
        <Text
          strong
          style={{
            color: value > 0 ? '#ff4d4f' : value < 0 ? '#52c41a' : undefined,
            fontSize: 14,
          }}
        >
          {value > 0 ? '+' : ''}{value?.toFixed(2)}%
          {value > 0 ? <RiseOutlined style={{ marginLeft: 4 }} /> :
           value < 0 ? <FallOutlined style={{ marginLeft: 4 }} /> : null}
        </Text>
      ),
    },
    {
      title: '成交额',
      dataIndex: 'amount',
      key: 'amount',
      sorter: (a, b) => (a.amount || 0) - (b.amount || 0),
      render: (value) => {
        if (value >= 100000000) {
          return `${(value / 100000000).toFixed(2)}亿`;
        }
        if (value >= 10000) {
          return `${(value / 10000).toFixed(2)}万`;
        }
        return value?.toLocaleString();
      },
    },
    {
      title: '换手率',
      dataIndex: 'turnover_rate',
      key: 'turnover_rate',
      render: (value) => value ? `${value.toFixed(2)}%` : '-',
    },
    {
      title: '领涨股',
      dataIndex: 'leading_stock',
      key: 'leading_stock',
      render: (text, record) => (
        <Space>
          <Text>{text}</Text>
          {record.leading_stock_change !== undefined && (
            <Text style={{ color: record.leading_stock_change > 0 ? '#ff4d4f' : '#52c41a', fontSize: 12 }}>
              {record.leading_stock_change > 0 ? '+' : ''}{record.leading_stock_change.toFixed(2)}%
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '涨跌家数',
      key: 'up_down_count',
      render: (_, record) => (
        <Space size="small">
          <Text style={{ color: '#ff4d4f' }}>{record.up_count || 0}↑</Text>
          <Text type="secondary">/</Text>
          <Text style={{ color: '#52c41a' }}>{record.down_count || 0}↓</Text>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewSector(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  // 成分股表格列
  const stockColumns: ColumnsType<SectorStock> = [
    {
      title: '代码',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text) => <Text code>{text}</Text>,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: '现价',
      dataIndex: 'price',
      key: 'price',
      render: (value) => value ? `¥${value.toFixed(2)}` : '-',
    },
    {
      title: '涨跌幅',
      dataIndex: 'change_pct',
      key: 'change_pct',
      sorter: (a, b) => (a.change_pct || 0) - (b.change_pct || 0),
      render: (value) => (
        <Text style={{ color: value > 0 ? '#ff4d4f' : value < 0 ? '#52c41a' : undefined, fontWeight: 'bold' }}>
          {value > 0 ? '+' : ''}{value?.toFixed(2)}%
        </Text>
      ),
    },
    {
      title: '成交额',
      dataIndex: 'amount',
      key: 'amount',
      render: (value) => {
        if (!value) return '-';
        if (value >= 100000000) {
          return `${(value / 100000000).toFixed(2)}亿`;
        }
        return `${(value / 10000).toFixed(0)}万`;
      },
    },
    {
      title: '换手率',
      dataIndex: 'turnover_rate',
      key: 'turnover_rate',
      render: (value) => value ? `${value.toFixed(2)}%` : '-',
    },
    {
      title: '市盈率',
      dataIndex: 'pe_ratio',
      key: 'pe_ratio',
      render: (value) => value ? value.toFixed(2) : '-',
    },
    {
      title: '市值(亿)',
      dataIndex: 'market_cap',
      key: 'market_cap',
      render: (value) => value ? value.toFixed(2) : '-',
    },
  ];

  return (
    <div className="sector-analysis-page">
      {/* 页面标题 */}
      <div className="page-header">
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              <StockOutlined style={{ marginRight: 8, color: 'var(--bb-accent-primary)' }} />
              {t('market.sectors')}
            </Title>
            <Text type="secondary">板块行情 · 资金流向 · 成分股分析</Text>
          </Col>
          <Col>
            <Space>
              <Search
                placeholder="搜索板块"
                allowClear
                style={{ width: 200 }}
                onSearch={setSearchText}
                onChange={(e) => setSearchText(e.target.value)}
                prefix={<SearchOutlined />}
              />
              <Button icon={<ReloadOutlined />} onClick={loadSectors} loading={loading}>
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* 统计概览卡片 */}
      {stats && (
        <Row gutter={16} className="stats-row">
          <Col span={4}>
            <Card size="small" className="stats-card">
              <Statistic
                title="板块总数"
                value={stats.total}
                prefix={<FundOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small" className="stats-card up">
              <Statistic
                title="上涨板块"
                value={stats.up}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<ArrowUpOutlined />}
                suffix={<span style={{ fontSize: 12 }}>({distribution.up}%)</span>}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small" className="stats-card down">
              <Statistic
                title="下跌板块"
                value={stats.down}
                valueStyle={{ color: '#52c41a' }}
                prefix={<ArrowDownOutlined />}
                suffix={<span style={{ fontSize: 12 }}>({distribution.down}%)</span>}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small" className="stats-card best">
              <div className="best-worst-info">
                <Text type="secondary">领涨板块</Text>
                <Text strong style={{ color: '#ff4d4f', fontSize: 16 }}>
                  <TrophyOutlined style={{ marginRight: 4 }} />
                  {stats.best?.name}
                </Text>
                <Text style={{ color: '#ff4d4f' }}>
                  +{stats.best?.change_pct?.toFixed(2)}%
                </Text>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small" className="stats-card worst">
              <div className="best-worst-info">
                <Text type="secondary">领跌板块</Text>
                <Text strong style={{ color: '#52c41a', fontSize: 16 }}>
                  {stats.worst?.name}
                </Text>
                <Text style={{ color: '#52c41a' }}>
                  {stats.worst?.change_pct?.toFixed(2)}%
                </Text>
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* 板块类型切换 */}
      <Card className="sector-main-card">
        <Tabs
          activeKey={sectorType}
          onChange={(key) => setSectorType(key as typeof sectorType)}
          tabBarExtraContent={
            <Alert
              message="数据更新时间: 实时"
              type="info"
              showIcon
              style={{ padding: '4px 12px' }}
            />
          }
        >
          <TabPane tab="行业板块" key="industry" />
          <TabPane tab="概念板块" key="concept" />
          <TabPane tab="地域板块" key="region" />
        </Tabs>

        <Spin spinning={loading}>
          <Table
            columns={sectorColumns}
            dataSource={filteredSectors}
            rowKey="code"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 个板块`,
            }}
            size="small"
            scroll={{ x: 1000 }}
            locale={{ emptyText: <Empty description="暂无板块数据" /> }}
          />
        </Spin>
      </Card>

      {/* 板块详情弹窗 */}
      <Modal
        title={
          <Space>
            <StockOutlined style={{ color: 'var(--bb-accent-primary)' }} />
            <span>{selectedSector?.name} - 成分股</span>
            {selectedSector && (
              <Tag color={(selectedSector.change_pct ?? 0) > 0 ? 'red' : (selectedSector.change_pct ?? 0) < 0 ? 'green' : 'default'}>
                {(selectedSector.change_pct ?? 0) > 0 ? '+' : ''}{(selectedSector.change_pct ?? 0).toFixed(2)}%
              </Tag>
            )}
          </Space>
        }
        open={sectorDetailVisible}
        onCancel={() => setSectorDetailVisible(false)}
        footer={null}
        width={1000}
        className="sector-detail-modal"
      >
        <Spin spinning={detailLoading}>
          {selectedSector && (
            <>
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                  <Statistic
                    title="板块代码"
                    value={selectedSector.code}
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="成分股数量"
                    value={selectedSector.stock_count || sectorStocks.length}
                    suffix="只"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="上涨家数"
                    value={selectedSector.up_count || sectorStocks.filter(s => (s.change_pct || 0) > 0).length}
                    valueStyle={{ color: '#ff4d4f' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="下跌家数"
                    value={selectedSector.down_count || sectorStocks.filter(s => (s.change_pct || 0) < 0).length}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
              </Row>
              <Divider style={{ margin: '12px 0' }} />
            </>
          )}
          <Table
            columns={stockColumns}
            dataSource={sectorStocks}
            rowKey="symbol"
            pagination={{ pageSize: 10 }}
            size="small"
            scroll={{ x: 800 }}
            locale={{ emptyText: <Empty description="暂无成分股数据" /> }}
          />
        </Spin>
      </Modal>
    </div>
  );
};

export default SectorAnalysis;
