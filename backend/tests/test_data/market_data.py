"""
市场数据测试工厂

提供股票、板块、K线等市场数据的测试数据生成函数。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import string


def random_string(length: int = 6) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


def random_price(min_price: float = 5.0, max_price: float = 500.0) -> float:
    """生成随机价格"""
    return round(random.uniform(min_price, max_price), 2)


def random_change_pct(min_pct: float = -10.0, max_pct: float = 10.0) -> float:
    """生成随机涨跌幅"""
    return round(random.uniform(min_pct, max_pct), 2)


def create_mock_stock(
    symbol: Optional[str] = None,
    name: Optional[str] = None,
    market: str = "SHSE",
    industry: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建单个股票测试数据

    Args:
        symbol: 股票代码
        name: 股票名称
        market: 市场 (SHSE/SZSE)
        industry: 所属行业
        **kwargs: 其他自定义字段

    Returns:
        股票数据字典
    """
    if symbol is None:
        prefix = "6" if market == "SHSE" else random.choice(["0", "3"])
        symbol = f"{prefix}{random.randint(100000, 999999)}"

    if name is None:
        name = f"测试股票{random_string(4)}"

    return {
        "symbol": symbol,
        "name": name,
        "market": market,
        "industry": industry or random.choice([
            "银行", "证券", "保险", "房地产", "基建",
            "半导体", "计算机", "通信", "电子制造", "软件开发",
            "医药生物", "医疗器械", "化学制药", "中药", "生物制品",
            "白酒", "食品饮料", "家电", "汽车", "零售",
        ]),
        "sector": kwargs.get("sector"),
        "list_date": kwargs.get("list_date", "2020-01-01"),
        "total_shares": kwargs.get("total_shares", random.randint(100000000, 10000000000)),
        "float_shares": kwargs.get("float_shares", random.randint(50000000, 5000000000)),
        "market_cap": kwargs.get("market_cap", random.randint(1000000000, 100000000000)),
        "pe_ratio": kwargs.get("pe_ratio", round(random.uniform(5, 100), 2)),
        "pb_ratio": kwargs.get("pb_ratio", round(random.uniform(0.5, 20), 2)),
        **kwargs
    }


