"""
AI 策略包装器

用于包装 AI 生成的 JSON 格式策略，使其能够注册到策略注册表。
支持基于技术指标和规则的自动化交易信号生成。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from loguru import logger

from .base import StrategyBase, StrategyConfig, StrategyStatus, Signal, SignalType


class AIStrategyWrapper(StrategyBase):
    """
    AI 策略包装器

    将 AI 生成的 JSON 格式策略包装成可执行的策略类。
    支持解析策略规则并生成交易信号。
    """

    def __init__(self, config: StrategyConfig):
        """初始化 AI 策略包装器"""
        super().__init__(config)

        # AI 策略特定属性
        self.ai_content: Dict[str, Any] = {}
        self.strategy_type: str = ""
        self.market_condition: str = ""
        self.risk_level: str = "medium"

        # 策略规则
        self.entry_rules: List[Dict[str, Any]] = []
        self.exit_rules: List[Dict[str, Any]] = []
        self.indicators: Dict[str, Any] = {}

        # 历史数据缓存
        self._price_history: List[float] = []
        self._volume_history: List[int] = []

    def initialize(self) -> None:
        """初始化策略"""
        logger.info(f"初始化 AI 策略: {self.config.name}")

        # 从配置中加载 AI 策略内容
        if hasattr(self.config, 'ai_content'):
            self.ai_content = self.config.ai_content
            self._parse_strategy_content()

    def _parse_strategy_content(self) -> None:
        """解析AI策略内容"""
        if not self.ai_content:
            return

        # 解析策略类型
        self.strategy_type = self.ai_content.get('strategy_type', 'unknown')

        # 解析市场条件
        self.market_condition = self.ai_content.get('market_condition', '')

        # 解析风险等级
        self.risk_level = self.ai_content.get('risk_level', 'medium')

        # 解析入场规则
        self.entry_rules = self.ai_content.get('entry_rules', [])
        if not self.entry_rules and 'entry_conditions' in self.ai_content:
            self.entry_rules = self._parse_conditions(self.ai_content['entry_conditions'])

        # 解析出场规则
        self.exit_rules = self.ai_content.get('exit_rules', [])
        if not self.exit_rules and 'exit_conditions' in self.ai_content:
            self.exit_rules = self._parse_conditions(self.ai_content['exit_conditions'])

        # 解析技术指标参数
        self.indicators = self.ai_content.get('indicators', {})

        logger.info(f"AI策略解析完成: 类型={self.strategy_type}, "
                   f"入场规则={len(self.entry_rules)}条, 出场规则={len(self.exit_rules)}条")

    def _parse_conditions(self, conditions: Any) -> List[Dict[str, Any]]:
        """将条件字符串或列表解析为规则列表"""
        if isinstance(conditions, str):
            # 简单的文本条件，转换为基本规则
            return [{'type': 'text', 'condition': conditions}]
        elif isinstance(conditions, list):
            return conditions
        elif isinstance(conditions, dict):
            return [conditions]
        return []

    def on_bar(self, bar: Dict[str, Any]) -> Optional[Signal]:
        """
        处理 K 线数据

        根据AI生成的策略逻辑生成交易信号。

        Args:
            bar: K线数据，包含 open, high, low, close, volume, timestamp 等

        Returns:
            Optional[Signal]: 交易信号
        """
        if not self._validate_bar(bar):
            return None

        # 更新历史数据
        close_price = float(bar.get('close', 0))
        volume = int(bar.get('volume', 0))

        self._price_history.append(close_price)
        self._volume_history.append(volume)

        # 保持历史数据在合理范围
        max_history = 200
        if len(self._price_history) > max_history:
            self._price_history = self._price_history[-max_history:]
            self._volume_history = self._volume_history[-max_history:]

        # 计算技术指标
        indicators = self._calculate_indicators()

        # 检查入场条件
        if self._check_entry_conditions(bar, indicators):
            return self._generate_entry_signal(bar, indicators)

        # 检查出场条件
        if self._check_exit_conditions(bar, indicators):
            return self._generate_exit_signal(bar, indicators)

        return None

    def on_tick(self, tick: Dict[str, Any]) -> Optional[Signal]:
        """
        处理 Tick 数据

        Args:
            tick: Tick数据，包含 price, volume, timestamp 等

        Returns:
            Optional[Signal]: 交易信号
        """
        # 对于tick数据，简单更新最新价格
        # 实际的信号生成主要在on_bar中完成
        if 'price' in tick:
            last_price = float(tick['price'])
            if self._price_history:
                # 更新最新价格
                self._price_history[-1] = last_price
        return None

    def on_timer(self) -> None:
        """定时器回调"""
        # 可以用于定期检查或清理
        pass

    def _validate_bar(self, bar: Dict[str, Any]) -> bool:
        """验证K线数据"""
        required_fields = ['close']
        for field in required_fields:
            if field not in bar or bar[field] is None:
                return False
        return True

    def _calculate_indicators(self) -> Dict[str, Any]:
        """计算技术指标"""
        indicators = {}

        if len(self._price_history) < 2:
            return indicators

        prices = self._price_history

        # 计算简单移动平均
        ma_periods = self.indicators.get('ma_periods', [5, 10, 20, 60])
        for period in ma_periods:
            if len(prices) >= period:
                ma_value = sum(prices[-period:]) / period
                indicators[f'ma{period}'] = ma_value

        # 计算RSI
        rsi_period = self.indicators.get('rsi_period', 14)
        if len(prices) >= rsi_period + 1:
            indicators['rsi'] = self._calculate_rsi(prices, rsi_period)

        # 计算MACD
        if len(prices) >= 26:
            macd, signal, hist = self._calculate_macd(prices)
            indicators['macd'] = macd
            indicators['macd_signal'] = signal
            indicators['macd_hist'] = hist

        # 计算布林带
        bb_period = self.indicators.get('bollinger_period', 20)
        if len(prices) >= bb_period:
            upper, middle, lower = self._calculate_bollinger(prices, bb_period)
            indicators['bb_upper'] = upper
            indicators['bb_middle'] = middle
            indicators['bb_lower'] = lower

        # 计算波动率
        if len(prices) >= 20:
            returns = [(prices[i] - prices[i-1]) / prices[i-1]
                      for i in range(1, len(prices))]
            volatility = sum(r*r for r in returns[-20:]) / 20
            indicators['volatility'] = volatility ** 0.5

        # 当前价格相对于均线的位置
        current_price = prices[-1]
        if 'ma20' in indicators:
            indicators['price_to_ma20'] = (current_price - indicators['ma20']) / indicators['ma20']

        return indicators

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: List[float],
                        fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """计算MACD指标"""
        # 计算EMA
        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema_values = [data[0]]
            for price in data[1:]:
                ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
            return ema_values

        ema_fast = ema(prices, fast)
        ema_slow = ema(prices, slow)

        macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(prices))]
        signal_line = ema(macd_line, signal)
        histogram = [macd_line[i] - signal_line[i] for i in range(len(macd_line))]

        return macd_line[-1], signal_line[-1], histogram[-1]

    def _calculate_bollinger(self, prices: List[float],
                            period: int = 20, std_dev: float = 2.0) -> tuple:
        """计算布林带"""
        recent_prices = prices[-period:]
        middle = sum(recent_prices) / period

        variance = sum((p - middle) ** 2 for p in recent_prices) / period
        std = variance ** 0.5

        upper = middle + std_dev * std
        lower = middle - std_dev * std

        return upper, middle, lower

    def _check_entry_conditions(self, bar: Dict[str, Any],
                               indicators: Dict[str, Any]) -> bool:
        """检查入场条件"""
        if not self.entry_rules:
            # 如果没有明确的入场规则，使用默认逻辑
            return self._default_entry_check(bar, indicators)

        for rule in self.entry_rules:
            if self._evaluate_rule(rule, bar, indicators):
                return True

        return False

    def _check_exit_conditions(self, bar: Dict[str, Any],
                              indicators: Dict[str, Any]) -> bool:
        """检查出场条件"""
        if not self.exit_rules:
            return False

        for rule in self.exit_rules:
            if self._evaluate_rule(rule, bar, indicators):
                return True

        return False

    def _evaluate_rule(self, rule: Dict[str, Any],
                      bar: Dict[str, Any],
                      indicators: Dict[str, Any]) -> bool:
        """评估单条规则"""
        rule_type = rule.get('type', '')

        if rule_type == 'text':
            # 文本条件，简单匹配关键词
            condition = rule.get('condition', '').lower()
            if 'rsi超卖' in condition or 'rsi < 30' in condition:
                rsi = indicators.get('rsi', 50)
                return rsi < 30
            elif 'rsi超买' in condition or 'rsi > 70' in condition:
                rsi = indicators.get('rsi', 50)
                return rsi > 70
            elif '金叉' in condition:
                macd = indicators.get('macd', 0)
                signal = indicators.get('macd_signal', 0)
                return macd > signal
            elif '死叉' in condition:
                macd = indicators.get('macd', 0)
                signal = indicators.get('macd_signal', 0)
                return macd < signal
            return False

        elif rule_type == 'indicator':
            # 指标条件
            indicator = rule.get('indicator', '')
            operator = rule.get('operator', '>')
            value = rule.get('value', 0)

            current_value = indicators.get(indicator)
            if current_value is None:
                return False

            return self._compare(current_value, operator, value)

        elif rule_type == 'price':
            # 价格条件
            price_type = rule.get('price_type', 'close')
            operator = rule.get('operator', '>')
            value = rule.get('value', 0)

            current_price = bar.get(price_type, bar.get('close', 0))
            return self._compare(current_price, operator, value)

        elif rule_type == 'compound':
            # 复合条件
            logic = rule.get('logic', 'and')
            sub_rules = rule.get('rules', [])

            results = [self._evaluate_rule(r, bar, indicators) for r in sub_rules]

            if logic == 'and':
                return all(results)
            else:  # or
                return any(results)

        return False

    def _compare(self, a: float, operator: str, b: float) -> bool:
        """比较两个值"""
        ops = {
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
        }
        return ops.get(operator, lambda x, y: False)(a, b)

    def _default_entry_check(self, bar: Dict[str, Any],
                            indicators: Dict[str, Any]) -> bool:
        """默认入场检查逻辑"""
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        signal = indicators.get('macd_signal', 0)

        # 默认入场条件：RSI超卖 + MACD金叉
        if rsi < 30 and macd > signal:
            return True

        # 或者：价格跌破布林带下轨
        bb_lower = indicators.get('bb_lower')
        current_price = bar.get('close', 0)
        if bb_lower and current_price < bb_lower:
            return True

        return False

    def _generate_entry_signal(self, bar: Dict[str, Any],
                              indicators: Dict[str, Any]) -> Signal:
        """生成入场信号"""
        current_price = Decimal(str(bar.get('close', 0)))
        timestamp = bar.get('timestamp', datetime.now())

        # 计算置信度
        confidence = self._calculate_confidence(indicators, is_entry=True)

        # 生成买入原因
        reason = self._generate_reason(indicators, is_entry=True)

        return Signal(
            symbol=bar.get('symbol', 'UNKNOWN'),
            signal_type=SignalType.BUY,
            timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(),
            price=current_price,
            quantity=0,  # 由风控模块决定
            confidence=confidence,
            reason=reason
        )

    def _generate_exit_signal(self, bar: Dict[str, Any],
                             indicators: Dict[str, Any]) -> Signal:
        """生成出场信号"""
        current_price = Decimal(str(bar.get('close', 0)))
        timestamp = bar.get('timestamp', datetime.now())

        # 计算置信度
        confidence = self._calculate_confidence(indicators, is_entry=False)

        # 生成卖出原因
        reason = self._generate_reason(indicators, is_entry=False)

        return Signal(
            symbol=bar.get('symbol', 'UNKNOWN'),
            signal_type=SignalType.SELL,
            timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(),
            price=current_price,
            quantity=0,  # 由风控模块决定
            confidence=confidence,
            reason=reason
        )

    def _calculate_confidence(self, indicators: Dict[str, Any],
                             is_entry: bool) -> float:
        """计算信号置信度"""
        base_confidence = 0.5

        # 根据多个指标调整置信度
        rsi = indicators.get('rsi', 50)
        if is_entry:
            # 入场：RSI越低，置信度越高
            if rsi < 20:
                base_confidence += 0.3
            elif rsi < 30:
                base_confidence += 0.2
            elif rsi < 40:
                base_confidence += 0.1
        else:
            # 出场：RSI越高，置信度越高
            if rsi > 80:
                base_confidence += 0.3
            elif rsi > 70:
                base_confidence += 0.2
            elif rsi > 60:
                base_confidence += 0.1

        # MACD确认
        macd = indicators.get('macd', 0)
        signal = indicators.get('macd_signal', 0)
        if (is_entry and macd > signal) or (not is_entry and macd < signal):
            base_confidence += 0.1

        # 限制在0-1范围
        return min(max(base_confidence, 0.0), 1.0)

    def _generate_reason(self, indicators: Dict[str, Any],
                        is_entry: bool) -> str:
        """生成交易原因说明"""
        reasons = []

        rsi = indicators.get('rsi')
        if rsi is not None:
            if is_entry and rsi < 30:
                reasons.append(f"RSI超卖({rsi:.1f})")
            elif not is_entry and rsi > 70:
                reasons.append(f"RSI超买({rsi:.1f})")

        macd = indicators.get('macd')
        signal = indicators.get('macd_signal')
        if macd is not None and signal is not None:
            if is_entry and macd > signal:
                reasons.append("MACD金叉")
            elif not is_entry and macd < signal:
                reasons.append("MACD死叉")

        bb_lower = indicators.get('bb_lower')
        bb_upper = indicators.get('bb_upper')
        if bb_lower is not None and is_entry:
            reasons.append("触及布林带下轨")
        if bb_upper is not None and not is_entry:
            reasons.append("触及布林带上轨")

        if not reasons:
            reasons.append("AI策略信号" if is_entry else "AI策略出场")

        return "; ".join(reasons)

    def get_state(self) -> Dict[str, Any]:
        """获取策略状态"""
        return {
            "status": self.status.value if self.status else "unknown",
            "ai_content": self.ai_content,
            "strategy_type": self.strategy_type,
            "price_history_length": len(self._price_history),
            "last_price": self._price_history[-1] if self._price_history else None,
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """设置策略状态"""
        if "ai_content" in state:
            self.ai_content = state["ai_content"]
        if "strategy_type" in state:
            self.strategy_type = state["strategy_type"]
        if "price_history" in state:
            self._price_history = state["price_history"]
        if "volume_history" in state:
            self._volume_history = state["volume_history"]


def load_ai_strategy_from_file(file_path: str) -> Dict[str, Any]:
    """
    从文件加载 AI 策略

    Args:
        file_path: 策略文件路径

    Returns:
        策略数据字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_ai_strategy_metadata(strategy_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建 AI 策略元数据

    Args:
        strategy_data: AI 策略数据

    Returns:
        适用于策略注册表的元数据
    """
    from .registry import StrategyMetadata, StrategyFrequency, StrategyLifecycleStatus

    # 映射频率
    freq_map = {
        "1m": StrategyFrequency.MIN_1,
        "5m": StrategyFrequency.MIN_5,
        "15m": StrategyFrequency.MIN_15,
        "30m": StrategyFrequency.MIN_30,
        "1h": StrategyFrequency.HOUR_1,
        "4h": StrategyFrequency.HOUR_4,
        "1d": StrategyFrequency.DAILY,
        "1w": StrategyFrequency.WEEKLY,
    }

    freq = freq_map.get(
        strategy_data.get("frequency", "1d"),
        StrategyFrequency.DAILY
    )

    # 映射状态
    status_map = {
        "development": StrategyLifecycleStatus.DEVELOPMENT,
        "testing": StrategyLifecycleStatus.TESTING,
        "backtest_passed": StrategyLifecycleStatus.BACKTEST_PASSED,
        "paper_trading": StrategyLifecycleStatus.PAPER_TRADING,
        "live_trading": StrategyLifecycleStatus.LIVE_TRADING,
        "deprecated": StrategyLifecycleStatus.DEPRECATED,
        "suspended": StrategyLifecycleStatus.SUSPENDED,
    }

    status = status_map.get(
        strategy_data.get("status", "development"),
        StrategyLifecycleStatus.DEVELOPMENT
    )

    return {
        "strategy_id": strategy_data.get("strategy_id"),
        "name": strategy_data.get("name"),
        "version": strategy_data.get("version", "1.0.0"),
        "author": strategy_data.get("author", "AI Generator"),
        "description": strategy_data.get("description", ""),
        "category": strategy_data.get("category", "ai_generated"),
        "frequency": freq,
        "status": status,
        "tags": strategy_data.get("tags", ["AI生成"]),
        "params_schema": strategy_data.get("params_schema", {}),
        "default_params": strategy_data.get("default_params", {}),
        "min_history_bars": strategy_data.get("min_history_bars", 100),
        "supported_markets": strategy_data.get("supported_markets", ["A股"]),
        "risk_level": strategy_data.get("risk_level", "medium"),
        "ai_content": strategy_data.get("content", {}),
        "strategy_class": AIStrategyWrapper,
    }


def load_all_ai_strategies() -> int:
    """
    加载所有已保存的 AI 策略到策略注册表

    Returns:
        加载的策略数量
    """
    from .registry import strategy_registry, StrategyMetadata, StrategyFrequency, StrategyLifecycleStatus

    # 获取 AI 策略目录
    strategy_dir = Path(__file__).parent.parent.parent / "strategies" / "ai_generated"

    if not strategy_dir.exists():
        logger.info(f"AI 策略目录不存在: {strategy_dir}")
        return 0

    loaded_count = 0

    # 遍历所有 JSON 文件
    for json_file in strategy_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                strategy_data = json.load(f)

            strategy_id = strategy_data.get("strategy_id")
            if not strategy_id:
                logger.warning(f"策略文件缺少 strategy_id: {json_file}")
                continue

            # 检查是否已注册
            if strategy_registry.get_strategy(strategy_id):
                logger.debug(f"策略已注册，跳过: {strategy_id}")
                continue

            # 映射频率
            freq_map = {
                "1m": StrategyFrequency.MIN_1,
                "5m": StrategyFrequency.MIN_5,
                "15m": StrategyFrequency.MIN_15,
                "30m": StrategyFrequency.MIN_30,
                "1h": StrategyFrequency.HOUR_1,
                "4h": StrategyFrequency.HOUR_4,
                "1d": StrategyFrequency.DAILY,
                "1w": StrategyFrequency.WEEKLY,
            }
            frequency = freq_map.get(
                strategy_data.get("frequency", "1d"),
                StrategyFrequency.DAILY
            )

            # 映射状态
            status_map = {
                "development": StrategyLifecycleStatus.DEVELOPMENT,
                "testing": StrategyLifecycleStatus.TESTING,
                "backtest_passed": StrategyLifecycleStatus.BACKTEST_PASSED,
                "paper_trading": StrategyLifecycleStatus.PAPER_TRADING,
                "live_trading": StrategyLifecycleStatus.LIVE_TRADING,
                "deprecated": StrategyLifecycleStatus.DEPRECATED,
                "suspended": StrategyLifecycleStatus.SUSPENDED,
            }
            status = status_map.get(
                strategy_data.get("status", "development"),
                StrategyLifecycleStatus.DEVELOPMENT
            )

            # 创建元数据
            metadata = StrategyMetadata(
                strategy_id=strategy_id,
                name=strategy_data.get("name", strategy_id),
                strategy_class=AIStrategyWrapper,
                version=strategy_data.get("version", "1.0.0"),
                author=strategy_data.get("author", "AI Generator"),
                description=strategy_data.get("description", ""),
                category=strategy_data.get("category", "ai_generated"),
                frequency=frequency,
                status=status,
                tags=strategy_data.get("tags", ["AI生成"]),
                params_schema=strategy_data.get("params_schema", {}),
                default_params={"ai_content": strategy_data.get("content", {})},
                min_history_bars=strategy_data.get("min_history_bars", 100),
                supported_markets=strategy_data.get("supported_markets", ["A股"]),
                risk_level=strategy_data.get("risk_level", "medium"),
            )

            # 注册到注册表
            strategy_registry._register_metadata(metadata)
            loaded_count += 1
            logger.info(f"加载 AI 策略: {strategy_id}")

        except Exception as e:
            logger.error(f"加载策略文件失败 {json_file}: {e}")

    if loaded_count > 0:
        logger.info(f"共加载 {loaded_count} 个 AI 策略")

    return loaded_count
