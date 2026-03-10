"""
策略注册表 API 端点

提供策略注册、发现、实例化和管理的 REST API。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from src.services.strategy.registry import (
    StrategyRegistry,
    StrategyMetadata,
    StrategyFrequency,
    StrategyLifecycleStatus,
    strategy_registry,
)
from src.services.strategy.base import StrategyConfig, StrategyStatus


router = APIRouter()


# ==============================================
# Pydantic 模型
# ==============================================

class StrategyCreateRequest(BaseModel):
    """创建策略请求"""
    strategy_id: str = Field(..., description="策略唯一标识")
    name: str = Field(..., description="策略名称")
    version: str = Field(default="1.0.0", description="版本号")
    author: str = Field(default="", description="作者")
    description: str = Field(default="", description="描述")
    category: str = Field(default="general", description="分类")
    frequency: str = Field(default="1d", description="运行频率")
    tags: List[str] = Field(default_factory=list, description="标签")
    params_schema: Dict[str, Any] = Field(default_factory=dict, description="参数 JSON Schema")
    default_params: Dict[str, Any] = Field(default_factory=dict, description="默认参数")
    min_history_bars: int = Field(default=0, description="最小历史 K 线数量")
    supported_markets: List[str] = Field(default=["A股"], description="支持的市场")
    risk_level: str = Field(default="medium", description="风险等级")


class StrategyInstanceCreateRequest(BaseModel):
    """创建策略实例请求"""
    strategy_id: str = Field(..., description="策略 ID")
    instance_id: Optional[str] = Field(default=None, description="实例 ID（可选）")
    params: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    initial_capital: float = Field(default=100000, description="初始资金")
    execution_mode: str = Field(default="PAPER", description="执行模式")


class StrategyStatusUpdateRequest(BaseModel):
    """更新策略状态请求"""
    status: str = Field(..., description="新状态")


class StrategyFilterRequest(BaseModel):
    """策略过滤请求"""
    category: Optional[str] = None
    status: Optional[str] = None
    frequency: Optional[str] = None
    tags: Optional[List[str]] = None


# ==============================================
# 策略注册表端点
# ==============================================

@router.get("/", summary="获取策略列表")
async def list_strategies(
    category: Optional[str] = Query(None, description="按分类过滤"),
    status: Optional[str] = Query(None, description="按状态过滤"),
    frequency: Optional[str] = Query(None, description="按频率过滤"),
    tags: Optional[str] = Query(None, description="按标签过滤（逗号分隔）"),
):
    """
    获取已注册的策略列表

    支持按分类、状态、频率和标签过滤。
    """
    try:
        # 处理过滤参数
        status_enum = None
        if status:
            try:
                status_enum = StrategyLifecycleStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

        frequency_enum = None
        if frequency:
            try:
                frequency_enum = StrategyFrequency(frequency)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的频率: {frequency}")

        tags_list = tags.split(",") if tags else None

        # 获取策略列表
        strategies = strategy_registry.list_strategies(
            category=category,
            status=status_enum,
            frequency=frequency_enum,
            tags=tags_list,
        )

        return {
            "success": True,
            "data": [s.to_dict() for s in strategies],
            "meta": {
                "total": len(strategies),
                "filters": {
                    "category": category,
                    "status": status,
                    "frequency": frequency,
                    "tags": tags_list,
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/{strategy_id}", summary="获取策略详情")
async def get_strategy(strategy_id: str):
    """
    获取指定策略的详细信息

    Args:
        strategy_id: 策略 ID
    """
    metadata = strategy_registry.get_strategy(strategy_id)

    if metadata is None:
        raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

    return {
        "success": True,
        "data": metadata.to_dict(),
    }


@router.post("/", summary="注册策略（手动）")
async def register_strategy(request: StrategyCreateRequest = Body(...)):
    """
    手动注册一个策略

    注意：通常策略通过装饰器自动注册，此接口用于动态注册。
    """
    try:
        # 这里需要动态导入策略类
        # 实际应用中，可能需要从数据库或文件系统加载策略代码
        raise HTTPException(
            status_code=501,
            detail="手动注册策略需要提供策略类，请使用装饰器方式或文件扫描"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册策略失败: {str(e)}")


@router.delete("/{strategy_id}", summary="注销策略")
async def unregister_strategy(strategy_id: str):
    """
    注销一个策略

    Args:
        strategy_id: 策略 ID
    """
    success = strategy_registry.unregister(strategy_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

    return {
        "success": True,
        "message": f"策略 {strategy_id} 已注销",
    }


@router.put("/{strategy_id}/status", summary="更新策略状态")
async def update_strategy_status(
    strategy_id: str,
    request: StrategyStatusUpdateRequest = Body(...),
):
    """
    更新策略的生命周期状态

    Args:
        strategy_id: 策略 ID
        request: 状态更新请求
    """
    try:
        new_status = StrategyLifecycleStatus(request.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态: {request.status}"
        )

    success = strategy_registry.update_strategy_status(strategy_id, new_status)

    if not success:
        raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

    return {
        "success": True,
        "message": f"策略 {strategy_id} 状态已更新为 {request.status}",
    }


@router.post("/scan", summary="扫描目录注册策略")
async def scan_strategies(
    directory: str = Body(..., embed=True, description="要扫描的目录路径"),
    recursive: bool = Body(True, embed=True, description="是否递归扫描子目录"),
):
    """
    扫描目录自动注册策略

    Args:
        directory: 目录路径
        recursive: 是否递归扫描
    """
    try:
        count = strategy_registry.scan_directory(directory, recursive)

        return {
            "success": True,
            "data": {
                "directory": directory,
                "registered_count": count,
            },
            "message": f"成功注册 {count} 个策略",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描目录失败: {str(e)}")


# ==============================================
# 策略实例端点
# ==============================================

@router.post("/instances", summary="创建策略实例")
async def create_strategy_instance(request: StrategyInstanceCreateRequest = Body(...)):
    """
    创建策略实例

    同一个策略类可以创建多个实例（使用不同参数）。
    """
    try:
        config = StrategyConfig(
            name=f"{request.strategy_id}_instance",
            initial_capital=request.initial_capital,
            execution_mode=request.execution_mode,
            parameters=request.params,
        )

        instance = strategy_registry.create_instance(
            strategy_id=request.strategy_id,
            config=config,
            params=request.params,
            instance_id=request.instance_id,
        )

        # 获取实例 ID
        instance_id = request.instance_id
        if instance_id is None:
            # 从注册表获取最后创建的实例 ID
            instances = strategy_registry.list_instances()
            for iid, inst in instances.items():
                if inst is instance:
                    instance_id = iid
                    break

        return {
            "success": True,
            "data": {
                "instance_id": instance_id,
                "strategy_id": request.strategy_id,
                "status": instance.status.value,
                "parameters": instance.parameters,
            },
            "message": f"策略实例 {instance_id} 创建成功",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建策略实例失败: {str(e)}")


@router.get("/instances/", summary="获取所有策略实例")
async def list_strategy_instances():
    """获取所有策略实例"""
    instances = strategy_registry.list_instances()

    result = []
    for instance_id, instance in instances.items():
        result.append({
            "instance_id": instance_id,
            "name": instance.name,
            "status": instance.status.value,
            "parameters": instance.parameters,
        })

    return {
        "success": True,
        "data": result,
        "meta": {
            "total": len(result),
        }
    }


@router.get("/instances/{instance_id}", summary="获取策略实例详情")
async def get_strategy_instance(instance_id: str):
    """
    获取策略实例详情

    Args:
        instance_id: 实例 ID
    """
    instance = strategy_registry.get_instance(instance_id)

    if instance is None:
        raise HTTPException(status_code=404, detail=f"策略实例不存在: {instance_id}")

    return {
        "success": True,
        "data": {
            "instance_id": instance_id,
            "name": instance.name,
            "description": instance.description,
            "status": instance.status.value,
            "parameters": instance.parameters,
            "state": instance.get_state(),
        },
    }


@router.delete("/instances/{instance_id}", summary="移除策略实例")
async def remove_strategy_instance(instance_id: str):
    """
    移除策略实例

    Args:
        instance_id: 实例 ID
    """
    success = strategy_registry.remove_instance(instance_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"策略实例不存在: {instance_id}")

    return {
        "success": True,
        "message": f"策略实例 {instance_id} 已移除",
    }


# ==============================================
# 注册表状态端点
# ==============================================

@router.get("/registry/status", summary="获取注册表状态")
async def get_registry_status():
    """获取策略注册表的整体状态"""
    status = strategy_registry.export_registry()

    return {
        "success": True,
        "data": status,
    }


@router.get("/registry/categories", summary="获取策略分类列表")
async def get_strategy_categories():
    """获取所有策略分类"""
    strategies = strategy_registry.list_strategies()
    categories = list(set(s.category for s in strategies))

    return {
        "success": True,
        "data": categories,
    }


@router.get("/registry/tags", summary="获取所有标签")
async def get_strategy_tags():
    """获取所有策略标签"""
    strategies = strategy_registry.list_strategies()
    tags = set()
    for s in strategies:
        tags.update(s.tags)

    return {
        "success": True,
        "data": list(tags),
    }


@router.get("/by-status/{status}", summary="按状态获取策略")
async def get_strategies_by_status(status: str):
    """
    按生命周期状态获取策略列表

    Args:
        status: 策略状态（development/testing/backtest_passed/paper_trading/live_trading/deprecated/suspended）
    """
    try:
        status_enum = StrategyLifecycleStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

    strategies = strategy_registry.get_strategies_by_status(status_enum)

    return {
        "success": True,
        "data": [s.to_dict() for s in strategies],
        "meta": {
            "status": status,
            "total": len(strategies),
        }
    }
