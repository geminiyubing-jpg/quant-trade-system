/**
 * Monaco 代码编辑器组件
 *
 * 提供专业级的代码编辑体验，支持 Python 语法高亮、自动补全等功能。
 */

import React, { useRef, useState } from 'react';
import Editor, { Monaco, OnMount } from '@monaco-editor/react';
import { Button, Select, Space, message, Tooltip } from 'antd';
import {
  SaveOutlined,
  FormatPainterOutlined,
  UndoOutlined,
  RedoOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
} from '@ant-design/icons';

// Monaco 类型定义
type IStandaloneCodeEditor = any;
type ITextModel = any;
type Position = any;
type IRange = any;

// 策略模板
const STRATEGY_TEMPLATES: Record<string, string> = {
  empty: `# 新建策略
# 请在此编写您的量化策略

class MyStrategy:
    def __init__(self):
        pass

    def on_bar(self, bar):
        """K线事件处理"""
        pass

    def on_tick(self, tick):
        """Tick事件处理"""
        pass
`,
  ma_cross: `# 双均线交叉策略
# 当短期均线上穿长期均线时买入，下穿时卖出

import numpy as np

class MACrossStrategy:
    """双均线交叉策略"""

    def __init__(self, fast_period=5, slow_period=20):
        self.fast_period = fast_period_period
        self.slow_period = slow_period
        self.fast_ma = None
        self.slow_ma = None
        self.position = 0

    def calculate_ma(self, prices: list, period: int) -> float:
        """计算移动平均线"""
        if len(prices) < period:
            return None
        return np.mean(prices[-period:])

    def on_bar(self, bar):
        """K线事件处理"""
        # 获取历史价格
        close_prices = self.get_history('close', self.slow_period + 1)

        if len(close_prices) < self.slow_period:
            return

        # 计算均线
        self.fast_ma = self.calculate_ma(close_prices, self.fast_period)
        self.slow_ma = self.calculate_ma(close_prices, self.slow_period)

        prev_fast = self.calculate_ma(close_prices[:-1], self.fast_period)
        prev_slow = self.calculate_ma(close_prices[:-1], self.slow_period)

        # 金叉买入
        if prev_fast <= prev_slow and self.fast_ma > self.slow_ma:
            if self.position <= 0:
                self.buy(bar.symbol, bar.close, 100)
                self.position = 100

        # 死叉卖出
        elif prev_fast >= prev_slow and self.fast_ma < self.slow_ma:
            if self.position > 0:
                self.sell(bar.symbol, bar.close, self.position)
                self.position = 0
`,
  momentum: `# 动量策略
# 基于价格动量的趋势跟踪策略

import numpy as np

class MomentumStrategy:
    """动量策略"""

    def __init__(self, lookback_period=20, threshold=0.02):
        self.lookback_period = lookback_period
        self.threshold = threshold  # 动量阈值
        self.position = 0

    def calculate_momentum(self, prices: list) -> float:
        """计算动量（收益率）"""
        if len(prices) < self.lookback_period:
            return 0
        return (prices[-1] - prices[-self.lookback_period]) / prices[-self.lookback_period]

    def on_bar(self, bar):
        """K线事件处理"""
        close_prices = self.get_history('close', self.lookback_period + 1)

        if len(close_prices) < self.lookback_period:
            return

        momentum = self.calculate_momentum(close_prices)

        # 动量突破阈值，买入
        if momentum > self.threshold and self.position <= 0:
            self.buy(bar.symbol, bar.close, 100)
            self.position = 100

        # 动量跌破负阈值，卖出
        elif momentum < -self.threshold and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position)
            self.position = 0

        # 动量回归，平仓
        elif abs(momentum) < self.threshold * 0.5 and self.position != 0:
            if self.position > 0:
                self.sell(bar.symbol, bar.close, self.position)
            self.position = 0
`,
  mean_reversion: `# 均值回归策略
# 当价格偏离均值过大时，预期回归

import numpy as np

class MeanReversionStrategy:
    """均值回归策略"""

    def __init__(self, period=20, std_threshold=2.0):
        self.period = period
        self.std_threshold = std_threshold
        self.position = 0

    def calculate_zscore(self, prices: list) -> float:
        """计算 Z-Score"""
        if len(prices) < self.period:
            return 0

        recent_prices = prices[-self.period:]
        mean = np.mean(recent_prices)
        std = np.std(recent_prices)

        if std == 0:
            return 0

        return (prices[-1] - mean) / std

    def on_bar(self, bar):
        """K线事件处理"""
        close_prices = self.get_history('close', self.period + 1)

        if len(close_prices) < self.period:
            return

        zscore = self.calculate_zscore(close_prices)

        # Z-Score 低于负阈值，超卖，买入
        if zscore < -self.std_threshold and self.position <= 0:
            self.buy(bar.symbol, bar.close, 100)
            self.position = 100

        # Z-Score 高于正阈值，超买，卖出
        elif zscore > self.std_threshold and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position)
            self.position = 0

        # 回归均值，平仓
        elif abs(zscore) < 0.5 and self.position != 0:
            if self.position > 0:
                self.sell(bar.symbol, bar.close, self.position)
            self.position = 0
`,
};

