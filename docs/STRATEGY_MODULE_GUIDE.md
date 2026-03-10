# 量化策略模块使用指南

> **版本**: v2.0.0
> **更新日期**: 2026-03-10
> **作者**: QuantDev Team

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [策略注册表](#策略注册表)
4. [策略基类](#策略基类)
5. [隔离上下文](#隔离上下文)
6. [数据引擎](#数据引擎)
7. [API 参考](#api-参考)
8. [最佳实践](#最佳实践)

---

## 概述

量化策略模块 v2.0 采用全新的架构设计，参考了 Vn.py 和 Backtrader 的优秀设计模式，提供：

- **装饰器注册** - 使用 `@strategy` 装饰器自动注册策略
- **隔离上下文** - 每个策略实例拥有独立的持仓、资金和订单
- **统一数据引擎** - 多数据源适配、缓存和实时订阅
- **事件驱动** - 支持生命周期回调和事件处理
- **状态持久化** - 策略状态保存和恢复

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      策略注册表 (Registry)                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │ 策略 A  │ │ 策略 B  │ │ 策略 C  │ │ ...     │            │
│  └────┬────┘ └────┬────┘ └────┬────┘ └─────────┘            │
│       │           │           │                              │
│       ▼           ▼           ▼                              │
│  ┌─────────────────────────────────────────────┐            │
│  │           策略实例 (Instances)               │            │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │            │
│  │  │ 实例 1  │ │ 实例 2  │ │ 实例 3  │        │            │
│  │  └────┬────┘ └────┬────┘ └────┬────┘        │            │
│  └───────┼───────────┼───────────┼─────────────┘            │
└──────────┼───────────┼───────────┼──────────────────────────┘
           │           │           │
           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                    隔离上下文 (Context)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ 持仓管理    │  │ 订单管理    │  │ 资金管理    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据引擎 (DataEngine)                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                        │
│  │ AkShare │ │ Tushare │ │ 自定义  │                        │
│  └────┬────┘ └────┬────┘ └────┬────┘                        │
│       └───────────┼───────────┘                              │
│                   ▼                                          │
│            ┌─────────────┐                                   │
│            │ 数据缓存    │                                   │
│            └─────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 创建策略

使用 `@strategy` 装饰器注册策略：

```python
from src.services.strategy.registry import strategy, StrategyFrequency
from src.services.strategy.base import StrategyBase, StrategyConfig, Signal, SignalType
from src.services.strategy.context import IsolatedStrategyContext
from typing import List, Optional

@strategy(
    strategy_id="my_ma_cross",
    name="我的均线策略",
    version="1.0.0",
    author="Your Name",
    description="基于双均线交叉的趋势跟踪策略",
    category="trend",
    frequency=StrategyFrequency.DAILY,
    tags=["均线", "趋势"],
    default_params={
        "short_period": 5,
        "long_period": 20,
    },
)
class MyMAStrategy(StrategyBase):
    """我的均线策略"""

    def initialize(self, context: IsolatedStrategyContext) -> None:
        """初始化策略"""
        self.short_period = self.parameters.get("short_period", 5)
        self.long_period = self.parameters.get("long_period", 20)
        self.price_history = []

    def on_data(self, context: IsolatedStrategyContext) -> Optional[List[Signal]]:
        """处理数据生成信号"""
        symbol = self.parameters.get("symbol", "")
        current_price = context.get_current_price(symbol)

        if current_price is None:
            return None

        self.price_history.append(current_price)

        # 计算均线
        if len(self.price_history) < self.long_period:
            return None

        short_ma = sum(self.price_history[-self.short_period:]) / self.short_period
        long_ma = sum(self.price_history[-self.long_period:]) / self.long_period

        signals = []

        # 金叉买入
        if short_ma > long_ma and not context.has_position(symbol):
            quantity = int(context.cash / current_price / 100) * 100
            if quantity > 0:
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=context.current_time,
                    price=float(current_price),
                    quantity=quantity,
                    reason="金叉买入"
                ))

        return signals if signals else None

    def finalize(self, context: IsolatedStrategyContext) -> None:
        """策略结束"""
        self.log_info("策略结束")
```

### 2. 创建实例并运行

```python
from src.services.strategy.registry import strategy_registry

# 创建策略实例
instance = strategy_registry.create_instance(
    strategy_id="my_ma_cross",
    params={"symbol": "000001.SZ"},
    initial_capital=100000,
)

# 运行策略（示例）
context = instance.get_context()
instance.initialize(context)

# 模拟数据输入
for bar_data in historical_data:
    context.update_current_price("000001.SZ", bar_data["close"])
    signals = instance.on_data(context)
    # 处理信号...
```

### 3. 通过 API 访问

```bash
# 获取策略列表
curl http://localhost:8000/api/v1/strategy-registry/

# 创建实例
curl -X POST http://localhost:8000/api/v1/strategy-registry/instances \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "my_ma_cross",
    "params": {"symbol": "000001.SZ"},
    "initial_capital": 100000
  }'
```

---

## 策略注册表

### 注册方式

#### 方式一：装饰器注册（推荐）

```python
from src.services.strategy.registry import strategy

@strategy(
    strategy_id="strategy_id",
    name="策略名称",
    category="trend",
    tags=["tag1", "tag2"],
    default_params={"param1": 10},
)
class MyStrategy(StrategyBase):
    # ...
```

#### 方式二：手动注册

```python
from src.services.strategy.registry import strategy_registry

strategy_registry.register_class(
    MyStrategy,
    strategy_id="my_strategy",
    name="我的策略",
    category="custom",
)
```

#### 方式三：目录扫描

```python
strategy_registry.scan_directory("./strategies", recursive=True)
```

### 策略元数据

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| strategy_id | str | 是 | 策略唯一标识 |
| name | str | 是 | 策略名称 |
| version | str | 否 | 版本号，默认 "1.0.0" |
| author | str | 否 | 作者 |
| description | str | 否 | 描述 |
| category | str | 否 | 分类，默认 "general" |
| frequency | Enum | 否 | 运行频率 |
| status | Enum | 否 | 生命周期状态 |
| tags | List[str] | 否 | 标签 |
| params_schema | Dict | 否 | 参数 JSON Schema |
| default_params | Dict | 否 | 默认参数 |
| min_history_bars | int | 否 | 最小历史 K 线数量 |
| supported_markets | List[str] | 否 | 支持的市场 |
| risk_level | str | 否 | 风险等级 |

### 生命周期状态

| 状态 | 值 | 说明 |
|------|-----|------|
| DEVELOPMENT | development | 开发中 |
| TESTING | testing | 测试中 |
| BACKTEST_PASSED | backtest_passed | 回测通过 |
| PAPER_TRADING | paper_trading | 模拟交易 |
| LIVE_TRADING | live_trading | 实盘交易 |
| DEPRECATED | deprecated | 已废弃 |
| SUSPENDED | suspended | 已暂停 |

---

## 策略基类

### 生命周期方法

```python
class StrategyBase(ABC):
    # 必须实现
    @abstractmethod
    def initialize(self, context) -> None:
        """初始化策略"""
        pass

    @abstractmethod
    def on_data(self, context) -> Optional[List[Signal]]:
        """处理数据生成信号"""
        pass

    @abstractmethod
    def finalize(self, context) -> None:
        """策略结束"""
        pass

    # 可选重写
    def on_bar_close(self, context) -> Optional[List[Signal]]:
        """K 线闭合处理"""
        return None

    def on_order_status(self, order, old_status, new_status) -> None:
        """订单状态变化回调"""
        pass

    def on_trade(self, trade, order) -> None:
        """成交回调"""
        pass

    def on_timer(self, context) -> Optional[List[Signal]]:
        """定时器回调"""
        return None

    def on_error(self, error, context=None) -> None:
        """错误处理"""
        pass
```

### 参数管理

```python
# 获取参数
value = self.get_parameter("period", default=20)

# 设置参数
self.set_parameter("period", 30)

# 热更新参数
success = self.update_parameters({"period": 25})

# 添加参数变更回调
def on_params_changed(old_params, new_params):
    self.log_info(f"参数已更新: {new_params}")

self.add_params_changed_callback(on_params_changed)
```

### 状态管理

```python
# 获取策略状态
state = self.get_state()

# 保存状态（用于持久化）
saved_state = self.save_state()

# 加载状态
self.load_state(saved_state)

# 内部状态
self.set_internal_state("key", value)
value = self.get_internal_state("key", default=None)
```

---

## 隔离上下文

### 持仓管理

```python
# 获取持仓
position = context.get_position("000001.SZ")

# 检查是否有持仓
has_pos = context.has_position("000001.SZ")

# 获取持仓数量
qty = context.get_position_quantity("000001.SZ")

# 获取所有持仓
all_positions = context.get_all_positions()
```

### 订单管理

```python
from decimal import Decimal

# 买入
order = context.buy(
    symbol="000001.SZ",
    quantity=1000,
    price=Decimal("10.0"),
    order_type="LIMIT",  # 或 "MARKET"
    reason="金叉买入"
)

# 卖出
order = context.sell(
    symbol="000001.SZ",
    quantity=500,
    price=Decimal("12.0"),
)

# 平仓
order = context.close_position("000001.SZ")

# 撤销订单
context.cancel_order(order.order_id)
```

### 资金和盈亏

```python
# 可用资金
cash = context.cash

# 总资产
total = context.total_value

# 总盈亏
pnl = context.profit_loss

# 收益率
pnl_pct = context.profit_loss_pct
```

### 数据访问

```python
# 获取历史数据
history = context.get_history("000001.SZ", length=100)

# 获取最新 K 线
latest = context.get_latest_bar("000001.SZ")

# 获取当前价格
price = context.get_current_price("000001.SZ")
```

---

## 数据引擎

### 使用数据引擎

```python
from src.services.data.engine import (
    DataEngine,
    DataRequest,
    DataType,
    DataFrequency,
    AdjustmentType,
)
from datetime import date

# 创建数据引擎
engine = DataEngine()

# 注册适配器（示例）
from src.services.data.adapters import AkShareAdapter
engine.register_adapter("akshare", AkShareAdapter())

# 创建数据请求
request = DataRequest(
    symbols=["000001.SZ", "600000.SH"],
    data_type=DataType.STOCK_PRICE,
    frequency=DataFrequency.DAY,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    adjustment=AdjustmentType.FORWARD,
)

# 获取数据
data = await engine.get_data(request)

# 获取最新行情
quotes = await engine.get_latest(["000001.SZ", "600000.SH"])

# 订阅实时数据
async for bar in engine.subscribe(["000001.SZ"]):
    print(f"收到数据: {bar.symbol} @ {bar.close}")
```

### 数据类型

| 类型 | 值 | 说明 |
|------|-----|------|
| STOCK_INFO | stock_info | 股票信息 |
| STOCK_PRICE | stock_price | 股票价格 |
| STOCK_MINUTE | stock_minute | 分钟数据 |
| STOCK_TICK | stock_tick | Tick 数据 |
| INDEX | index | 指数数据 |
| FUNDAMENTAL | fundamental | 基本面数据 |
| CORPORATE_ACTION | corp_action | 公司行动 |

### 复权方式

| 方式 | 值 | 说明 |
|------|-----|------|
| NONE | none | 不复权 |
| FORWARD | qfq | 前复权 |
| BACKWARD | hfq | 后复权 |

---

## API 参考

### 策略注册表 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/strategy-registry/ | 获取策略列表 |
| GET | /api/v1/strategy-registry/{id} | 获取策略详情 |
| PUT | /api/v1/strategy-registry/{id}/status | 更新策略状态 |
| POST | /api/v1/strategy-registry/scan | 扫描目录注册策略 |
| GET | /api/v1/strategy-registry/registry/status | 获取注册表状态 |
| GET | /api/v1/strategy-registry/registry/categories | 获取分类列表 |
| GET | /api/v1/strategy-registry/registry/tags | 获取标签列表 |
| GET | /api/v1/strategy-registry/by-status/{status} | 按状态获取策略 |
| POST | /api/v1/strategy-registry/instances | 创建策略实例 |
| GET | /api/v1/strategy-registry/instances/ | 获取实例列表 |
| GET | /api/v1/strategy-registry/instances/{id} | 获取实例详情 |
| DELETE | /api/v1/strategy-registry/instances/{id} | 移除实例 |

### 数据引擎 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/data-engine/fetch | 获取历史数据 |
| POST | /api/v1/data-engine/latest | 获取最新行情 |
| GET | /api/v1/data-engine/quote/{symbol} | 获取单股行情 |
| GET | /api/v1/data-engine/adapters | 获取适配器列表 |
| POST | /api/v1/data-engine/adapters/connect | 连接所有适配器 |
| POST | /api/v1/data-engine/subscribe | 订阅实时数据 |
| DELETE | /api/v1/data-engine/subscribe/{id} | 取消订阅 |
| DELETE | /api/v1/data-engine/cache | 清除缓存 |
| GET | /api/v1/data-engine/status | 获取引擎状态 |

---

## 最佳实践

### 1. 参数验证

```python
def validate_parameters(self) -> tuple[bool, Optional[str]]:
    """验证参数有效性"""
    period = self.parameters.get("period", 20)

    if period < 5:
        return False, "周期必须 >= 5"

    if period > 200:
        return False, "周期不能超过 200"

    return True, None
```

### 2. 状态持久化

```python
def save_state(self) -> Dict[str, Any]:
    """保存状态"""
    return {
        "parameters": self.parameters.copy(),
        "internal_state": {
            "price_history": self._price_history[-100:],  # 只保留最近100条
            "signals_count": self._signals_count,
        }
    }

def load_state(self, state: Dict[str, Any]) -> None:
    """加载状态"""
    self.parameters = state.get("parameters", {})
    internal = state.get("internal_state", {})
    self._price_history = internal.get("price_history", [])
    self._signals_count = internal.get("signals_count", 0)
```

### 3. 错误处理

```python
def on_error(self, error: Exception, context=None) -> None:
    """错误处理"""
    self.log_error(f"策略错误: {error}")

    # 发送告警
    if self.parameters.get("alert_on_error", True):
        # ... 发送告警逻辑
        pass

    # 根据错误类型决定是否停止
    if isinstance(error, DataError):
        # 数据错误，可以暂停等待
        pass
    elif isinstance(error, TradingError):
        # 交易错误，需要立即停止
        self.status = StrategyStatus.ERROR
```

### 4. 日志规范

```python
# 使用内置日志方法
self.log_info("策略初始化完成")
self.log_warning("数据延迟超过阈值")
self.log_error("订单执行失败")
self.log_debug("当前持仓: " + str(position))
```

### 5. 信号生成

```python
def on_data(self, context) -> Optional[List[Signal]]:
    """生成信号时包含完整信息"""
    signals = []

    if buy_condition:
        signal = Signal(
            symbol="000001.SZ",
            signal_type=SignalType.BUY,
            timestamp=context.current_time,
            price=float(current_price),
            quantity=calculated_quantity,
            confidence=0.8,  # 信号置信度
            reason=f"金叉买入: MA5({ma5:.2f}) > MA20({ma20:.2f})",
            metadata={  # 额外元数据
                "ma5": float(ma5),
                "ma20": float(ma20),
                "volume_ratio": volume_ratio,
            }
        )
        signals.append(signal)

    return signals if signals else None
```

---

## 常见问题

### Q: 如何在同一策略类上创建多个实例？

```python
# 使用不同参数创建多个实例
instance1 = strategy_registry.create_instance(
    strategy_id="dual_ma_cross",
    instance_id="instance_1",
    params={"short_period": 5, "long_period": 20},
)

instance2 = strategy_registry.create_instance(
    strategy_id="dual_ma_cross",
    instance_id="instance_2",
    params={"short_period": 10, "long_period": 50},
)
```

### Q: 如何动态更新策略参数？

```python
# 方式一：直接更新
success = strategy.update_parameters({"period": 30})

# 方式二：通过 API
# PUT /api/v1/strategy-registry/instances/{instance_id}/params
```

### Q: 如何访问历史数据？

```python
# 通过上下文访问
history = context.get_history("000001.SZ", length=100)

# 通过数据引擎访问
from src.services.data.engine import DataEngine, DataRequest

engine = DataEngine()
data = await engine.get_data(DataRequest(
    symbols=["000001.SZ"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
))
```

---

## 更新日志

### v2.0.0 (2026-03-10)
- 全新的策略注册表架构
- 装饰器注册支持
- 隔离上下文
- 统一数据引擎
- REST API 端点
- 前端集成

### v1.0.0 (2026-03-01)
- 初始版本

---

**维护者**: QuantDev Team
**最后更新**: 2026-03-10
