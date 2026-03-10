"""
全局风控配置

定义不可覆盖的绝对风险限制。
这些限制由系统强制执行，策略无法绕过。
"""

from typing import Dict, Any, List
from decimal import Decimal
from datetime import time
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class GlobalRiskLimits:
    """
    全局风险限制

    这些是硬编码的绝对限制，不能被用户配置覆盖。
    """

    # ==========================================
    # 仓位限制
    # ==========================================

    # 单票最大仓位比例（50%）
    ABSOLUTE_MAX_SINGLE_POSITION: Decimal = Decimal("0.50")

    # 总仓位上限（100%，不允许杠杆）
    ABSOLUTE_MAX_TOTAL_POSITION: Decimal = Decimal("1.00")

    # 单日最大买入比例
    MAX_DAILY_BUY_RATIO: Decimal = Decimal("0.30")

    # ==========================================
    # 亏损限制
    # ==========================================

    # 单日最大亏损比例（10%）
    ABSOLUTE_MAX_DAILY_LOSS: Decimal = Decimal("0.10")

    # 最大回撤限制（20%）
    ABSOLUTE_MAX_DRAWDOWN: Decimal = "0.20"

    # 连续亏损天数限制
    MAX_CONSECUTIVE_LOSS_DAYS: int = 5

    # ==========================================
    # 交易限制
    # ==========================================

    # 单笔最大订单金额
    MAX_SINGLE_ORDER_VALUE: Decimal = Decimal("10000000")

    # 单日最大交易次数
    MAX_DAILY_TRADES: int = 100

    # 单票单日最大交易次数
    MAX_DAILY_TRADES_PER_SYMBOL: int = 20

    # 最大持仓数量
    MAX_POSITIONS: int = 50

    # ==========================================
    # 杠杆限制
    # ==========================================

    # 是否允许杠杆
    ALLOW_LEVERAGE: bool = False

    # 最大杠杆倍数（如果允许）
    MAX_LEVERAGE: Decimal = Decimal("1.0")

    # ==========================================
    # 交易时间
    # ==========================================

    # A股交易时段
    TRADING_HOURS: List[tuple] = field(default_factory=lambda: [
        (time(9, 30), time(11, 30)),
        (time(13, 0), time(15, 0)),
    ])

    # 是否允许盘前交易
    ALLOW_PRE_MARKET: bool = False

    # 是否允许盘后交易
    ALLOW_AFTER_HOURS: bool = False

    # ==========================================
    # 黑名单
    # ==========================================

    # 永久黑名单（不可交易）
    PERMANENT_BLACKLIST: List[str] = field(default_factory=list)

    # 临时黑名单（如 ST 股票）
    TEMPORARY_BLACKLIST: List[str] = field(default_factory=list)

    # ==========================================
    # 行业限制
    # ==========================================

    # 单行业最大持仓比例
    MAX_INDUSTRY_POSITION: Decimal = Decimal("0.30")

    # 禁止的行业
    FORBIDDEN_INDUSTRIES: List[str] = field(default_factory=list)


# 全局限制实例
GLOBAL_LIMITS = GlobalRiskLimits()


