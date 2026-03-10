"""
==============================================
WebSocket 实时行情 - API 端点
==============================================
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import decode_token
from src.schemas.market_data import (
    ErrorMessage,
    PingMessage,
    PongMessage,
    QuotePushMessage,
    SubscriptionRequest,
    UnsubscribeRequest,
)
from src.services.websocket.connection_manager import Connection, connection_manager
from src.services.websocket.market_data_service import market_data_service
from src.services.websocket.redis_manager import redis_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/market/symbols")
async def get_available_symbols(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    获取可用的股票列表

    Args:
        limit: 返回数量限制

    Returns:
        list: 股票列表
    """
    try:
        simulated_stocks = market_data_service.get_simulated_stocks()
        symbols = [
            {"symbol": symbol, "name": info["name"], "price": info["base_price"]}
            for symbol, info in list(simulated_stocks.items())[:limit]
        ]
        return {"symbols": symbols, "total": len(symbols)}
    except Exception as e:
        logger.error(f"❌ 获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取股票列表失败")


@router.get("/market/quotes")
async def get_market_quotes(
    symbols: str = Query(..., description="股票代码，逗号分隔，例如: 000001.SZ,000002.SZ"),
):
    """
    获取实时行情数据（HTTP 接口）

    Args:
        symbols: 股票代码，逗号分隔

    Returns:
        dict: 行情数据
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        quotes = await market_data_service.get_current_quotes(symbol_list)
        return {
            "quotes": {symbol: quote.model_dump() for symbol, quote in quotes.items()},
            "total": len(quotes),
        }
    except Exception as e:
        logger.error(f"❌ 获取行情数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取行情数据失败")


@router.websocket("/ws/market")
async def websocket_market_data(websocket: WebSocket):
    """
    WebSocket 实时行情推送

    连接 URL: ws://localhost:8000/api/v1/ws/market?token={jwt_token}

    消息协议:
    1. 订阅行情: {"type": "subscribe", "symbols": ["000001.SZ", "000002.SZ"]}
    2. 取消订阅: {"type": "unsubscribe", "symbols": ["000001.SZ"]}
    3. 心跳检测: {"type": "ping"}

    服务器推送:
    1. 行情推送: {"type": "quote", "data": {...}}
    2. 心跳响应: {"type": "pong"}
    3. 错误消息: {"type": "error", "message": "...", "code": 400}
    """

    # 验证 Token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    try:
        # 解码 Token 获取用户 ID
        payload = decode_token(token)
        user_id = payload.sub  # TokenPayload.sub 已经是字符串（UUID）
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
        # 将 UUID 字符串保持为字符串类型
    except Exception as e:
        logger.error(f"❌ Token 验证失败: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # 接受连接
    connection = await connection_manager.connect(websocket, user_id)

    # 恢复之前的订阅（从 Redis）
    previous_subscriptions = redis_manager.get_user_subscriptions(user_id)
    if previous_subscriptions:
        connection.subscriptions = previous_subscriptions
        logger.info(f"📋 恢复用户 {user_id} 的订阅: {len(previous_subscriptions)} 个")

    # 发送欢迎消息
    try:
        await connection.send_json(
            {
                "type": "connected",
                "data": {
                    "connection_id": connection.connection_id,
                    "user_id": user_id,
                    "subscriptions": list(connection.subscriptions),
                    "message": "WebSocket 连接成功",
                    "connected_at": connection.connected_at.isoformat(),
                },
            }
        )
    except Exception as e:
        logger.error(f"❌ 发送欢迎消息失败: {e}")
        await connection_manager.disconnect(connection.connection_id)
        return

    logger.info(f"✅ WebSocket 连接建立: {connection.connection_id} (用户: {user_id})")

    # 消息处理循环
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            logger.debug(f"📨 收到消息 (用户: {user_id}): {data}")

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                # 处理不同类型的消息
                if msg_type == "subscribe":
                    await _handle_subscribe(connection, message)
                elif msg_type == "unsubscribe":
                    await _handle_unsubscribe(connection, message)
                elif msg_type == "ping":
                    await _handle_ping(connection)
                else:
                    await connection.send_json(
                        {"type": "error", "message": f"Unknown message type: {msg_type}", "code": 400}
                    )

            except json.JSONDecodeError:
                await connection.send_json({"type": "error", "message": "Invalid JSON format", "code": 400})
            except Exception as e:
                logger.error(f"❌ 处理消息失败: {e}")
                await connection.send_json({"type": "error", "message": str(e), "code": 500})

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket 断开连接: {connection.connection_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket 异常: {e}")
    finally:
        # 清理连接
        await connection_manager.disconnect(connection.connection_id)


async def _handle_subscribe(connection: Connection, message: dict):
    """
    处理订阅请求

    Args:
        connection: 连接对象
        message: 消息内容
    """
    try:
        # 验证请求格式
        request = SubscriptionRequest(**message)
        symbols = request.symbols

        # 验证订阅数量限制
        if len(connection.subscriptions) + len(symbols) > 100:
            await connection.send_json(
                {"type": "error", "message": "超过订阅数量限制（最多 100 个）", "code": 400}
            )
            return

        # 添加订阅
        for symbol in symbols:
            # 更新内存中的订阅
            connection.subscriptions.add(symbol)
            # 更新 Redis
            redis_manager.add_subscription(connection.user_id, symbol)

        logger.info(f"✅ 用户 {connection.user_id} 订阅: {symbols}")

        # 立即推送当前行情
        quotes = await market_data_service.get_current_quotes(symbols)
        for symbol, quote in quotes.items():
            await connection.send_json({"type": "quote", "data": quote.model_dump(mode='json')})

        # 发送确认
        await connection.send_json(
            {
                "type": "subscribed",
                "data": {"symbols": symbols, "total_subscriptions": len(connection.subscriptions)},
            }
        )

    except Exception as e:
        logger.error(f"❌ 处理订阅失败: {e}")
        await connection.send_json({"type": "error", "message": str(e), "code": 500})


async def _handle_unsubscribe(connection: Connection, message: dict):
    """
    处理取消订阅请求

    Args:
        connection: 连接对象
        message: 消息内容
    """
    try:
        # 验证请求格式
        request = UnsubscribeRequest(**message)
        symbols = request.symbols

        # 移除订阅
        for symbol in symbols:
            # 更新内存中的订阅
            connection.subscriptions.discard(symbol)
            # 更新 Redis
            redis_manager.remove_subscription(connection.user_id, symbol)

        logger.info(f"✅ 用户 {connection.user_id} 取消订阅: {symbols}")

        # 发送确认
        await connection.send_json(
            {
                "type": "unsubscribed",
                "data": {"symbols": symbols, "total_subscriptions": len(connection.subscriptions)},
            }
        )

    except Exception as e:
        logger.error(f"❌ 处理取消订阅失败: {e}")
        await connection.send_json({"type": "error", "message": str(e), "code": 500})


async def _handle_ping(connection: Connection):
    """
    处理心跳请求

    Args:
        connection: 连接对象
    """
    try:
        # 更新最后心跳时间
        connection_manager.update_last_ping(connection.connection_id)
        # 发送 pong
        await connection.send_json({"type": "pong"})
        logger.debug(f"💓 心跳响应: {connection.connection_id}")
    except Exception as e:
        logger.error(f"❌ 处理心跳失败: {e}")


@router.get("/ws/status")
async def get_websocket_status():
    """
    获取 WebSocket 服务状态

    Returns:
        dict: 服务状态信息
    """
    try:
        return {
            "status": "running" if market_data_service.is_running else "stopped",
            "connections": connection_manager.get_connection_count(),
            "market_data_service": "running" if market_data_service.is_running else "stopped",
            "redis_connected": redis_manager.ping(),
        }
    except Exception as e:
        logger.error(f"❌ 获取服务状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取服务状态失败")
