"""
均值回归策略

当价格偏离均值过大时进行反向操作。
"""

from typing import Dict, Any, Optional, List
from src.services.strategy.base import StrategyBase, StrategyConfig, StrategyContext, Signal, SignalType
from src.services.strategy.registry import strategy_registry, StrategyFrequency, StrategyLifecycleStatus


@strategy_registry.register(
    strategy_id="mean_reversion",
    name="均值回归策略",
    version="1.0.0",
    author="QuantDev",
    description="基于均值回归原理的策略。当价格偏离均线过大时进行反向操作，适合震荡行情中的高抛低吸。",
    category="mean_reversion",
    frequency=StrategyFrequency.DAILY,
    status=StrategyLifecycleStatus.TESTING,
    tags=["均值回归", "震荡", "短线"],
    params_schema={
        "type": "object",
        "properties": {
            "ma_period": {"type": "integer", "description": "均线周期", "default": 20, "minimum": 5},
            "entry_deviation": {"type": "number", "description": "入场偏离度", "default": 0.03, "minimum": 0.01},
            "exit_deviation": {"type": "number", "description": "出场偏离度", "default": 0.01},
            "position_size": {"type": "number", "description": "仓位比例", "default": 0.2, "minimum": 0.1, "maximum": 1.0},
        },
        "required": ["ma_period"]
    },
    default_params={
        "ma_period": 20,
        "entry_deviation": 0.03,
        "exit_deviation": 0.01,
        "position_size": 0.2,
    },
    min_history_bars=30,
    supported_markets=["A股", "港股", "美股"],
    risk_level="low",
)
class MeanReversionStrategy(StrategyBase):
    """均值回归策略"""

    def initialize(self, context: StrategyContext) -> None:
        """初始化策略"""
        self.ma_period = self.parameters.get('ma_period', 20)
        self.entry_deviation = self.parameters.get('entry_deviation', 0.03)
        self.exit_deviation = self.parameters.get('exit_deviation', 0.01)
        self.position_size = self.parameters.get('position_size', 0.2)
        self.log_info(f"初始化均值回归策略: 均线周期={self.ma_period}")

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        """处理数据"""
        historical_data = context.historical_data
        if len(historical_data) < self.ma_period:
            return None

        # 计算均线
        closes = [bar['close'] for bar in historical_data[-self.ma_period:]]
        ma = sum(closes) / len(closes)

        current_price = context.current_price
        deviation = (current_price - ma) / ma

        signals = []
        symbol = context.get_custom_data('symbol', 'UNKNOWN')

        if deviation < -self.entry_deviation and context.position <= 0:
            # 价格低于均线过多，买入
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=context.current_time,
                price=current_price,
                quantity=int(context.cash * self.position_size / current_price),
                confidence=min(abs(deviation) / self.entry_deviation, 1.0),
                reason=f"超卖买入: 价格偏离 {deviation:.2%} < -{self.entry_deviation:.2%}"
            ))
        elif deviation > self.entry_deviation and context.position <= 0:
            # 价格高于均线过多，可做空（这里简化为不操作）
            pass
        elif abs(deviation) < self.exit_deviation and context.position > 0:
            # 价格回归均值，平仓
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=context.current_time,
                price=current_price,
                quantity=context.position,
                confidence=0.8,
                reason=f"回归平仓: 价格偏离 {deviation:.2%}"
            ))

        return signals if signals else None

    def finalize(self, context: StrategyContext) -> None:
        """结束策略"""
        self.log_info("均值回归策略结束")
