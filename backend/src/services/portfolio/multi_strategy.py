"""
==============================================
QuantAI Ecosystem - 多策略组合管理服务
==============================================

提供多策略组合管理、资金分配和协同执行功能。
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import uuid
import logging
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

logger = logging.getLogger(__name__)


# ==============================================
# 数据模型
# ==============================================

class AllocationMethod(str, Enum):
    """资金分配方法"""
    EQUAL = "EQUAL"  # 等权重
    RISK_PARITY = "RISK_PARITY"  # 风险平价
    KELLY = "KELLY"  # 凯利公式
    CUSTOM = "CUSTOM"  # 自定义


class StrategyStatus(str, Enum):
    """策略状态"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


@dataclass
class StrategyAllocation:
    """策略资金分配"""
    strategy_id: str
    strategy_name: str
    weight: Decimal
    allocated_capital: Decimal
    used_capital: Decimal = Decimal("0")
    available_capital: Decimal = Decimal("0")
    pnl: Decimal = Decimal("0")
    status: StrategyStatus = StrategyStatus.ACTIVE


@dataclass
class MultiStrategyConfig:
    """多策略配置"""
    total_capital: Decimal
    allocation_method: AllocationMethod = AllocationMethod.EQUAL
    rebalance_threshold: Decimal = Decimal("0.05")  # 5% 再平衡阈值
    max_strategies: int = 10
    min_strategy_weight: Decimal = Decimal("0.05")  # 最小策略权重 5%
    max_strategy_weight: Decimal = Decimal("0.30")  # 最大策略权重 30%


@dataclass
class RebalanceResult:
    """再平衡结果"""
    rebalance_id: str
    timestamp: datetime
    trades: List[Dict[str, Any]]
    estimated_cost: Decimal
    status: str = "PENDING"


# ==============================================
# 多策略组合管理器
# ==============================================

