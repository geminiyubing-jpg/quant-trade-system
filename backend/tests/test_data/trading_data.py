"""
交易数据测试工厂

提供订单、成交、账户等交易相关测试数据生成函数。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import random
import string
import uuid


def random_string(length: int = 6) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


def random_order_id() -> str:
    """生成订单ID"""
    return f"ord_{uuid.uuid4().hex[:12]}"


def random_trade_id() -> str:
    """生成成交ID"""
    return f"trd_{uuid.uuid4().hex[:12]}"


def create_mock_order(
    order_id: Optional[str] = None,
    symbol: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建订单测试数据

    Args:
        order_id: 订单ID
        symbol: 股票代码
        **kwargs: 其他自定义字段

    Returns:
        订单数据字典
    """
    if order_id is None:
        order_id = random_order_id()

    if symbol is None:
        symbol = f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}"

    side = kwargs.get("side", random.choice(["BUY", "SELL"]))
    order_type = kwargs.get("order_type", random.choice(["LIMIT", "MARKET", "STOP", "STOP_LIMIT"]))
    quantity = kwargs.get("quantity", random.randint(100, 10000))
    price = kwargs.get("price", Decimal(str(round(random.uniform(10, 200), 2))))

    status = kwargs.get("status", random.choice([
        "PENDING", "SUBMITTED", "PARTIAL_FILLED", "FILLED", "CANCELLED", "REJECTED"
    ]))

    filled_quantity = 0
    if status == "FILLED":
        filled_quantity = quantity
    elif status == "PARTIAL_FILLED":
        filled_quantity = random.randint(1, quantity - 1)

    return {
        "id": order_id,
        "portfolio_id": kwargs.get("portfolio_id", f"pf_{random_string(8).lower()}"),
        "strategy_id": kwargs.get("strategy_id", f"stg_{random_string(8).lower()}"),
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": float(price),
        "filled_quantity": filled_quantity,
        "avg_fill_price": float(kwargs.get("avg_fill_price", price if filled_quantity > 0 else 0)),
        "status": status,
        "time_in_force": kwargs.get("time_in_force", random.choice(["DAY", "GTC", "IOC", "FOK"])),
        "stop_price": float(kwargs.get("stop_price", price * Decimal("0.95"))) if "STOP" in order_type else None,
        "commission": float(kwargs.get("commission", round(random.uniform(1, 50), 2))),
        "slippage": float(kwargs.get("slippage", round(random.uniform(0, 0.5), 4))),
        "created_at": kwargs.get("created_at", datetime.now().isoformat()),
        "updated_at": kwargs.get("updated_at", datetime.now().isoformat()),
        "submitted_at": kwargs.get("submitted_at", datetime.now().isoformat() if status != "PENDING" else None),
        "filled_at": kwargs.get("filled_at", datetime.now().isoformat() if filled_quantity > 0 else None),
        "notes": kwargs.get("notes"),
        "error_message": kwargs.get("error_message"),
    }


def create_mock_orders(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    创建订单列表测试数据

    Args:
        count: 订单数量
        **kwargs: 传递给 create_mock_order 的参数

    Returns:
        订单列表
    """
    return [create_mock_order(**kwargs) for _ in range(count)]


def create_mock_trade(
    trade_id: Optional[str] = None,
    order_id: Optional[str] = None,
    symbol: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建成交测试数据

    Args:
        trade_id: 成交ID
        order_id: 关联订单ID
        symbol: 股票代码
        **kwargs: 其他自定义字段

    Returns:
        成交数据字典
    """
    if trade_id is None:
        trade_id = random_trade_id()

    if order_id is None:
        order_id = random_order_id()

    if symbol is None:
        symbol = f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}"

    quantity = kwargs.get("quantity", random.randint(100, 10000))
    price = kwargs.get("price", Decimal(str(round(random.uniform(10, 200), 2))))

    return {
        "id": trade_id,
        "order_id": order_id,
        "portfolio_id": kwargs.get("portfolio_id", f"pf_{random_string(8).lower()}"),
        "strategy_id": kwargs.get("strategy_id", f"stg_{random_string(8).lower()}"),
        "symbol": symbol,
        "side": kwargs.get("side", random.choice(["BUY", "SELL"])),
        "quantity": quantity,
        "price": float(price),
        "amount": float(quantity * price),
        "commission": float(kwargs.get("commission", round(random.uniform(1, 50), 2))),
        "tax": float(kwargs.get("tax", round(random.uniform(0.5, 20), 2))),
        "slippage": float(kwargs.get("slippage", round(random.uniform(0, 0.5), 4))),
        "executed_at": kwargs.get("executed_at", datetime.now().isoformat()),
        "venue": kwargs.get("venue", random.choice(["XSHG", "XSHE", "SMART", "DMA"])),
        "counterparty": kwargs.get("counterparty"),
        "notes": kwargs.get("notes"),
    }


