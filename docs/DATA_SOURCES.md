# 数据源配置指南

> **版本**: v1.0.0
> **更新日期**: 2026-03-12
> **作者**: QuantDev Team

---

## 1. 概述

Quant-Trade System 集成了多种数据源，提供全面的 A 股、美股、宏观经济、技术分析等数据支持。本文档详细说明各数据源的配置和使用方法。

---

## 2. A 股数据源

### 2.1 AkShare (免费)

**类型**: 免费数据源
**优先级**: 10 (基础数据源)
**文件位置**: `backend/src/services/data/akshare.py`

**支持数据**:
- 股票日线行情 (开高低收、成交量)
- 股票基础信息(代码、名称、行业)
- 指数数据
- 板块数据
- 财务数据(部分)

**使用示例**:
```python
from services.data.akshare import AkShareAdapter

adapter = AkShareAdapter()
await adapter.connect()

# 获取日线数据
data = await adapter.fetch_history(DataRequest(
    symbols=["000001.SZ"],
    data_type=DataType.STOCK_PRICE,
    start_date=date(2026, 1, 1),
    end_date=date(2026, 3, 12),
    frequency=DataFrequency.DAY
))
```

**配置要求**:
- 无需 API Key
- 建议设置请求频率限制，避免被封禁

### 2.2 Tushare Pro (专业)

**类型**: 付费数据源
**优先级**: 15
**文件位置**: 待实现

**支持数据**:
- 高质量历史数据
- 复权数据
- 财务报表
- 宏观数据

**配置参数**:
```env
TUSHARE_API_KEY=your_api_key
TUSHARE_API_URL=https://api.tushare.pro
```

---

## 3. 美股/国际市场数据源

### 3.1 OpenBB Platform

**类型**: 多源聚合数据
**优先级**: 25 (高优先级)
**文件位置**: `backend/src/services/data/openbb/`

**支持数据**:
- 美股实时报价和历史数据
- 国际市场股票数据
- 基本面数据(资产负债表/利润表/现金流量表)
- 宏观经济指标(FRED/OECD/IMF)
- 技术分析指标(RSI/MACD/布林带等)
- 新闻数据(部分)

**数据提供商**:

| 提供商 | 类型 | 数据范围 | 费用 |
|--------|------|----------|------|
| yfinance | 免费 | 美股行情 | 免费 |
| FMP | 付费 | 美股基本面 | 付费 |
| Polygon | 付费 | 实时行情 | 付费 |
| FRED | 免费 | 美国宏观经济 | 免费 |
| OECD | 付费 | 国际宏观 | 付费 |
| Benzinga | 付费 | 财经新闻 | 付费 |

**使用示例**:
```python
from services.data.openbb import OpenBBAdapter

adapter = OpenBBAdapter(config={
    'fmp_api_key': 'your_key',
    'fred_api_key': 'your_key',
})
await adapter.connect()

# 获取美股报价
quote = await adapter.get_quote("AAPL")

# 获取历史数据
data = await adapter.get_historical_price(
    symbol="AAPL",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 3, 12),
)

# 获取宏观数据
gdp = await adapter.economy.get_indicator("GDP", provider="fred")

# 获取技术指标
rsi = await adapter.technical.get_rsi("AAPL", length=14)
```

**配置参数**:
```env
# OpenBB Hub 个人访问令牌 (可选)
OPENBB_HUB_PAT=your_pat

# 各数据源 API Key
OPENBB_FMP_API_KEY=your_key
OPENBB_POLYGON_API_KEY=your_key
OPENBB_FRED_API_KEY=your_key
OPENBB_BENZINGA_API_KEY=your_key
OPENBB_INTRINIO_API_KEY=your_key
OPENBB_TIINGO_API_KEY=your_key

# 默认提供商
OPENBB_DEFAULT_EQUITY_PROVIDER=yfinance
OPENBB_DEFAULT_ECONOMY_PROVIDER=fred
```

**API 端点**:
- `/api/v1/openbb/equity/quote/{symbol}` - 股票报价
- `/api/v1/openbb/equity/historical/{symbol}` - 历史数据
- `/api/v1/openbb/equity/fundamentals/{symbol}` - 基本面数据
- `/api/v1/openbb/economy/macro/{indicator}` - 宏观指标
- `/api/v1/openbb/technical/indicators/{symbol}` - 技术分析
- `/api/v1/openbb/status` - 服务状态
- `/api/v1/openbb/providers` - 提供商列表

### 3.2 Yahoo Finance

**类型**: 免费数据源
**优先级**: 20
**文件位置**: `backend/src/services/data/yahoo_finance.py`

**支持数据**:
- 美股/港股行情
- 历史K线数据
- 股票基本信息

**使用示例**:
```python
from services.data.yahoo_finance import YahooFinanceAdapter

adapter = YahooFinanceAdapter()
await adapter.connect()

data = await adapter.fetch_history(DataRequest(
    symbols=["AAPL", "MSFT"],
    data_type=DataType.STOCK_PRICE,
))
```

