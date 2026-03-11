/**
 * SmartTaskWizard - 智能任务创建向导
 *
 * 分步创建 ETL 任务：
 * 1. 选择任务类型
 * 2. 配置任务参数
 * 3. 设置调度计划（可选）
 * 4. 确认并创建
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Modal,
  Steps,
  Card,
  Form,
  Input,
  Select,
  Radio,
  Checkbox,
  Button,
  Space,
  Typography,
  Divider,
  message,
  Row,
  Col,
  Switch,
} from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

import {
  TASK_TYPE_CONFIGS,
  getTaskConfig,
  generateTaskName,
  getDateRangeFromPreset,
  DATE_RANGE_PRESETS,
  TaskTypeConfig,
} from '../config/taskSchemas';
import StockSelector from './StockSelector';

const { Option } = Select;
const { Text, Paragraph } = Typography;

// ==============================================
// 类型定义
// ==============================================

// 任务类型
type TaskType = 'stock_daily' | 'stock_info' | 'factor' | 'index' | 'custom';

interface SmartTaskWizardProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: (task: TaskCreateParams) => Promise<void>;
  initialTaskType?: string;
}

export interface TaskCreateParams {
  name: string;
  task_type: TaskType;
  config: Record<string, any>;
  schedule?: string;
}

// ==============================================
// 主组件
// ==============================================

const SmartTaskWizard: React.FC<SmartTaskWizardProps> = ({
  visible,
  onClose,
  onSubmit,
  initialTaskType,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedType, setSelectedType] = useState<string>(initialTaskType || '');
  const [form] = Form.useForm();
  const [enableSchedule, setEnableSchedule] = useState(false);
  const [schedulePreset, setSchedulePreset] = useState('daily');
  const [customSchedule, setCustomSchedule] = useState('');
  const [loading, setLoading] = useState(false);

  // 当前任务配置
  const currentTaskConfig = useMemo<TaskTypeConfig | undefined>(
    () => getTaskConfig(selectedType),
    [selectedType]
  );

  // 重置向导
  const resetWizard = useCallback(() => {
    setCurrentStep(0);
    setSelectedType(initialTaskType || '');
    form.resetFields();
    setEnableSchedule(false);
    setSchedulePreset('daily');
    setCustomSchedule('');
  }, [form, initialTaskType]);

  // 关闭弹窗
  const handleClose = () => {
    resetWizard();
    onClose();
  };

  // 选择任务类型
  const handleSelectType = (type: string) => {
    setSelectedType(type);
    const config = getTaskConfig(type);
    // 设置默认值
    if (config) {
      const defaultValues: Record<string, any> = {};
      config.fields.forEach((field) => {
        if (field.default !== undefined) {
          defaultValues[field.name] = field.default;
        }
      });
      form.setFieldsValue(defaultValues);
    }
    setCurrentStep(1);
  };

  // 下一步
  const handleNext = async () => {
    if (currentStep === 1) {
      try {
        await form.validateFields();
        setCurrentStep(2);
      } catch (error) {
        // 表单验证失败
      }
    } else if (currentStep === 2) {
      setCurrentStep(3);
    }
  };

  // 上一步
  const handlePrev = () => {
    setCurrentStep(Math.max(0, currentStep - 1));
  };

  // 提交任务
  const handleSubmit = async () => {
    setLoading(true);
    try {
      const formValues = form.getFieldsValue();
      const config = processConfig(formValues);
      const taskName = generateTaskName(selectedType, config);

      const taskParams: TaskCreateParams = {
        name: taskName,
        task_type: selectedType,
        config,
        schedule: enableSchedule ? getScheduleCron() : undefined,
      };

      await onSubmit(taskParams);
      message.success('任务创建成功');
      handleClose();
    } catch (error) {
      message.error('创建任务失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理配置数据
  const processConfig = (values: Record<string, any>): Record<string, any> => {
    const config: Record<string, any> = {};

    Object.entries(values).forEach(([key, value]) => {
      if (value === undefined || value === null) return;

      // 处理日期范围
      if (key === 'date_range') {
        if (typeof value === 'string') {
          // 预设值
          const [start, end] = getDateRangeFromPreset(value);
          config.start_date = start;
          config.end_date = end;
        } else if (Array.isArray(value) && value.length === 2) {
          // 自定义日期
          config.start_date = value[0].format('YYYY-MM-DD');
          config.end_date = value[1].format('YYYY-MM-DD');
        }
      } else {
        config[key] = value;
      }
    });

    return config;
  };

  // 获取调度 Cron 表达式
  const getScheduleCron = (): string => {
    if (customSchedule) return customSchedule;

    const presets: Record<string, string> = {
      daily: '0 18 * * *',           // 每天 18:00
      weekdays: '0 18 * * 1-5',      // 工作日 18:00
      weekly: '0 18 * * 1',          // 每周一 18:00
      monthly: '0 18 1 * *',         // 每月1日 18:00
    };

    return presets[schedulePreset] || presets.daily;
  };

  // 渲染任务类型选择
  const renderTypeSelection = () => (
    <div className="task-type-grid">
      {TASK_TYPE_CONFIGS.map((config) => (
        <Card
          key={config.type}
          hoverable
          className={`task-type-card ${selectedType === config.type ? 'selected' : ''}`}
          onClick={() => handleSelectType(config.type)}
          style={{ borderColor: selectedType === config.type ? config.color : undefined }}
        >
          <div className="card-content">
            <div className="card-icon" style={{ color: config.color }}>
              {config.icon}
            </div>
            <div className="card-info">
              <Text strong style={{ fontSize: 16 }}>{config.name}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {config.description}
              </Text>
            </div>
          </div>
        </Card>
      ))}

      <style>{`
        .task-type-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
          padding: 8px 0;
        }

        .task-type-card {
          cursor: pointer;
          transition: all 0.3s;
          border-width: 2px;
        }

        .task-type-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .task-type-card.selected {
          background: #f0f5ff;
        }

        .card-content {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }

        .card-icon {
          font-size: 28px;
          flex-shrink: 0;
        }

        .card-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        @media (max-width: 640px) {
          .task-type-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );

  // 渲染动态表单字段
  const renderFormField = (field: TaskTypeConfig['fields'][0]) => {
    switch (field.type) {
      case 'stock_selector':
        return (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            rules={[{ required: field.required, message: `请${field.label}` }]}
            tooltip={field.tooltip}
          >
            <StockSelector placeholder={field.placeholder} />
          </Form.Item>
        );

      case 'date_range':
        return (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            initialValue={field.default || 'last_year'}
            tooltip={field.tooltip}
          >
            <Select style={{ width: '100%' }}>
              {DATE_RANGE_PRESETS.map((preset) => (
                <Option key={preset.value} value={preset.value}>
                  {preset.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
        );

      case 'select':
        return (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            initialValue={field.default}
            tooltip={field.tooltip}
          >
            <Select
              mode={field.mode === 'multiple' ? 'multiple' : undefined}
              placeholder={field.placeholder || `请选择${field.label}`}
            >
              {field.options?.map((opt) => {
                const isObject = typeof opt === 'object';
                return (
                  <Option
                    key={isObject ? opt.value : opt}
                    value={isObject ? opt.value : opt}
                  >
                    {isObject ? opt.label : opt}
                  </Option>
                );
              })}
            </Select>
          </Form.Item>
        );

      case 'radio':
        return (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            initialValue={field.default}
            tooltip={field.tooltip}
          >
            <Radio.Group>
              {field.options?.map((opt) => {
                const isObject = typeof opt === 'object';
                return (
                  <Radio
                    key={isObject ? opt.value : opt}
                    value={isObject ? opt.value : opt}
                  >
                    {isObject ? opt.label : opt}
                  </Radio>
                );
              })}
            </Radio.Group>
          </Form.Item>
        );

      case 'checkbox_group':
        return (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            rules={[{ required: field.required, message: `请选择${field.label}` }]}
            tooltip={field.tooltip}
          >
            <Checkbox.Group style={{ width: '100%' }}>
              <Row gutter={[8, 8]}>
                {field.options?.map((opt) => {
                  const isObject = typeof opt === 'object';
                  return (
                    <Col key={isObject ? opt.value : opt} span={12}>
                      <Checkbox value={isObject ? opt.value : opt}>
                        {isObject ? opt.label : opt}
                      </Checkbox>
                    </Col>
                  );
                })}
              </Row>
            </Checkbox.Group>
          </Form.Item>
        );

      case 'input':
        return (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            rules={[{ required: field.required, message: `请输入${field.label}` }]}
            tooltip={field.tooltip}
          >
            <Input.TextArea
              rows={4}
              placeholder={field.placeholder}
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        );

      default:
        return null;
    }
  };

  // 渲染配置表单
  const renderConfigForm = () => {
    if (!currentTaskConfig) return null;

    return (
      <Form
        form={form}
        layout="vertical"
        requiredMark="optional"
      >
        {currentTaskConfig.fields.map(renderFormField)}
      </Form>
    );
  };

  // 渲染调度设置
  const renderScheduleSettings = () => (
    <div className="schedule-settings">
      <Form.Item label="启用定时执行">
        <Switch
          checked={enableSchedule}
          onChange={setEnableSchedule}
          checkedChildren="开启"
          unCheckedChildren="关闭"
        />
      </Form.Item>

      {enableSchedule && (
        <>
          <Form.Item label="执行频率">
            <Select
              value={schedulePreset}
              onChange={setSchedulePreset}
              style={{ width: 200 }}
            >
              <Option value="daily">每天执行</Option>
              <Option value="weekdays">工作日执行</Option>
              <Option value="weekly">每周执行</Option>
              <Option value="monthly">每月执行</Option>
              <Option value="custom">自定义 Cron</Option>
            </Select>
          </Form.Item>

          {schedulePreset === 'custom' && (
            <Form.Item
              label="Cron 表达式"
              tooltip="格式: 秒 分 时 日 月 周，如 0 18 * * * 表示每天 18:00"
            >
              <Input
                value={customSchedule}
                onChange={(e) => setCustomSchedule(e.target.value)}
                placeholder="0 18 * * *"
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>
          )}

          <div className="schedule-preview">
            <InfoCircleOutlined style={{ marginRight: 8 }} />
            <Text type="secondary">
              执行时间: {getScheduleCron()} (Cron)
            </Text>
          </div>
        </>
      )}

      <style>{`
        .schedule-settings {
          padding: 16px;
          background: #fafafa;
          border-radius: 8px;
        }

        .schedule-preview {
          margin-top: 16px;
          padding: 8px 12px;
          background: #e6f7ff;
          border-radius: 4px;
          display: flex;
          align-items: center;
        }
      `}</style>
    </div>
  );

  // 渲染确认页面
  const renderConfirmation = () => {
    const formValues = form.getFieldsValue();
    const config = processConfig(formValues);
    const taskName = generateTaskName(selectedType, config);

    return (
      <div className="confirmation-page">
        <div className="confirm-section">
          <Text type="secondary">任务名称</Text>
          <Text strong style={{ fontSize: 18 }}>{taskName}</Text>
        </div>

        <Divider />

        <div className="confirm-section">
          <Text type="secondary">任务类型</Text>
          <Text>{currentTaskConfig?.name}</Text>
        </div>

        <div className="confirm-section">
          <Text type="secondary">配置参数</Text>
          <Paragraph
            code
            style={{
              background: '#f5f5f5',
              padding: 12,
              borderRadius: 4,
              maxHeight: 150,
              overflow: 'auto',
            }}
          >
            {JSON.stringify(config, null, 2)}
          </Paragraph>
        </div>

        {enableSchedule && (
          <div className="confirm-section">
            <Text type="secondary">定时计划</Text>
            <Text code>{getScheduleCron()}</Text>
          </div>
        )}

        <style>{`
          .confirmation-page {
            padding: 8px 0;
          }

          .confirm-section {
            margin-bottom: 16px;
            display: flex;
            flex-direction: column;
            gap: 4px;
          }
        `}</style>
      </div>
    );
  };

  // 步骤内容
  const stepContents = [
    { title: '选择类型', icon: <CheckCircleOutlined />, content: renderTypeSelection() },
    { title: '配置参数', icon: <SettingOutlined />, content: renderConfigForm() },
    { title: '调度设置', icon: <ClockCircleOutlined />, content: renderScheduleSettings() },
    { title: '确认创建', icon: <CheckCircleOutlined />, content: renderConfirmation() },
  ];

  return (
    <Modal
      title="创建数据任务"
      open={visible}
      onCancel={handleClose}
      width={700}
      footer={null}
      destroyOnClose
    >
      <Steps
        current={currentStep}
        size="small"
        style={{ marginBottom: 24 }}
        items={stepContents.map((s) => ({ title: s.title, icon: s.icon }))}
      />

      <div className="step-content" style={{ minHeight: 300 }}>
        {stepContents[currentStep].content}
      </div>

      <Divider />

      <div className="wizard-footer" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={handleClose}>取消</Button>
        <Space>
          {currentStep > 0 && (
            <Button onClick={handlePrev}>上一步</Button>
          )}
          {currentStep < 3 ? (
            <Button
              type="primary"
              onClick={handleNext}
              disabled={currentStep === 0 && !selectedType}
            >
              下一步
            </Button>
          ) : (
            <Button
              type="primary"
              loading={loading}
              onClick={handleSubmit}
            >
              创建任务
            </Button>
          )}
        </Space>
      </div>
    </Modal>
  );
};

export default SmartTaskWizard;
