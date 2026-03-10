/**
 * 交易确认弹窗组件
 *
 * 提供交易操作的二次确认机制，支持：
 * - 风险提示展示
 * - 密码验证
 * - 验证码验证
 * - 确认/取消操作
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  Button,
  Alert,
  Space,
  Typography,
  Divider,
  Tag,
  Statistic,
  Row,
  Col,
  message,
  Spin,
} from 'antd';
import {
  WarningOutlined,
  SafetyCertificateOutlined,
  LockOutlined,
  MailOutlined,
  MobileOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;
const { Password } = Input;

// 类型定义
export type ConfirmationType =
  | 'ORDER_CREATE'
  | 'ORDER_CANCEL'
  | 'POSITION_CLOSE'
  | 'STRATEGY_START'
  | 'STRATEGY_STOP'
  | 'RISK_OVERRIDE';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface TradeConfirmationProps {
  visible: boolean;
  type: ConfirmationType;
  operationData: Record<string, any>;
  riskAssessment?: {
    risk_level: RiskLevel;
    risk_factors: string[];
    warnings: string[];
    require_confirmation: boolean;
    confirmation_methods: string[];
    estimated_impact: {
      risk_score: number;
      potential_loss: number;
      position_change: number;
    };
  };
  requestId?: string;
  onConfirm: (verificationData: Record<string, any>) => Promise<void>;
  onCancel: () => void;
  onSendCode?: () => Promise<void>;
}

const riskLevelConfig = {
  LOW: { color: 'green', text: '低风险', bgColor: '#f6ffed' },
  MEDIUM: { color: 'orange', text: '中风险', bgColor: '#fff7e6' },
  HIGH: { color: 'red', text: '高风险', bgColor: '#fff1f0' },
  CRITICAL: { color: 'magenta', text: '极高风险', bgColor: '#fff0f6' },
};

const operationTypeConfig: Record<ConfirmationType, { title: string; icon: React.ReactNode }> = {
  ORDER_CREATE: { title: '创建订单确认', icon: <SafetyCertificateOutlined /> },
  ORDER_CANCEL: { title: '取消订单确认', icon: <ExclamationCircleOutlined /> },
  POSITION_CLOSE: { title: '平仓确认', icon: <WarningOutlined /> },
  STRATEGY_START: { title: '启动策略确认', icon: <SafetyCertificateOutlined /> },
  STRATEGY_STOP: { title: '停止策略确认', icon: <ExclamationCircleOutlined /> },
  RISK_OVERRIDE: { title: '风控覆盖确认', icon: <WarningOutlined /> },
};

const TradeConfirmationModal: React.FC<TradeConfirmationProps> = ({
  visible,
  type,
  operationData,
  riskAssessment,
  requestId,
  onConfirm,
  onCancel,
  onSendCode,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const riskConfig = riskAssessment
    ? riskLevelConfig[riskAssessment.risk_level]
    : riskLevelConfig.LOW;

  const opConfig = operationTypeConfig[type];

  // 倒计时
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // 发送验证码
  const handleSendCode = async () => {
    if (!onSendCode) return;

    setSendingCode(true);
    try {
      await onSendCode();
      message.success('验证码已发送');
      setCountdown(60);
    } catch (error) {
      message.error('验证码发送失败');
    } finally {
      setSendingCode(false);
    }
  };

  // 确认操作
  const handleConfirm = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const verificationData = {
        password: values.password,
        verification_code: values.verificationCode,
        totp_code: values.totpCode,
        request_id: requestId,
      };

      await onConfirm(verificationData);
      message.success('操作确认成功');
      form.resetFields();
    } catch (error: any) {
      message.error(error?.message || '操作确认失败');
    } finally {
      setLoading(false);
    }
  };

  // 取消操作
  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  // 渲染操作详情
  const renderOperationDetails = () => {
    const { symbol, quantity, price, estimated_value, side } = operationData;

    return (
      <div style={{ background: '#fafafa', padding: 16, borderRadius: 8, marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          {symbol && (
            <Col span={8}>
              <Statistic title="股票代码" value={symbol} />
            </Col>
          )}
          {side && (
            <Col span={8}>
              <Statistic
                title="交易方向"
                value={side === 'BUY' ? '买入' : '卖出'}
                valueStyle={{ color: side === 'BUY' ? '#cf1322' : '#3f8600' }}
              />
            </Col>
          )}
          {quantity && (
            <Col span={8}>
              <Statistic title="委托数量" value={quantity} suffix="股" />
            </Col>
          )}
          {price && (
            <Col span={8}>
              <Statistic title="委托价格" value={price} prefix="¥" precision={2} />
            </Col>
          )}
          {estimated_value && (
            <Col span={8}>
              <Statistic
                title="预估金额"
                value={estimated_value}
                prefix="¥"
                precision={2}
              />
            </Col>
          )}
        </Row>
      </div>
    );
  };

  // 渲染风险提示
  const renderRiskWarnings = () => {
    if (!riskAssessment || riskAssessment.risk_level === 'LOW') return null;

    return (
      <div
        style={{
          background: riskConfig.bgColor,
          padding: 16,
          borderRadius: 8,
          marginBottom: 16,
          border: `1px solid ${riskConfig.color}`,
        }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <WarningOutlined style={{ color: riskConfig.color }} />
            <Text strong style={{ color: riskConfig.color }}>
              {riskConfig.text} - 风险评分: {riskAssessment.estimated_impact.risk_score}
            </Text>
          </Space>

          {riskAssessment.risk_factors.length > 0 && (
            <div>
              <Text type="secondary">风险因素：</Text>
              <div style={{ marginTop: 8 }}>
                {riskAssessment.risk_factors.map((factor, index) => (
                  <Tag key={index} color={riskConfig.color}>
                    {factor}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          {riskAssessment.warnings.length > 0 && (
            <Alert
              type="warning"
              showIcon
              message="注意事项"
              description={
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {riskAssessment.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              }
            />
          )}
        </Space>
      </div>
    );
  };

  // 渲染验证表单
  const renderVerificationForm = () => {
    const methods = riskAssessment?.confirmation_methods || [];

    return (
      <Form form={form} layout="vertical">
        {/* 密码验证 */}
        {methods.includes('password') && (
          <Form.Item
            name="password"
            label="登录密码"
            rules={[{ required: true, message: '请输入登录密码' }]}
          >
            <Password
              prefix={<LockOutlined />}
              placeholder="请输入登录密码确认身份"
              autoComplete="off"
            />
          </Form.Item>
        )}

        {/* 短信验证码 */}
        {methods.includes('sms') && (
          <Form.Item
            name="verificationCode"
            label="短信验证码"
            rules={[
              { required: true, message: '请输入验证码' },
              { len: 6, message: '验证码为6位数字' },
            ]}
          >
            <Input
              prefix={<MobileOutlined />}
              placeholder="请输入短信验证码"
              maxLength={6}
              addonAfter={
                <Button
                  type="link"
                  size="small"
                  onClick={handleSendCode}
                  loading={sendingCode}
                  disabled={countdown > 0}
                  style={{ padding: 0 }}
                >
                  {countdown > 0 ? `${countdown}s` : '获取验证码'}
                </Button>
              }
            />
          </Form.Item>
        )}

        {/* 邮箱验证码 */}
        {methods.includes('email') && !methods.includes('sms') && (
          <Form.Item
            name="verificationCode"
            label="邮箱验证码"
            rules={[
              { required: true, message: '请输入验证码' },
              { len: 6, message: '验证码为6位数字' },
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="请输入邮箱验证码"
              maxLength={6}
              addonAfter={
                <Button
                  type="link"
                  size="small"
                  onClick={handleSendCode}
                  loading={sendingCode}
                  disabled={countdown > 0}
                  style={{ padding: 0 }}
                >
                  {countdown > 0 ? `${countdown}s` : '获取验证码'}
                </Button>
              }
            />
          </Form.Item>
        )}

        {/* 双因素认证 */}
        {methods.includes('2fa') && (
          <Form.Item
            name="totpCode"
            label="双因素认证码"
            rules={[
              { required: true, message: '请输入双因素认证码' },
              { len: 6, message: '认证码为6位数字' },
            ]}
          >
            <Input
              prefix={<SafetyCertificateOutlined />}
              placeholder="请输入 Google Authenticator 验证码"
              maxLength={6}
            />
          </Form.Item>
        )}
      </Form>
    );
  };

  return (
    <Modal
      open={visible}
      title={
        <Space>
          {opConfig.icon}
          <span>{opConfig.title}</span>
        </Space>
      }
      width={600}
      onCancel={handleCancel}
      footer={[
        <Button key="cancel" onClick={handleCancel} disabled={loading}>
          取消操作
        </Button>,
        <Button
          key="confirm"
          type="primary"
          onClick={handleConfirm}
          loading={loading}
          danger={riskAssessment?.risk_level === 'HIGH' || riskAssessment?.risk_level === 'CRITICAL'}
        >
          确认执行
        </Button>,
      ]}
      maskClosable={false}
      destroyOnClose
    >
      <Spin spinning={loading}>
        {/* 操作详情 */}
        {renderOperationDetails()}

        <Divider />

        {/* 风险提示 */}
        {renderRiskWarnings()}

        {/* 验证表单 */}
        {riskAssessment?.require_confirmation && (
          <>
            <Title level={5}>
              <LockOutlined /> 身份验证
            </Title>
            {renderVerificationForm()}
          </>
        )}

        {/* 确认提示 */}
        <Alert
          type="info"
          showIcon
          message="请仔细核对以上信息，确认无误后再执行操作"
          style={{ marginTop: 16 }}
        />
      </Spin>
    </Modal>
  );
};

export default TradeConfirmationModal;
