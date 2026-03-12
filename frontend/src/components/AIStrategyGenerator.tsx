/**
 * AI 策略生成器组件
 *
 * 使用 AI 辅助生成量化交易策略
 */

import React, { useState } from 'react';
import {
  Modal,
  Form,
  Select,
  Input,
  Button,
  Space,
  Spin,
  Alert,
  Typography,
  Divider,
  Card,
  Tag,
  message,
  Row,
  Col,
} from 'antd';
import {
  RobotOutlined,
  CopyOutlined,
  SaveOutlined,
  BulbOutlined,
  StockOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { generateStrategy, getAIStatus, saveAIStrategy, AIServiceStatus } from '../services/ai';

const { Option } = Select;
const { TextArea } = Input;
const { Text, Title, Paragraph } = Typography;

// 策略类型选项
const STRATEGY_TYPES = [
  { value: 'momentum', label: '📈 动量策略', desc: '追踪市场趋势，买入上涨股票' },
  { value: 'mean_reversion', label: '🔄 均值回归', desc: '利用价格回归均值的特性' },
  { value: 'breakout', label: '🚀 突破策略', desc: '捕捉价格突破关键位置的时机' },
  { value: 'pair_trading', label: '⚖️ 配对交易', desc: '利用相关性进行对冲套利' },
  { value: 'factor_based', label: '📊 多因子策略', desc: '基于量化因子选股' },
  { value: 'event_driven', label: '📅 事件驱动', desc: '基于特定事件或新闻交易' },
  { value: 'arbitrage', label: '💱 套利策略', desc: '利用市场定价差异获利' },
  { value: 'turtle_trading', label: '🐢 海龟交易', desc: '经典的趋势跟随系统' },
];

// 风险承受能力选项
const RISK_TOLERANCE_OPTIONS = [
  { value: 'low', label: '🛡️ 保守型', desc: '低风险，稳定收益' },
  { value: 'medium', label: '⚖️ 稳健型', desc: '中等风险，平衡收益' },
  { value: 'high', label: '🚀 激进型', desc: '高风险，高收益潜力' },
];

// 市场状况模板
const MARKET_CONDITION_TEMPLATES = [
  '当前市场处于震荡行情，波动率较低',
  '市场呈现明显上涨趋势，成交量放大',
  '市场处于下跌趋势，避险情绪浓厚',
  '市场风格切换频繁，板块轮动明显',
  '大盘蓝筹股表现优于中小盘',
  '成长股估值较高，价值股受到关注',
  '市场流动性充裕，资金面宽松',
  '外部不确定性增加，市场波动加剧',
];

interface AIStrategyGeneratorProps {
  visible: boolean;
  onClose: () => void;
  onStrategyGenerated?: (strategy: any) => void;
}

const AIStrategyGenerator: React.FC<AIStrategyGeneratorProps> = ({
  visible,
  onClose,
  onStrategyGenerated,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [aiStatus, setAiStatus] = useState<AIServiceStatus | null>(null);
  const [generatedStrategy, setGeneratedStrategy] = useState<any>(null);
  const [rawContent, setRawContent] = useState<string>('');

  // 检查 AI 服务状态
  const checkAIStatus = async () => {
    try {
      const status = await getAIStatus();
      setAiStatus(status);
    } catch (error) {
      console.error('检查 AI 状态失败:', error);
      setAiStatus({ glm5_available: false, mcp_tools_count: 0, mcp_tools: [], status: 'unavailable' });
    }
  };

  // 弹窗打开时检查状态
  React.useEffect(() => {
    if (visible) {
      checkAIStatus();
      setGeneratedStrategy(null);
      setRawContent('');
      form.resetFields();
    }
  }, [visible]);

  // 生成策略
  const handleGenerate = async () => {
    // 检查 AI 服务是否可用
    if (!aiStatus?.glm5_available) {
      message.error('AI 服务不可用，请先配置 GLM API Key');
      return;
    }

    try {
      const values = await form.validateFields();
      setLoading(true);
      setGeneratedStrategy(null);
      setRawContent('');

      const response = await generateStrategy({
        strategy_type: values.strategy_type,
        market_condition: values.market_condition,
        risk_tolerance: values.risk_tolerance || 'medium',
        symbol: values.symbol || undefined,
        custom_prompt: values.custom_prompt || undefined,
      });

      if (response.success && response.data) {
        const content = response.data.generated_content?.content || '';
        setRawContent(content);

        // 尝试解析 JSON 格式的策略内容
        try {
          // 提取 JSON 部分（如果 AI 返回的是 markdown 代码块）
          const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/) ||
                           content.match(/```\s*([\s\S]*?)\s*```/);
          const jsonStr = jsonMatch ? jsonMatch[1] : content;

          // 尝试解析为 JSON
          const parsed = JSON.parse(jsonStr);
          setGeneratedStrategy(parsed);
        } catch {
          // 如果不是 JSON，直接显示原始内容
          setGeneratedStrategy({
            raw_content: content,
            strategy_type: values.strategy_type,
          });
        }

        message.success('策略生成成功！');
      } else {
        throw new Error('AI 返回数据格式错误');
      }
    } catch (error: any) {
      console.error('生成策略失败:', error);

      // 更友好的错误提示
      let errorMsg = '生成策略失败，请重试';
      if (error?.message?.includes('timeout') || error?.message?.includes('超时')) {
        errorMsg = 'AI 服务响应超时，请稍后重试';
      } else if (error?.message?.includes('503') || error?.message?.includes('不可用')) {
        errorMsg = 'AI 服务暂不可用，请检查后端配置';
      } else if (error?.message?.includes('401') || error?.message?.includes('Unauthorized')) {
        errorMsg = 'API Key 无效，请检查配置';
      } else if (error?.message) {
        errorMsg = error.message;
      }

      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 复制策略内容
  const handleCopy = () => {
    const text = generatedStrategy
      ? JSON.stringify(generatedStrategy, null, 2)
      : rawContent;
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  // 保存策略
  const handleSave = async () => {
    if (!generatedStrategy) {
      message.warning('请先生成策略');
      return;
    }

    setSaving(true);
    try {
      const strategyType = form.getFieldValue('strategy_type');
      const marketCondition = form.getFieldValue('market_condition');
      const riskTolerance = form.getFieldValue('risk_tolerance') || 'medium';

      // 获取策略名称
      const strategyName = generatedStrategy.strategy_name ||
        `AI${strategyType.charAt(0).toUpperCase() + strategyType.slice(1)}Strategy`;

      // 调用后端 API 保存策略
      const result = await saveAIStrategy({
        strategy_name: strategyName,
        strategy_type: strategyType,
        description: generatedStrategy.principle || generatedStrategy.description || '',
        content: generatedStrategy,
        risk_level: riskTolerance,
        market_condition: marketCondition,
      });

      if (result.success) {
        message.success(`策略已保存: ${result.data.strategy_id}`);

        // 回调
        if (onStrategyGenerated) {
          onStrategyGenerated({
            ...generatedStrategy,
            strategy_id: result.data.strategy_id,
            strategy_type: strategyType,
            market_condition: marketCondition,
          });
        }

        onClose();
      }
    } catch (error: any) {
      console.error('保存策略失败:', error);
      message.error(error?.message || '保存策略失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={
        <Space>
          <RobotOutlined style={{ color: '#1890ff' }} />
          <span>AI 策略生成器</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={null}
      destroyOnClose
    >
      {/* AI 服务状态 */}
      {aiStatus && (
        <Alert
          message={aiStatus.glm5_available ? 'AI 服务可用' : 'AI 服务不可用'}
          description={
            aiStatus.glm5_available
              ? `GLM-5 已就绪，可用工具: ${aiStatus.mcp_tools_count} 个`
              : '请检查后端 GLM_API_KEY 配置'
          }
          type={aiStatus.glm5_available ? 'success' : 'error'}
          showIcon
          style={{
            marginBottom: 16,
            ...(aiStatus.glm5_available ? {
              backgroundColor: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid rgba(34, 197, 94, 0.4)',
            } : {
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
            })
          }}
        />
      )}

      <Row gutter={24}>
        {/* 左侧：输入表单 */}
        <Col span={10}>
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              risk_tolerance: 'medium',
            }}
          >
            <Form.Item
              name="symbol"
              label={
                <Space>
                  <span>指导股票</span>
                  <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
                    (可选，填入后将获取股票实时信息)
                  </Text>
                </Space>
              }
              tooltip="填入股票代码后，AI 将获取该股票的实时交易信息、基本面、新闻等综合信息来生成针对性策略"
            >
              <Input
                placeholder="例如: 000001.SZ, 600519.SH"
                prefix={<StockOutlined style={{ color: '#1890ff' }} />}
                allowClear
              />
            </Form.Item>

            <Form.Item
              name="strategy_type"
              label="策略类型"
              rules={[{ required: true, message: '请选择策略类型' }]}
            >
              <Select
                placeholder="选择要生成的策略类型"
                optionLabelProp="label"
              >
                {STRATEGY_TYPES.map((type) => (
                  <Option key={type.value} value={type.value} label={type.label}>
                    <div>
                      <div>{type.label}</div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {type.desc}
                      </Text>
                    </div>
                  </Option>
                ))}
              </Select>
            </Form.Item>

            {/* 指导股票选项 */}
            <Form.Item
              name="symbol"
              label={
                <Space>
                  <StockOutlined />
                  <span>指导股票</span>
                  <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
                    (可选)
                  </Text>
                </Space>
              }
              tooltip="填入股票代码后，AI 将获取该股票的实时交易信息、基本面、新闻等综合信息来生成针对性策略"
            >
              <Input
                placeholder="例如: 000001.SZ, 600519.SH"
                allowClear
              />
            </Form.Item>

            <Form.Item
              name="risk_tolerance"
              label="风险承受能力"
              rules={[{ required: true }]}
            >
              <Select optionLabelProp="label">
                {RISK_TOLERANCE_OPTIONS.map((option) => (
                  <Option key={option.value} value={option.value} label={option.label}>
                    <div>
                      <div>{option.label}</div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {option.desc}
                      </Text>
                    </div>
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="market_condition"
              label="市场状况描述"
              rules={[{ required: true, message: '请描述当前市场状况' }]}
            >
              <TextArea
                rows={4}
                placeholder="描述当前市场环境，帮助 AI 生成更适合的策略..."
                showCount
                maxLength={500}
              />
            </Form.Item>

            {/* 快速填充模板 */}
            <Form.Item label={<Text type="secondary">快速填充模板</Text>}>
              <div style={{ maxHeight: 120, overflow: 'auto' }}>
                <Space wrap size={[4, 4]}>
                  {MARKET_CONDITION_TEMPLATES.map((template, index) => (
                    <Tag
                      key={index}
                      style={{ cursor: 'pointer', margin: '2px' }}
                      onClick={() => form.setFieldsValue({ market_condition: template })}
                    >
                      {template.slice(0, 15)}...
                    </Tag>
                  ))}
                </Space>
              </div>
            </Form.Item>

            {/* 自定义策略约束/提示词 */}
            <Form.Item
              name="custom_prompt"
              label={
                <Space>
                  <EditOutlined />
                  <span>策略约束 / 自定义提示词</span>
                  <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
                    (可选)
                  </Text>
                </Space>
              }
              tooltip="输入自然语言约束或提示词，AI 将根据您的要求优化生成的策略。例如：'重点关注流动性好的蓝筹股'、'止损线设为 5%'、'避免在市场波动大时交易'等"
            >
              <TextArea
                rows={3}
                placeholder="例如：&#10;- 重点关注流动性好的蓝筹股&#10;- 止损线设为 5%，止盈线设为 15%&#10;- 避免在市场波动大时交易&#10;- 持仓周期控制在 5-10 个交易日"
                showCount
                maxLength={1000}
              />
            </Form.Item>

            {/* 策略约束模板 */}
            <Form.Item label={<Text type="secondary">常用约束模板</Text>}>
              <div style={{ maxHeight: 100, overflow: 'auto' }}>
                <Space wrap size={[4, 4]}>
                  {[
                    '止损5%，止盈15%',
                    '持仓周期5-10天',
                    '仅交易蓝筹股',
                    '避免追高杀跌',
                    '设置动态仓位管理',
                    '加入波动率过滤',
                  ].map((template, index) => (
                    <Tag
                      key={index}
                      style={{ cursor: 'pointer', margin: '2px' }}
                      onClick={() => {
                        const current = form.getFieldValue('custom_prompt') || '';
                        form.setFieldsValue({
                          custom_prompt: current ? `${current}\n${template}` : template
                        });
                      }}
                    >
                      {template}
                    </Tag>
                  ))}
                </Space>
              </div>
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                icon={<RobotOutlined />}
                onClick={handleGenerate}
                loading={loading}
                disabled={!aiStatus?.glm5_available}
                block
              >
                生成策略
              </Button>
            </Form.Item>
          </Form>
        </Col>

        {/* 右侧：生成结果 */}
        <Col span={14}>
          <Card
            title={
              <Space>
                <BulbOutlined />
                <span>生成结果</span>
              </Space>
            }
            extra={
              generatedStrategy && (
                <Space>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={handleCopy}
                  >
                    复制
                  </Button>
                  <Button
                    size="small"
                    type="primary"
                    icon={<SaveOutlined />}
                    loading={saving}
                    onClick={handleSave}
                  >
                    保存策略
                  </Button>
                </Space>
              )
            }
            style={{
              minHeight: 400,
              backgroundColor: '#1a1a2e',
              borderColor: '#303055',
            }}
            headStyle={{
              backgroundColor: '#1a1a2e',
              borderBottomColor: '#303055',
              color: '#fff',
            }}
            bodyStyle={{
              backgroundColor: '#1a1a2e',
              color: '#e0e0e0',
            }}
          >
            <Spin spinning={loading} tip="AI 正在生成策略...">
              {generatedStrategy ? (
                <div style={{ color: '#e0e0e0' }}>
                  {/* 结构化策略展示 */}
                  {generatedStrategy.strategy_name && (
                    <>
                      <Title level={5} style={{ color: '#fff', marginBottom: 8 }}>
                        {generatedStrategy.strategy_name}
                      </Title>
                      <Divider style={{ margin: '12px 0', borderColor: '#303055' }} />
                    </>
                  )}

                  {generatedStrategy.principle && (
                    <div style={{ marginBottom: 16, color: '#e0e0e0' }}>
                      <Text strong style={{ color: '#4ade80', fontSize: 14 }}>策略原理：</Text>
                      <Paragraph style={{ color: '#e0e0e0', margin: '4px 0' }}>
                        {generatedStrategy.principle}
                      </Paragraph>
                    </div>
                  )}

                  {generatedStrategy.entry_conditions && (
                    <div style={{ marginBottom: 16 }}>
                      <Text strong style={{ color: '#4ade80', fontSize: 14 }}>入场条件：</Text>
                      <ul style={{ margin: '4px 0', paddingLeft: 20, color: '#e0e0e0' }}>
                        {Array.isArray(generatedStrategy.entry_conditions) ?
                          generatedStrategy.entry_conditions.map((c: string, i: number) => (
                            <li key={i} style={{ color: '#e0e0e0' }}>{c}</li>
                          )) : typeof generatedStrategy.entry_conditions === 'object' ?
                            Object.entries(generatedStrategy.entry_conditions).map(([key, value]) => (
                              <li key={key} style={{ color: '#e0e0e0' }}>
                                <Text strong style={{ color: '#60a5fa' }}>{key}：</Text>
                                <span style={{ color: '#e0e0e0' }}>
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </span>
                              </li>
                            )) : <li style={{ color: '#e0e0e0' }}>{String(generatedStrategy.entry_conditions)}</li>
                        }
                      </ul>
                    </div>
                  )}

                  {generatedStrategy.exit_conditions && (
                    <div style={{ marginBottom: 16 }}>
                      <Text strong style={{ color: '#4ade80', fontSize: 14 }}>出场条件：</Text>
                      <ul style={{ margin: '4px 0', paddingLeft: 20, color: '#e0e0e0' }}>
                        {Array.isArray(generatedStrategy.exit_conditions) ?
                          generatedStrategy.exit_conditions.map((c: string, i: number) => (
                            <li key={i} style={{ color: '#e0e0e0' }}>{c}</li>
                          )) : typeof generatedStrategy.exit_conditions === 'object' ?
                            Object.entries(generatedStrategy.exit_conditions).map(([key, value]) => (
                              <li key={key} style={{ color: '#e0e0e0' }}>
                                <Text strong style={{ color: '#60a5fa' }}>{key}：</Text>
                                <span style={{ color: '#e0e0e0' }}>
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </span>
                              </li>
                            )) : <li style={{ color: '#e0e0e0' }}>{String(generatedStrategy.exit_conditions)}</li>
                        }
                      </ul>
                    </div>
                  )}

                  {generatedStrategy.risk_management && (
                    <div style={{ marginBottom: 16 }}>
                      <Text strong style={{ color: '#4ade80', fontSize: 14 }}>风控规则：</Text>
                      <ul style={{ margin: '4px 0', paddingLeft: 20, color: '#e0e0e0' }}>
                        {Array.isArray(generatedStrategy.risk_management) ?
                          generatedStrategy.risk_management.map((c: string, i: number) => (
                            <li key={i} style={{ color: '#e0e0e0' }}>{c}</li>
                          )) : typeof generatedStrategy.risk_management === 'object' ?
                            Object.entries(generatedStrategy.risk_management).map(([key, value]) => (
                              <li key={key} style={{ color: '#e0e0e0' }}>
                                <Text strong style={{ color: '#60a5fa' }}>{key}：</Text>
                                <span style={{ color: '#e0e0e0' }}>
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </span>
                              </li>
                            )) : <li style={{ color: '#e0e0e0' }}>{String(generatedStrategy.risk_management)}</li>
                        }
                      </ul>
                    </div>
                  )}

                  {/* 原始内容展示 */}
                  <Divider style={{ margin: '16px 0', borderColor: '#303055' }} />
                  <Text style={{ color: '#9ca3af', fontSize: 12 }}>
                    原始 AI 输出：
                  </Text>
                  <pre
                    style={{
                      background: '#0f0f1a',
                      padding: 12,
                      borderRadius: 4,
                      maxHeight: 200,
                      overflow: 'auto',
                      fontSize: 12,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                      color: '#d1d5db',
                      border: '1px solid #303055',
                    }}
                  >
                    {rawContent || JSON.stringify(generatedStrategy, null, 2)}
                  </pre>
                </div>
              ) : (
                <div
                  style={{
                    height: 300,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Space direction="vertical" align="center">
                    <RobotOutlined style={{ fontSize: 48, color: '#4b5563' }} />
                    <Text style={{ color: '#9ca3af' }}>
                      选择策略类型并描述市场状况，点击"生成策略"
                    </Text>
                  </Space>
                </div>
              )}
            </Spin>
          </Card>
        </Col>
      </Row>
    </Modal>
  );
};

export default AIStrategyGenerator;
