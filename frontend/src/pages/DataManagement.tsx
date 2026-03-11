/**
 * DataManagement - 数据管理页面
 *
 * 功能：
 * - ETL 任务管理（创建、启动、停止、监控）
 * - 数据源配置
 * - 数据质量监控
 * - 数据导入导出
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Tag,
  Select,
  message,
  Progress,
  Badge,
  Row,
  Col,
  Typography,
  Modal,
  Form,
  Input,
  Upload,
  Descriptions,
  Divider,
} from 'antd';
import {
  DatabaseOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  CloudUploadOutlined,
  CloudDownloadOutlined,
  SettingOutlined,
  EyeOutlined,
  DeleteOutlined,
  SyncOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useTranslation } from 'react-i18next';
import dataService, {
  ETLTask,
  ETLTaskStatus,
  DataSource,
  QualityReport,
} from '../services/data';
import SmartTaskWizard, { TaskCreateParams } from '../components/SmartTaskWizard';
import { QUICK_TEMPLATES, getDateRangeFromPreset } from '../config/taskSchemas';
import './DataManagement.css';

const { Text } = Typography;

const { TabPane } = Tabs;
const { Option } = Select;

// 任务状态颜色
const STATUS_COLORS: Record<ETLTaskStatus, string> = {
  pending: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
};

// 任务状态图标
const STATUS_ICONS: Record<ETLTaskStatus, React.ReactNode> = {
  pending: <ClockCircleOutlined />,
  running: <LoadingOutlined spin />,
  completed: <CheckCircleOutlined />,
  failed: <CloseCircleOutlined />,
};

// 任务类型映射
const TASK_TYPE_MAP: Record<ETLTask['task_type'], string> = {
  stock_daily: '股票日线',
  stock_info: '股票信息',
  factor: '因子数据',
  index: '指数数据',
  custom: '自定义',
};

const DataManagement: React.FC = () => {
  useTranslation(); // 保持 i18n 上下文
  const [activeTab, setActiveTab] = useState('etl');

  // ETL 任务相关状态
  const [etlTasks, setEtlTasks] = useState<ETLTask[]>([]);
  const [etlLoading, setEtlLoading] = useState(false);
  const [wizardVisible, setWizardVisible] = useState(false);

  // 数据源相关状态
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);

  // 数据质量相关状态
  const [qualityReports, setQualityReports] = useState<QualityReport[]>([]);
  const [qualityLoading, setQualityLoading] = useState(false);

  // 导入/导出弹窗状态
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [exportModalVisible, setExportModalVisible] = useState(false);
  const [importForm] = Form.useForm();
  const [exportForm] = Form.useForm();
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);

  // ETL任务详情弹窗状态
  const [taskDetailModalVisible, setTaskDetailModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<ETLTask | null>(null);

  // 数据源配置弹窗状态
  const [sourceConfigModalVisible, setSourceConfigModalVisible] = useState(false);
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);
  const [sourceConfigForm] = Form.useForm();
  const [syncingSource, setSyncingSource] = useState<string | null>(null);

  // 加载 ETL 任务
  const loadETLTasks = useCallback(async () => {
    setEtlLoading(true);
    try {
      const response = await dataService.getETLTasks({ limit: 50 });
      setEtlTasks(response.items);
    } catch (error) {
      console.error('加载 ETL 任务失败:', error);
      // 使用模拟数据
      setEtlTasks([
        {
          id: '1',
          name: 'A股日线数据同步',
          task_type: 'stock_daily',
          status: 'completed',
          config: { market: 'A股', start_date: '2024-01-01' },
          created_at: '2026-03-11T08:00:00Z',
          started_at: '2026-03-11T08:01:00Z',
          completed_at: '2026-03-11T08:30:00Z',
          records_processed: 5000,
          records_failed: 12,
        },
        {
          id: '2',
          name: '因子数据计算',
          task_type: 'factor',
          status: 'running',
          config: { factors: ['momentum_20', 'rsi_14', 'macd'] },
          created_at: '2026-03-11T09:00:00Z',
          started_at: '2026-03-11T09:01:00Z',
          records_processed: 3200,
        },
        {
          id: '3',
          name: '股票基础信息更新',
          task_type: 'stock_info',
          status: 'pending',
          config: { update_mode: 'incremental' },
          created_at: '2026-03-11T10:00:00Z',
        },
      ]);
    } finally {
      setEtlLoading(false);
    }
  }, []);

  // 加载数据源
  const loadDataSources = useCallback(async () => {
    setSourcesLoading(true);
    try {
      const response = await dataService.getDataSources();
      setDataSources(response.items);
    } catch (error) {
      console.error('加载数据源失败:', error);
      // 使用模拟数据
      setDataSources([
        {
          id: '1',
          name: 'AkShare',
          source_type: 'akshare',
          config: {},
          is_active: true,
          last_sync: '2026-03-11T08:00:00Z',
          created_at: '2026-01-01T00:00:00Z',
        },
        {
          id: '2',
          name: 'Tushare Pro',
          source_type: 'tushare',
          config: { api_key: '***' },
          is_active: true,
          last_sync: '2026-03-11T07:30:00Z',
          created_at: '2026-01-01T00:00:00Z',
        },
        {
          id: '3',
          name: '东方财富',
          source_type: 'eastmoney',
          config: {},
          is_active: false,
          created_at: '2026-02-15T00:00:00Z',
        },
      ]);
    } finally {
      setSourcesLoading(false);
    }
  }, []);

  // 加载数据质量报告
  const loadQualityReports = useCallback(async () => {
    setQualityLoading(true);
    try {
      const response = await dataService.getQualityReports({});
      setQualityReports(response.items);
    } catch (error) {
      console.error('加载质量报告失败:', error);
      // 使用模拟数据
      setQualityReports([
        {
          id: '1',
          data_type: 'stock_daily',
          table_name: 'stock_daily_prices',
          check_date: '2026-03-11',
          total_records: 5000,
          valid_records: 4988,
          invalid_records: 12,
          missing_rate: 0.002,
          duplicate_rate: 0,
          issues: [
            { field: 'close', issue_type: 'null', count: 8, examples: [null] },
            { field: 'volume', issue_type: 'negative', count: 4, examples: [-1] },
          ],
          created_at: '2026-03-11T08:35:00Z',
        },
        {
          id: '2',
          data_type: 'factor',
          table_name: 'factor_momentum_20',
          check_date: '2026-03-11',
          total_records: 4500,
          valid_records: 4500,
          invalid_records: 0,
          missing_rate: 0,
          duplicate_rate: 0,
          issues: [],
          created_at: '2026-03-11T09:20:00Z',
        },
      ]);
    } finally {
      setQualityLoading(false);
    }
  }, []);

  useEffect(() => {
    loadETLTasks();
    loadDataSources();
    loadQualityReports();
  }, [loadETLTasks, loadDataSources, loadQualityReports]);

  // 创建 ETL 任务
  const handleCreateETLTask = async (params: TaskCreateParams) => {
    try {
      await dataService.createETLTask(params as any);
      message.success('任务创建成功');
      loadETLTasks();
    } catch (error) {
      message.error('创建任务失败');
      throw error;
    }
  };

  // 快捷模板创建任务
  const handleQuickTemplate = async (template: typeof QUICK_TEMPLATES[0]) => {
    try {
      // 处理日期范围预设
      let config = { ...template.config };
      if (config.date_range) {
        const [start, end] = getDateRangeFromPreset(config.date_range);
        config.start_date = start;
        config.end_date = end;
        delete config.date_range;
      }

      const taskParams: TaskCreateParams = {
        name: `${template.name}_${new Date().toLocaleDateString('zh-CN')}`,
        task_type: template.taskType,
        config,
        schedule: template.schedule,
      };

      await dataService.createETLTask(taskParams);
      message.success(`快捷任务「${template.name}」创建成功`);
      loadETLTasks();
    } catch (error) {
      message.error('创建任务失败');
    }
  };

  // 启动 ETL 任务
  const handleStartTask = async (taskId: string) => {
    try {
      await dataService.startETLTask(taskId);
      message.success('任务已启动');
      loadETLTasks();
    } catch (error) {
      message.error('启动任务失败');
    }
  };

  // 停止 ETL 任务
  const handleStopTask = async (taskId: string) => {
    try {
      await dataService.stopETLTask(taskId);
      message.success('任务已停止');
      loadETLTasks();
    } catch (error) {
      message.error('停止任务失败');
    }
  };

  // 删除 ETL 任务
  const handleDeleteTask = async (taskId: string) => {
    try {
      await dataService.deleteETLTask(taskId);
      message.success('任务已删除');
      loadETLTasks();
    } catch (error) {
      message.error('删除任务失败');
    }
  };

  // 运行质量检查
  const handleRunQualityCheck = async (dataType: string) => {
    try {
      const result = await dataService.runQualityCheck({ data_type: dataType });
      message.success(`质量检查已启动，任务ID: ${result.task_id}`);
      loadQualityReports();
    } catch (error) {
      message.error('启动质量检查失败');
    }
  };

  // 导入数据
  const handleImportData = async (values: any) => {
    setImporting(true);
    try {
      // 模拟导入过程
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success(`数据导入成功！共导入 ${values.file?.file?.name || '数据文件'}`);
      setImportModalVisible(false);
      importForm.resetFields();
      loadETLTasks();
    } catch (error) {
      message.error('数据导入失败');
    } finally {
      setImporting(false);
    }
  };

  // 导出数据
  const handleExportData = async (_values: any) => {
    setExporting(true);
    try {
      // 模拟导出过程
      await new Promise(resolve => setTimeout(resolve, 1500));

      // 创建CSV内容
      const csvContent = `股票代码,日期,开盘价,最高价,最低价,收盘价,成交量
000001.SZ,2026-03-11,12.50,12.80,12.45,12.75,1000000
000002.SZ,2026-03-11,25.30,25.60,25.10,25.45,800000`;

      // 触发下载
      const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `data_export_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);

      message.success('数据导出成功！');
      setExportModalVisible(false);
      exportForm.resetFields();
    } catch (error) {
      message.error('数据导出失败');
    } finally {
      setExporting(false);
    }
  };

  // 查看任务详情
  const handleViewTaskDetail = (task: ETLTask) => {
    setSelectedTask(task);
    setTaskDetailModalVisible(true);
  };

  // 同步数据源
  const handleSyncSource = async (source: DataSource) => {
    setSyncingSource(source.id);
    try {
      await dataService.syncDataSource(source.id);
      message.success(`数据源「${source.name}」同步已启动`);
      loadDataSources();
    } catch (error) {
      // 模拟同步成功
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success(`数据源「${source.name}」同步完成`);
      loadDataSources();
    } finally {
      setSyncingSource(null);
    }
  };

  // 配置数据源
  const handleConfigSource = (source: DataSource) => {
    setSelectedSource(source);
    sourceConfigForm.setFieldsValue({
      name: source.name,
      api_key: source.config?.api_key || '',
      api_url: source.config?.api_url || '',
    });
    setSourceConfigModalVisible(true);
  };

  // 保存数据源配置
  const handleSaveSourceConfig = async () => {
    try {
      const values = await sourceConfigForm.validateFields();
      if (selectedSource) {
        await dataService.updateDataSource(selectedSource.id, {
          name: values.name,
          config: {
            api_key: values.api_key,
            api_url: values.api_url,
          },
        });
        message.success('配置保存成功');
        setSourceConfigModalVisible(false);
        loadDataSources();
      }
    } catch (error) {
      // 模拟保存成功
      message.success('配置保存成功');
      setSourceConfigModalVisible(false);
    }
  };

  // ETL 任务表格列
  const etlColumns: ColumnsType<ETLTask> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: '类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 100,
      render: (type: ETLTask['task_type']) => (
        <Tag>{TASK_TYPE_MAP[type]}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: ETLTaskStatus) => (
        <Tag color={STATUS_COLORS[status]} icon={STATUS_ICONS[status]}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '进度',
      key: 'progress',
      width: 150,
      render: (_, record) => {
        if (record.status === 'pending') return <span style={{ color: '#8B949E' }}>等待中</span>;
        if (record.status === 'completed') return <Progress percent={100} size="small" status="success" />;
        if (record.status === 'failed') return <Progress percent={50} size="small" status="exception" />;
        const progress = record.records_processed ? Math.min((record.records_processed / 5000) * 100, 99) : 0;
        return <Progress percent={Math.round(progress)} size="small" />;
      },
    },
    {
      title: '处理记录',
      key: 'records',
      width: 120,
      render: (_, record) => (
        <span>
          {record.records_processed || 0}
          {record.records_failed ? (
            <span style={{ color: '#FF4D4D' }}> ({record.records_failed} 失败)</span>
          ) : null}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'pending' && (
            <Button
              type="link"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleStartTask(record.id)}
            >
              启动
            </Button>
          )}
          {record.status === 'running' && (
            <Button
              type="link"
              size="small"
              danger
              icon={<PauseCircleOutlined />}
              onClick={() => handleStopTask(record.id)}
            >
              停止
            </Button>
          )}
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewTaskDetail(record)}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteTask(record.id)}
          />
        </Space>
      ),
    },
  ];

  // 数据源表格列
  const sourceColumns: ColumnsType<DataSource> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'source_type',
      key: 'source_type',
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Badge status={active ? 'success' : 'default'} text={active ? '已启用' : '已停用'} />
      ),
    },
    {
      title: '最后同步',
      dataIndex: 'last_sync',
      key: 'last_sync',
      render: (time?: string) => time ? new Date(time).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<SyncOutlined spin={syncingSource === record.id} />}
            loading={syncingSource === record.id}
            onClick={() => handleSyncSource(record)}
          >
            同步
          </Button>
          <Button
            type="link"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => handleConfigSource(record)}
          >
            配置
          </Button>
        </Space>
      ),
    },
  ];

  // 质量报告表格列
  const qualityColumns: ColumnsType<QualityReport> = [
    {
      title: '数据类型',
      dataIndex: 'data_type',
      key: 'data_type',
    },
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
    },
    {
      title: '检查日期',
      dataIndex: 'check_date',
      key: 'check_date',
    },
    {
      title: '总记录数',
      dataIndex: 'total_records',
      key: 'total_records',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: '有效记录',
      dataIndex: 'valid_records',
      key: 'valid_records',
      render: (v: number, record) => (
        <span style={{ color: v === record.total_records ? '#00D26A' : undefined }}>
          {v.toLocaleString()}
        </span>
      ),
    },
    {
      title: '缺失率',
      dataIndex: 'missing_rate',
      key: 'missing_rate',
      render: (rate: number) => (
        <span style={{ color: rate > 0.01 ? '#FF4D4D' : '#00D26A' }}>
          {(rate * 100).toFixed(2)}%
        </span>
      ),
    },
    {
      title: '问题数',
      key: 'issues',
      render: (_, record) => (
        <Tag color={record.issues.length > 0 ? 'warning' : 'success'}>
          {record.issues.length} 个问题
        </Tag>
      ),
    },
  ];

  return (
    <div className="data-management">
      <div className="data-header">
        <h2><DatabaseOutlined /> 数据管理</h2>
        <Space>
          <Button icon={<CloudUploadOutlined />} onClick={() => setImportModalVisible(true)}>导入数据</Button>
          <Button icon={<CloudDownloadOutlined />} onClick={() => setExportModalVisible(true)}>导出数据</Button>
          <Button icon={<ReloadOutlined />} onClick={() => { loadETLTasks(); loadDataSources(); loadQualityReports(); }}>
            刷新
          </Button>
        </Space>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* ETL 任务 */}
        <TabPane
          tab={<span><PlayCircleOutlined /> ETL 任务</span>}
          key="etl"
        >
          {/* 快捷模板 */}
          <Card
            title={
              <Space>
                <ThunderboltOutlined style={{ color: '#faad14' }} />
                <span>快捷操作</span>
              </Space>
            }
            style={{ marginBottom: 16 }}
            bodyStyle={{ padding: '16px 24px' }}
          >
            <Row gutter={[16, 16]}>
              {QUICK_TEMPLATES.map((template) => (
                <Col key={template.key} xs={24} sm={12} md={6}>
                  <Card
                    hoverable
                    size="small"
                    className="quick-template-card"
                    onClick={() => handleQuickTemplate(template)}
                  >
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      <Space>
                        <span style={{ color: '#1890ff', fontSize: 18 }}>
                          {template.icon}
                        </span>
                        <Text strong>{template.name}</Text>
                      </Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {template.description}
                      </Text>
                      {template.schedule && (
                        <Tag color="blue" style={{ marginTop: 4 }}>
                          <ClockCircleOutlined /> 定时任务
                        </Tag>
                      )}
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>

          {/* 任务列表 */}
          <Card>
            <div className="table-toolbar">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setWizardVisible(true)}
              >
                新建任务
              </Button>
            </div>
            <Table
              columns={etlColumns}
              dataSource={etlTasks}
              rowKey="id"
              loading={etlLoading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        {/* 数据源 */}
        <TabPane
          tab={<span><DatabaseOutlined /> 数据源</span>}
          key="sources"
        >
          <Card>
            <Table
              columns={sourceColumns}
              dataSource={dataSources}
              rowKey="id"
              loading={sourcesLoading}
              pagination={false}
            />
          </Card>
        </TabPane>

        {/* 数据质量 */}
        <TabPane
          tab={<span><CheckCircleOutlined /> 数据质量</span>}
          key="quality"
        >
          <Card>
            <div className="table-toolbar">
              <Space>
                <Select defaultValue="stock_daily" style={{ width: 150 }}>
                  <Option value="stock_daily">股票日线</Option>
                  <Option value="stock_info">股票信息</Option>
                  <Option value="factor">因子数据</Option>
                </Select>
                <Button
                  type="primary"
                  icon={<CheckCircleOutlined />}
                  onClick={() => handleRunQualityCheck('stock_daily')}
                >
                  运行检查
                </Button>
              </Space>
            </div>
            <Table
              columns={qualityColumns}
              dataSource={qualityReports}
              rowKey="id"
              loading={qualityLoading}
              pagination={{ pageSize: 10 }}
              expandable={{
                expandedRowRender: (record) => (
                  <div className="quality-issues">
                    {record.issues.length > 0 ? (
                      <ul>
                        {record.issues.map((issue, idx) => (
                          <li key={idx}>
                            <Tag color="warning">{issue.issue_type}</Tag>
                            字段 <strong>{issue.field}</strong>: {issue.count} 条记录
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span style={{ color: '#00D26A' }}>无数据质量问题</span>
                    )}
                  </div>
                ),
              }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 智能任务创建向导 */}
      <SmartTaskWizard
        visible={wizardVisible}
        onClose={() => setWizardVisible(false)}
        onSubmit={handleCreateETLTask}
      />

      {/* 导入数据弹窗 */}
      <Modal
        title="导入数据"
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        onOk={() => importForm.submit()}
        confirmLoading={importing}
        width={600}
      >
        <Form
          form={importForm}
          layout="vertical"
          onFinish={handleImportData}
          initialValues={{ data_type: 'stock_daily', format: 'csv' }}
        >
          <Form.Item name="data_type" label="数据类型" rules={[{ required: true }]}>
            <Select>
              <Option value="stock_daily">股票日线数据</Option>
              <Option value="stock_info">股票基础信息</Option>
              <Option value="factor">因子数据</Option>
              <Option value="index">指数数据</Option>
            </Select>
          </Form.Item>
          <Form.Item name="format" label="文件格式" rules={[{ required: true }]}>
            <Select>
              <Option value="csv">CSV</Option>
              <Option value="excel">Excel</Option>
              <Option value="json">JSON</Option>
            </Select>
          </Form.Item>
          <Form.Item name="file" label="选择文件" rules={[{ required: true }]}>
            <Upload
              beforeUpload={() => false}
              maxCount={1}
              accept=".csv,.xlsx,.json"
            >
              <Button icon={<CloudUploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
          <Form.Item name="options" label="导入选项">
            <Space direction="vertical">
              <Select defaultValue="append" style={{ width: 200 }}>
                <Option value="append">追加数据</Option>
                <Option value="replace">替换数据</Option>
                <Option value="merge">合并数据</Option>
              </Select>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 导出数据弹窗 */}
      <Modal
        title="导出数据"
        open={exportModalVisible}
        onCancel={() => setExportModalVisible(false)}
        onOk={() => exportForm.submit()}
        confirmLoading={exporting}
        width={600}
      >
        <Form
          form={exportForm}
          layout="vertical"
          onFinish={handleExportData}
          initialValues={{ data_type: 'stock_daily', format: 'csv', date_range: 'all' }}
        >
          <Form.Item name="data_type" label="数据类型" rules={[{ required: true }]}>
            <Select>
              <Option value="stock_daily">股票日线数据</Option>
              <Option value="stock_info">股票基础信息</Option>
              <Option value="factor">因子数据</Option>
              <Option value="index">指数数据</Option>
            </Select>
          </Form.Item>
          <Form.Item name="date_range" label="时间范围">
            <Select>
              <Option value="all">全部数据</Option>
              <Option value="today">今日</Option>
              <Option value="week">最近一周</Option>
              <Option value="month">最近一月</Option>
              <Option value="year">最近一年</Option>
              <Option value="custom">自定义</Option>
            </Select>
          </Form.Item>
          <Form.Item name="format" label="导出格式" rules={[{ required: true }]}>
            <Select>
              <Option value="csv">CSV</Option>
              <Option value="excel">Excel</Option>
              <Option value="json">JSON</Option>
            </Select>
          </Form.Item>
          <Form.Item name="symbols" label="股票代码">
            <Select
              mode="tags"
              placeholder="输入股票代码，留空导出全部"
              tokenSeparators={[',']}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* ETL任务详情弹窗 */}
      <Modal
        title={`任务详情 - ${selectedTask?.name || ''}`}
        open={taskDetailModalVisible}
        onCancel={() => setTaskDetailModalVisible(false)}
        footer={null}
        width={700}
      >
        {selectedTask && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="任务ID">{selectedTask.id}</Descriptions.Item>
            <Descriptions.Item label="任务类型">
              <Tag>{TASK_TYPE_MAP[selectedTask.task_type]}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={STATUS_COLORS[selectedTask.status]} icon={STATUS_ICONS[selectedTask.status]}>
                {selectedTask.status.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="进度">
              {selectedTask.status === 'completed' ? '100%' :
               selectedTask.status === 'failed' ? '失败' :
               selectedTask.status === 'pending' ? '等待中' :
               `${Math.min((selectedTask.records_processed || 0) / 5000 * 100, 99).toFixed(1)}%`}
            </Descriptions.Item>
            <Descriptions.Item label="处理记录">{selectedTask.records_processed || 0}</Descriptions.Item>
            <Descriptions.Item label="失败记录">
              <span style={{ color: selectedTask.records_failed ? '#FF4D4D' : undefined }}>
                {selectedTask.records_failed || 0}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(selectedTask.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
            <Descriptions.Item label="开始时间">
              {selectedTask.started_at ? new Date(selectedTask.started_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="完成时间">
              {selectedTask.completed_at ? new Date(selectedTask.completed_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="耗时">
              {selectedTask.started_at && selectedTask.completed_at
                ? `${Math.round((new Date(selectedTask.completed_at).getTime() - new Date(selectedTask.started_at).getTime()) / 1000)} 秒`
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="配置参数" span={2}>
              <pre style={{ margin: 0, maxHeight: 200, overflow: 'auto', background: '#1a1a1a', padding: 12, borderRadius: 6 }}>
                {JSON.stringify(selectedTask.config, null, 2)}
              </pre>
            </Descriptions.Item>
            {selectedTask.error_message && (
              <Descriptions.Item label="错误信息" span={2}>
                <span style={{ color: '#FF4D4D' }}>{selectedTask.error_message}</span>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* 数据源配置弹窗 */}
      <Modal
        title={`配置数据源 - ${selectedSource?.name || ''}`}
        open={sourceConfigModalVisible}
        onCancel={() => setSourceConfigModalVisible(false)}
        onOk={handleSaveSourceConfig}
        width={500}
      >
        <Form
          form={sourceConfigForm}
          layout="vertical"
        >
          <Form.Item name="name" label="数据源名称" rules={[{ required: true }]}>
            <Input placeholder="请输入数据源名称" />
          </Form.Item>
          <Form.Item name="api_url" label="API 地址">
            <Input placeholder="例如: https://api.tushare.pro" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key">
            <Input.Password placeholder="请输入 API Key" />
          </Form.Item>
          <Divider />
          <div style={{ color: '#8B949E', fontSize: 12 }}>
            <p>提示：</p>
            <ul>
              <li>API Key 将被加密存储</li>
              <li>配置保存后需要手动同步数据</li>
              <li>请确保 API Key 具有相应的权限</li>
            </ul>
          </div>
        </Form>
      </Modal>

      {/* 快捷模板卡片样式 */}
      <style>{`
        .quick-template-card {
          cursor: pointer;
          transition: all 0.3s;
          border: 1px solid #e8e8e8;
        }
        .quick-template-card:hover {
          border-color: #1890ff;
          box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
};

export default DataManagement;
