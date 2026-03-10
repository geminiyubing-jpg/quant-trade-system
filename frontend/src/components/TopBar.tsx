import React from 'react';
import { Input, Badge, Dropdown, Avatar, Space, Typography, Modal } from 'antd';
import {
  SearchOutlined,
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  RiseOutlined,
  DotChartOutlined,
  MenuOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { logoutAsync } from '../store/slices/authSlice';
import LanguageSwitcher from './LanguageSwitcher';
import TradingModeSwitcher from './TradingModeSwitcher';
import ThemeSwitch from './ThemeSwitch';
import type { MenuProps } from 'antd';
import type { AppDispatch } from '../store';
import './TopBar.css';

const { Text } = Typography;

interface TopBarProps {
  isMobile?: boolean;
  onMenuClick?: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ isMobile = false, onMenuClick }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();

  const handleLogout = () => {
    Modal.confirm({
      title: t('common.logout'),
      content: '确定要退出登录吗？',
      okText: t('common.confirm'),
      cancelText: t('common.cancel'),
      onOk: async () => {
        try {
          await dispatch(logoutAsync()).unwrap();
          navigate('/login');
        } catch (error) {
          console.error('登出失败:', error);
        }
      },
    });
  };

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: t('nav.settings'),
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: t('common.logout'),
      onClick: handleLogout,
    },
  ];

  return (
    <div className="top-bar">
      {/* 左侧：系统 Logo */}
      <div className="top-bar-left">
        {/* 移动端汉堡菜单 */}
        {isMobile && (
          <div className="mobile-menu-btn" onClick={onMenuClick}>
            <MenuOutlined />
          </div>
        )}

        <div className="system-logo" onClick={() => navigate('/')}>
          {/* Logo 图标容器 */}
          <div className="logo-icon-wrapper">
            {/* 外圈 */}
            <div className="logo-icon-ring"></div>
            {/* 内圈 */}
            <div className="logo-icon-inner">
              <RiseOutlined className="logo-icon-symbol" />
            </div>
            {/* 装饰点 */}
            <div className="logo-icon-dot top-right"></div>
            <div className="logo-icon-dot bottom-left"></div>
          </div>

          {/* Logo 文字 - 移动端隐藏 */}
          {!isMobile && (
            <div className="logo-text">
              <div className="logo-title">
                <span className="logo-main">Quant</span>
                <span className="logo-divider">|</span>
                <span className="logo-accent">Trade</span>
              </div>
              <div className="logo-subtitle">
                <DotChartOutlined style={{ fontSize: '9px', marginRight: '6px' }} />
                <Text style={{ fontSize: '9px', color: 'var(--bb-text-muted)', letterSpacing: '1px' }}>
                  {t('app.subtitle')}
                </Text>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 中央：搜索框 - 移动端隐藏 */}
      {!isMobile && (
        <div className="top-bar-center">
          <Input.Search
            placeholder={t('common.search')}
            prefix={<SearchOutlined />}
            style={{ width: 300 }}
            className="top-bar-search"
          />
        </div>
      )}

      {/* 右侧：功能按钮 */}
      <div className="top-bar-right">
        <Space size={isMobile ? 'small' : 'large'}>
          {/* 交易模式切换器 - 移动端隐藏 */}
          {!isMobile && <TradingModeSwitcher />}

          {/* 主题切换器 */}
          <ThemeSwitch showMenu size="small" />

          {/* 语言切换器 - 移动端隐藏 */}
          {!isMobile && <LanguageSwitcher />}

          {/* 通知图标 */}
          <Badge count={5} size="small" offset={[-5, 5]}>
            <BellOutlined className="top-bar-icon" />
          </Badge>

          {/* 用户下拉菜单 */}
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Avatar icon={<UserOutlined />} className="top-bar-avatar" />
          </Dropdown>
        </Space>
      </div>
    </div>
  );
};

export default TopBar;
