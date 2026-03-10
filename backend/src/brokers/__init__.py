"""
券商集成模块

支持多个券商的统一接口。
"""

from .base import BaseBroker
from .simulated import SimulatedBroker

__all__ = ['BaseBroker', 'SimulatedBroker']
