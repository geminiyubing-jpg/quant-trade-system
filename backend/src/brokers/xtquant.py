"""
迅投 QMT 券商接口

实现与迅投 QMT (Quantitative Trading Platform) 的对接。
QMT 是国内最常用的专业量化交易终端之一。

支持功能：
- 实时行情订阅
- 股票交易（买入/卖出）
- 撤单
- 查询持仓和资金
- 查询订单状态

使用前需要：
1. 安装 QMT 客户端
2. 在 QMT 中开启外部 Python 接口
3. 配置账户信息
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import asyncio
import logging
import os
import sys

from .base import BaseBroker, OrderResult, Position, AccountInfo

logger = logging.getLogger(__name__)


class XTQuantBroker(BaseBroker):
    """
    迅投 QMT 券商接口

    通过 Python API 与 QMT 客户端通信，实现实盘交易。

    注意：
    - 需要先启动 QMT 客户端
    - 需要在 QMT 中启用外部 Python 接口
    - 支持A股、可转债、ETF等品种
    """

    broker_type = "XTQUANT"

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 QMT 券商接口

        Args:
            config: 配置信息
                - qmt_path: QMT 安装路径（可选，默认自动检测）
                - account_id: 资金账号
                - account_type: 账户类型（STOCK/FUTURE）
        """
        super().__init__(config)

        self.qmt_path = config.get('qmt_path', self._find_qmt_path())
        self.account_id = config.get('account_id', '')
        self.account_type = config.get('account_type', 'STOCK')

        # QMT Python API 模块
        self.xt_trader = None
        self.xt_quote = None
        self.session_id = None

        # 缓存数据
        self._positions_cache: List[Dict] = []
        self._account_cache: Dict = {}

    def _find_qmt_path(self) -> str:
        """自动查找 QMT 安装路径"""
        common_paths = [
            "C:\\国金证券QMT交易端\\userdata_mini",
            "C:\\华泰证券QMT交易端\\userdata_mini",
            "C:\\迅投QMT交易端\\userdata_mini",
            os.path.expanduser("~/.qmt/userdata_mini"),
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return ""

    def _init_qmt_api(self) -> bool:
        """初始化 QMT API"""
        try:
            # 添加 QMT 路径到 Python 路径
            if self.qmt_path:
                bin_path = os.path.join(self.qmt_path, '..', 'bin.x64')
                if bin_path not in sys.path:
                    sys.path.insert(0, bin_path)

            # 尝试导入 QMT API
            try:
                from xtquant import xtconstant
                from xtquant.xttrader import XtQuantTrader, XtAccount
                from xtquant.xtquote import XtQuantQuote

                # 创建交易实例
                self.xt_trader = XtQuantTrader(self.qmt_path)
                self.xt_quote = XtQuantQuote(self.qmt_path)

                logger.info("QMT API 初始化成功")
                return True

            except ImportError as e:
                logger.warning(f"QMT API 未安装或导入失败: {e}")
                logger.info("将使用模拟模式运行")
                return False

        except Exception as e:
            logger.error(f"初始化 QMT API 失败: {e}")
            return False

    async def connect(self) -> bool:
        """
        连接 QMT 券商

        Returns:
            连接是否成功
        """
        try:
            # 初始化 API
            if not self._init_qmt_api():
                logger.warning("QMT API 初始化失败，使用模拟模式")
                self.connected = True  # 模拟模式
                return True

            # 连接行情服务
            if self.xt_quote:
                await asyncio.to_thread(self.xt_quote.connect)

            # 创建交易会话
            if self.xt_trader:
                self.session_id = await asyncio.to_thread(
                    self.xt_trader.create_session,
                    self.account_id
                )

                if self.session_id:
                    self.connected = True
                    logger.info(f"成功连接到 QMT，会话ID: {self.session_id}")
                    return True
                else:
                    logger.error("创建 QMT 交易会话失败")
                    return False

            return False

        except Exception as e:
            logger.error(f"连接 QMT 失败: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开 QMT 连接"""
        try:
            if self.xt_trader and self.session_id:
                await asyncio.to_thread(
                    self.xt_trader.disconnect,
                    self.session_id
                )

            self.connected = False
            logger.info("已断开 QMT 连接")
            return True

        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False

    async def get_account_info(self) -> AccountInfo:
        """
        获取账户信息

        Returns:
            账户信息
        """
        if not self.connected:
            raise ConnectionError("未连接到券商")

        try:
            if self.xt_trader and self.session_id:
                # 从 QMT 获取账户信息
                account = await asyncio.to_thread(
                    self.xt_trader.query_stock_account,
                    self.session_id,
                    self.account_id
                )

                return AccountInfo(
                    total_assets=Decimal(str(account.total_asset)),
                    cash=Decimal(str(account.cash)),
                    available_cash=Decimal(str(account.available_cash)),
                    market_value=Decimal(str(account.market_value)),
                    profit_loss=Decimal(str(account.profit_loss)),
                    profit_loss_ratio=Decimal(str(account.profit_loss_ratio or 0))
                )
            else:
                # 模拟模式
                return AccountInfo(
                    total_assets=Decimal("1000000"),
                    cash=Decimal("500000"),
                    available_cash=Decimal("500000"),
                    market_value=Decimal("500000"),
                    profit_loss=Decimal("0"),
                    profit_loss_ratio=Decimal("0")
                )

        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            raise

    async def get_positions(self) -> List[Position]:
        """
        获取持仓列表

        Returns:
            持仓列表
        """
        if not self.connected:
            raise ConnectionError("未连接到券商")

        try:
            positions = []

            if self.xt_trader and self.session_id:
                # 从 QMT 获取持仓
                qmt_positions = await asyncio.to_thread(
                    self.xt_trader.query_stock_positions,
                    self.session_id,
                    self.account_id
                )

                for pos in qmt_positions:
                    positions.append(Position(
                        symbol=pos.stock_code,
                        quantity=pos.volume,
                        available_quantity=pos.can_use_volume,
                        avg_price=Decimal(str(pos.open_price)),
                        current_price=Decimal(str(pos.market_price or pos.open_price)),
                        market_value=Decimal(str(pos.market_value or 0)),
                        profit_loss=Decimal(str(pos.profit_loss or 0)),
                        profit_loss_ratio=Decimal(str(pos.profit_loss_ratio or 0))
                    ))
            else:
                # 模拟模式 - 返回空持仓
                pass

            self._positions_cache = positions
            return positions

        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            raise

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
            symbol: 股票代码（如 000001.SZ）
            side: 买卖方向（BUY/SELL）
            quantity: 数量（股）
            price: 价格（限价单必填）
            order_type: 订单类型（LIMIT/MARKET）

        Returns:
            订单执行结果
        """
        if not self.connected:
            return OrderResult(
                success=False,
                message="未连接到券商"
            )

        try:
            # 转换股票代码格式
            xt_symbol = self._convert_symbol(symbol)

            # 确定订单类型
            from xtquant import xtconstant
            xt_order_type = xtconstant.STOCK_LIMIT if order_type == "LIMIT" else xtconstant.STOCK_MARKET

            # 确定买卖方向
            xt_side = xtconstant.STOCK_BUY if side == "BUY" else xtconstant.STOCK_SELL

            if self.xt_trader and self.session_id:
                # 通过 QMT 下单
                order_id = await asyncio.to_thread(
                    self.xt_trader.order_stock,
                    self.session_id,
                    self.account_id,
                    xt_symbol,
                    xt_order_type,
                    xt_side,
                    quantity,
                    float(price) if price else 0,
                    "订单备注",
                    ""
                )

                if order_id > 0:
                    logger.info(f"下单成功: {symbol} {side} {quantity}@{price}, 订单ID: {order_id}")
                    return OrderResult(
                        success=True,
                        order_id=str(order_id),
                        message="下单成功",
                        status="SUBMITTED"
                    )
                else:
                    logger.error(f"下单失败: 返回订单ID无效")
                    return OrderResult(
                        success=False,
                        message="下单失败：返回订单ID无效"
                    )
            else:
                # 模拟模式
                order_id = f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{symbol}"
                logger.info(f"[模拟] 下单成功: {symbol} {side} {quantity}@{price}")
                return OrderResult(
                    success=True,
                    order_id=order_id,
                    message="模拟下单成功",
                    filled_quantity=quantity,
                    filled_price=price or Decimal("0"),
                    status="FILLED"
                )

        except Exception as e:
            logger.error(f"下单失败: {e}")
            return OrderResult(
                success=False,
                message=f"下单异常: {str(e)}"
            )

    async def cancel_order(self, order_id: str) -> bool:
        """
        撤单

        Args:
            order_id: 订单ID

        Returns:
            是否成功
        """
        if not self.connected:
            return False

        try:
            if self.xt_trader and self.session_id:
                result = await asyncio.to_thread(
                    self.xt_trader.cancel_order,
                    self.session_id,
                    int(order_id)
                )
                return result == 0
            else:
                # 模拟模式
                logger.info(f"[模拟] 撤单成功: {order_id}")
                return True

        except Exception as e:
            logger.error(f"撤单失败: {e}")
            return False

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单状态

        Args:
            order_id: 订单ID

        Returns:
            订单状态信息
        """
        if not self.connected:
            return {"status": "UNKNOWN", "message": "未连接"}

        try:
            if self.xt_trader and self.session_id:
                orders = await asyncio.to_thread(
                    self.xt_trader.query_stock_order,
                    self.session_id,
                    self.account_id
                )

                for order in orders:
                    if str(order.order_id) == order_id:
                        return {
                            "order_id": order_id,
                            "symbol": order.stock_code,
                            "status": self._convert_order_status(order.order_status),
                            "filled_quantity": order.traded_volume,
                            "filled_price": order.traded_price,
                            "message": "查询成功"
                        }

                return {"status": "NOT_FOUND", "message": "订单不存在"}
            else:
                # 模拟模式
                return {
                    "order_id": order_id,
                    "status": "FILLED",
                    "message": "模拟订单已成交"
                }

        except Exception as e:
            logger.error(f"查询订单状态失败: {e}")
            return {"status": "ERROR", "message": str(e)}

    async def subscribe_quote(self, symbols: List[str], callback):
        """
        订阅实时行情

        Args:
            symbols: 股票代码列表
            callback: 回调函数
        """
        if not self.xt_quote:
            logger.warning("行情接口未初始化")
            return

        try:
            # 转换股票代码
            xt_symbols = [self._convert_symbol(s) for s in symbols]

            # 订阅行情
            await asyncio.to_thread(
                self.xt_quote.subscribe_quote,
                xt_symbols,
                callback
            )

            logger.info(f"已订阅行情: {symbols}")

        except Exception as e:
            logger.error(f"订阅行情失败: {e}")

    def _convert_symbol(self, symbol: str) -> str:
        """
        转换股票代码格式

        将 000001.SZ 格式转换为 QMT 格式
        """
        if '.' in symbol:
            code, market = symbol.split('.')
            if market.upper() == 'SZ':
                return f"0.{code}"
            elif market.upper() == 'SH':
                return f"1.{code}"
        return symbol

    def _convert_order_status(self, xt_status: int) -> str:
        """转换订单状态"""
        status_map = {
            48: "PENDING",      # 待报
            49: "SUBMITTED",    # 已报
            50: "PARTIAL",      # 部成
            51: "FILLED",       # 已成
            52: "CANCELED",     # 已撤
            53: "REJECTED",     # 废单
        }
        return status_map.get(xt_status, "UNKNOWN")
