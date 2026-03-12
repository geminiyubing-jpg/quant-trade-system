"""
东方财富券商接口

实现与东方财富证券的 HTTP API 对接。
适用于个人投资者的实盘交易接口。

支持功能：
- 股票交易（买入/卖出）
- 撤单
- 查询持仓和资金
- 查询订单状态

注意：
- 需要开通东方财富证券账户
- 需要申请 API 权限
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import asyncio
import logging
import hashlib
import hmac
import base64
import time
import uuid

import aiohttp

from .base import BaseBroker, OrderResult, Position, AccountInfo

logger = logging.getLogger(__name__)


class EastMoneyBroker(BaseBroker):
    """
    东方财富券商接口

    通过 HTTP API 与东方财富服务器通信。

    注意：
    - 需要开通东财证券账户并申请 API 权限
    - API 调用有频率限制
    - 建议使用内网环境提高稳定性
    """

    broker_type = "EASTMONEY"

    # API 端点
    BASE_URL = "https://api.eastmoney.com/trade/v1"
    SANDBOX_URL = "https://sandbox-api.eastmoney.com/trade/v1"

    def __init__(self, config: Dict[str, Any]):
        """
        初始化东方财富券商接口

        Args:
            config: 配置信息
                - api_key: API Key
                - api_secret: API Secret
                - account_id: 资金账号
                - sandbox: 是否使用沙箱环境（默认 True）
        """
        super().__init__(config)

        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.account_id = config.get('account_id', '')
        self.sandbox = config.get('sandbox', True)

        self.base_url = self.SANDBOX_URL if self.sandbox else self.BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None

        # 请求计数器（用于限流）
        self._request_count = 0
        self._last_reset = time.time()

    async def connect(self) -> bool:
        """连接东方财富服务器"""
        try:
            # 创建 HTTP 会话
            self.session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "QuantAI-Ecosystem/1.0"
                }
            )

            # 验证连接
            result = await self._request("GET", "/ping")

            if result and result.get("status") == "ok":
                self.connected = True
                logger.info(f"成功连接到东方财富 API ({'沙箱' if self.sandbox else '生产'}环境)")
                return True
            else:
                logger.error("连接验证失败")
                return False

        except Exception as e:
            logger.error(f"连接东方财富失败: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False
        logger.info("已断开东方财富连接")
        return True

    async def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        if not self.connected:
            raise ConnectionError("未连接到券商")

        try:
            result = await self._request(
                "GET",
                "/account/info",
                params={"account_id": self.account_id}
            )

            if result and result.get("success"):
                data = result["data"]
                return AccountInfo(
                    total_assets=Decimal(str(data.get("total_assets", 0))),
                    cash=Decimal(str(data.get("cash", 0))),
                    available_cash=Decimal(str(data.get("available_cash", 0))),
                    market_value=Decimal(str(data.get("market_value", 0))),
                    profit_loss=Decimal(str(data.get("profit_loss", 0))),
                    profit_loss_ratio=Decimal(str(data.get("profit_loss_ratio", 0)))
                )
            else:
                raise Exception(result.get("message", "获取账户信息失败"))

        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            raise

    async def get_positions(self) -> List[Position]:
        """获取持仓列表"""
        if not self.connected:
            raise ConnectionError("未连接到券商")

        try:
            result = await self._request(
                "GET",
                "/account/positions",
                params={"account_id": self.account_id}
            )

            positions = []
            if result and result.get("success"):
                for item in result.get("data", []):
                    positions.append(Position(
                        symbol=item.get("symbol", ""),
                        quantity=int(item.get("quantity", 0)),
                        available_quantity=int(item.get("available_quantity", 0)),
                        avg_price=Decimal(str(item.get("avg_price", 0))),
                        current_price=Decimal(str(item.get("current_price", 0))),
                        market_value=Decimal(str(item.get("market_value", 0))),
                        profit_loss=Decimal(str(item.get("profit_loss", 0))),
                        profit_loss_ratio=Decimal(str(item.get("profit_loss_ratio", 0)))
                    ))

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
        """下单"""
        if not self.connected:
            return OrderResult(
                success=False,
                message="未连接到券商"
            )

        try:
            data = {
                "account_id": self.account_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "price": float(price) if price else None
            }

            result = await self._request("POST", "/order/submit", json=data)

            if result and result.get("success"):
                order_data = result.get("data", {})
                return OrderResult(
                    success=True,
                    order_id=order_data.get("order_id"),
                    message="下单成功",
                    status="SUBMITTED"
                )
            else:
                return OrderResult(
                    success=False,
                    message=result.get("message", "下单失败")
                )

        except Exception as e:
            logger.error(f"下单失败: {e}")
            return OrderResult(
                success=False,
                message=f"下单异常: {str(e)}"
            )

    async def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        if not self.connected:
            return False

        try:
            result = await self._request(
                "POST",
                f"/order/{order_id}/cancel",
                json={"account_id": self.account_id}
            )

            return result and result.get("success", False)

        except Exception as e:
            logger.error(f"撤单失败: {e}")
            return False

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        if not self.connected:
            return {"status": "UNKNOWN", "message": "未连接"}

        try:
            result = await self._request(
                "GET",
                f"/order/{order_id}",
                params={"account_id": self.account_id}
            )

            if result and result.get("success"):
                data = result.get("data", {})
                return {
                    "order_id": order_id,
                    "symbol": data.get("symbol"),
                    "status": data.get("status"),
                    "filled_quantity": data.get("filled_quantity"),
                    "filled_price": data.get("filled_price"),
                    "message": "查询成功"
                }
            else:
                return {"status": "ERROR", "message": result.get("message", "查询失败")}

        except Exception as e:
            logger.error(f"查询订单状态失败: {e}")
            return {"status": "ERROR", "message": str(e)}

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        json: Dict = None
    ) -> Optional[Dict]:
        """
        发送 API 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: URL 参数
            json: JSON 数据

        Returns:
            响应数据
        """
        if not self.session:
            return None

        # 限流检查
        await self._rate_limit()

        # 构建请求
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())

        # 生成签名
        signature = self._generate_signature(method, endpoint, timestamp, nonce, json)

        headers = {
            "X-Api-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature
        }

        try:
            async with self.session.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers
            ) as response:
                self._request_count += 1

                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"API 请求失败: {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"API 请求异常: {e}")
            return None

    def _generate_signature(
        self,
        method: str,
        endpoint: str,
        timestamp: str,
        nonce: str,
        body: Dict = None
    ) -> str:
        """
        生成请求签名

        Args:
            method: HTTP 方法
            endpoint: API 端点
            timestamp: 时间戳
            nonce: 随机字符串
            body: 请求体

        Returns:
            签名字符串
        """
        # 构建签名字符串
        sign_str = f"{method}\n{endpoint}\n{timestamp}\n{nonce}"
        if body:
            import json
            sign_str += f"\n{json.dumps(body, separators=(',', ':'))}"

        # HMAC-SHA256 签名
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode('utf-8')

    async def _rate_limit(self):
        """请求限流"""
        current_time = time.time()

        # 每秒重置计数器
        if current_time - self._last_reset >= 1:
            self._request_count = 0
            self._last_reset = current_time

        # 每秒最多 10 次请求
        if self._request_count >= 10:
            sleep_time = 1 - (current_time - self._last_reset)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self._request_count = 0
            self._last_reset = time.time()
