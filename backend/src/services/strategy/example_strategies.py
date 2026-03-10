"""
增强版示例策略

使用新的策略注册表架构实现的示例策略。
展示装饰器注册、参数验证、状态管理等高级特性。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import logging

from .base import (
    StrategyBase,
    StrategyConfig,
    Signal,
    SignalType,
    StrategyContext,
)
from .context import IsolatedStrategyContext, Order, Trade
from .registry import strategy, StrategyFrequency, StrategyLifecycleStatus


# ==============================================
# 双均线策略
# ==============================================

@strategy(
    strategy_id="dual_ma_cross",
    name="双均线交叉策略",
    version="2.0.0",
    author="QuantDev Team",
    description="""
    经典的双均线交叉趋势跟踪策略。

    信号逻辑：
    - 金叉买入：短期均线上穿长期均线
    - 死叉卖出：短期均线下穿长期均线

    参数说明：
    - short_period: 短期均线周期（默认 5）
    - long_period: 长期均线周期（默认 20）
    - ma_type: 均线类型（SMA/EMA，默认 SMA）
    """,
    category="trend",
    frequency=StrategyFrequency.DAILY,
    tags=["均线", "趋势跟踪", "经典策略"],
    params_schema={
        "type": "object",
        "properties": {
            "short_period": {
                "type": "integer",
                "minimum": 2,
                "maximum": 50,
                "description": "短期均线周期"
            },
            "long_period": {
                "type": "integer",
                "minimum": 5,
                "maximum": 200,
                "description": "长期均线周期"
            },
            "ma_type": {
                "type": "string",
                "enum": ["SMA", "EMA"],
                "description": "均线类型"
            },
            "position_pct": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 1.0,
                "description": "仓位比例"
            }
        },
        "required": ["short_period", "long_period"]
    },
    default_params={
        "short_period": 5,
        "long_period": 20,
        "ma_type": "SMA",
        "position_pct": 0.95,
    },
    min_history_bars=30,
    risk_level="medium",
)
class DualMACrossStrategy(StrategyBase):
    """
    双均线交叉策略（增强版）

    特性：
    - 支持 SMA 和 EMA 两种均线类型
    - 可配置仓位比例
    - 完整的参数验证
    - 状态持久化支持
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)

        # 策略参数
        self.short_period = self.parameters.get("short_period", 5)
        self.long_period = self.parameters.get("long_period", 20)
        self.ma_type = self.parameters.get("ma_type", "SMA")
        self.position_pct = self.parameters.get("position_pct", 0.95)

        # 价格历史
        self._price_history: List[Decimal] = []

        # 均线历史（用于检测交叉）
        self._short_ma_history: List[Decimal] = []
        self._long_ma_history: List[Decimal] = []

        # 当前持仓状态
        self._has_position = False

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """验证参数有效性"""
        if self.short_period >= self.long_period:
            return False, "短期周期必须小于长期周期"

        if self.short_period < 2:
            return False, "短期周期必须 >= 2"

        if self.long_period < 5:
            return False, "长期周期必须 >= 5"

        if self.ma_type not in ["SMA", "EMA"]:
            return False, "均线类型必须是 SMA 或 EMA"

        if not (0 < self.position_pct <= 1):
            return False, "仓位比例必须在 (0, 1] 范围内"

        return True, None

    def initialize(self, context: IsolatedStrategyContext) -> None:
        """初始化策略"""
        self._price_history = []
        self._short_ma_history = []
        self._long_ma_history = []
        self._has_position = context.has_position(
            self.parameters.get("symbol", "")
        )

        self.log_info(
            f"初始化完成: 短期={self.short_period}, "
            f"长期={self.long_period}, 类型={self.ma_type}"
        )

    def _calculate_ma(self, prices: List[Decimal], period: int) -> Optional[Decimal]:
        """计算移动平均线"""
        if len(prices) < period:
            return None

        if self.ma_type == "SMA":
            return sum(prices[-period:]) / period
        else:  # EMA
            multiplier = Decimal("2") / (period + 1)
            ema = prices[0]
            for price in prices[1:]:
                ema = (price - ema) * multiplier + ema
            return ema

    def on_data(self, context: IsolatedStrategyContext) -> Optional[List[Signal]]:
        """处理数据并生成信号"""
        symbol = self.parameters.get("symbol", "")
        current_price = context.get_current_price(symbol)

        if current_price is None:
            return None

        # 更新价格历史
        self._price_history.append(current_price)

        # 计算均线
        short_ma = self._calculate_ma(self._price_history, self.short_period)
        long_ma = self._calculate_ma(self._price_history, self.long_period)

        if short_ma is None or long_ma is None:
            return None

        # 保存均线历史
        self._short_ma_history.append(short_ma)
        self._long_ma_history.append(long_ma)

        # 检测交叉（需要至少两根 K 线）
        signals = []

        if len(self._short_ma_history) >= 2:
            prev_short_ma = self._short_ma_history[-2]
            prev_long_ma = self._long_ma_history[-2]

            # 金叉检测
            if (prev_short_ma <= prev_long_ma and short_ma > long_ma
                and not self._has_position):
                # 计算买入数量
                buy_amount = context.cash * Decimal(str(self.position_pct))
                quantity = int(buy_amount / current_price / 100) * 100  # 整手

                if quantity > 0:
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        timestamp=context.current_time,
                        price=float(current_price),
                        quantity=quantity,
                        confidence=0.8,
                        reason=f"金叉买入: MA{self.short_period}({short_ma:.2f}) > MA{self.long_period}({long_ma:.2f})",
                        metadata={
                            "short_ma": float(short_ma),
                            "long_ma": float(long_ma),
                            "cross_type": "golden"
                        }
                    )
                    signals.append(signal)
                    self._has_position = True
                    self.log_info(f"金叉信号: {signal.reason}")

            # 死叉检测
            elif (prev_short_ma >= prev_long_ma and short_ma < long_ma
                  and self._has_position):
                position = context.get_position(symbol)
                if position and position.quantity > 0:
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        timestamp=context.current_time,
                        price=float(current_price),
                        quantity=position.quantity,
                        confidence=0.8,
                        reason=f"死叉卖出: MA{self.short_period}({short_ma:.2f}) < MA{self.long_period}({long_ma:.2f})",
                        metadata={
                            "short_ma": float(short_ma),
                            "long_ma": float(long_ma),
                            "cross_type": "death"
                        }
                    )
                    signals.append(signal)
                    self._has_position = False
                    self.log_info(f"死叉信号: {signal.reason}")

        return signals if signals else None

    def on_bar_close(self, context: IsolatedStrategyContext) -> Optional[List[Signal]]:
        """K 线闭合处理"""
        # 可以在这里添加收盘价确认后的逻辑
        return None

    def on_order_status(self, order: Order, old_status: str, new_status: str) -> None:
        """订单状态变化回调"""
        self.log_info(f"订单状态更新: {order.order_id} {old_status} -> {new_status}")

        if new_status == "REJECTED":
            # 订单被拒绝，重置持仓状态
            self._has_position = False
            self.log_warning(f"订单被拒绝: {order.reason}")

    def on_trade(self, trade: Trade, order: Order) -> None:
        """成交回调"""
        self.log_info(
            f"成交确认: {trade.symbol} {trade.side} "
            f"{trade.quantity}@{trade.price}"
        )

    def finalize(self, context: IsolatedStrategyContext) -> None:
        """策略结束"""
        summary = context.get_summary()
        self.log_info(
            f"策略结束: 总资产={summary['total_value']}, "
            f"收益率={summary['profit_loss_pct']}"
        )

    def save_state(self) -> Dict[str, Any]:
        """保存策略状态"""
        return {
            "parameters": self.parameters.copy(),
            "internal_state": {
                "price_history": [str(p) for p in self._price_history[-100:]],  # 只保留最近 100 条
                "short_ma_history": [str(m) for m in self._short_ma_history[-50:]],
                "long_ma_history": [str(m) for m in self._long_ma_history[-50:]],
                "has_position": self._has_position,
            }
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """加载策略状态"""
        internal = state.get("internal_state", {})
        self._price_history = [Decimal(p) for p in internal.get("price_history", [])]
        self._short_ma_history = [Decimal(m) for m in internal.get("short_ma_history", [])]
        self._long_ma_history = [Decimal(m) for m in internal.get("long_ma_history", [])]
        self._has_position = internal.get("has_position", False)


# ==============================================
# 布林带均值回归策略
# ==============================================

@strategy(
    strategy_id="bollinger_reversion",
    name="布林带均值回归策略",
    version="2.0.0",
    author="QuantDev Team",
    description="""
    基于布林带的均值回归策略。

    信号逻辑：
    - 触及下轨买入：价格跌破下轨（超卖）
    - 回归中轨卖出：价格回归到中轨附近
    - 触及上轨卖出：价格突破上轨（超买）时如有持仓则卖出

    参数说明：
    - period: 布林带周期（默认 20）
    - std_dev: 标准差倍数（默认 2.0）
    - exit_threshold: 离场阈值（默认 0.1，即 10% 距离中轨）
    """,
    category="mean_reversion",
    frequency=StrategyFrequency.DAILY,
    tags=["布林带", "均值回归", "震荡策略"],
    params_schema={
        "type": "object",
        "properties": {
            "period": {
                "type": "integer",
                "minimum": 5,
                "maximum": 50,
                "description": "布林带周期"
            },
            "std_dev": {
                "type": "number",
                "minimum": 0.5,
                "maximum": 3.0,
                "description": "标准差倍数"
            },
            "exit_threshold": {
                "type": "number",
                "minimum": 0,
                "maximum": 0.5,
                "description": "离场阈值（距中轨比例）"
            },
            "position_pct": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 1.0,
                "description": "仓位比例"
            }
        },
        "required": ["period", "std_dev"]
    },
    default_params={
        "period": 20,
        "std_dev": 2.0,
        "exit_threshold": 0.1,
        "position_pct": 0.95,
    },
    min_history_bars=25,
    risk_level="medium",
)
class BollingerReversionStrategy(StrategyBase):
    """
    布林带均值回归策略（增强版）

    特性：
    - 动态布林带计算
    - 可配置的离场阈值
    - 支持部分止盈止损
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)

        # 策略参数
        self.period = self.parameters.get("period", 20)
        self.std_dev = Decimal(str(self.parameters.get("std_dev", 2.0)))
        self.exit_threshold = Decimal(str(self.parameters.get("exit_threshold", 0.1)))
        self.position_pct = Decimal(str(self.parameters.get("position_pct", 0.95)))

        # 价格历史
        self._price_history: List[Decimal] = []

        # 布林带值
        self._upper: Optional[Decimal] = None
        self._middle: Optional[Decimal] = None
        self._lower: Optional[Decimal] = None

        # 入场价格（用于计算盈亏）
        self._entry_price: Optional[Decimal] = None

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """验证参数"""
        if self.period < 5:
            return False, "周期必须 >= 5"

        if self.std_dev < 0.5 or self.std_dev > 3:
            return False, "标准差倍数必须在 [0.5, 3] 范围内"

        return True, None

    def initialize(self, context: IsolatedStrategyContext) -> None:
        """初始化"""
        self._price_history = []
        self._upper = None
        self._middle = None
        self._lower = None
        self._entry_price = None

        self.log_info(
            f"初始化完成: 周期={self.period}, "
            f"标准差倍数={self.std_dev}"
        )

    def _calculate_bollinger(self) -> tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """计算布林带"""
        if len(self._price_history) < self.period:
            return None, None, None

        recent_prices = self._price_history[-self.period:]

        # 计算中轨（SMA）
        middle = sum(recent_prices) / self.period

        # 计算标准差
        variance = sum((p - middle) ** 2 for p in recent_prices) / self.period
        std = variance ** Decimal("0.5")

        # 计算上下轨
        upper = middle + self.std_dev * std
        lower = middle - self.std_dev * std

        return upper, middle, lower

    def on_data(self, context: IsolatedStrategyContext) -> Optional[List[Signal]]:
        """处理数据"""
        symbol = self.parameters.get("symbol", "")
        current_price = context.get_current_price(symbol)

        if current_price is None:
            return None

        # 更新价格历史
        self._price_history.append(current_price)

        # 计算布林带
        self._upper, self._middle, self._lower = self._calculate_bollinger()

        if self._upper is None or self._middle is None or self._lower is None:
            return None

        signals = []
        has_position = context.has_position(symbol)

        # 计算价格相对位置
        band_width = self._upper - self._lower
        if band_width > 0:
            price_position = (current_price - self._middle) / (band_width / 2)
        else:
            price_position = Decimal("0")

        # 超卖区域：触及或跌破下轨
        if current_price <= self._lower and not has_position:
            buy_amount = context.cash * self.position_pct
            quantity = int(buy_amount / current_price / 100) * 100

            if quantity > 0:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=context.current_time,
                    price=float(current_price),
                    quantity=quantity,
                    confidence=min(float(abs(price_position) / 2), 1.0),
                    reason=f"触及下轨买入: 价格={current_price:.2f}, 下轨={self._lower:.2f}",
                    metadata={
                        "upper": float(self._upper),
                        "middle": float(self._middle),
                        "lower": float(self._lower),
                        "price_position": float(price_position)
                    }
                )
                signals.append(signal)
                self._entry_price = current_price
                self.log_info(f"下轨买入信号: {signal.reason}")

        # 回归中轨：离场条件
        elif has_position and self._entry_price is not None:
            distance_to_middle = abs(current_price - self._middle) / self._middle

            # 回归到中轨附近
            if distance_to_middle <= self.exit_threshold:
                position = context.get_position(symbol)
                if position and position.quantity > 0:
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        timestamp=context.current_time,
                        price=float(current_price),
                        quantity=position.quantity,
                        confidence=0.9,
                        reason=f"回归中轨卖出: 价格={current_price:.2f}, 中轨={self._middle:.2f}",
                        metadata={
                            "entry_price": float(self._entry_price),
                            "profit_pct": float((current_price - self._entry_price) / self._entry_price * 100)
                        }
                    )
                    signals.append(signal)
                    self._entry_price = None
                    self.log_info(f"中轨卖出信号: {signal.reason}")

            # 突破上轨止损/止盈
            elif current_price >= self._upper:
                position = context.get_position(symbol)
                if position and position.quantity > 0:
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        timestamp=context.current_time,
                        price=float(current_price),
                        quantity=position.quantity,
                        confidence=0.7,
                        reason=f"突破上轨卖出: 价格={current_price:.2f}, 上轨={self._upper:.2f}",
                        metadata={
                            "entry_price": float(self._entry_price),
                            "profit_pct": float((current_price - self._entry_price) / self._entry_price * 100)
                        }
                    )
                    signals.append(signal)
                    self._entry_price = None
                    self.log_info(f"上轨卖出信号: {signal.reason}")

        return signals if signals else None

    def finalize(self, context: IsolatedStrategyContext) -> None:
        """策略结束"""
        summary = context.get_summary()
        self.log_info(
            f"策略结束: 总资产={summary['total_value']}, "
            f"收益率={summary['profit_loss_pct']}"
        )


# ==============================================
# 网格交易策略
# ==============================================

@strategy(
    strategy_id="grid_trading",
    name="网格交易策略",
    version="2.0.0",
    author="QuantDev Team",
    description="""
    经典的网格交易策略。

    在设定的价格区间内，按照固定的间隔挂单买卖，
    利用价格波动赚取差价。

    参数说明：
    - grid_count: 网格数量（默认 10）
    - grid_range: 网格范围（默认 0.1，即上下 10%）
    - base_position: 基础持仓比例（默认 0.5）
    """,
    category="market_making",
    frequency=StrategyFrequency.MIN_1,
    tags=["网格", "做市", "震荡策略"],
    params_schema={
        "type": "object",
        "properties": {
            "grid_count": {
                "type": "integer",
                "minimum": 5,
                "maximum": 50,
                "description": "网格数量"
            },
            "grid_range": {
                "type": "number",
                "minimum": 0.05,
                "maximum": 0.5,
                "description": "网格范围（上下比例）"
            },
            "base_position": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "基础持仓比例"
            }
        },
        "required": ["grid_count", "grid_range"]
    },
    default_params={
        "grid_count": 10,
        "grid_range": 0.1,
        "base_position": 0.5,
    },
    min_history_bars=1,
    risk_level="high",
)
class GridTradingStrategy(StrategyBase):
    """
    网格交易策略（增强版）

    特性：
    - 动态网格调整
    - 支持不对称网格
    - 自动再平衡
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)

        # 策略参数
        self.grid_count = self.parameters.get("grid_count", 10)
        self.grid_range = Decimal(str(self.parameters.get("grid_range", 0.1)))
        self.base_position = Decimal(str(self.parameters.get("base_position", 0.5)))

        # 网格状态
        self._grid_levels: List[Decimal] = []
        self._reference_price: Optional[Decimal] = None
        self._current_grid_index: int = 0

    def initialize(self, context: IsolatedStrategyContext) -> None:
        """初始化网格"""
        symbol = self.parameters.get("symbol", "")
        current_price = context.get_current_price(symbol)

        if current_price:
            self._reference_price = current_price
            self._setup_grid()

        self.log_info(
            f"初始化完成: 网格数={self.grid_count}, "
            f"范围=±{float(self.grid_range)*100}%"
        )

    def _setup_grid(self):
        """设置网格水平"""
        if self._reference_price is None:
            return

        upper = self._reference_price * (1 + self.grid_range)
        lower = self._reference_price * (1 - self.grid_range)
        step = (upper - lower) / (self.grid_count - 1)

        self._grid_levels = [lower + step * i for i in range(self.grid_count)]
        self.log_info(f"网格水平: {[f'{float(g):.2f}' for g in self._grid_levels[:5]]}...")

    def on_data(self, context: IsolatedStrategyContext) -> Optional[List[Signal]]:
        """处理数据"""
        symbol = self.parameters.get("symbol", "")
        current_price = context.get_current_price(symbol)

        if current_price is None:
            return None

        # 首次初始化
        if not self._grid_levels:
            self._reference_price = current_price
            self._setup_grid()

        # 找到当前价格所在的网格区间
        grid_index = 0
        for i, level in enumerate(self._grid_levels):
            if current_price >= level:
                grid_index = i

        signals = []

        # 价格向上穿越网格线 -> 卖出
        if grid_index < self._current_grid_index:
            position = context.get_position(symbol)
            if position and position.quantity > 0:
                sell_qty = position.quantity // (self.grid_count // 2)
                if sell_qty > 0:
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        timestamp=context.current_time,
                        price=float(current_price),
                        quantity=sell_qty,
                        confidence=0.7,
                        reason=f"网格卖出: 从网格{self._current_grid_index}到{grid_index}",
                    )
                    signals.append(signal)
                    self.log_info(f"网格卖出: {signal.reason}")

        # 价格向下穿越网格线 -> 买入
        elif grid_index > self._current_grid_index:
            buy_amount = context.cash / (self.grid_count // 2)
            quantity = int(buy_amount / current_price / 100) * 100
            if quantity > 0:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=context.current_time,
                    price=float(current_price),
                    quantity=quantity,
                    confidence=0.7,
                    reason=f"网格买入: 从网格{self._current_grid_index}到{grid_index}",
                )
                signals.append(signal)
                self.log_info(f"网格买入: {signal.reason}")

        self._current_grid_index = grid_index

        return signals if signals else None

    def finalize(self, context: IsolatedStrategyContext) -> None:
        """策略结束"""
        summary = context.get_summary()
        self.log_info(
            f"策略结束: 总资产={summary['total_value']}, "
            f"收益率={summary['profit_loss_pct']}"
        )
