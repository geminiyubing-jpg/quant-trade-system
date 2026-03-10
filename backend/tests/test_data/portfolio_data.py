"""
投资组合测试数据工厂

提供投资组合、持仓、风险指标、绩效指标等测试数据生成函数。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import random
import string


def random_string(length: int = 6) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


def random_amount(min_val: float = 10000, max_val: float = 1000000) -> Decimal:
    """生成随机金额"""
    return Decimal(str(round(random.uniform(min_val, max_val), 2)))


def create_mock_portfolio(
    portfolio_id: Optional[str] = None,
    name: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建投资组合测试数据

    Args:
        portfolio_id: 组合ID
        name: 组合名称
        **kwargs: 其他自定义字段

    Returns:
        投资组合数据字典
    """
    if portfolio_id is None:
        portfolio_id = f"pf_{random_string(8).lower()}"

    if name is None:
        name = f"测试组合{random_string(4)}"

    initial_capital = kwargs.get("initial_capital", random_amount(100000, 10000000))
    total_value = kwargs.get("total_value", initial_capital * Decimal(str(random.uniform(0.8, 1.5))))

    return {
        "id": portfolio_id,
        "user_id": kwargs.get("user_id", f"user_{random_string(8).lower()}"),
        "name": name,
        "description": kwargs.get("description", f"{name}的描述"),
        "benchmark_symbol": kwargs.get("benchmark_symbol", random.choice([
            "000300.SH",  # 沪深300
            "000905.SH",  # 中证500
            "399006.SZ",  # 创业板指
        ])),
        "base_currency": kwargs.get("base_currency", "CNY"),
        "status": kwargs.get("status", random.choice(["ACTIVE", "PAUSED", "CLOSED"])),
        "initial_capital": float(initial_capital),
        "total_value": float(total_value),
        "cash_balance": float(kwargs.get("cash_balance", total_value * Decimal("0.2"))),
        "inception_date": kwargs.get("inception_date", (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")),
        "created_at": kwargs.get("created_at", datetime.now().isoformat()),
        "updated_at": kwargs.get("updated_at", datetime.now().isoformat()),
    }


def create_mock_position(
    symbol: Optional[str] = None,
    portfolio_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建持仓测试数据

    Args:
        symbol: 股票代码
        portfolio_id: 组合ID
        **kwargs: 其他自定义字段

    Returns:
        持仓数据字典
    """
    if symbol is None:
        symbol = f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}"

    if portfolio_id is None:
        portfolio_id = f"pf_{random_string(8).lower()}"

    avg_cost = kwargs.get("avg_cost", Decimal(str(round(random.uniform(10, 200), 2))))
    current_price = kwargs.get("current_price", avg_cost * Decimal(str(random.uniform(0.8, 1.2))))
    quantity = kwargs.get("quantity", random.randint(100, 10000))
    market_value = current_price * quantity

    return {
        "id": kwargs.get("id", f"pos_{random_string(8).lower()}"),
        "portfolio_id": portfolio_id,
        "symbol": symbol,
        "name": kwargs.get("name", f"股票{random_string(4)}"),
        "quantity": quantity,
        "avg_cost": float(avg_cost),
        "current_price": float(current_price),
        "market_value": float(market_value),
        "weight": float(kwargs.get("weight", round(random.uniform(0.01, 0.2), 4))),
        "target_weight": float(kwargs.get("target_weight", round(random.uniform(0.01, 0.2), 4))),
        "unrealized_pnl": float(kwargs.get("unrealized_pnl", (current_price - avg_cost) * quantity)),
        "realized_pnl": float(kwargs.get("realized_pnl", random.uniform(-10000, 50000))),
        "sector": kwargs.get("sector", random.choice([
            "银行", "证券", "保险", "半导体", "计算机", "医药生物", "白酒", "新能源"
        ])),
        "industry": kwargs.get("industry"),
        "status": kwargs.get("status", "OPEN"),
    }


def create_mock_positions(count: int = 5, portfolio_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    创建持仓列表测试数据

    Args:
        count: 持仓数量
        portfolio_id: 组合ID

    Returns:
        持仓列表
    """
    positions = []
    total_weight = 0

    for i in range(count):
        weight = round(random.uniform(0.05, 0.3), 4) if i < count - 1 else round(1 - total_weight, 4)
        total_weight += weight

        position = create_mock_position(portfolio_id=portfolio_id)
        position["weight"] = weight
        positions.append(position)

    return positions


def create_mock_risk_metrics(
    portfolio_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建风险指标测试数据

    Args:
        portfolio_id: 组合ID
        **kwargs: 其他自定义字段

    Returns:
        风险指标数据字典
    """
    if portfolio_id is None:
        portfolio_id = f"pf_{random_string(8).lower()}"

    return {
        "id": kwargs.get("id", f"risk_{random_string(8).lower()}"),
        "portfolio_id": portfolio_id,
        "calculation_date": kwargs.get("calculation_date", date.today().isoformat()),

        # VaR 指标
        "var_95": kwargs.get("var_95", round(random.uniform(1, 5), 2)),  # 95% VaR
        "var_99": kwargs.get("var_99", round(random.uniform(2, 8), 2)),  # 99% VaR
        "cvar_95": kwargs.get("cvar_95", round(random.uniform(2, 6), 2)),  # 95% CVaR

        # 波动率
        "portfolio_volatility": kwargs.get("portfolio_volatility", round(random.uniform(10, 30), 2)),

        # 集中度风险
        "herfindahl_index": kwargs.get("herfindahl_index", round(random.uniform(0.1, 0.5), 3)),
        "max_single_weight": kwargs.get("max_single_weight", round(random.uniform(0.1, 0.4), 4)),
        "top_5_weight": kwargs.get("top_5_weight", round(random.uniform(0.4, 0.8), 4)),
        "top_10_weight": kwargs.get("top_10_weight", round(random.uniform(0.6, 0.95), 4)),

        # 其他风险指标
        "diversification_ratio": kwargs.get("diversification_ratio", round(random.uniform(0.5, 1.5), 2)),
        "beta_to_benchmark": kwargs.get("beta_to_benchmark", round(random.uniform(0.5, 1.5), 2)),
        "max_drawdown": kwargs.get("max_drawdown", round(random.uniform(-30, -5), 2)),

        "created_at": kwargs.get("created_at", datetime.now().isoformat()),
    }


def create_mock_performance_metrics(
    portfolio_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建绩效指标测试数据

    Args:
        portfolio_id: 组合ID
        **kwargs: 其他自定义字段

    Returns:
        绩效指标数据字典
    """
    if portfolio_id is None:
        portfolio_id = f"pf_{random_string(8).lower()}"

    start_date = kwargs.get("start_date", (date.today() - timedelta(days=365)).isoformat())
    end_date = kwargs.get("end_date", date.today().isoformat())

    total_return = round(random.uniform(-20, 50), 2)
    benchmark_return = round(random.uniform(-15, 40), 2)
    annualized_return = round(total_return * random.uniform(0.8, 1.2), 2)

    return {
        "portfolio_id": portfolio_id,
        "calculation_date": date.today().isoformat(),
        "start_date": start_date,
        "end_date": end_date,

        # 收益指标
        "total_return": total_return,
        "annualized_return": annualized_return,
        "benchmark_return": benchmark_return,
        "excess_return": round(total_return - benchmark_return, 2),

        # 风险指标
        "annualized_volatility": kwargs.get("annualized_volatility", round(random.uniform(10, 30), 2)),
        "downside_volatility": kwargs.get("downside_volatility", round(random.uniform(5, 20), 2)),
        "max_drawdown": kwargs.get("max_drawdown", round(random.uniform(-25, -5), 2)),

        # 风险调整收益
        "sharpe_ratio": kwargs.get("sharpe_ratio", round(random.uniform(0.5, 2.5), 2)),
        "sortino_ratio": kwargs.get("sortino_ratio", round(random.uniform(0.3, 3.0), 2)),
        "calmar_ratio": kwargs.get("calmar_ratio", round(random.uniform(0.2, 2.0), 2)),
        "information_ratio": kwargs.get("information_ratio", round(random.uniform(-0.5, 1.5), 2)),
        "treynor_ratio": kwargs.get("treynor_ratio", round(random.uniform(0.1, 1.0), 2)),

        # Alpha/Beta
        "alpha": kwargs.get("alpha", round(random.uniform(-5, 10), 2)),
        "beta": kwargs.get("beta", round(random.uniform(0.5, 1.5), 2)),

        # 交易统计
        "win_rate": kwargs.get("win_rate", round(random.uniform(0.4, 0.7), 2)),
        "profit_loss_ratio": kwargs.get("profit_loss_ratio", round(random.uniform(1.0, 3.0), 2)),
        "total_trades": kwargs.get("total_trades", random.randint(50, 500)),
        "winning_trades": kwargs.get("winning_trades", random.randint(25, 300)),
        "losing_trades": kwargs.get("losing_trades", random.randint(20, 200)),
    }


def create_mock_optimization_result(
    portfolio_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建优化结果测试数据

    Args:
        portfolio_id: 组合ID
        **kwargs: 其他自定义字段

    Returns:
        优化结果数据字典
    """
    if portfolio_id is None:
        portfolio_id = f"pf_{random_string(8).lower()}"

    methods = ["MEAN_VARIANCE", "RISK_PARITY", "MIN_VARIANCE", "MAX_SHARPE", "EQUAL_WEIGHT"]

    # 生成优化权重
    num_stocks = kwargs.get("num_stocks", 5)
    weights = [round(random.uniform(0.05, 0.3), 4) for _ in range(num_stocks)]
    total = sum(weights)
    weights = [round(w / total, 4) for w in weights]

    optimal_weights = {
        f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}": w
        for w in weights
    }

    return {
        "id": kwargs.get("id", f"opt_{random_string(8).lower()}"),
        "portfolio_id": portfolio_id,
        "optimization_method": kwargs.get("optimization_method", random.choice(methods)),
        "current_weights": kwargs.get("current_weights", optimal_weights),
        "optimal_weights": optimal_weights,
        "expected_return": kwargs.get("expected_return", round(random.uniform(5, 25), 2)),
        "expected_risk": kwargs.get("expected_risk", round(random.uniform(8, 25), 2)),
        "expected_sharpe": kwargs.get("expected_sharpe", round(random.uniform(0.5, 2.0), 2)),
        "rebalance_trades": kwargs.get("rebalance_trades", [
            {
                "symbol": f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}",
                "action": random.choice(["BUY", "SELL"]),
                "quantity": random.randint(100, 1000),
                "reason": "权重调整",
            }
            for _ in range(3)
        ]),
        "estimated_transaction_cost": kwargs.get("estimated_transaction_cost", round(random.uniform(100, 5000), 2)),
        "status": kwargs.get("status", random.choice(["PENDING", "APPLIED", "REJECTED"])),
        "created_at": kwargs.get("created_at", datetime.now().isoformat()),
    }


def create_mock_benchmark(
    portfolio_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建自定义基准测试数据

    Args:
        portfolio_id: 组合ID
        **kwargs: 其他自定义字段

    Returns:
        自定义基准数据字典
    """
    if portfolio_id is None:
        portfolio_id = f"pf_{random_string(8).lower()}"

    # 生成基准成分
    num_stocks = kwargs.get("num_stocks", 5)
    weights = [round(random.uniform(0.1, 0.4), 4) for _ in range(num_stocks)]
    total = sum(weights)
    weights = [round(w / total, 4) for w in weights]

    composition = [
        {
            "symbol": f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}",
            "weight": w,
            "name": f"成分股{i+1}",
        }
        for i, w in enumerate(weights)
    ]

    return {
        "id": kwargs.get("id", f"bm_{random_string(8).lower()}"),
        "portfolio_id": portfolio_id,
        "name": kwargs.get("name", f"自定义基准{random_string(4)}"),
        "description": kwargs.get("description", "用于绩效比较的自定义基准"),
        "composition": composition,
        "rebalance_frequency": kwargs.get("rebalance_frequency", random.choice(["MONTHLY", "QUARTERLY", "YEARLY"])),
        "created_at": kwargs.get("created_at", datetime.now().isoformat()),
    }
