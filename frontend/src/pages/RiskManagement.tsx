/**
 * RiskManagement - 风险管理页面
 *
 * 功能：
 * - 风险规则管理（创建、编辑、启用/禁用）
 * - 风险预警监控
 * - 风险指标展示（VaR、CVaR、最大回撤等）
 * - 风控检查执行
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Popconfirm,
  Badge,
  Statistic,
  Row,
  Col,
  Divider,
} from 'antd';
import {
  SafetyOutlined,
  WarningOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import riskService, {
  RiskRule,
  RiskAlert,
  RiskMetrics,
  RiskRuleType,
  RiskRuleStatus,
} from '../services/risk';
import './RiskManagement.css';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

// 规则类型映射
const RULE_TYPE_MAP: Record<RiskRuleType, string> = {
  position_limit: '持仓限制',
  loss_limit: '亏损限制',
  exposure_limit: '敞口限制',
  custom: '自定义规则',
};

// 严重程度颜色
const SEVERITY_COLORS = {
  low: 'default',
  medium: 'warning',
  high: 'orange',
  critical: 'error',
};

const RiskManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState('rules');

  // 规则相关状态
  const [rules, setRules] = useState<RiskRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [ruleModalVisible, setRuleModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<RiskRule | null>(null);
  const [ruleForm] = Form.useForm();

  // 预警相关状态
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);

  // 风险指标状态
  const [metrics, setMetrics] = useState<RiskMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);

  // 加载风险规则
  const loadRules = useCallback(async () => {
    setRulesLoading(true);
    try {
      const response = await riskService.getRiskRules({ limit: 100 });
      setRules(response.items);
    } catch (error) {
      console.error('加载风险规则失败:', error);
      message.error('加载风险规则失败');
      // 使用模拟数据
      setRules([
        {
          id: '1',
          name: '单只股票持仓上限',
          rule_type: 'position_limit',
          description: '单只股票持仓不超过总资产的10%',
          config: { max_position_ratio: 0.1 },
          severity: 'high',
          status: 'active',
          created_at: '2026-03-01T00:00:00Z',
          updated_at: '2026-03-01T00:00:00Z',
        },
        {
          id: '2',
          name: '单日亏损限制',
          rule_type: 'loss_limit',
          description: '单日亏损超过5%触发预警',
          config: { daily_loss_limit: 0.05 },
          severity: 'critical',
          status: 'active',
          created_at: '2026-03-01T00:00:00Z',
          updated_at: '2026-03-01T00:00:00Z',
        },
        {
          id: '3',
          name: '行业敞口限制',
          rule_type: 'exposure_limit',
          description: '单一行业敞口不超过30%',
          config: { sector_exposure_limit: 0.3 },
          severity: 'medium',
          status: 'active',
          created_at: '2026-03-01T00:00:00Z',
          updated_at: '2026-03-01T00:00:00Z',
        },
      ]);
    } finally {
      setRulesLoading(false);
    }
  }, []);

  // 加载风险预警
  const loadAlerts = useCallback(async () => {
    setAlertsLoading(true);
    try {
      const response = await riskService.getRiskAlerts({ limit: 50 });
      setAlerts(response.items);
    } catch (error) {
      console.error('加载风险预警失败:', error);
      // 使用模拟数据
      setAlerts([
        {
          id: '1',
          rule_id: '1',
          rule_name: '单只股票持仓上限',
          alert_type: 'position_limit',
          severity: 'high',
          message: '贵州茅台(600519)持仓比例达到12.5%，超过10%限制',
          details: { symbol: '600519', current_ratio: 0.125, limit: 0.1 },
          status: 'active',
          created_at: '2026-03-11T10:30:00Z',
        },
        {
          id: '2',
          rule_id: '2',
          rule_name: '单日亏损限制',
          alert_type: 'loss_limit',
          severity: 'critical',
          message: '当日亏损达到4.2%，接近5%限制',
          details: { daily_loss: 0.042, limit: 0.05 },
          status: 'active',
          created_at: '2026-03-11T14:00:00Z',
        },
      ]);
    } finally {
      setAlertsLoading(false);
    }
  }, []);

  // 加载风险指标
  const loadMetrics = useCallback(async () => {
    setMetricsLoading(true);
    try {
      const response = await riskService.getRiskMetrics();
      setMetrics(response);
    } catch (error) {
      console.error('加载风险指标失败:', error);
      // 使用模拟数据
      setMetrics({
        var_95: -0.023,
        var_99: -0.038,
        cvar_95: -0.031,
        cvar_99: -0.045,
        max_drawdown: -0.12,
        volatility: 0.18,
        beta: 1.05,
        sharpe_ratio: 1.35,
        concentration_risk: 0.35,
        sector_concentration: { '科技': 0.25, '金融': 0.20, '消费': 0.15 },
        calculated_at: '2026-03-11T15:00:00Z',
      });
    } finally {
      setMetricsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRules();
    loadAlerts();
    loadMetrics();
  }, [loadRules, loadAlerts, loadMetrics]);

  // 打开创建/编辑规则弹窗
  const openRuleModal = (rule?: RiskRule) => {
    setEditingRule(rule || null);
    if (rule) {
      ruleForm.setFieldsValue({
        name: rule.name,
        rule_type: rule.rule_type,
        description: rule.description,
        severity: rule.severity,
        ...rule.config,
      });
    } else {
      ruleForm.resetFields();
    }
    setRuleModalVisible(true);
  };

  // 保存规则
  const handleSaveRule = async () => {
    try {
      const values = await ruleForm.validateFields();
      const { name, rule_type, description, severity, ...config } = values;

      if (editingRule) {
        await riskService.updateRiskRule(editingRule.id, {
          name,
          description,
          severity,
          config,
        });
        message.success('规则更新成功');
      } else {
        await riskService.createRiskRule({
          name,
          rule_type,
          description,
          severity,
          config,
        });
        message.success('规则创建成功');
      }
      setRuleModalVisible(false);
      loadRules();
    } catch (error) {
      message.error('保存规则失败');
    }
  };

  // 删除规则
  const handleDeleteRule = async (ruleId: string) => {
    try {
      await riskService.deleteRiskRule(ruleId);
      message.success('规则删除成功');
      loadRules();
    } catch (error) {
      message.error('删除规则失败');
    }
  };

  // 切换规则状态
  const handleToggleRule = async (rule: RiskRule) => {
    try {
      if (rule.status === 'active') {
        await riskService.deactivateRiskRule(rule.id);
        message.success('规则已停用');
      } else {
        await riskService.activateRiskRule(rule.id);
        message.success('规则已启用');
      }
      loadRules();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 确认预警
  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await riskService.acknowledgeAlert(alertId);
      message.success('预警已确认');
      loadAlerts();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 解决预警
  const handleResolveAlert = async (alertId: string) => {
    try {
      await riskService.resolveAlert(alertId);
      message.success('预警已解决');
      loadAlerts();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 规则表格列定义
  const ruleColumns: ColumnsType<RiskRule> = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
    },
    {
      title: '类型',
      dataIndex: 'rule_type',
      key: 'rule_type',
      width: 120,
      render: (type: RiskRuleType) => (
        <Tag>{RULE_TYPE_MAP[type]}</Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: RiskRule['severity']) => (
        <Tag color={SEVERITY_COLORS[severity]}>
          {severity.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: RiskRuleStatus) => (
        <Badge
          status={status === 'active' ? 'success' : 'default'}
          text={status === 'active' ? '启用' : '停用'}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openRuleModal(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleToggleRule(record)}
          >
            {record.status === 'active' ? '停用' : '启用'}
          </Button>
          <Popconfirm
            title="确定删除该规则吗？"
            onConfirm={() => handleDeleteRule(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 预警表格列定义
  const alertColumns: ColumnsType<RiskAlert> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: RiskAlert['severity']) => (
        <Tag color={SEVERITY_COLORS[severity]}>
          {severity.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '规则',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 150,
    },
    {
      title: '预警信息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: RiskAlert['status']) => {
        const statusMap = {
          active: { color: 'error', text: '待处理' },
          acknowledged: { color: 'warning', text: '已确认' },
          resolved: { color: 'success', text: '已解决' },
        };
        return (
          <Tag color={statusMap[status].color}>{statusMap[status].text}</Tag>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'active' && (
            <Button
              type="link"
              size="small"
              onClick={() => handleAcknowledgeAlert(record.id)}
            >
              确认
            </Button>
          )}
          {record.status !== 'resolved' && (
            <Button
              type="link"
              size="small"
              onClick={() => handleResolveAlert(record.id)}
            >
              解决
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div className="risk-management">
      <div className="risk-header">
        <h2><SafetyOutlined /> 风险管理</h2>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => { loadRules(); loadAlerts(); loadMetrics(); }}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 风险指标概览 */}
      <Card className="risk-metrics-card" loading={metricsLoading}>
        <Row gutter={16}>
          <Col span={4}>
            <Statistic
              title="VaR (95%)"
              value={metrics?.var_95 ? (metrics.var_95 * 100).toFixed(2) : '-'}
              suffix="%"
              valueStyle={{ color: metrics?.var_95 && metrics.var_95 < 0 ? '#cf1322' : '#3f8600' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="CVaR (95%)"
              value={metrics?.cvar_95 ? (metrics.cvar_95 * 100).toFixed(2) : '-'}
              suffix="%"
              valueStyle={{ color: metrics?.cvar_95 && metrics.cvar_95 < 0 ? '#cf1322' : '#3f8600' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="最大回撤"
              value={metrics?.max_drawdown ? (metrics.max_drawdown * 100).toFixed(2) : '-'}
              suffix="%"
              valueStyle={{ color: '#cf1322' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="波动率"
              value={metrics?.volatility ? (metrics.volatility * 100).toFixed(2) : '-'}
              suffix="%"
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="Beta"
              value={metrics?.beta?.toFixed(2) || '-'}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="夏普比率"
              value={metrics?.sharpe_ratio?.toFixed(2) || '-'}
              valueStyle={{ color: metrics?.sharpe_ratio && metrics.sharpe_ratio > 1 ? '#3f8600' : undefined }}
            />
          </Col>
        </Row>
      </Card>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 风险规则 */}
        <TabPane
          tab={<span><SafetyOutlined /> 风险规则</span>}
          key="rules"
        >
          <Card>
            <div className="table-toolbar">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => openRuleModal()}
              >
                新建规则
              </Button>
            </div>
            <Table
              columns={ruleColumns}
              dataSource={rules}
              rowKey="id"
              loading={rulesLoading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        {/* 风险预警 */}
        <TabPane
          tab={
            <span>
              <WarningOutlined />
              风险预警
              {alerts.filter(a => a.status === 'active').length > 0 && (
                <Badge
                  count={alerts.filter(a => a.status === 'active').length}
                  style={{ marginLeft: 8 }}
                />
              )}
            </span>
          }
          key="alerts"
        >
          <Card>
            <Table
              columns={alertColumns}
              dataSource={alerts}
              rowKey="id"
              loading={alertsLoading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 规则编辑弹窗 */}
      <Modal
        title={editingRule ? '编辑规则' : '新建规则'}
        open={ruleModalVisible}
        onOk={handleSaveRule}
        onCancel={() => setRuleModalVisible(false)}
        width={600}
        destroyOnClose
      >
        <Form form={ruleForm} layout="vertical">
          <Form.Item
            name="name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="请输入规则名称" />
          </Form.Item>
          <Form.Item
            name="rule_type"
            label="规则类型"
            rules={[{ required: true, message: '请选择规则类型' }]}
          >
            <Select placeholder="请选择规则类型" disabled={!!editingRule}>
              <Option value="position_limit">持仓限制</Option>
              <Option value="loss_limit">亏损限制</Option>
              <Option value="exposure_limit">敞口限制</Option>
              <Option value="custom">自定义规则</Option>
            </Select>
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="请输入规则描述" />
          </Form.Item>
          <Form.Item name="severity" label="严重程度" initialValue="medium">
            <Select>
              <Option value="low">低</Option>
              <Option value="medium">中</Option>
              <Option value="high">高</Option>
              <Option value="critical">严重</Option>
            </Select>
          </Form.Item>

          <Divider>规则配置</Divider>

          <Form.Item
            noStyle
            shouldUpdate={(prev, cur) => prev.rule_type !== cur.rule_type}
          >
            {({ getFieldValue }) => {
              const ruleType = getFieldValue('rule_type');
              if (ruleType === 'position_limit') {
                return (
                  <Form.Item
                    name="max_position_ratio"
                    label="最大持仓比例"
                    rules={[{ required: true }]}
                  >
                    <InputNumber
                      min={0}
                      max={1}
                      step={0.01}
                      formatter={v => `${Number(v) * 100}%`}
                      parser={v => Number(v?.replace('%', '')) / 100 as 0 | 1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                );
              }
              if (ruleType === 'loss_limit') {
                return (
                  <>
                    <Form.Item
                      name="daily_loss_limit"
                      label="单日亏损限制"
                      rules={[{ required: true }]}
                    >
                      <InputNumber
                        min={0}
                        max={1}
                        step={0.01}
                        formatter={v => `${Number(v) * 100}%`}
                        parser={v => (v ? Number(v.replace('%', '')) / 100 : 0) as 0 | 1}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                    <Form.Item name="max_drawdown_limit" label="最大回撤限制">
                      <InputNumber
                        min={0}
                        max={1}
                        step={0.01}
                        formatter={v => `${Number(v) * 100}%`}
                        parser={v => (v ? Number(v.replace('%', '')) / 100 : 0) as 0 | 1}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                  </>
                );
              }
              if (ruleType === 'exposure_limit') {
                return (
                  <Form.Item
                    name="sector_exposure_limit"
                    label="行业敞口限制"
                    rules={[{ required: true }]}
                  >
                    <InputNumber
                      min={0}
                      max={1}
                      step={0.01}
                      formatter={v => `${Number(v) * 100}%`}
                      parser={v => (v ? Number(v.replace('%', '')) / 100 : 0) as 0 | 1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                );
              }
              return (
                <Form.Item name="custom_config" label="自定义配置 (JSON)">
                  <TextArea rows={4} placeholder='{"key": "value"}' />
                </Form.Item>
              );
            }}
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RiskManagement;
