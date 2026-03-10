# Quant-Trade System - 快速开始指南

> **5 分钟快速启动** | 从零到运行
> **版本**: v2.2.0 | **更新日期**: 2026-03-10

---

## 📋 前置要求

在开始之前，请确保您的系统已安装以下软件：

- **Python**: 3.11+ ([下载](https://www.python.org/))
- **Node.js**: 18+ ([下载](https://nodejs.org/))
- **Git**: ([下载](https://git-scm.com/))
- **Docker**: (可选，用于容器化部署) ([下载](https://www.docker.com/))

---

## 🚀 快速启动

### 方式一：Docker 启动（推荐）

这是最简单的方式，适合快速体验系统。

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/quant-trade-system.git
cd quant-trade-system

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，修改必要的配置

# 3. 启动所有服务
docker-compose up -d

# 4. 等待服务启动（约 30 秒）
docker-compose logs -f

# 5. 访问应用
# 前端: http://localhost:3000
# 后端: http://localhost:8000
# API 文档: http://localhost:8000/docs
# Grafana: http://localhost:3001
```

### 方式二：本地开发

适合需要自定义开发的场景。

#### 1. 启动数据库

```bash
# 启动 PostgreSQL 和 Redis
docker-compose up -d postgres redis
```

#### 2. 启动后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 文件

# 初始化数据库
python scripts/init_db.py

# 启动后端服务
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动前端

```bash
# 打开新终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start

# 自动打开浏览器 http://localhost:3000
```

---

## 📚 验证安装

### 检查后端 API

访问以下 URL 验证后端是否正常运行：

- **健康检查**: http://localhost:8000/health
- **API 文档**: http://localhost:8000/docs
- **Ping 检查**: http://localhost:8000/ping

预期返回：
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "app_name": "Quant-Trade System",
    "version": "1.0.0"
  }
}
```

### 检查前端

访问 http://localhost:3000，应该看到：

- ✅ 侧边栏菜单
- ✅ 仪表盘页面
- ✅ 资产统计卡片

---

## 🎯 下一步

安装完成后，您可以：

### 1. 获取实时行情
访问 http://localhost:3000/market/realtime，订阅实时股票行情。

### 2. 创建策略
访问 http://localhost:3000/strategy，创建您的第一个交易策略。

### 3. 运行回测
访问 http://localhost:3000/backtest，测试策略历史表现。
- 支持因子分析（IC、IC_IR、因子收益）
- 支持归因分析（配置效应、选股效应）
- 支持扩展指标（Sortino、Calmar、Alpha、Beta、VaR）

### 4. 管理投资组合
访问 http://localhost:3000/portfolio，管理您的投资组合。
- 组合持仓管理
- 风险度量（VaR、CVaR、集中度）
- 组合优化（均值方差、风险平价、最大夏普）

### 5. 模拟交易
访问 http://localhost:3000/trading，体验模拟交易。
- 订单管理
- 成交记录
- 交易日历

### 6. 阅读文档
- [系统架构](./SYSTEM_ARCHITECTURE.md)
- [API 文档](./API.md)
- [WebSocket 架构](../backend/docs/WEBSOCKET_ARCHITECTURE.md)

---

## 🛠️ 常见问题

### 问题 1: 端口被占用

**错误**: `Error: listen EADDRINUSE: address already in use :::8000`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000
# 或者
netstat -ano | findstr :8000

# 杀死进程
kill -9 <PID>
```

### 问题 2: 数据库连接失败

**错误**: `psycopg2.OperationalError: could not connect to server`

**解决**:
```bash
# 检查 PostgreSQL 是否运行
docker-compose ps postgres

# 查看日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### 问题 3: 前端无法连接后端

**错误**: `Network Error` 或 `ERR_CONNECTION_REFUSED`

**解决**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查 CORS 配置
# 确认 .env 中的 CORS_ORIGINS 包含前端地址
```

### 问题 4: 依赖安装失败

**错误**: `pip install` 或 `npm install` 失败

**解决**:
```bash
# Python: 使用国内镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Node: 使用国内镜像
npm config set registry https://registry.npmmirror.com
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看 [FAQ](./FAQ.md)
2. 搜索 [Issues](https://github.com/your-org/quant-trade-system/issues)
3. 加入社区讨论
4. 发送邮件至 support@quanttrade.example.com

---

## 🎉 开始使用

恭喜！您已经成功启动 Quant-Trade System v2.2.0。

现在可以：
- 📊 探索实时行情功能
- 🧮 创建您的第一个策略
- 📈 运行历史回测（支持因子分析和归因分析）
- 💼 管理投资组合
- 💹 开始模拟交易
- 🤖 体验 AI 增强功能

### 功能概览

| 功能模块 | 页面路由 | 状态 |
|----------|----------|:----:|
| 用户认证 | /login | ✅ |
| 仪表盘 | /dashboard | ✅ |
| 策略管理 | /strategy | ✅ |
| 策略回测 | /backtest | ✅ |
| 交易管理 | /trading | ✅ |
| 投资组合 | /portfolio | ✅ |
| 实时行情 | /market/realtime | ✅ |
| AI 实验室 | /ai-lab | ✅ |

**祝您交易愉快！** 🚀
