# PostgreSQL 数据库配置指南

> **版本**: v1.0.0
> **数据库**: PostgreSQL 15+
> **项目**: quant-trade-system
> **团队**: Quant Core Team

---

## 📋 数据库选型

### 为什么选择 PostgreSQL？

✅ **高精度数值计算**
- NUMERIC 类型确保金融数据精度
- 避免浮点数误差
- 符合 Quant Core Team 的精度第一原则

✅ **强大的查询能力**
- 复杂的 SQL 查询
- 窗口函数（用于时序数据分析）
- 全文搜索（pg_trgm）

✅ **时序数据支持**
- TimescaleDB 扩展（PostgreSQL 时序数据库）
- 高效的时间范围查询
- 自动分区

✅ **ACID 事务**
- 数据一致性保证
- 并发安全
- 原子性操作

✅ **JSON 支持**
- 灵活存储策略参数
- 复杂查询
- 索引支持

---

## 🚀 快速开始

### 1. 启动 PostgreSQL

```bash
cd /Users/yubing/quant-trade-system

# 使用 Docker Compose 启动
docker-compose up -d postgres
```

### 2. 初始化数据库

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行初始化脚本
python database/scripts/init_db.py
```

### 3. 测试连接

```bash
# 测试数据库连接
python database/scripts/test_db.py
```

---

## 📊 数据库架构

### 核心表结构

```
PostgreSQL Database: quant_trade
│
├── 用户和认证
│   ├── users (用户表)
│   └── roles (角色表)
│
├── 市场数据
│   ├── stocks (股票基本信息)
│   └── stock_prices (实时行情)
│
├── 策略管理
│   ├── strategies (策略表)
│   └── backtests (回测表)
│
├── 交易管理
│   ├── orders (订单表)
│   └── positions (持仓表)
│
├── 风险管理
│   └── risk_alerts (风险告警表)
│
└── 系统配置
    └── system_config (系统配置表)
```

---

## 🔧 数据类型使用规范

### 金融数据必须使用 NUMERIC

**✅ 正确示例**:
```python
# 使用 NUMERIC 确保精度
price_close: NUMERIC(20, 8)  # 总共20位，小数点后8位
initial_capital: NUMERIC(30, 8)  # 总共30位，小数点后8位
```

**❌ 错误示例**:
```python
# 禁止使用 FLOAT 或 DOUBLE
price_close: Float  # ❌ 会产生精度误差
```

### 金额、价格、数量数据类型

```sql
-- 价格（小数点后8位）
price NUMERIC(20, 8)

-- 金额（支持更大的数字）
amount NUMERIC(30, 8)

-- 数量（整数）
quantity INTEGER

-- 成交量（大整数）
volume BIGINT
```

---

## 📝 数据库初始化

### SQL 脚本位置
- 初始化脚本: `backend/database/migrations/init_postgres.sql`
- Python 脚本: `backend/database/scripts/init_db.py`

### 初始化步骤

1. **启动 PostgreSQL**
   ```bash
   docker-compose up -d postgres
   ```

2. **运行初始化脚本**
   ```bash
   python backend/database/scripts/init_db.py
   ```

3. **验证初始化**
   ```bash
   python backend/database/scripts/test_db.py
   ```

---

## 🔗 连接配置

### 环境变量

```bash
# .env 文件
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=quant_trade
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=quant_trade
```

### 连接字符串

```python
DATABASE_URL = "postgresql+asyncpg://quant_trade:password@localhost:5432/quant_trade"
```

---

## 📈 性能优化

### 1. 索引优化

```sql
-- 复合索引（symbol + timestamp）
CREATE INDEX idx_stock_prices_symbol_timestamp 
ON stock_prices(symbol, timestamp DESC);

-- 覆盖索引（减少回表查询）
CREATE INDEX idx_orders_user_id_status 
ON orders(user_id, status);
```

### 2. 分区表（TimescaleDB）

```sql
-- 创建超表（Hypertable）
SELECT create_hypertable('stock_prices', 'timestamp');

-- 按时间自动分区
-- 自动按天、周或月分区
```

### 3. 查询优化

```python
# ✅ 使用参数化查询
session.execute(
    text("SELECT * FROM stocks WHERE symbol = :symbol"),
    {"symbol": "000001.SZ"}
)

# ❌ 禁止字符串拼接（SQL 注入风险）
# symbol = "000001.SZ"
# query = f"SELECT * FROM stocks WHERE symbol = '{symbol}'"
```

---

## 🔒 安全规范

### 1. 禁止 SQL 注入

```python
# ✅ 正确：使用参数化查询
from sqlalchemy import text

stmt = text("SELECT * FROM stocks WHERE symbol = :symbol")
result = await session.execute(stmt, {"symbol": symbol})

# ❌ 错误：字符串拼接
# query = f"SELECT * FROM stocks WHERE symbol = '{symbol}'"
```

### 2. 最小权限原则

```sql
-- 创建只读用户
CREATE USER quant_trade_readonly WITH PASSWORD 'readonly_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO quant_trade_readonly;

-- 创建读写用户
CREATE USER quant_trade_user WITH PASSWORD 'user_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO quant_trade_user;
```

### 3. 密码管理

⚠️ **绝对禁止**:
- ❌ 将密码硬编码到代码中
- ❌ 将密码提交到 Git 仓库
- ❌ 使用弱密码

✅ **必须**:
- ✅ 使用环境变量存储密码
- ✅ 使用强密码（16位以上，包含大小写字母、数字、特殊字符）
- ✅ 定期更换密码

---

## 📊 数据备份

### 1. 手动备份

```bash
# 备份整个数据库
pg_dump -U quant_trade -d quant_trade > backup_$(date +%Y%m%d).sql

# 恢复数据库
psql -U quant_trade -d quant_trade < backup_20260308.sql
```

### 2. 自动备份（Cron）

```bash
# 添加到 crontab
0 2 * * * pg_dump -U quant_trade quant_trade | gzip > /backup/quant_trade_$(date +\%Y\%m\%d).sql.gz
```

---

## 🔍 监控和维护

### 1. 查看数据库大小

```sql
SELECT
    pg_size_pretty(pg_database_size('quant_trade')) AS database_size,
    pg_size_pretty(pg_total_relation_size('stocks')) AS stocks_size,
    pg_size_pretty(pg_total_relation_size('stock_prices')) AS prices_size;
```

### 2. 查看表行数

```sql
SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

### 3. 查看慢查询

```sql
-- 启用慢查询日志
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1秒

-- 查看慢查询
SELECT
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

---

## 📚 相关文档

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [SQLAlchemy Async 文档](https://docs.sqlalchemy.org/en/20/core/engines.html#asyncio)
- [TimescaleDB 文档](https://docs.timescale.com/)

---

**维护者**: 角色 C（全栈开发工程师）
**审核者**: 角色 B（金融系统架构师）
**版本**: v1.0.0
**最后更新**: 2026-03-08
