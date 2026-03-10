/**
 * 价格预警设置弹窗组件
 *
 * 功能：
 * - 设置价格预警（价格高于/低于、涨跌幅、成交量）
 * - 查看已有预警列表
 * - 启用/禁用/删除预警
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Form, InputNumber, Select, Button, Table, Switch, Tag, Space, message, Popconfirm, Empty, Spin, Tabs } from 'antd';
import { BellOutlined, DeleteOutlined, PlusOutlined, HistoryOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import alertService from '../services/alerts';
import { AlertType, AlertTypeLabels, PriceAlert, AlertHistory } from '../types/alert';
import type { Quote } from '../types/market';

const { Option } = Select;
const { TabPane } = Tabs;

interface PriceAlertModalProps {
  visible: boolean;
  symbol: string;
  quote: Quote | null;
  onClose: () => void;
}

const PriceAlertModal: React.FC<PriceAlertModalProps> = ({
  visible,
  symbol,
  quote,
  onClose,
}) => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [history, setHistory] = useState<AlertHistory[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState('create');

  // 加载预警列表
  const loadAlerts = useCallback(async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const response = await alertService.getAlerts({ symbol });
      setAlerts(response.items);
    } catch (error) {
      console.error('加载预警列表失败:', error);
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  // 加载预警历史
  const loadHistory = useCallback(async () => {
    if (!symbol) return;
    try {
      const response = await alertService.getHistory({ symbol, limit: 20 });
      setHistory(response.items);
    } catch (error) {
      console.error('加载预警历史失败:', error);
    }
  }, [symbol]);

  useEffect(() => {
    if (visible) {
      loadAlerts();
      loadHistory();
    }
  }, [visible, loadAlerts, loadHistory]);

  // 创建预警
  const handleCreateAlert = async (values: { alert_type: AlertType; target_value: number }) => {
    setSubmitting(true);
    try {
      await alertService.createAlert({
        symbol,
        alert_type: values.alert_type,
        target_value: values.target_value,
      });
      message.success(t('alerts.createSuccess'));
      form.resetFields();
      loadAlerts();
    } catch (error) {
      console.error('创建预警失败:', error);
    } finally {
      setSubmitting(false);
    }
  };

  // 切换预警状态
  const handleToggleAlert = async (alertId: string, isActive: boolean) => {
    try {
      await alertService.updateAlert(alertId, { is_active: isActive });
      message.success(isActive ? t('alerts.enabled') : t('alerts.disabled'));
      loadAlerts();
    } catch (error) {
      console.error('更新预警状态失败:', error);
    }
  };

  // 删除预警
  const handleDeleteAlert = async (alertId: string) => {
    try {
      await alertService.deleteAlert(alertId);
      message.success(t('alerts.deleteSuccess'));
      loadAlerts();
    } catch (error) {
      console.error('删除预警失败:', error);
    }
  };

  // 确认历史记录
  const handleAcknowledge = async (historyId: string) => {
    try {
      await alertService.acknowledgeHistory(historyId);
      loadHistory();
    } catch (error) {
      console.error('确认历史记录失败:', error);
    }
  };

  // 获取预警类型颜色
  const getAlertTypeColor = (type: AlertType): string => {
    const colorMap: Record<AlertType, string> = {
      [AlertType.PRICE_ABOVE]: '#52c41a',
      [AlertType.PRICE_BELOW]: '#ff4d4f',
      [AlertType.CHANGE_PCT_ABOVE]: '#52c41a',
      [AlertType.CHANGE_PCT_BELOW]: '#ff4d4f',
      [AlertType.VOLUME_ABOVE]: '#1890ff',
      [AlertType.VOLUME_BELOW]: '#faad14',
    };
    return colorMap[type] || '#666';
  };

  // 预警列表列定义
  const alertColumns = [
    {
      title: t('alerts.type'),
      dataIndex: 'alert_type',
      key: 'alert_type',
      width: 120,
      render: (type: AlertType) => (
        <Tag color={getAlertTypeColor(type)}>{AlertTypeLabels[type]}</Tag>
      ),
    },
    {
      title: t('alerts.targetValue'),
      dataIndex: 'target_value',
      key: 'target_value',
      width: 100,
      render: (value: number, record: PriceAlert) => {
        if (record.alert_type === AlertType.CHANGE_PCT_ABOVE || record.alert_type === AlertType.CHANGE_PCT_BELOW) {
          return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
        }
        if (record.alert_type === AlertType.VOLUME_ABOVE || record.alert_type === AlertType.VOLUME_BELOW) {
          return (value / 10000).toFixed(0) + '万';
        }
        return value.toFixed(2);
      },
    },
    {
      title: t('alerts.status'),
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean, record: PriceAlert) => (
        <Switch
          size="small"
          checked={isActive && !record.is_triggered}
          onChange={(checked) => handleToggleAlert(record.id, checked)}
          disabled={record.is_triggered}
        />
      ),
    },
    {
      title: t('alerts.triggered'),
      dataIndex: 'is_triggered',
      key: 'is_triggered',
      width: 80,
      render: (triggered: boolean) => (
        triggered ? <Tag color="orange">{t('alerts.yes')}</Tag> : <Tag>{t('alerts.no')}</Tag>
      ),
    },
    {
      title: t('alerts.action'),
      key: 'action',
      width: 60,
      render: (_: unknown, record: PriceAlert) => (
        <Popconfirm
          title={t('alerts.deleteConfirm')}
          onConfirm={() => handleDeleteAlert(record.id)}
          okText={t('common.confirm')}
          cancelText={t('common.cancel')}
        >
          <Button type="link" danger size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  // 历史记录列定义
  const historyColumns = [
    {
      title: t('alerts.type'),
      dataIndex: 'alert_type',
      key: 'alert_type',
      width: 120,
      render: (type: AlertType) => (
        <Tag color={getAlertTypeColor(type)}>{AlertTypeLabels[type]}</Tag>
      ),
    },
    {
      title: t('alerts.targetValue'),
      dataIndex: 'target_value',
      key: 'target_value',
      width: 100,
    },
    {
      title: t('alerts.actualValue'),
      dataIndex: 'actual_value',
      key: 'actual_value',
      width: 100,
    },
    {
      title: t('alerts.triggeredAt'),
      dataIndex: 'triggered_at',
      key: 'triggered_at',
      width: 160,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: t('alerts.acknowledged'),
      dataIndex: 'acknowledged',
      key: 'acknowledged',
      width: 80,
      render: (acknowledged: boolean) => (
        acknowledged ? <Tag color="green">{t('alerts.yes')}</Tag> : <Tag color="orange">{t('alerts.no')}</Tag>
      ),
    },
    {
      title: t('alerts.action'),
      key: 'action',
      width: 80,
      render: (_: unknown, record: AlertHistory) => (
        !record.acknowledged && (
          <Button
            type="link"
            size="small"
            onClick={() => handleAcknowledge(record.id)}
          >
            {t('alerts.acknowledge')}
          </Button>
        )
      ),
    },
  ];

  return (
    <Modal
      title={
        <Space>
          <BellOutlined style={{ color: 'var(--accent-gold)' }} />
          <span>{t('alerts.title')} - {symbol}</span>
          {quote && (
            <Tag color={quote.change >= 0 ? 'success' : 'error'}>
              ¥{quote.price.toFixed(2)} {quote.change >= 0 ? '+' : ''}{quote.change_pct.toFixed(2)}%
            </Tag>
          )}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={700}
      styles={{
        body: { padding: '16px 24px' },
      }}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 创建预警 */}
        <TabPane
          tab={<span><PlusOutlined /> {t('alerts.createAlert')}</span>}
          key="create"
        >
          <Form
            form={form}
            layout="inline"
            onFinish={handleCreateAlert}
            style={{ marginBottom: 16 }}
          >
            <Form.Item
              name="alert_type"
              rules={[{ required: true, message: t('alerts.selectType') }]}
              style={{ width: 150 }}
            >
              <Select placeholder={t('alerts.type')}>
                <Option value={AlertType.PRICE_ABOVE}>{AlertTypeLabels[AlertType.PRICE_ABOVE]}</Option>
                <Option value={AlertType.PRICE_BELOW}>{AlertTypeLabels[AlertType.PRICE_BELOW]}</Option>
                <Option value={AlertType.CHANGE_PCT_ABOVE}>{AlertTypeLabels[AlertType.CHANGE_PCT_ABOVE]}</Option>
                <Option value={AlertType.CHANGE_PCT_BELOW}>{AlertTypeLabels[AlertType.CHANGE_PCT_BELOW]}</Option>
                <Option value={AlertType.VOLUME_ABOVE}>{AlertTypeLabels[AlertType.VOLUME_ABOVE]}</Option>
                <Option value={AlertType.VOLUME_BELOW}>{AlertTypeLabels[AlertType.VOLUME_BELOW]}</Option>
              </Select>
            </Form.Item>
            <Form.Item
              name="target_value"
              rules={[{ required: true, message: t('alerts.inputValue') }]}
              style={{ width: 150 }}
            >
              <InputNumber
                placeholder={t('alerts.targetValue')}
                style={{ width: '100%' }}
                step={0.01}
              />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={submitting}>
                {t('alerts.create')}
              </Button>
            </Form.Item>
          </Form>

          {/* 快捷设置按钮 */}
          <div style={{ marginBottom: 16 }}>
            <Space>
              <span style={{ color: '#666' }}>{t('alerts.quickSet')}:</span>
              {quote && (
                <>
                  <Button
                    size="small"
                    onClick={() => {
                      form.setFieldsValue({
                        alert_type: AlertType.PRICE_ABOVE,
                        target_value: Math.ceil(quote.price * 1.03 * 100) / 100,
                      });
                    }}
                  >
                    +3% ({(quote.price * 1.03).toFixed(2)})
                  </Button>
                  <Button
                    size="small"
                    onClick={() => {
                      form.setFieldsValue({
                        alert_type: AlertType.PRICE_BELOW,
                        target_value: Math.floor(quote.price * 0.97 * 100) / 100,
                      });
                    }}
                  >
                    -3% ({(quote.price * 0.97).toFixed(2)})
                  </Button>
                  <Button
                    size="small"
                    onClick={() => {
                      form.setFieldsValue({
                        alert_type: AlertType.CHANGE_PCT_ABOVE,
                        target_value: 5,
                      });
                    }}
                  >
                    {t('alerts.up')}5%
                  </Button>
                  <Button
                    size="small"
                    onClick={() => {
                      form.setFieldsValue({
                        alert_type: AlertType.CHANGE_PCT_BELOW,
                        target_value: -5,
                      });
                    }}
                  >
                    {t('alerts.down')}5%
                  </Button>
                </>
              )}
            </Space>
          </div>

          {/* 预警列表 */}
          <Spin spinning={loading}>
            {alerts.length > 0 ? (
              <Table
                dataSource={alerts}
                columns={alertColumns}
                rowKey="id"
                size="small"
                pagination={false}
              />
            ) : (
              <Empty description={t('alerts.noAlerts')} />
            )}
          </Spin>
        </TabPane>

        {/* 预警历史 */}
        <TabPane
          tab={<span><HistoryOutlined /> {t('alerts.history')}</span>}
          key="history"
        >
          <Table
            dataSource={history}
            columns={historyColumns}
            rowKey="id"
            size="small"
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: t('alerts.noHistory') }}
          />
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default PriceAlertModal;
