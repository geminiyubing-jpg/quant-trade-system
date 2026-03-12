/**
 * 策略管理页面 - 增强版 v2.0
 * 功能：策略列表、策略注册表、版本控制、配置管理、实例管理
 * 集成后端策略注册表 API
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, Select,
  InputNumber, Tooltip, Dropdown, message, Row, Col,
  Statistic, Tabs, Spin, Typography, Popconfirm, Descriptions, Empty, Alert
} from 'antd';
import {
  DeleteOutlined, PlayCircleOutlined,
  MoreOutlined, RocketOutlined,
  FileTextOutlined, SettingOutlined,
  CheckOutlined, ReloadOutlined, AppstoreAddOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { MenuProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import strategyRegistryService, {
  StrategyMetadata,
  StrategyInstance,
} from '../services/strategyRegistry';

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Text, Title } = Typography;

// 策略状态映射
const lifecycleStatusMap: Record<string, { label: string; color: string }> = {
  development: { label: '开发中', color: 'default' },
  testing: { label: '测试中', color: 'blue' },
  backtest_passed: { label: '回测通过', color: 'cyan' },
  paper_trading: { label: '模拟交易', color: 'orange' },
  live_trading: { label: '实盘交易', color: 'green' },
  deprecated: { label: '已废弃', color: 'red' },
  suspended: { label: '已暂停', color: 'warning' },
};

// 频率映射
const frequencyMap: Record<string, { label: string; icon: string }> = {
  tick: { label: 'Tick', icon: '⚡' },
  '1m': { label: '1分钟', icon: '1️⃣' },
  '5m': { label: '5分钟', icon: '5️⃣' },
  '15m': { label: '15分钟', icon: '🕐' },
  '30m': { label: '30分钟', icon: '🕞' },
  '1h': { label: '1小时', icon: '⏰' },
  '4h': { label: '4小时', icon: '🕓' },
  '1d': { label: '日线', icon: '📅' },
  '1w': { label: '周线', icon: '📆' },
};

// 风险等级映射
const riskLevelMap: Record<string, { label: string; color: string }> = {
  low: { label: '低风险', color: 'green' },
  medium: { label: '中等风险', color: 'orange' },
  high: { label: '高风险', color: 'red' },
};

const StrategyManagement: React.FC = () => {
  useTranslation();

  // 状态
  const [strategies, setStrategies] = useState<StrategyMetadata[]>([]);
  const [instances, setInstances] = useState<StrategyInstance[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyMetadata | null>(null);
  const [selectedInstance, setSelectedInstance] = useState<StrategyInstance | null>(null);

  // 弹窗状态
  const [createInstanceModalVisible, setCreateInstanceModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [instanceDetailModalVisible, setInstanceDetailModalVisible] = useState(false);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [configSaving, setConfigSaving] = useState(false);

  // 过滤条件
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterFrequency, setFilterFrequency] = useState('all');

  // 表单
  const [createInstanceForm] = Form.useForm();
  const [configForm] = Form.useForm();

  // 加载数据
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [strategiesRes, instancesRes, categoriesRes, tagsRes] = await Promise.all([
        strategyRegistryService.getStrategies(),
        strategyRegistryService.getInstances(),
        strategyRegistryService.getCategories(),
        strategyRegistryService.getTags(),
      ]);

      setStrategies(strategiesRes.data || []);
      setInstances(instancesRes || []);
      setCategories(categoriesRes || []);
      // 从策略中提取标签或使用服务返回的标签
      if (tagsRes && tagsRes.length > 0) {
        setTags(tagsRes);
      } else {
        // 从策略中提取标签
        const extractedTags = new Set<string>();
        (strategiesRes.data || []).forEach(s => {
          s.tags?.forEach((t: string) => extractedTags.add(t));
        });
        setTags(Array.from(extractedTags));
      }
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 统计数据
  const stats = useMemo(() => {
    const liveCount = strategies.filter(s => s.status === 'live_trading').length;
    const paperCount = strategies.filter(s => s.status === 'paper_trading').length;
    const instanceCount = instances.length;
    const avgRisk = strategies.length > 0
      ? strategies.filter(s => s.risk_level === 'low').length / strategies.length * 100
      : 0;

    return {
      total: strategies.length,
      live: liveCount,
      paper: paperCount,
      instances: instanceCount,
      safeRatio: avgRisk.toFixed(0),
    };
  }, [strategies, instances]);

  // 从策略中提取所有标签（优先使用从API获取的tags，否则从strategies中提取）
  const allTags = useMemo(() => {
    if (tags.length > 0) {
      return tags;
    }
    const tagSet = new Set<string>();
    strategies.forEach(s => {
      s.tags?.forEach(t => tagSet.add(t));
    });
    return Array.from(tagSet);
  }, [tags, strategies]);

  // 过滤后的策略
  const filteredStrategies = useMemo(() => {
    return strategies.filter(s => {
      if (filterStatus !== 'all' && s.status !== filterStatus) return false;
      if (filterCategory !== 'all' && s.category !== filterCategory) return false;
      if (filterFrequency !== 'all' && s.frequency !== filterFrequency) return false;
      return true;
    });
  }, [strategies, filterStatus, filterCategory, filterFrequency]);

  // 策略表格列
  const strategyColumns: ColumnsType<StrategyMetadata> = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Space>
          <span style={{ fontWeight: 600 }}>{name}</span>
          <Tag color={record.risk_level === 'high' ? 'red' : record.risk_level === 'low' ? 'green' : 'orange'}>
            {riskLevelMap[record.risk_level]?.label || record.risk_level}
          </Tag>
        </Space>
      ),
    },
    {
      title: '策略ID',
      dataIndex: 'strategy_id',
      key: 'strategy_id',
      render: (id) => <Text code>{id}</Text>,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category) => <Tag color="blue">{category}</Tag>,
    },
    {
      title: '频率',
      dataIndex: 'frequency',
      key: 'frequency',
      render: (freq) => (
        <span>{frequencyMap[freq]?.icon} {frequencyMap[freq]?.label || freq}</span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const info = lifecycleStatusMap[status] || { label: status, color: 'default' };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (v) => <Tag>v{v}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => {
        const items: MenuProps['items'] = [
          {
            key: 'instance',
            icon: <AppstoreAddOutlined />,
            label: '创建实例',
            onClick: () => handleCreateInstance(record),
          },
          {
            key: 'config',
            icon: <SettingOutlined />,
            label: '配置参数',
            onClick: () => handleConfig(record),
          },
          { type: 'divider' },
          {
            key: 'detail',
            icon: <FileTextOutlined />,
            label: '查看详情',
            onClick: () => handleViewDetail(record),
          },
        ];

        // 根据状态添加状态变更选项
        if (record.status === 'development') {
          items.push({
            key: 'test',
            icon: <PlayCircleOutlined />,
            label: '开始测试',
            onClick: () => handleStatusChange(record.strategy_id, 'testing'),
          });
        } else if (record.status === 'testing') {
          items.push({
            key: 'backtest',
            icon: <CheckOutlined />,
            label: '标记回测通过',
            onClick: () => handleStatusChange(record.strategy_id, 'backtest_passed'),
          });
        } else if (record.status === 'backtest_passed') {
          items.push({
            key: 'paper',
            icon: <RocketOutlined />,
            label: '开始模拟交易',
            onClick: () => handleStatusChange(record.strategy_id, 'paper_trading'),
          });
        } else if (record.status === 'paper_trading') {
          items.push({
            key: 'live',
            icon: <PlayCircleOutlined style={{ color: '#52c41a' }} />,
            label: '开始实盘交易',
            onClick: () => handleStatusChange(record.strategy_id, 'live_trading'),
          });
        }

        return (
          <Space>
            <Tooltip title="创建实例">
              <Button
                type="text"
                size="small"
                icon={<AppstoreAddOutlined />}
                onClick={() => handleCreateInstance(record)}
              />
            </Tooltip>
            <Tooltip title="详情">
              <Button
                type="text"
                size="small"
                icon={<FileTextOutlined />}
                onClick={() => handleViewDetail(record)}
              />
            </Tooltip>
            <Dropdown menu={{ items }} trigger={['click']}>
              <Button type="text" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  // 实例表格列
  const instanceColumns: ColumnsType<StrategyInstance> = [
    {
      title: '实例ID',
      dataIndex: 'instance_id',
      key: 'instance_id',
      render: (id) => <Text code>{id}</Text>,
    },
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colorMap: Record<string, string> = {
          RUNNING: 'green',
          PAUSED: 'orange',
          STOPPED: 'default',
          ERROR: 'red',
        };
        return <Tag color={colorMap[status] || 'default'}>{status}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<FileTextOutlined />}
              onClick={() => handleViewInstanceDetail(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要移除此实例？"
            onConfirm={() => handleRemoveInstance(record.instance_id)}
          >
            <Tooltip title="移除">
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 处理函数
  const handleViewDetail = (strategy: StrategyMetadata) => {
    setSelectedStrategy(strategy);
    setDetailModalVisible(true);
  };

  const handleCreateInstance = (strategy: StrategyMetadata) => {
    setSelectedStrategy(strategy);
    createInstanceForm.setFieldsValue({
      strategy_id: strategy.strategy_id,
      params: strategy.default_params,
      initial_capital: 100000,
      execution_mode: 'PAPER',
    });
    setCreateInstanceModalVisible(true);
  };

  const handleConfig = (strategy: StrategyMetadata) => {
    setSelectedStrategy(strategy);
    configForm.setFieldsValue({
      params: JSON.stringify(strategy.default_params || {}, null, 2),
    });
    setConfigModalVisible(true);
  };

  // 保存策略配置
  const handleSaveConfig = async () => {
    if (!selectedStrategy) return;

    setConfigSaving(true);
    try {
      const values = await configForm.validateFields();
      let params;
      try {
        params = JSON.parse(values.params);
      } catch {
        message.error('参数配置格式错误，请输入有效的 JSON');
        return;
      }

      // 调用后端 API 保存配置
      try {
        await strategyRegistryService.updateStrategyConfig(selectedStrategy.strategy_id, params);
        message.success('配置保存成功');
      } catch (error) {
        console.error('后端保存失败，使用本地保存:', error);
        // 如果后端 API 不可用，保存到本地存储
        localStorage.setItem(`strategy_config_${selectedStrategy.strategy_id}`, JSON.stringify(params));
        message.success('配置已保存到本地');
      }

      setConfigModalVisible(false);
      loadData();
    } catch (error) {
      console.error('保存配置失败:', error);
      message.error('保存配置失败');
    } finally {
      setConfigSaving(false);
    }
  };

  const handleViewInstanceDetail = (instance: StrategyInstance) => {
    setSelectedInstance(instance);
    setInstanceDetailModalVisible(true);
  };

  const handleStatusChange = async (strategyId: string, newStatus: string) => {
    try {
      await strategyRegistryService.updateStrategyStatus(strategyId, newStatus);
      message.success('状态更新成功');
      loadData();
    } catch (error) {
      message.error('状态更新失败');
    }
  };

  const handleRemoveInstance = async (instanceId: string) => {
    try {
      await strategyRegistryService.removeInstance(instanceId);
      message.success('实例已移除');
      loadData();
    } catch (error) {
      message.error('移除实例失败');
    }
  };

  const handleCreateInstanceSubmit = async () => {
    try {
      const values = await createInstanceForm.validateFields();
      await strategyRegistryService.createInstance({
        strategy_id: values.strategy_id,
        params: values.params,
        initial_capital: values.initial_capital,
        execution_mode: values.execution_mode,
      });
      message.success('实例创建成功');
      setCreateInstanceModalVisible(false);
      loadData();
    } catch (error) {
      message.error('创建实例失败');
    }
  };

  return (
    <div className="strategy-management">
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, marginBottom: 8 }}>策略管理</Title>
        <Text type="secondary">策略注册表 · 版本控制 · 实例管理 · 配置管理</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="实盘策略"
              value={stats.live}
              prefix={<PlayCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="模拟策略"
              value={stats.paper}
              prefix={<RocketOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="运行实例"
              value={stats.instances}
              prefix={<AppstoreAddOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="低风险占比"
              value={stats.safeRatio}
              suffix="%"
              prefix={<CheckOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 主内容 */}
      <Tabs defaultActiveKey="strategies">
        <TabPane tab="策略注册表" key="strategies">
          <Card
            extra={
              <Space>
                <Select
                  value={filterStatus}
                  onChange={setFilterStatus}
                  style={{ width: 120 }}
                  placeholder="状态过滤"
                >
                  <Option value="all">全部状态</Option>
                  {Object.entries(lifecycleStatusMap).map(([key, val]) => (
                    <Option key={key} value={key}>{val.label}</Option>
                  ))}
                </Select>
                <Select
                  value={filterCategory}
                  onChange={setFilterCategory}
                  style={{ width: 120 }}
                  placeholder="分类过滤"
                >
                  <Option value="all">全部分类</Option>
                  {categories.map(c => (
                    <Option key={c} value={c}>{c}</Option>
                  ))}
                </Select>
                <Select
                  value={filterFrequency}
                  onChange={setFilterFrequency}
                  style={{ width: 120 }}
                  placeholder="频率过滤"
                >
                  <Option value="all">全部频率</Option>
                  {Object.entries(frequencyMap).map(([key, val]) => (
                    <Option key={key} value={key}>{val.label}</Option>
                  ))}
                </Select>
                <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
              </Space>
            }
          >
            <Spin spinning={loading}>
              <Table
                columns={strategyColumns}
                dataSource={filteredStrategies}
                rowKey="strategy_id"
                pagination={{ pageSize: 10 }}
                locale={{ emptyText: <Empty description="暂无策略" /> }}
              />
            </Spin>
          </Card>
        </TabPane>

        <TabPane tab={`运行实例 (${instances.length})`} key="instances">
          <Card>
            <Spin spinning={loading}>
              <Table
                columns={instanceColumns}
                dataSource={instances}
                rowKey="instance_id"
                pagination={{ pageSize: 10 }}
                locale={{ emptyText: <Empty description="暂无运行实例" /> }}
              />
            </Spin>
          </Card>
        </TabPane>

        <TabPane tab="分类与标签" key="tags">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="策略分类">
                {categories.length > 0 ? (
                  <Space wrap>
                    {categories.map(c => (
                      <Tag key={c} color="blue" style={{ margin: 4 }}>
                        {c} ({strategies.filter(s => s.category === c).length})
                      </Tag>
                    ))}
                  </Space>
                ) : (
                  <Empty description="暂无分类" />
                )}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="策略标签">
                {allTags.length > 0 ? (
                  <Space wrap>
                    {allTags.map(t => (
                      <Tag key={t} style={{ margin: 4 }}>
                        {t}
                      </Tag>
                    ))}
                  </Space>
                ) : (
                  <Empty description="暂无标签" />
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* 策略详情弹窗 */}
      <Modal
        title={selectedStrategy?.name}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedStrategy && (
          <Tabs defaultActiveKey="overview">
            <TabPane tab="概览" key="overview">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="策略ID">{selectedStrategy.strategy_id}</Descriptions.Item>
                <Descriptions.Item label="版本">{selectedStrategy.version}</Descriptions.Item>
                <Descriptions.Item label="作者">{selectedStrategy.author || '-'}</Descriptions.Item>
                <Descriptions.Item label="分类">{selectedStrategy.category}</Descriptions.Item>
                <Descriptions.Item label="频率">{frequencyMap[selectedStrategy.frequency]?.label}</Descriptions.Item>
                <Descriptions.Item label="风险等级">
                  <Tag color={riskLevelMap[selectedStrategy.risk_level]?.color}>
                    {riskLevelMap[selectedStrategy.risk_level]?.label}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="状态" span={2}>
                  <Tag color={lifecycleStatusMap[selectedStrategy.status]?.color}>
                    {lifecycleStatusMap[selectedStrategy.status]?.label}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>
                  {selectedStrategy.description || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="支持市场" span={2}>
                  {selectedStrategy.supported_markets.join(', ')}
                </Descriptions.Item>
                <Descriptions.Item label="标签" span={2}>
                  <Space>
                    {selectedStrategy.tags.map(t => <Tag key={t}>{t}</Tag>)}
                  </Space>
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
            <TabPane tab="参数配置" key="params">
              <Alert
                message="默认参数"
                description={
                  <pre style={{
                    margin: 0,
                    maxHeight: 300,
                    overflow: 'auto',
                    background: 'rgba(30, 30, 30, 0.95)',
                    padding: 12,
                    borderRadius: 6,
                    color: '#ffffff',
                    fontSize: 12,
                    lineHeight: 1.6,
                  }}>
                    {JSON.stringify(selectedStrategy.default_params, null, 2)}
                  </pre>
                }
                type="info"
              />
            </TabPane>
            <TabPane tab="参数Schema" key="schema">
              <pre style={{
                maxHeight: 400,
                overflow: 'auto',
                background: 'rgba(30, 30, 30, 0.95)',
                padding: 16,
                borderRadius: 8,
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                fontSize: 13,
                lineHeight: 1.6,
              }}>
                {JSON.stringify(selectedStrategy.params_schema, null, 2)}
              </pre>
            </TabPane>
          </Tabs>
        )}
      </Modal>

      {/* 创建实例弹窗 */}
      <Modal
        title={`创建实例 - ${selectedStrategy?.name}`}
        open={createInstanceModalVisible}
        onCancel={() => setCreateInstanceModalVisible(false)}
        onOk={handleCreateInstanceSubmit}
        width={600}
      >
        <Form form={createInstanceForm} layout="vertical">
          <Form.Item name="strategy_id" hidden>
            <Input />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="initial_capital" label="初始资金" rules={[{ required: true }]}>
                <InputNumber
                  style={{ width: '100%' }}
                  min={10000}
                  step={10000}
                  formatter={v => `¥ ${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="execution_mode" label="执行模式" rules={[{ required: true }]}>
                <Select>
                  <Option value="PAPER">🧪 模拟交易</Option>
                  <Option value="LIVE">⚡ 实盘交易</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="params" label="策略参数">
            <TextArea
              rows={6}
              placeholder='{"param1": value1}'
              onChange={(e) => {
                try {
                  const params = JSON.parse(e.target.value);
                  createInstanceForm.setFieldsValue({ params });
                } catch {}
              }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 配置弹窗 */}
      <Modal
        title={`配置参数 - ${selectedStrategy?.name}`}
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        onOk={handleSaveConfig}
        confirmLoading={configSaving}
        width={600}
      >
        <Alert
          message="此功能用于修改策略的默认参数配置，修改后需要重新创建实例才能生效"
          type="info"
          style={{ marginBottom: 16 }}
        />
        <Form form={configForm} layout="vertical">
          <Form.Item
            name="params"
            label="参数配置 (JSON 格式)"
            rules={[
              { required: true, message: '请输入参数配置' },
              {
                validator: (_, value) => {
                  try {
                    JSON.parse(value);
                    return Promise.resolve();
                  } catch {
                    return Promise.reject(new Error('请输入有效的 JSON 格式'));
                  }
                },
              },
            ]}
          >
            <TextArea
              rows={10}
              placeholder='{"param1": "value1", "param2": 100}'
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 实例详情弹窗 */}
      <Modal
        title={`实例详情 - ${selectedInstance?.instance_id}`}
        open={instanceDetailModalVisible}
        onCancel={() => setInstanceDetailModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedInstance && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="实例ID">{selectedInstance.instance_id}</Descriptions.Item>
            <Descriptions.Item label="策略名称">{selectedInstance.name}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedInstance.status === 'RUNNING' ? 'green' : 'default'}>
                {selectedInstance.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="参数">
              <pre style={{
                margin: 0,
                maxHeight: 200,
                overflow: 'auto',
                background: 'rgba(30, 30, 30, 0.95)',
                padding: 12,
                borderRadius: 6,
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                fontSize: 12,
                lineHeight: 1.5,
              }}>
                {JSON.stringify(selectedInstance.parameters, null, 2)}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default StrategyManagement;
