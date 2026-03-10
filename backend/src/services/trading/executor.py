"""
==============================================
QuantAI Ecosystem - 实时交易执行引擎
==============================================

提供策略信号到订单执行的完整流程管理。
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Callable
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ==============================================
# 数据模型
# ==============================================

class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SignalType(str, Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradingSignal:
    """交易信号"""
    symbol: str
    signal_type: SignalType
    quantity: int
    price: Optional[Decimal] = None
    confidence: float = 1.0
    reason: str = ""
    strategy_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    order_id: Optional[str] = None
    fills: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    message: str = ""


@dataclass
class ExecutionConfig:
    """执行配置"""
    execution_mode: str = "PAPER"  # PAPER 或 LIVE
    order_type: str = "LIMIT"  # LIMIT, MARKET, STOP
    time_in_force: str = "GTC"  # GTC, IOC, FOK
    slippage_tolerance: Decimal = Decimal("0.001")  # 0.1% 滑点容忍度
    max_retries: int = 3
    retry_delay: float = 1.0  # 重试延迟秒数
    auto_cancel_on_error: bool = True


# ==============================================
# 交易执行引擎
# ==============================================

class TradingExecutor:
    """
    实时交易执行引擎

    负责将策略信号转换为订单并执行，包括：
    - 信号验证
    - 风控检查
    - 订单创建
    - 订单执行
    - 成交处理
    - 持仓更新
    """

    def __init__(
        self,
        db: Session,
        config: Optional[ExecutionConfig] = None
    ):
        """
        初始化交易执行引擎

        Args:
            db: 数据库会话
            config: 执行配置
        """
        self.db = db
        self.config = config or ExecutionConfig()

        # 内部状态
        self.pending_orders: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []

    async def execute_signal(
        self,
        signal: TradingSignal,
        user_id: str,
        execution_mode: Optional[str] = None
    ) -> ExecutionResult:
        """
        执行交易信号

        Args:
            signal: 交易信号
            user_id: 用户ID
            execution_mode: 执行模式（覆盖默认配置）

        Returns:
            ExecutionResult: 执行结果
        """
        mode = execution_mode or self.config.execution_mode

        logger.info(
            f"Executing signal: {signal.signal_type.value} {signal.quantity} {signal.symbol} "
            f"for user {user_id} (mode: {mode})"
        )

        # 1. 验证信号
        validation_result = self._validate_signal(signal)
        if not validation_result["valid"]:
            return ExecutionResult(
                success=False,
                error=validation_result["error"],
                message="Signal validation failed"
            )

        # 2. 执行风控检查
        risk_result = await self._check_risk(signal, user_id, mode)
        if not risk_result["passed"]:
            return ExecutionResult(
                success=False,
                error=risk_result["message"],
                message="Risk check failed"
            )

        # 3. 创建订单
        order_result = await self._create_order(signal, user_id, mode)
        if not order_result["success"]:
            return ExecutionResult(
                success=False,
                error=order_result.get("error"),
                message="Order creation failed"
            )

        order_id = order_result["order_id"]

        # 4. 执行订单
        execution_result = await self._execute_order(order_id, signal, mode)
        if not execution_result["success"]:
            return ExecutionResult(
                success=False,
                order_id=order_id,
                error=execution_result.get("error"),
                message="Order execution failed"
            )

        # 5. 记录执行历史
        self._record_execution(signal, order_id, execution_result, mode)

        return ExecutionResult(
            success=True,
            order_id=order_id,
            fills=execution_result.get("fills", []),
            message="Signal executed successfully"
        )

    async def execute_signals_batch(
        self,
        signals: List[TradingSignal],
        user_id: str,
        execution_mode: Optional[str] = None
    ) -> List[ExecutionResult]:
        """
        批量执行交易信号

        Args:
            signals: 交易信号列表
            user_id: 用户ID
            execution_mode: 执行模式

        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        results = []

        for signal in signals:
            result = await self.execute_signal(signal, user_id, execution_mode)
            results.append(result)

            # 如果执行失败且配置了自动取消，停止后续执行
            if not result.success and self.config.auto_cancel_on_error:
                logger.warning(f"Stopping batch execution due to error: {result.error}")
                break

        return results

    async def cancel_order(
        self,
        order_id: str,
        user_id: str,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        撤销订单

        Args:
            order_id: 订单ID
            user_id: 用户ID
            reason: 撤销原因

        Returns:
            Dict: 撤销结果
        """
        from ...models.trading import Order

        order = self.db.query(Order).filter(Order.id == order_id).first()

        if not order:
            return {"success": False, "error": "Order not found"}

        if str(order.user_id) != user_id:
            return {"success": False, "error": "Unauthorized"}

        if order.status not in ["PENDING", "SUBMITTED", "PARTIAL_FILLED"]:
            return {"success": False, "error": f"Cannot cancel order in {order.status} status"}

        # 更新订单状态
        order.status = "CANCELED"
        order.update_time = datetime.utcnow()
        self.db.commit()

        logger.info(f"Order {order_id} canceled: {reason}")

        return {
            "success": True,
            "order_id": order_id,
            "status": "CANCELED",
            "reason": reason
        }

    async def get_order_status(
        self,
        order_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        获取订单状态

        Args:
            order_id: 订单ID
            user_id: 用户ID

        Returns:
            Dict: 订单状态
        """
        from ...models.trading import Order, Fill

        order = self.db.query(Order).filter(Order.id == order_id).first()

        if not order:
            return {"error": "Order not found"}

        if str(order.user_id) != user_id:
            return {"error": "Unauthorized"}

        # 获取成交记录
        fills = self.db.query(Fill).filter(Fill.order_id == order_id).all()

        return {
            "order_id": str(order.id),
            "symbol": order.ts_code,
            "side": order.side,
            "status": order.status,
            "quantity": order.quantity,
            "price": float(order.price),
            "filled_quantity": order.filled_quantity,
            "avg_price": float(order.avg_price),
            "execution_mode": order.execution_mode,
            "fills": [
                {
                    "fill_id": str(f.id),
                    "quantity": f.quantity,
                    "price": float(f.price),
                    "time": f.fill_time.isoformat() if f.fill_time else None
                }
                for f in fills
            ],
            "create_time": order.create_time.isoformat() if order.create_time else None,
            "update_time": order.update_time.isoformat() if order.update_time else None
        }

    def get_execution_history(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取执行历史

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            List: 执行历史列表
        """
        return [
            h for h in self.execution_history
            if h.get("user_id") == user_id
        ][-limit:]

    # ==============================================
    # 内部方法
    # ==============================================

    def _validate_signal(self, signal: TradingSignal) -> Dict[str, Any]:
        """验证交易信号"""
        # 检查股票代码
        if not signal.symbol or len(signal.symbol) < 6:
            return {"valid": False, "error": "Invalid symbol"}

        # 检查数量
        if signal.quantity <= 0:
            return {"valid": False, "error": "Invalid quantity"}

        # 检查信号类型
        if signal.signal_type == SignalType.HOLD:
            return {"valid": False, "error": "HOLD signal cannot be executed"}

        # 检查价格（限价单必须有价格）
        if self.config.order_type == "LIMIT" and signal.price is None:
            return {"valid": False, "error": "Limit order requires price"}

        return {"valid": True}

    async def _check_risk(
        self,
        signal: TradingSignal,
        user_id: str,
        execution_mode: str
    ) -> Dict[str, Any]:
        """执行风控检查"""
        from ..risk import RiskControlEngine

        risk_engine = RiskControlEngine()

        try:
            check_results = risk_engine.validate_order(
                db=self.db,
                user_id=user_id,
                symbol=signal.symbol,
                side=signal.signal_type.value,
                quantity=signal.quantity,
                price=signal.price or Decimal("0"),
                execution_mode=execution_mode
            )

            failed_checks = [r for r in check_results if not r.passed]

            if failed_checks:
                return {
                    "passed": False,
                    "message": "; ".join(r.message for r in failed_checks),
                    "failed_checks": [
                        {"type": r.check_type, "message": r.message}
                        for r in failed_checks
                    ]
                }

            return {"passed": True}

        except Exception as e:
            logger.error(f"Risk check error: {e}")
            return {"passed": False, "message": str(e)}

    async def _create_order(
        self,
        signal: TradingSignal,
        user_id: str,
        execution_mode: str
    ) -> Dict[str, Any]:
        """创建订单"""
        from ...models.trading import Order

        try:
            order = Order(
                id=str(uuid.uuid4()),
                user_id=user_id,
                ts_code=signal.symbol,
                side=signal.signal_type.value,
                order_type=self.config.order_type,
                quantity=signal.quantity,
                price=signal.price or Decimal("0"),
                execution_mode=execution_mode,
                status="PENDING",
                filled_quantity=0,
                avg_price=Decimal("0"),
                strategy_id=signal.strategy_id,
                create_time=datetime.utcnow(),
                update_time=datetime.utcnow()
            )

            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)

            # 记录待处理订单
            self.pending_orders[str(order.id)] = {
                "order": order,
                "signal": signal,
                "created_at": datetime.utcnow()
            }

            return {"success": True, "order_id": str(order.id)}

        except Exception as e:
            logger.error(f"Order creation error: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_order(
        self,
        order_id: str,
        signal: TradingSignal,
        execution_mode: str
    ) -> Dict[str, Any]:
        """执行订单"""
        from ...models.trading import Order

        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "error": "Order not found"}

        # 根据执行模式选择执行器
        if execution_mode == "PAPER":
            result = await self._execute_paper_order(order, signal)
        else:
            result = await self._execute_live_order(order, signal)

        return result

    async def _execute_paper_order(
        self,
        order: Any,
        signal: TradingSignal
    ) -> Dict[str, Any]:
        """执行模拟订单"""
        from .fill_service import FillService

        try:
            # 模拟成交（假设立即全部成交）
            fills = []

            # 模拟滑点
            price = signal.price or Decimal("0")
            if self.config.slippage_tolerance > 0:
                import random
                slippage = random.uniform(
                    -float(self.config.slippage_tolerance),
                    float(self.config.slippage_tolerance)
                )
                price = price * Decimal(str(1 + slippage))

            # 更新订单状态
            order.status = "FILLED"
            order.filled_quantity = order.quantity
            order.avg_price = price
            order.update_time = datetime.utcnow()

            # 记录成交
            fill_service = FillService(self.db)

            fill = fill_service.record_fill(
                order_id=str(order.id),
                user_id=str(order.user_id),
                symbol=signal.symbol,
                side=signal.signal_type.value,
                quantity=order.quantity,
                price=price,
                execution_mode="PAPER",
                strategy_id=signal.strategy_id
            )

            fills.append({
                "fill_id": str(fill.id),
                "quantity": fill.quantity,
                "price": float(fill.price),
                "time": fill.fill_time.isoformat()
            })

            self.db.commit()

            # 更新持仓
            await self._update_position(order, price)

            # 从待处理列表中移除
            if str(order.id) in self.pending_orders:
                del self.pending_orders[str(order.id)]

            return {
                "success": True,
                "fills": fills,
                "avg_price": float(price)
            }

        except Exception as e:
            logger.error(f"Paper order execution error: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_live_order(
        self,
        order: Any,
        signal: TradingSignal
    ) -> Dict[str, Any]:
        """执行实盘订单"""
        # TODO: 实现实盘交易接口对接
        # 这里需要对接券商API（如华泰、中信等）

        logger.warning("Live trading not implemented yet, falling back to paper trading")

        # 暂时使用模拟交易
        return await self._execute_paper_order(order, signal)

    async def _update_position(
        self,
        order: Any,
        fill_price: Decimal
    ) -> None:
        """更新持仓"""
        from ...models.trading import Position

        try:
            # 查找现有持仓
            position = self.db.query(Position).filter(
                Position.user_id == order.user_id,
                Position.ts_code == order.ts_code,
                Position.execution_mode == order.execution_mode
            ).first()

            if order.side == "BUY":
                if position:
                    # 更新现有持仓
                    total_cost = position.avg_cost * position.quantity + fill_price * order.filled_quantity
                    position.quantity += order.filled_quantity
                    position.avg_cost = total_cost / position.quantity if position.quantity > 0 else Decimal("0")
                    position.market_value = fill_price * position.quantity
                else:
                    # 创建新持仓
                    position = Position(
                        id=str(uuid.uuid4()),
                        user_id=order.user_id,
                        ts_code=order.ts_code,
                        quantity=order.filled_quantity,
                        avg_cost=fill_price,
                        current_price=fill_price,
                        market_value=fill_price * order.filled_quantity,
                        execution_mode=order.execution_mode,
                        create_time=datetime.utcnow(),
                        update_time=datetime.utcnow()
                    )
                    self.db.add(position)

            elif order.side == "SELL":
                if position:
                    # 计算已实现盈亏
                    realized_pnl = (fill_price - position.avg_cost) * order.filled_quantity
                    position.realized_pnl = (position.realized_pnl or 0) + realized_pnl
                    position.quantity -= order.filled_quantity

                    if position.quantity <= 0:
                        position.quantity = 0
                        position.market_value = Decimal("0")
                    else:
                        position.market_value = fill_price * position.quantity

            self.db.commit()

        except Exception as e:
            logger.error(f"Position update error: {e}")

    def _record_execution(
        self,
        signal: TradingSignal,
        order_id: str,
        execution_result: Dict[str, Any],
        execution_mode: str
    ) -> None:
        """记录执行历史"""
        self.execution_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "signal": {
                "symbol": signal.symbol,
                "type": signal.signal_type.value,
                "quantity": signal.quantity,
                "price": float(signal.price) if signal.price else None,
                "strategy_id": signal.strategy_id
            },
            "order_id": order_id,
            "success": execution_result.get("success", False),
            "fills": execution_result.get("fills", []),
            "execution_mode": execution_mode
        })


# ==============================================
# 信号处理器
# ==============================================

class SignalProcessor:
    """
    信号处理器

    负责从策略引擎接收信号并分发到执行引擎。
    """

    def __init__(self, executor: TradingExecutor):
        self.executor = executor
        self.signal_handlers: List[Callable] = []

    def register_handler(self, handler: Callable):
        """注册信号处理器"""
        self.signal_handlers.append(handler)

    async def process_signal(
        self,
        signal: TradingSignal,
        user_id: str,
        execution_mode: Optional[str] = None
    ) -> ExecutionResult:
        """处理信号"""
        # 调用所有注册的处理器
        for handler in self.signal_handlers:
            try:
                await handler(signal, user_id)
            except Exception as e:
                logger.error(f"Signal handler error: {e}")

        # 执行信号
        return await self.executor.execute_signal(signal, user_id, execution_mode)

    async def process_strategy_signals(
        self,
        strategy_id: str,
        user_id: str,
        execution_mode: Optional[str] = None
    ) -> List[ExecutionResult]:
        """处理策略生成的所有信号"""
        # TODO: 从策略引擎获取信号
        return []


# ==============================================
# 全局实例
# ==============================================

_executor_instance: Optional[TradingExecutor] = None


def get_executor(db: Session, config: Optional[ExecutionConfig] = None) -> TradingExecutor:
    """获取交易执行器实例"""
    global _executor_instance
    if _executor_instance is None or _executor_instance.db != db:
        _executor_instance = TradingExecutor(db, config)
    return _executor_instance
