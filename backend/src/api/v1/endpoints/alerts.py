"""
价格预警 API Endpoints
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models import User, PriceAlert, AlertHistory, Stock
from src.models.alert import AlertType
from src.schemas.alert import (
    PriceAlertCreate,
    PriceAlertUpdate,
    PriceAlertResponse,
    PriceAlertListResponse,
    AlertHistoryResponse,
    AlertHistoryListResponse,
    AlertHistoryAcknowledge,
    AlertSettings,
    AlertSettingsUpdate,
)

router = APIRouter()


# ==============================================
# 价格预警 API
# ==============================================

@router.get("", response_model=PriceAlertListResponse)
async def get_alerts(
    is_active: Optional[bool] = Query(None, description="是否启用"),
    symbol: Optional[str] = Query(None, description="股票代码"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的价格预警列表"""
    query = db.query(PriceAlert).filter(PriceAlert.user_id == current_user.id)

    if is_active is not None:
        query = query.filter(PriceAlert.is_active == is_active)

    if symbol:
        query = query.filter(PriceAlert.symbol == symbol)

    alerts = query.order_by(desc(PriceAlert.created_at)).all()

    # 获取股票信息
    result = []
    for alert in alerts:
        stock = db.query(Stock).filter(Stock.symbol == alert.symbol).first()
        alert_dict = {
            "id": alert.id,
            "user_id": alert.user_id,
            "symbol": alert.symbol,
            "alert_type": alert.alert_type,
            "target_value": alert.target_value,
            "current_price": alert.current_price,
            "is_active": alert.is_active,
            "is_triggered": alert.is_triggered,
            "triggered_at": alert.triggered_at,
            "notification_sent": alert.notification_sent,
            "created_at": alert.created_at,
            "updated_at": alert.updated_at,
            "stock_name": stock.name if stock else None,
        }
        result.append(PriceAlertResponse(**alert_dict))

    return PriceAlertListResponse(total=len(result), items=result)


