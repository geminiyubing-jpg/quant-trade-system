/**
 * ==============================================
 * 登录页面 - 高端金融科技风格
 * Premium Fintech Login Design
 * ==============================================
 */

import React, { useEffect, useMemo } from 'react';
import { Form, Input, Button, message } from 'antd';
import {
  UserOutlined,
  LockOutlined,
  ThunderboltOutlined,
  StockOutlined,
  LineChartOutlined,
  SafetyCertificateOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  loginAsync,
  clearError,
  selectAuthLoading,
  selectAuthError,
  selectIsAuthenticated,
} from '../store/slices/authSlice';
import type { AppDispatch } from '../store';
import type { RootState } from '../store';
import './Login.css';

interface LoginFormValues {
  username: string;
  password: string;
}

// 生成随机浮动数字
const generateFloatingNumbers = () => {
  const numbers = [];
  for (let i = 0; i < 15; i++) {
    const value = (Math.random() * 200 - 100).toFixed(2);
    const isUp = parseFloat(value) >= 0;
    numbers.push({
      id: i,
      value: isUp ? `+${value}%` : `${value}%`,
      type: isUp ? 'up' : 'down',
      left: `${Math.random() * 100}%`,
      delay: `${Math.random() * 8}s`,
      duration: `${6 + Math.random() * 4}s`,
    });
  }
  return numbers;
};

const Login: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const location = useLocation();
  const loading = useSelector((state: RootState) => selectAuthLoading(state));
  const error = useSelector((state: RootState) => selectAuthError(state));
  const isAuthenticated = useSelector((state: RootState) => selectIsAuthenticated(state));

  // 生成装饰性数据点
  const dataDots = useMemo(() => Array.from({ length: 32 }), []);
  const floatingNumbers = useMemo(() => generateFloatingNumbers(), []);

  // 获取登录前的跳转路径
  const from = (location.state as any)?.from?.pathname || '/';

  useEffect(() => {
    // 如果已经登录，跳转到目标页面
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  useEffect(() => {
    // 显示错误消息
    if (error) {
      message.error(error);
      dispatch(clearError());
    }
  }, [error, dispatch]);

  const onFinish = async (values: LoginFormValues) => {
    try {
      const result = await dispatch(loginAsync(values));

      if (loginAsync.fulfilled.match(result)) {
        message.success('登录成功！');
        navigate(from, { replace: true });
      } else if (loginAsync.rejected.match(result)) {
        message.error('登录失败，请检查用户名和密码');
      }
    } catch {
      message.error('登录失败，请稍后重试');
    }
  };

  return (
    <div className="login-container">
      {/* 动态网格背景 */}
      <div className="login-grid-bg" />

      {/* 左侧品牌展示区 */}
      <div className="login-brand">
        {/* 装饰性金融图表背景 */}
        <div className="login-chart-bg">
          {/* K线图装饰 */}
          <div className="login-chart-decoration" />

          {/* 折线图装饰 SVG */}
          <div className="login-line-chart">
            <svg viewBox="0 0 1000 200" preserveAspectRatio="none">
              <defs>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#FF6B00" stopOpacity="0" />
                  <stop offset="50%" stopColor="#FF6B00" stopOpacity="1" />
                  <stop offset="100%" stopColor="#FFD700" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path
                d="M0,150 Q50,140 100,120 T200,100 T300,130 T400,80 T500,90 T600,60 T700,70 T800,40 T900,50 T1000,30"
                fill="none"
                stroke="url(#lineGradient)"
                strokeWidth="2"
              />
              <path
                d="M0,180 Q100,170 200,160 T400,150 T600,140 T800,130 T1000,120"
                fill="none"
                stroke="#00D26A"
                strokeWidth="1"
                strokeOpacity="0.3"
              />
            </svg>
          </div>

          {/* 数据点装饰 */}
          <div className="login-data-dots">
            {dataDots.map((_, index) => (
              <div
                key={index}
                className="login-data-dot"
                style={{ animationDelay: `${index * 0.1}s` }}
              />
            ))}
          </div>

          {/* 浮动数字 */}
          <div className="login-floating-numbers">
            {floatingNumbers.map((num) => (
              <span
                key={num.id}
                className={`login-float-num ${num.type}`}
                style={{
                  left: num.left,
                  animationDelay: num.delay,
                  animationDuration: num.duration,
                }}
              >
                {num.value}
              </span>
            ))}
          </div>
        </div>

        <div className="login-brand-content">
          {/* Logo */}
          <ThunderboltOutlined className="login-logo" />

          {/* 品牌标题 */}
          <h1 className="login-brand-title">Quant-Trade</h1>
          <p className="login-brand-subtitle">Professional Quantitative Trading System</p>

          {/* 特性列表 */}
          <div className="login-features">
            <div className="login-feature-item">
              <StockOutlined className="login-feature-icon" />
              <span className="login-feature-text">实时行情 · A股全市场覆盖</span>
            </div>
            <div className="login-feature-item">
              <LineChartOutlined className="login-feature-icon" />
              <span className="login-feature-text">策略回测 · 专业级回测引擎</span>
            </div>
            <div className="login-feature-item">
              <SafetyCertificateOutlined className="login-feature-icon" />
              <span className="login-feature-text">风控系统 · 多维度风险管理</span>
            </div>
            <div className="login-feature-item">
              <BulbOutlined className="login-feature-icon" />
              <span className="login-feature-text">AI 辅助 · 智能策略优化</span>
            </div>
          </div>
        </div>
      </div>

      {/* 右侧登录表单区 */}
      <div className="login-form-section">
        <div className="login-card">
          {/* 移动端显示的品牌信息 */}
          <div className="login-mobile-title">
            <ThunderboltOutlined className="login-logo" />
            <h1 className="login-brand-title">Quant-Trade</h1>
            <p className="login-brand-subtitle">专业量化交易系统</p>
          </div>

          {/* 表单标题 */}
          <h2 className="login-form-title">欢迎回来</h2>
          <p className="login-form-subtitle">登录您的账户以继续</p>

          {/* 登录表单 */}
          <Form
            name="login"
            initialValues={{ username: 'test_user', password: 'testpass123' }}
            onFinish={onFinish}
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                autoComplete="username"
                disabled={loading}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                autoComplete="current-password"
                disabled={loading}
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                className="login-submit-btn"
              >
                {loading ? '登录中...' : '登 录'}
              </Button>
            </Form.Item>
          </Form>

          {/* 测试账户提示 */}
          <div className="login-test-hint">
            <div className="login-test-hint-title">
              <BulbOutlined />
              测试账户
            </div>
            <div className="login-test-hint-content">
              <span>
                用户名: <strong>test_user</strong>
              </span>
              <span>
                密码: <strong>testpass123</strong>
              </span>
            </div>
          </div>

          {/* 版本信息 */}
          <div className="login-version">
            Version 1.0.0 © 2026 QuantDev Team
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