def create_mock_trades(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    创建成交列表测试数据

    Args:
        count: 成交数量
        **kwargs: 传递给 create_mock_trade 的参数

    Returns:
        成交列表
    """
    return [create_mock_trade(**kwargs) for _ in range(count)]


def create_mock_account_info(
    account_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建账户信息测试数据

    Args:
        account_id: 账户ID
        **kwargs: 其他自定义字段

    Returns:
        账户信息数据字典
    """
    if account_id is None:
        account_id = f"acc_{random_string(8).lower()}"

    cash_balance = kwargs.get("cash_balance", Decimal(str(round(random.uniform(10000, 1000000), 2))))
    market_value = kwargs.get("market_value", Decimal(str(round(random.uniform(50000, 5000000), 2))))
    total_value = cash_balance + market_value

    return {
        "id": account_id,
        "user_id": kwargs.get("user_id", f"user_{random_string(8).lower()}"),
        "account_type": kwargs.get("account_type", random.choice(["CASH", "MARGIN", "FUTURES"])),
        "currency": kwargs.get("currency", "CNY"),
        "cash_balance": float(cash_balance),
        "available_cash": float(kwargs.get("available_cash", cash_balance * Decimal("0.8"))),
        "frozen_cash": float(kwargs.get("frozen_cash", cash_balance * Decimal("0.2"))),
        "market_value": float(market_value),
        "total_value": float(total_value),
        "total_pnl": float(kwargs.get("total_pnl", random.uniform(-50000, 200000))),
        "realized_pnl": float(kwargs.get("realized_pnl", random.uniform(-30000, 100000))),
        "unrealized_pnl": float(kwargs.get("unrealized_pnl", random.uniform(-20000, 100000))),
        "margin_used": float(kwargs.get("margin_used", random.uniform(0, 500000))),
        "margin_available": float(kwargs.get("margin_available", random.uniform(10000, 1000000))),
        "buying_power": float(kwargs.get("buying_power", random.uniform(50000, 2000000))),
        "risk_level": kwargs.get("risk_level", random.choice(["LOW", "MEDIUM", "HIGH"])),
        "status": kwargs.get("status", random.choice(["ACTIVE", "FROZEN", "CLOSED"])),
        "created_at": kwargs.get("created_at", (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()),
        "updated_at": kwargs.get("updated_at", datetime.now().isoformat()),
    }


def create_mock_position_summary(
    symbol: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建持仓汇总测试数据

    Args:
        symbol: 股票代码
        **kwargs: 其他自定义字段

    Returns:
        持仓汇总数据字典
    """
    if symbol is None:
        symbol = f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}"

    quantity = kwargs.get("quantity", random.randint(100, 10000))
    avg_cost = kwargs.get("avg_cost", Decimal(str(round(random.uniform(10, 200), 2))))
    current_price = kwargs.get("current_price", avg_cost * Decimal(str(random.uniform(0.8, 1.2))))
    market_value = quantity * current_price
    unrealized_pnl = (current_price - avg_cost) * quantity

    return {
        "symbol": symbol,
        "name": kwargs.get("name", f"股票{random_string(4)}"),
        "quantity": quantity,
        "available_quantity": kwargs.get("available_quantity", quantity - random.randint(0, quantity // 10)),
        "frozen_quantity": kwargs.get("frozen_quantity", random.randint(0, quantity // 10)),
        "avg_cost": float(avg_cost),
        "current_price": float(current_price),
        "market_value": float(market_value),
        "unrealized_pnl": float(unrealized_pnl),
        "realized_pnl": float(kwargs.get("realized_pnl", random.uniform(-10000, 50000))),
        "today_pnl": float(kwargs.get("today_pnl", random.uniform(-5000, 10000))),
        "cost_basis": float(kwargs.get("cost_basis", quantity * avg_cost)),
        "weight": float(kwargs.get("weight", round(random.uniform(0.01, 0.2), 4))),
        "sector": kwargs.get("sector", random.choice([
            "银行", "证券", "保险", "半导体", "计算机", "医药生物", "白酒", "新能源"
        ])),
    }


def create_mock_daily_trade_stats(
    date: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建每日交易统计测试数据

    Args:
        date: 日期
        **kwargs: 其他自定义字段

    Returns:
        每日交易统计数据字典
    """
    if date is None:
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")

    total_trades = kwargs.get("total_trades", random.randint(5, 50))
    winning_trades = kwargs.get("winning_trades", random.randint(2, total_trades // 2))
    losing_trades = total_trades - winning_trades

    return {
        "date": date,
        "portfolio_id": kwargs.get("portfolio_id", f"pf_{random_string(8).lower()}"),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(winning_trades / total_trades, 4) if total_trades > 0 else 0,
        "total_volume": kwargs.get("total_volume", random.randint(10000, 500000)),
        "total_amount": kwargs.get("total_amount", random.uniform(100000, 10000000)),
        "total_commission": kwargs.get("total_commission", random.uniform(10, 500)),
        "total_slippage": kwargs.get("total_slippage", random.uniform(0, 100)),
        "realized_pnl": kwargs.get("realized_pnl", random.uniform(-50000, 100000)),
        "unrealized_pnl": kwargs.get("unrealized_pnl", random.uniform(-30000, 50000)),
        "avg_trade_size": kwargs.get("avg_trade_size", random.uniform(1000, 50000)),
        "max_trade_size": kwargs.get("max_trade_size", random.uniform(5000, 100000)),
        "avg_holding_time": kwargs.get("avg_holding_time", random.uniform(1, 120)),  # 分钟
    }