interface CodeEditorProps {
  /** 初始代码 */
  value?: string;
  /** 代码变更回调 */
  onChange?: (value: string) => void;
  /** 保存回调 */
  onSave?: (value: string) => void;
  /** 是否只读 */
  readOnly?: boolean;
  /** 编辑器高度 */
  height?: string | number;
  /** 是否显示工具栏 */
  showToolbar?: boolean;
  /** 初始模板 */
  template?: keyof typeof STRATEGY_TEMPLATES;
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  value = '',
  onChange,
  onSave,
  readOnly = false,
  height = '100%',
  showToolbar = true,
  template = 'empty',
}) => {
  const editorRef = useRef<IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState<string>(template);
  const [code, setCode] = useState<string>(value || STRATEGY_TEMPLATES[template]);

  // 编辑器挂载
  const handleEditorMount: OnMount = (editorInstance: IStandaloneCodeEditor, monaco: Monaco) => {
    editorRef.current = editorInstance;
    monacoRef.current = monaco;

    // 配置 Python 语法高亮
    monaco.languages.registerCompletionItemProvider('python', {
      provideCompletionItems: (model: ITextModel, position: Position) => {
        const word = model.getWordUntilPosition(position);
        const range: IRange = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        };

        // 常用代码片段
        const suggestions = [
          {
            label: 'on_bar',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'def on_bar(self, bar):\n\t"""K线事件处理"""\n\t${1:pass}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'K线事件处理函数',
            range,
          },
          {
            label: 'on_tick',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'def on_tick(self, tick):\n\t"""Tick事件处理"""\n\t${1:pass}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Tick事件处理函数',
            range,
          },
          {
            label: 'buy',
            kind: monaco.languages.CompletionItemKind.Method,
            insertText: 'self.buy(${1:symbol}, ${2:price}, ${3:quantity})',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: '买入股票',
            range,
          },
          {
            label: 'sell',
            kind: monaco.languages.CompletionItemKind.Method,
            insertText: 'self.sell(${1:symbol}, ${2:price}, ${3:quantity})',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: '卖出股票',
            range,
          },
          {
            label: 'get_history',
            kind: monaco.languages.CompletionItemKind.Method,
            insertText: "self.get_history('${1:close}', ${2:20})",
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: '获取历史数据',
            range,
          },
        ];

        return { suggestions };
      },
    });

    // 快捷键绑定
    editorInstance.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      handleSave();
    });

    // 格式化快捷键
    editorInstance.addCommand(monaco.KeyMod.Alt | monaco.KeyCode.KeyF, () => {
      handleFormat();
    });
  };

  // 代码变更
  const handleChange = (value: string | undefined) => {
    const newCode = value || '';
    setCode(newCode);
    onChange?.(newCode);
  };

  // 保存
  const handleSave = () => {
    onSave?.(code);
    message.success('代码已保存');
  };

  // 格式化代码
  const handleFormat = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument')?.run();
    }
  };

  // 撤销
  const handleUndo = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'undo', null);
    }
  };

  // 重做
  const handleRedo = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'redo', null);
    }
  };

  // 全屏切换
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // 加载模板
  const handleTemplateChange = (templateName: string) => {
    setCurrentTemplate(templateName);
    const templateCode = STRATEGY_TEMPLATES[templateName] || '';
    setCode(templateCode);
    if (editorRef.current) {
      editorRef.current.setValue(templateCode);
    }
    onChange?.(templateCode);
  };

  // 编辑器样式
  const editorStyle: React.CSSProperties = {
    height: isFullscreen ? '100vh' : height,
    border: '1px solid #303030',
    borderRadius: '4px',
    overflow: 'hidden',
  };

  return (
    <div style={{ height: isFullscreen ? '100vh' : '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 工具栏 */}
      {showToolbar && (
        <div
          style={{
            padding: '8px 12px',
            background: '#1a1a1a',
            borderBottom: '1px solid #303030',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Space>
            <Select
              value={currentTemplate}
              onChange={handleTemplateChange}
              style={{ width: 150 }}
              options={[
                { value: 'empty', label: '空白策略' },
                { value: 'ma_cross', label: '双均线交叉' },
                { value: 'momentum', label: '动量策略' },
                { value: 'mean_reversion', label: '均值回归' },
              ]}
              size="small"
            />

            <Tooltip title="撤销 (Ctrl+Z)">
              <Button size="small" icon={<UndoOutlined />} onClick={handleUndo} />
            </Tooltip>

            <Tooltip title="重做 (Ctrl+Y)">
              <Button size="small" icon={<RedoOutlined />} onClick={handleRedo} />
            </Tooltip>

            <Tooltip title="格式化 (Alt+F)">
              <Button size="small" icon={<FormatPainterOutlined />} onClick={handleFormat} />
            </Tooltip>
          </Space>

          <Space>
            <Tooltip title="保存 (Ctrl+S)">
              <Button
                type="primary"
                size="small"
                icon={<SaveOutlined />}
                onClick={handleSave}
              >
                保存
              </Button>
            </Tooltip>

            <Tooltip title={isFullscreen ? '退出全屏' : '全屏'}>
              <Button
                size="small"
                icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
                onClick={toggleFullscreen}
              />
            </Tooltip>
          </Space>
        </div>
      )}

      {/* 编辑器 */}
      <div style={editorStyle}>
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={handleChange}
          onMount={handleEditorMount}
          options={{
            readOnly,
            fontSize: 14,
            fontFamily: "'Fira Code', 'Consolas', monospace",
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            insertSpaces: true,
            wordWrap: 'on',
            lineNumbers: 'on',
            renderWhitespace: 'selection',
            bracketPairColorization: { enabled: true },
            autoClosingBrackets: 'always',
            autoClosingQuotes: 'always',
            formatOnPaste: true,
            formatOnType: true,
            suggestOnTriggerCharacters: true,
            quickSuggestions: true,
            acceptSuggestionOnEnter: 'on',
            folding: true,
            foldingStrategy: 'indentation',
            showFoldingControls: 'always',
            matchBrackets: 'always',
            renderLineHighlight: 'all',
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            smoothScrolling: true,
          }}
        />
      </div>
    </div>
  );
};

export default CodeEditor;
