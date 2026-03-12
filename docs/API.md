# Quant-Trade System API 文档

> **版本**: v2.3.0
> **基础 URL**: `http://localhost:8000/api/v1`
> **更新日期**: 2026-03-12

---

## 1. 概述

Quant-Trade System 提供了一套完整的 RESTful API，支持策略管理、回测执行、交易管理、投资组合等核心功能。

### 1.1 通用规范

#### 请求格式
- **Content-Type**: `application/json`
- **认证方式**: `Bearer Token` (JWT)

#### 响应格式
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "detail": "详细错误信息"
  }
}
```

### 1.2 认证

除了登录接口外，所有 API 请求都需要在 Header 中携带 JWT Token：

```
Authorization: Bearer <your_jwt_token>
```

---

## 2. 认证接口 `/api/v1/auth`

### 2.1 用户登录

**POST** `/auth/login`

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### 2.2 刷新 Token

**POST** `/auth/refresh`

**请求体**:
```json
{
  "refresh_token": "string"
}
```

### 2.3 登出

**POST** `/auth/logout`

---

## 3. 用户接口 `/api/v1/users`

### 3.1 获取当前用户

**GET** `/users/me`

**响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "test_user",
    "email": "test@example.com",
    "role": "trader",
    "created_at": "2026-03-01T00:00:00Z"
  }
}
```

### 3.2 更新用户信息

**PUT** `/users/me`

**请求体**:
```json
{
  "email": "new_email@example.com",
  "preferences": {
    "language": "zh_CN",
    "theme": "dark"
  }
}
```

---

## 4. 策略接口 `/api/v1/strategies`

### 4.1 获取策略列表

**GET** `/strategies`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |
| status | string | 否 | 状态筛选 |

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "动量策略",
        "version": "1.2.0",
        "status": "active",
        "created_at": "2026-03-01T00:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 4.2 创建策略

**POST** `/strategies`

**请求体**:
```json
{
  "name": "string",
  "description": "string",
  "type": "momentum",
  "parameters": {
    "lookback_period": 20,
    "threshold": 0.05
  }
}
```

### 4.3 获取策略版本列表

**GET** `/strategies/{strategy_id}/versions`

### 4.4 激活策略版本

**POST** `/strategies/{strategy_id}/versions/{version_id}/activate`

### 4.5 回滚策略版本

**POST** `/strategies/{strategy_id}/versions/{version_id}/rollback`

---

## 5. 回测接口 `/api/v1/backtest`

### 5.1 创建回测任务

**POST** `/backtest`

**请求体**:
```json
{
  "strategy_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 1000000,
  "commission_rate": 0.0003,
  "slippage": 0.001
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_20260310_001",
    "status": "running",
    "progress": 0
  }
}
```

### 5.2 获取回测状态

**GET** `/backtest/{backtest_id}/status`

### 5.3 获取回测结果

**GET** `/backtest/{backtest_id}/result`

**响应**:
```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_20260310_001",
    "status": "completed",
    "metrics": {
      "total_return": 0.256,
      "annual_return": 0.312,
      "sharpe_ratio": 1.85,
      "max_drawdown": -0.125,
      "win_rate": 0.62
    },
    "daily_returns": [...],
    "positions": [...]
  }
}
```

### 5.4 获取因子分析

**GET** `/backtest/{backtest_id}/factors`

**响应**:
```json
{
  "success": true,
  "data": {
    "factors": [
      {
        "name": "momentum_20",
        "ic": 0.045,
        "ic_ir": 2.1,
        "factor_return": 0.012,
        "turnover": 0.35
      }
    ]
  }
}
```

### 5.5 获取归因分析

**GET** `/backtest/{backtest_id}/attribution`

---

## 6. 交易接口 `/api/v1/trading`

### 6.1 获取交易模式

**GET** `/trading/mode`

**响应**:
```json
{
  "success": true,
  "data": {
    "mode": "simulation",
    "broker": "mock",
    "account_id": "sim_001"
  }
}
```

### 6.2 设置交易模式

**POST** `/trading/mode`

**请求体**:
```json
{
  "mode": "simulation",
  "broker": "mock"
}
```

### 6.3 下单

**POST** `/trading/orders`

**请求体**:
```json
{
  "symbol": "000001.SZ",
  "side": "buy",
  "order_type": "limit",
  "quantity": 1000,
  "price": 12.50,
  "strategy_id": 1
}
```

### 6.4 获取订单列表

**GET** `/trading/orders`

### 6.5 取消订单

**DELETE** `/trading/orders/{order_id}`

---

## 7. 成交接口 `/api/v1/fills`

### 7.1 获取成交记录

