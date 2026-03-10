# WebSocket 实时行情系统架构设计

> **版本**: v1.0.0
> **创建日期**: 2026-03-08
> **作者**: QuantDev Team

---

## 1. 系统概述

### 1.1 功能目标
- 提供实时行情数据推送（A股市场）
- 支持多客户端同时订阅
- 低延迟、高并发
- 自动心跳检测和断线重连

### 1.2 技术栈
- **WebSocket 服务器**: FastAPI WebSocket
- **缓存**: Redis 7+
- **行情源**: AkShare / Tushare
- **前端**: WebSocket API

---

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Web App │  │  Web App │  │  Mobile  │  │  Desktop │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │           │
│       └─────────────┴─────────────┴─────────────┘           │
│                     │ (WebSocket)                           │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│              WebSocket Server Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Connection Manager (FastAPI WebSocket)       │  │
│  │  - 连接管理                                           │  │
│  │  - 消息路由                                           │  │
│  │  - 心跳检测                                           │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────┴───────────────────────────────────┐  │
│  │           Subscription Manager                        │  │
│  │  - 订阅关系管理                                       │  │
│  │  - 广播推送                                           │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│              Market Data Layer                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Market Data Service                          │  │
│  │  - 行情数据获取                                       │  │
│  │  - 数据聚合计算                                       │  │
│  │  - 缓存更新                                           │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│         ┌───────────┴───────────┐                          │
│         │                       │                          │
│  ┌──────▼──────┐        ┌──────▼──────┐                   │
│  │   Redis     │        │  Data Source │                   │
│  │   Cache     │        │  (AkShare)  │                   │
│  └─────────────┘        └─────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
1. 客户端连接
   Client → WebSocket Server → Connection Manager
   └─> 建立连接，分配 connection_id

2. 订阅行情
   Client → WebSocket: {"type": "subscribe", "symbols": ["000001.SZ"]}
   └─> Subscription Manager 记录订阅关系
   └─> 立即推送当前缓存行情

3. 行情更新
   Market Data Service → AkShare API
   └─> 更新 Redis 缓存
   └─> Subscription Manager 查询订阅者
   └─> 广播推送: {"type": "quote", "data": {...}}

4. 取消订阅
   Client → WebSocket: {"type": "unsubscribe", "symbols": ["000001.SZ"]}
   └─> Subscription Manager 移除订阅关系

5. 断开连接
   Client → WebSocket: close
   └─> Connection Manager 清理连接
   └─> Subscription Manager 清理订阅
```

---

## 3. 消息协议

### 3.1 客户端 → 服务器

#### 3.1.1 订阅行情
```json
{
  "type": "subscribe",
  "symbols": ["000001.SZ", "000002.SZ", "600000.SH"]
}
```

#### 3.1.2 取消订阅
```json
{
  "type": "unsubscribe",
  "symbols": ["000001.SZ"]
}
```

#### 3.1.3 心跳包
```json
{
  "type": "ping"
}
```

### 3.2 服务器 → 客户端

#### 3.2.1 行情推送
```json
{
  "type": "quote",
  "data": {
    "symbol": "000001.SZ",
    "name": "平安银行",
    "price": 10.50,
    "change": 0.15,
    "change_pct": 1.45,
    "volume": 1234567,
    "amount": 13024500.00,
    "bid_price": 10.49,
    "ask_price": 10.51,
    "high": 10.60,
    "low": 10.40,
    "open": 10.45,
    "prev_close": 10.35,
    "timestamp": "2026-03-08T14:30:00+08:00"
  }
}
```

#### 3.2.2 心跳响应
```json
{
  "type": "pong"
}
```

#### 3.2.3 错误消息
```json
{
  "type": "error",
  "message": "Invalid subscription request",
  "code": 400
}
```

---

## 4. 数据结构

### 4.1 Redis 数据结构

#### 4.1.1 行情缓存
```
Key: market:quote:{symbol}
Type: Hash
TTL: 5 秒
Fields:
  - symbol: 股票代码
  - name: 股票名称
  - price: 最新价
  - change: 涨跌额
  - change_pct: 涨跌幅
  - volume: 成交量
  - amount: 成交额
  - bid_price: 买一价
  - ask_price: 卖一价
  - high: 最高价
  - low: 最低价
  - open: 今开价
  - prev_close: 昨收价
  - timestamp: 时间戳
```

#### 4.1.2 订阅关系
```
Key: market:subscription:{user_id}
Type: Set
Members: [symbol1, symbol2, ...]
```

#### 4.1.3 反向索引（Symbol -> Users）
```
Key: market:subscribers:{symbol}
Type: Set
Members: [user_id1, user_id2, ...]
```

### 4.2 内存数据结构

#### 4.1.1 连接管理
```python
{
    connection_id: {
        "user_id": int,
        "websocket": WebSocket,
        "subscriptions": Set[str],
        "last_ping": datetime
    }
}
```

---

## 5. 性能指标

### 5.1 目标指标
- **并发连接**: ≥ 10,000
- **消息延迟**: ≤ 100ms (P95)
- **推送频率**: 1-5 次/秒（根据市场活跃度）
- **吞吐量**: ≥ 100,000 msg/s

### 5.2 优化策略
1. **Redis 缓存**: 减少外部 API 调用
2. **批量推送**: 聚合多个股票行情
3. **连接池**: Redis 连接复用
4. **异步处理**: asyncio 全链路异步

---

## 6. 安全性

### 6.1 认证授权
- WebSocket 连接时验证 JWT Token
- 每个消息验证用户权限
- 限制订阅数量（防止资源滥用）

### 6.2 限流策略
- 单用户最多订阅 100 只股票
- 心跳间隔 ≥ 30 秒
- 连接超时时间：5 分钟

---

## 7. 监控告警

### 7.1 监控指标
- WebSocket 连接数
- 消息推送成功率
- 平均延迟
- Redis 命中率
- 外部 API 调用次数

### 7.2 告警规则
- 连接数 > 8000：容量预警
- 推送失败率 > 5%：服务异常
- 延迟 > 500ms：性能告警

---

## 8. 扩展性

### 8.1 水平扩展
- WebSocket 服务器无状态
- 使用 Redis Pub/Sub 实现跨服务器广播
- 负载均衡：Sticky Session

### 8.2 功能扩展
- 支持更多市场（港股、美股）
- 支持 K 线推送
- 支持自定义指标计算
- 支持行情回放

---

**最后更新**: 2026-03-08
