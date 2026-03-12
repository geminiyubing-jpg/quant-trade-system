"""
OpenBB 工具函数

提供市场检测、符号转换等工具函数。
"""

import re
from typing import Tuple


def detect_market(symbol: str) -> str:
    """
    检测股票所属市场

    Args:
        symbol: 股票代码

    Returns:
        市场标识: 'cn' (A股), 'us' (美股), 'hk' (港股), 'intl' (其他国际市场)
    """
    # 指数符号: ^DJI, ^GSPC, ^IXIC 等
    if symbol.startswith('^'):
        return 'us'

    # A股格式: 000001.SZ, 600000.SH, 300001.BJ
    if symbol.endswith(('.SZ', '.SH', '.BJ')):
        return 'cn'

    # 港股格式: 00700.HK, 01810.HK
    if symbol.endswith('.HK'):
        return 'hk'

    # 美股格式: AAPL, MSFT, GOOGL (纯字母)
    if symbol.isalpha():
        return 'us'

    # 其他国际市场格式: VOD.L, SAP.DE 等
    if '.' in symbol:
        return 'intl'

    return 'unknown'


def convert_symbol_format(symbol: str, target_format: str = 'openbb') -> str:
    """
    转换股票代码格式

    Args:
        symbol: 原始股票代码
        target_format: 目标格式 ('openbb', 'yfinance', 'akshare')

    Returns:
        转换后的股票代码
    """
    market = detect_market(symbol)

    if market == 'cn':
        # A股代码转换
        if target_format == 'openbb' or target_format == 'yfinance':
            # 000001.SZ -> 000001.SZ (yfinance/OpenBB 使用相同格式)
            return symbol
        elif target_format == 'akshare':
            # 000001.SZ -> 000001
            return symbol.split('.')[0]

    elif market == 'us':
        # 美股代码保持不变
        return symbol

    elif market == 'hk':
        # 港股代码
        if target_format == 'openbb':
            # 00700.HK -> 0700.HK (OpenBB 格式)
            code = symbol.split('.')[0]
            return f"{int(code)}.HK"
        return symbol

    return symbol


def get_openbb_provider(market: str, data_type: str) -> str:
    """
    根据市场和数据类型推荐 OpenBB Provider

    Args:
        market: 市场标识
        data_type: 数据类型

    Returns:
        推荐的 Provider 名称
    """
    provider_map = {
        'us': {
            'price': 'yfinance',
            'fundamental': 'fmp',
            'news': 'benzinga',
        },
        'cn': {
            'price': 'yfinance',
            'fundamental': 'yfinance',
        },
        'hk': {
            'price': 'yfinance',
        },
        'intl': {
            'price': 'yfinance',
        }
    }

    return provider_map.get(market, {}).get(data_type, 'yfinance')


def validate_symbol(symbol: str) -> Tuple[bool, str]:
    """
    验证股票代码格式

    Args:
        symbol: 股票代码

    Returns:
        (是否有效, 错误信息)
    """
    if not symbol:
        return False, "股票代码不能为空"

    if len(symbol) > 20:
        return False, "股票代码过长"

    # 基本格式检查
    pattern = r'^[A-Za-z0-9\.]+$'
    if not re.match(pattern, symbol):
        return False, "股票代码包含非法字符"

    return True, ""
