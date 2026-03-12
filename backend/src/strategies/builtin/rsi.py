"""
RSI 策略

基于相对强弱指标(RSI)的超买超卖策略。
当RSI低于超卖线时买入，高于超买线时卖出。
"""

from typing import Dict, Any, Optional, List
from src.services.strategy.base import StrategyBase, StrategyConfig, StrategyContext, Signal, SignalType
from src.services.strategy.registry import strategy_registry, StrategyFrequency, StrategyLifecycleStatus


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    计算RSI指标

    Args:
        prices: 价格列表
        period: RSI周期

    Returns:
        RSI值 (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # 默认返回中性值

    # 计算价格变化
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

    # 分离上涨和下跌
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]

    # 计算平均上涨和下跌
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


@strategy_registry.register(
    strategy_id="rsi",
    name="RSI策略",
    version="1.0.0",
    author="QuantDev",
    description="基于相对强弱指标(RSI)的超买超卖策略。当RSI低于超卖线(30)时买入信号，高于超买线(70)时卖出信号。",
    category="oscillator",
    frequency=StrategyFrequency.DAILY,
    status=StrategyLifecycleStatus.TESTING,
    tags=["RSI", "震荡指标", "超买超卖"],
    params_schema={
        "type": "object",
        "properties": {
            "rsi_period": {"type": "integer", "description": "RSI计算周期", "default": 14, "minimum": 5, "maximum": 30},
            "oversold_threshold": {"type": "number", "description": "超卖阈值", "default": 30, "minimum": 10, "maximum": 40},
            "overbought_threshold": {"type": "number", "description": "超买阈值", "default": 70, "minimum": 60, "maximum": 90},
            "position_size": {"type": "number", "description": "仓位比例", "default": 0.25, "minimum": 0.1, "maximum": 1.0},
        },
        "required": ["rsi_period"]
    },
    default_params={
        "rsi_period": 14,
        "oversold_threshold": 30,
        "overbought_threshold": 70,
        "position_size": 0.25,
    },
    min_history_bars=30,
    supported_markets=["A股", "港股", "美股"],
    risk_level="medium",
)
class RSIStrategy(StrategyBase):
    """RSI超买超卖策略"""

    def initialize(self, context: StrategyContext) -> None:
        """初始化策略"""
        self.rsi_period = self.parameters.get('rsi_period', 14)
        self.oversold_threshold = self.parameters.get('oversold_threshold', 30)
        self.overbought_threshold = self.parameters.get('overbought_threshold', 70)
        self.position_size = self.parameters.get('position_size', 0.25)
        self.log_info(f"初始化RSI策略: 周期={self.rsi_period}, 超卖={self.oversold_threshold}, 超买={self.overbought_threshold}")

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        """处理数据"""
        historical_data = context.historical_data
        if len(historical_data) < self.rsi_period + 1:
            return None

        # 计算RSI
        closes = [bar['close'] for bar in historical_data]
        rsi = calculate_rsi(closes, self.rsi_period)

        signals = []
        symbol = context.get_custom_data('symbol', 'UNKNOWN')
        current_price = context.current_price

        # 获取前一个RSI值用于判断穿越
        prev_rsi = calculate_rsi(closes[:-1], self.rsi_period) if len(closes) > self.rsi_period + 1 else 50

        # 超卖反弹信号 - RSI从下方穿越超卖线
        if rsi < self.oversold_threshold and context.position <= 0:
            confidence = min((self.oversold_threshold - rsi) / self.oversold_threshold, 1.0)
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=context.current_time,
                price=current_price,
                quantity=int(context.cash * self.position_size / current_price),
                confidence=confidence,
                reason=f"RSI超卖买入: RSI={rsi:.1f} < {self.oversold_threshold}"
            ))

        # 超卖回升信号 - RSI从超卖区域回升
        elif prev_rsi < self.oversold_threshold and rsi > prev_rsi and rsi < 50 and context.position <= 0:
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=context.current_time,
                price=current_price,
                quantity=int(context.cash * self.position_size / current_price),
                confidence=0.6,
                reason=f"RSI超卖回升买入: RSI从{prev_rsi:.1f}回升至{rsi:.1f}"
            ))

        # 超买卖出信号 - RSI从上方穿越超买线
        elif rsi > self.overbought_threshold and context.position > 0:
            confidence = min((rsi - self.overbought_threshold) / (100 - self.overbought_threshold), 1.0)
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=context.current_time,
                price=current_price,
                quantity=context.position,
                confidence=confidence,
                reason=f"RSI超买卖出: RSI={rsi:.1f} > {self.overbought_threshold}"
            ))

        # 超买回落信号 - RSI从超买区域回落
        elif prev_rsi > self.overbought_threshold and rsi < prev_rsi and rsi > 50 and context.position > 0:
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=context.current_time,
                price=current_price,
                quantity=context.position,
                confidence=0.6,
                reason=f"RSI超买回落卖出: RSI从{prev_rsi:.1f}回落至{rsi:.1f}"
            ))

        return signals if signals else None

    def finalize(self, context: StrategyContext) -> None:
        """结束策略"""
        self.log_info("RSI策略结束")