**GET** `/fills`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |
| symbol | string | 否 | 股票代码 |

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "order_id": "ord_001",
        "symbol": "000001.SZ",
        "side": "buy",
        "quantity": 1000,
        "price": 12.50,
        "commission": 3.75,
        "stamp_duty": 1.25,
        "transfer_fee": 0.1,
        "filled_at": "2026-03-10T10:30:00Z"
      }
    ],
    "total": 50
  }
}
```

---

## 8. 交易日历接口 `/api/v1/trading-calendar`

### 8.1 获取交易日历

**GET** `/trading-calendar`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| year | int | 是 | 年份 |
| month | int | 否 | 月份 |

### 8.2 检查交易日

**GET** `/trading-calendar/is-trading-day`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| date | date | 是 | 日期 |

---

## 9. 投资组合接口 `/api/v1/portfolios`

### 9.1 获取组合列表

**GET** `/portfolios`

### 9.2 创建组合

**POST** `/portfolios`

**请求体**:
```json
{
  "name": "string",
  "description": "string",
  "base_currency": "CNY"
}
```

### 9.3 获取组合持仓

**GET** `/portfolios/{portfolio_id}/positions`

### 9.4 更新持仓权重

**PUT** `/portfolios/{portfolio_id}/positions`

**请求体**:
```json
{
  "positions": [
    {
      "symbol": "000001.SZ",
      "target_weight": 0.15
    }
  ]
}
```

### 9.5 获取风险指标

**GET** `/portfolios/{portfolio_id}/risk-metrics`

**响应**:
```json
{
  "success": true,
  "data": {
    "var_95": 0.025,
    "cvar_95": 0.035,
    "concentration": 0.32,
    "diversification_ratio": 0.85,
    "beta": 1.12,
    "volatility": 0.18
  }
}
```

### 9.6 组合优化

**POST** `/portfolios/{portfolio_id}/optimize`

**请求体**:
```json
{
  "method": "mean_variance",
  "target_return": 0.15,
  "constraints": {
    "max_weight": 0.1,
    "min_weight": 0.01
  }
}
```

---

## 10. 风控接口 `/api/v1/risk`

### 10.1 获取风控规则

**GET** `/risk/rules`

### 10.2 创建风控规则

**POST** `/risk/rules`

**请求体**:
```json
{
  "name": "单只股票止损",
  "type": "stop_loss",
  "parameters": {
    "threshold": -0.05,
    "action": "sell_all"
  }
}
```

### 10.3 获取风控事件

**GET** `/risk/events`

---

## 11. 数据接口 `/api/v1/data`

### 11.1 获取股票列表

**GET** `/data/stocks`

### 11.2 获取股票行情

**GET** `/data/stocks/{symbol}/quote`

### 11.3 获取历史 K 线

**GET** `/data/stocks/{symbol}/klines`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| start_date | date | 是 | 开始日期 |
| end_date | date | 是 | 结束日期 |
| period | string | 否 | 周期：day/week/month |

---

## 12. 自选股接口 `/api/v1/watchlist`

### 12.1 获取自选股列表

**GET** `/watchlist`

### 12.2 添加自选股

**POST** `/watchlist`

**请求体**:
```json
{
  "symbol": "000001.SZ",
  "group": "main"
}
```

### 12.3 删除自选股

**DELETE** `/watchlist/{symbol}`

---

## 13. 价格预警接口 `/api/v1/alerts`

### 13.1 获取预警列表

**GET** `/alerts`

### 13.2 创建价格预警

**POST** `/alerts`

**请求体**:
```json
{
  "symbol": "000001.SZ",
  "type": "price_above",
  "value": 15.00,
  "notification": {
    "email": true,
    "web_push": true
  }
}
```

### 13.3 删除预警

**DELETE** `/alerts/{alert_id}`

---

## 14. WebSocket 接口

### 14.1 连接

**URL**: `ws://localhost:8000/api/v1/ws/market`

### 14.2 订阅行情

**发送消息**:
```json
{
  "action": "subscribe",
  "symbols": ["000001.SZ", "600000.SH"]
}
```

### 14.3 取消订阅

**发送消息**:
```json
{
  "action": "unsubscribe",
  "symbols": ["000001.SZ"]
}
```

### 14.4 接收行情推送

**接收消息**:
```json
{
  "type": "quote",
  "data": {
    "symbol": "000001.SZ",
    "price": 12.50,
    "change": 0.05,
    "change_pct": 0.004,
    "volume": 12345678,
    "amount": 154321000,
    "high": 12.80,
    "low": 12.30,
    "open": 12.45,
    "prev_close": 12.45,
    "timestamp": "2026-03-10T10:30:00Z"
  }
}
```

---

## 15. 错误码

| 错误码 | 描述 |
|--------|------|
| AUTH_001 | 认证失败 |
| AUTH_002 | Token 过期 |
| AUTH_003 | 权限不足 |
| DATA_001 | 数据不存在 |
| DATA_002 | 数据格式错误 |
| TRADE_001 | 交易时间不允许 |
| TRADE_002 | 余额不足 |
| TRADE_003 | 持仓不足 |
| RISK_001 | 触发风控规则 |
| SYS_001 | 系统错误 |
| SYS_002 | 服务不可用 |

---

## 16. OpenBB 平台接口 `/api/v1/openbb`

OpenBB Platform 提供全球市场数据，包括美股、国际股票、宏观经济、技术分析等。

