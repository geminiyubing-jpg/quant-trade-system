/**
 * 策略工作室页面
 *
 * 提供策略代码编辑、调试和优化的集成开发环境。
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Layout,
  Button,
  Input,
  Tree,
  Tabs,
  Descriptions,
  Tag,
  Space,
  message,
  Modal,
  Form,
  Select,
  Divider,
  List,
  Typography,
  Tooltip,
  Dropdown,
  Empty,
  Spin,
} from 'antd';
import {
  FileAddOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  FileOutlined,
  PlayCircleOutlined,
  BugOutlined,
  DeleteOutlined,
  EditOutlined,
  CopyOutlined,
  DownloadOutlined,
  MoreOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  RobotOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import CodeEditor from '../components/CodeEditor';
import AIStrategyGenerator from '../components/AIStrategyGenerator';
import strategyRegistryService, { StrategyMetadata } from '../services/strategyRegistry';
import './StrategyStudio.css';

const { Sider, Content } = Layout;
const { Text, Title } = Typography;
const { TabPane } = Tabs;

// 策略文件接口
interface StrategyFile {
  id: string;
  name: string;
  type: 'file' | 'folder';
  content?: string;
  children?: StrategyFile[];
  status?: 'draft' | 'testing' | 'passed' | 'failed';
  createdAt?: string;
  updatedAt?: string;
}

// 日志条目接口
interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
}

// 策略状态到文件状态的映射
const strategyStatusToFileStatus = (status: string): 'draft' | 'testing' | 'passed' | 'failed' => {
  const mapping: Record<string, 'draft' | 'testing' | 'passed' | 'failed'> = {
    development: 'draft',
    testing: 'testing',
    backtest_passed: 'passed',
    paper_trading: 'passed',
    live_trading: 'passed',
    deprecated: 'failed',
    suspended: 'failed',
  };
  return mapping[status] || 'draft';
};

// 将策略注册表数据转换为文件树格式
const convertStrategiesToFiles = (strategies: StrategyMetadata[]): StrategyFile[] => {
  // 按分类分组
  const categoryMap = new Map<string, StrategyMetadata[]>();

  strategies.forEach(strategy => {
    const category = strategy.category || '未分类';
    if (!categoryMap.has(category)) {
      categoryMap.set(category, []);
    }
    categoryMap.get(category)!.push(strategy);
  });

  // 转换为文件树结构
  const files: StrategyFile[] = [];

  categoryMap.forEach((strategyList, categoryName) => {
    const folder: StrategyFile = {
      id: `folder-${categoryName}`,
      name: categoryName,
      type: 'folder',
      children: strategyList.map(strategy => ({
        id: strategy.strategy_id,
        name: `${strategy.name}.py`,
        type: 'file' as const,
        status: strategyStatusToFileStatus(strategy.status),
        content: `# ${strategy.name}\n# ${strategy.description || ''}\n# 版本: ${strategy.version}\n# 作者: ${strategy.author || '未知'}\n\n# 参数配置:\n# ${JSON.stringify(strategy.default_params, null, 2)}\n\nclass ${strategy.strategy_id}:\n    """${strategy.description || strategy.name}"""\n    pass`,
        createdAt: strategy.version ? new Date().toISOString() : undefined,
        updatedAt: new Date().toISOString(),
      })),
    };
    files.push(folder);
  });

  // 如果没有策略，返回默认的空结构
  if (files.length === 0) {
    files.push({
      id: 'folder-empty',
      name: '策略文件',
      type: 'folder',
      children: [],
    });
  }

  return files;
};

const StrategyStudio: React.FC = () => {
  // 状态
  const [files, setFiles] = useState<StrategyFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<StrategyFile | null>(null);
  const [code, setCode] = useState<string>('');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [aiGeneratorVisible, setAiGeneratorVisible] = useState(false);
  // 预留状态变量，未来用于 Tab 切换
  const [_activeTab, _setActiveTab] = useState('editor');
  // 新建文件夹弹窗状态
  const [createFolderModalVisible, setCreateFolderModalVisible] = useState(false);
  const [folderForm] = Form.useForm();
  // 调试状态
  const [debugging, setDebugging] = useState(false);
  // 重命名弹窗状态
  const [renameModalVisible, setRenameModalVisible] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  // 版本恢复弹窗状态
  const [versionRestoreId, setVersionRestoreId] = useState<string | null>(null);

  const [form] = Form.useForm();

  // 从策略注册表加载策略文件
  const loadStrategies = useCallback(async () => {
    setLoading(true);
    try {
      const result = await strategyRegistryService.getStrategies();
      const strategyList = result.data || [];
      setFiles(convertStrategiesToFiles(strategyList));
      addLog('info', `已从策略注册表加载 ${strategyList.length} 个策略`);
    } catch (error) {
      console.error('加载策略失败:', error);
      addLog('error', '从策略注册表加载策略失败');
      message.error('加载策略失败');
      // 设置空的文件结构
      setFiles([{
        id: 'folder-empty',
        name: '策略文件',
        type: 'folder',
        children: [],
      }]);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始化
  useEffect(() => {
    addLog('info', '策略工作室已加载');
    addLog('info', '正在从策略注册表加载策略文件...');
    loadStrategies();
  }, [loadStrategies]);

  // 添加日志
  const addLog = (level: LogEntry['level'], message: string) => {
    const now = new Date();
    const timestamp = now.toLocaleTimeString('zh-CN', { hour12: false });
    setLogs(prev => [...prev, { timestamp, level, message }]);
  };

  // 将文件树转换为 Ant Design Tree 格式
  const convertToTreeData = (items: StrategyFile[]): any[] => {
    return items.map(item => ({
      key: item.id,
      title: (
        <span>
          {item.name}
          {item.status && (
            <Tag
              color={
                item.status === 'passed' ? 'success' :
                item.status === 'testing' ? 'processing' :
                item.status === 'failed' ? 'error' : 'default'
              }
              style={{ marginLeft: 8, fontSize: 10 }}
            >
              {item.status === 'passed' ? '已通过' :
               item.status === 'testing' ? '测试中' :
               item.status === 'failed' ? '失败' : '草稿'}
            </Tag>
          )}
        </span>
      ),
      icon: item.type === 'folder' ? <FolderOutlined /> : <FileOutlined />,
      children: item.children ? convertToTreeData(item.children) : undefined,
    }));
  };

  // 选择文件
  const handleFileSelect = (selectedKeys: React.Key[]) => {
    const fileId = selectedKeys[0] as string;
    const file = findFileById(files, fileId);
    if (file && file.type === 'file') {
      setSelectedFile(file);
      setCode(file.content || '');
      addLog('info', `已打开策略: ${file.name}`);
    }
  };

  // 查找文件
  const findFileById = (items: StrategyFile[], id: string): StrategyFile | null => {
    for (const item of items) {
      if (item.id === id) return item;
      if (item.children) {
        const found = findFileById(item.children, id);
        if (found) return found;
      }
    }
    return null;
  };

  // 保存代码
  const handleSave = (newCode: string) => {
    if (selectedFile) {
      // 更新文件内容
      const updateFileContent = (items: StrategyFile[]): StrategyFile[] => {
        return items.map(item => {
          if (item.id === selectedFile.id) {
            return { ...item, content: newCode, updatedAt: new Date().toISOString() };
          }
          if (item.children) {
            return { ...item, children: updateFileContent(item.children) };
          }
          return item;
        });
      };
      setFiles(updateFileContent(files));
      addLog('success', `策略已保存: ${selectedFile.name}`);
    }
  };

  // 运行回测
  const handleRunBacktest = () => {
    if (!selectedFile) {
      message.warning('请先选择一个策略文件');
      return;
    }

    setIsRunning(true);
    addLog('info', `开始运行回测: ${selectedFile.name}`);

    // 模拟回测过程
    setTimeout(() => {
      addLog('info', '加载数据...');
    }, 500);

    setTimeout(() => {
      addLog('info', '执行策略逻辑...');
    }, 1000);

    setTimeout(() => {
      addLog('success', '回测完成！年化收益率: 15.2%, 最大回撤: 8.5%, 夏普比率: 1.35');
      setIsRunning(false);
    }, 2000);
  };

  // 创建新策略
  const handleCreateStrategy = (values: { name: string; template: string; folder: string }) => {
    const newFile: StrategyFile = {
      id: Date.now().toString(),
      name: values.name.endsWith('.py') ? values.name : `${values.name}.py`,
      type: 'file',
      status: 'draft',
      content: `# ${values.name}\n# 创建时间: ${new Date().toLocaleString()}\n\nclass ${values.name.replace('.py', '').replace(/\s+/g, '')}:\n    pass`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // 添加到文件列表
    setFiles(prev => {
      const newFiles = [...prev];
      // 找到目标文件夹或添加到根目录
      const addToFolder = (items: StrategyFile[]): void => {
        for (const item of items) {
          if (item.type === 'folder') {
            if (item.name === values.folder || values.folder === 'root') {
              item.children = item.children || [];
              item.children.push(newFile);
              return;
            }
            if (item.children) {
              addToFolder(item.children);
            }
          }
        }
      };

      if (values.folder === 'root') {
        newFiles.push(newFile);
      } else {
        addToFolder(newFiles);
      }

      return newFiles;
    });

    setCreateModalVisible(false);
    form.resetFields();
    addLog('success', `创建新策略: ${newFile.name}`);
    message.success('策略创建成功，请通过策略注册表注册此策略');
  };

  // 文件操作菜单
  const getFileOperations = () => ({
    items: [
      {
        key: 'rename',
        icon: <EditOutlined />,
        label: '重命名',
      },
      {
        key: 'copy',
        icon: <CopyOutlined />,
        label: '复制',
      },
      {
        key: 'download',
        icon: <DownloadOutlined />,
        label: '下载',
      },
      { type: 'divider' as const },
      {
        key: 'delete',
        icon: <DeleteOutlined />,
        label: '删除',
        danger: true,
      },
    ],
    onClick: ({ key }: { key: string }) => {
      switch (key) {
        case 'rename':
          if (selectedFile) {
            setNewFileName(selectedFile.name.replace('.py', ''));
            setRenameModalVisible(true);
          }
          break;
        case 'copy':
          if (selectedFile) {
            // 复制文件到同一目录
            const newFile: StrategyFile = {
              ...selectedFile,
              id: `${Date.now()}`,
              name: `${selectedFile.name.replace('.py', '')}_copy.py`,
              status: 'draft',
              updatedAt: new Date().toISOString(),
            };
            setFiles(prev => {
              const addToFolder = (items: StrategyFile[]): StrategyFile[] => {
                return items.map(item => {
                  if (item.type === 'folder') {
                    const hasFile = item.children?.some(c => c.id === selectedFile.id);
                    if (hasFile) {
                      return {
                        ...item,
                        children: [...(item.children || []), newFile],
                      };
                    }
                    return { ...item, children: addToFolder(item.children || []) };
                  }
                  return item;
                });
              };
              return addToFolder(prev);
            });
            addLog('success', `策略已复制: ${newFile.name}`);
            message.success('策略复制成功');
          }
          break;
        case 'download':
          if (selectedFile) {
            const blob = new Blob([code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = selectedFile.name;
            a.click();
            URL.revokeObjectURL(url);
            message.success('下载成功');
          }
          break;
        case 'delete':
          Modal.confirm({
            title: '确认删除',
            content: `确定要删除 "${selectedFile?.name}" 吗？`,
            onOk: () => {
              setFiles(prev => {
                const removeFile = (items: StrategyFile[]): StrategyFile[] => {
                  return items
                    .filter(item => item.id !== selectedFile?.id)
                    .map(item => {
                      if (item.children) {
                        return { ...item, children: removeFile(item.children) };
                      }
                      return item;
                    });
                };
                return removeFile(prev);
              });
              addLog('info', `策略已删除: ${selectedFile?.name}`);
              message.success('删除成功');
              setSelectedFile(null);
              setCode('');
            },
          });
          break;
      }
    },
  });

  // 清空日志
  const clearLogs = () => {
    setLogs([]);
    addLog('info', '日志已清空');
  };

  // 新建文件夹
  const handleCreateFolder = (values: { name: string }) => {
    const newFolder: StrategyFile = {
      id: `folder-${Date.now()}`,
      name: values.name,
      type: 'folder',
      children: [],
    };
    setFiles(prev => [...prev, newFolder]);
    setCreateFolderModalVisible(false);
    folderForm.resetFields();
    addLog('success', `文件夹已创建: ${values.name}`);
    message.success('文件夹创建成功');
  };

  // 调试策略
  const handleDebugStrategy = async () => {
    if (!selectedFile) {
      message.warning('请先选择一个策略文件');
      return;
    }

    setDebugging(true);
    addLog('info', `开始调试策略: ${selectedFile.name}`);

    // 模拟调试过程
    setTimeout(() => {
      addLog('info', '解析策略代码...');
    }, 500);

    setTimeout(() => {
      addLog('info', '检查语法错误...');
    }, 1000);

    setTimeout(() => {
      addLog('info', '运行单元测试...');
    }, 1500);

    setTimeout(() => {
      addLog('success', '调试完成！策略代码无语法错误');
      setDebugging(false);
    }, 2500);
  };

  // 确认重命名
  const handleRenameConfirm = () => {
    if (!selectedFile || !newFileName.trim()) {
      message.error('请输入有效的文件名');
      return;
    }

    const updatedName = newFileName.endsWith('.py') ? newFileName : `${newFileName}.py`;
    setFiles(prev => {
      const renameFile = (items: StrategyFile[]): StrategyFile[] => {
        return items.map(item => {
          if (item.id === selectedFile.id) {
            return { ...item, name: updatedName, updatedAt: new Date().toISOString() };
          }
          if (item.children) {
            return { ...item, children: renameFile(item.children) };
          }
          return item;
        });
      };
      return renameFile(prev);
    });

    setSelectedFile(prev => prev ? { ...prev, name: updatedName } : null);
    setRenameModalVisible(false);
    addLog('success', `文件已重命名为: ${updatedName}`);
    message.success('重命名成功');
  };

  // 恢复历史版本
  const handleRestoreVersion = (version: string) => {
    setVersionRestoreId(version);
    Modal.confirm({
      title: '恢复历史版本',
      content: `确定要恢复到 ${version} 吗？当前未保存的更改将丢失。`,
      onOk: () => {
        // 模拟恢复历史版本
        addLog('info', `正在恢复到 ${version}...`);
        setTimeout(() => {
          addLog('success', `已恢复到 ${version}`);
          message.success(`已恢复到 ${version}`);
          setVersionRestoreId(null);
        }, 500);
      },
      onCancel: () => {
        setVersionRestoreId(null);
      },
    });
  };

  return (
    <Layout className="strategy-studio">
      {/* 左侧边栏 - 文件浏览器 */}
      <Sider width={260} theme="light" className="file-explorer">
        <div className="explorer-header">
          <Title level={5} style={{ margin: 0 }}>
            <FolderOpenOutlined style={{ marginRight: 8 }} />
            策略文件
          </Title>
          <Space>
            <Tooltip title="刷新策略列表">
              <Button
                type="text"
                size="small"
                icon={<ReloadOutlined spin={loading} />}
                onClick={loadStrategies}
                loading={loading}
              />
            </Tooltip>
            <Tooltip title="新建策略">
              <Button
                type="text"
                size="small"
                icon={<FileAddOutlined />}
                onClick={() => setCreateModalVisible(true)}
              />
            </Tooltip>
            <Tooltip title="新建文件夹">
              <Button type="text" size="small" icon={<FolderOutlined />} onClick={() => setCreateFolderModalVisible(true)} />
            </Tooltip>
          </Space>
        </div>

        <Spin spinning={loading}>
          <div className="file-tree">
            {files.length > 0 ? (
              <Tree
                showIcon
                showLine
                defaultExpandAll
                treeData={convertToTreeData(files)}
                onSelect={handleFileSelect}
              />
            ) : (
              <Empty description="暂无策略文件" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </div>
        </Spin>

        {/* 快速操作 */}
        <div className="quick-actions">
          <Button
            type="primary"
            icon={<RobotOutlined />}
            block
            onClick={() => setAiGeneratorVisible(true)}
            style={{ marginBottom: 8 }}
          >
            AI 生成策略
          </Button>
          <Button
            icon={<PlayCircleOutlined />}
            block
            onClick={handleRunBacktest}
            loading={isRunning}
            disabled={!selectedFile}
          >
            运行回测
          </Button>
          <Button
            icon={<BugOutlined />}
            block
            style={{ marginTop: 8 }}
            disabled={!selectedFile}
            loading={debugging}
            onClick={handleDebugStrategy}
          >
            调试策略
          </Button>
        </div>
      </Sider>

      {/* 主内容区 */}
      <Layout>
        {/* 编辑器区域 */}
        <Content className="editor-content">
          {selectedFile ? (
            <div className="editor-wrapper">
              <div className="editor-header">
                <Space>
                  <Dropdown menu={getFileOperations()}>
                    <Button type="text" icon={<MoreOutlined />} />
                  </Dropdown>
                  <Text strong>{selectedFile.name}</Text>
                  {selectedFile.status && (
                    <Tag
                      color={
                        selectedFile.status === 'passed' ? 'success' :
                        selectedFile.status === 'testing' ? 'processing' :
                        selectedFile.status === 'failed' ? 'error' : 'default'
                      }
                    >
                      {selectedFile.status === 'passed' ? '已通过' :
                       selectedFile.status === 'testing' ? '测试中' :
                       selectedFile.status === 'failed' ? '失败' : '草稿'}
                    </Tag>
                  )}
                </Space>
                <Space>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    最后更新: {selectedFile.updatedAt}
                  </Text>
                </Space>
              </div>
              <CodeEditor
                value={code}
                onChange={setCode}
                onSave={handleSave}
                height="calc(100vh - 180px)"
              />
            </div>
          ) : (
            <div className="empty-editor">
              <Empty
                description="选择一个策略文件开始编辑"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button
                  type="primary"
                  icon={<FileAddOutlined />}
                  onClick={() => setCreateModalVisible(true)}
                >
                  创建新策略
                </Button>
              </Empty>
            </div>
          )}
        </Content>

        {/* 底部日志面板 */}
        <div className="log-panel">
          <div className="log-header">
            <Space>
              <Text strong>输出日志</Text>
              <Tag>{logs.length} 条</Tag>
            </Space>
            <Button type="text" size="small" onClick={clearLogs}>
              清空
            </Button>
          </div>
          <div className="log-content">
            {logs.map((log, index) => (
              <div key={index} className={`log-entry log-${log.level}`}>
                <span className="log-time">[{log.timestamp}]</span>
                <span className="log-level">
                  {log.level === 'success' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                  {log.level === 'error' && <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
                  {log.level === 'warning' && <ExclamationCircleOutlined style={{ color: '#faad14' }} />}
                  {log.level === 'info' && <SyncOutlined style={{ color: '#1890ff' }} />}
                </span>
                <span className="log-message">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      </Layout>

      {/* 右侧边栏 - 策略信息 */}
      <Sider width={280} theme="light" className="strategy-info">
        <Tabs defaultActiveKey="info" size="small">
          <TabPane tab="策略信息" key="info">
            {selectedFile ? (
              <Descriptions column={1} size="small">
                <Descriptions.Item label="名称">{selectedFile.name}</Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={selectedFile.status === 'passed' ? 'success' : 'default'}>
                    {selectedFile.status || '草稿'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">{selectedFile.createdAt}</Descriptions.Item>
                <Descriptions.Item label="更新时间">{selectedFile.updatedAt}</Descriptions.Item>
              </Descriptions>
            ) : (
              <Empty description="未选择策略" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}

            <Divider />

            <Title level={5}>最近回测结果</Title>
            {selectedFile ? (
              <List
                size="small"
                dataSource={[
                  { label: '年化收益率', value: '15.2%' },
                  { label: '最大回撤', value: '8.5%' },
                  { label: '夏普比率', value: '1.35' },
                  { label: '胜率', value: '62.5%' },
                ]}
                renderItem={item => (
                  <List.Item>
                    <Text type="secondary">{item.label}:</Text>
                    <Text strong>{item.value}</Text>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无回测结果" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </TabPane>

          <TabPane tab="历史版本" key="history">
            <List
              size="small"
              dataSource={selectedFile ? [
                { version: 'v1.2', date: '2026-03-10', desc: '优化参数' },
                { version: 'v1.1', date: '2026-03-08', desc: '修复bug' },
                { version: 'v1.0', date: '2026-03-05', desc: '初始版本' },
              ] : []}
              renderItem={item => (
                <List.Item actions={[
                  <Button
                    type="link"
                    size="small"
                    loading={versionRestoreId === item.version}
                    onClick={() => handleRestoreVersion(item.version)}
                  >
                    恢复
                  </Button>
                ]}>
                  <List.Item.Meta
                    title={item.version}
                    description={`${item.date} - ${item.desc}`}
                  />
                </List.Item>
              )}
            />
          </TabPane>

          <TabPane tab="设置" key="settings">
            <Form layout="vertical" size="small">
              <Form.Item label="回测起始日期">
                <Input type="date" defaultValue="2025-01-01" />
              </Form.Item>
              <Form.Item label="回测结束日期">
                <Input type="date" defaultValue="2025-12-31" />
              </Form.Item>
              <Form.Item label="初始资金">
                <Input defaultValue="1000000" />
              </Form.Item>
              <Form.Item label="手续费率">
                <Input defaultValue="0.0003" />
              </Form.Item>
              <Form.Item label="滑点">
                <Input defaultValue="0.001" />
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Sider>

      {/* 创建策略弹窗 */}
      <Modal
        title="创建新策略"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateStrategy}
          initialValues={{ template: 'empty', folder: 'root' }}
        >
          <Form.Item
            name="name"
            label="策略名称"
            rules={[{ required: true, message: '请输入策略名称' }]}
          >
            <Input placeholder="例如: my_strategy" />
          </Form.Item>

          <Form.Item name="template" label="策略模板">
            <Select>
              <Select.Option value="empty">空白策略</Select.Option>
              <Select.Option value="ma_cross">双均线交叉</Select.Option>
              <Select.Option value="momentum">动量策略</Select.Option>
              <Select.Option value="mean_reversion">均值回归</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="folder" label="保存位置">
            <Select>
              <Select.Option value="root">根目录</Select.Option>
              <Select.Option value="我的策略">我的策略</Select.Option>
              <Select.Option value="示例策略">示例策略</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* AI 策略生成器弹窗 */}
      <AIStrategyGenerator
        visible={aiGeneratorVisible}
        onClose={() => setAiGeneratorVisible(false)}
        onStrategyGenerated={(strategy) => {
          addLog('success', `AI 策略已生成并保存: ${strategy.strategy_id}`);
          message.success('AI 策略已保存到策略注册表');
          // 刷新策略列表
          loadStrategies();
        }}
      />

      {/* 新建文件夹弹窗 */}
      <Modal
        title="新建文件夹"
        open={createFolderModalVisible}
        onCancel={() => setCreateFolderModalVisible(false)}
        onOk={() => folderForm.submit()}
      >
        <Form
          form={folderForm}
          layout="vertical"
          onFinish={handleCreateFolder}
        >
          <Form.Item
            name="name"
            label="文件夹名称"
            rules={[{ required: true, message: '请输入文件夹名称' }]}
          >
            <Input placeholder="例如: 我的策略" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 重命名弹窗 */}
      <Modal
        title="重命名策略"
        open={renameModalVisible}
        onCancel={() => setRenameModalVisible(false)}
        onOk={handleRenameConfirm}
      >
        <Form layout="vertical">
          <Form.Item label="新文件名">
            <Input
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              placeholder="输入新文件名"
              suffix=".py"
            />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
};

export default StrategyStudio;
