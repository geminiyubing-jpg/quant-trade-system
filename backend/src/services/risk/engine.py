"""
==============================================
QuantAI Ecosystem - 风控规则引擎
==============================================

提供风险控制和合规检查的核心引擎。
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from .models import (
    RiskCheckResult,
    RiskCheckType,
    RiskRuleConfig,
    RiskMetrics,
)
from .checks import (
    PositionLimitChecker,
    StopLossChecker,
    TakeProfitChecker,
    DailyLossLimitChecker,
    OrderSizeChecker,
    ConcentrationChecker,
)


class RiskControlEngine:
    """
    风控规则引擎

    整合所有风控检查模块，提供统一的风控检查接口。
    """

    def __init__(self, config: Optional[RiskRuleConfig] = None):
        """
        初始化风控引擎

        Args:
            config: 风控规则配置
        """
        self.config = config or RiskRuleConfig()

        # 初始化所有检查器
        self.checkers = {
            RiskCheckType.POSITION_LIMIT: PositionLimitChecker(self.config),
            RiskCheckType.STOP_LOSS: StopLossChecker(self.config),
            RiskCheckType.TAKE_PROFIT: TakeProfitChecker(self.config),
            RiskCheckType.DAILY_LOSS_LIMIT: DailyLossLimitChecker(self.config),
            RiskCheckType.ORDER_SIZE: OrderSizeChecker(self.config),
            RiskCheckType.CONCENTRATION: ConcentrationChecker(self.config),
        }

    def validate_order(
        self,
        db: Session,
        user_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal,
        execution_mode: str,
        **kwargs
    ) -> List[RiskCheckResult]:
        """
        验证订单是否符合风控规则

        Args:
            db: 数据库会话
            user_id: 用户 ID
            symbol: 股票代码
            side: 买卖方向（BUY/SELL）
            quantity: 数量
            price: 价格
            execution_mode: 执行模式（PAPER/LIVE）
            **kwargs: 其他参数

        Returns:
            List[RiskCheckResult]: 所有检查结果
        """
        results = []

        # 1. 订单大小检查
        order_size_result = self.checkers[RiskCheckType.ORDER_SIZE].check(
            order_quantity=quantity
        )
        results.append(order_size_result)

        # 2. 获取用户风险指标
        metrics = self._calculate_risk_metrics(
            db=db,
            user_id=user_id,
            execution_mode=execution_mode
        )

        # 计算订单金额
        order_value = Decimal(quantity) * price

        # 3. 持仓限制检查
        position_limit_result = self.checkers[RiskCheckType.POSITION_LIMIT].check(
            order_value=order_value,
            total_account_value=metrics.total_market_value + Decimal("100000"),  # 假设初始资金 10 万
        )
        results.append(position_limit_result)

        # 4. 持仓集中度检查
        current_position = self._get_position_value(
            db=db,
            user_id=user_id,
            symbol=symbol,
            execution_mode=execution_mode
        )
        new_position_value = current_position + order_value

        concentration_result = self.checkers[RiskCheckType.CONCENTRATION].check(
            symbol_market_value=new_position_value,
            total_account_value=metrics.total_market_value + Decimal("100000"),
        )
        results.append(concentration_result)

        # 5. 单日亏损限制检查
        daily_loss_result = self.checkers[RiskCheckType.DAILY_LOSS_LIMIT].check(
            daily_pnl=metrics.daily_pnl,
            total_account_value=metrics.total_market_value + Decimal("100000"),
        )
        results.append(daily_loss_result)

        # 如果是卖出订单，检查止损/止盈
        if side == "SELL":
            entry_price = self._get_entry_price(
                db=db,
                user_id=user_id,
                symbol=symbol,
                execution_mode=execution_mode
            )

            if entry_price is not None:
                # 止损检查
                stop_loss_result = self.checkers[RiskCheckType.STOP_LOSS].check(
                    current_price=price,
                    entry_price=entry_price
                )
                results.append(stop_loss_result)

                # 止盈检查
                take_profit_result = self.checkers[RiskCheckType.TAKE_PROFIT].check(
                    current_price=price,
                    entry_price=entry_price
                )
                results.append(take_profit_result)

        return results

    def check_position_risk(
        self,
        db: Session,
        user_id: str,
        symbol: str,
        execution_mode: str,
        **kwargs
    ) -> List[RiskCheckResult]:
        """
        检查持仓风险

        Args:
            db: 数据库会话
            user_id: 用户 ID
            symbol: 股票代码
            execution_mode: 执行模式
            **kwargs: 其他参数

        Returns:
            List[RiskCheckResult]: 所有检查结果
        """
        results = []

        # 获取持仓信息
        position = self._get_position(
            db=db,
            user_id=user_id,
            symbol=symbol,
            execution_mode=execution_mode
        )

        if position is None:
            return results

        # 获取风险指标
        metrics = self._calculate_risk_metrics(
            db=db,
            user_id=user_id,
            execution_mode=execution_mode
        )

        # 检查止损
        if self.config.stop_loss_ratio is not None:
            stop_loss_result = self.checkers[RiskCheckType.STOP_LOSS].check(
                current_price=Decimal(str(position.get("current_price", 0))),
                entry_price=Decimal(str(position.get("entry_price", 0)))
            )
            results.append(stop_loss_result)

        # 检查止盈
        if self.config.take_profit_ratio is not None:
            take_profit_result = self.checkers[RiskCheckType.TAKE_PROFIT].check(
                current_price=Decimal(str(position.get("current_price", 0))),
                entry_price=Decimal(str(position.get("entry_price", 0)))
            )
            results.append(take_profit_result)

        return results

    def get_all_risk_alerts(
        self,
        db: Session,
        user_id: str,
        execution_mode: str,
        **kwargs
    ) -> List[RiskCheckResult]:
        """
        获取所有风险告警

        Args:
            db: 数据库会话
            user_id: 用户 ID
            execution_mode: 执行模式
            **kwargs: 其他参数

        Returns:
            List[RiskCheckResult]: 所有风险告警
        """
        alerts = []

        # 获取风险指标
        metrics = self._calculate_risk_metrics(
            db=db,
            user_id=user_id,
            execution_mode=execution_mode
        )

        # 检查单日亏损限制
        daily_loss_result = self.checkers[RiskCheckType.DAILY_LOSS_LIMIT].check(
            daily_pnl=metrics.daily_pnl,
            total_account_value=metrics.total_market_value + Decimal("100000"),
        )
        if not daily_loss_result.passed:
            alerts.append(daily_loss_result)

        return alerts

    def _calculate_risk_metrics(
        self,
        db: Session,
        user_id: str,
        execution_mode: str
    ) -> RiskMetrics:
        """
        计算风险指标

        Args:
            db: 数据库会话
            user_id: 用户 ID
            execution_mode: 执行模式

        Returns:
            RiskMetrics: 风险指标
        """
        # TODO: 从数据库查询实际的风险指标
        # 这里先返回默认值
        return RiskMetrics(
            total_market_value=Decimal("0"),
            total_cost=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            daily_pnl=Decimal("0"),
            position_count=0,
            max_single_position_ratio=Decimal("0")
        )

    def _get_position_value(
        self,
        db: Session,
        user_id: str,
        symbol: str,
        execution_mode: str
    ) -> Decimal:
        """获取持仓市值"""
        # TODO: 从数据库查询
        return Decimal("0")

    def _get_entry_price(
        self,
        db: Session,
        user_id: str,
        symbol: str,
        execution_mode: str
    ) -> Optional[Decimal]:
        """获取成本价"""
        # TODO: 从数据库查询
        return None

    def _get_position(
        self,
        db: Session,
        user_id: str,
        symbol: str,
        execution_mode: str
    ) -> Optional[Dict[str, Any]]:
        """获取持仓信息"""
        # TODO: 从数据库查询
        return None
