"""
策略版本管理 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models.user import User
from src.models.strategy import Strategy
from src.models.strategy_version import StrategyVersion, StrategyConfig, StrategyAuditLog, ChangeType, ActionType

router = APIRouter()


# ==============================================
# Pydantic Schemas
# ==============================================

class StrategyVersionCreate(BaseModel):
    """创建策略版本请求"""
    code: Optional[str] = Field(None, description="策略代码")
    parameters: Optional[dict] = Field(None, description="参数快照")
    change_log: str = Field(..., description="变更日志")
    change_type: ChangeType = Field(default=ChangeType.PATCH, description="变更类型")


class StrategyVersionResponse(BaseModel):
    """策略版本响应"""
    id: str
    strategy_id: str
    version_number: str
    change_log: Optional[str]
    change_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StrategyConfigUpdate(BaseModel):
    """更新策略配置请求"""
    symbols: Optional[List[str]] = Field(None, description="股票代码列表")
    allocation_ratio: Optional[Decimal] = Field(None, ge=0, le=1, description="资金分配比例")
    max_position_count: Optional[int] = Field(None, ge=1, le=50, description="最大持仓数量")
    stop_loss_ratio: Optional[Decimal] = Field(None, ge=0, le=1, description="止损比例")
    take_profit_ratio: Optional[Decimal] = Field(None, ge=0, le=1, description="止盈比例")
    execution_mode: Optional[str] = Field(None, description="执行模式")


class StrategyConfigResponse(BaseModel):
    """策略配置响应"""
    id: str
    strategy_id: str
    symbols: List[str]
    allocation_ratio: Optional[float]
    max_position_count: int
    stop_loss_ratio: Optional[float]
    take_profit_ratio: Optional[float]
    execution_mode: str
    is_active: bool

    class Config:
        from_attributes = True


class StrategyAuditLogResponse(BaseModel):
    """审计日志响应"""
    id: str
    strategy_id: str
    action_type: str
    action_description: Optional[str]
    old_value: Optional[dict]
    new_value: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================
# 策略版本管理端点
# ==============================================

@router.get("/{strategy_id}/versions", response_model=List[StrategyVersionResponse])
async def get_strategy_versions(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取策略的所有版本"""
    from src.repositories.strategy_version import StrategyVersionRepository
    repo = StrategyVersionRepository(db)
    versions = repo.get_by_strategy(strategy_id, include_inactive=True)
    return [
        StrategyVersionResponse(
            id=str(v.id),
            strategy_id=str(v.strategy_id),
            version_number=v.version_number,
            change_log=v.change_log,
            change_type=v.change_type,
            is_active=v.is_active,
            created_at=v.created_at
        )
        for v in versions
    ]


@router.get("/{strategy_id}/versions/active", response_model=Optional[StrategyVersionResponse])
async def get_active_version(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取策略当前激活版本"""
    from src.repositories.strategy_version import StrategyVersionRepository
    repo = StrategyVersionRepository(db)
    active_version = repo.get_active_version(strategy_id)
    if not active_version:
        return None
    return StrategyVersionResponse(
        id=str(active_version.id),
        strategy_id=str(active_version.strategy_id),
        version_number=active_version.version_number,
        change_log=active_version.change_log,
        change_type=active_version.change_type,
        is_active=active_version.is_active,
        created_at=active_version.created_at
    )


@router.post("/{strategy_id}/versions", response_model=StrategyVersionResponse)
async def create_version(
    strategy_id: str,
    request: StrategyVersionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新版本"""
    from src.services.strategy.manager import StrategyManager
    manager = StrategyManager(db)

    version = manager.create_version(
        strategy_id=strategy_id,
        code=request.code,
        parameters=request.parameters,
        change_log=request.change_log,
        change_type=request.change_type,
        created_by=str(current_user.id)
    )
    return StrategyVersionResponse(
        id=str(version.id),
        strategy_id=str(version.strategy_id),
        version_number=version.version_number,
        change_log=version.change_log,
        change_type=version.change_type,
        is_active=version.is_active,
        created_at=version.created_at
    )


@router.post("/{strategy_id}/versions/{version_id}/activate")
async def activate_version(
    strategy_id: str,
    version_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """激活指定版本"""
    from src.services.strategy.manager import StrategyManager
    manager = StrategyManager(db)
    success = manager.activate_version(version_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"success": True, "message": f"Version {version_id} activated"}


@router.get("/{strategy_id}/config", response_model=StrategyConfigResponse)
async def get_strategy_config(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取策略配置"""
    from src.services.strategy.manager import StrategyManager
    manager = StrategyManager(db)
    config = manager.get_config(strategy_id)
    if not config:
        config = manager.create_default_config(strategy_id, str(current_user.id))
    return StrategyConfigResponse(
        id=str(config.id),
        strategy_id=str(config.strategy_id),
        symbols=config.symbols or [],
        allocation_ratio=float(config.allocation_ratio) if config.allocation_ratio else None,
        max_position_count=config.max_position_count,
        stop_loss_ratio=float(config.stop_loss_ratio) if config.stop_loss_ratio else None,
        take_profit_ratio=float(config.take_profit_ratio) if config.take_profit_ratio else None,
        execution_mode=config.execution_mode,
        is_active=config.is_active
    )


@router.put("/{strategy_id}/config", response_model=StrategyConfigResponse)
async def update_strategy_config(
    strategy_id: str,
    request: StrategyConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新策略配置"""
    from src.services.strategy.manager import StrategyManager
    manager = StrategyManager(db)
    config = manager.update_config(
        strategy_id=strategy_id,
        config_data=request.model_dump(exclude_none=True),
        user_id=str(current_user.id)
    )
    return StrategyConfigResponse(
        id=str(config.id),
        strategy_id=str(config.strategy_id),
        symbols=config.symbols or [],
        allocation_ratio=float(config.allocation_ratio) if config.allocation_ratio else None,
        max_position_count=config.max_position_count,
        stop_loss_ratio=float(config.stop_loss_ratio) if config.stop_loss_ratio else None,
        take_profit_ratio=float(config.take_profit_ratio) if config.take_profit_ratio else None,
        execution_mode=config.execution_mode,
        is_active=config.is_active
    )


@router.get("/{strategy_id}/audit-logs", response_model=List[StrategyAuditLogResponse])
async def get_audit_logs(
    strategy_id: str,
    action_type: Optional[ActionType] = Query(None),
    limit: int = Query(100, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取审计日志"""
    from src.services.strategy.manager import StrategyManager
    manager = StrategyManager(db)
    logs = manager.get_audit_log(
        strategy_id=strategy_id,
        action_type=action_type,
        limit=limit
    )
    return [
        StrategyAuditLogResponse(
            id=str(log.id),
            strategy_id=str(log.strategy_id),
            action_type=log.action_type,
            action_description=log.action_description,
            old_value=log.old_value,
            new_value=log.new_value,
            created_at=log.created_at
        )
        for log in logs
    ]
