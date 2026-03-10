/**
 * 系统文档页面
 *
 * 展示系统架构文档、API文档、用户指南等
 */

import React, { useState } from 'react';
import { Card, Tabs, Typography, Space, Button, Tag, Divider, Table, Progress } from 'antd';
import {
  FileTextOutlined,
  ApiOutlined,
  BookOutlined,
  CodeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  ExportOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

// 技术栈数据
const techStackData = {
  backend: [
    { name: 'Python', version: '3.11+', status: 'done' },
    { name: 'FastAPI', version: '0.109.0', status: 'done' },
    { name: 'SQLAlchemy', version: '2.0', status: 'done' },
    { name: 'PostgreSQL', version: '15', status: 'done' },
    { name: 'Redis', version: '7', status: 'done' },
    { name: 'Celery', version: '5.3', status: 'done' },
    { name: 'WebSocket', version: '-', status: 'done' },
    { name: 'AkShare', version: 'latest', status: 'done' },
  ],
  frontend: [
    { name: 'React', version: '18', status: 'done' },
    { name: 'TypeScript', version: '5.3', status: 'done' },
    { name: 'Ant Design', version: '5.12', status: 'done' },
    { name: 'Redux Toolkit', version: '2.0', status: 'done' },
    { name: 'React Router', version: '6', status: 'done' },
    { name: 'i18next', version: '23', status: 'done' },
    { name: 'ECharts', version: '5', status: 'done' },
    { name: 'IndexedDB', version: '-', status: 'done' },
  ],
};

// 功能模块完成度
const moduleStatus = [
  { module: '认证系统', backend: 100, frontend: 100, priority: 'P0' },
  { module: '用户管理', backend: 100, frontend: 100, priority: 'P0' },
  { module: '实时行情', backend: 100, frontend: 100, priority: 'P0' },
  { module: 'WebSocket推送', backend: 100, frontend: 100, priority: 'P0' },
  { module: '交易系统', backend: 100, frontend: 100, priority: 'P1' },
  { module: '风控系统', backend: 100, frontend: 80, priority: 'P1' },
  { module: '回测引擎', backend: 100, frontend: 100, priority: 'P1' },
  { module: '自选股管理', backend: 100, frontend: 100, priority: 'P1' },
  { module: '价格预警', backend: 100, frontend: 100, priority: 'P1' },
  { module: '策略引擎', backend: 100, frontend: 80, priority: 'P1' },
  { module: 'AI服务', backend: 80, frontend: 60, priority: 'P2' },
  { module: '投资组合', backend: 100, frontend: 80, priority: 'P2' },
  { module: '板块分析', backend: 100, frontend: 100, priority: 'P2' },
  { module: '数据管理', backend: 100, frontend: 80, priority: 'P2' },
  { module: '社区功能', backend: 0, frontend: 0, priority: 'P3' },
];

const Docs: React.FC = () => {
  const [activeTab, setActiveTab] = useState('architecture');

  // 打开系统架构文档
  const openArchitectureDoc = () => {
    window.open('/docs/SYSTEM_ARCHITECTURE.html', '_blank');
  };

  // 状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircleOutlined style={{ color: 'var(--color-up)' }} />;
      case 'partial':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      case 'pending':
        return <CloseCircleOutlined style={{ color: 'var(--color-down)' }} />;
      default:
        return null;
    }
  };

  // 进度条颜色
  const getProgressColor = (percent: number) => {
    if (percent >= 80) return 'var(--color-up)';
    if (percent >= 40) return '#faad14';
    return 'var(--color-down)';
  };

  // 技术栈表格列
  const techColumns = [
    {
      title: '技术',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (version: string) => <Tag>{version}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusIcon(status),
    },
  ];

  // 模块状态表格列
  const moduleColumns = [
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => {
        const colorMap: Record<string, string> = {
          P0: '#ff4d4f',
          P1: '#faad14',
          P2: '#52c41a',
          P3: '#1890ff',
        };
        return <Tag color={colorMap[priority]}>{priority}</Tag>;
      },
    },
    {
      title: '后端',
      dataIndex: 'backend',
      key: 'backend',
      render: (percent: number) => (
        <Progress
          percent={percent}
          size="small"
          strokeColor={getProgressColor(percent)}
          format={(p) => `${p}%`}
        />
      ),
    },
    {
      title: '前端',
      dataIndex: 'frontend',
      key: 'frontend',
      render: (percent: number) => (
        <Progress
          percent={percent}
          size="small"
          strokeColor={getProgressColor(percent)}
          format={(p) => `${p}%`}
        />
      ),
    },
  ];

  return (
    <div style={{ padding: '0 24px' }}>
      <Card
        style={{
          background: 'var(--bg-card)',
          borderRadius: 12,
          border: '1px solid var(--border-color)',
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 标题 */}
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ color: 'var(--text-primary)', marginBottom: 8 }}>
              <BookOutlined style={{ marginRight: 12, color: 'var(--accent-gold)' }} />
              系统文档中心
            </Title>
            <Text type="secondary">Quant-Trade System v2.5.0 技术文档</Text>
          </div>

          <Divider />

          {/* 文档标签页 */}
          <Tabs activeKey={activeTab} onChange={setActiveTab} size="large">
            {/* 系统架构 */}
            <TabPane
              tab={
                <span>
                  <CodeOutlined />
                  系统架构
                </span>
              }
              key="architecture"
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Card
                  size="small"
                  style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}
                >
                  <Space>
                    <FileTextOutlined style={{ fontSize: 24, color: 'var(--accent-blue)' }} />
                    <div>
                      <Title level={5} style={{ margin: 0 }}>
                        系统架构文档
                      </Title>
                      <Text type="secondary">
                        完整的系统架构说明、技术栈、功能模块完成度
                      </Text>
                    </div>
                    <Button
                      type="primary"
                      icon={<ExportOutlined />}
                      onClick={openArchitectureDoc}
                    >
                      打开文档
                    </Button>
                  </Space>
                </Card>

                <Title level={4}>技术栈</Title>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <Card
                    title="后端技术"
                    size="small"
                    style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}
                  >
                    <Table
                      dataSource={techStackData.backend}
                      columns={techColumns}
                      pagination={false}
                      size="small"
                      rowKey="name"
                    />
                  </Card>
                  <Card
                    title="前端技术"
                    size="small"
                    style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}
                  >
                    <Table
                      dataSource={techStackData.frontend}
                      columns={techColumns}
                      pagination={false}
                      size="small"
                      rowKey="name"
                    />
                  </Card>
                </div>

                <Title level={4}>功能模块完成度</Title>
                <Table
                  dataSource={moduleStatus}
                  columns={moduleColumns}
                  pagination={false}
                  size="small"
                  rowKey="module"
                  style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}
                />
              </Space>
            </TabPane>

            {/* API 文档 */}
            <TabPane
              tab={
                <span>
                  <ApiOutlined />
                  API 文档
                </span>
              }
              key="api"
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Card
                  size="small"
                  style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}
                >
                  <Space>
                    <ApiOutlined style={{ fontSize: 24, color: 'var(--accent-gold)' }} />
                    <div>
                      <Title level={5} style={{ margin: 0 }}>
                        FastAPI 自动生成文档
                      </Title>
                      <Text type="secondary">
                        Swagger UI 和 ReDoc 格式的 API 文档
                      </Text>
                    </div>
                    <Button
                      type="primary"
                      icon={<ExportOutlined />}
                      onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                    >
                      Swagger UI
                    </Button>
                    <Button
                      icon={<ExportOutlined />}
                      onClick={() => window.open('http://localhost:8000/redoc', '_blank')}
                    >
                      ReDoc
                    </Button>
                  </Space>
                </Card>

                <Title level={4}>API 端点列表</Title>
                <Card size="small" style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <Paragraph>
                    <Text strong>认证 API</Text> - <code>/api/v1/auth/*</code>
                    <br />
                    登录、刷新Token、验证Token
                  </Paragraph>
                  <Paragraph>
                    <Text strong>用户 API</Text> - <code>/api/v1/users/*</code>
                    <br />
                    用户CRUD、设置管理
                  </Paragraph>
                  <Paragraph>
                    <Text strong>交易 API</Text> - <code>/api/v1/trading/*</code>
                    <br />
                    订单管理、持仓管理、交易模式切换
                  </Paragraph>
                  <Paragraph>
                    <Text strong>回测 API</Text> - <code>/api/v1/backtest/*</code>
                    <br />
                    回测配置、运行、结果分析
                  </Paragraph>
                  <Paragraph>
                    <Text strong>自选股 API</Text> - <code>/api/v1/watchlist/*</code>
                    <br />
                    分组管理、股票收藏、批量操作
                  </Paragraph>
                  <Paragraph>
                    <Text strong>预警 API</Text> - <code>/api/v1/alerts/*</code>
                    <br />
                    价格预警、预警历史、设置
                  </Paragraph>
                </Card>
              </Space>
            </TabPane>

            {/* 用户指南 */}
            <TabPane
              tab={
                <span>
                  <BookOutlined />
                  用户指南
                </span>
              }
              key="guide"
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Title level={4}>快速开始</Title>
                <Card size="small" style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <Paragraph>
                    <Text strong>1. 登录系统</Text>
                    <br />
                    使用用户名和密码登录系统，获取JWT Token
                  </Paragraph>
                  <Paragraph>
                    <Text strong>2. 订阅股票</Text>
                    <br />
                    在实时行情页面输入股票代码（如：000001.SZ）订阅行情
                  </Paragraph>
                  <Paragraph>
                    <Text strong>3. 设置预警</Text>
                    <br />
                    点击股票行的🔔图标设置价格预警
                  </Paragraph>
                  <Paragraph>
                    <Text strong>4. 添加自选</Text>
                    <br />
                    点击⭐图标将股票添加到自选列表
                  </Paragraph>
                  <Paragraph>
                    <Text strong>5. 导出数据</Text>
                    <br />
                    使用导出按钮将行情数据导出为CSV或Excel
                  </Paragraph>
                </Card>

                <Title level={4}>键盘快捷键</Title>
                <Card size="small" style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <Paragraph>
                    <Text keyboard>Ctrl</Text> + <Text keyboard>K</Text> - 打开搜索
                  </Paragraph>
                  <Paragraph>
                    <Text keyboard>Ctrl</Text> + <Text keyboard>E</Text> - 导出数据
                  </Paragraph>
                  <Paragraph>
                    <Text keyboard>Ctrl</Text> + <Text keyboard>D</Text> - 添加到自选
                  </Paragraph>
                  <Paragraph>
                    <Text keyboard>↑</Text> / <Text keyboard>↓</Text> - 导航选择
                  </Paragraph>
                  <Paragraph>
                    <Text keyboard>Enter</Text> - 打开股票详情
                  </Paragraph>
                  <Paragraph>
                    <Text keyboard>Esc</Text> - 关闭弹窗
                  </Paragraph>
                </Card>
              </Space>
            </TabPane>

            {/* 测试数据 */}
            <TabPane
              tab={
                <span>
                  <DatabaseOutlined />
                  测试数据
                </span>
              }
              key="testdata"
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Title level={4}>测试数据脚本</Title>
                <Card size="small" style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <Paragraph>
                    <Text strong>Python 版本：</Text>
                    <br />
                    <code>backend/database/scripts/seed_test_data.py</code>
                  </Paragraph>
                  <Paragraph>
                    <Text strong>SQL 版本：</Text>
                    <br />
                    <code>backend/database/scripts/seed_test_data.sql</code>
                  </Paragraph>
                </Card>

                <Title level={4}>测试账号</Title>
                <Card size="small" style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <Paragraph>
                    <Text strong>管理员：</Text> admin / admin123
                  </Paragraph>
                  <Paragraph>
                    <Text strong>交易员：</Text> trader_zhang / trader123
                  </Paragraph>
                  <Paragraph>
                    <Text strong>分析师：</Text> analyst_li / analyst123
                  </Paragraph>
                </Card>

                <Title level={4}>测试数据内容</Title>
                <Card size="small" style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <Paragraph>• 25 只测试股票（覆盖金融、科技、消费、医药等行业）</Paragraph>
                  <Paragraph>• 1500+ 条股票历史价格（每只股票60天数据）</Paragraph>
                  <Paragraph>• 5 个测试策略（双均线、RSI、布林带、MACD、多因子）</Paragraph>
                  <Paragraph>• 3 个回测任务（带完整回测结果）</Paragraph>
                  <Paragraph>• 10 条测试订单（各种状态）</Paragraph>
                  <Paragraph>• 6 条测试持仓记录</Paragraph>
                </Card>
              </Space>
            </TabPane>

            {/* 文档链接 */}
            <TabPane
              tab={
                <span>
                  <FileTextOutlined />
                  文档链接
                </span>
              }
              key="links"
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Title level={4}>项目文档</Title>
                <Card size="small" style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Button type="link" icon={<FileTextOutlined />} onClick={() => window.open('/docs/SYSTEM_ARCHITECTURE.html', '_blank')}>
                      系统架构文档
                    </Button>
                    <Button type="link" icon={<FileTextOutlined />} onClick={() => window.open('https://github.com/geminiyubing-jpg/quant-trade-system/blob/main/docs/GETTING_STARTED.md', '_blank')}>
                      快速开始指南
                    </Button>
                    <Button type="link" icon={<FileTextOutlined />} onClick={() => window.open('https://github.com/geminiyubing-jpg/quant-trade-system/blob/main/docs/API.md', '_blank')}>
                      API 文档
                    </Button>
                    <Button type="link" icon={<FileTextOutlined />} onClick={() => window.open('https://github.com/geminiyubing-jpg/quant-trade-system/blob/main/docs/USER_GUIDE.md', '_blank')}>
                      用户指南
                    </Button>
                    <Button type="link" icon={<FileTextOutlined />} onClick={() => window.open('https://github.com/geminiyubing-jpg/quant-trade-system/blob/main/docs/STRATEGY_MODULE_GUIDE.md', '_blank')}>
                      策略模块指南
                    </Button>
                    <Button type="link" icon={<FileTextOutlined />} onClick={() => window.open('https://github.com/geminiyubing-jpg/quant-trade-system/blob/main/docs/POSTGRESQL_SETUP.md', '_blank')}>
                      PostgreSQL 设置
                    </Button>
                    <Button type="link" icon={<FileTextOutlined />} onClick={() => window.open('https://github.com/geminiyubing-jpg/quant-trade-system/blob/main/docs/BLOOMBERG_THEME_GUIDE.md', '_blank')}>
                      Bloomberg 主题指南
                    </Button>
                  </Space>
                </Card>

                <Title level={4}>外部链接</Title>
                <Card size="small" style={{ background: 'var(--bg-secondary)', borderRadius: 8 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Button type="link" icon={<ExportOutlined />} onClick={() => window.open('https://github.com/geminiyubing-jpg/quant-trade-system', '_blank')}>
                      GitHub 仓库
                    </Button>
                    <Button type="link" icon={<ExportOutlined />} onClick={() => window.open('http://localhost:8000/docs', '_blank')}>
                      Swagger API 文档
                    </Button>
                    <Button type="link" icon={<ExportOutlined />} onClick={() => window.open('http://localhost:8000/redoc', '_blank')}>
                      ReDoc API 文档
                    </Button>
                  </Space>
                </Card>
              </Space>
            </TabPane>
          </Tabs>
        </Space>
      </Card>
    </div>
  );
};

export default Docs;
