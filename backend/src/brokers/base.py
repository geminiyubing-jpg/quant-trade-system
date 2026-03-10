"""
券商基础接口

定义所有券商必须实现的统一接口。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime


class OrderResult:
    """订单执行结果"""
    def __init__(
        self,
        success: bool,
        order_id: Optional[str] = None,
        message: str = "",
        filled_quantity: int = 0,
        filled_price: Optional[Decimal] = None,
        status: str = "PENDING"
    ):
        self.success = success
        self.order_id = order_id
        self.message = message
        self.filled_quantity = filled_quantity
        self.filled_price = filled_price
        self.status = status


class Position:
    """持仓信息"""
    def __init__(
        self,
        symbol: str,
        quantity: int,
        available_quantity: int,
        avg_price: Decimal,
        current_price: Decimal,
        market_value: Decimal,
        profit_loss: Decimal,
        profit_loss_ratio: Decimal
    ):
        self.symbol = symbol
        self.quantity = quantity
        self.available_quantity = available_quantity
        self.avg_price = avg_price
        self.current_price = current_price
        self.market_value = market_value
        self.profit_loss = profit_loss
        self.profit_loss_ratio = profit_loss_ratio


class AccountInfo:
    """账户信息"""
    def __init__(
        self,
        total_assets: Decimal,
        cash: Decimal,
        available_cash: Decimal,
        market_value: Decimal,
        profit_loss: Decimal,
        profit_loss_ratio: Decimal
    ):
        self.total_assets = total_assets
        self.cash = cash
        self.available_cash = available_cash
        self.market_value = market_value
        self.profit_loss = profit_loss
        self.profit_loss_ratio = profit_loss_ratio


class BaseBroker(ABC):
    """
    券商基础接口
    
    所有券商必须实现此接口，确保系统可以无缝切换不同券商。
    """
    
    broker_type: str = "BASE"
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化券商连接
        
        Args:
            config: 券商配置信息
        """
        self.config = config
        self.connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        连接券商
        
        Returns:
            连接是否成功
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        断开券商连接
        
        Returns:
            断开是否成功
        """
        pass
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """
        获取账户信息
        
        Returns:
            账户信息
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """
        获取持仓列表
        
        Returns:
            持仓列表
        """
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: Optional[Decimal] = None,
        order_type: str = "LIMIT"
    ) -> OrderResult:
        """
        下单
        
        Args:
            symbol: 股票代码
            side: 买卖方向（BUY/SELL）
            quantity: 数量
            price: 价格（限价单需要）
            order_type: 订单类型（MARKET/LIMIT）
        
        Returns:
            订单执行结果
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        撤单
        
        Args:
            order_id: 订单ID
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
        
        Returns:
            订单状态信息
        """
        pass
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected
