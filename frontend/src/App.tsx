import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import { TradingModeProvider } from './contexts/TradingModeContext';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Dashboard from './pages/Dashboard';
import DataManagement from './pages/DataManagement';
import StrategyManagement from './pages/StrategyManagement';
import Backtest from './pages/Backtest';
import Trading from './pages/Trading';
import './App.css';

const { Content } = Layout;

function App() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <TradingModeProvider>
      <BrowserRouter>
        <Layout style={{ minHeight: '100vh' }}>
          {/* 顶部功能栏 - 贯通整个页面 */}
          <Layout.Header style={{
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
          }}>
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
              <Content style={{
                background: 'var(--bb-bg-primary)',
                padding: 24,
                overflow: 'auto',
                minHeight: 'calc(100vh - 64px)',
              }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />

                  {/* 旧路由重定向 */}
                  <Route path="/data" element={<Navigate to="/market" replace />} />
                  <Route path="/strategy" element={<Navigate to="/strategy/library" replace />} />
                  <Route path="/trading" element={<Trading />} />

                  {/* 新路由 */}
                  <Route path="/workspace" element={<Dashboard />} />
                  <Route path="/market" element={<DataManagement />} />
                  <Route path="/strategy/library" element={<StrategyManagement />} />
                  <Route path="/strategy/studio" element={<StrategyManagement />} />
                  <Route path="/backtest" element={<Backtest />} />
                  <Route path="/portfolio" element={<Dashboard />} />
                  <Route path="/ai/generate" element={<Dashboard />} />
                  <Route path="/ai/pick" element={<Dashboard />} />
                  <Route path="/ai/analyze" element={<Dashboard />} />
                  <Route path="/risk" element={<Dashboard />} />
                  <Route path="/data" element={<DataManagement />} />
                  <Route path="/community" element={<Dashboard />} />
                  <Route path="/docs" element={<Dashboard />} />
                </Routes>
              </Content>
            </Layout>
          </Layout>
        </Layout>
      </BrowserRouter>
    </TradingModeProvider>
  );
}

export default App;
