/**
 * AI 实验室页面
 * 功能：
 * - AI 策略生成器: 自然语言生成策略代码
 * - AI 智能选股: 根据条件筛选股票
 * - AI 市场分析: 情绪监控和异动解读
 * - 策略进化引擎: 遗传算法和贝叶斯优化
 * - AI 设置: 配置 API Key 等
 */

import React, { useState, useEffect } from 'react';
import {
  Tabs,
  Typography,
  Card,
  Form,
  Input,
  Button,
  Select,
  Space,
  message,
  Spin,
  Empty,
  Divider,
  Tag,
  Row,
  Col,
  Statistic,
  Alert,
  Slider,
} from 'antd';
import {
  RobotOutlined,
  LineChartOutlined,
  StockOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  CopyOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExperimentOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface AIServiceStatus {
  glm5_available: boolean;
  mcp_tools_count: number;
  mcp_tools: string[];
  status: string;
}

const AILab: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('generate');
  const [loading, setLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(true);
  const [aiStatus, setAiStatus] = useState<AIServiceStatus | null>(null);

  // 策略生成表单
  const [strategyForm] = Form.useForm();
  const [generatedStrategy, setGeneratedStrategy] = useState<string>('');

  // 智能选股表单
  const [pickingForm] = Form.useForm();
  const [pickedStocks, setPickedStocks] = useState<any[]>([]);

  // 市场分析表单
  const [analyzeForm] = Form.useForm();
  const [analysisResult, setAnalysisResult] = useState<string>('');

  // AI 设置表单
  const [settingsForm] = Form.useForm();
  const [apiKey, setApiKey] = useState<string>('');
  const [apiUrl, setApiUrl] = useState<string>('https://open.bigmodel.cn/api/paas/v4/chat/completions');
  const [model, setModel] = useState<string>('glm-4');

  // 策略进化表单
  const [evolutionForm] = Form.useForm();
  const [evolutionType, setEvolutionType] = useState<'genetic' | 'bayesian'>('genetic');
  const [evolutionLoading, setEvolutionLoading] = useState(false);
  const [evolutionResult, setEvolutionResult] = useState<any>(null);
  const [taskStatus, setTaskStatus] = useState<string>('');

  // 获取 AI 服务状态
  const fetchAIStatus = async () => {
    setStatusLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/ai/status', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json();
      if (result.success) {
        setAiStatus(result.data);
      }
    } catch (error) {
      console.error('Failed to fetch AI status:', error);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => {
    fetchAIStatus();
    // 从 localStorage 加载 AI 设置
    const savedApiKey = localStorage.getItem('ai_api_key') || '';
    const savedApiUrl = localStorage.getItem('ai_api_url') || 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
    const savedModel = localStorage.getItem('ai_model') || 'glm-4';
    setApiKey(savedApiKey);
    setApiUrl(savedApiUrl);
    setModel(savedModel);
    settingsForm.setFieldsValue({
      apiKey: savedApiKey,
      apiUrl: savedApiUrl,
      model: savedModel,
    });
  }, [settingsForm]);

  // 保存 AI 设置
  const handleSaveSettings = () => {
    localStorage.setItem('ai_api_key', apiKey);
    localStorage.setItem('ai_api_url', apiUrl);
    localStorage.setItem('ai_model', model);
    message.success(t('ai.settingsSaved', 'AI 设置已保存'));
  };

  // 生成策略
  const handleGenerateStrategy = async (values: any) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/ai/generate/strategy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(values),
      });
      const result = await response.json();
      if (result.success) {
        const content = result.data?.generated_content?.content || result.data?.raw_response?.choices?.[0]?.message?.content || '';
        setGeneratedStrategy(content);
        message.success(t('ai.strategyGenerated', '策略生成成功'));
      } else {
        message.error(result.detail || t('ai.generateFailed', '策略生成失败'));
      }
    } catch (error) {
      console.error('Strategy generation error:', error);
      message.error(t('ai.generateFailed', '策略生成失败'));
    } finally {
      setLoading(false);
    }
  };

  // 智能选股
  const handleSmartPick = async (values: any) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/ai/pick/stocks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          criteria: { description: values.criteria },
          universe: values.universe || 'A股全市场',
          top_n: values.top_n || 10,
        }),
      });
      const result = await response.json();
      if (result.success) {
        const content = result.data?.picking_result?.content || result.data?.raw_response?.choices?.[0]?.message?.content || '';
        // 尝试解析 JSON 结果
        try {
          const parsed = JSON.parse(content);
          setPickedStocks(Array.isArray(parsed) ? parsed : [parsed]);
        } catch {
          setPickedStocks([{ content }]);
        }
        message.success(t('ai.pickSuccess', '选股完成'));
      } else {
        message.error(result.detail || t('ai.pickFailed', '选股失败'));
      }
    } catch (error) {
      console.error('Smart pick error:', error);
      message.error(t('ai.pickFailed', '选股失败'));
    } finally {
      setLoading(false);
    }
  };

  // 市场分析
  const handleAnalyzeMarket = async (values: any) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const symbols = values.symbols.split(',').map((s: string) => s.trim()).filter(Boolean);
      const response = await fetch('http://localhost:8000/api/v1/ai/analyze/market', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          symbols,
          analysis_type: values.analysis_type || 'comprehensive',
        }),
      });
      const result = await response.json();
      if (result.success) {
        const content = result.data?.analysis_result?.content || result.data?.raw_response?.choices?.[0]?.message?.content || '';
        setAnalysisResult(content);
        message.success(t('ai.analyzeSuccess', '分析完成'));
      } else {
        message.error(result.detail || t('ai.analyzeFailed', '分析失败'));
      }
    } catch (error) {
      console.error('Market analysis error:', error);
      message.error(t('ai.analyzeFailed', '分析失败'));
    } finally {
      setLoading(false);
    }
  };

  // 复制到剪贴板
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success(t('common.copied', '已复制到剪贴板'));
  };

  // 策略进化 - 遗传算法优化
  const handleGeneticOptimization = async (values: any) => {
    setEvolutionLoading(true);
    setEvolutionResult(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/evolution/genetic/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          param_bounds: {
            ma_short: { min: 5, max: 20 },
            ma_long: { min: 20, max: 60 },
            rsi_period: { min: 7, max: 21 },
            stop_loss: { min: 0.02, max: 0.10 },
            take_profit: { min: 0.05, max: 0.30 },
          },
          population_size: values.population_size || 50,
          generations: values.generations || 50,
          mutation_rate: values.mutation_rate || 0.1,
          crossover_rate: values.crossover_rate || 0.8,
        }),
      });
      const result = await response.json();
      if (result.success) {
        message.success(t('evolution.started', '优化任务已启动'));
        // 轮询获取结果
        pollTaskStatus(result.task_id);
      } else {
        message.error(result.detail || t('evolution.startFailed', '启动失败'));
      }
    } catch (error) {
      console.error('Genetic optimization error:', error);
      message.error(t('evolution.startFailed', '启动失败'));
    } finally {
      setEvolutionLoading(false);
    }
  };

  // 策略进化 - 贝叶斯优化
  const handleBayesianOptimization = async (values: any) => {
    setEvolutionLoading(true);
    setEvolutionResult(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/evolution/bayesian/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          param_bounds: {
            ma_short: { min: 5, max: 20 },
            ma_long: { min: 20, max: 60 },
            rsi_period: { min: 7, max: 21 },
            stop_loss: { min: 0.02, max: 0.10 },
            take_profit: { min: 0.05, max: 0.30 },
          },
          n_iterations: values.n_iterations || 30,
          mode: values.mode || 'maximize',
        }),
      });
      const result = await response.json();
      if (result.success) {
        message.success(t('evolution.started', '优化任务已启动'));
        pollTaskStatus(result.task_id);
      } else {
        message.error(result.detail || t('evolution.startFailed', '启动失败'));
      }
    } catch (error) {
      console.error('Bayesian optimization error:', error);
      message.error(t('evolution.startFailed', '启动失败'));
    } finally {
      setEvolutionLoading(false);
    }
  };

  // 轮询任务状态
  const pollTaskStatus = async (id: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:8000/api/v1/evolution/status/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const result = await response.json();
        setTaskStatus(result.status);

        if (result.status === 'completed') {
          setEvolutionResult(result.result);
          message.success(t('evolution.completed', '优化完成'));
        } else if (result.status === 'failed') {
          message.error(t('evolution.failed', '优化失败'));
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error('Poll status error:', error);
      }
    };

    poll();
  };

  // 快速测试
  const handleQuickTest = async () => {
    setEvolutionLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/evolution/quick-test', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json();
      if (result.success) {
        setEvolutionResult(result.result);
        message.success(t('evolution.testCompleted', '测试完成'));
      } else {
        message.error(result.detail || t('evolution.testFailed', '测试失败'));
      }
    } catch (error) {
      console.error('Quick test error:', error);
      message.error(t('evolution.testFailed', '测试失败'));
    } finally {
      setEvolutionLoading(false);
    }
  };

  // Tab 内容
  const renderTabContent = () => {
    switch (activeTab) {
      case 'generate':
        return (
          <Row gutter={24}>
            <Col span={12}>
              <Card
                title={t('ai.generateStrategy', '生成交易策略')}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)' }}
              >
                <Form
                  form={strategyForm}
                  layout="vertical"
                  onFinish={handleGenerateStrategy}
                  initialValues={{ risk_tolerance: 'medium' }}
                >
                  <Form.Item
                    name="strategy_type"
                    label={t('ai.strategyType', '策略类型')}
                    rules={[{ required: true, message: t('ai.selectStrategyType', '请选择策略类型') }]}
                  >
                    <Select placeholder={t('ai.selectStrategyType', '请选择策略类型')}>
                      <Option value="trend">{t('ai.trendFollowing', '趋势跟踪')}</Option>
                      <Option value="mean_reversion">{t('ai.meanReversion', '均值回归')}</Option>
                      <Option value="momentum">{t('ai.momentum', '动量策略')}</Option>
                      <Option value="arbitrage">{t('ai.arbitrage', '套利策略')}</Option>
                      <Option value="breakout">{t('ai.breakout', '突破策略')}</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item
                    name="market_condition"
                    label={t('ai.marketCondition', '市场状况描述')}
                    rules={[{ required: true, message: t('ai.inputMarketCondition', '请描述市场状况') }]}
                  >
                    <TextArea
                      rows={4}
                      placeholder={t('ai.marketConditionPlaceholder', '例如：当前A股市场处于震荡上行阶段，科技板块表现活跃...')}
                    />
                  </Form.Item>
                  <Form.Item
                    name="risk_tolerance"
                    label={t('ai.riskTolerance', '风险承受能力')}
                  >
                    <Select>
                      <Option value="low">{t('ai.lowRisk', '低风险')}</Option>
                      <Option value="medium">{t('ai.mediumRisk', '中等风险')}</Option>
                      <Option value="high">{t('ai.highRisk', '高风险')}</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      icon={<ThunderboltOutlined />}
                      style={{ background: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)', border: 'none' }}
                    >
                      {t('ai.generate', '生成策略')}
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={12}>
              <Card
                title={t('ai.generatedResult', '生成结果')}
                extra={generatedStrategy && (
                  <Button
                    type="link"
                    icon={<CopyOutlined />}
                    onClick={() => copyToClipboard(generatedStrategy)}
                  >
                    {t('common.copy', '复制')}
                  </Button>
                )}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)', height: '100%' }}
              >
                {loading ? (
                  <div style={{ textAlign: 'center', padding: '60px 0' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16, color: 'var(--bb-text-secondary)' }}>
                      {t('ai.generating', 'AI 正在生成策略...')}
                    </div>
                  </div>
                ) : generatedStrategy ? (
                  <Paragraph
                    style={{
                      whiteSpace: 'pre-wrap',
                      color: 'var(--bb-text)',
                      fontFamily: 'monospace',
                      fontSize: '13px',
                    }}
                  >
                    {generatedStrategy}
                  </Paragraph>
                ) : (
                  <Empty description={t('ai.noResult', '暂无结果')} />
                )}
              </Card>
            </Col>
          </Row>
        );

      case 'pick':
        return (
          <Row gutter={24}>
            <Col span={10}>
              <Card
                title={t('ai.smartPickTitle', '智能选股条件')}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)' }}
              >
                <Form
                  form={pickingForm}
                  layout="vertical"
                  onFinish={handleSmartPick}
                  initialValues={{ universe: 'A股全市场', top_n: 10 }}
                >
                  <Form.Item
                    name="criteria"
                    label={t('ai.pickCriteria', '选股标准')}
                    rules={[{ required: true, message: t('ai.inputPickCriteria', '请输入选股标准') }]}
                  >
                    <TextArea
                      rows={6}
                      placeholder={t('ai.pickCriteriaPlaceholder', '例如：ROE大于15%，市盈率小于30，负债率小于60%，市值大于100亿...')}
                    />
                  </Form.Item>
                  <Form.Item
                    name="universe"
                    label={t('ai.stockUniverse', '股票池')}
                  >
                    <Select>
                      <Option value="A股全市场">{t('ai.allAStocks', 'A股全市场')}</Option>
                      <Option value="沪深300">{t('ai.hs300', '沪深300')}</Option>
                      <Option value="中证500">{t('ai.zz500', '中证500')}</Option>
                      <Option value="创业板">{t('ai.gem', '创业板')}</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item
                    name="top_n"
                    label={t('ai.topN', '返回数量')}
                  >
                    <Select>
                      <Option value={5}>5</Option>
                      <Option value={10}>10</Option>
                      <Option value={20}>20</Option>
                      <Option value={50}>50</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      icon={<StockOutlined />}
                      style={{ background: 'linear-gradient(135deg, #f5c842 0%, #f0a500 100%)', border: 'none' }}
                    >
                      {t('ai.startPick', '开始选股')}
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={14}>
              <Card
                title={t('ai.pickResults', '选股结果')}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)', height: '100%' }}
              >
                {loading ? (
                  <div style={{ textAlign: 'center', padding: '60px 0' }}>
                    <Spin size="large" />
                  </div>
                ) : pickedStocks.length > 0 ? (
                  <div>
                    {pickedStocks.map((stock, index) => (
                      <Card
                        key={index}
                        size="small"
                        style={{
                          marginBottom: '12px',
                          background: 'var(--bb-bg)',
                          borderColor: 'var(--bb-border)',
                        }}
                      >
                        <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                          {typeof stock === 'string' ? stock : stock.content || JSON.stringify(stock, null, 2)}
                        </Paragraph>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <Empty description={t('ai.noPickResult', '暂无选股结果')} />
                )}
              </Card>
            </Col>
          </Row>
        );

      case 'analyze':
        return (
          <Row gutter={24}>
            <Col span={10}>
              <Card
                title={t('ai.marketAnalysis', '市场分析')}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)' }}
              >
                <Form
                  form={analyzeForm}
                  layout="vertical"
                  onFinish={handleAnalyzeMarket}
                  initialValues={{ analysis_type: 'comprehensive' }}
                >
                  <Form.Item
                    name="symbols"
                    label={t('ai.stockSymbols', '股票代码')}
                    rules={[{ required: true, message: t('ai.inputSymbols', '请输入股票代码') }]}
                  >
                    <TextArea
                      rows={3}
                      placeholder={t('ai.symbolsPlaceholder', '输入股票代码，用逗号分隔，如：000001.SZ, 600000.SH')}
                    />
                  </Form.Item>
                  <Form.Item
                    name="analysis_type"
                    label={t('ai.analysisType', '分析类型')}
                  >
                    <Select>
                      <Option value="comprehensive">{t('ai.comprehensive', '综合分析')}</Option>
                      <Option value="technical">{t('ai.technical', '技术分析')}</Option>
                      <Option value="fundamental">{t('ai.fundamental', '基本面分析')}</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      icon={<LineChartOutlined />}
                      style={{ background: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)', border: 'none' }}
                    >
                      {t('ai.startAnalysis', '开始分析')}
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={14}>
              <Card
                title={t('ai.analysisResult', '分析结果')}
                extra={analysisResult && (
                  <Button
                    type="link"
                    icon={<CopyOutlined />}
                    onClick={() => copyToClipboard(analysisResult)}
                  >
                    {t('common.copy', '复制')}
                  </Button>
                )}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)', height: '100%' }}
              >
                {loading ? (
                  <div style={{ textAlign: 'center', padding: '60px 0' }}>
                    <Spin size="large" />
                  </div>
                ) : analysisResult ? (
                  <Paragraph
                    style={{
                      whiteSpace: 'pre-wrap',
                      color: 'var(--bb-text)',
                      fontFamily: 'monospace',
                      fontSize: '13px',
                    }}
                  >
                    {analysisResult}
                  </Paragraph>
                ) : (
                  <Empty description={t('ai.noAnalysisResult', '暂无分析结果')} />
                )}
              </Card>
            </Col>
          </Row>
        );

      case 'settings':
        return (
          <Row gutter={24}>
            <Col span={12}>
              <Card
                title={t('ai.apiSettings', 'API 设置')}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)' }}
              >
                <Form
                  form={settingsForm}
                  layout="vertical"
                >
                  <Form.Item
                    name="apiKey"
                    label={t('ai.apiKey', 'API Key')}
                  >
                    <Input.Password
                      placeholder={t('ai.apiKeyPlaceholder', '输入您的 GLM API Key')}
                      onChange={(e) => setApiKey(e.target.value)}
                    />
                  </Form.Item>
                  <Form.Item
                    name="apiUrl"
                    label={t('ai.apiUrl', 'API URL')}
                  >
                    <Input
                      placeholder={t('ai.apiUrlPlaceholder', 'API 端点 URL')}
                      onChange={(e) => setApiUrl(e.target.value)}
                    />
                  </Form.Item>
                  <Form.Item
                    name="model"
                    label={t('ai.model', '模型')}
                  >
                    <Select onChange={(value) => setModel(value)}>
                      <Option value="glm-4">GLM-4</Option>
                      <Option value="glm-4-flash">GLM-4-Flash</Option>
                      <Option value="glm-4-plus">GLM-4-Plus</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item>
                    <Space>
                      <Button
                        type="primary"
                        icon={<CheckCircleOutlined />}
                        onClick={handleSaveSettings}
                        style={{ background: 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)', border: 'none' }}
                      >
                        {t('common.save', '保存')}
                      </Button>
                      <Button onClick={() => fetchAIStatus()}>
                        {t('ai.testConnection', '测试连接')}
                      </Button>
                    </Space>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={12}>
              <Card
                title={t('ai.serviceStatus', '服务状态')}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)' }}
              >
                {statusLoading ? (
                  <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin />
                  </div>
                ) : aiStatus ? (
                  <div>
                    <Row gutter={16}>
                      <Col span={8}>
                        <Statistic
                          title={t('ai.glm5Status', 'GLM-5 状态')}
                          value={aiStatus.glm5_available ? '可用' : '不可用'}
                          valueStyle={{
                            color: aiStatus.glm5_available ? '#52c41a' : '#ff4d4f',
                          }}
                          prefix={aiStatus.glm5_available ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title={t('ai.toolsCount', '工具数量')}
                          value={aiStatus.mcp_tools_count}
                          suffix={t('ai.tools', '个')}
                        />
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title={t('ai.overallStatus', '整体状态')}
                          value={aiStatus.status === 'available' ? '正常' : '异常'}
                          valueStyle={{
                            color: aiStatus.status === 'available' ? '#52c41a' : '#ff4d4f',
                          }}
                        />
                      </Col>
                    </Row>
                    <Divider />
                    <div>
                      <Text strong>{t('ai.availableTools', '可用工具')}:</Text>
                      <div style={{ marginTop: '12px' }}>
                        {aiStatus.mcp_tools.map((tool) => (
                          <Tag key={tool} color="blue" style={{ marginBottom: '8px' }}>
                            {tool}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <Empty description={t('ai.noStatus', '无法获取服务状态')} />
                )}
              </Card>
            </Col>
          </Row>
        );

      case 'evolution':
        return (
          <Row gutter={24}>
            <Col span={10}>
              <Card
                title={t('evolution.title', '策略进化引擎')}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)' }}
              >
                <Form
                  form={evolutionForm}
                  layout="vertical"
                  initialValues={{
                    population_size: 50,
                    generations: 50,
                    mutation_rate: 0.1,
                    crossover_rate: 0.8,
                    n_iterations: 30,
                    mode: 'maximize',
                  }}
                >
                  <Form.Item
                    label={t('evolution.optimizationType', '优化类型')}
                  >
                    <Select
                      value={evolutionType}
                      onChange={setEvolutionType}
                    >
                      <Option value="genetic">
                        {t('evolution.genetic', '遗传算法')}
                      </Option>
                      <Option value="bayesian">
                        {t('evolution.bayesian', '贝叶斯优化')}
                      </Option>
                    </Select>
                  </Form.Item>

                  {evolutionType === 'genetic' ? (
                    <>
                      <Form.Item
                        name="population_size"
                        label={t('evolution.populationSize', '种群大小')}
                      >
                        <Slider min={10} max={200} />
                      </Form.Item>
                      <Form.Item
                        name="generations"
                        label={t('evolution.generations', '迭代次数')}
                      >
                        <Slider min={10} max={200} />
                      </Form.Item>
                      <Form.Item
                        name="mutation_rate"
                        label={t('evolution.mutationRate', '变异率')}
                      >
                        <Slider min={0.01} max={0.5} step={0.01} />
                      </Form.Item>
                    </>
                  ) : (
                    <>
                      <Form.Item
                        name="n_iterations"
                        label={t('evolution.iterations', '迭代次数')}
                      >
                        <Slider min={10} max={100} />
                      </Form.Item>
                      <Form.Item
                        name="mode"
                        label={t('evolution.mode', '优化模式')}
                      >
                        <Select>
                          <Option value="maximize">{t('evolution.maximize', '最大化')}</Option>
                          <Option value="minimize">{t('evolution.minimize', '最小化')}</Option>
                        </Select>
                      </Form.Item>
                    </>
                  )}

                  <Form.Item>
                    <Space>
                      <Button
                        type="primary"
                        loading={evolutionLoading}
                        onClick={() => {
                          const values = evolutionForm.getFieldsValue();
                          if (evolutionType === 'genetic') {
                            handleGeneticOptimization(values);
                          } else {
                            handleBayesianOptimization(values);
                          }
                        }}
                        icon={<ExperimentOutlined />}
                        style={{ background: 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)', border: 'none' }}
                      >
                        {t('evolution.start', '开始优化')}
                      </Button>
                      <Button
                        onClick={handleQuickTest}
                        loading={evolutionLoading}
                      >
                        {t('evolution.quickTest', '快速测试')}
                      </Button>
                    </Space>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col span={14}>
              <Card
                title={t('evolution.result', '优化结果')}
                extra={taskStatus === 'running' && <SyncOutlined spin />}
                style={{ background: 'var(--bb-bg-secondary)', borderColor: 'var(--bb-border)', height: '100%' }}
              >
                {evolutionLoading && taskStatus !== 'running' ? (
                  <div style={{ textAlign: 'center', padding: '60px 0' }}>
                    <Spin size="large" />
                  </div>
                ) : evolutionResult ? (
                  <div>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Statistic
                          title={t('evolution.bestFitness', '最佳适应度')}
                          value={evolutionResult.best_fitness?.toFixed(4) || evolutionResult.best_value?.toFixed(4)}
                          suffix="/ 1.0"
                          valueStyle={{ color: '#52c41a' }}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title={t('evolution.generations', '迭代次数')}
                          value={evolutionResult.generations || evolutionResult.iterations}
                        />
                      </Col>
                    </Row>
                    <Divider />
                    <div>
                      <Text strong>{t('evolution.bestParams', '最优参数')}:</Text>
                      <div style={{ marginTop: '12px' }}>
                        {evolutionResult.best_params && Object.entries(evolutionResult.best_params).map(([key, value]) => (
                          <Tag key={key} color="purple" style={{ marginBottom: '8px' }}>
                            {key}: {typeof value === 'number' ? value.toFixed(4) : String(value)}
                          </Tag>
                        ))}
                      </div>
                    </div>
                    {evolutionResult.fitness_history && (
                      <>
                        <Divider />
                        <div>
                          <Text strong>{t('evolution.fitnessHistory', '适应度历史')}:</Text>
                          <div style={{ marginTop: '12px', maxHeight: '150px', overflow: 'auto' }}>
                            {evolutionResult.fitness_history.map((fitness: number, index: number) => (
                              <Tag key={index} style={{ marginBottom: '4px' }}>
                                G{index + 1}: {fitness.toFixed(4)}
                              </Tag>
                            ))}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                ) : (
                  <Empty description={t('evolution.noResult', '暂无优化结果')} />
                )}
              </Card>
            </Col>
          </Row>
        );

      default:
        return null;
    }
  };

  const tabItems = [
    { key: 'generate', icon: <RobotOutlined />, label: t('ai.tabGenerate', 'AI 策略生成') },
    { key: 'pick', icon: <StockOutlined />, label: t('ai.tabPick', 'AI 智能选股') },
    { key: 'analyze', icon: <LineChartOutlined />, label: t('ai.tabAnalyze', 'AI 市场分析') },
    { key: 'evolution', icon: <ExperimentOutlined />, label: t('ai.tabEvolution', '策略进化') },
    { key: 'settings', icon: <SettingOutlined />, label: t('ai.tabSettings', '设置') },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={3} style={{ marginBottom: 24, color: 'var(--bb-text)' }}>
        <RobotOutlined style={{ marginRight: 8, color: 'var(--bb-accent-primary)' }} />
        {t('ai.title', 'AI 实验室')}
      </Title>

      {!aiStatus?.glm5_available && !statusLoading && (
        <Alert
          message={t('ai.apiNotConfigured', 'AI API 未配置')}
          description={t('ai.apiNotConfiguredDesc', '请在设置页面配置 GLM API Key 以使用 AI 功能')}
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        style={{ marginTop: 16 }}
      />

      <div style={{ marginTop: 24 }}>
        {renderTabContent()}
      </div>
    </div>
  );
};

export default AILab;
