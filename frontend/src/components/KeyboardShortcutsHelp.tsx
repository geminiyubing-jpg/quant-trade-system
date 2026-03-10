/**
 * 快捷键帮助面板组件
 * 显示可用的快捷键列表和帮助信息
 */

import React, { useMemo, useState } from 'react';
import { Modal, Typography, Tag, Table, Input, Tabs } from 'antd';
import {
  SearchOutlined,
  MacCommandOutlined,
  StarOutlined,
  ThunderboltOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  EnterOutlined,
  CloseOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts/ThemeContext';
import './KeyboardShortcutsHelp.css';

const { Text, Paragraph } = Typography;
const { Search } = Input;

interface ShortcutItem {
  keys: string;
  description: string;
  category: 'navigation' | 'action' | 'global';
  icon: React.ReactNode;
}



interface ShortcutItem {
  keys: string;
  description: string;
  category: 'navigation' | 'action' | 'global';
  icon: React.ReactNode;
}

interface KeyboardShortcutsHelpProps {
  visible: boolean;
  onClose: () => void;
}

const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({
  visible,
  onClose,
}) => {
  const { t } = useTranslation();
  const { theme } = useTheme();
  const [searchText, setSearchText] = useState('');

  const isDark = theme === 'dark';

  const shortcuts: ShortcutItem[] = useMemo(() => [
    {
      keys: 'Ctrl + K',
      description: t('shortcuts.search', '搜索股票'),
      category: 'navigation',
      icon: <SearchOutlined />,
    },
    {
      keys: 'Ctrl + E',
      description: t('shortcuts.export', '导出数据'),
      category: 'action',
      icon: <MacCommandOutlined />,
    },
    {
      keys: 'Ctrl + D',
      description: t('shortcuts.toggleWatchlist', '切换自选'),
      category: 'action',
      icon: <StarOutlined />,
    },
    {
      keys: '↑',
      description: t('shortcuts.navigateUp', '向上导航'),
      category: 'navigation',
      icon: <ArrowUpOutlined />,
    },
    {
      keys: '↓',
      description: t('shortcuts.navigateDown', '向下导航'),
      category: 'navigation',
      icon: <ArrowDownOutlined />,
    },
    {
      keys: 'Enter',
      description: t('shortcuts.openDetail', '打开详情'),
      category: 'navigation',
      icon: <EnterOutlined />,
    },
    {
      keys: 'Escape',
      description: t('shortcuts.close', '关闭弹窗'),
      category: 'global',
      icon: <CloseOutlined />,
    },
    {
      keys: '?',
      description: t('shortcuts.help', '显示帮助'),
      category: 'global',
      icon: <QuestionCircleOutlined />,
    },
  ], [t]);

  // 过滤快捷键
  const filteredShortcuts = useMemo(() => {
    if (!searchText) return shortcuts;
    const lowerSearch = searchText.toLowerCase();
    return shortcuts.filter(
      (s) =>
        s.keys.toLowerCase().includes(lowerSearch) ||
        s.description.toLowerCase().includes(lowerSearch)
    );
  }, [shortcuts, searchText]);

  // 按分类分组
  const groupedShortcuts = useMemo(() => ({
    navigation: filteredShortcuts.filter((s) => s.category === 'navigation'),
    action: filteredShortcuts.filter((s) => s.category === 'action'),
    global: filteredShortcuts.filter((s) => s.category === 'global'),
  }), [filteredShortcuts]);

  const categoryLabels = {
    navigation: t('shortcuts.category.navigation', '导航'),
    action: t('shortcuts.category.action', '操作'),
    global: t('shortcuts.category.global', '全局'),
  };

  const columns = [
    {
      title: t('shortcuts.column.key', '快捷键'),
      dataIndex: 'keys',
      key: 'keys',
      width: 140,
      render: (keys: string) => (
        <Tag
          color={isDark ? 'gold' : 'blue'}
          style={{
            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
            fontWeight: 'bold',
            fontSize: 13,
          }}
        >
          {keys}
        </Tag>
      ),
    },
    {
      title: t('shortcuts.column.description', '描述'),
      dataIndex: 'description',
      key: 'description',
      render: (description: string) => (
        <Text style={{ color: isDark ? '#e0e0e0' : '#333' }}>{description}</Text>
      ),
    },
    {
      title: t('shortcuts.column.icon', '类型'),
      dataIndex: 'icon',
      key: 'icon',
      width: 60,
      render: (icon: React.ReactNode) => (
        <span style={{ fontSize: 16, color: isDark ? '#ffab00' : '#1890ff' }}>
          {icon}
        </span>
      ),
    },
  ];

  const renderShortcutTable = (data: ShortcutItem[]) => (
    <Table
      dataSource={data}
      columns={columns}
      pagination={false}
      size="small"
      rowKey="keys"
      className="shortcuts-table"
      showHeader={false}
    />
  );

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
      centered
      className="keyboard-shortcuts-help"
      styles={{
        content: {
          background: isDark ? '#1a1a1a' : '#fff',
          borderRadius: 12,
        },
        header: {
          background: isDark ? '#1a1a1a' : '#fff',
          borderBottom: `1px solid ${isDark ? '#333' : '#e8e8e8'}`,
        },
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ThunderboltOutlined style={{ fontSize: 20, color: isDark ? '#ffab00' : '#1890ff' }} />
          <span style={{ fontSize: 16, fontWeight: 600 }}>
            {t('shortcuts.title', '快捷键帮助')}
          </span>
          <Tag color={isDark ? 'gold' : 'blue'} style={{ marginLeft: 8 }}>
            {t('shortcuts.subtitle', 'Keyboard Shortcuts')}
          </Tag>
        </div>
      }
    >
      {/* 搜索框 */}
      <Search
        placeholder={t('shortcuts.searchPlaceholder', '搜索快捷键...')}
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        style={{ marginBottom: 16 }}
        allowClear
      />

      {/* 按分类展示 */}
      <Tabs
        defaultActiveKey="all"
        items={[
          {
            key: 'all',
            label: t('shortcuts.tab.all', '全部'),
            children: renderShortcutTable(filteredShortcuts),
          },
          {
            key: 'navigation',
            label: `${categoryLabels.navigation} (${groupedShortcuts.navigation.length})`,
            children: renderShortcutTable(groupedShortcuts.navigation),
          },
          {
            key: 'action',
            label: `${categoryLabels.action} (${groupedShortcuts.action.length})`,
            children: renderShortcutTable(groupedShortcuts.action),
          },
          {
            key: 'global',
            label: `${categoryLabels.global} (${groupedShortcuts.global.length})`,
            children: renderShortcutTable(groupedShortcuts.global),
          },
        ]}
      />

      {/* 提示信息 */}
      <div className="shortcut-footer" style={{ marginTop: 16, textAlign: 'center' }}>
        <Paragraph style={{ color: isDark ? '#888' : '#666', fontSize: 12, marginBottom: 8 }}>
          {t('shortcuts.footer', '按 ? 键可随时打开此帮助面板')}
        </Paragraph>
        <Tag
          color={isDark ? 'gold' : 'blue'}
          style={{ cursor: 'pointer' }}
          onClick={onClose}
        >
          {t('shortcuts.close', '关闭')} (Esc)
        </Tag>
      </div>
    </Modal>
  );
};

export default KeyboardShortcutsHelp;
