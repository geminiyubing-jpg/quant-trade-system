"""
券商工厂模块

提供统一的券商实例创建接口。
"""

from typing import Dict, Any, Optional
import logging

from .base import BaseBroker
from .simulated import SimulatedBroker
from .xtquant import XTQuantBroker
from .eastmoney import EastMoneyBroker

logger = logging.getLogger(__name__)


class BrokerFactory:
    """
    券商工厂类

    根据配置创建对应的券商实例。

    使用方式：
        # 创建模拟券商
        broker = BrokerFactory.create({"type": "simulated", "initial_cash": 1000000})

        # 创建 QMT 券商
        broker = BrokerFactory.create({
            "type": "xtquant",
            "qmt_path": "/path/to/qmt",
            "account_id": "12345678"
        })

        # 创建东方财富券商
        broker = BrokerFactory.create({
            "type": "eastmoney",
            "api_key": "your-api-key",
            "api_secret": "your-api-secret",
            "account_id": "12345678"
        })
    """

    # 支持的券商类型
    BROKER_TYPES = {
        "simulated": SimulatedBroker,
        "simulation": SimulatedBroker,
        "paper": SimulatedBroker,
        "xtquant": XTQuantBroker,
        "qmt": XTQuantBroker,
        "eastmoney": EastMoneyBroker,
        "em": EastMoneyBroker,
    }

    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseBroker:
        """
        创建券商实例

        Args:
            config: 配置字典，必须包含 "type" 字段
                - type: 券商类型（simulated/xtquant/eastmoney）
                - 其他配置参数请参考各券商类的文档

        Returns:
            券商实例

        Raises:
            ValueError: 不支持的券商类型
        """
        broker_type = config.get("type", "simulated").lower()

        if broker_type not in cls.BROKER_TYPES:
            raise ValueError(
                f"不支持的券商类型: {broker_type}。"
                f"支持的类型: {list(cls.BROKER_TYPES.keys())}"
            )

        broker_class = cls.BROKER_TYPES[broker_type]
        broker = broker_class(config)

        logger.info(f"创建券商实例: {broker_class.__name__} (type={broker_type})")
        return broker

    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的券商类型列表"""
        return list(cls.BROKER_TYPES.keys())

    @classmethod
    def get_broker_info(cls, broker_type: str) -> Dict[str, Any]:
        """
        获取券商信息

        Args:
            broker_type: 券商类型

        Returns:
            券商信息字典
        """
        broker_type = broker_type.lower()

        info_map = {
            "simulated": {
                "name": "模拟券商",
                "description": "用于模拟交易和测试，不需要真实账户",
                "features": ["模拟交易", "虚拟资金", "即时成交"],
                "config_fields": ["initial_cash"]
            },
            "xtquant": {
                "name": "迅投 QMT",
                "description": "专业量化交易终端，支持 A 股实盘交易",
                "features": ["实盘交易", "实时行情", "程序化交易", "支持 A 股/可转债/ETF"],
                "config_fields": ["qmt_path", "account_id", "account_type"]
            },
            "eastmoney": {
                "name": "东方财富证券",
                "description": "东方财富证券 HTTP API 接口",
                "features": ["实盘交易", "HTTP API", "沙箱测试"],
                "config_fields": ["api_key", "api_secret", "account_id", "sandbox"]
            }
        }

        return info_map.get(broker_type, {})


def create_broker(config: Dict[str, Any]) -> BaseBroker:
    """
    便捷函数：创建券商实例

    Args:
        config: 配置字典

    Returns:
        券商实例
    """
    return BrokerFactory.create(config)
