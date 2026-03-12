"""
券商集成模块

支持多个券商的统一接口，包括模拟交易和实盘交易。

支持的券商：
- SimulatedBroker: 模拟券商（用于测试）
- XTQuantBroker: 迅投 QMT（专业量化交易终端）
- EastMoneyBroker: 东方财富证券（HTTP API）

使用方式：
    from src.brokers import BrokerFactory, create_broker

    # 方式一：使用工厂类
    broker = BrokerFactory.create({
        "type": "simulated",
        "initial_cash": 1000000
    })

    # 方式二：使用便捷函数
    broker = create_broker({"type": "xtquant", "account_id": "12345678"})

    # 连接券商
    await broker.connect()

    # 获取账户信息
    account = await broker.get_account_info()

    # 下单
    result = await broker.place_order(
        symbol="000001.SZ",
        side="BUY",
        quantity=100,
        price=Decimal("10.50")
    )
"""

from .base import BaseBroker, OrderResult, Position, AccountInfo
from .simulated import SimulatedBroker
from .xtquant import XTQuantBroker
from .eastmoney import EastMoneyBroker
from .factory import BrokerFactory, create_broker

__all__ = [
    # 基础类
    'BaseBroker',
    'OrderResult',
    'Position',
    'AccountInfo',

    # 券商实现
    'SimulatedBroker',
    'XTQuantBroker',
    'EastMoneyBroker',

    # 工厂
    'BrokerFactory',
    'create_broker',
]