### 16.1 股票实时报价

**GET** `/openbb/equity/quote/{symbol}`

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 股票代码 (如 AAPL, MSFT) |

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| provider | string | 否 | 数据提供商 (yfinance, fmp, polygon) |

**响应**:
```json
{
  "symbol": "AAPL",
  "price": 178.50,
  "open": 177.20,
  "high": 179.30,
  "low": 176.80,
  "close": 178.50,
  "volume": 52345678,
  "change": 1.30,
  "change_percent": 0.73,
  "previous_close": 177.20,
  "provider": "yfinance"
}
```

### 16.2 历史价格数据

**GET** `/openbb/equity/historical/{symbol}`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| start_date | date | 否 | 开始日期 (YYYY-MM-DD) |
| end_date | date | 否 | 结束日期 (YYYY-MM-DD) |
| provider | string | 否 | 数据提供商 |

**响应**:
```json
{
  "symbol": "AAPL",
  "data": [
    {
      "timestamp": "2026-03-11T00:00:00",
      "open": 177.20,
      "high": 179.30,
      "low": 176.80,
      "close": 178.50,
      "volume": 52345678
    }
  ],
  "provider": "yfinance",
  "count": 30
}
```

### 16.3 股票基本面数据

**GET** `/openbb/equity/fundamentals/{symbol}`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| statement_type | string | 否 | 报表类型: balance/income/cash |
| period | string | 否 | 周期: annual/quarterly |
| provider | string | 否 | 数据提供商 |

### 16.4 宏观经济指标

**GET** `/openbb/economy/macro/{indicator}`

**常用指标**:
- `GDP`: 国内生产总值
- `CPI`: 消费者物价指数
- `UNRATE`: 失业率
- `FEDFUNDS`: 联邦基金利率
- `DGS10`: 10年期国债收益率

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |
| provider | string | 否 | 数据提供商 (fred, oecd) |

### 16.5 技术分析指标

**GET** `/openbb/technical/indicators/{symbol}`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| indicators | string | 是 | 指标列表 (逗号分隔): rsi,macd,bbands,sma,ema |
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |

**响应**:
```json
{
  "symbol": "AAPL",
  "indicators": ["rsi", "macd"],
  "data": [
    {
      "timestamp": "2026-03-11",
      "rsi": 65.32,
      "macd": 1.25,
      "macd_signal": 1.10,
      "macd_histogram": 0.15
    }
  ],
  "provider": "yfinance",
  "count": 30
}
```

### 16.6 服务状态

**GET** `/openbb/status`

**响应**:
```json
{
  "name": "openbb",
  "description": "OpenBB Platform 多源数据",
  "is_connected": true,
  "use_fallback": false,
  "supported_types": ["stock_price", "fundamental", "macro_economic", "technical_indicator"],
  "providers": {
    "equity": true,
    "economy": true,
    "technical": true
  }
}
```

### 16.7 支持的提供商列表

**GET** `/openbb/providers`

**响应**:
```json
{
  "equity": {
    "free": ["yfinance"],
    "paid": ["fmp", "polygon", "intrinio"]
  },
  "economy": {
    "free": ["fred"],
    "paid": ["oecd", "tradingeconomics"]
  },
  "news": {
    "paid": ["benzinga", "biztoc"]
  }
}
```

---

## 17. 券商接口

系统支持多种券商接口，用于实盘交易执行。

### 17.1 东方财富证券

**文件位置**: `backend/src/brokers/eastmoney.py`

**支持功能**:
- 股票交易（买入/卖出）
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

### 17.2 迅投 QMT

**文件位置**: `backend/src/brokers/xtquant.py`

**支持功能**:
- 实时行情订阅
- 股票交易（买入/卖出）
- 撤单
- 查询持仓和资金
- 查询订单状态

**配置参数**:
```python
{
    "qmt_path": "C:\\迅投QMT交易端\\userdata_mini",
    "account_id": "your_account_id",
    "account_type": "STOCK"
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

# 订阅行情
await broker.subscribe_quote(["000001.SZ", "600000.SH"], callback)
```

### 17.3 券商工厂

**文件位置**: `backend/src/brokers/factory.py`

通过券商工厂创建券商实例：

```python
from brokers.factory import BrokerFactory

# 创建东方财富券商
broker = BrokerFactory.create_broker("eastmoney", config)

# 创建 QMT 券商
broker = BrokerFactory.create_broker("xtquant", config)
```

---

## 18. 请求限流

| 接口类型 | 限制 |
|----------|------|
| 普通接口 | 100 次/分钟 |
| 交易接口 | 30 次/分钟 |
| WebSocket | 10 个连接/用户 |

---

## 17. 更多资源

- [Swagger UI](http://localhost:8000/docs) - 交互式 API 文档
- [ReDoc](http://localhost:8000/redoc) - 精美的 API 文档
- [系统架构](./SYSTEM_ARCHITECTURE.md) - 系统架构详解

---

**维护者**: QuantDev Team
**最后更新**: 2026-03-12
