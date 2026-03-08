"""
Trading Endpoint

交易相关端点（订单、持仓）。
"""

from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from enum import Enum
import uuid

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.repositories import OrderRepository, PositionRepository, UserSettingsRepository
from src.models.trading import Order, Position
from src.models.user import User
from src.schemas.trading import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderListResponse,
    PositionResponse,
    PositionListResponse,
    PositionSummary,
    ExecutionMode,
    TradingModeStatus,
    TradingModeSwitchRequest,
    TradingModeSwitchResponse,
    LiveTradingPasswordRequest,
    LiveTradingPasswordResponse,
)
from src.services.risk import RiskControlEngine

router = APIRouter()


# ==============================================
# 依赖注入
# ==============================================

def get_order_repository() -> OrderRepository:
    """获取订单 Repository"""
    return OrderRepository(Order)


def get_position_repository() -> PositionRepository:
    """获取持仓 Repository"""
    return PositionRepository(Position)


def get_user_settings_repository() -> UserSettingsRepository:
    """获取用户设置 Repository"""
    return UserSettingsRepository()


# ==============================================
# 订单管理
# ==============================================

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    创建订单

    Args:
        order_in: 订单创建数据
        current_user: 当前用户
        db: 数据库会话
        order_repo: 订单 Repository

    Returns:
        创建的订单信息

    Raises:
        HTTPException: 创建失败
    """
    from src.models.trading import Order as OrderModel

    # 🔴 P0 架构红线：强制验证 execution_mode 字段
    if not order_in.execution_mode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="execution_mode 字段不能为空（架构红线：强制隔离模拟/实盘）"
        )

    # TODO: 验证股票代码是否存在
    # TODO: 验证策略 ID 是否存在（如果提供）

    # 🔴 P0 任务：执行风控检查
    risk_engine = RiskControlEngine()

    check_results = risk_engine.validate_order(
        db=db,
        user_id=str(current_user.id),
        symbol=order_in.symbol,
        side=order_in.side,
        quantity=order_in.quantity,
        price=Decimal(str(order_in.price)),
        execution_mode=order_in.execution_mode
    )

    # 检查是否有未通过的风控检查
    failed_checks = [r for r in check_results if not r.passed]

    if failed_checks:
        # 收集所有错误消息
        error_messages = [r.message for r in failed_checks]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "订单未通过风控检查",
                "failed_checks": [
                    {
                        "type": r.check_type,
                        "severity": r.severity,
                        "message": r.message,
                        "details": r.details
                    }
                    for r in failed_checks
                ]
            }
        )

    # 创建订单（只使用数据库字段）
    order_data = {
        "id": str(uuid.uuid4()),
        "user_id": str(current_user.id),
        "ts_code": order_in.symbol,  # schema 的 symbol 映射到 ts_code
        "side": order_in.side,
        "order_type": order_in.order_type,
        "quantity": order_in.quantity,
        "price": Decimal(str(order_in.price)),
        "execution_mode": order_in.execution_mode.value if isinstance(order_in.execution_mode, Enum) else order_in.execution_mode,
        "status": "PENDING",
        "filled_quantity": 0,
        "avg_price": Decimal("0.000"),
        "create_time": datetime.utcnow(),
        "update_time": datetime.utcnow(),
        "strategy_id": order_in.strategy_id
    }

    # 创建订单对象
    order = OrderModel(**order_data)
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    execution_mode: Optional[ExecutionMode] = Query(None, description="执行模式"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    获取订单列表

    Args:
        skip: 跳过记录数
        limit: 返回记录数
        execution_mode: 执行模式（PAPER/LIVE）
        current_user: 当前用户
        db: 数据库会话
        order_repo: 订单 Repository

    Returns:
        订单列表
    """
    user_id = str(current_user.id)

    orders = order_repo.get_user_orders(
        db,
        user_id=user_id,
        skip=skip,
        limit=limit,
        execution_mode=execution_mode
    )

    total = len(orders)  # 临时处理，后续需要优化

    return OrderListResponse(total=total, items=orders)


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    获取订单详情

    Args:
        order_id: 订单 ID
        current_user: 当前用户
        db: 数据库会话
        order_repo: 订单 Repository

    Returns:
        订单信息

    Raises:
        HTTPException: 订单不存在
    """
    order = order_repo.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 验证订单属于当前用户
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此订单"
        )

    return order


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_in: OrderUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    更新订单（通常用于更新订单状态、成交数量等）

    Args:
        order_id: 订单 ID
        order_in: 订单更新数据
        current_user: 当前用户
        db: 数据库会话
        order_repo: 订单 Repository

    Returns:
        更新后的订单信息

    Raises:
        HTTPException: 订单不存在
    """
    order = order_repo.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 验证订单属于当前用户
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此订单"
        )

    # TODO: 验证订单状态是否允许更新

    updated_order = order_repo.update(db, db_obj=order, obj_in=order_in)
    return updated_order


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    撤销订单

    Args:
        order_id: 订单 ID
        current_user: 当前用户
        db: 数据库会话
        order_repo: 订单 Repository

    Raises:
        HTTPException: 订单不存在或无法撤销
    """
    order = order_repo.get(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 验证订单属于当前用户
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权撤销此订单"
        )

    # TODO: 验证订单状态是否允许撤销
    # TODO: 调用交易所 API 撤销订单（如果是实盘）

    # 更新订单状态为已撤销
    order_repo.update(db, db_obj=order, obj_in={"status": "CANCELED"})


# ==============================================
# 持仓管理
# ==============================================

@router.get("/positions", response_model=PositionListResponse)
async def list_positions(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    execution_mode: ExecutionMode = Query(ExecutionMode.PAPER, description="执行模式"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
    position_repo: PositionRepository = Depends(get_position_repository)
):
    """
    获取持仓列表

    Args:
        skip: 跳过记录数
        limit: 返回记录数
        execution_mode: 执行模式
        current_user: 当前用户
        db: 数据库会话
        position_repo: 持仓 Repository

    Returns:
        持仓列表
    """
    user_id = str(current_user.id)

    positions = position_repo.get_user_positions(
        db,
        user_id=user_id,
        execution_mode=execution_mode,
        skip=skip,
        limit=limit
    )

    total = len(positions)  # 临时处理，后续需要优化

    return PositionListResponse(total=total, items=positions)


@router.get("/positions/{symbol}", response_model=PositionResponse)
async def get_position(
    symbol: str,
    execution_mode: ExecutionMode = Query(ExecutionMode.PAPER, description="执行模式"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
    position_repo: PositionRepository = Depends(get_position_repository)
):
    """
    获取某股票的持仓详情

    Args:
        symbol: 股票代码
        execution_mode: 执行模式
        current_user: 当前用户
        db: 数据库会话
        position_repo: 持仓 Repository

    Returns:
        持仓信息

    Raises:
        HTTPException: 持仓不存在
    """
    user_id = str(current_user.id)

    position = position_repo.get_position_by_symbol(
        db,
        user_id=user_id,
        symbol=symbol,
        execution_mode=execution_mode
    )

    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="持仓不存在"
        )

    return position


@router.get("/positions/summary", response_model=PositionSummary)
async def get_position_summary(
    execution_mode: ExecutionMode = Query(ExecutionMode.PAPER, description="执行模式"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db),
    position_repo: PositionRepository = Depends(get_position_repository)
):
    """
    获取持仓汇总统计

    Args:
        execution_mode: 执行模式
        current_user: 当前用户
        db: 数据库会话
        position_repo: 持仓 Repository

    Returns:
        持仓汇总信息
    """
    user_id = str(current_user.id)

    positions = position_repo.get_user_positions(
        db,
        user_id=user_id,
        execution_mode=execution_mode,
        skip=0,
        limit=10000  # 获取所有持仓
    )

    total_market_value = sum(p.market_value or 0 for p in positions)
    total_unrealized_pnl = sum(p.unrealized_pnl or 0 for p in positions)
    total_realized_pnl = sum(p.realized_pnl for p in positions)

    return PositionSummary(
        total_market_value=total_market_value,
        total_unrealized_pnl=total_unrealized_pnl,
        total_realized_pnl=total_realized_pnl,
        position_count=len(positions)
    )



# ==============================================
# 交易模式管理
# ==============================================

@router.get("/mode", response_model=TradingModeStatus)
async def get_trading_mode(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    settings_repo: UserSettingsRepository = Depends(get_user_settings_repository)
):
    """
    获取当前交易模式

    Args:
        current_user: 当前用户
        db: 数据库会话
        settings_repo: 用户设置 Repository

    Returns:
        当前交易模式状态
    """
    from src.schemas.trading import TradingModeStatus, ExecutionMode

    # 获取用户设置
    user_settings = settings_repo.get_or_create(db, str(current_user.id))

    # 转换交易模式
    current_mode = ExecutionMode(user_settings.trading_mode)

    # 检查用户是否允许切换到实盘模式
    can_switch, requirements = user_settings.can_switch_to_live()

    # 构建警告消息
    warning_message = None
    if current_mode == ExecutionMode.LIVE:
        warning_message = "⚠️ 您当前处于实盘交易模式，所有交易将使用真实资金"

    return TradingModeStatus(
        current_mode=current_mode,
        can_switch_to_live=can_switch,
        requirements=requirements,
        warning_message=warning_message
    )


@router.post("/live-password", response_model=LiveTradingPasswordResponse)
async def set_live_trading_password(
    request: LiveTradingPasswordRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    settings_repo: UserSettingsRepository = Depends(get_user_settings_repository)
):
    """
    设置实盘交易密码

    Args:
        request: 密码设置请求
        current_user: 当前用户
        db: 数据库会话
        settings_repo: 用户设置 Repository

    Returns:
        设置结果
    """
    from src.schemas.trading import LiveTradingPasswordResponse
    from src.core.security import get_password_hash
    from src.services.audit import audit_logger

    # 验证密码匹配
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次输入的密码不一致"
        )

    # 验证密码强度
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少8个字符"
        )

    # 哈希密码
    hashed_password = get_password_hash(request.password)

    # 更新密码
    settings_repo.update_live_trading_password(
        db,
        user_id=str(current_user.id),
        hashed_password=hashed_password
    )

    # 记录审计日志
    audit_logger.log_security_event(
        db=db,
        event_type="SET_LIVE_TRADING_PASSWORD",
        severity="INFO",
        message=f"用户 {current_user.id} 设置了实盘交易密码",
        metadata={
            "user_id": str(current_user.id),
            "username": current_user.username,
            "ip_address": "localhost"  # TODO: 从请求中获取真实IP
        }
    )

    return LiveTradingPasswordResponse(
        success=True,
        message="实盘交易密码设置成功",
        has_password=True
    )


@router.get("/live-password/status", response_model=dict)
async def check_live_password_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    settings_repo: UserSettingsRepository = Depends(get_user_settings_repository)
):
    """
    检查实盘交易密码设置状态

    Args:
        current_user: 当前用户
        db: 数据库会话
        settings_repo: 用户设置 Repository

    Returns:
        密码设置状态
    """
    user_settings = settings_repo.get_or_create(db, str(current_user.id))

    return {
        "has_password": bool(user_settings.live_trading_password),
        "live_trading_enabled": user_settings.live_trading_enabled
    }


@router.post("/mode/switch", response_model=TradingModeSwitchResponse)
async def switch_trading_mode(
    request: TradingModeSwitchRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    settings_repo: UserSettingsRepository = Depends(get_user_settings_repository)
):
    """
    切换交易模式

    Args:
        request: 模式切换请求
        current_user: 当前用户
        db: 数据库会话
        settings_repo: 用户设置 Repository

    Returns:
        切换结果

    Raises:
        HTTPException: 切换失败
    """
    from src.schemas.trading import TradingModeSwitchResponse, ExecutionMode
    from src.services.audit import audit_logger

    # 获取用户当前设置
    user_settings = settings_repo.get_or_create(db, str(current_user.id))
    current_mode = ExecutionMode(user_settings.trading_mode)

    # 验证确认标志
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="需要确认切换操作"
        )

    # 如果目标模式与当前模式相同，直接返回
    if request.mode == current_mode:
        return TradingModeSwitchResponse(
            success=True,
            mode=request.mode,
            message=f"当前已是{request.mode.value}模式",
            previous_mode=current_mode
        )

    # 如果是切换到实盘模式，进行额外验证
    if request.mode == ExecutionMode.LIVE:
        # 验证密码
        if not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="切换到实盘模式需要密码验证"
            )

        # 验证密码是否正确
        if not user_settings.verify_live_trading_password(request.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="实盘交易密码错误"
            )

        # 检查是否可以切换到实盘模式
        can_switch, requirements = user_settings.can_switch_to_live()
        if not can_switch:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "不满足切换到实盘模式的条件",
                    "requirements": requirements
                }
            )

        # 记录切换到实盘模式的审计日志
        audit_logger.log_security_event(
            db=db,
            event_type="SWITCH_TO_LIVE_MODE",
            severity="WARNING",
            message=f"用户 {current_user.id} 切换到实盘交易模式",
            metadata={
                "user_id": str(current_user.id),
                "username": current_user.username,
                "target_mode": "LIVE",
                "ip_address": "localhost"  # TODO: 从请求中获取真实IP
            }
        )

    # 更新交易模式到数据库
    settings_repo.update_trading_mode(
        db,
        user_id=str(current_user.id),
        new_mode=request.mode.value,
        previous_mode=current_mode.value
    )

    # 记录模式切换操作
    audit_logger.log_trading_mode_switch(
        db=db,
        user_id=str(current_user.id),
        previous_mode=current_mode.value,
        new_mode=request.mode.value,
        ip_address="localhost",  # TODO: 从请求中获取真实IP
        user_agent="Unknown",  # TODO: 从请求头中获取
        metadata={
            "username": current_user.username,
            "email": current_user.email
        }
    )

    return TradingModeSwitchResponse(
        success=True,
        mode=request.mode,
        message=f"成功切换到{request.mode.value}模式",
        previous_mode=current_mode
    )
