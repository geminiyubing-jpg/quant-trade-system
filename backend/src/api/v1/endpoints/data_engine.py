"""
数据引擎 API 端点

提供统一的数据管理、多数据源适配和数据订阅的 REST API。
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Query, Body, BackgroundTasks
from pydantic import BaseModel, Field
import asyncio

from src.services.data.engine import (
    DataEngine,
    DataRequest,
    DataType,
    DataFrequency,
    AdjustmentType,
    Bar,
    DataSourceAdapter,
)


router = APIRouter()

# 全局数据引擎实例
_data_engine: Optional[DataEngine] = None


def get_data_engine() -> DataEngine:
    """获取数据引擎单例"""
    global _data_engine
    if _data_engine is None:
        _data_engine = DataEngine()
    return _data_engine


# ==============================================
# Pydantic 模型
# ==============================================

class DataFetchRequest(BaseModel):
    """数据获取请求"""
    symbols: List[str] = Field(..., description="股票代码列表")
    data_type: str = Field(default="stock_price", description="数据类型")
    frequency: str = Field(default="1d", description="数据频率")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    adjustment: str = Field(default="none", description="复权方式 (none/qfq/hfq)")
    fields: Optional[List[str]] = Field(None, description="需要的字段")
    limit: Optional[int] = Field(None, description="限制返回数量")


class LatestQuoteRequest(BaseModel):
    """最新行情请求"""
    symbols: List[str] = Field(..., description="股票代码列表")


class SubscriptionRequest(BaseModel):
    """订阅请求"""
    symbols: List[str] = Field(..., description="股票代码列表")
    frequency: str = Field(default="1m", description="数据频率")


class AdapterRegisterRequest(BaseModel):
    """适配器注册请求"""
    name: str = Field(..., description="适配器名称")
    config: Dict[str, Any] = Field(default_factory=dict, description="适配器配置")


# ==============================================
# 数据获取端点
# ==============================================

@router.post("/fetch", summary="获取数据")
async def fetch_data(request: DataFetchRequest = Body(...)):
    """
    获取历史数据

    支持多种数据类型、频率和复权方式。
    """
    try:
        engine = get_data_engine()

        # 解析日期
        start = date.fromisoformat(request.start_date) if request.start_date else None
        end = date.fromisoformat(request.end_date) if request.end_date else None

        # 创建数据请求
        data_request = DataRequest(
            symbols=request.symbols,
            data_type=DataType(request.data_type),
            frequency=DataFrequency(request.frequency),
            start_date=start,
            end_date=end,
            adjustment=AdjustmentType(request.adjustment),
            fields=request.fields,
            limit=request.limit,
        )

        # 获取数据
        data = await engine.get_data(data_request)

        return {
            "success": True,
            "data": data,
            "meta": {
                "request_id": data_request.request_id,
                "symbols": request.symbols,
                "data_type": request.data_type,
                "frequency": request.frequency,
                "count": len(data),
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.post("/latest", summary="获取最新行情")
async def get_latest_quotes(request: LatestQuoteRequest = Body(...)):
    """
    获取最新行情

    Args:
        request: 包含股票代码列表的请求
    """
    try:
        engine = get_data_engine()
        quotes = await engine.get_latest(request.symbols)

        result = []
        for symbol, bar in quotes.items():
            result.append(bar.to_dict())

        return {
            "success": True,
            "data": result,
            "meta": {
                "count": len(result),
                "timestamp": datetime.now().isoformat(),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新行情失败: {str(e)}")


@router.get("/quote/{symbol}", summary="获取单个股票最新行情")
async def get_single_quote(symbol: str):
    """
    获取单个股票的最新行情

    Args:
        symbol: 股票代码
    """
    try:
        engine = get_data_engine()
        quotes = await engine.get_latest([symbol])

        if symbol not in quotes:
            raise HTTPException(status_code=404, detail=f"未找到 {symbol} 的行情数据")

        return {
            "success": True,
            "data": quotes[symbol].to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情失败: {str(e)}")


@router.get("/corporate-actions/{symbol}", summary="获取公司行动")
async def get_corporate_actions(
    symbol: str,
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
):
    """
    获取公司行动（分红、送股、配股等）

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        engine = get_data_engine()

        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None

        actions = await engine.get_corporate_actions(symbol, start, end)

        result = []
        for action in actions:
            result.append({
                "symbol": action.symbol,
                "action_type": action.action_type,
                "ex_date": action.ex_date.isoformat(),
                "record_date": action.record_date.isoformat() if action.record_date else None,
                "pay_date": action.pay_date.isoformat() if action.pay_date else None,
                "dividend_per_share": str(action.dividend_per_share),
                "bonus_per_share": str(action.bonus_per_share),
                "transfer_per_share": str(action.transfer_per_share),
                "rights_per_share": str(action.rights_per_share),
                "rights_price": str(action.rights_price),
                "split_ratio": str(action.split_ratio),
            })

        return {
            "success": True,
            "data": result,
            "meta": {
                "symbol": symbol,
                "count": len(result),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取公司行动失败: {str(e)}")


# ==============================================
# 适配器管理端点
# ==============================================

@router.get("/adapters", summary="获取适配器列表")
async def list_adapters():
    """获取所有已注册的数据源适配器"""
    engine = get_data_engine()
    adapters = engine.list_adapters()

    return {
        "success": True,
        "data": adapters,
    }


@router.get("/adapters/{name}", summary="获取适配器详情")
async def get_adapter_detail(name: str):
    """
    获取适配器详情

    Args:
        name: 适配器名称
    """
    engine = get_data_engine()
    adapter = engine.get_adapter(name)

    if adapter is None:
        raise HTTPException(status_code=404, detail=f"适配器不存在: {name}")

    return {
        "success": True,
        "data": {
            "name": name,
            "description": adapter.description,
            "is_connected": adapter.is_connected,
            "is_realtime": adapter.is_realtime,
            "priority": adapter.priority,
            "supported_types": [t.value for t in adapter.supported_types],
            "supported_frequencies": [f.value for f in adapter.supported_frequencies],
        },
    }


@router.post("/adapters/connect", summary="连接所有适配器")
async def connect_all_adapters(background_tasks: BackgroundTasks):
    """连接所有数据源适配器"""
    engine = get_data_engine()

    # 在后台执行连接
    async def connect():
        await engine.connect_all()

    background_tasks.add_task(connect)

    return {
        "success": True,
        "message": "正在连接所有数据源适配器",
    }


@router.post("/adapters/disconnect", summary="断开所有适配器")
async def disconnect_all_adapters():
    """断开所有数据源适配器连接"""
    engine = get_data_engine()
    await engine.disconnect_all()

    return {
        "success": True,
        "message": "已断开所有数据源适配器连接",
    }


# ==============================================
# 实时订阅端点
# ==============================================

# 存储活跃订阅
_active_subscriptions: Dict[str, asyncio.Task] = {}


@router.post("/subscribe", summary="订阅实时数据")
async def subscribe_realtime(request: SubscriptionRequest = Body(...)):
    """
    订阅实时数据

    注意：实际的数据推送通过 WebSocket 实现，此接口仅创建订阅。
    """
    try:
        engine = get_data_engine()

        # 创建订阅（使用占位回调）
        subscription_id = await engine.subscribe(
            symbols=request.symbols,
            callback=lambda bar: None,  # 实际推送通过 WebSocket
            frequency=DataFrequency(request.frequency),
        )

        return {
            "success": True,
            "data": {
                "subscription_id": subscription_id,
                "symbols": request.symbols,
                "frequency": request.frequency,
            },
            "message": "订阅成功，请通过 WebSocket 接收数据",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"订阅失败: {str(e)}")


@router.delete("/subscribe/{subscription_id}", summary="取消订阅")
async def unsubscribe_realtime(subscription_id: str):
    """
    取消实时数据订阅

    Args:
        subscription_id: 订阅 ID
    """
    engine = get_data_engine()
    success = await engine.unsubscribe(subscription_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"订阅不存在: {subscription_id}")

    return {
        "success": True,
        "message": f"订阅 {subscription_id} 已取消",
    }


@router.get("/subscriptions", summary="获取活跃订阅列表")
async def list_subscriptions():
    """获取所有活跃的数据订阅"""
    engine = get_data_engine()
    status = engine.get_status()

    return {
        "success": True,
        "data": {
            "active_subscriptions": status["active_subscriptions"],
        },
    }


# ==============================================
# 缓存管理端点
# ==============================================

@router.delete("/cache", summary="清除缓存")
async def clear_cache(pattern: Optional[str] = Query(None, description="缓存键模式")):
    """
    清除数据缓存

    Args:
        pattern: 缓存键模式（支持通配符）
    """
    engine = get_data_engine()
    engine.invalidate_cache(pattern)

    return {
        "success": True,
        "message": f"缓存已清除" + (f" (pattern: {pattern})" if pattern else ""),
    }


# ==============================================
# 引擎状态端点
# ==============================================

@router.get("/status", summary="获取引擎状态")
async def get_engine_status():
    """获取数据引擎的整体状态"""
    engine = get_data_engine()
    status = engine.get_status()

    return {
        "success": True,
        "data": status,
    }


@router.get("/data-types", summary="获取支持的数据类型")
async def get_data_types():
    """获取所有支持的数据类型"""
    return {
        "success": True,
        "data": [
            {"value": t.value, "name": t.name}
            for t in DataType
        ],
    }


@router.get("/frequencies", summary="获取支持的数据频率")
async def get_frequencies():
    """获取所有支持的数据频率"""
    return {
        "success": True,
        "data": [
            {"value": f.value, "name": f.name}
            for f in DataFrequency
        ],
    }


@router.get("/adjustments", summary="获取支持的复权方式")
async def get_adjustments():
    """获取所有支持的复权方式"""
    return {
        "success": True,
        "data": [
            {"value": a.value, "name": a.name, "description": {
                "none": "不复权",
                "qfq": "前复权",
                "hfq": "后复权",
            }.get(a.value, "")}
            for a in AdjustmentType
        ],
    }
