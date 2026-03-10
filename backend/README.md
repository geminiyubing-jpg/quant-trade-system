# 🚀 QuantAI Ecosystem - FastAPI 后端

> **版本**: v2.2.0
> **Python**: 3.11+
> **框架**: FastAPI 0.109.0
> **更新日期**: 2026-03-10

---

## 📋 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填写实际配置
vim .env
```

### 3. 初始化数据库

```bash
# 方式 1：使用初始化脚本（推荐）
psql -U quant_trio -d quant_trio -f database/init_postgres.sql

# 方式 2：使用 Alembic 迁移
alembic upgrade head
```

### 4. 启动开发服务器

```bash
# 方式 1：使用 Python
python -m src.main

# 方式 2：使用 Uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 方式 3：使用脚本
./scripts/dev.sh
```

### 5. 访问 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

---

## 📁 项目结构

```
backend/
├── src/
│   ├── core/               # 核心模块
│   │   ├── config.py       # 配置管理
│   │   └── database.py     # 数据库连接
│   ├── models/             # SQLAlchemy 模型
│   ├── api/                # API 路由
│   ├── services/           # 业务逻辑
│   ├── data/               # 数据处理
│   └── main.py             # FastAPI 主应用
├── tests/                  # 测试
├── database/               # 数据库脚本
├── scripts/                # 脚本工具
├── logs/                   # 日志文件
├── .env                    # 环境变量（不提交到 Git）
└── requirements.txt        # Python 依赖
```

---

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

---

## 📊 API 端点

### 基础端点

| 端点 | 方法 | 描述 |
|:---|:---:|:---|
| `/` | GET | 根路径 |
| `/health` | GET | 健康检查 |
| `/config` | GET | 应用配置（仅开发环境） |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | ReDoc |

### 业务端点

| 模块 | 前缀 | 描述 | 状态 |
|:---|:---|:---|:---:|
| 认证 | `/api/v1/auth` | JWT 认证、登录登出 | ✅ |
| 用户 | `/api/v1/users` | 用户管理 | ✅ |
| 策略 | `/api/v1/strategies` | 策略版本管理、配置管理 | ✅ |
| 回测 | `/api/v1/backtest` | 回测执行、因子分析、归因分析 | ✅ |
| 交易 | `/api/v1/trading` | 交易管理、订单执行 | ✅ |
| 成交 | `/api/v1/fills` | 成交记录管理 | ✅ |
| 交易日历 | `/api/v1/trading-calendar` | 交易日历查询 | ✅ |
| 交易统计 | `/api/v1/trade-stats` | 每日交易统计 | ✅ |
| 组合 | `/api/v1/portfolios` | 投资组合管理、风险分析 | ✅ |
| 风控 | `/api/v1/risk` | 风险控制、止损止盈 | ✅ |
| 数据 | `/api/v1/data` | 市场数据获取 | ✅ |
| 数据 ETL | `/api/v1/data-etl` | 数据清洗和导入 | ✅ |
| 数据质量 | `/api/v1/data-quality` | 数据质量监控 | ✅ |
| 自选股 | `/api/v1/watchlist` | 自选股管理 | ✅ |
| 预警 | `/api/v1/alerts` | 价格预警 | ✅ |
| WebSocket | `/api/v1/ws` | 实时行情推送 | ✅ |
| AI | `/api/v1/ai` | AI 功能集成 | ✅ |
| 策略进化 | `/api/v1/evolution` | 策略自动进化 | ✅ |

---

## 🔧 开发工具

### 代码格式化

```bash
# 使用 Black 格式化代码
black src/ tests/

# 使用 isort 排序 import
isort src/ tests/
```

### 代码检查

```bash
# 使用 Pylint 检查代码
pylint src/

# 使用 MyPy 进行类型检查
mypy src/
```

---

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t quantai-backend:latest .

# 运行容器
docker run -d \
  --name quantai-backend \
  -p 8000:8000 \
  --env-file .env \
  quantai-backend:latest
```

---

## 📝 更新日志

### v2.2.0 (2026-03-10)

#### ✅ 新增
- **策略版本管理**: 版本控制、配置管理、审计日志
- **回测分析增强**: 因子分析、归因分析、扩展指标
- **交易管理增强**: 成交记录、交易日历、交易统计
- **投资组合管理**: 组合管理、风险度量、组合优化
- **实时行情**: WebSocket 实时推送、自选股管理、价格预警
- **数据服务**: 数据 ETL、数据质量监控

#### 🐛 修复
- 修复 WebSocket 订阅时序问题
- 修复菜单导航问题
- 修复 CORS 配置问题

### v2.0.0 (2026-03-08)

#### ✅ 新增
- FastAPI 框架搭建
- 数据库连接层（SQLAlchemy 2.0）
- 配置管理（Pydantic Settings）
- 日志系统（Loguru）
- 健康检查端点
- 全局异常处理
- 请求日志中间件

#### 🔴 P0 修复
- execution_mode 强制隔离（架构红线）
- TimescaleDB 时序数据分区

#### 🟠 P1 优化
- 风控字段（止损/止盈/滑点）
- 审计日志（created_by/updated_by/version）

---

## 📁 项目结构

```
backend/
├── src/
│   ├── core/               # 核心模块
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库连接
│   │   └── security.py     # 安全认证
│   ├── models/             # SQLAlchemy 模型
│   ├── api/v1/endpoints/   # API 路由
│   ├── services/           # 业务逻辑
│   │   ├── data/           # 数据服务
│   │   ├── strategy/       # 策略服务
│   │   ├── backtest/       # 回测服务
│   │   └── trading/        # 交易服务
│   ├── repositories/       # 数据访问层
│   ├── schemas/            # Pydantic 模型
│   └── main.py             # FastAPI 主应用
├── tests/                  # 测试
├── database/               # 数据库脚本
├── scripts/                # 脚本工具
├── logs/                   # 日志文件
├── .env                    # 环境变量（不提交到 Git）
└── requirements.txt        # Python 依赖
```

---

**维护者**: QuantDev Team
**最后更新**: 2026-03-10
