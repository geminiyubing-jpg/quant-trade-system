"""
模拟券商

用于模拟交易和测试。
"""

from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime
import asyncio

from .base import BaseBroker, OrderResult, Position, AccountInfo


class SimulatedBroker(BaseBroker):
    """
    模拟券商
    
    实现完整的交易逻辑，但使用虚拟资金和数据。
    """
    
    broker_type = "SIMULATED"
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模拟券商
        
        Args:
            config: 配置信息
                - initial_cash: 初始资金（默认 1,000,000）
        """
        super().__init__(config)
        
        # 初始化账户
        self.cash = Decimal(str(config.get('initial_cash', 1000000)))
        self.positions: Dict[str, Dict] = {}  # symbol -> {quantity, avg_price}
        self.orders: Dict[str, Dict] = {}  # order_id -> order info
        self.order_counter = 0
        
        # 模拟行情数据（简化版）
        self.market_data: Dict[str, Decimal] = {
            "000001.SZ": Decimal("10.50"),
            "000002.SZ": Decimal("12.00"),
            "600000.SH": Decimal("8.80"),
        }
    
    async def connect(self) -> bool:
        """连接模拟券商"""
        await asyncio.sleep(0.1)  # 模拟网络延迟
        self.connected = True
        return True
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.connected = False
        return True
    
    async def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        # 计算持仓市值
        market_value = Decimal("0")
        for symbol, pos in self.positions.items():
            current_price = self.market_data.get(symbol, Decimal("10.00"))
            market_value += current_price * pos['quantity']
        
        total_assets = self.cash + market_value
        
        return AccountInfo(
            total_assets=total_assets,
            cash=self.cash,
            available_cash=self.cash,  # 简化，不考虑冻结资金
            market_value=market_value,
            profit_loss=Decimal("0"),  # 模拟账户无盈亏
            profit_loss_ratio=Decimal("0")
        )
    
    async def get_positions(self) -> List[Position]:
        """获取持仓列表"""
        positions = []
        
        for symbol, pos in self.positions.items():
            current_price = self.market_data.get(symbol, Decimal("10.00"))
            quantity = pos['quantity']
            avg_price = Decimal(str(pos['avg_price']))
            
            market_value = current_price * quantity
            profit_loss = (current_price - avg_price) * quantity
            profit_loss_ratio = (current_price - avg_price) / avg_price if avg_price > 0 else Decimal("0")
            
            positions.append(Position(
                symbol=symbol,
                quantity=quantity,
                available_quantity=quantity,  # 简化
                avg_price=avg_price,
                current_price=current_price,
                market_value=market_value,
                profit_loss=profit_loss,
                profit_loss_ratio=profit_loss_ratio
            ))
        
        return positions
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: Optional[Decimal] = None,
        order_type: str = "LIMIT"
    ) -> OrderResult:
        """下单"""
        if not self.connected:
            return OrderResult(
                success=False,
                message="未连接到券商"
            )
        
        # 生成订单ID
        self.order_counter += 1
        order_id = f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.order_counter}"
        
        # 获取当前价格
        current_price = self.market_data.get(symbol, Decimal("10.00"))
        execution_price = price if price and order_type == "LIMIT" else current_price
        
        # 执行订单逻辑
        if side == "BUY":
            # 买入逻辑
            required_amount = execution_price * quantity
            if required_amount > self.cash:
                return OrderResult(
                    success=False,
                    message=f"资金不足。需要 {required_amount}，可用 {self.cash}"
                )
            
            # 扣除资金
            self.cash -= required_amount
            
            # 更新持仓
            if symbol not in self.positions:
                self.positions[symbol] = {"quantity": 0, "avg_price": Decimal("0")}
            
            pos = self.positions[symbol]
            total_cost = pos['avg_price'] * pos['quantity'] + required_amount
            total_quantity = pos['quantity'] + quantity
            pos['quantity'] = total_quantity
            pos['avg_price'] = total_cost / total_quantity if total_quantity > 0 else Decimal("0")
            
            return OrderResult(
                success=True,
                order_id=order_id,
                message="买入成功",
                filled_quantity=quantity,
                filled_price=execution_price,
                status="FILLED"
            )
        
        elif side == "SELL":
            # 卖出逻辑
            if symbol not in self.positions or self.positions[symbol]['quantity'] < quantity:
                return OrderResult(
                    success=False,
                    message=f"持仓不足。需要 {quantity}，可用 {self.positions.get(symbol, {}).get('quantity', 0)}"
                )
            
            # 更新持仓
            pos = self.positions[symbol]
            pos['quantity'] -= quantity
            
            # 如果持仓为0，删除记录
            if pos['quantity'] == 0:
                del self.positions[symbol]
            
            # 增加资金
            self.cash += execution_price * quantity
            
            return OrderResult(
                success=True,
                order_id=order_id,
                message="卖出成功",
                filled_quantity=quantity,
                filled_price=execution_price,
                status="FILLED"
            )
        
        else:
            return OrderResult(
                success=False,
                message=f"无效的订单方向: {side}"
            )
    
    async def cancel_order(self, order_id: str) -> bool:
        """撤单（模拟券商中所有订单立即成交，无法撤单）"""
        return False
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        return {
            "order_id": order_id,
            "status": "FILLED",  # 模拟券商订单立即成交
            "message": "订单已成交"
        }
    
    def update_market_price(self, symbol: str, price: Decimal):
        """
        更新市场价格（用于测试）
        
        Args:
            symbol: 股票代码
            price: 新价格
        """
        self.market_data[symbol] = price
