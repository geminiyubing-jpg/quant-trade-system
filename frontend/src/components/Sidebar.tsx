import React, { useMemo, useState, useEffect, useCallback } from 'react';
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

// 子菜单路径配置 - 统一管理
const SUBMENU_CONFIG: Record<string, string[]> = {
  'market-group': ['/market/realtime', '/market/stocks', '/market/sectors', '/market/futures'],
  'strategy-group': ['/strategy/library', '/strategy/studio'],
  'ai-group': ['/ai/generate', '/ai/pick', '/ai/analyze'],
};

// 根据路径查找所属的子菜单组
const findParentGroup = (pathname: string): string | null => {
  for (const [groupKey, paths] of Object.entries(SUBMENU_CONFIG)) {
    if (paths.some(path => pathname === path || pathname.startsWith(path + '/'))) {
      return groupKey;
    }
  }
  return null;
};

// 获取所有子菜单的路径集合
const getAllSubmenuPaths = (): Set<string> => {
  const paths = new Set<string>();
  Object.values(SUBMENU_CONFIG).forEach(groupPaths => {
    groupPaths.forEach(path => paths.add(path));
  });
  return paths;
};

const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [openKeys, setOpenKeys] = useState<string[]>([]);
  const submenuPaths = useMemo(() => getAllSubmenuPaths(), []);

  // 根据当前路径自动展开对应的子菜单
  useEffect(() => {
    const pathname = location.pathname;
    const parentGroup = findParentGroup(pathname);

    if (parentGroup && !openKeys.includes(parentGroup)) {
      setOpenKeys(prev => [...prev, parentGroup]);
    }
  }, [location.pathname, openKeys]);

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
        key: '/data/management',
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

  // 处理菜单点击 - 优化导航逻辑
  const handleMenuClick = useCallback(({ key }: { key: string }) => {
    // 只有点击实际的路径才导航（排除子菜单组）
    if (key.startsWith('/')) {
      navigate(key);
      // 点击一级菜单时，收起所有展开的子菜单
      setOpenKeys([]);
    }
  }, [navigate]);

  // 处理子菜单展开/收起 - 只保持当前展开的子菜单
  const handleOpenChange = useCallback((keys: string[]) => {
    // 如果有新展开的子菜单，关闭其他子菜单
    if (keys.length > 0) {
      const latestOpenKey = keys[keys.length - 1];
      setOpenKeys([latestOpenKey]);
    } else {
      setOpenKeys([]);
    }
  }, []);

  // 计算当前选中的菜单项
  const selectedKeys = useMemo(() => {
    const pathname = location.pathname;

    // 如果当前路径是子菜单项，直接返回
    if (submenuPaths.has(pathname)) {
      return [pathname];
    }

    // 检查是否匹配某个子菜单路径的前缀
    for (const path of submenuPaths) {
      if (pathname.startsWith(path + '/')) {
        return [path];
      }
    }

    // 返回当前路径
    return [pathname];
  }, [location.pathname, submenuPaths]);

  return (
    <div className="sidebar">
      {/* Navigation Menu */}
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={selectedKeys}
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
