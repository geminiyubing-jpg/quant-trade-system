import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import DataManagement from './pages/DataManagement';
import StrategyManagement from './pages/StrategyManagement';
import Backtest from './pages/Backtest';
import Trading from './pages/Trading';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <BrowserRouter>
      <Layout style={{ minHeight: '100vh' }}>
        <Sidebar />
        <Layout>
          <Content style={{ padding: '24px', background: '#f0f2f5' }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/data" element={<DataManagement />} />
              <Route path="/strategy" element={<StrategyManagement />} />
              <Route path="/backtest" element={<Backtest />} />
              <Route path="/trading" element={<Trading />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
