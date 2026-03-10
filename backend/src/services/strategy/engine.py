"""
策略执行引擎

负责执行策略、生成订单、管理策略生命周期。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import logging

from .base import (
    StrategyBase,
    StrategyConfig,
    StrategyContext,
    Signal,
    StrategyStatus,
    StrategyError,
    StrategyExecutionError
)

logger = logging.getLogger(__name__)


# ==============================================
# 策略执行结果
# ==============================================

class ExecutionResult:
    """策略执行结果"""

    def __init__(
        self,
        success: bool,
        signals_generated: List[Signal] = None,
        error: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.signals_generated = signals_generated or []
        self.error = error
        self.metrics = metrics or {}

    def __repr__(self):
        return f"<ExecutionResult(success={self.success}, signals={len(self.signals_generated)})>"


# ==============================================
# 策略执行引擎
# ==============================================

class StrategyEngine:
    """
    策略执行引擎

    负责策略的运行、信号生成、订单转换等。
    """

    def __init__(self):
        """初始化策略引擎"""
        self.strategies: Dict[str, StrategyBase] = {}
        self.strategy_states: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("StrategyEngine")

    def add_strategy(self, strategy_id: str, strategy: StrategyBase) -> None:
        """
        添加策略

        Args:
            strategy_id: 策略 ID
            strategy: 策略实例
        """
        # 验证策略参数
        is_valid, error_msg = strategy.validate_parameters()
        if not is_valid:
            raise StrategyExecutionError(f"策略参数验证失败: {error_msg}")

        self.strategies[strategy_id] = strategy
        self.strategy_states[strategy_id] = {
            "status": StrategyStatus.CREATED,
            "created_at": datetime.now(),
            "last_execution": None,
            "total_signals": 0,
            "errors": []
        }

        self.logger.info(f"添加策略: {strategy_id} ({strategy.name})")

    def remove_strategy(self, strategy_id: str) -> None:
        """
        移除策略

        Args:
            strategy_id: 策略 ID
        """
        if strategy_id in self.strategies:
            strategy = self.strategies.pop(strategy_id)
            self.strategy_states.pop(strategy_id)
            self.logger.info(f"移除策略: {strategy_id} ({strategy.name})")

    def get_strategy(self, strategy_id: str) -> Optional[StrategyBase]:
        """
        获取策略

        Args:
            strategy_id: 策略 ID

        Returns:
            策略实例或 None
        """
        return self.strategies.get(strategy_id)

    def list_strategies(self) -> List[str]:
        """
        列出所有策略 ID

        Returns:
            策略 ID 列表
        """
        return list(self.strategies.keys())

    def execute_strategy(
        self,
        strategy_id: str,
        context: StrategyContext
    ) -> ExecutionResult:
        """
        执行策略

        Args:
            strategy_id: 策略 ID
            context: 策略上下文

        Returns:
            执行结果
        """
        # 检查策略是否存在
        if strategy_id not in self.strategies:
            return ExecutionResult(
                success=False,
                error=f"策略不存在: {strategy_id}"
            )

        strategy = self.strategies[strategy_id]
        state = self.strategy_states[strategy_id]

        try:
            # 执行策略
            signals = strategy.on_data(context)

            # 更新状态
            state["last_execution"] = datetime.now()
            if signals:
                state["total_signals"] += len(signals)

            self.logger.debug(
                f"执行策略 {strategy_id}: 生成 {len(signals) if signals else 0} 个信号"
            )

            return ExecutionResult(
                success=True,
                signals_generated=signals or [],
                metrics={
                    "execution_time": state["last_execution"],
                    "total_signals": state["total_signals"]
                }
            )

        except Exception as e:
            # 记录错误
            error_msg = f"策略执行失败: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(f"{strategy_id} - {error_msg}")

            return ExecutionResult(
                success=False,
                error=error_msg
            )

    def execute_all_strategies(
        self,
        contexts: Dict[str, StrategyContext]
    ) -> Dict[str, ExecutionResult]:
        """
        执行所有策略

        Args:
            contexts: {strategy_id: context}

        Returns:
            {strategy_id: execution_result}
        """
        results = {}

        for strategy_id, context in contexts.items():
            results[strategy_id] = self.execute_strategy(strategy_id, context)

        return results

    def start_strategy(self, strategy_id: str, context: StrategyContext) -> ExecutionResult:
        """
        启动策略

        Args:
            strategy_id: 策略 ID
            context: 策略上下文

        Returns:
            执行结果
        """
        if strategy_id not in self.strategies:
            return ExecutionResult(
                success=False,
                error=f"策略不存在: {strategy_id}"
            )

        strategy = self.strategies[strategy_id]
        state = self.strategy_states[strategy_id]

        try:
            # 初始化策略
            strategy.initialize(context)

            # 更新状态
            state["status"] = StrategyStatus.RUNNING
            state["started_at"] = datetime.now()

            self.logger.info(f"启动策略: {strategy_id}")

            return ExecutionResult(success=True)

        except Exception as e:
            error_msg = f"策略启动失败: {str(e)}"
            state["errors"].append(error_msg)
            state["status"] = StrategyStatus.ERROR

            self.logger.error(f"{strategy_id} - {error_msg}")

            return ExecutionResult(
                success=False,
                error=error_msg
            )

    def stop_strategy(self, strategy_id: str, context: StrategyContext) -> ExecutionResult:
        """
        停止策略

        Args:
            strategy_id: 策略 ID
            context: 策略上下文

        Returns:
            执行结果
        """
        if strategy_id not in self.strategies:
            return ExecutionResult(
                success=False,
                error=f"策略不存在: {strategy_id}"
            )

        strategy = self.strategies[strategy_id]
        state = self.strategy_states[strategy_id]

        try:
            # 结束策略
            strategy.finalize(context)

            # 更新状态
            state["status"] = StrategyStatus.STOPPED
            state["stopped_at"] = datetime.now()

            self.logger.info(f"停止策略: {strategy_id}")

            return ExecutionResult(success=True)

        except Exception as e:
            error_msg = f"策略停止失败: {str(e)}"
            state["errors"].append(error_msg)

            self.logger.error(f"{strategy_id} - {error_msg}")

            return ExecutionResult(
                success=False,
                error=error_msg
            )

    def pause_strategy(self, strategy_id: str) -> ExecutionResult:
        """
        暂停策略

        Args:
            strategy_id: 策略 ID

        Returns:
            执行结果
        """
        if strategy_id not in self.strategies:
            return ExecutionResult(
                success=False,
                error=f"策略不存在: {strategy_id}"
            )

        state = self.strategy_states[strategy_id]
        state["status"] = StrategyStatus.PAUSED
        state["paused_at"] = datetime.now()

        self.logger.info(f"暂停策略: {strategy_id}")

        return ExecutionResult(success=True)

    def resume_strategy(self, strategy_id: str) -> ExecutionResult:
        """
        恢复策略

        Args:
            strategy_id: 策略 ID

        Returns:
            执行结果
        """
        if strategy_id not in self.strategies:
            return ExecutionResult(
                success=False,
                error=f"策略不存在: {strategy_id}"
            )

        state = self.strategy_states[strategy_id]
        state["status"] = StrategyStatus.RUNNING
        state["resumed_at"] = datetime.now()

        self.logger.info(f"恢复策略: {strategy_id}")

        return ExecutionResult(success=True)

    def get_strategy_state(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        获取策略状态

        Args:
            strategy_id: 策略 ID

        Returns:
            策略状态字典或 None
        """
        return self.strategy_states.get(strategy_id)

    def get_all_strategy_states(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有策略状态

        Returns:
            {strategy_id: state}
        """
        return self.strategy_states.copy()


# ==============================================
# 信号转换器
# ==============================================

class SignalConverter:
    """
    信号转换器

    将策略信号转换为订单。
    """

    @staticmethod
    def signal_to_order(signal: Signal, user_id: str, strategy_id: str = None) -> Dict[str, Any]:
        """
        将信号转换为订单

        Args:
            signal: 交易信号
            user_id: 用户 ID
            strategy_id: 策略 ID

        Returns:
            订单字典
        """
        from ....repositories.trading import OrderRepository

        order = {
            "user_id": user_id,
            "strategy_id": strategy_id,
            "symbol": signal.symbol,
            "side": signal.signal_type.value,
            "quantity": signal.quantity,
            "price": Decimal(str(signal.price)),
            "execution_mode": "PAPER",  # 默认为模拟交易
            "status": "PENDING",
            "reason": signal.reason,
            "confidence": signal.confidence
        }

        return order

    @staticmethod
    def signals_to_orders(
        signals: List[Signal],
        user_id: str,
        strategy_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        批量转换信号为订单

        Args:
            signals: 信号列表
            user_id: 用户 ID
            strategy_id: 策略 ID

        Returns:
            订单列表
        """
        return [
            SignalConverter.signal_to_order(signal, user_id, strategy_id)
            for signal in signals
        ]