def create_mock_stock_list(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    创建股票列表测试数据

    Args:
        count: 股票数量
        **kwargs: 传递给 create_mock_stock 的参数

    Returns:
        股票列表
    """
    return [create_mock_stock(**kwargs) for _ in range(count)]


def create_mock_stock_detail(
    symbol: str = "600519.SH",
    name: str = "贵州茅台",
    **kwargs
) -> Dict[str, Any]:
    """
    创建股票详情测试数据

    Args:
        symbol: 股票代码
        name: 股票名称
        **kwargs: 其他自定义字段

    Returns:
        股票详情数据
    """
    current_price = random_price(100, 2000)
    change_pct = random_change_pct()

    return {
        "symbol": symbol,
        "name": name,
        "market": "SHSE" if symbol.startswith("6") else "SZSE",
        "industry": kwargs.get("industry", "白酒"),
        "sector": kwargs.get("sector", "食品饮料"),

        # 价格信息
        "current_price": current_price,
        "open_price": round(current_price * (1 + random.uniform(-0.02, 0.02)), 2),
        "high_price": round(current_price * (1 + random.uniform(0, 0.03)), 2),
        "low_price": round(current_price * (1 - random.uniform(0, 0.03)), 2),
        "pre_close": round(current_price / (1 + change_pct / 100), 2),

        # 涨跌信息
        "change_pct": change_pct,
        "change_amount": round(current_price * change_pct / 100, 2),
        "amplitude": round(random.uniform(2, 10), 2),

        # 成交信息
        "volume": random.randint(100000, 100000000),
        "amount": random.randint(10000000, 10000000000),
        "turnover_rate": round(random.uniform(0.1, 10), 2),

        # 估值指标
        "pe_ratio": round(random.uniform(10, 100), 2),
        "pb_ratio": round(random.uniform(1, 20), 2),
        "market_cap": random.randint(10000000000, 3000000000000),

        # 公司信息
        "list_date": kwargs.get("list_date", "2001-08-27"),
        "total_shares": kwargs.get("total_shares", 1256197800),
        "float_shares": kwargs.get("float_shares", 1256197800),

        **kwargs
    }


def create_mock_sector(
    name: Optional[str] = None,
    sector_type: str = "industry",
    **kwargs
) -> Dict[str, Any]:
    """
    创建板块测试数据

    Args:
        name: 板块名称
        sector_type: 板块类型 (industry/concept/region)
        **kwargs: 其他自定义字段

    Returns:
        板块数据字典
    """
    if name is None:
        industry_names = [
            "半导体", "计算机", "通信", "电子制造", "软件开发",
            "新能源", "光伏", "锂电池", "储能", "风电",
            "医药生物", "医疗器械", "化学制药", "中药", "生物制品",
            "银行", "证券", "保险", "房地产", "基建",
        ]
        name = random.choice(industry_names)

    change_pct = random_change_pct()
    amount = random.randint(1000000000, 50000000000)

    return {
        "name": name,
        "code": kwargs.get("code", f"BK{random.randint(1000, 9999)}"),
        "type": sector_type,
        "change_pct": change_pct,
        "amount": amount,
        "volume": kwargs.get("volume", random.randint(10000000, 1000000000)),
        "turnover_rate": round(random.uniform(1, 10), 2),
        "leading_stock": kwargs.get("leading_stock", f"领涨股{random_string(4)}"),
        "leading_stock_change": round(random.uniform(1, 10), 2),
        "stock_count": kwargs.get("stock_count", random.randint(20, 100)),
        "up_count": kwargs.get("up_count", random.randint(10, 50)),
        "down_count": kwargs.get("down_count", random.randint(5, 30)),
        **kwargs
    }


def create_mock_sector_data(count: int = 10, sector_type: str = "industry") -> List[Dict[str, Any]]:
    """
    创建板块列表测试数据

    Args:
        count: 板块数量
        sector_type: 板块类型

    Returns:
        板块列表
    """
    sectors = []
    for i in range(count):
        sector = create_mock_sector(sector_type=sector_type)
        sector["code"] = f"BK{1000 + i}"
        sectors.append(sector)

    # 按涨跌幅排序
    return sorted(sectors, key=lambda x: x["change_pct"], reverse=True)


def create_mock_kline_data(
    symbol: str = "600519.SH",
    days: int = 100,
    start_date: Optional[str] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    创建K线测试数据

    Args:
        symbol: 股票代码
        days: 天数
        start_date: 起始日期
        **kwargs: 其他自定义字段

    Returns:
        K线数据列表
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    base_price = random_price(10, 100)
    klines = []

    for i in range(days):
        current_date = start + timedelta(days=i)
        if current_date.weekday() >= 5:  # 跳过周末
            continue

        # 模拟价格波动
        change = random.uniform(-0.03, 0.03)
        open_price = base_price
        close_price = round(base_price * (1 + change), 2)
        high_price = round(max(open_price, close_price) * (1 + random.uniform(0, 0.02)), 2)
        low_price = round(min(open_price, close_price) * (1 - random.uniform(0, 0.02)), 2)

        klines.append({
            "symbol": symbol,
            "date": current_date.strftime("%Y-%m-%d"),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.randint(100000, 10000000),
            "amount": random.randint(1000000, 100000000),
            "change_pct": round((close_price - open_price) / open_price * 100, 2),
            "turnover_rate": round(random.uniform(0.1, 5), 2),
            **kwargs
        })

        base_price = close_price  # 下一天基准价格

    return klines


def create_mock_realtime_quotes(count: int = 10) -> List[Dict[str, Any]]:
    """
    创建实时行情测试数据

    Args:
        count: 股票数量

    Returns:
        实时行情列表
    """
    quotes = []

    for _ in range(count):
        symbol = f"{random.choice(['6', '0', '3'])}{random.randint(100000, 999999)}"
        current_price = random_price()
        pre_close = round(current_price / (1 + random.uniform(-0.1, 0.1)), 2)
        change_pct = round((current_price - pre_close) / pre_close * 100, 2)

        quotes.append({
            "symbol": symbol,
            "name": f"股票{random_string(4)}",
            "current_price": current_price,
            "pre_close": pre_close,
            "open": round(current_price * (1 + random.uniform(-0.01, 0.01)), 2),
            "high": round(current_price * (1 + random.uniform(0, 0.02)), 2),
            "low": round(current_price * (1 - random.uniform(0, 0.02)), 2),
            "volume": random.randint(100000, 10000000),
            "amount": random.randint(1000000, 100000000),
            "change_pct": change_pct,
            "change_amount": round(current_price - pre_close, 2),
            "bid_price": round(current_price * 0.998, 2),
            "ask_price": round(current_price * 1.002, 2),
            "bid_volume": random.randint(100, 10000),
            "ask_volume": random.randint(100, 10000),
            "timestamp": datetime.now().isoformat(),
        })

    return quotes


def create_mock_market_overview() -> Dict[str, Any]:
    """
    创建市场概览测试数据

    Returns:
        市场概览数据
    """
    return {
        "index_quotes": [
            {
                "symbol": "000001.SH",
                "name": "上证指数",
                "current": round(random.uniform(3000, 3500), 2),
                "change_pct": random_change_pct(-3, 3),
            },
            {
                "symbol": "399001.SZ",
                "name": "深证成指",
                "current": round(random.uniform(10000, 12000), 2),
                "change_pct": random_change_pct(-3, 3),
            },
            {
                "symbol": "399006.SZ",
                "name": "创业板指",
                "current": round(random.uniform(2000, 2500), 2),
                "change_pct": random_change_pct(-3, 3),
            },
        ],
        "market_sentiment": {
            "up_count": random.randint(1000, 3000),
            "down_count": random.randint(1000, 3000),
            "flat_count": random.randint(100, 500),
            "limit_up": random.randint(10, 100),
            "limit_down": random.randint(5, 50),
        },
        "hot_sectors": create_mock_sector_data(5, "industry"),
        "hot_stocks": create_mock_realtime_quotes(5),
        "timestamp": datetime.now().isoformat(),
    }
