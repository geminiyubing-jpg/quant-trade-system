/**
 * 工作区持久化 Hook
 * Workspace Persistence Hook
 *
 * 负责工作区配置的本地存储读写
 */
import { useState, useEffect, useCallback } from 'react';
import { WorkspaceConfig, PanelConfig } from '../types/workspace';

// 存储键
const WORKSPACE_STORAGE_KEY = 'quant_workspace_configs';
const MAX_SAVED_WORKSPACES = 10;

// 默认工作区模板
export const DEFAULT_TEMPLATES: WorkspaceConfig[] = [
  {
    id: 'template-technical-analysis',
    name: '技术分析',
    description: 'K线图、技术指标、成交量、资金流向',
    panels: [
      {
        id: 'chart-1',
        type: 'chart',
        title: 'K线图',
        layout: { x: 0, y: 0, w: 8, h: 12, minW: 4, minH: 6 },
        config: { symbol: '000001.SZ', chartType: 'candlestick', indicators: ['MA5', 'MA10', 'MA20'] },
      },
      {
        id: 'capitalFlow-1',
        type: 'capitalFlow',
        title: '资金流向',
        layout: { x: 8, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
      },
      {
        id: 'watchlist-1',
        type: 'watchlist',
        title: '自选股',
        layout: { x: 8, y: 6, w: 4, h: 6, minW: 3, minH: 4 },
      },
    ],
    isPreset: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'template-fundamental-analysis',
    name: '基本面分析',
    description: '财务数据、估值指标、新闻、公告',
    panels: [
      {
        id: 'table-1',
        type: 'table',
        title: '财务数据',
        layout: { x: 0, y: 0, w: 6, h: 8, minW: 4, minH: 5 },
      },
      {
        id: 'news-1',
        type: 'news',
        title: '相关新闻',
        layout: { x: 6, y: 0, w: 6, h: 8, minW: 3, minH: 4 },
      },
      {
        id: 'table-2',
        type: 'table',
        title: '估值指标',
        layout: { x: 0, y: 8, w: 12, h: 4, minW: 6, minH: 3 },
      },
    ],
    isPreset: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'template-realtime-monitor',
    name: '实时监控',
    description: '自选股列表、实时行情、涨跌幅榜',
    panels: [
      {
        id: 'watchlist-2',
        type: 'watchlist',
        title: '自选股监控',
        layout: { x: 0, y: 0, w: 4, h: 12, minW: 3, minH: 6 },
      },
      {
        id: 'table-3',
        type: 'table',
        title: '涨幅榜',
        layout: { x: 4, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
      },
      {
        id: 'table-4',
        type: 'table',
        title: '跌幅榜',
        layout: { x: 8, y: 0, w: 4, h: 6, minW: 3, minH: 4 },
      },
      {
        id: 'heatmap-1',
        type: 'heatmap',
        title: '板块热力图',
        layout: { x: 4, y: 6, w: 8, h: 6, minW: 4, minH: 4 },
      },
    ],
    isPreset: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'template-ai-research',
    name: 'AI 研报',
    description: 'AI 对话、数据表、图表',
    panels: [
      {
        id: 'chart-2',
        type: 'chart',
        title: '价格走势',
        layout: { x: 0, y: 0, w: 6, h: 6, minW: 4, minH: 4 },
      },
      {
        id: 'table-5',
        type: 'table',
        title: '核心数据',
        layout: { x: 6, y: 0, w: 6, h: 6, minW: 3, minH: 4 },
      },
      {
        id: 'news-2',
        type: 'news',
        title: '研报新闻',
        layout: { x: 0, y: 6, w: 12, h: 6, minW: 6, minH: 4 },
      },
    ],
    isPreset: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

interface UseWorkspacePersistenceReturn {
  // 当前工作区
  currentWorkspace: WorkspaceConfig | null;
  setCurrentWorkspace: (workspace: WorkspaceConfig | null) => void;

  // 保存的工作区列表
  savedWorkspaces: WorkspaceConfig[];

  // 预设模板
  templates: WorkspaceConfig[];

  // 操作方法
  saveWorkspace: (workspace: WorkspaceConfig) => void;
  deleteWorkspace: (workspaceId: string) => void;
  loadWorkspace: (workspaceId: string) => WorkspaceConfig | null;
  createNewWorkspace: (name: string) => WorkspaceConfig;
  duplicateWorkspace: (workspaceId: string) => WorkspaceConfig | null;

  // 面板操作
  updatePanels: (panels: PanelConfig[]) => void;
}

/**
 * 工作区持久化 Hook
 */
export function useWorkspacePersistence(): UseWorkspacePersistenceReturn {
  const [currentWorkspace, setCurrentWorkspace] = useState<WorkspaceConfig | null>(null);
  const [savedWorkspaces, setSavedWorkspaces] = useState<WorkspaceConfig[]>([]);

  // 从 localStorage 加载保存的工作区
  useEffect(() => {
    try {
      const saved = localStorage.getItem(WORKSPACE_STORAGE_KEY);
      if (saved) {
        const data = JSON.parse(saved);
        setSavedWorkspaces(data.savedWorkspaces || []);

        // 恢复上次活动的工作区
        if (data.activeWorkspaceId) {
          const active = (data.savedWorkspaces || []).find(
            (w: WorkspaceConfig) => w.id === data.activeWorkspaceId
          );
          if (active) {
            setCurrentWorkspace(active);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load workspace from localStorage:', error);
    }
  }, []);

  // 保存到 localStorage
  const saveToStorage = useCallback(
    (workspaces: WorkspaceConfig[], activeId?: string) => {
      try {
        localStorage.setItem(
          WORKSPACE_STORAGE_KEY,
          JSON.stringify({
            savedWorkspaces: workspaces,
            activeWorkspaceId: activeId || currentWorkspace?.id,
          })
        );
      } catch (error) {
        console.error('Failed to save workspace to localStorage:', error);
        // 如果存储空间不足，删除最旧的工作区
        if (error instanceof DOMException && error.name === 'QuotaExceededError') {
          const trimmed = workspaces.slice(-MAX_SAVED_WORKSPACES + 1);
          saveToStorage(trimmed, activeId);
        }
      }
    },
    [currentWorkspace]
  );

  // 保存工作区
  const saveWorkspace = useCallback(
    (workspace: WorkspaceConfig) => {
      const updatedWorkspace = {
        ...workspace,
        updatedAt: new Date().toISOString(),
      };

      setSavedWorkspaces((prev) => {
        const existingIndex = prev.findIndex((w) => w.id === workspace.id);
        let newWorkspaces: WorkspaceConfig[];

        if (existingIndex >= 0) {
          newWorkspaces = [...prev];
          newWorkspaces[existingIndex] = updatedWorkspace;
        } else {
          newWorkspaces = [...prev, updatedWorkspace];
        }

        saveToStorage(newWorkspaces, workspace.id);
        return newWorkspaces;
      });

      setCurrentWorkspace(updatedWorkspace);
    },
    [saveToStorage]
  );

  // 删除工作区
  const deleteWorkspace = useCallback(
    (workspaceId: string) => {
      setSavedWorkspaces((prev) => {
        const newWorkspaces = prev.filter((w) => w.id !== workspaceId);
        saveToStorage(newWorkspaces);

        if (currentWorkspace?.id === workspaceId) {
          setCurrentWorkspace(null);
        }

        return newWorkspaces;
      });
    },
    [currentWorkspace, saveToStorage]
  );

  // 加载工作区
  const loadWorkspace = useCallback(
    (workspaceId: string): WorkspaceConfig | null => {
      // 先从保存的工作区中查找
      const saved = savedWorkspaces.find((w) => w.id === workspaceId);
      if (saved) {
        setCurrentWorkspace(saved);
        saveToStorage(savedWorkspaces, workspaceId);
        return saved;
      }

      // 再从模板中查找
      const template = DEFAULT_TEMPLATES.find((t) => t.id === workspaceId);
      if (template) {
        // 从模板创建新实例
        const newWorkspace: WorkspaceConfig = {
          ...template,
          id: `workspace-${Date.now()}`,
          isPreset: false,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        setCurrentWorkspace(newWorkspace);
        return newWorkspace;
      }

      return null;
    },
    [savedWorkspaces, saveToStorage]
  );

  // 创建新工作区
  const createNewWorkspace = useCallback((name: string): WorkspaceConfig => {
    const newWorkspace: WorkspaceConfig = {
      id: `workspace-${Date.now()}`,
      name,
      panels: [],
      isPreset: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setCurrentWorkspace(newWorkspace);
    return newWorkspace;
  }, []);

  // 复制工作区
  const duplicateWorkspace = useCallback(
    (workspaceId: string): WorkspaceConfig | null => {
      const original =
        savedWorkspaces.find((w) => w.id === workspaceId) ||
        DEFAULT_TEMPLATES.find((t) => t.id === workspaceId);

      if (!original) return null;

      const duplicated: WorkspaceConfig = {
        ...original,
        id: `workspace-${Date.now()}`,
        name: `${original.name} (副本)`,
        isPreset: false,
        panels: original.panels.map((p) => ({
          ...p,
          id: `panel-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        })),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      saveWorkspace(duplicated);
      return duplicated;
    },
    [savedWorkspaces, saveWorkspace]
  );

  // 更新面板
  const updatePanels = useCallback(
    (panels: PanelConfig[]) => {
      if (!currentWorkspace) return;

      const updated = {
        ...currentWorkspace,
        panels,
        updatedAt: new Date().toISOString(),
      };

      setCurrentWorkspace(updated);

      // 自动保存到 savedWorkspaces
      setSavedWorkspaces((prev) => {
        const existingIndex = prev.findIndex((w) => w.id === currentWorkspace.id);
        let newWorkspaces: WorkspaceConfig[];

        if (existingIndex >= 0) {
          newWorkspaces = [...prev];
          newWorkspaces[existingIndex] = updated;
        } else {
          newWorkspaces = [...prev, updated];
        }

        saveToStorage(newWorkspaces, currentWorkspace.id);
        return newWorkspaces;
      });
    },
    [currentWorkspace, saveToStorage]
  );

  return {
    currentWorkspace,
    setCurrentWorkspace,
    savedWorkspaces,
    templates: DEFAULT_TEMPLATES,
    saveWorkspace,
    deleteWorkspace,
    loadWorkspace,
    createNewWorkspace,
    duplicateWorkspace,
    updatePanels,
  };
}

export default useWorkspacePersistence;
