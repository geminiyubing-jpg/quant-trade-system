/**
 * TradingModeSwitcher - 交易模式切换器
 *
 * 显示当前交易模式，支持切换 PAPER/LIVE 模式
 * 切换到 LIVE 模式时显示警告对话框
 */

import React, { useState } from 'react';
import { Space, Typography, Button, Modal, Tag, Tooltip } from 'antd';
import { ExperimentOutlined, ThunderboltOutlined, SwapOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useTradingMode } from '../contexts/TradingModeContext';
import './TopBar.css';

const { Text } = Typography;

const TradingModeSwitcher: React.FC = () => {
  const { t } = useTranslation();
  const { setMode, isPaperTrading } = useTradingMode();
  const [warningVisible, setWarningVisible] = useState(false);

  // 处理模式切换请求
  const handleSwitchRequest = () => {
    // 如果当前是 PAPER，切换到 LIVE 时需要确认
    if (isPaperTrading) {
      setWarningVisible(true);
    } else {
      // 从 LIVE 切换到 PAPER 不需要确认
      setMode('PAPER');
    }
  };

  // 确认切换到 LIVE
  const handleConfirmSwitch = () => {
    setMode('LIVE');
    setWarningVisible(false);
  };

  // 取消切换
  const handleCancelSwitch = () => {
    setWarningVisible(false);
  };

  // 获取当前模式的显示配置
  const getModeConfig = () => {
    if (isPaperTrading) {
      return {
        icon: <ExperimentOutlined />,
        label: t('tradingMode.paper'),
        description: t('tradingMode.paperDescription'),
        color: '#52c41a', // 绿色
        tagColor: 'success',
      };
    } else {
      return {
        icon: <ThunderboltOutlined />,
        label: t('tradingMode.live'),
        description: t('tradingMode.liveDescription'),
        color: '#ff4d4f', // 红色
        tagColor: 'error',
      };
    }
  };

  const config = getModeConfig();

  return (
    <>
      <Space size="small">
        {/* 当前模式显示 */}
        <Tooltip title={config.description}>
          <Tag
            icon={config.icon}
            className="trading-mode-tag"
            onClick={handleSwitchRequest}
          >
            <span style={{ color: config.color, fontWeight: 500, fontSize: 13 }}>
              {config.label}
            </span>
          </Tag>
        </Tooltip>

        {/* 切换按钮 */}
        <Tooltip title={isPaperTrading ? t('tradingMode.switchToLive') : t('tradingMode.switchToPaper')}>
          <Button
            type="text"
            icon={<SwapOutlined />}
            className="trading-mode-switch-btn"
            onClick={handleSwitchRequest}
          >
            <span style={{ color: config.color, fontSize: 13 }}>
              {isPaperTrading ? t('tradingMode.live') : t('tradingMode.paper')}
            </span>
          </Button>
        </Tooltip>
      </Space>

      {/* LIVE 模式切换警告对话框 */}
      <Modal
        title={
          <Space>
            <ThunderboltOutlined style={{ color: '#ff4d4f' }} />
            <Text strong style={{ color: '#ff4d4f' }}>
              {t('tradingMode.warning')}
            </Text>
          </Space>
        }
        open={warningVisible}
        onOk={handleConfirmSwitch}
        onCancel={handleCancelSwitch}
        okText={t('tradingMode.confirmSwitch')}
        cancelText={t('tradingMode.cancel')}
        okButtonProps={{ danger: true }}
        centered
      >
        <div style={{ marginTop: 16 }}>
          <Text strong style={{ fontSize: 16 }}>
            {t('tradingMode.liveWarningTitle')}
          </Text>
          <pre
            style={{
              marginTop: 16,
              padding: 16,
              background: '#fff2f0',
              border: '1px solid #ffccc7',
              borderRadius: 4,
              fontSize: 13,
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
              color: '#262626',
            }}
          >
            {t('tradingMode.liveWarningMessage')}
          </pre>
        </div>
      </Modal>
    </>
  );
};

export default TradingModeSwitcher;