def validate_user_config(user_config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    验证用户配置是否超过全局限制

    Args:
        user_config: 用户配置字典

    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []

    # 检查单票仓位限制
    if "max_single_position" in user_config:
        user_value = Decimal(str(user_config["max_single_position"]))
        if user_value > GLOBAL_LIMITS.ABSOLUTE_MAX_SINGLE_POSITION:
            errors.append(
                f"单票仓位限制 {user_value} 超过系统上限 "
                f"{GLOBAL_LIMITS.ABSOLUTE_MAX_SINGLE_POSITION}"
            )

    # 检查总仓位限制
    if "max_total_position" in user_config:
        user_value = Decimal(str(user_config["max_total_position"]))
        if user_value > GLOBAL_LIMITS.ABSOLUTE_MAX_TOTAL_POSITION:
            errors.append(
                f"总仓位限制 {user_value} 超过系统上限 "
                f"{GLOBAL_LIMITS.ABSOLUTE_MAX_TOTAL_POSITION}"
            )

    # 检查单日亏损限制
    if "max_daily_loss" in user_config:
        user_value = Decimal(str(user_config["max_daily_loss"]))
        if user_value > GLOBAL_LIMITS.ABSOLUTE_MAX_DAILY_LOSS:
            errors.append(
                f"单日亏损限制 {user_value} 超过系统上限 "
                f"{GLOBAL_LIMITS.ABSOLUTE_MAX_DAILY_LOSS}"
            )

    # 检查杠杆限制
    if "leverage" in user_config:
        user_value = Decimal(str(user_config["leverage"]))
        if not GLOBAL_LIMITS.ALLOW_LEVERAGE and user_value > Decimal("1.0"):
            errors.append("系统不允许使用杠杆")
        elif user_value > GLOBAL_LIMITS.MAX_LEVERAGE:
            errors.append(
                f"杠杆倍数 {user_value} 超过系统上限 "
                f"{GLOBAL_LIMITS.MAX_LEVERAGE}"
            )

    return len(errors) == 0, errors


def check_order_against_global_limits(
    order_value: Decimal,
    portfolio_value: Decimal,
    current_position: Decimal,
    daily_trades: int
) -> tuple[bool, str]:
    """
    根据全局限制检查订单

    Args:
        order_value: 订单金额
        portfolio_value: 组合价值
        current_position: 当前持仓价值
        daily_trades: 当日交易次数

    Returns:
        (是否通过, 原因)
    """
    # 检查单笔订单金额
    if order_value > GLOBAL_LIMITS.MAX_SINGLE_ORDER_VALUE:
        return False, f"订单金额 {order_value} 超过单笔上限 {GLOBAL_LIMITS.MAX_SINGLE_ORDER_VALUE}"

    # 检查仓位比例
    if portfolio_value > 0:
        position_ratio = current_position / portfolio_value
        if position_ratio > GLOBAL_LIMITS.ABSOLUTE_MAX_SINGLE_POSITION:
            return False, f"持仓比例 {position_ratio} 超过单票上限 {GLOBAL_LIMITS.ABSOLUTE_MAX_SINGLE_POSITION}"

    # 检查交易次数
    if daily_trades >= GLOBAL_LIMITS.MAX_DAILY_TRADES:
        return False, f"当日交易次数 {daily_trades} 已达上限 {GLOBAL_LIMITS.MAX_DAILY_TRADES}"

    return True, "通过全局限制检查"


def is_trading_hours() -> bool:
    """检查当前是否在交易时段"""
    from datetime import datetime

    now = datetime.now().time()

    for start, end in GLOBAL_LIMITS.TRADING_HOURS:
        if start <= now <= end:
            return True

    return False


def get_global_limits_summary() -> Dict[str, Any]:
    """获取全局限制摘要"""
    return {
        "position_limits": {
            "max_single_position": f"{float(GLOBAL_LIMITS.ABSOLUTE_MAX_SINGLE_POSITION) * 100:.0f}%",
            "max_total_position": f"{float(GLOBAL_LIMITS.ABSOLUTE_MAX_TOTAL_POSITION) * 100:.0f}%",
        },
        "loss_limits": {
            "max_daily_loss": f"{float(GLOBAL_LIMITS.ABSOLUTE_MAX_DAILY_LOSS) * 100:.0f}%",
            "max_drawdown": f"{float(GLOBAL_LIMITS.ABSOLUTE_MAX_DRAWDOWN) * 100:.0f}%",
        },
        "trade_limits": {
            "max_single_order": f"{float(GLOBAL_LIMITS.MAX_SINGLE_ORDER_VALUE):,.0f}",
            "max_daily_trades": GLOBAL_LIMITS.MAX_DAILY_TRADES,
            "max_positions": GLOBAL_LIMITS.MAX_POSITIONS,
        },
        "leverage": {
            "allowed": GLOBAL_LIMITS.ALLOW_LEVERAGE,
            "max_leverage": float(GLOBAL_LIMITS.MAX_LEVERAGE),
        },
    }
