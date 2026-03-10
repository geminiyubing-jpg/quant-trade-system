"""
策略隔离上下文模块

为每个策略实例提供独立的运行环境，包括：
- 独立的持仓管理
- 独立的资金账户
- 独立的订单管理
- 数据访问接口
- 技术指标计算

设计目标：
- 防止策略间的状态污染
- 支持同一策略多实例并行运行
- 提供统一的数据和交易接口
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


# ==============================================
# 数据类定义
# ==============================================

@dataclass
class Position:
    """
    持仓信息

    记录单个标的的持仓详情。
    """
    symbol: str                           # 股票代码
    quantity: int                         # 持仓数量
    avg_cost: Decimal                     # 平均成本
    current_price: Decimal = Decimal("0") # 当前价格
    market_value: Decimal = Decimal("0")  # 市值
    profit_loss: Decimal = Decimal("0")   # 浮动盈亏
    profit_loss_pct: Decimal = Decimal("0")  # 盈亏比例
    available: int = 0                    # 可用数量（T+1 考虑）
    frozen: int = 0                       # 冻结数量
    updated_at: datetime = None           # 更新时间

    def __post_init__(self):
        """初始化后计算市值和盈亏"""
        self._calculate()

    def _calculate(self):
        """计算市值和盈亏"""
        self.market_value = self.current_price * self.quantity
        if self.quantity > 0 and self.avg_cost > 0:
            cost_basis = self.avg_cost * self.quantity
            self.profit_loss = self.market_value - cost_basis
            self.profit_loss_pct = self.profit_loss / cost_basis if cost_basis > 0 else Decimal("0")
        else:
            self.profit_loss = Decimal("0")
            self.profit_loss_pct = Decimal("0")

    def update_price(self, price: Decimal):
        """更新当前价格"""
        self.current_price = price
        self.updated_at = datetime.now()
        self._calculate()

    def add_quantity(self, quantity: int, price: Decimal):
        """增加持仓"""
        if quantity <= 0:
            return

        total_cost = self.avg_cost * self.quantity + price * quantity
        self.quantity += quantity
        if self.quantity > 0:
            self.avg_cost = total_cost / self.quantity
        self.updated_at = datetime.now()
        self._calculate()

    def reduce_quantity(self, quantity: int) -> bool:
        """减少持仓"""
        if quantity <= 0 or quantity > self.quantity:
            return False

        self.quantity -= quantity
        if self.quantity == 0:
            self.avg_cost = Decimal("0")
        self.updated_at = datetime.now()
        self._calculate()
        return True


@dataclass
class Order:
    """
    订单信息

    记录订单的完整生命周期。
    """
    order_id: str                          # 订单 ID
    symbol: str                            # 股票代码
    side: str                              # 买卖方向（BUY/SELL）
    order_type: str = "LIMIT"              # 订单类型（LIMIT/MARKET）
    quantity: int = 0                      # 委托数量
    price: Decimal = Decimal("0")          # 委托价格
    filled_quantity: int = 0               # 成交数量
    filled_price: Decimal = Decimal("0")   # 成交均价
    status: str = "PENDING"                # 订单状态
    created_at: datetime = None            # 创建时间
    updated_at: datetime = None            # 更新时间
    strategy_id: str = ""                  # 关联策略 ID
    reason: str = ""                       # 下单原因
    commission: Decimal = Decimal("0")     # 佣金
    slippage: Decimal = Decimal("0")       # 滑点

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def is_active(self) -> bool:
        """订单是否仍然活跃"""
        return self.status in ["PENDING", "SUBMITTED", "PARTIAL_FILLED"]

    @property
    def is_complete(self) -> bool:
        """订单是否已完成"""
        return self.status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]

    @property
    def unfilled_quantity(self) -> int:
        """未成交数量"""
        return self.quantity - self.filled_quantity


@dataclass
class Trade:
    """
    成交记录

    记录单笔成交的详细信息。
    """
    trade_id: str                          # 成交 ID
    order_id: str                          # 关联订单 ID
    symbol: str                            # 股票代码
    side: str                              # 买卖方向
    quantity: int                          # 成交数量
    price: Decimal                         # 成交价格
    timestamp: datetime                    # 成交时间
    commission: Decimal = Decimal("0")     # 佣金
    slippage: Decimal = Decimal("0")       # 滑点
    strategy_id: str = ""                  # 关联策略 ID


# ==============================================
# 指标管理器
# ==============================================

class IndicatorManager:
    """
    技术指标管理器

    管理策略使用的技术指标，支持缓存和自动更新。
    """

    def __init__(self):
        self._indicators: Dict[str, Dict[str, Any]] = {}  # {symbol: {indicator_name: value}}
        self._indicator_funcs: Dict[str, Callable] = {}    # 指标计算函数

    def register_indicator(self, name: str, func: Callable):
        """
        注册指标计算函数

        Args:
            name: 指标名称
            func: 计算函数，签名: func(data: pd.DataFrame) -> Any
        """
        self._indicator_funcs[name] = func

    def calculate(self, name: str, data: Any) -> Any:
        """
        计算指标

        Args:
            name: 指标名称
            data: 输入数据

        Returns:
            指标值
        """
        if name not in self._indicator_funcs:
            raise ValueError(f"指标 {name} 未注册")

        return self._indicator_funcs[name](data)

    def get(self, symbol: str, name: str, default: Any = None) -> Any:
        """
        获取缓存的指标值

        Args:
            symbol: 股票代码
            name: 指标名称
            default: 默认值

        Returns:
            指标值
        """
        return self._indicators.get(symbol, {}).get(name, default)

    def set(self, symbol: str, name: str, value: Any):
        """
        设置指标值

        Args:
            symbol: 股票代码
            name: 指标名称
            value: 指标值
        """
        if symbol not in self._indicators:
            self._indicators[symbol] = {}
        self._indicators[symbol][name] = value

    def clear(self, symbol: str = None):
        """
        清除指标缓存

        Args:
            symbol: 股票代码（如果为 None 则清除所有）
        """
        if symbol is None:
            self._indicators.clear()
        elif symbol in self._indicators:
            del self._indicators[symbol]


# ==============================================
# 数据提供者接口
# ==============================================

class DataProvider:
    """
    数据提供者接口

    提供历史数据和实时数据访问接口。
    """

    def __init__(self):
        self._history_data: Dict[str, List[Dict]] = {}  # {symbol: [bar_data]}

    def set_history_data(self, symbol: str, data: List[Dict]):
        """
        设置历史数据

        Args:
            symbol: 股票代码
            data: 历史数据列表
        """
        self._history_data[symbol] = data

    def get_history(
        self,
        symbol: str,
        length: int = 100,
        fields: List[str] = None
    ) -> List[Dict]:
        """
        获取历史数据

        Args:
            symbol: 股票代码
            length: 数据长度
            fields: 需要的字段

        Returns:
            历史数据列表
        """
        data = self._history_data.get(symbol, [])
        if length > 0:
            data = data[-length:]

        if fields:
            return [{k: v for k, v in bar.items() if k in fields} for bar in data]
        return data

    def get_latest_bar(self, symbol: str) -> Optional[Dict]:
        """
        获取最新一根 K 线

        Args:
            symbol: 股票代码

        Returns:
            K 线数据或 None
        """
        data = self._history_data.get(symbol, [])
        return data[-1] if data else None

    def get_symbols(self) -> List[str]:
        """获取所有有数据的股票代码"""
        return list(self._history_data.keys())


# ==============================================
# 隔离上下文
# ==============================================

class IsolatedStrategyContext:
    """
    隔离策略上下文

    为每个策略实例提供独立的运行环境。

    特性：
    - 独立的持仓管理
    - 独立的资金账户
    - 独立的订单管理
    - 数据访问接口
    - 指标管理

    使用方式：
        context = IsolatedStrategyContext(
            strategy_id="ma_cross_1",
            config=strategy_config
        )

        # 获取持仓
        position = context.get_position("000001.SZ")

        # 下单
        order = context.buy("000001.SZ", 100, Decimal("10.0"))

        # 获取历史数据
        history = context.get_history("000001.SZ", 50)
    """

    def __init__(
        self,
        strategy_id: str,
        config: 'StrategyConfig',
        data_provider: DataProvider = None,
    ):
        """
        初始化隔离上下文

        Args:
            strategy_id: 策略实例 ID
            config: 策略配置
            data_provider: 数据提供者（可选）
        """
        self.strategy_id = strategy_id
        self.config = config

        # 独立状态
        self._positions: Dict[str, Position] = {}
        self._cash: Decimal = Decimal(str(config.initial_capital))
        self._initial_capital: Decimal = Decimal(str(config.initial_capital))
        self._pending_orders: Dict[str, Order] = {}
        self._completed_orders: Dict[str, Order] = {}
        self._trades: List[Trade] = []

        # 数据和指标
        self._data_provider: DataProvider = data_provider or DataProvider()
        self._indicators: IndicatorManager = IndicatorManager()

        # 自定义数据存储
        self._custom_data: Dict[str, Any] = {}

        # 当前时间
        self._current_time: datetime = datetime.now()
        self._current_prices: Dict[str, Decimal] = {}

        # 回调函数
        self._on_order_callback: Optional[Callable] = None
        self._on_trade_callback: Optional[Callable] = None

        # 日志
        self.logger = logging.getLogger(f"Context.{strategy_id}")

    # ==========================================
    # 属性
    # ==========================================

    @property
    def cash(self) -> Decimal:
        """可用资金"""
        return self._cash

    @property
    def initial_capital(self) -> Decimal:
        """初始资金"""
        return self._initial_capital

    @property
    def total_value(self) -> Decimal:
        """总资产（现金 + 持仓市值）"""
        positions_value = sum(
            pos.market_value for pos in self._positions.values()
        )
        return self._cash + positions_value

    @property
    def profit_loss(self) -> Decimal:
        """总盈亏"""
        return self.total_value - self._initial_capital

    @property
    def profit_loss_pct(self) -> Decimal:
        """总收益率"""
        if self._initial_capital > 0:
            return self.profit_loss / self._initial_capital
        return Decimal("0")

    @property
    def current_time(self) -> datetime:
        """当前时间"""
        return self._current_time

    @property
    def positions(self) -> Dict[str, Position]:
        """所有持仓"""
        return self._positions.copy()

    @property
    def pending_orders(self) -> Dict[str, Order]:
        """待处理订单"""
        return self._pending_orders.copy()

    @property
    def trades(self) -> List[Trade]:
        """所有成交记录"""
        return self._trades.copy()

    # ==========================================
    # 时间管理
    # ==========================================

    def set_current_time(self, time: datetime):
        """
        设置当前时间

        Args:
            time: 当前时间
        """
        self._current_time = time

    def update_current_price(self, symbol: str, price: Decimal):
        """
        更新当前价格

        Args:
            symbol: 股票代码
            price: 当前价格
        """
        self._current_prices[symbol] = price

        # 更新持仓价格
        if symbol in self._positions:
            self._positions[symbol].update_price(price)

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        获取当前价格

        Args:
            symbol: 股票代码

        Returns:
            当前价格或 None
        """
        return self._current_prices.get(symbol)

    # ==========================================
    # 持仓管理
    # ==========================================

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        获取持仓

        Args:
            symbol: 股票代码

        Returns:
            持仓信息或 None
        """
        return self._positions.get(symbol)

    def get_all_positions(self) -> List[Position]:
        """
        获取所有持仓

        Returns:
            持仓列表
        """
        return list(self._positions.values())

    def has_position(self, symbol: str) -> bool:
        """
        是否持有指定标的

        Args:
            symbol: 股票代码

        Returns:
            是否持有
        """
        position = self._positions.get(symbol)
        return position is not None and position.quantity > 0

    def get_position_quantity(self, symbol: str) -> int:
        """
        获取持仓数量

        Args:
            symbol: 股票代码

        Returns:
            持仓数量
        """
        position = self._positions.get(symbol)
        return position.quantity if position else 0

    # ==========================================
    # 订单管理
    # ==========================================

    def buy(
        self,
        symbol: str,
        quantity: int,
        price: Decimal = None,
        order_type: str = "LIMIT",
        reason: str = "",
    ) -> Order:
        """
        买入

        Args:
            symbol: 股票代码
            quantity: 数量
            price: 价格（市价单可省略）
            order_type: 订单类型（LIMIT/MARKET）
            reason: 下单原因

        Returns:
            订单对象
        """
        if price is None:
            price = self._current_prices.get(symbol, Decimal("0"))
            order_type = "MARKET"

        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side="BUY",
            order_type=order_type,
            quantity=quantity,
            price=price,
            strategy_id=self.strategy_id,
            reason=reason,
            status="PENDING",
        )

        self._pending_orders[order.order_id] = order

        self.logger.info(
            f"创建买入订单: {order.order_id} {symbol} {quantity}@{price}"
        )

        if self._on_order_callback:
            self._on_order_callback(order)

        return order

    def sell(
        self,
        symbol: str,
        quantity: int,
        price: Decimal = None,
        order_type: str = "LIMIT",
        reason: str = "",
    ) -> Order:
        """
        卖出

        Args:
            symbol: 股票代码
            quantity: 数量
            price: 价格（市价单可省略）
            order_type: 订单类型（LIMIT/MARKET）
            reason: 下单原因

        Returns:
            订单对象
        """
        if price is None:
            price = self._current_prices.get(symbol, Decimal("0"))
            order_type = "MARKET"

        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side="SELL",
            order_type=order_type,
            quantity=quantity,
            price=price,
            strategy_id=self.strategy_id,
            reason=reason,
            status="PENDING",
        )

        self._pending_orders[order.order_id] = order

        self.logger.info(
            f"创建卖出订单: {order.order_id} {symbol} {quantity}@{price}"
        )

        if self._on_order_callback:
            self._on_order_callback(order)

        return order

    def close_position(
        self,
        symbol: str,
        price: Decimal = None,
        order_type: str = "MARKET",
        reason: str = "平仓",
    ) -> Optional[Order]:
        """
        平仓

        Args:
            symbol: 股票代码
            price: 价格
            order_type: 订单类型
            reason: 原因

        Returns:
            订单对象或 None
        """
        position = self._positions.get(symbol)
        if position is None or position.quantity <= 0:
            return None

        return self.sell(
            symbol=symbol,
            quantity=position.quantity,
            price=price,
            order_type=order_type,
            reason=reason,
        )

    def cancel_order(self, order_id: str) -> bool:
        """
        撤销订单

        Args:
            order_id: 订单 ID

        Returns:
            是否成功
        """
        if order_id in self._pending_orders:
            order = self._pending_orders.pop(order_id)
            order.status = "CANCELED"
            order.updated_at = datetime.now()
            self._completed_orders[order_id] = order

            self.logger.info(f"撤销订单: {order_id}")

            if self._on_order_callback:
                self._on_order_callback(order)

            return True
        return False

    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取订单

        Args:
            order_id: 订单 ID

        Returns:
            订单对象或 None
        """
        return self._pending_orders.get(order_id) or self._completed_orders.get(order_id)

    # ==========================================
    # 成交处理
    # ==========================================

    def process_fill(
        self,
        order_id: str,
        filled_quantity: int,
        filled_price: Decimal,
        commission: Decimal = Decimal("0"),
        slippage: Decimal = Decimal("0"),
    ) -> Optional[Trade]:
        """
        处理成交

        Args:
            order_id: 订单 ID
            filled_quantity: 成交数量
            filled_price: 成交价格
            commission: 佣金
            slippage: 滑点

        Returns:
            成交记录或 None
        """
        order = self._pending_orders.get(order_id)
        if order is None:
            return None

        # 更新订单状态
        order.filled_quantity += filled_quantity
        # 计算加权平均成交价
        if order.filled_quantity > 0:
            total_filled_value = order.filled_price * (order.filled_quantity - filled_quantity) + filled_price * filled_quantity
            order.filled_price = total_filled_value / order.filled_quantity

        order.commission += commission
        order.slippage += slippage
        order.updated_at = datetime.now()

        if order.filled_quantity >= order.quantity:
            order.status = "FILLED"
            self._completed_orders[order_id] = order
            del self._pending_orders[order_id]
        else:
            order.status = "PARTIAL_FILLED"

        # 创建成交记录
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=filled_quantity,
            price=filled_price,
            timestamp=datetime.now(),
            commission=commission,
            slippage=slippage,
            strategy_id=self.strategy_id,
        )
        self._trades.append(trade)

        # 更新持仓和资金
        self._process_trade_impact(trade, order)

        self.logger.info(
            f"成交: {trade.trade_id} {order.symbol} {order.side} "
            f"{filled_quantity}@{filled_price}"
        )

        if self._on_trade_callback:
            self._on_trade_callback(trade)

        return trade

    def _process_trade_impact(self, trade: Trade, order: Order):
        """处理成交对持仓和资金的影响"""
        symbol = trade.symbol

        if trade.side == "BUY":
            # 买入：扣除资金，增加持仓
            trade_value = trade.price * trade.quantity
            total_cost = trade_value + trade.commission + trade.slippage

            self._cash -= total_cost

            if symbol not in self._positions:
                self._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=trade.quantity,
                    avg_cost=trade.price,
                    current_price=trade.price,
                )
            else:
                self._positions[symbol].add_quantity(trade.quantity, trade.price)

        else:  # SELL
            # 卖出：增加资金，减少持仓
            trade_value = trade.price * trade.quantity
            net_proceeds = trade_value - trade.commission - trade.slippage

            self._cash += net_proceeds

            if symbol in self._positions:
                self._positions[symbol].reduce_quantity(trade.quantity)
                if self._positions[symbol].quantity == 0:
                    del self._positions[symbol]

    # ==========================================
    # 数据访问
    # ==========================================

    def get_history(
        self,
        symbol: str,
        length: int = 100,
        fields: List[str] = None
    ) -> List[Dict]:
        """
        获取历史数据

        Args:
            symbol: 股票代码
            length: 数据长度
            fields: 需要的字段

        Returns:
            历史数据列表
        """
        return self._data_provider.get_history(symbol, length, fields)

    def get_latest_bar(self, symbol: str) -> Optional[Dict]:
        """
        获取最新 K 线

        Args:
            symbol: 股票代码

        Returns:
            K 线数据或 None
        """
        return self._data_provider.get_latest_bar(symbol)

    def set_data_provider(self, provider: DataProvider):
        """
        设置数据提供者

        Args:
            provider: 数据提供者
        """
        self._data_provider = provider

    # ==========================================
    # 指标管理
    # ==========================================

    def get_indicator(self, symbol: str, name: str, default: Any = None) -> Any:
        """
        获取指标值

        Args:
            symbol: 股票代码
            name: 指标名称
            default: 默认值

        Returns:
            指标值
        """
        return self._indicators.get(symbol, name, default)

    def set_indicator(self, symbol: str, name: str, value: Any):
        """
        设置指标值

        Args:
            symbol: 股票代码
            name: 指标名称
            value: 指标值
        """
        self._indicators.set(symbol, name, value)

    def calculate_indicator(self, name: str, data: Any) -> Any:
        """
        计算指标

        Args:
            name: 指标名称
            data: 输入数据

        Returns:
            指标值
        """
        return self._indicators.calculate(name, data)

    def register_indicator_func(self, name: str, func: Callable):
        """
        注册指标计算函数

        Args:
            name: 指标名称
            func: 计算函数
        """
        self._indicators.register_indicator(name, func)

    # ==========================================
    # 自定义数据存储
    # ==========================================

    def set_custom_data(self, key: str, value: Any):
        """
        设置自定义数据

        Args:
            key: 键
            value: 值
        """
        self._custom_data[key] = value

    def get_custom_data(self, key: str, default: Any = None) -> Any:
        """
        获取自定义数据

        Args:
            key: 键
            default: 默认值

        Returns:
            值
        """
        return self._custom_data.get(key, default)

    def delete_custom_data(self, key: str) -> bool:
        """
        删除自定义数据

        Args:
            key: 键

        Returns:
            是否成功
        """
        if key in self._custom_data:
            del self._custom_data[key]
            return True
        return False

    # ==========================================
    # 回调设置
    # ==========================================

    def set_order_callback(self, callback: Callable[[Order], None]):
        """
        设置订单回调

        Args:
            callback: 回调函数
        """
        self._on_order_callback = callback

    def set_trade_callback(self, callback: Callable[[Trade], None]):
        """
        设置成交回调

        Args:
            callback: 回调函数
        """
        self._on_trade_callback = callback

    # ==========================================
    # 状态管理
    # ==========================================

    def save_state(self) -> Dict[str, Any]:
        """
        保存上下文状态

        Returns:
            状态字典
        """
        return {
            "strategy_id": self.strategy_id,
            "cash": str(self._cash),
            "initial_capital": str(self._initial_capital),
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "avg_cost": str(pos.avg_cost),
                    "current_price": str(pos.current_price),
                }
                for symbol, pos in self._positions.items()
            },
            "custom_data": self._custom_data,
            "current_time": self._current_time.isoformat() if self._current_time else None,
        }

    def load_state(self, state: Dict[str, Any]):
        """
        加载上下文状态

        Args:
            state: 状态字典
        """
        self._cash = Decimal(state.get("cash", "0"))
        self._initial_capital = Decimal(state.get("initial_capital", "0"))

        positions_data = state.get("positions", {})
        self._positions.clear()
        for symbol, pos_data in positions_data.items():
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=pos_data["quantity"],
                avg_cost=Decimal(pos_data["avg_cost"]),
                current_price=Decimal(pos_data["current_price"]),
            )

        self._custom_data = state.get("custom_data", {})

        if state.get("current_time"):
            self._current_time = datetime.fromisoformat(state["current_time"])

    def reset(self):
        """重置上下文状态"""
        self._positions.clear()
        self._cash = self._initial_capital
        self._pending_orders.clear()
        self._completed_orders.clear()
        self._trades.clear()
        self._custom_data.clear()
        self._indicators.clear()

        self.logger.info(f"上下文已重置: {self.strategy_id}")

    def get_summary(self) -> Dict[str, Any]:
        """
        获取上下文摘要

        Returns:
            摘要字典
        """
        return {
            "strategy_id": self.strategy_id,
            "cash": str(self._cash),
            "total_value": str(self.total_value),
            "profit_loss": str(self.profit_loss),
            "profit_loss_pct": f"{float(self.profit_loss_pct) * 100:.2f}%",
            "positions_count": len(self._positions),
            "pending_orders_count": len(self._pending_orders),
            "trades_count": len(self._trades),
            "current_time": self._current_time.isoformat() if self._current_time else None,
        }
