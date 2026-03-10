"""
简单策略示例

提供几个基础的策略实现示例。
"""

from typing import List, Optional
from datetime import datetime
import logging

from .base import (
    StrategyBase,
    StrategyConfig,
    StrategyContext,
    Signal,
    SignalType,
    StrategyError
)

logger = logging.getLogger(__name__)


# ==============================================
# 买入持有策略
# ==============================================

class BuyAndHoldStrategy(StrategyBase):
    """
    买入持有策略

    最简单的策略：在开始时买入，一直持有到结束。
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.has_bought = False

    def initialize(self, context: StrategyContext) -> None:
        """
        初始化策略

        重置买入标志。
        """
        self.has_bought = False
        self.logger.info(f"初始化买入持有策略: {self.name}")

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        """
        处理数据并生成信号

        第一次收到数据时生成买入信号。
        """
        signals = []

        # 第一次买入
        if not self.has_bought:
            # 计算可买入的股数
            quantity = int(context.cash / context.current_price)

            if quantity > 0:
                signal = Signal(
                    symbol=self.parameters.get("symbol", "UNKNOWN"),
                    signal_type=SignalType.BUY,
                    timestamp=context.current_time,
                    price=context.current_price,
                    quantity=quantity,
                    confidence=1.0,
                    reason="买入持有策略：初始买入"
                )
                signals.append(signal)
                self.has_bought = True
                self.logger.info(f"生成买入信号: {quantity} 股 @ {context.current_price}")

        return signals if signals else None

    def finalize(self, context: StrategyContext) -> None:
        """
        结束策略

        记录最终状态。
        """
        self.logger.info(f"策略结束: 持仓 {context.position} 股, 现金 {context.cash:.2f}")


# ==============================================
# 移动平均线策略
# ==============================================

class MovingAverageStrategy(StrategyBase):
    """
    移动平均线策略

    基于简单移动平均线的趋势跟踪策略：
    - 短期均线上穿长期均线时买入（金叉）
    - 短期均线下穿长期均线时卖出（死叉）
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        # 默认参数
        self.short_window = self.parameters.get("short_window", 5)    # 短期窗口
        self.long_window = self.parameters.get("long_window", 20)    # 长期窗口

        # 价格历史
        self.price_history: List[float] = []

        # 上一次的均线值
        self.prev_short_ma: Optional[float] = None
        self.prev_long_ma: Optional[float] = None

        # 当前趋势（True=多头, False=空头）
        self.is_bullish = False

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """
        验证策略参数

        Returns:
            (是否有效, 错误信息)
        """
        if self.short_window >= self.long_window:
            return False, "短期窗口必须小于长期窗口"

        if self.short_window < 2:
            return False, "短期窗口必须 >= 2"

        if self.long_window < 5:
            return False, "长期窗口必须 >= 5"

        return True, None

    def initialize(self, context: StrategyContext) -> None:
        """
        初始化策略

        重置价格历史和均线值。
        """
        self.price_history = []
        self.prev_short_ma = None
        self.prev_long_ma = None
        self.is_bullish = False
        self.logger.info(f"初始化移动平均线策略: 短期={self.short_window}, 长期={self.long_window}")

    def _calculate_ma(self, window: int) -> Optional[float]:
        """
        计算简单移动平均线

        Args:
            window: 窗口大小

        Returns:
            均线值或 None（数据不足）
        """
        if len(self.price_history) < window:
            return None

        return sum(self.price_history[-window:]) / window

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        """
        处理数据并生成信号

        根据均线交叉生成买卖信号。
        """
        signals = []

        # 添加当前价格到历史
        self.price_history.append(context.current_price)

        # 计算均线
        short_ma = self._calculate_ma(self.short_window)
        long_ma = self._calculate_ma(self.long_window)

        # 如果数据不足，无法生成信号
        if short_ma is None or long_ma is None:
            return None

        # 检查金叉（买入信号）
        if (not self.is_bullish and
            short_ma > long_ma and
            self.prev_short_ma is not None and
            self.prev_long_ma is not None and
            self.prev_short_ma <= self.prev_long_ma):

            # 金叉：买入
            quantity = int(context.cash / context.current_price)

            if quantity > 0:
                signal = Signal(
                    symbol=self.parameters.get("symbol", "UNKNOWN"),
                    signal_type=SignalType.BUY,
                    timestamp=context.current_time,
                    price=context.current_price,
                    quantity=quantity,
                    confidence=0.8,
                    reason=f"金叉买入: MA{self.short_window}({short_ma:.2f}) > MA{self.long_window}({long_ma:.2f})"
                )
                signals.append(signal)
                self.is_bullish = True
                self.logger.info(f"金叉买入信号: {signal.reason}")

        # 检查死叉（卖出信号）
        elif (self.is_bullish and
              short_ma < long_ma and
              self.prev_short_ma is not None and
              self.prev_long_ma is not None and
              self.prev_short_ma >= self.prev_long_ma):

            # 死叉：卖出
            if context.position > 0:
                signal = Signal(
                    symbol=self.parameters.get("symbol", "UNKNOWN"),
                    signal_type=SignalType.SELL,
                    timestamp=context.current_time,
                    price=context.current_price,
                    quantity=context.position,  # 全部卖出
                    confidence=0.8,
                    reason=f"死叉卖出: MA{self.short_window}({short_ma:.2f}) < MA{self.long_window}({long_ma:.2f})"
                )
                signals.append(signal)
                self.is_bullish = False
                self.logger.info(f"死叉卖出信号: {signal.reason}")

        # 更新均线值
        self.prev_short_ma = short_ma
        self.prev_long_ma = long_ma

        return signals if signals else None

    def finalize(self, context: StrategyContext) -> None:
        """
        结束策略

        记录最终状态和指标。
        """
        self.logger.info(f"策略结束: 持仓 {context.position} 股, 现金 {context.cash:.2f}")


