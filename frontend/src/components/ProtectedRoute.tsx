/**
 * ==============================================
 * 路由守卫组件
 * ==============================================
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useSelector } from 'react-redux';
import type { RootState } from '../store';
import { selectIsAuthenticated, selectAuthLoading } from '../store/slices/authSlice';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const isAuthenticated = useSelector((state: RootState) => selectIsAuthenticated(state));
  const loading = useSelector((state: RootState) => selectAuthLoading(state));
  const location = useLocation();

  // 显示加载状态
  if (loading) {
    return (
      <div
        style={{
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '16px',
        }}
      >
        <Spin size="large" />
        <span style={{ color: '#666' }}>加载中...</span>
      </div>
    );
  }

  // 未登录，跳转到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 已登录，渲染子组件
  return <>{children}</>;
};

export default ProtectedRoute;
