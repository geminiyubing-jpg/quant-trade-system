/**
 * ==============================================
 * 主题切换按钮组件
 * ==============================================
 */

import React from 'react';
import { Button, Tooltip, Dropdown, Space } from 'antd';
import { SunOutlined, MoonOutlined, SyncOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts/ThemeContext';

interface ThemeSwitchProps {
  // 显示模式：icon 只显示图标，text 显示文字，full 显示全部
  mode?: 'icon' | 'text' | 'full';
  // 是否显示下拉菜单（包含自动模式选项）
  showMenu?: boolean;
  // 尺寸
  size?: 'small' | 'middle' | 'large';
}

const ThemeSwitch: React.FC<ThemeSwitchProps> = ({
  mode = 'icon',
  showMenu = false,
  size = 'middle',
}) => {
  const { t } = useTranslation();
  const { theme, toggleTheme, setTheme, setAutoMode, isAutoMode } = useTheme();

  const isDark = theme === 'dark';

  const buttonStyle: React.CSSProperties = {
    background: isDark ? 'rgba(0, 212, 255, 0.1)' : 'rgba(0, 102, 204, 0.1)',
    border: `1px solid ${isDark ? 'rgba(0, 212, 255, 0.3)' : 'rgba(0, 102, 204, 0.3)'}`,
    color: isDark ? '#00d4ff' : '#0066cc',
    borderRadius: '6px',
    transition: 'all 0.3s ease',
  };

  const renderIcon = () => {
    if (isDark) {
      return <MoonOutlined style={{ fontSize: size === 'small' ? '14px' : '16px' }} />;
    }
    return <SunOutlined style={{ fontSize: size === 'small' ? '14px' : '16px', color: '#d4a536' }} />;
  };

  const renderText = () => {
    if (mode === 'icon') return null;
    return (
      <span style={{ marginLeft: mode === 'full' ? 8 : 0 }}>
        {isDark ? t('theme.dark') : t('theme.light')}
      </span>
    );
  };

  // 简单按钮（无下拉菜单）
  if (!showMenu) {
    return (
      <Tooltip title={isDark ? t('theme.switchToLight') : t('theme.switchToDark')}>
        <Button
          size={size}
          icon={mode !== 'text' ? renderIcon() : undefined}
          onClick={toggleTheme}
          style={buttonStyle}
        >
          {renderText()}
        </Button>
      </Tooltip>
    );
  }

  // 带下拉菜单的按钮
  const menuItems = [
    {
      key: 'light',
      label: (
        <Space>
          <SunOutlined style={{ color: '#d4a536' }} />
          {t('theme.light')}
        </Space>
      ),
      onClick: () => setTheme('light'),
    },
    {
      key: 'dark',
      label: (
        <Space>
          <MoonOutlined style={{ color: '#00d4ff' }} />
          {t('theme.dark')}
        </Space>
      ),
      onClick: () => setTheme('dark'),
    },
    { type: 'divider' as const },
    {
      key: 'auto',
      label: (
        <Space>
          <SyncOutlined style={{ color: '#52c41a' }} />
          {t('theme.auto')}
          {isAutoMode && <span style={{ color: '#52c41a', fontSize: '12px' }}>({t('theme.active')})</span>}
        </Space>
      ),
      onClick: setAutoMode,
    },
  ];

  return (
    <Dropdown
      menu={{ items: menuItems, selectedKeys: [isAutoMode ? 'auto' : theme] }}
      trigger={['click']}
    >
      <Button
        size={size}
        icon={mode !== 'text' ? renderIcon() : undefined}
        style={{ ...buttonStyle, cursor: 'pointer' }}
      >
        {renderText()}
        {isAutoMode && mode === 'full' && (
          <span style={{ marginLeft: 4, fontSize: '10px', color: '#52c41a' }}>
            ({t('theme.autoMode')})
          </span>
        )}
      </Button>
    </Dropdown>
  );
};

export default ThemeSwitch;