# ==============================================
# 均值回归策略
# ==============================================

class MeanReversionStrategy(StrategyBase):
    """
    均值回归策略

    基于价格偏离均线的程度进行交易：
    - 价格显著低于均线时买入（超卖）
    - 价格显著高于均线时卖出（超买）
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        # 默认参数
        self.window = self.parameters.get("window", 20)              # 均线窗口
        self.entry_threshold = self.parameters.get("entry_threshold", 2.0)  # 入场阈值（标准差倍数）
        self.exit_threshold = self.parameters.get("exit_threshold", 0.5)    # 离场阈值（标准差倍数）

        # 价格历史
        self.price_history: List[float] = []

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """
        验证策略参数

        Returns:
            (是否有效, 错误信息)
        """
        if self.window < 5:
            return False, "窗口必须 >= 5"

        if self.entry_threshold <= self.exit_threshold:
            return False, "入场阈值必须大于离场阈值"

        if self.entry_threshold < 0 or self.exit_threshold < 0:
            return False, "阈值必须 >= 0"

        return True, None

    def initialize(self, context: StrategyContext) -> None:
        """
        初始化策略
        """
        self.price_history = []
        self.logger.info(f"初始化均值回归策略: 窗口={self.window}, 阈值={self.entry_threshold}/{self.exit_threshold}")

    def _calculate_statistics(self) -> Optional[tuple[float, float]]:
        """
        计算均值和标准差

        Returns:
            (均值, 标准差)或 None（数据不足）
        """
        if len(self.price_history) < self.window:
            return None

        recent_prices = self.price_history[-self.window:]
        import statistics
        mean = statistics.mean(recent_prices)
        stdev = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0

        return mean, stdev

    def on_data(self, context: StrategyContext) -> Optional[List[Signal]]:
        """
        处理数据并生成信号

        基于价格偏离均线的程度生成信号。
        """
        signals = []

        # 添加当前价格到历史
        self.price_history.append(context.current_price)

        # 计算统计量
        stats = self._calculate_statistics()
        if stats is None:
            return None

        mean, stdev = stats

        # 计算Z-score（偏离度）
        if stdev == 0:
            z_score = 0
        else:
            z_score = (context.current_price - mean) / stdev

        # 超卖：买入信号
        if z_score <= -self.entry_threshold and context.position == 0:
            quantity = int(context.cash / context.current_price)

            if quantity > 0:
                signal = Signal(
                    symbol=self.parameters.get("symbol", "UNKNOWN"),
                    signal_type=SignalType.BUY,
                    timestamp=context.current_time,
                    price=context.current_price,
                    quantity=quantity,
                    confidence=min(abs(z_score) / self.entry_threshold, 1.0),
                    reason=f"均值回归买入: Z-score={z_score:.2f} <= -{self.entry_threshold}"
                )
                signals.append(signal)
                self.logger.info(f"超卖买入信号: {signal.reason}")

        # 超买/回归均值：卖出信号
        elif z_score >= self.entry_threshold or (abs(z_score) <= self.exit_threshold and context.position > 0):
            if context.position > 0:
                signal = Signal(
                    symbol=self.parameters.get("symbol", "UNKNOWN"),
                    signal_type=SignalType.SELL,
                    timestamp=context.current_time,
                    price=context.current_price,
                    quantity=context.position,
                    confidence=1.0,
                    reason=f"均值回归卖出: Z-score={z_score:.2f}"
                )
                signals.append(signal)
                self.logger.info(f"均值回归卖出信号: {signal.reason}")

        return signals if signals else None

    def finalize(self, context: StrategyContext) -> None:
        """
        结束策略
        """
        self.logger.info(f"策略结束: 持仓 {context.position} 股, 现金 {context.cash:.2f}")