class MultiStrategyManager:
    """
    多策略组合管理器

    管理多个策略的组合，包括：
    - 资金分配
    - 权重再平衡
    - 策略协同
    - 风险聚合
    """

    def __init__(
        self,
        db: Session,
        config: Optional[MultiStrategyConfig] = None
    ):
        self.db = db
        self.config = config or MultiStrategyConfig(total_capital=Decimal("1000000"))

        # 策略分配
        self.allocations: Dict[str, StrategyAllocation] = {}

        # 历史记录
        self.allocation_history: List[Dict[str, Any]] = []
        self.rebalance_history: List[RebalanceResult] = []

    def add_strategy(
        self,
        strategy_id: str,
        strategy_name: str,
        initial_weight: Optional[Decimal] = None,
        custom_capital: Optional[Decimal] = None
    ) -> StrategyAllocation:
        """
        添加策略到组合

        Args:
            strategy_id: 策略ID
            strategy_name: 策略名称
            initial_weight: 初始权重
            custom_capital: 自定义资金（覆盖权重计算）

        Returns:
            StrategyAllocation: 策略分配
        """
        if len(self.allocations) >= self.config.max_strategies:
            raise ValueError(f"Maximum strategies ({self.config.max_strategies}) reached")

        if strategy_id in self.allocations:
            raise ValueError(f"Strategy {strategy_id} already exists")

        # 计算资金分配
        if custom_capital:
            allocated = custom_capital
            weight = allocated / self.config.total_capital
        elif initial_weight:
            weight = min(initial_weight, self.config.max_strategy_weight)
            weight = max(weight, self.config.min_strategy_weight)
            allocated = self.config.total_capital * weight
        else:
            # 等权重分配
            n_strategies = len(self.allocations) + 1
            weight = Decimal("1") / Decimal(str(n_strategies))
            allocated = self.config.total_capital * weight

        allocation = StrategyAllocation(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            weight=weight,
            allocated_capital=allocated,
            available_capital=allocated
        )

        self.allocations[strategy_id] = allocation

        # 重新计算所有策略权重
        self._rebalance_weights()

        logger.info(f"Added strategy {strategy_name} with weight {weight:.2%}")

        return allocation

    def remove_strategy(self, strategy_id: str) -> bool:
        """
        移除策略

        Args:
            strategy_id: 策略ID

        Returns:
            bool: 是否成功
        """
        if strategy_id not in self.allocations:
            return False

        del self.allocations[strategy_id]

        # 重新计算权重
        self._rebalance_weights()

        logger.info(f"Removed strategy {strategy_id}")

        return True

    def update_strategy_status(
        self,
        strategy_id: str,
        status: StrategyStatus
    ) -> Optional[StrategyAllocation]:
        """更新策略状态"""
        if strategy_id not in self.allocations:
            return None

        self.allocations[strategy_id].status = status

        logger.info(f"Strategy {strategy_id} status updated to {status.value}")

        return self.allocations[strategy_id]

    def get_allocation(self, strategy_id: str) -> Optional[StrategyAllocation]:
        """获取策略分配"""
        return self.allocations.get(strategy_id)

    def get_all_allocations(self) -> List[StrategyAllocation]:
        """获取所有策略分配"""
        return list(self.allocations.values())

    def allocate_capital(
        self,
        strategy_id: str,
        amount: Decimal
    ) -> Optional[StrategyAllocation]:
        """
        为策略分配资金

        Args:
            strategy_id: 策略ID
            amount: 分配金额

        Returns:
            StrategyAllocation: 更新后的分配
        """
        if strategy_id not in self.allocations:
            return None

        allocation = self.allocations[strategy_id]

        if amount > allocation.available_capital:
            logger.warning(
                f"Requested amount {amount} exceeds available capital {allocation.available_capital}"
            )
            amount = allocation.available_capital

        allocation.used_capital += amount
        allocation.available_capital = allocation.allocated_capital - allocation.used_capital

        logger.info(f"Allocated {amount} to strategy {strategy_id}")

        return allocation

    def release_capital(
        self,
        strategy_id: str,
        amount: Decimal,
        pnl: Decimal = Decimal("0")
    ) -> Optional[StrategyAllocation]:
        """
        释放策略资金

        Args:
            strategy_id: 策略ID
            amount: 释放金额
            pnl: 盈亏

        Returns:
            StrategyAllocation: 更新后的分配
        """
        if strategy_id not in self.allocations:
            return None

        allocation = self.allocations[strategy_id]

        allocation.used_capital -= amount
        if allocation.used_capital < 0:
            allocation.used_capital = Decimal("0")

        allocation.available_capital = allocation.allocated_capital - allocation.used_capital
        allocation.pnl += pnl

        logger.info(f"Released {amount} from strategy {strategy_id}, PnL: {pnl}")

        return allocation

    def calculate_allocation(
        self,
        method: Optional[AllocationMethod] = None
    ) -> Dict[str, Decimal]:
        """
        计算策略资金分配

        Args:
            method: 分配方法

        Returns:
            Dict[str, Decimal]: 策略ID到权重的映射
        """
        method = method or self.config.allocation_method
        active_strategies = [
            s for s in self.allocations.values()
            if s.status == StrategyStatus.ACTIVE
        ]

        if not active_strategies:
            return {}

        if method == AllocationMethod.EQUAL:
            return self._equal_weight_allocation(active_strategies)
        elif method == AllocationMethod.RISK_PARITY:
            return self._risk_parity_allocation(active_strategies)
        elif method == AllocationMethod.KELLY:
            return self._kelly_allocation(active_strategies)
        else:
            return {s.strategy_id: s.weight for s in active_strategies}

    def check_rebalance_needed(self) -> Dict[str, Any]:
        """
        检查是否需要再平衡

        Returns:
            Dict: 检查结果
        """
        if not self.allocations:
            return {"needed": False, "reason": "No strategies"}

        current_weights = {s.strategy_id: s.weight for s in self.allocations.values()}
        target_weights = self.calculate_allocation()

        deviations = {}
        max_deviation = Decimal("0")

        for strategy_id, target in target_weights.items():
            current = current_weights.get(strategy_id, Decimal("0"))
            deviation = abs(target - current)
            deviations[strategy_id] = {
                "current": float(current),
                "target": float(target),
                "deviation": float(deviation)
            }
            max_deviation = max(max_deviation, deviation)

        needed = max_deviation > self.config.rebalance_threshold

        return {
            "needed": needed,
            "max_deviation": float(max_deviation),
            "threshold": float(self.config.rebalance_threshold),
            "deviations": deviations
        }

    def execute_rebalance(
        self,
        force: bool = False
    ) -> Optional[RebalanceResult]:
        """
        执行再平衡

        Args:
            force: 是否强制执行

        Returns:
            RebalanceResult: 再平衡结果
        """
        check = self.check_rebalance_needed()

        if not check["needed"] and not force:
            logger.info("Rebalance not needed")
            return None

        target_weights = self.calculate_allocation()
        trades = []

        for strategy_id, target_weight in target_weights.items():
            if strategy_id not in self.allocations:
                continue

            allocation = self.allocations[strategy_id]
            current_weight = allocation.weight
            weight_change = target_weight - current_weight

            if abs(weight_change) < Decimal("0.001"):
                continue

            target_capital = self.config.total_capital * target_weight
            capital_change = target_capital - allocation.allocated_capital

            trades.append({
                "strategy_id": strategy_id,
                "strategy_name": allocation.strategy_name,
                "action": "INCREASE" if capital_change > 0 else "DECREASE",
                "weight_change": float(weight_change),
                "capital_change": float(capital_change),
                "current_weight": float(current_weight),
                "target_weight": float(target_weight)
            })

            # 更新分配
            allocation.weight = target_weight
            allocation.allocated_capital = target_capital
            allocation.available_capital = target_capital - allocation.used_capital

        # 计算预估成本
        total_trade_value = sum(abs(Decimal(str(t["capital_change"])) for t in trades))
        estimated_cost = total_trade_value * Decimal("0.002")  # 0.2% 交易成本

        result = RebalanceResult(
            rebalance_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            trades=trades,
            estimated_cost=estimated_cost,
            status="COMPLETED"
        )

        self.rebalance_history.append(result)

        # 记录历史
        self._record_allocation_snapshot("REBALANCE")

        logger.info(f"Rebalance completed: {len(trades)} trades, estimated cost: {estimated_cost}")

        return result

    def get_aggregated_risk(self) -> Dict[str, Any]:
        """
        获取聚合风险指标

        Returns:
            Dict: 风险指标
        """
        if not self.allocations:
            return {"total_capital": float(self.config.total_capital)}

        total_used = sum(a.used_capital for a in self.allocations.values())
        total_pnl = sum(a.pnl for a in self.allocations.values())
        total_available = sum(a.available_capital for a in self.allocations.values())

        # 计算集中度
        weights = [float(a.weight) for a in self.allocations.values()]
        herfindahl = sum(w ** 2 for w in weights)

        # 活跃策略数
        active_count = sum(1 for a in self.allocations.values() if a.status == StrategyStatus.ACTIVE)

        return {
            "total_capital": float(self.config.total_capital),
            "total_used": float(total_used),
            "total_available": float(total_available),
            "total_pnl": float(total_pnl),
            "usage_ratio": float(total_used / self.config.total_capital) if self.config.total_capital > 0 else 0,
            "strategy_count": len(self.allocations),
            "active_strategy_count": active_count,
            "herfindahl_index": round(herfindahl, 4),
            "diversification_score": round(1 / herfindahl, 2) if herfindahl > 0 else 0,
            "allocations": [
                {
                    "strategy_id": a.strategy_id,
                    "strategy_name": a.strategy_name,
                    "weight": float(a.weight),
                    "allocated": float(a.allocated_capital),
                    "used": float(a.used_capital),
                    "available": float(a.available_capital),
                    "pnl": float(a.pnl),
                    "status": a.status.value
                }
                for a in self.allocations.values()
            ]
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取绩效汇总"""
        if not self.allocations:
            return {"total_pnl": 0, "win_rate": 0}

        total_pnl = sum(a.pnl for a in self.allocations.values())
        winning = sum(1 for a in self.allocations.values() if a.pnl > 0)
        total = len(self.allocations)

        return {
            "total_pnl": float(total_pnl),
            "total_return": float(total_pnl / self.config.total_capital) if self.config.total_capital > 0 else 0,
            "winning_strategies": winning,
            "losing_strategies": total - winning,
            "win_rate": float(winning / total) if total > 0 else 0,
            "best_strategy": max(
                [(a.strategy_name, float(a.pnl)) for a in self.allocations.values()],
                key=lambda x: x[1],
                default=("N/A", 0)
            ),
            "worst_strategy": min(
                [(a.strategy_name, float(a.pnl)) for a in self.allocations.values()],
                key=lambda x: x[1],
                default=("N/A", 0)
            )
        }

    # ==============================================
    # 内部方法
    # ==============================================

    def _rebalance_weights(self) -> None:
        """重新平衡所有策略权重"""
        active_strategies = [
            s for s in self.allocations.values()
            if s.status == StrategyStatus.ACTIVE
        ]

        if not active_strategies:
            return

        n = len(active_strategies)
        equal_weight = Decimal("1") / Decimal(str(n))

        for allocation in active_strategies:
            allocation.weight = equal_weight
            allocation.allocated_capital = self.config.total_capital * equal_weight
            allocation.available_capital = allocation.allocated_capital - allocation.used_capital

    def _equal_weight_allocation(
        self,
        strategies: List[StrategyAllocation]
    ) -> Dict[str, Decimal]:
        """等权重分配"""
        n = len(strategies)
        weight = Decimal("1") / Decimal(str(n))
        return {s.strategy_id: weight for s in strategies}

    def _risk_parity_allocation(
        self,
        strategies: List[StrategyAllocation]
    ) -> Dict[str, Decimal]:
        """风险平价分配（简化实现）"""
        # 简化实现：使用等权重
        return self._equal_weight_allocation(strategies)

    def _kelly_allocation(
        self,
        strategies: List[StrategyAllocation]
    ) -> Dict[str, Decimal]:
        """凯利公式分配（简化实现）"""
        # 简化实现：使用等权重
        return self._equal_weight_allocation(strategies)

    def _record_allocation_snapshot(self, event: str) -> None:
        """记录分配快照"""
        self.allocation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "allocations": [
                {
                    "strategy_id": a.strategy_id,
                    "weight": float(a.weight),
                    "allocated": float(a.allocated_capital),
                    "used": float(a.used_capital),
                    "pnl": float(a.pnl)
                }
                for a in self.allocations.values()
            ]
        })


# ==============================================
# 策略协调器
# ==============================================

class StrategyCoordinator:
    """
    策略协调器

    协调多个策略的信号和执行，避免冲突。
    """

    def __init__(self, manager: MultiStrategyManager):
        self.manager = manager
        self.pending_signals: Dict[str, List[Any]] = {}
        self.conflict_rules: List[Callable] = []

    def add_conflict_rule(self, rule: Callable):
        """添加冲突规则"""
        self.conflict_rules.append(rule)

    async def submit_signal(
        self,
        strategy_id: str,
        signal: Any
    ) -> Dict[str, Any]:
        """
        提交策略信号

        Args:
            strategy_id: 策略ID
            signal: 交易信号

        Returns:
            Dict: 提交结果
        """
        if strategy_id not in self.manager.allocations:
            return {"accepted": False, "reason": "Strategy not in portfolio"}

        allocation = self.manager.allocations[strategy_id]

        if allocation.status != StrategyStatus.ACTIVE:
            return {"accepted": False, "reason": f"Strategy is {allocation.status.value}"}

        # 检查冲突
        conflicts = self._check_conflicts(strategy_id, signal)
        if conflicts:
            return {"accepted": False, "reason": "Signal conflicts detected", "conflicts": conflicts}

        # 检查资金
        signal_cost = self._calculate_signal_cost(signal)
        if signal_cost > allocation.available_capital:
            return {
                "accepted": False,
                "reason": "Insufficient capital",
                "required": float(signal_cost),
                "available": float(allocation.available_capital)
            }

        # 添加到待处理队列
        if strategy_id not in self.pending_signals:
            self.pending_signals[strategy_id] = []
        self.pending_signals[strategy_id].append(signal)

        return {"accepted": True, "signal_id": str(uuid.uuid4())}

    async def execute_pending_signals(
        self,
        executor: Any
    ) -> List[Dict[str, Any]]:
        """执行待处理信号"""
        results = []

        for strategy_id, signals in self.pending_signals.items():
            for signal in signals:
                try:
                    result = await executor.execute_signal(
                        signal,
                        user_id=strategy_id,  # TODO: 使用实际用户ID
                        execution_mode="PAPER"
                    )
                    results.append({
                        "strategy_id": strategy_id,
                        "signal": signal,
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Signal execution error: {e}")
                    results.append({
                        "strategy_id": strategy_id,
                        "signal": signal,
                        "error": str(e)
                    })

        # 清空待处理队列
        self.pending_signals.clear()

        return results

    def _check_conflicts(
        self,
        strategy_id: str,
        signal: Any
    ) -> List[Dict[str, Any]]:
        """检查信号冲突"""
        conflicts = []

        for rule in self.conflict_rules:
            try:
                conflict = rule(strategy_id, signal, self.pending_signals)
                if conflict:
                    conflicts.append(conflict)
            except Exception as e:
                logger.error(f"Conflict rule error: {e}")

        return conflicts

    def _calculate_signal_cost(self, signal: Any) -> Decimal:
        """计算信号成本"""
        # 简化实现
        if hasattr(signal, 'price') and hasattr(signal, 'quantity'):
            return Decimal(str(signal.price)) * Decimal(str(signal.quantity))
        return Decimal("0")


# ==============================================
# 全局实例
# ==============================================

_manager_instance: Optional[MultiStrategyManager] = None


def get_multi_strategy_manager(
    db: Session,
    config: Optional[MultiStrategyConfig] = None
) -> MultiStrategyManager:
    """获取多策略管理器实例"""
    global _manager_instance
    if _manager_instance is None or _manager_instance.db != db:
        _manager_instance = MultiStrategyManager(db, config)
    return _manager_instance
