/**
 * MarketOverview - 市场概览页面
 *
 * 功能：
 * - 大盘指数卡片
 * - 市场情绪仪表盘
 * - 经济周期判断 (美林时钟)
 * - 资产配置建议
 * - 热门板块排行
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Row, Col, Statistic, Tag, Space, Button, Spin, Typography,
  Progress, Tooltip, Divider, Alert, Tabs, Table
} from 'antd';
import {
  RiseOutlined, FallOutlined, DashboardOutlined,
  ThunderboltOutlined, BulbOutlined, WarningOutlined,
  SyncOutlined, InfoCircleOutlined, TrophyOutlined,
  ClockCircleOutlined, FundOutlined, StockOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { ColumnsType } from 'antd/es/table';
import { get } from '../services/api';
import './MarketOverview.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

// 类型定义
interface MainIndex {
  name: string;
  value: number;
  change: number;
  change_percent: number;
}

interface MarketBreadth {
  advancing: number;
  declining: number;
  unchanged: number;
}

interface PhaseJudgment {
  judgment_id: string;
  country: string;
  phase: string;
  phase_name: string;
  confidence: number;
  growth_score: number;
  inflation_score: number;
  reasoning: string;
  alternative_phases: Array<{ phase: string; probability: number }>;
  judgment_time: string;
}

interface MarketOverviewData {
  country: string;
  main_index: MainIndex;
  market_breadth: MarketBreadth;
  sentiment: string;
  phase_judgment: PhaseJudgment | null;
  allocation_recommendation: {
    equities: number;
    bonds: number;
    commodities: number;
    cash: number;
    sectors: Array<{ sector: string; weight: number; rationale: string }>;
  } | null;
}

// 美林时钟配置
const MERRILL_CLOCK_CONFIG = {
  recession: {
    name: '衰退期',
    icon: '❄️',
    color: '#1890ff',
    bgClass: 'phase-winter',
    description: '经济下行、通胀下行，债券表现最优'
  },
  recovery: {
    name: '复苏期',
    icon: '🌱',
    color: '#52c41a',
    bgClass: 'phase-spring',
    description: '经济上行、通胀下行，股票表现最优'
  },
  overheat: {
    name: '过热期',
    icon: '🔥',
    color: '#fa8c16',
    bgClass: 'phase-summer',
    description: '经济上行、通胀上行，商品表现最优'
  },
  stagflation: {
    name: '滞胀期',
    icon: '🍂',
    color: '#eb2f96',
    bgClass: 'phase-autumn',
    description: '经济下行、通胀上行，现金表现最优'
  }
};

const MarketOverview: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [country, setCountry] = useState<'CN' | 'US'>('CN');
  const [data, setData] = useState<MarketOverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 加载数据
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await get(`/api/v1/market-dynamics/overview?country=${country}`);
      setData(response);
    } catch (err: any) {
      setError(err.message || '加载数据失败');
    } finally {
      setLoading(false);
    }
  }, [country]);

  useEffect(() => {
    loadData();
    // 每5分钟刷新
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  // 渲染指数卡片
  const renderIndexCard = () => {
    if (!data?.main_index) return null;

    const index = data.main_index;
    const isUp = index.change >= 0;

    return (
      <Card className="index-card">
        <div className="index-header">
          <Title level={4}>{index.name}</Title>
          <Tag color={isUp ? 'green' : 'red'}>
            {country === 'CN' ? 'A股' : '美股'}
          </Tag>
        </div>
        <div className="index-value">
          <span className="value">{index.value.toLocaleString()}</span>
          <span className={`change ${isUp ? 'up' : 'down'}`}>
            {isUp ? <RiseOutlined /> : <FallOutlined />}
            {isUp ? '+' : ''}{index.change_percent.toFixed(2)}%
          </span>
        </div>
      </Card>
    );
  };

  // 渲染市场宽度
  const renderMarketBreadth = () => {
    if (!data?.market_breadth) return null;

    const breadth = data.market_breadth;
    const total = breadth.advancing + breadth.declining + breadth.unchanged;
    const advanceRatio = (breadth.advancing / total) * 100;

    return (
      <Card title="市场宽度" className="breadth-card">
        <div className="breadth-bar">
          <div className="advance-bar" style={{ width: `${advanceRatio}%` }}>
            {breadth.advancing}
          </div>
          <div className="decline-bar" style={{ width: `${100 - advanceRatio}%` }}>
            {breadth.declining}
          </div>
        </div>
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={8}>
            <Statistic
              title="上涨"
              value={breadth.advancing}
              valueStyle={{ color: '#cf1322' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="下跌"
              value={breadth.declining}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="平盘"
              value={breadth.unchanged}
            />
          </Col>
        </Row>
      </Card>
    );
  };

  // 渲染美林时钟
  const renderMerrillClock = () => {
    if (!data?.phase_judgment) return null;

    const judgment = data.phase_judgment;
    const phaseConfig = MERRILL_CLOCK_CONFIG[judgment.phase as keyof typeof MERRILL_CLOCK_CONFIG];

    return (
      <Card
        title={
          <Space>
            <ClockCircleOutlined />
            <span>美林时钟判断</span>
          </Space>
        }
        className={`clock-card ${phaseConfig?.bgClass || ''}`}
        extra={
          <Tooltip title="基于宏观经济指标自动判断">
            <InfoCircleOutlined />
          </Tooltip>
        }
      >
        <div className="clock-display">
          <div className="clock-icon">{phaseConfig?.icon}</div>
          <Title level={3}>{phaseConfig?.name || judgment.phase}</Title>
          <Progress
            percent={judgment.confidence * 100}
            format={(percent) => `置信度 ${percent?.toFixed(0)}%`}
            strokeColor={phaseConfig?.color}
          />
        </div>

        <Divider />

        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="增长得分"
              value={judgment.growth_score}
              precision={2}
              valueStyle={{
                color: judgment.growth_score > 0 ? '#cf1322' : '#3f8600'
              }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="通胀得分"
              value={judgment.inflation_score}
              precision={2}
              valueStyle={{
                color: judgment.inflation_score > 0 ? '#cf1322' : '#3f8600'
              }}
            />
          </Col>
        </Row>

        <Divider />

        <Alert
          message={phaseConfig?.description}
          type="info"
          showIcon
        />

        <div className="reasoning" style={{ marginTop: 16 }}>
          <Text type="secondary">{judgment.reasoning}</Text>
        </div>
      </Card>
    );
  };

  // 渲染资产配置
  const renderAssetAllocation = () => {
    if (!data?.allocation_recommendation) return null;

    const allocation = data.allocation_recommendation;

    const assets = [
      { key: 'equities', name: '股票', weight: allocation.equities, color: '#1890ff' },
      { key: 'bonds', name: '债券', weight: allocation.bonds, color: '#52c41a' },
      { key: 'commodities', name: '商品', weight: allocation.commodities, color: '#fa8c16' },
      { key: 'cash', name: '现金', weight: allocation.cash, color: '#722ed1' },
    ];

    const sectorColumns: ColumnsType<any> = [
      { title: '行业', dataIndex: 'sector', key: 'sector' },
      { title: '权重', dataIndex: 'weight', key: 'weight', render: (v: number) => `${(v * 100).toFixed(0)}%` },
      { title: '理由', dataIndex: 'rationale', key: 'rationale' },
    ];

    return (
      <Card
        title={
          <Space>
            <FundOutlined />
            <span>资产配置建议</span>
          </Space>
        }
        className="allocation-card"
      >
        <Row gutter={[16, 16]}>
          {assets.map(asset => (
            <Col span={12} key={asset.key}>
              <Card size="small" className="asset-item">
                <div className="asset-header">
                  <Text strong>{asset.name}</Text>
                  <Text style={{ color: asset.color, fontWeight: 'bold' }}>
                    {(asset.weight * 100).toFixed(0)}%
                  </Text>
                </div>
                <Progress
                  percent={asset.weight * 100}
                  showInfo={false}
                  strokeColor={asset.color}
                />
              </Card>
            </Col>
          ))}
        </Row>

        <Divider orientation="left">重点行业</Divider>

        <Table
          columns={sectorColumns}
          dataSource={allocation.sectors || []}
          rowKey="sector"
          pagination={false}
          size="small"
        />
      </Card>
    );
  };

  // 渲染时钟图
  const renderClockDiagram = () => {
    const phases = ['recovery', 'overheat', 'stagflation', 'recession'];
    const currentPhase = data?.phase_judgment?.phase;

    return (
      <Card title="美林时钟" className="clock-diagram-card">
        <div className="clock-container">
          {phases.map((phase, index) => {
            const config = MERRILL_CLOCK_CONFIG[phase as keyof typeof MERRILL_CLOCK_CONFIG];
            const isActive = phase === currentPhase;

            return (
              <div
                key={phase}
                className={`clock-quadrant quadrant-${index + 1} ${isActive ? 'active' : ''}`}
                style={{ borderColor: isActive ? config?.color : 'transparent' }}
              >
                <div className="quadrant-icon">{config?.icon}</div>
                <div className="quadrant-name">{config?.name}</div>
              </div>
            );
          })}
          <div className="clock-center">
            <div className="growth-axis">
              <span className="axis-label up">增长 ↑</span>
              <span className="axis-label down">增长 ↓</span>
            </div>
            <div className="inflation-axis">
              <span className="axis-label left">通胀 ←</span>
              <span className="axis-label right">通胀 →</span>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  if (loading && !data) {
    return (
      <div className="loading-container">
        <Spin size="large" tip="加载市场数据..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="加载失败"
        description={error}
        type="error"
        showIcon
        action={
          <Button onClick={loadData}>
            重试
          </Button>
        }
      />
    );
  }

  return (
    <div className="market-overview">
      {/* 页面头部 */}
      <div className="page-header">
        <Title level={2}>
          <DashboardOutlined /> 市场概览
        </Title>
        <Space>
          <Button
            type={country === 'CN' ? 'primary' : 'default'}
            onClick={() => setCountry('CN')}
          >
            A股市场
          </Button>
          <Button
            type={country === 'US' ? 'primary' : 'default'}
            onClick={() => setCountry('US')}
          >
            美股市场
          </Button>
          <Button icon={<SyncOutlined />} onClick={loadData}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 主要内容 */}
      <Row gutter={[16, 16]}>
        {/* 左侧 */}
        <Col xs={24} lg={16}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              {renderIndexCard()}
            </Col>
            <Col xs={24} md={12}>
              {renderMarketBreadth()}
            </Col>
            <Col xs={24} md={12}>
              {renderClockDiagram()}
            </Col>
          </Row>
        </Col>

        {/* 右侧 */}
        <Col xs={24} lg={8}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              {renderMerrillClock()}
            </Col>
            <Col span={24}>
              {renderAssetAllocation()}
            </Col>
          </Row>
        </Col>
      </Row>
    </div>
  );
};

export default MarketOverview;
