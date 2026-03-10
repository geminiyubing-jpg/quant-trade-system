# Quant-Trade System

> **专业级量化交易系统** | A 股市场智能投资解决方案
> **版本**: v2.2.0 | **更新日期**: 2026-03-10

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 项目简介

**Quant-Trade System** 是一个功能完整的量化交易系统，提供从数据获取、因子挖掘、策略回测到实盘交易的全流程支持。

### 核心功能

- 📊 **数据管理**: 支持 AkShare、Tushare 等多数据源，实时行情推送
- 🧮 **因子引擎**: 200+ 预置因子，自动挖掘和验证
- 📈 **策略回测**: 高性能历史回测，因子分析，归因分析
- 💹 **交易管理**: 模拟/实盘交易，成交记录，交易日历
- 💼 **投资组合**: 组合管理，风险度量，组合优化
- 🤖 **AI 增强**: 集成 GLM 等大模型进行因子优化
- 🎛️ **风险控制**: 实时监控，VaR/CVaR 计算，自动风控
- 🌐 **实时行情**: WebSocket 实时推送，自选股管理，价格预警

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React 18 + TS)                  │
│   Ant Design | ECharts | WebSocket | Redux Toolkit           │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP/WebSocket
┌─────────────────────────────▼───────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 认证服务  │ │ 数据服务  │ │ 策略服务  │ │ 交易服务  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 回测服务  │ │ 风控服务  │ │ 组合服务  │ │ AI 服务   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                       Data Layer                             │
│   PostgreSQL (63 tables) | Redis | TimescaleDB               │
└─────────────────────────────────────────────────────────────┘
```

### 已实现模块 (v2.2.0)

| 模块 | 数据库 | 后端 API | 前端页面 | 状态 |
|------|:------:|:--------:|:--------:|:----:|
| 用户认证 | ✅ | ✅ | ✅ | 完成 |
| 策略管理 | ✅ | ✅ | ✅ | 完成 |
| 策略回测 | ✅ | ✅ | ✅ | 完成 |
| 交易管理 | ✅ | ✅ | ✅ | 完成 |
| 投资组合 | ✅ | ✅ | ✅ | 完成 |
| 实时行情 | ✅ | ✅ | ✅ | 完成 |
| 风险控制 | ✅ | ✅ | 🔄 | 进行中 |
| AI 功能 | ✅ | ✅ | 🔄 | 进行中 |

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.11+
- **Node.js**: 18+
- **PostgreSQL**: 15+
- **Redis**: 7+

### 安装步骤

#### 1. 克隆仓库
```bash
git clone https://github.com/your-org/quant-trade-system.git
cd quant-trade-system
```

#### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入配置信息
```

#### 3. 启动数据库
```bash
docker-compose up -d postgres redis
```

#### 4. 初始化数据库
```bash
cd backend
python scripts/init_db.py
```

#### 5. 启动后端服务
```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload
```

#### 6. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

#### 7. 访问应用
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 📖 使用指南

### 数据获取
```python
from backend.src.services.data import DataManager

# 获取股票数据
manager = DataManager()
data = manager.get_stock_data(
    symbol="000001.SZ",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

### 因子计算
```python
from backend.src.services.factor import FactorEngine

# 计算动量因子
engine = FactorEngine()
momentum = engine.calculate_factor(
    factor_name="momentum_20",
    data=data
)
```

### 策略回测
```python
from backend.src.services.backtest import BacktestEngine

# 运行回测
backtest = BacktestEngine()
result = backtest.run(
    strategy="MomentumStrategy",
    start_date="2020-01-01",
    end_date="2024-12-31",
    initial_capital=1000000
)
```

---

## 🏗️ 项目结构

```
quant-trade-system/
├── backend/              # 后端服务（FastAPI）
├── frontend/             # 前端应用（React）
├── docs/                 # 项目文档
├── scripts/              # 工具脚本
├── tests/                # 集成测试
├── database/             # 数据库脚本
└── .github/workflows/    # CI/CD 配置
```

详细结构请参考 [CLAUDE.md](./CLAUDE.md)

---

## 🧪 测试

### 后端测试
```bash
cd backend
pytest tests/ -v --cov=src
```

### 前端测试
```bash
cd frontend
npm test
```

### 集成测试
```bash
pytest tests/integration/ -v
```

---

## 📚 文档

- [快速开始指南](./docs/GETTING_STARTED.md) - 5 分钟快速启动
- [用户使用指南](./docs/USER_GUIDE.md) - 详细使用说明
- [系统架构](./docs/SYSTEM_ARCHITECTURE.md) - 技术架构详解
- [API 文档](./docs/API.md) - RESTful API 接口文档
- [WebSocket 架构](./backend/docs/WEBSOCKET_ARCHITECTURE.md) - 实时数据推送
- [数据库设计](./docs/DATABASE.md) - 数据库表结构
- [Bloomberg 主题指南](./docs/BLOOMBERG_THEME_GUIDE.md) - UI 主题定制
- [PostgreSQL 配置](./docs/POSTGRESQL_SETUP.md) - 数据库安装配置
- [项目状态](./PROJECT_STATUS.md) - 当前开发进度

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献流程
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- Python: 遵循 PEP 8
- TypeScript: Airbnb Style Guide
- 提交信息: 遵循 Conventional Commits

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

**QuantDev Team** - 量化开发团队

- **架构师**: 系统设计和技术选型
- **后端工程师**: API 开发和数据处理
- **前端工程师**: UI 开发和数据可视化
- **数据工程师**: 数据获取和质量监控
- **AI/ML 工程师**: 因子挖掘和模型优化
- **测试工程师**: 测试框架和质量保证

---

## 📮 联系我们

- **Issues**: [GitHub Issues](https://github.com/your-org/quant-trade-system/issues)
- **Email**: support@quanttrade.example.com
- **文档**: [Wiki](https://github.com/your-org/quant-trade-system/wiki)

---

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代高性能 Python Web 框架
- [React](https://react.dev/) - 用于构建用户界面的 JavaScript 库
- [Ant Design](https://ant.design/) - 企业级 UI 设计语言和 React 组件库
- [AkShare](https://akshare.akfamily.xyz/) - 开源财经数据接口库
- [PostgreSQL](https://www.postgresql.org/) - 世界上最先进的开源关系数据库
- [ECharts](https://echarts.apache.org/) - 强大的可视化图表库

---

## 📊 项目统计

- **数据库表**: 63 张
- **API 端点**: 15+ 模块
- **前端页面**: 12+ 页面
- **测试覆盖**: 核心功能已测试

---

**⚠️ 免责声明**: 本系统仅供学习和研究使用，不构成任何投资建议。使用本系统进行实盘交易的所有风险由使用者自行承担。

---

🚀 **让我们一起构建专业的量化交易系统！**

**最后更新**: 2026-03-10 | **维护者**: QuantDev Team
