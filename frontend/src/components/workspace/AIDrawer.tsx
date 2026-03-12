/**
 * AI 助手抽屉组件
 * AI Assistant Drawer Component
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Drawer, Input, Button, Spin, message } from 'antd';
import {
  SendOutlined,
  ClearOutlined,
  CopyOutlined,
  CodeOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import { ChatMessage } from '../../types/workspace';
import { aiService } from '../../services/ai';

const { TextArea } = Input;

interface AIDrawerProps {
  open: boolean;
  onClose: () => void;
}

const AIDrawer: React.FC<AIDrawerProps> = ({ open, onClose }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '👋 您好！我是您的 AI 投研助手。\n\n我可以帮您：\n- 分析股票走势\n- 解读财务数据\n- 筛选投资标的\n- 生成策略代码\n\n请问有什么可以帮您的？',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 发送消息
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      // 调用 AI 服务
      const response = await aiService.chat({
        message: userMessage.content,
        context: 'workspace',
      });

      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-response`,
        role: 'assistant',
        content: response.response || response.message || '抱歉，我暂时无法回答这个问题。',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI chat error:', error);
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: '抱歉，连接 AI 服务时出现错误。请稍后重试。',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }, [inputValue, loading]);

  // 清空对话
  const handleClear = useCallback(() => {
    setMessages([
      {
        id: 'welcome-new',
        role: 'assistant',
        content: '对话已清空。请问有什么可以帮您的？',
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  // 复制内容
  const handleCopy = useCallback((content: string) => {
    navigator.clipboard.writeText(content);
    message.success('已复制到剪贴板');
  }, []);

  // 快捷提示
  const quickPrompts = [
    { icon: <CodeOutlined />, text: '生成策略代码', prompt: '请帮我写一个基于均线交叉的量化策略代码' },
    { icon: <FileTextOutlined />, text: '分析财报', prompt: '请分析贵州茅台最新的财务报表' },
  ];

  return (
    <Drawer
      title={
        <div className="ai-drawer-header">
          <span>AI 投研助手</span>
          <Button
            icon={<ClearOutlined />}
            size="small"
            onClick={handleClear}
            title="清空对话"
          />
        </div>
      }
      placement="right"
      width={400}
      open={open}
      onClose={onClose}
      className="ai-drawer"
      styles={{
        body: { padding: 0, display: 'flex', flexDirection: 'column' },
      }}
    >
      {/* 消息列表 */}
      <div className="ai-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message message-${msg.role}`}>
            <div className="message-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    return inline ? (
                      <code className="inline-code" {...props}>{children}</code>
                    ) : (
                      <div className="code-block">
                        <button
                          className="copy-btn"
                          onClick={() => handleCopy(String(children))}
                        >
                          <CopyOutlined /> 复制
                        </button>
                        <pre>
                          <code className={className} {...props}>{children}</code>
                        </pre>
                      </div>
                    );
                  },
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
            <div className="message-time">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message message-assistant loading">
            <Spin size="small" />
            <span>思考中...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 快捷提示 */}
      <div className="quick-prompts">
        {quickPrompts.map((item, idx) => (
          <button
            key={idx}
            className="quick-prompt-btn"
            onClick={() => setInputValue(item.prompt)}
          >
            {item.icon}
            <span>{item.text}</span>
          </button>
        ))}
      </div>

      {/* 输入区域 */}
      <div className="ai-input-area">
        <TextArea
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          placeholder="输入您的问题..."
          autoSize={{ minRows: 2, maxRows: 4 }}
          onPressEnter={e => {
            if (!e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={loading}
          disabled={!inputValue.trim()}
        >
          发送
        </Button>
      </div>
    </Drawer>
  );
};

export default AIDrawer;
