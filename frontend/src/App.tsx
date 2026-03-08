import { useState, useEffect, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, ConfigProvider, theme } from 'antd';
import { useTranslation } from 'react-i18next';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import { TradingModeProvider } from './contexts/TradingModeContext';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DataManagement from './pages/DataManagement';
import StrategyManagement from './pages/StrategyManagement';
import Backtest from './pages/Backtest';
import Trading from './pages/Trading';
import MarketRealtime from './pages/MarketRealtime';
import './App.css';
import './styles/font-switch.css';

const { Content } = Layout;

function App() {
  const { i18n } = useTranslation();
  const [collapsed, setCollapsed] = useState(false);

  // 根据当前语言动态设置字体
  useEffect(() => {
    const fontType = i18n.language === 'zh_CN' ? 'zh' : 'en';
    document.body.setAttribute('data-font', fontType);
  }, [i18n.language]);

  // 根据语言动态设置字体
  const currentFont = useMemo(() => {
    return i18n.language === 'zh_CN'
      ? "'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace"
      : "'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif";
  }, [i18n.language]);

  // Ant Design 主题配置（动态字体）
  const antdTheme = {
    algorithm: theme.darkAlgorithm,
    token: {
      fontFamily: currentFont,
      fontSize: 13,
    },
  };

  // 根据当前语言动态设置 Ant Design locale
  const antdLocale = i18n.language === 'zh_CN' ? zhCN : enUS;

  return (
    <TradingModeProvider>
      <ConfigProvider locale={antdLocale} theme={antdTheme}>
        <BrowserRouter>
          <Routes>
            {/* 登录页面 - 无需认证 */}
            <Route path="/login" element={<Login />} />

            {/* 主应用 - 需要认证 */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout style={{ minHeight: '100vh' }}>
                    {/* 顶部功能栏 - 贯通整个页面 */}
                    <Layout.Header
                      style={{
                        background: 'var(--bb-bg-secondary)',
                        padding: 0,
                        borderBottom: '1px solid var(--bb-border)',
                        height: 64,
                        width: '100%',
                        position: 'fixed',
                        zIndex: 1000,
                        left: 0,
                        right: 0,
                        top: 0,
                      }}
                    >
                      <TopBar />
                    </Layout.Header>

                    {/* 主体区域 - 包含侧边栏和内容 */}
                    <Layout style={{ marginTop: 64 }}>
                      {/* 左侧导航栏 */}
                      <Layout.Sider
                        collapsible
                        collapsed={collapsed}
                        onCollapse={setCollapsed}
                        theme="dark"
                        width={200}
                        collapsedWidth={64}
                        trigger={null}
                        style={{
                          background: 'var(--bb-bg-secondary)',
                          borderRight: '1px solid var(--bb-border)',
                          position: 'fixed',
                          left: 0,
                          top: 64,
                          bottom: 0,
                          zIndex: 999,
                        }}
                      >
                        <Sidebar collapsed={collapsed} />
                      </Layout.Sider>

                      {/* 右侧内容区 */}
                      <Layout style={{ marginLeft: collapsed ? 64 : 200 }}>
                        {/* 中央内容区 */}
                        <Content
                          style={{
                            background: 'var(--bb-bg-primary)',
                            padding: 24,
                            overflow: 'auto',
                            minHeight: 'calc(100vh - 64px)',
                          }}
                        >
                          <Routes>
                            <Route path="/" element={<Dashboard />} />

                            {/* 旧路由重定向 */}
                            <Route path="/data" element={<Navigate to="/market/realtime" replace />} />
                            <Route path="/market" element={<Navigate to="/market/realtime" replace />} />
                            <Route path="/strategy" element={<Navigate to="/strategy/library" replace />} />

                            {/* 新路由 */}
                            <Route path="/workspace" element={<Dashboard />} />
                            <Route path="/market" element={<DataManagement />} />
                            <Route path="/market/realtime" element={<MarketRealtime />} />
                            <Route path="/strategy/library" element={<StrategyManagement />} />
                            <Route path="/strategy/studio" element={<StrategyManagement />} />
                            <Route path="/trading" element={<Trading />} />
                            <Route path="/backtest" element={<Backtest />} />
                            <Route path="/portfolio" element={<Dashboard />} />
                            <Route path="/ai/generate" element={<Dashboard />} />
                            <Route path="/ai/pick" element={<Dashboard />} />
                            <Route path="/ai/analyze" element={<Dashboard />} />
                            <Route path="/risk" element={<Dashboard />} />
                            <Route path="/community" element={<Dashboard />} />
                            <Route path="/docs" element={<Dashboard />} />
                          </Routes>
                        </Content>
                      </Layout>
                    </Layout>
                  </Layout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </TradingModeProvider>
  );
}

export default App;
