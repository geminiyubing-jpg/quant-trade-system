# quant-trade-system 整体架构模式

> **架构类型**: 左侧导航 + 顶部功能栏 + 中央内容区
> **设计风格**: 彭博终端主题
> **国际化**: 支持中英文切换

---

## 📐 布局架构

```
+----------------+------------------------------------------+
|  Logo / 菜单   |  顶部栏 (Top Bar)                        |
|  (可折叠)      |  [语言切换] [搜索] [通知] [用户头像/设置] |
+----------------+------------------------------------------+
|                |                                          |
|  左侧导航栏    |           中央内容区域                   |
|  (Sidebar)     |         (Main Content Area)              |
|                |                                          |
| - 仪表盘       |  - 实时行情展示 / 策略回测 / 交易执行    |
| - 数据管理     |  - 数据图表 / K线图 / 深度数据          |
| - 策略管理     |  - 输入框 / 控制面板 / 操作按钮           |
| - 回测         |                                          |
| - 交易         |                                          |
| - 风险控制     |                                          |
| - 设置         |                                          |
+----------------+------------------------------------------+
```

---

## 🎨 设计规范

### 1. 左侧导航栏 (Sidebar)

#### 功能
- ✅ Logo 和系统名称
- ✅ 导航菜单
- ✅ 折叠/展开功能
- ✅ 当前页面高亮

#### 彭博主题样式
```css
.sidebar {
  background: var(--bb-bg-secondary);
  border-right: 1px solid var(--bb-border);
  width: 200px; /* 展开时 */
}

.sidebar.collapsed {
  width: 64px; /* 折叠时 */
}
```

#### 组件结构
```tsx
<Sidebar>
  {/* Logo 区 */}
  <div className="sidebar-logo">
    <h2>{t('app.name')}</h2>
  </div>

  {/* 导航菜单 */}
  <Menu items={menuItems} />

  {/* 折叠按钮 */}
  <Button onClick={toggleCollapse}>
    {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
  </Button>
</Sidebar>
```

---

### 2. 顶部功能栏 (Top Bar)

#### 功能模块
1. **左侧区**
   - 面包屑导航（可选）
   - 当前页面标题

2. **中央区**
   - 搜索框（全局搜索）
   - 快捷操作按钮

3. **右侧区**
   - 语言切换器
   - 通知图标
   - 用户头像/设置

#### 彭博主题样式
```css
.top-bar {
  background: var(--bb-bg-secondary);
  border-bottom: 1px solid var(--bb-border);
  padding: 0 24px;
  height: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
```

#### 组件结构
```tsx
<Header>
  {/* 左侧：页面标题 */}
  <div className="top-bar-left">
    <h2>{pageTitle}</h2>
  </div>

  {/* 中央：搜索框 */}
  <div className="top-bar-center">
    <Input.Search
      placeholder={t('common.search')}
      style={{ width: 300 }}
    />
  </div>

  {/* 右侧：功能按钮 */}
  <div className="top-bar-right">
    <LanguageSwitcher />
    <NotificationIcon />
    <UserAvatar />
  </div>
</Header>
```

---

### 3. 中央内容区 (Main Content Area)

#### 布局特点
- **最大化内容展示区域**
- **数据优先设计**
- **实时更新支持**
- **彭博终端风格**

#### 彭博主题样式
```css
.main-content {
  background: var(--bb-bg-primary); /* 纯黑背景 */
  padding: 24px;
  overflow-y: auto;
  height: calc(100vh - 64px); /* 减去顶部栏高度 */
}
```

#### 内容类型

##### 1. 仪表盘 (Dashboard)
```
+------------------------------------------+
|  实时行情卡片                              |
|  [总资产] [今日收益] [持仓数] [运行策略]    |
+------------------------------------------+
|  持仓列表表格                              |
|  [代码] [价格] [涨跌幅] [成交量] ...        |
+------------------------------------------+
|  策略表现图表                              |
|  [收益率曲线]                             |
+------------------------------------------+
```

##### 2. 数据管理 (Data Management)
```
+------------------------------------------+
|  数据源选择器                              |
|  [AkShare] [Tushare] [Wind] [自定义]       |
+------------------------------------------+
|  数据预览表格                              |
|  [股票代码] [名称] [最新价] [涨跌幅]       |
+------------------------------------------+
|  数据下载按钮                              |
+------------------------------------------+
```

##### 3. 策略回测 (Backtest)
```
+------------------------------------------+
|  策略参数配置                              |
|  [策略类型] [时间范围] [初始资金]          |
+------------------------------------------+
|  回测按钮                                  |
|  [运行回测] [保存配置] [导出报告]         |
+------------------------------------------+
|  回测结果图表                              |
|  [净值曲线] [回撤图] [收益分布]           |
+------------------------------------------+
```

---

## 📱 响应式设计

### 桌面端 (≥ 1024px)
```
[侧边栏展开] [顶部栏] [中央内容区]
    200px      64px       自适应
```

### 平板端 (768px - 1023px)
```
[侧边栏折叠] [顶部栏] [中央内容区]
    64px       64px       自适应
```

### 移动端 (< 768px)
```
[汉堡菜单] [顶部栏]
[中央内容区（全屏）]
```

---

## 🎯 组件层次结构

```
App
├── Sidebar (左侧导航)
│   ├── Logo
│   ├── Menu
│   └── CollapseButton
│
├── Header (顶部栏)
│   ├── PageTitle
│   ├── SearchBar
│   ├── LanguageSwitcher
│   ├── NotificationBell
│   └── UserDropdown
│
└── MainContent (中央内容区)
    ├── Dashboard
    ├── DataManagement
    ├── StrategyManagement
    ├── Backtest
    ├── Trading
    └── RiskControl
```

---

## ⚡ 性能优化

### 1. 组件懒加载
```typescript
const Dashboard = lazy(() => import('./pages/Dashboard'));
const DataManagement = lazy(() => import('./pages/DataManagement'));
```

### 2. 虚拟滚动（长列表）
```tsx
import { List } from 'react-virtualized';

<List
  width={300}
  height={600}
  rowCount={data.length}
  rowHeight={50}
  rowRenderer={({ index, key, style }) => (
    <div key={key} style={style}>
      {data[index]}
    </div>
  )}
/>
```

### 3. 防抖搜索
```typescript
import { debounce } from 'lodash';

const debouncedSearch = debounce((value: string) => {
  // 执行搜索
}, 300);
```

---

## 🔧 技术实现

### 布局配置
```typescript
import { Layout } from 'antd';
const { Header, Sider, Content } = Layout;

function App() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
      >
        <Sidebar collapsed={collapsed} />
      </Sider>

      <Layout>
        <Header style={{ padding: 0 }}>
          <TopBar />
        </Header>

        <Content style={{ background: 'var(--bb-bg-primary)' }}>
          <Routes>
            {/* 路由配置 */}
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}
```

---

## 📋 待实现功能

### 短期目标
- [ ] 完善顶部栏搜索功能
- [ ] 添加通知图标和下拉菜单
- [ ] 实现侧边栏折叠动画
- [ ] 优化移动端布局

### 中期目标
- [ ] 添加快捷键支持
- [ ] 实现全局搜索
- [ ] 添加多标签页支持
- [ ] 优化数据加载性能

---

**架构设计师**: 角色 B (金融系统架构师)
**前端开发**: 角色 C (全栈开发工程师)
**版本**: v1.0.0
**最后更新**: 2026-03-08
