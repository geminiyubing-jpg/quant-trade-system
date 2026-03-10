import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import './index.css';
import './styles/bloomberg-theme.css';
import './styles/bloomberg-components.css';
import './styles/bloomberg-enhanced.css';
import './styles/bloomberg-animations.css';
import './styles/light-theme-enhanced.css';
import './styles/bloomberg-enhanced.css';
import './styles/market-colors-enhanced.css';
import './i18n/config'; // 引入 i18n 配置
import App from './App';
import store from './store';

// 从 localStorage 读取保存的语言
const savedLanguage = localStorage.getItem('language') || 'zh_CN';

// 设置 dayjs 语言
dayjs.locale(savedLanguage === 'zh_CN' ? 'zh-cn' : 'en');

// Ant Design 国际化配置
const antdLocale = savedLanguage === 'zh_CN' ? zhCN : enUS;

// Ant Design 彭博深色主题配置
const antdTheme = {
  algorithm: theme.darkAlgorithm, // 使用深色算法
  token: {
    // 主色调 - 彭博橙
    colorPrimary: '#FF6B00',
    colorSuccess: '#00D26A',
    colorWarning: '#FFA500',
    colorError: '#FF4D4D',
    colorInfo: '#58A6FF',

    // 背景色 - 彭博深色
    colorBgBase: '#000000',
    colorBgContainer: '#0D1117',
    colorBgElevated: '#21262D',
    colorBgLayout: '#000000',

    // 边框色
    colorBorder: '#30363D',
    colorBorderSecondary: '#21262D',

    // 文字色
    colorText: '#E6EDF3',
    colorTextSecondary: '#8B949E',
    colorTextTertiary: '#6E7681',
    colorTextQuaternary: '#484F58',

    // 圆角 - 彭博风格（较小）
    borderRadius: 4,

    // 字体
    fontFamily: "'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace",
    fontSize: 13,
  },
  components: {
    Layout: {
      headerBg: '#0D1117',
      siderBg: '#0D1117',
    },
    Menu: {
      darkItemBg: '#0D1117',
      darkSubMenuItemBg: '#0D1117',
      darkItemSelectedBg: '#1C2128',
      darkItemHoverBg: '#1C2128',
      darkItemColor: '#8B949E',
      darkItemSelectedColor: '#FF6B00',
      darkItemHoverColor: '#E6EDF3',
    },
    Input: {
      colorBgContainer: '#0D1117',
      colorBorder: '#30363D',
      colorText: '#E6EDF3',
      colorTextPlaceholder: '#6E7681',
      hoverBorderColor: '#FF6B00',
      activeBorderColor: '#FF6B00',
    },
    Button: {
      defaultBg: '#21262D',
      defaultColor: '#E6EDF3',
      defaultBorderColor: '#30363D',
      defaultHoverBg: '#1C2128',
      defaultHoverColor: '#FF6B00',
      defaultHoverBorderColor: '#FF6B00',
    },
    Table: {
      headerBg: '#0D1117',
      headerColor: '#8B949E',
      rowHoverBg: '#1C2128',
      borderColor: '#30363D',
    },
    Card: {
      colorBgContainer: '#0D1117',
      borderColor: '#30363D',
    },
    Modal: {
      contentBg: '#0D1117',
      headerBg: '#161B22',
    },
    Select: {
      colorBgContainer: '#0D1117',
      colorBgElevated: '#21262D',
      optionSelectedBg: '#1C2128',
    },
    Tag: {
      defaultBg: 'rgba(255, 107, 0, 0.15)',
      defaultColor: '#FF6B00',
    },
  },
};

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <ConfigProvider
        locale={antdLocale}
        theme={antdTheme}
      >
        <App />
      </ConfigProvider>
    </Provider>
  </React.StrictMode>
);
