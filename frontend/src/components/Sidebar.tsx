import React, { useMemo, useState, useEffect } from 'react';
import { Menu } from 'antd';
import {
  DashboardOutlined,
  LineChartOutlined,
  FundOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  PieChartOutlined,
  RobotOutlined,
  SafetyOutlined,
  DatabaseOutlined,
  TeamOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Sidebar.css';

type SidebarProps = {
  collapsed: boolean;
};

const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [openKeys, setOpenKeys] = useState<string[]>([]);

  // 根据当前路径自动展开对应的子菜单
  useEffect(() => {
    const pathname = location.pathname;

    // 定义子菜单组和它们的路径前缀
    const submenuGroups: { [key: string]: string[] } = {
      'market-group': ['/market'],
      'strategy-group': ['/strategy/library', '/strategy/studio'],
      'ai-group': ['/ai/generate', '/ai/pick', '/ai/analyze'],
    };

    // 检查当前路径属于哪个子菜单组
    const shouldOpen: string[] = [];
    Object.entries(submenuGroups).forEach(([groupKey, paths]) => {
      if (paths.some(path => pathname.startsWith(path))) {
        shouldOpen.push(groupKey);
      }
    });

    setOpenKeys(shouldOpen);
  }, [location.pathname]);

  // 使用 i18n 的菜单配置
  const menuItems = useMemo(
    () => [
      {
        key: '/',
        icon: <DashboardOutlined />,
        label: t('nav.dashboard'),
      },
      {
        type: 'divider' as const,
      },
      {
        key: 'market-group',
        icon: <LineChartOutlined />,
        label: t('nav.market'),
        children: [
          {
            key: '/market/realtime',
            label: t('market.realtime'),
          },
          {
            key: '/market/stocks',
            label: t('market.stocks'),
          },
          {
            key: '/market/sectors',
            label: t('market.sectors'),
          },
          {
            key: '/market/futures',
            label: t('market.futures'),
          },
        ],
      },
      {
        key: 'strategy-group',
        icon: <FundOutlined />,
        label: t('nav.strategy'),
        children: [
          {
            key: '/strategy/library',
            label: t('nav.strategyLibrary'),
          },
          {
            key: '/strategy/studio',
            label: t('nav.strategyStudio'),
          },
        ],
      },
      {
        key: '/backtest',
        icon: <ExperimentOutlined />,
        label: t('nav.backtest'),
      },
      {
        key: '/trading',
        icon: <ThunderboltOutlined />,
        label: t('nav.trading'),
      },
      {
        key: '/portfolio',
        icon: <PieChartOutlined />,
        label: t('nav.portfolio'),
      },
      {
        type: 'divider' as const,
      },
      {
        key: 'ai-group',
        icon: <RobotOutlined />,
        label: t('nav.ai'),
        children: [
          {
            key: '/ai/generate',
            label: t('nav.aiGenerate'),
          },
          {
            key: '/ai/pick',
            label: t('nav.aiPick'),
          },
          {
            key: '/ai/analyze',
            label: t('nav.aiAnalyze'),
          },
        ],
      },
      {
        key: '/risk',
        icon: <SafetyOutlined />,
        label: t('nav.risk'),
      },
      {
        type: 'divider' as const,
      },
      {
        key: '/data',
        icon: <DatabaseOutlined />,
        label: t('nav.data'),
      },
      {
        key: '/community',
        icon: <TeamOutlined />,
        label: t('nav.community'),
      },
      {
        key: '/docs',
        icon: <FileTextOutlined />,
        label: t('nav.docs'),
      },
    ],
    [t, i18n.language]
  );

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  // 处理子菜单展开/收起
  const handleOpenChange = (keys: string[]) => {
    setOpenKeys(keys);
  };

  return (
    <div className="sidebar">
      {/* Navigation Menu */}
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        openKeys={openKeys}
        onOpenChange={handleOpenChange}
        items={menuItems}
        onClick={handleMenuClick}
        key={i18n.language}
        inlineCollapsed={collapsed}
        className="sidebar-menu"
      />
    </div>
  );
};

export default Sidebar;
