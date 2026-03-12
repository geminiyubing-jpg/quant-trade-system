"""
布林带策略

基于布林带的均值回归策略。
当价格触及下轨时买入，触及上轨时卖出。
"""

from typing import Dict, Any, Optional, List
from src.services.strategy.base import StrategyBase, StrategyConfig, StrategyContext, Signal, SignalType
from src.services.strategy.registry import strategy_registry, StrategyFrequency, StrategyLifecycleStatus


def calculate_bollinger(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
    """
    计算布林带指标

    Args:
        prices: 价格列表
        period: 计算周期
        std_dev: 标准差倍数

    Returns:
        包含上轨、中轨、下轨的字典
    """
    if len(prices) < period:
        return {"upper": 0, "middle": 0, "lower": 0, "bandwidth": 0}

    recent_prices = prices[-period:]
    middle = sum(recent_prices) / period

    # 计算标准差
    variance = sum((p - middle) ** 2 for p in recent_prices) / period
    std = variance ** 0.5

    upper = middle + std_dev * std
    lower = middle - std_dev * std

    # 布林带宽度
    bandwidth = (upper - lower) / middle if middle > 0 else 0

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
        "bandwidth": bandwidth
    }


def calculate_bollinger_position(current_price: float, upper: float, middle: float, lower: float) -> float:
    """
    计算价格在布林带中的位置 (0-1)

    Args:
        current_price: 当前价格
        upper: 上轨
        middle: 中轨
        lower: 下轨

    Returns:
        位置值 (0=下轨, 0.5=中轨, 1=上轨)
    """
    if upper == lower:
        return 0.5
    return (current_price - lower) / (upper - lower)


@strategy_registry.register(
    strategy_id="bollinger",
    name="布林带策略",
    version="1.0.0",
    author="QuantDev",
    description="基于布林带的均值回归策略。当价格触及下轨时产生买入信号，触及上轨时产生卖出信号。适合震荡行情中的高抛低吸。",
    category="oscillator",
    frequency=StrategyFrequency.DAILY,
    status=StrategyLifecycleStatus.TESTING,
    tags=["布林带", "均值回归", "震荡策略", "经典策略"],
    params_schema={
        "type": "object",
        "properties": {
            "period": {"type": "integer", "description": "布林带计算周期", "default": 20, "minimum": 10, "maximum": 50},
            "std_dev": {"type": "number", "description": "标准差倍数", "default": 2.0, "minimum": 1.0, "maximum": 3.0},
            "entry_threshold": {"type": "number", "description": "入场阈值（触及轨线的百分比）", "default": 0.05, "minimum": 0, "maximum": 0.2},
            "exit_threshold": {"type": "number", "description": "出场阈值（回归中轨的百分比）", "default": 0.3, "minimum": 0, "maximum": 0.5},
            "position_size": {"type": "number", "description": "仓位比例", "default": 0.25, "minimum": 0.1, "maximum": 1.0},
        },
        "required": ["period"]
    },
    default_params={
        "period": 20,
        "std_dev": 2.0,
        "entry_threshold": 0.05,
        "exit_threshold": 0.3,
        "position_size": 0.25,
    },
    min_history_bars=30,
    supported_markets=["A股", "港股", "美股"],
    risk_level="low",
)
class BollingerStrategy(StrategyBase):
    """布林带均值回归策略"""

    def initialize(self, context: StrategyContext) -> None:
        """初始化策略"""
        self.period = self.parameters.get('period', 20)
        self.std_dev = self.parameters.get('std_dev', 2.0)
        self.entry_threshold = self.parameters.get('entry_threshold', 0.05)
        self.exit_threshold = self.parameters.get('exit_threshold', 0.3)
        self.position_size = self.parameters.get('position_size', 0.25)
        self.log_info(f"初始化布林带策略: 周期={self.period}, 标准差倍数={self.std_dev}")

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        """处理数据"""
        historical_data = context.historical_data
        if len(historical_data) < self.period:
            return None

        # 计算布林带
        closes = [bar['close'] for bar in historical_data]
        bb = calculate_bollinger(closes, self.period, self.std_dev)

        upper = bb["upper"]
        middle = bb["middle"]
        lower = bb["lower"]
        bandwidth = bb["bandwidth"]

        current_price = context.current_price
        signals = []
        symbol = context.get_custom_data('symbol', 'UNKNOWN')

        # 计算价格在布林带中的位置
        bb_position = calculate_bollinger_position(current_price, upper, middle, lower)

        # 计算距离轨线的百分比
        lower_distance = (current_price - lower) / lower if lower > 0 else 0
        upper_distance = (upper - current_price) / current_price if current_price > 0 else 0

        # 下轨买入信号 - 价格接近或跌破下轨
        if lower_distance <= self.entry_threshold and context.position <= 0:
            confidence = min(1.0 - bb_position, 1.0)  # 越接近下轨，置信度越高
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=context.current_time,
                price=current_price,
                quantity=int(context.cash * self.position_size / current_price),
                confidence=confidence,
                reason=f"布林带下轨买入: 价格{current_price:.2f}接近下轨{lower:.2f}, 位置={bb_position:.2%}"
            ))

        # 上轨卖出信号 - 价格接近或突破上轨
        elif upper_distance <= self.entry_threshold and context.position > 0:
            confidence = min(bb_position, 1.0)  # 越接近上轨，置信度越高
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=context.current_time,
                price=current_price,
                quantity=context.position,
                confidence=confidence,
                reason=f"布林带上轨卖出: 价格{current_price:.2f}接近上轨{upper:.2f}, 位置={bb_position:.2%}"
            ))

        # 回归中轨出场信号
        elif context.position > 0:
            # 如果价格回归到中轨附近，考虑平仓
            if bb_position > (0.5 - self.exit_threshold) and bb_position < (0.5 + self.exit_threshold):
                signals.append(Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    timestamp=context.current_time,
                    price=current_price,
                    quantity=context.position,
                    confidence=0.7,
                    reason=f"布林带回归中轨卖出: 价格{current_price:.2f}回归至中轨{middle:.2f}附近"
                ))

        return signals if signals else None

    def finalize(self, context: StrategyContext) -> None:
        """结束策略"""
        self.log_info("布林带策略结束")