@router.post("", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: PriceAlertCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """创建价格预警"""
    # 检查股票是否存在
    stock = db.query(Stock).filter(Stock.symbol == alert_data.symbol).first()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"股票 {alert_data.symbol} 不存在",
        )

    # 检查是否已存在相同的预警
    existing = (
        db.query(PriceAlert)
        .filter(
            PriceAlert.user_id == current_user.id,
            PriceAlert.symbol == alert_data.symbol,
            PriceAlert.alert_type == alert_data.alert_type,
            PriceAlert.target_value == alert_data.target_value,
            PriceAlert.is_active == True,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在相同的预警",
        )

    # 创建预警
    alert = PriceAlert(
        user_id=current_user.id,
        symbol=alert_data.symbol,
        alert_type=alert_data.alert_type,
        target_value=alert_data.target_value,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return PriceAlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        symbol=alert.symbol,
        alert_type=alert.alert_type,
        target_value=alert.target_value,
        current_price=alert.current_price,
        is_active=alert.is_active,
        is_triggered=alert.is_triggered,
        triggered_at=alert.triggered_at,
        notification_sent=alert.notification_sent,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        stock_name=stock.name,
    )


@router.put("/{alert_id}", response_model=PriceAlertResponse)
async def update_alert(
    alert_id: str,
    alert_data: PriceAlertUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新价格预警"""
    alert = (
        db.query(PriceAlert)
        .filter(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == current_user.id,
        )
        .first()
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警不存在",
        )

    # 更新字段
    if alert_data.target_value is not None:
        alert.target_value = alert_data.target_value
        # 重置触发状态
        alert.is_triggered = False
        alert.triggered_at = None

    if alert_data.is_active is not None:
        alert.is_active = alert_data.is_active

    db.commit()
    db.refresh(alert)

    stock = db.query(Stock).filter(Stock.symbol == alert.symbol).first()

    return PriceAlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        symbol=alert.symbol,
        alert_type=alert.alert_type,
        target_value=alert.target_value,
        current_price=alert.current_price,
        is_active=alert.is_active,
        is_triggered=alert.is_triggered,
        triggered_at=alert.triggered_at,
        notification_sent=alert.notification_sent,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        stock_name=stock.name if stock else None,
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """删除价格预警"""
    alert = (
        db.query(PriceAlert)
        .filter(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == current_user.id,
        )
        .first()
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警不存在",
        )

    db.delete(alert)
    db.commit()


# ==============================================
# 预警历史 API
# ==============================================

@router.get("/history", response_model=AlertHistoryListResponse)
async def get_history(
    symbol: Optional[str] = Query(None, description="股票代码"),
    acknowledged: Optional[bool] = Query(None, description="是否已确认"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取预警历史记录"""
    query = db.query(AlertHistory).filter(AlertHistory.user_id == current_user.id)

    if symbol:
        query = query.filter(AlertHistory.symbol == symbol)

    if acknowledged is not None:
        query = query.filter(AlertHistory.acknowledged == acknowledged)

    history = query.order_by(desc(AlertHistory.triggered_at)).limit(limit).all()

    # 获取股票信息
    result = []
    for record in history:
        stock = db.query(Stock).filter(Stock.symbol == record.symbol).first()
        record_dict = {
            "id": record.id,
            "user_id": record.user_id,
            "alert_id": record.alert_id,
            "symbol": record.symbol,
            "alert_type": record.alert_type,
            "target_value": record.target_value,
            "actual_value": record.actual_value,
            "triggered_at": record.triggered_at,
            "acknowledged": record.acknowledged,
            "acknowledged_at": record.acknowledged_at,
            "stock_name": stock.name if stock else None,
        }
        result.append(AlertHistoryResponse(**record_dict))

    return AlertHistoryListResponse(total=len(result), items=result)


@router.post("/history/{history_id}/acknowledge", response_model=AlertHistoryResponse)
async def acknowledge_history(
    history_id: str,
    ack_data: AlertHistoryAcknowledge = AlertHistoryAcknowledge(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """确认预警历史记录"""
    record = (
        db.query(AlertHistory)
        .filter(
            AlertHistory.id == history_id,
            AlertHistory.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警历史记录不存在",
        )

    record.acknowledged = ack_data.acknowledged
    if ack_data.acknowledged:
        record.acknowledged_at = datetime.utcnow()
    else:
        record.acknowledged_at = None

    db.commit()
    db.refresh(record)

    stock = db.query(Stock).filter(Stock.symbol == record.symbol).first()

    return AlertHistoryResponse(
        id=record.id,
        user_id=record.user_id,
        alert_id=record.alert_id,
        symbol=record.symbol,
        alert_type=record.alert_type,
        target_value=record.target_value,
        actual_value=record.actual_value,
        triggered_at=record.triggered_at,
        acknowledged=record.acknowledged,
        acknowledged_at=record.acknowledged_at,
        stock_name=stock.name if stock else None,
    )


# ==============================================
# 预警设置 API
# ==============================================

@router.get("/settings", response_model=AlertSettings)
async def get_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取预警设置"""
    # 从用户偏好中获取预警设置
    preferences = current_user.preferences or {}
    alert_settings = preferences.get("alerts", {})

    return AlertSettings(
        sound_enabled=alert_settings.get("sound_enabled", True),
        browser_notification=alert_settings.get("browser_notification", True),
        email_notification=alert_settings.get("email_notification", False),
        quiet_hours_start=alert_settings.get("quiet_hours_start"),
        quiet_hours_end=alert_settings.get("quiet_hours_end"),
    )


@router.put("/settings", response_model=AlertSettings)
async def update_settings(
    settings_data: AlertSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新预警设置"""
    # 获取当前偏好
    preferences = current_user.preferences or {}
    alert_settings = preferences.get("alerts", {})

    # 更新设置
    if settings_data.sound_enabled is not None:
        alert_settings["sound_enabled"] = settings_data.sound_enabled
    if settings_data.browser_notification is not None:
        alert_settings["browser_notification"] = settings_data.browser_notification
    if settings_data.email_notification is not None:
        alert_settings["email_notification"] = settings_data.email_notification
    if settings_data.quiet_hours_start is not None:
        alert_settings["quiet_hours_start"] = settings_data.quiet_hours_start
    if settings_data.quiet_hours_end is not None:
        alert_settings["quiet_hours_end"] = settings_data.quiet_hours_end

    # 保存
    preferences["alerts"] = alert_settings
    current_user.preferences = preferences
    db.commit()

    return AlertSettings(**alert_settings)


# ==============================================
# 未读预警数量 API
# ==============================================

@router.post("/{alert_id}/trigger", status_code=status.HTTP_200_OK)
async def trigger_alert_manually(
    alert_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """手动触发预警（测试用)"""
    alert = (
        db.query(PriceAlert)
        .filter(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == current_user.id,
        )
        .first()
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警不存在"
        )

    # 这里只是标记为手动触发测试
    alert.is_triggered = True
    alert.triggered_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "预警已触发"}
