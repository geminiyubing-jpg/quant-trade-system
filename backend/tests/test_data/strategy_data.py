"""
策略数据测试工厂

提供策略、回测结果、信号等策略相关测试数据生成函数。
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


def random_strategy_id() -> str:
    """生成策略ID"""
    return f"stg_{uuid.uuid4().hex[:12]}"


def create_mock_strategy(
    strategy_id: Optional[str] = None,
    name: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建策略测试数据

    Args:
        strategy_id: 策略ID
        name: 策略名称
        **kwargs: 其他自定义字段

    Returns:
        策略数据字典
    """
    if strategy_id is None:
        strategy_id = random_strategy_id()

    if name is None:
        strategy_names = [
            "双均线交叉", "动量突破", "均值回归", "RSI反转",
            "布林带突破", "MACD背离", "量价策略", "多因子选股",
            "趋势跟踪", "统计套利", "Alpha因子", "事件驱动",
        ]
        name = random.choice(strategy_names)

    strategy_types = ["TREND", "MEAN_REVERSION", "MOMENTUM", "ARBITRAGE", "FACTOR", "EVENT"]
    status_list = ["DRAFT", "TESTING", "ACTIVE", "PAUSED", "ARCHIVED"]

    return {
        "id": strategy_id,
        "user_id": kwargs.get("user_id", f"user_{random_string(8).lower()}"),
        "name": name,
        "description": kwargs.get("description", f"{name}策略的详细描述"),
        "type": kwargs.get("type", random.choice(strategy_types)),
        "status": kwargs.get("status", random.choice(status_list)),
        "version": kwargs.get("version", f"v{random.randint(1, 5)}.{random.randint(0, 9)}"),

        # 策略参数
        "parameters": kwargs.get("parameters", {
            "lookback_period": random.randint(10, 60),
            "entry_threshold": round(random.uniform(0.01, 0.05), 4),
            "exit_threshold": round(random.uniform(0.01, 0.05), 4),
            "position_size": round(random.uniform(0.05, 0.2), 4),
            "stop_loss": round(random.uniform(0.02, 0.1), 4),
            "take_profit": round(random.uniform(0.05, 0.2), 4),
        }),

        # 风险控制
        "risk_config": kwargs.get("risk_config", {
            "max_position": round(random.uniform(0.1, 0.3), 4),
            "max_drawdown": round(random.uniform(0.1, 0.3), 4),
            "max_daily_trades": random.randint(5, 20),
            "max_single_trade_size": round(random.uniform(0.05, 0.15), 4),
        }),

        # 统计指标
        "total_trades": kwargs.get("total_trades", random.randint(100, 10000)),
        "win_rate": kwargs.get("win_rate", round(random.uniform(0.4, 0.7), 4)),
        "sharpe_ratio": kwargs.get("sharpe_ratio", round(random.uniform(0.5, 3.0), 2)),
        "max_drawdown": kwargs.get("max_drawdown", round(random.uniform(-0.3, -0.05), 4)),
        "annualized_return": kwargs.get("annualized_return", round(random.uniform(-0.1, 0.5), 4)),

        # 时间信息
        "created_at": kwargs.get("created_at", (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()),
        "updated_at": kwargs.get("updated_at", datetime.now().isoformat()),
        "last_run_at": kwargs.get("last_run_at", (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()),
    }


def create_mock_strategies(count: int = 5, **kwargs) -> List[Dict[str, Any]]:
    """
    创建策略列表测试数据

    Args:
        count: 策略数量
        **kwargs: 传递给 create_mock_strategy 的参数

    Returns:
        策略列表
    """
    return [create_mock_strategy(**kwargs) for _ in range(count)]


def create_mock_backtest_result(
    strategy_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建回测结果测试数据

    Args:
        strategy_id: 策略ID
        **kwargs: 其他自定义字段

    Returns:
        回测结果数据字典
    """
    if strategy_id is None:
        strategy_id = random_strategy_id()

    start_date = kwargs.get("start_date", (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
    end_date = kwargs.get("end_date", datetime.now().strftime("%Y-%m-%d"))

    total_return = round(random.uniform(-0.3, 0.8), 4)
    benchmark_return = round(random.uniform(-0.2, 0.5), 4)

    return {
        "id": kwargs.get("id", f"bt_{uuid.uuid4().hex[:12]}"),
        "strategy_id": strategy_id,
        "name": kwargs.get("name", f"回测_{random_string(4)}"),
        "start_date": start_date,
        "end_date": end_date,
        "initial_capital": kwargs.get("initial_capital", 1000000),

        # 收益指标
        "total_return": total_return,
        "annualized_return": kwargs.get("annualized_return", round(total_return * random.uniform(0.8, 1.2), 4)),
        "benchmark_return": benchmark_return,
        "excess_return": round(total_return - benchmark_return, 4),

        # 风险指标
        "max_drawdown": kwargs.get("max_drawdown", round(random.uniform(-0.4, -0.05), 4)),
        "volatility": kwargs.get("volatility", round(random.uniform(0.1, 0.4), 4)),
        "downside_volatility": kwargs.get("downside_volatility", round(random.uniform(0.05, 0.25), 4)),

        # 风险调整收益
        "sharpe_ratio": kwargs.get("sharpe_ratio", round(random.uniform(0.5, 3.0), 2)),
        "sortino_ratio": kwargs.get("sortino_ratio", round(random.uniform(0.3, 4.0), 2)),
        "calmar_ratio": kwargs.get("calmar_ratio", round(random.uniform(0.2, 3.0), 2)),
        "information_ratio": kwargs.get("information_ratio", round(random.uniform(-0.5, 2.0), 2)),

        # 交易统计
        "total_trades": kwargs.get("total_trades", random.randint(100, 1000)),
        "winning_trades": kwargs.get("winning_trades", random.randint(40, 600)),
        "losing_trades": kwargs.get("losing_trades", random.randint(30, 400)),
        "win_rate": kwargs.get("win_rate", round(random.uniform(0.4, 0.7), 4)),
        "profit_loss_ratio": kwargs.get("profit_loss_ratio", round(random.uniform(1.0, 3.0), 2)),

        # 成本
        "total_commission": kwargs.get("total_commission", round(random.uniform(1000, 50000), 2)),
        "total_slippage": kwargs.get("total_slippage", round(random.uniform(100, 10000), 2)),

        # Alpha/Beta
        "alpha": kwargs.get("alpha", round(random.uniform(-0.1, 0.2), 4)),
        "beta": kwargs.get("beta", round(random.uniform(0.5, 1.5), 4)),

        # 时间信息
        "created_at": kwargs.get("created_at", datetime.now().isoformat()),
        "duration_seconds": kwargs.get("duration_seconds", random.randint(10, 600)),
    }


def create_mock_signal(
    strategy_id: Optional[str] = None,
    symbol: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建交易信号测试数据

    Args:
        strategy_id: 策略ID
        symbol: 股票代码
        **kwargs: 其他自定义字段

    Returns:
        交易信号数据字典
    """
    if strategy_id is None:
        strategy_id = random_strategy_id()

    if symbol is None:
        symbol = f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}"

    signal_types = ["BUY", "SELL", "HOLD"]
    signal_strengths = ["STRONG", "MODERATE", "WEAK"]

    return {
        "id": kwargs.get("id", f"sig_{uuid.uuid4().hex[:12]}"),
        "strategy_id": strategy_id,
        "symbol": symbol,
        "signal_type": kwargs.get("signal_type", random.choice(signal_types)),
        "signal_strength": kwargs.get("signal_strength", random.choice(signal_strengths)),
        "confidence": kwargs.get("confidence", round(random.uniform(0.5, 1.0), 4)),
        "price": kwargs.get("price", round(random.uniform(10, 200), 2)),
        "target_price": kwargs.get("target_price", round(random.uniform(12, 250), 2)),
        "stop_loss": kwargs.get("stop_loss", round(random.uniform(8, 180), 2)),

        # 信号指标
        "indicators": kwargs.get("indicators", {
            "ma_cross": random.choice(["golden", "dead", "none"]),
            "rsi": round(random.uniform(20, 80), 2),
            "macd": random.choice(["bullish", "bearish", "neutral"]),
            "volume_ratio": round(random.uniform(0.5, 2.0), 2),
        }),

        # 推荐操作
        "recommended_action": kwargs.get("recommended_action", random.choice([
            "OPEN_LONG", "CLOSE_LONG", "OPEN_SHORT", "CLOSE_SHORT", "HOLD"
        ])),
        "recommended_quantity": kwargs.get("recommended_quantity", random.randint(100, 5000)),

        # 时间信息
        "generated_at": kwargs.get("generated_at", datetime.now().isoformat()),
        "expires_at": kwargs.get("expires_at", (datetime.now() + timedelta(hours=random.randint(1, 24))).isoformat()),
        "status": kwargs.get("status", random.choice(["PENDING", "EXECUTED", "EXPIRED", "CANCELLED"])),

        # 备注
        "reason": kwargs.get("reason", f"信号生成原因: {random_string(10)}"),
        "notes": kwargs.get("notes"),
    }


def create_mock_signals(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    创建交易信号列表测试数据

    Args:
        count: 信号数量
        **kwargs: 传递给 create_mock_signal 的参数

    Returns:
        交易信号列表
    """
    return [create_mock_signal(**kwargs) for _ in range(count)]


def create_mock_backtest_trades(
    backtest_id: Optional[str] = None,
    count: int = 20,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    创建回测交易记录测试数据

    Args:
        backtest_id: 回测ID
        count: 交易数量
        **kwargs: 其他自定义字段

    Returns:
        回测交易记录列表
    """
    if backtest_id is None:
        backtest_id = f"bt_{uuid.uuid4().hex[:12]}"

    trades = []
    base_date = datetime.now() - timedelta(days=365)

    for i in range(count):
        trade_date = base_date + timedelta(days=i * (365 // count))
        symbol = f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}"
        side = random.choice(["BUY", "SELL"])
        quantity = random.randint(100, 1000)
        price = round(random.uniform(10, 200), 2)

        trades.append({
            "id": f"trd_{uuid.uuid4().hex[:12]}",
            "backtest_id": backtest_id,
            "date": trade_date.strftime("%Y-%m-%d"),
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "amount": round(quantity * price, 2),
            "commission": round(quantity * price * 0.0003, 2),
            "pnl": round(random.uniform(-5000, 10000), 2),
            "cumulative_pnl": round(sum(t.get("pnl", 0) for t in trades) + random.uniform(-5000, 10000), 2),
            **kwargs
        })

    return trades


def create_mock_factor_exposure(
    strategy_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建因子暴露测试数据

    Args:
        strategy_id: 策略ID
        **kwargs: 其他自定义字段

    Returns:
        因子暴露数据字典
    """
    if strategy_id is None:
        strategy_id = random_strategy_id()

    factors = [
        "market_beta", "size_factor", "value_factor", "momentum_factor",
        "quality_factor", "volatility_factor", "liquidity_factor"
    ]

    return {
        "id": kwargs.get("id", f"fac_{uuid.uuid4().hex[:12]}"),
        "strategy_id": strategy_id,
        "date": kwargs.get("date", datetime.now().strftime("%Y-%m-%d")),
        "exposures": kwargs.get("exposures", {
            factor: round(random.uniform(-1.5, 1.5), 4)
            for factor in factors
        }),
        "factor_returns": kwargs.get("factor_returns", {
            factor: round(random.uniform(-0.05, 0.05), 4)
            for factor in factors
        }),
        "specific_return": kwargs.get("specific_return", round(random.uniform(-0.02, 0.02), 4)),
        "total_return": kwargs.get("total_return", round(random.uniform(-0.05, 0.05), 4)),
    }
