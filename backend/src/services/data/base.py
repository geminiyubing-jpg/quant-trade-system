"""
数据服务基础模块

定义数据源的基础接口和抽象类。
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class StockPriceData:
    """股票价格数据"""
    symbol: str  # 股票代码
    timestamp: datetime  # 时间戳
    open: Decimal  # 开盘价
    high: Decimal  # 最高价
    low: Decimal  # 最低价
    close: Decimal  # 收盘价
    volume: int  # 成交量
    amount: Optional[Decimal]  # 成交额

    def __repr__(self):
        return f"<StockPriceData(symbol={self.symbol}, timestamp={self.timestamp}, close={self.close})>"


@dataclass
class StockInfo:
    """股票基本信息"""
    symbol: str  # 股票代码
    name: str  # 股票名称
    sector: Optional[str] = None  # 行业
    industry: Optional[str] = None  # 子行业
    market: Optional[str] = None  # 市场（SZSE, SHSE, HKEX, US）
    list_date: Optional[date] = None  # 上市日期

    def __repr__(self):
        return f"<StockInfo(symbol={self.symbol}, name={self.name}, market={self.market})>"


class DataSourceBase(ABC):
    """
    数据源基础类

    所有数据源都需要继承此类并实现抽象方法。
    """

    def __init__(self):
        """初始化数据源"""
        self.name = self.__class__.__name__
        self.is_available = False

    @abstractmethod
    def check_connection(self) -> bool:
        """
        检查数据源连接是否正常

        Returns:
            bool: 连接是否正常
        """
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            股票基本信息或 None
        """
        pass

    @abstractmethod
    def get_stock_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[StockPriceData]:
        """
        获取股票价格数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔（1d, 1wk, 1mo 等）

        Returns:
            股票价格数据列表
        """
        pass

    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[StockPriceData]:
        """
        获取最新价格数据

        Args:
            symbol: 股票代码

        Returns:
            最新价格数据或 None
        """
        pass

    def validate_symbol(self, symbol: str) -> bool:
        """
        验证股票代码格式

        Args:
            symbol: 股票代码

        Returns:
            bool: 是否有效
        """
        if not symbol or len(symbol) > 20:
            return False
        return True


class DataValidationError(Exception):
    """数据验证错误"""
    pass


class DataSourceConnectionError(Exception):
    """数据源连接错误"""
    pass
