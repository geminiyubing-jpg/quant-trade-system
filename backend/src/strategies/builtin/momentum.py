"""
动量策略

基于价格动量进行趋势跟踪交易。
"""

from typing import Dict, Any, Optional, List
from src.services.strategy.base import StrategyBase, StrategyConfig, StrategyContext, Signal, SignalType
from src.services.strategy.registry import strategy_registry, StrategyFrequency, StrategyLifecycleStatus


@strategy_registry.register(
    strategy_id="momentum",
    name="动量策略",
    version="1.0.0",
    author="QuantDev",
    description="基于价格动量的趋势跟踪策略。追踪强势股票，在动量强劲时买入，动量衰竭时卖出。",
    category="momentum",
    frequency=StrategyFrequency.DAILY,
    status=StrategyLifecycleStatus.TESTING,
    tags=["动量", "趋势", "短线"],
    params_schema={
        "type": "object",
        "properties": {
            "lookback_period": {"type": "integer", "description": "回看周期", "default": 14, "minimum": 5},
            "momentum_threshold": {"type": "number", "description": "动量阈值", "default": 0.05},
            "position_size": {"type": "number", "description": "仓位比例", "default": 0.25, "minimum": 0.1, "maximum": 1.0},
        },
        "required": ["lookback_period"]
    },
    default_params={
        "lookback_period": 14,
        "momentum_threshold": 0.05,
        "position_size": 0.25,
    },
    min_history_bars=30,
    supported_markets=["A股", "港股", "美股"],
    risk_level="high",
)
class MomentumStrategy(StrategyBase):
    """动量策略"""

    def initialize(self, context: StrategyContext) -> None:
        """初始化策略"""
        self.lookback_period = self.parameters.get('lookback_period', 14)
        self.momentum_threshold = self.parameters.get('momentum_threshold', 0.05)
        self.position_size = self.parameters.get('position_size', 0.25)
        self.log_info(f"初始化动量策略: 回看周期={self.lookback_period}")

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        """处理数据"""
        historical_data = context.historical_data
        if len(historical_data) < self.lookback_period + 1:
            return None

        # 计算动量（价格变化率）
        current_price = context.current_price
        past_price = historical_data[-self.lookback_period]['close']
        momentum = (current_price - past_price) / past_price

        signals = []
        symbol = context.get_custom_data('symbol', 'UNKNOWN')

        if momentum > self.momentum_threshold and context.position <= 0:
            # 动量强劲，买入
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=context.current_time,
                price=current_price,
                quantity=int(context.cash * self.position_size / current_price),
                confidence=min(momentum / self.momentum_threshold, 1.0),
                reason=f"动量买入: {momentum:.2%} > {self.momentum_threshold:.2%}"
            ))
        elif momentum < -self.momentum_threshold * 0.5 and context.position > 0:
            # 动量衰竭，卖出
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=context.current_time,
                price=current_price,
                quantity=context.position,
                confidence=min(abs(momentum) / self.momentum_threshold, 1.0),
                reason=f"动量卖出: {momentum:.2%} < {-self.momentum_threshold * 0.5:.2%}"
            ))

        return signals if signals else None

    def finalize(self, context: StrategyContext) -> None:
        """结束策略"""
        self.log_info("动量策略结束")
