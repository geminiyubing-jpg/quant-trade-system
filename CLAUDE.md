# Quant-Trade System - Claude Code 配置

> **版本**: v1.0.0
> **创建日期**: 2026-03-08
> **团队**: QuantDev

---

## 项目概述

**Quant-Trade System** 是一个专业级量化交易系统，专注于 A 股市场的策略研发和实盘交易。

### 技术栈
- **后端**: Python 3.11+ / FastAPI
- **前端**: React 18 + TypeScript + Ant Design
- **数据库**: PostgreSQL 15+
- **缓存**: Redis 7+
- **消息队列**: Celery + RabbitMQ

### 项目定位
- 📊 数据获取和管理（AkShare、Tushare）
- 🧮 因子计算和验证
- 📈 策略回测和优化
- 💹 实盘交易执行
- 🤖 AI/ML 模型集成

---

## 开发规范

### 代码风格
- **Python**: 遵循 PEP 8，使用 4 空格缩进，最大行宽 100 字符
- **TypeScript**: Airbnb Style Guide，使用 2 空格缩进，必须使用分号
- **注释**: 复杂逻辑必须添加中文注释

### Git 提交规范
```
<类型>(<范围>): <简短描述>

<详细描述>

<关联 Issue>
```

**类型**:
- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具

### 分支策略
- `main`: 生产环境
- `develop`: 开发环境
- `feature/xxx`: 功能分支
- `hotfix/xxx`: 紧急修复
- `release/xxx`: 发布分支

---

## 项目结构

```
quant-trade-system/
├── backend/                 # 后端服务
│   ├── src/
│   │   ├── core/           # 核心模块（配置、日志、安全）
│   │   ├── models/         # 数据模型
│   │   ├── api/            # API 路由
│   │   ├── services/       # 业务逻辑
│   │   │   ├── data/       # 数据服务
│   │   │   ├── strategy/   # 策略服务
│   │   │   ├── backtest/   # 回测服务
│   │   │   └── trading/    # 交易服务
│   │   └── repositories/   # 数据访问层
│   ├── tests/              # 测试
│   └── config/             # 配置文件
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/    # 组件
│   │   ├── pages/         # 页面
│   │   ├── services/      # API 服务
│   │   ├── hooks/         # 自定义 Hooks
│   │   ├── utils/         # 工具函数
│   │   └── types/         # TypeScript 类型
│   ├── public/            # 静态资源
│   └── tests/             # 测试
│
├── docs/                  # 文档
├── scripts/               # 脚本工具
├── tests/                 # 集成测试
├── database/              # 数据库脚本
└── .github/workflows/     # CI/CD
```

---

## 开发指南

### 后端开发
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest tests/ -v --cov

# 代码检查
pylint src/
mypy src/
```

### 前端开发
```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 运行测试
npm test

# 构建生产版本
npm run build
```

### 数据库
```bash
# 启动 PostgreSQL
docker-compose up -d postgres

# 运行迁移
python scripts/migrate.py

# 初始化数据
python scripts/init_data.py
```

---

## 代码质量要求

### 测试覆盖率
- 单元测试覆盖率: ≥ 80%
- 关键路径覆盖率: 100%
- 所有新功能必须有测试

### 代码审查
- 所有代码合并前必须经过审查
- 审查重点: 功能正确性、代码质量、性能、安全性
- 至少 1 人审查通过才能合并

### 性能要求
- API 响应时间: < 200ms (P95)
- 因子计算: < 1s (1000 股)
- 回测速度: > 1000 数据点/秒

---

## 团队协作

### 角色
- **架构师**: 系统设计、技术选型、核心模块
- **后端工程师**: FastAPI 开发、数据处理、策略实现
- **前端工程师**: React 组件、数据可视化
- **数据工程师**: 数据获取、清洗、质量监控
- **AI/ML 工程师**: 因子挖掘、模型训练
- **测试工程师**: 测试框架、自动化测试

### 工作流程
1. 需求分析
2. 技术设计
3. 创建功能分支
4. 编写代码 + 测试
5. 代码审查
6. 合并到 develop
7. 集成测试
8. 部署到 staging
9. 用户验收
10. 合并到 main + 部署生产

---

## 重要提醒

### 安全
- ⚠️ 严禁将 API Key、密码等敏感信息提交到 Git
- ⚠️ 使用环境变量管理敏感配置
- ⚠️ 生产数据必须有备份

### 交易安全
- ⚠️ 所有实盘交易操作必须经过严格测试
- ⚠️ 风控模块必须始终启用
- ⚠️ 异常情况必须自动止损

### 数据安全
- ⚠️ 用户数据加密存储
- ⚠️ 定期备份重要数据
- ⚠️ 遵守数据隐私法规

---

## 常用命令

### Git
```bash
# 创建功能分支
git checkout -b feature/data-alpha-mining

# 提交代码
git add .
git commit -m "feat(data): 添加 Alpha 因子挖掘模块"

# 推送到远程
git push origin feature/data-alpha-mining
```

### Docker
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 文档资源

- [团队规范](./quant-team.md)
- [API 文档](./docs/API.md)
- [数据库设计](./docs/DATABASE.md)
- [部署指南](./docs/DEPLOYMENT.md)

---

**维护者**: QuantDev Team
**最后更新**: 2026-03-08
