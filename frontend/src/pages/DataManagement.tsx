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
  Modal,
  Form,
  Input,
  Select,
  message,
  Progress,
  Badge,
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
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useTranslation } from 'react-i18next';
import dataService, {
  ETLTask,
  ETLTaskStatus,
  ETLTaskCreate,
  DataSource,
  QualityReport,
} from '../services/data';
import './DataManagement.css';

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
  const [etlModalVisible, setEtlModalVisible] = useState(false);
  const [etlForm] = Form.useForm();

  // 数据源相关状态
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);

  // 数据质量相关状态
  const [qualityReports, setQualityReports] = useState<QualityReport[]>([]);
  const [qualityLoading, setQualityLoading] = useState(false);

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
  const handleCreateETLTask = async (values: ETLTaskCreate) => {
    try {
      await dataService.createETLTask(values);
      message.success('任务创建成功');
      setEtlModalVisible(false);
      etlForm.resetFields();
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
      render: () => (
        <Space>
          <Button type="link" size="small" icon={<SyncOutlined />}>
            同步
          </Button>
          <Button type="link" size="small" icon={<SettingOutlined />}>
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
          <Button icon={<CloudUploadOutlined />}>导入数据</Button>
          <Button icon={<CloudDownloadOutlined />}>导出数据</Button>
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
          <Card>
            <div className="table-toolbar">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setEtlModalVisible(true)}
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

      {/* 创建 ETL 任务弹窗 */}
      <Modal
        title="新建 ETL 任务"
        open={etlModalVisible}
        onOk={() => etlForm.submit()}
        onCancel={() => { setEtlModalVisible(false); etlForm.resetFields(); }}
        destroyOnClose
      >
        <Form form={etlForm} layout="vertical" onFinish={handleCreateETLTask}>
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>
          <Form.Item
            name="task_type"
            label="任务类型"
            rules={[{ required: true, message: '请选择任务类型' }]}
          >
            <Select placeholder="请选择任务类型">
              <Option value="stock_daily">股票日线</Option>
              <Option value="stock_info">股票信息</Option>
              <Option value="factor">因子数据</Option>
              <Option value="index">指数数据</Option>
              <Option value="custom">自定义</Option>
            </Select>
          </Form.Item>
          <Form.Item name="config" label="配置 (JSON)">
            <Input.TextArea rows={4} placeholder='{"market": "A股"}' />
          </Form.Item>
          <Form.Item name="schedule" label="定时计划 (Cron)">
            <Input placeholder="0 8 * * *" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DataManagement;