---

## 4. 券商交易接口

### 4.1 东方财富证券

**类型**: 券商API
**文件位置**: `backend/src/brokers/eastmoney.py`

**支持功能**:
- 股票交易(买入/卖出)
- 撤单
- 查询持仓和资金
- 查询订单状态

**配置参数**:
```python
{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "account_id": "your_account_id",
    "sandbox": True  # 沙箱环境
}
```

**使用示例**:
```python
from brokers.eastmoney import EastMoneyBroker

broker = EastMoneyBroker(config)
await broker.connect()

# 下单
result = await broker.place_order(
    symbol="000001.SZ",
    side="BUY",
    quantity=1000,
    price=Decimal("12.50"),
    order_type="LIMIT"
)

# 获取持仓
positions = await broker.get_positions()
```

### 4.2 迅投 QMT

**类型**: 本地量化终端
**文件位置**: `backend/src/brokers/xtquant.py`

**支持功能**:
- 实时行情订阅
- 股票交易(买入/卖出)
- 撤单
- 查询持仓和资金
- 查询订单状态

**使用要求**:
- 需要安装 QMT 客户端
- 需要在 QMT 中开启外部 Python 接口

**配置参数**:
```python
{
    "qmt_path": "C:\\迅投QMT交易端\\userdata_mini",
    "account_id": "your_account_id",
    "account_type": "STOCK"  # STOCK/FUTURE
}
```

**使用示例**:
```python
from brokers.xtquant import XTQuantBroker

broker = XTQuantBroker(config)
await broker.connect()

# 下单
result = await broker.place_order(
    symbol="000001.SZ",
    side="BUY",
    quantity=1000,
    price=Decimal("12.50"),
    order_type="LIMIT"
)

# 订阅实时行情
await broker.subscribe_quote(["000001.SZ", "600000.SH"], callback)
```

---

## 5. 数据引擎架构

数据引擎采用多源适配器模式，支持自动数据源选择和优先级路由。

### 5.1 架构图

```
┌───────────────────────────────────────────────────────────────┐
│                         数据引擎                               │
│                   (services/data/engine.py)                    │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  适配器管理器                            │ │
│  │  - 注册/注销适配器                                     │ │
│  │  - 优先级排序                                           │ │
│  │  - 自动数据源选择                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                   │
│  ┌───────────┬───────────┬───────────┬───────────┐         │
│  │ AkShare   │ OpenBB   │ YahooFin  │ Database  │         │
│  │ (A股)     │ (美股)   │ (后备)    │ (存储)    │         │
│  │ Priority: │ Priority: │ Priority: │ Priority: │         │
│  │    10     │    25     │    20     │    30     │         │
│  └───────────┴───────────┴───────────┴───────────┘         │
└───────────────────────────────────────────────────────────────┘
```

### 5.2 数据源选择逻辑

1. **市场判断**: 根据股票代码判断市场 (A 股 vs 美股)
2. **优先级排序**: 按优先级从高到低选择可用适配器
3. **降级策略**: 高优先级失败时自动降级到低优先级

```python
# 示例: A 股数据获取流程
1. 检测市场: 000001.SZ -> A 股
2. 选择适配器: AkShare (优先级 10)
3. 如果 AkShare 失败 -> 降级到 Database (优先级 30)

# 示例: 美股数据获取流程
1. 检测市场: AAPL -> 美股
2. 选择适配器: OpenBB (优先级 25)
3. 如果 OpenBB 失败 -> 降级到 Yahoo Finance (优先级 20)
```

---

## 6. 数据缓存策略

### 6.1 Redis 缓存

**缓存键格式**: `data:{type}:{symbol}:{date}`

**示例**:
- `data:quote:000001.SZ:2026-03-12` - 实时报价 (TTL: 60s)
- `data:kline:000001.SZ:daily` - 日K线 (TTL: 1天)
- `data:fundamental:AAPL:annual` - 基本面 (TTL: 1周)

### 6.2 OpenBB 专用缓存

**文件位置**: `backend/src/services/data/openbb/cache.py`

**缓存策略**:
- 报价数据: 60 秒
- 历史数据: 1 天
- 基本面数据: 1 周
- 宏观数据: 1 月

---

## 7. 配置最佳实践

### 7.1 开发环境

推荐使用免费数据源:
- A 股: AkShare
- 美股: yfinance
- 宏观: FRED

### 7.2 生产环境

推荐使用付费数据源:
- A 股: Tushare Pro
- 美股: OpenBB + FMP/Polygon
- 实时行情: 券商 API

### 7.3 交易环境

推荐配置:
- 行情: 券商实时行情 (QMT/东财)
- 数据: 本地数据库缓存
- 备份: AkShare/OpenBB

---

**维护者**: QuantDev Team
**最后更新**: 2026-03-12
