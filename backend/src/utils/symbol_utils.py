"""
==============================================
股票代码格式化工具
==============================================
统一管理股票代码格式化逻辑
"""

import re
from typing import Tuple, Optional


def format_symbol(symbol: str, market: str = "auto") -> str:
    """
    格式化股票代码为标准格式

    Args:
        symbol: 原始股票代码
        market: 目标市场（auto/SHSE/SZSE）

    Returns:
        str: 格式化后的股票代码（如: 000001.SZ, 600000.SH）
    """
    # 移除所有非数字字符
    symbol_clean = re.sub(r'\D', '', symbol)

    # 补齐6位
    if len(symbol_clean) < 6:
        symbol_clean = symbol_clean.zfill(6)

    # 自动检测市场
    if market == "auto":
        market = detect_market(symbol_clean)

    # 添加后缀
    if market == "SHSE":
        return f"{symbol_clean}.SH"
    elif market == "SZSE":
        return f"{symbol_clean}.SZ"
    else:
        return symbol_clean


def clean_symbol(symbol: str) -> str:
    """
    清理股票代码（去除后缀，统一为6位数字）

    Args:
        symbol: 原始股票代码

    Returns:
        str: 清理后的股票代码（纯数字）
    """
    # 移除所有非数字字符
    symbol_clean = re.sub(r'\D', '', symbol)

    # 补齐6位
    if len(symbol_clean) < 6:
        symbol_clean = symbol_clean.zfill(6)

    return symbol_clean


def detect_market(symbol: str) -> str:
    """
    检测股票所属市场

    Args:
        symbol: 股票代码

    Returns:
        str: 市场代码（SHSE/SZSE/UNKNOWN）
    """
    # 清理代码
    symbol_clean = clean_symbol(symbol)

    # 上海证券交易所（6开头）
    if symbol_clean.startswith('6'):
        return "SHSE"
    # 深圳证券交易所（0或3开头）
    elif symbol_clean.startswith('0') or symbol_clean.startswith('3'):
        return "SZSE"
    else:
        return "UNKNOWN"


def parse_symbol(symbol: str) -> Tuple[str, str]:
    """
    解析股票代码，返回纯代码和市场

    Args:
        symbol: 股票代码（可以是带后缀的格式）

    Returns:
        Tuple[str, str]: (纯代码, 市场代码)
    """
    symbol_clean = clean_symbol(symbol)
    market = detect_market(symbol_clean)
    return symbol_clean, market


def is_valid_symbol(symbol: str) -> bool:
    """
    验证股票代码是否有效

    Args:
        symbol: 股票代码

    Returns:
        bool: 是否有效
    """
    symbol_clean = clean_symbol(symbol)

    # 检查是否为6位数字
    if len(symbol_clean) != 6:
        return False

    # 检查是否以有效数字开头
    if symbol_clean[0] not in ('0', '3', '6'):
        return False

    return True


def get_market_name(market: str, lang: str = "zh") -> str:
    """
    获取市场中文名称

    Args:
        market: 市场代码
        lang: 语言（zh/en）

    Returns:
        str: 市场名称
    """
    market_names = {
        "SHSE": {"zh": "上海证券交易所", "en": "Shanghai Stock Exchange"},
        "SZSE": {"zh": "深圳证券交易所", "en": "Shenzhen Stock Exchange"},
        "UNKNOWN": {"zh": "未知市场", "en": "Unknown Market"}
    }

    return market_names.get(market, market_names["UNKNOWN"]).get(lang, market)


def normalize_symbols(symbols: list[str]) -> list[str]:
    """
    批量标准化股票代码

    Args:
        symbols: 股票代码列表

    Returns:
        list[str]: 标准化后的股票代码列表
    """
    return [format_symbol(s) for s in symbols if is_valid_symbol(s)]


def symbol_to_wind(symbol: str) -> str:
    """
    转换为 Wind 格式

    Args:
        symbol: 股票代码

    Returns:
        str: Wind 格式的股票代码
    """
    symbol_clean, market = parse_symbol(symbol)

    if market == "SHSE":
        return f"{symbol_clean}.SH"
    elif market == "SZSE":
        return f"{symbol_clean}.SZ"
    else:
        return symbol_clean


def symbol_to_tushare(symbol: str) -> str:
    """
    转换为 Tushare 格式

    Args:
        symbol: 股票代码

    Returns:
        str: Tushare 格式的股票代码
    """
    return symbol_to_wind(symbol)


def symbol_to_akshare(symbol: str) -> str:
    """
    转换为 AkShare 格式（纯数字）

    Args:
        symbol: 股票代码

    Returns:
        str: AkShare 格式的股票代码
    """
    return clean_symbol(symbol)
