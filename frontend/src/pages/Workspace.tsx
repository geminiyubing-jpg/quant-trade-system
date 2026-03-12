/**
 * 工作区主页面
 * Workspace Page - OpenBB Style Custom Workspace
 *
 * 功能:
 * - 可拖拽面板布局
 * - 工作区持久化 (localStorage)
 * - 键盘快捷键
 * - AI 助手抽屉
 */
import React, { useEffect, useCallback } from 'react';
import { Button, Tooltip, Dropdown, Modal, Input, message, Popconfirm } from 'antd';
import { useTranslation } from 'react-i18next';
import {
  PlusOutlined,
  SaveOutlined,
  FolderOpenOutlined,
  AppstoreOutlined,
  RobotOutlined,
  DeleteOutlined,
  CopyOutlined,
  CloudSyncOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import WorkspaceCanvas from '../components/workspace/WorkspaceCanvas';
import AIDrawer from '../components/workspace/AIDrawer';
import { PanelConfig } from '../types/workspace';
import { useWorkspacePersistence } from '../hooks/useWorkspacePersistence';
import { useShortcut } from '../hooks/useKeyboardShortcuts';
import '../styles/workspace.css';

// 生成唯一 ID
const generateId = () => `panel-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

const Workspace: React.FC = () => {
  const { t } = useTranslation();

  // 使用持久化 Hook
  const {
    currentWorkspace,
    setCurrentWorkspace,
    savedWorkspaces,
    templates,
    saveWorkspace,
    deleteWorkspace,
    loadWorkspace,
    createNewWorkspace,
    duplicateWorkspace,
    updatePanels,
  } = useWorkspacePersistence();

  const [aiDrawerOpen, setAIDrawerOpen] = React.useState(false);
  const [saveModalVisible, setSaveModalVisible] = React.useState(false);
  const [newWorkspaceModalVisible, setNewWorkspaceModalVisible] = React.useState(false);
  const [workspaceName, setWorkspaceName] = React.useState('');

  // ==============================================
  // 键盘快捷键
  // ==============================================

  // Ctrl+S 保存工作区
  useShortcut('s', useCallback(() => {
    if (currentWorkspace) {
      setWorkspaceName(currentWorkspace.name || '');
      setSaveModalVisible(true);
    }
  }, [currentWorkspace]), { ctrl: true });

  // Ctrl+N 新建工作区
  useShortcut('n', useCallback(() => {
    setWorkspaceName('');
    setNewWorkspaceModalVisible(true);
  }, []), { ctrl: true });

  // Escape 关闭 AI 抽屉
  useShortcut('Escape', useCallback(() => {
    if (aiDrawerOpen) {
      setAIDrawerOpen(false);
    }
  }, [aiDrawerOpen]));

  // Ctrl+Shift+P 添加面板
  useShortcut('p', useCallback(() => {
    if (currentWorkspace) {
      message.info(t('workspace.selectPanelType'));
    }
  }, [currentWorkspace, t]), { ctrl: true, shift: true });

  // ==============================================
  // 工作区操作
  // ==============================================

  // 保存工作区
  const handleSaveWorkspace = useCallback(() => {
    if (!currentWorkspace) return;

    if (workspaceName.trim()) {
      const updatedWorkspace = {
        ...currentWorkspace,
        name: workspaceName.trim(),
      };
      saveWorkspace(updatedWorkspace);
      message.success(t('workspace.saved'));
    } else {
      message.warning(t('workspace.inputWorkspaceName'));
      return;
    }
    setSaveModalVisible(false);
  }, [currentWorkspace, workspaceName, saveWorkspace, t]);

  // 创建新工作区
  const handleCreateNewWorkspace = useCallback(() => {
    if (!workspaceName.trim()) {
      message.warning(t('workspace.inputWorkspaceName'));
      return;
    }

    const newWorkspace = createNewWorkspace(workspaceName.trim());
    saveWorkspace(newWorkspace);
    message.success(t('workspace.created'));
    setNewWorkspaceModalVisible(false);
    setWorkspaceName('');
  }, [workspaceName, createNewWorkspace, saveWorkspace, t]);

  // 从模板创建工作区
  const handleCreateFromTemplate = useCallback((templateId: string) => {
    const workspace = loadWorkspace(templateId);
    if (workspace) {
      saveWorkspace(workspace);
      message.success(`${t('workspace.templateLoaded')}: ${workspace.name}`);
    }
  }, [loadWorkspace, saveWorkspace, t]);

  // 加载已保存的工作区
  const handleLoadWorkspace = useCallback((workspaceId: string) => {
    const workspace = loadWorkspace(workspaceId);
    if (workspace) {
      setCurrentWorkspace(workspace);
      message.success(`${t('workspace.loaded')}: ${workspace.name}`);
    }
  }, [loadWorkspace, setCurrentWorkspace, t]);

  // 删除工作区
  const handleDeleteWorkspace = useCallback((workspaceId: string) => {
    deleteWorkspace(workspaceId);
    message.success(t('workspace.deleted'));
  }, [deleteWorkspace, t]);

  // 复制工作区
  const handleDuplicateWorkspace = useCallback((workspaceId: string) => {
    const duplicated = duplicateWorkspace(workspaceId);
    if (duplicated) {
      message.success(`${t('workspace.duplicated')}: ${duplicated.name}`);
    }
  }, [duplicateWorkspace, t]);

  // ==============================================
  // 面板操作
  // ==============================================

  // 添加面板
  const handleAddPanel = useCallback((type: PanelConfig['type']) => {
    if (!currentWorkspace) {
      // 如果没有工作区，先创建一个默认的
      const newWorkspace = createNewWorkspace(t('workspace.unnamedWorkspace'));
      const newPanel: PanelConfig = {
        id: generateId(),
        type,
        title: getPanelTitle(type, t),
        layout: { x: 0, y: 0, w: 4, h: 6, minW: 2, minH: 3 },
      };
      saveWorkspace({ ...newWorkspace, panels: [newPanel] });
      return;
    }

    const newPanel: PanelConfig = {
      id: generateId(),
      type,
      title: getPanelTitle(type, t),
      layout: { x: 0, y: 0, w: 4, h: 6, minW: 2, minH: 3 },
    };

    updatePanels([...currentWorkspace.panels, newPanel]);
  }, [currentWorkspace, createNewWorkspace, saveWorkspace, updatePanels, t]);

  // 更新面板布局
  const handleLayoutChange = useCallback((panels: PanelConfig[]) => {
    updatePanels(panels);
  }, [updatePanels]);

  // 删除面板
  const handleRemovePanel = useCallback((panelId: string) => {
    if (!currentWorkspace) return;
    updatePanels(currentWorkspace.panels.filter(p => p.id !== panelId));
  }, [currentWorkspace, updatePanels]);

  // ==============================================
  // 菜单配置
  // ==============================================

  // 模板菜单
  const templateMenuItems: MenuProps['items'] = [
    ...templates.map(template => ({
      key: template.id,
      label: (
        <div className="template-menu-item">
          <div className="template-name">{template.name}</div>
          <div className="template-desc">{template.description}</div>
        </div>
      ),
      onClick: () => handleCreateFromTemplate(template.id),
    })),
    { type: 'divider' as const },
    {
      key: 'new-blank',
      label: (
        <div className="template-menu-item">
          <div className="template-name">{t('workspace.blankWorkspace')}</div>
          <div className="template-desc">{t('workspace.blankWorkspaceDesc')}</div>
        </div>
      ),
      onClick: () => {
        setWorkspaceName('');
        setNewWorkspaceModalVisible(true);
      },
    },
  ];

  // 已保存工作区菜单
  const savedWorkspaceMenuItems: MenuProps['items'] = savedWorkspaces.length > 0
    ? savedWorkspaces.map(workspace => ({
        key: workspace.id,
        label: (
          <div className="saved-workspace-item">
            <div className="workspace-item-info">
              <span className="workspace-item-name">{workspace.name}</span>
              <span className="workspace-item-panels">{workspace.panels.length} {t('workspace.panels')}</span>
            </div>
            <div className="workspace-item-actions">
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleDuplicateWorkspace(workspace.id);
                }}
              />
              <Popconfirm
                title={t('workspace.deleteConfirm')}
                onConfirm={() => handleDeleteWorkspace(workspace.id)}
                okText={t('common.delete')}
                cancelText={t('common.cancel')}
              >
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={(e) => e.stopPropagation()}
                />
              </Popconfirm>
            </div>
          </div>
        ),
        onClick: () => handleLoadWorkspace(workspace.id),
      }))
    : [{ key: 'empty', label: <span style={{ color: '#8B949E' }}>{t('workspace.noSavedWorkspaces')}</span>, disabled: true }];

  // 添加面板菜单
  const addPanelMenuItems: MenuProps['items'] = [
    { key: 'chart', label: t('workspace.panelTypes.chart'), icon: <AppstoreOutlined />, onClick: () => handleAddPanel('chart') },
    { key: 'table', label: t('workspace.panelTypes.table'), icon: <AppstoreOutlined />, onClick: () => handleAddPanel('table') },
    { key: 'watchlist', label: t('workspace.panelTypes.watchlist'), icon: <AppstoreOutlined />, onClick: () => handleAddPanel('watchlist') },
    { key: 'news', label: t('workspace.panelTypes.news'), icon: <AppstoreOutlined />, onClick: () => handleAddPanel('news') },
    { key: 'capitalFlow', label: t('workspace.panelTypes.capitalFlow'), icon: <AppstoreOutlined />, onClick: () => handleAddPanel('capitalFlow') },
    { key: 'heatmap', label: t('workspace.panelTypes.heatmap'), icon: <AppstoreOutlined />, onClick: () => handleAddPanel('heatmap') },
  ];

  // 自动保存
  useEffect(() => {
    if (currentWorkspace && currentWorkspace.panels.length > 0) {
      // 每次面板变化时自动保存
      const timer = setTimeout(() => {
        saveWorkspace(currentWorkspace);
      }, 1000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [currentWorkspace, saveWorkspace]);

  return (
    <div className="workspace-page">
      {/* 工作区工具栏 */}
      <div className="workspace-toolbar">
        <div className="toolbar-left">
          <Dropdown menu={{ items: templateMenuItems }} placement="bottomLeft">
            <Button icon={<FolderOpenOutlined />}>
              {t('workspace.newWorkspace')}
            </Button>
          </Dropdown>

          <Dropdown menu={{ items: savedWorkspaceMenuItems }} placement="bottomLeft">
            <Button icon={<FolderOpenOutlined />}>
              {t('workspace.openWorkspace')}
            </Button>
          </Dropdown>

          <Dropdown menu={{ items: addPanelMenuItems }} placement="bottomLeft" disabled={!currentWorkspace}>
            <Button icon={<PlusOutlined />} disabled={!currentWorkspace}>
              {t('workspace.addPanel')}
            </Button>
          </Dropdown>

          <Button
            icon={<SaveOutlined />}
            disabled={!currentWorkspace}
            onClick={() => {
              setWorkspaceName(currentWorkspace?.name || '');
              setSaveModalVisible(true);
            }}
          >
            {t('workspace.save')}
          </Button>
        </div>

        <div className="toolbar-center">
          <span className="workspace-title">
            {currentWorkspace?.name || t('workspace.unnamedWorkspace')}
          </span>
          {currentWorkspace && (
            <span className="workspace-info">
              {currentWorkspace.panels.length} {t('workspace.panels')}
              <Tooltip title={t('workspace.autoSaveEnabled')}>
                <CloudSyncOutlined style={{ marginLeft: 8, color: '#52C41A' }} />
              </Tooltip>
            </span>
          )}
        </div>

        <div className="toolbar-right">
          <Tooltip title={`${t('workspace.aiAssistant')} (Ctrl+Shift+A)`}>
            <Button
              type={aiDrawerOpen ? 'primary' : 'default'}
              icon={<RobotOutlined />}
              onClick={() => setAIDrawerOpen(!aiDrawerOpen)}
            >
              {t('workspace.aiAssistant')}
            </Button>
          </Tooltip>
        </div>
      </div>

      {/* 工作区主体 */}
      <div className="workspace-body">
        {currentWorkspace ? (
          <WorkspaceCanvas
            panels={currentWorkspace.panels}
            onLayoutChange={handleLayoutChange}
            onRemovePanel={handleRemovePanel}
          />
        ) : (
          <div className="workspace-empty">
            <div className="empty-content">
              <AppstoreOutlined className="empty-icon" />
              <h2>{t('workspace.emptyTitle')}</h2>
              <p>{t('workspace.emptyDesc')}</p>
              <div className="template-cards">
                {templates.map(template => (
                  <div
                    key={template.id}
                    className="template-card"
                    onClick={() => handleCreateFromTemplate(template.id)}
                  >
                    <div className="template-card-title">{template.name}</div>
                    <div className="template-card-desc">{template.description}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* AI 助手抽屉 */}
      <AIDrawer
        open={aiDrawerOpen}
        onClose={() => setAIDrawerOpen(false)}
      />

      {/* 保存工作区弹窗 */}
      <Modal
        title={t('workspace.saveWorkspaceTitle')}
        open={saveModalVisible}
        onOk={handleSaveWorkspace}
        onCancel={() => setSaveModalVisible(false)}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
      >
        <Input
          placeholder={t('workspace.inputWorkspaceNamePlaceholder')}
          value={workspaceName}
          onChange={e => setWorkspaceName(e.target.value)}
          onPressEnter={handleSaveWorkspace}
          autoFocus
        />
      </Modal>

      {/* 新建工作区弹窗 */}
      <Modal
        title={t('workspace.newWorkspaceTitle')}
        open={newWorkspaceModalVisible}
        onOk={handleCreateNewWorkspace}
        onCancel={() => setNewWorkspaceModalVisible(false)}
        okText={t('workspace.create')}
        cancelText={t('common.cancel')}
      >
        <Input
          placeholder={t('workspace.inputWorkspaceNamePlaceholder')}
          value={workspaceName}
          onChange={e => setWorkspaceName(e.target.value)}
          onPressEnter={handleCreateNewWorkspace}
          autoFocus
        />
      </Modal>
    </div>
  );
};

// 获取面板标题
function getPanelTitle(type: PanelConfig['type'], t: (key: string) => string): string {
  const titles: Record<PanelConfig['type'], string> = {
    chart: t('workspace.panelTypes.chart'),
    table: t('workspace.panelTypes.table'),
    news: t('workspace.panelTypes.news'),
    watchlist: t('workspace.panelTypes.watchlist'),
    capitalFlow: t('workspace.panelTypes.capitalFlow'),
    heatmap: t('workspace.panelTypes.heatmap'),
    custom: t('workspace.panelTypes.custom') || t('workspace.panel'),
  };
  return titles[type] || t('workspace.panel');
}

export default Workspace;
