import { useState, useEffect, useMemo, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, ConfigProvider, theme, Drawer, Spin } from 'antd';
import { useTranslation } from 'react-i18next';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import { TradingModeProvider } from './contexts/TradingModeContext';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ProtectedRoute from './components/ProtectedRoute';

// ==========================================
// 路由懒加载 - 优化首屏加载性能
// ==========================================

// 核心页面 - 高优先级
const Login = lazy(() => import('./pages/Login'));
const Dashboard = lazy(() => import('./pages/Dashboard'));

// 数据相关
const DataManagement = lazy(() => import('./pages/DataManagement'));

// 策略相关
const StrategyManagement = lazy(() => import('./pages/StrategyManagement'));
const StrategyStudio = lazy(() => import('./pages/StrategyStudio'));
const Backtest = lazy(() => import('./pages/Backtest'));

// 交易相关
const Trading = lazy(() => import('./pages/Trading'));
const Portfolio = lazy(() => import('./pages/Portfolio'));
const RiskManagement = lazy(() => import('./pages/RiskManagement'));

// 行情相关
const MarketRealtime = lazy(() => import('./pages/MarketRealtime'));
const SectorAnalysis = lazy(() => import('./pages/SectorAnalysis'));

// AI 相关
const AILab = lazy(() => import('./pages/AILab'));

// 其他
const Docs = lazy(() => import('./pages/Docs'));

// ==========================================
// 加载组件
// ==========================================

const PageLoader = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    minHeight: 400,
  }}>
    <Spin size="large" tip="加载中..." />
  </div>
);

import './App.css';
import './styles/font-switch.css';

const { Content } = Layout;

function AppContent() {
  const { i18n } = useTranslation();
  const { theme: appTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // 检测移动端
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (!mobile) {
        setMobileMenuOpen(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

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

  // Ant Design 主题配置（动态字体 + 动态主题）
  const antdTheme = {
    algorithm: appTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      fontFamily: currentFont,
      fontSize: 13,
    },
  };

  // 根据当前语言动态设置 Ant Design locale
  const antdLocale = i18n.language === 'zh_CN' ? zhCN : enUS;

  // 计算侧边栏宽度
  const sidebarWidth = isMobile ? 0 : (collapsed ? 64 : 200);

  return (
    <TradingModeProvider>
      <ConfigProvider locale={antdLocale} theme={antdTheme}>
        <BrowserRouter>
          <Routes>
            {/* 登录页面 - 无需认证 */}
            <Route
              path="/login"
              element={
                <Suspense fallback={<PageLoader />}>
                  <Login />
                </Suspense>
              }
            />

            {/* 主应用 - 需要认证 */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout style={{ minHeight: '100vh' }} className={`app-layout ${isMobile ? 'mobile' : 'desktop'}`}>
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
                      <TopBar
                        isMobile={isMobile}
                        onMenuClick={() => setMobileMenuOpen(true)}
                      />
                    </Layout.Header>

                    {/* 主体区域 - 包含侧边栏和内容 */}
                    <Layout style={{ marginTop: 64 }}>
                      {/* 移动端侧边栏 - 使用 Drawer */}
                      {isMobile && (
                        <Drawer
                          placement="left"
                          open={mobileMenuOpen}
                          onClose={() => setMobileMenuOpen(false)}
                          width={250}
                          className="mobile-menu-drawer"
                          styles={{
                            body: { padding: 0 },
                            header: { display: 'none' },
                          }}
                        >
                          <div style={{
                            height: '100%',
                            background: 'var(--bb-bg-secondary)',
                          }}>
                            <Sidebar collapsed={false} />
                          </div>
                        </Drawer>
                      )}

                      {/* 桌面端侧边栏 */}
                      {!isMobile && (
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
                      )}

                      {/* 右侧内容区 */}
                      <Layout style={{ marginLeft: sidebarWidth, transition: 'margin-left 0.2s' }}>
                        {/* 中央内容区 */}
                        <Content
                          style={{
                            background: 'var(--bb-bg-primary)',
                            padding: isMobile ? 12 : 24,
                            overflow: 'auto',
                            minHeight: 'calc(100vh - 64px)',
                          }}
                          className="main-content"
                        >
                          <Suspense fallback={<PageLoader />}>
                            <Routes>
                              <Route path="/" element={<Dashboard />} />

                              {/* 旧路由重定向 */}
                              <Route path="/data" element={<Navigate to="/data/management" replace />} />
                              <Route path="/market" element={<Navigate to="/market/realtime" replace />} />
                              <Route path="/strategy" element={<Navigate to="/strategy/library" replace />} />

                              {/* 新路由 */}
                              <Route path="/workspace" element={<Dashboard />} />
                              <Route path="/data/management" element={<DataManagement />} />
                              <Route path="/data" element={<Navigate to="/data/management" replace />} />
                              <Route path="/market/realtime" element={<MarketRealtime />} />
                              <Route path="/market/sectors" element={<SectorAnalysis />} />
                              <Route path="/strategy/library" element={<StrategyManagement />} />
                              <Route path="/strategy/studio" element={<StrategyStudio />} />
                              <Route path="/trading" element={<Trading />} />
                              <Route path="/backtest" element={<Backtest />} />
                              <Route path="/portfolio" element={<Portfolio />} />
                              <Route path="/ai/generate" element={<AILab />} />
                              <Route path="/ai/pick" element={<AILab />} />
                              <Route path="/ai/analyze" element={<AILab />} />
                              <Route path="/risk" element={<RiskManagement />} />
                              <Route path="/community" element={<Dashboard />} />
                              <Route path="/docs" element={<Docs />} />
                            </Routes>
                          </Suspense>
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

// 主 App 组件 - 包裹 ThemeProvider
function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
