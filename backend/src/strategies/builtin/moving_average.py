"""
双均线策略

当短期均线上穿长期均线时买入，下穿时卖出。
"""

from typing import Dict, Any, Optional, List
from src.services.strategy.base import StrategyBase, StrategyConfig, StrategyContext, Signal, SignalType
from src.services.strategy.registry import strategy_registry, StrategyFrequency, StrategyLifecycleStatus


@strategy_registry.register(
    strategy_id="ma_cross",
    name="双均线策略",
    version="1.0.0",
    author="QuantDev",
    description="基于短期和长期移动平均线交叉的趋势跟踪策略。当短期均线上穿长期均线时买入，下穿时卖出。",
    category="trend",
    frequency=StrategyFrequency.DAILY,
    status=StrategyLifecycleStatus.TESTING,
    tags=["趋势", "均线", "经典策略"],
    params_schema={
        "type": "object",
        "properties": {
            "fast_period": {"type": "integer", "description": "短期均线周期", "default": 10, "minimum": 5},
            "slow_period": {"type": "integer", "description": "长期均线周期", "default": 30, "minimum": 10},
            "position_size": {"type": "number", "description": "仓位比例", "default": 0.3, "minimum": 0.1, "maximum": 1.0},
        },
        "required": ["fast_period", "slow_period"]
    },
    default_params={
        "fast_period": 10,
        "slow_period": 30,
        "position_size": 0.3,
    },
    min_history_bars=50,
    supported_markets=["A股", "港股", "美股"],
    risk_level="medium",
)
class MovingAverageStrategy(StrategyBase):
    """双均线交叉策略"""

    def initialize(self, context: StrategyContext) -> None:
        """初始化策略"""
        self.fast_period = self.parameters.get('fast_period', 10)
        self.slow_period = self.parameters.get('slow_period', 30)
        self.position_size = self.parameters.get('position_size', 0.3)
        self.log_info(f"初始化双均线策略: 快线={self.fast_period}, 慢线={self.slow_period}")

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        """处理数据"""
        # 获取历史数据
        historical_data = context.historical_data
        if len(historical_data) < self.slow_period:
            return None

        # 计算均线
        closes = [bar['close'] for bar in historical_data[-self.slow_period-1:]]
        fast_ma = sum(closes[-self.fast_period:]) / self.fast_period
        slow_ma = sum(closes[-self.slow_period:]) / self.slow_period

        # 生成信号
        signals = []
        if fast_ma > slow_ma and context.position <= 0:
            # 金叉买入
            signals.append(Signal(
                symbol=context.get_custom_data('symbol', 'UNKNOWN'),
                signal_type=SignalType.BUY,
                timestamp=context.current_time,
                price=context.current_price,
                quantity=int(context.cash * self.position_size / context.current_price),
                confidence=0.7,
                reason=f"金叉买入: 快线{fast_ma:.2f} > 慢线{slow_ma:.2f}"
            ))
        elif fast_ma < slow_ma and context.position > 0:
            # 死叉卖出
            signals.append(Signal(
                symbol=context.get_custom_data('symbol', 'UNKNOWN'),
                signal_type=SignalType.SELL,
                timestamp=context.current_time,
                price=context.current_price,
                quantity=context.position,
                confidence=0.7,
                reason=f"死叉卖出: 快线{fast_ma:.2f} < 慢线{slow_ma:.2f}"
            ))

        return signals if signals else None

    def finalize(self, context: StrategyContext) -> None:
        """结束策略"""
        self.log_info("双均线策略结束")
