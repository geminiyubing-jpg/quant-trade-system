/**
 * ==============================================
 * 快速登录组件
 * ==============================================
 */

import React, { useState } from 'react';
import { Button, Card, Space, message, Typography } from 'antd';
import { ThunderboltOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const QuickLogin: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleQuickLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'test_user',
          password: 'testpass123'
        })
      });

      const data = await response.json();

      if (data.access_token) {
        // 保存 Token
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('auth', JSON.stringify({
          accessToken: data.access_token,
          user: { id: data.user_id || 1 }
        }));

        message.success('✅ 登录成功！正在刷新...');
        setTimeout(() => location.reload(), 1000);
      } else {
        message.error('登录失败：' + JSON.stringify(data));
      }
    } catch (error: any) {
      message.error('登录错误：' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card style={{ maxWidth: 400, margin: '100px auto', textAlign: 'center' }}>
      <Space direction="vertical" size="large">
        <Title level={4}>
          <ThunderboltOutlined /> 需要登录才能使用实时行情
        </Title>
        <Text type="secondary">
          点击下方按钮快速登录测试账号
        </Text>
        <Button
          type="primary"
          size="large"
          icon={<ThunderboltOutlined />}
          loading={loading}
          onClick={handleQuickLogin}
        >
          快速登录
        </Button>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          测试账号: test_user / testpass123
        </Text>
      </Space>
    </Card>
  );
};

export default QuickLogin;
