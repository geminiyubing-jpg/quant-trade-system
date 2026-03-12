"""
==============================================
QuantAI Ecosystem - 风控管理端点
==============================================

提供风控规则管理和风险告警查询功能。
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

from src.core.database import get_db
from src.core.security import get_current_active_user, get_current_superuser
from src.models.user import User
from src.models.risk import SystemConfig
from src.services.risk import RiskControlEngine
from src.services.risk.models import (
    RiskCheckResult,
    RiskRuleConfig,
    RiskMetrics,
    RiskCheckType,
)
from src.repositories.backtest import SystemConfigRepository
import json


router = APIRouter()

# 初始化 Repository
system_config_repo = SystemConfigRepository(SystemConfig)


# ==============================================
# 风控检查端点
# ==============================================

@router.post("/check-order", response_model=List[RiskCheckResult])
async def check_order_risk(
    symbol: str = Query(..., description="股票代码"),
    side: str = Query(..., description="买卖方向（BUY/SELL）"),
    quantity: int = Query(..., gt=0, description="数量"),
    price: Decimal = Query(..., gt=0, description="价格"),
    execution_mode: str = Query("PAPER", description="执行模式"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db)
):
    """
    检查订单风险

    在创建订单之前，可以使用此端点预先检查订单是否符合风控规则。

    Args:
        symbol: 股票代码
        side: 买卖方向
        quantity: 数量
        price: 价格
        execution_mode: 执行模式
        current_user: 当前用户
        db: 数据库会话

    Returns:
        List[RiskCheckResult]: 所有风控检查结果
    """
    risk_engine = RiskControlEngine()

    check_results = risk_engine.validate_order(
        db=db,
        user_id=str(current_user.id),
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        execution_mode=execution_mode
    )

    return check_results


@router.get("/alerts", response_model=List[RiskCheckResult])
async def get_risk_alerts(
    execution_mode: str = Query("PAPER", description="执行模式"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取当前风险告警

    返回当前用户的所有未解决的风险告警。

    Args:
        execution_mode: 执行模式
        current_user: 当前用户
        db: 数据库会话

    Returns:
        List[RiskCheckResult]: 风险告警列表
    """
    risk_engine = RiskControlEngine()

    alerts = risk_engine.get_all_risk_alerts(
        db=db,
        user_id=str(current_user.id),
        execution_mode=execution_mode
    )

    return alerts


@router.get("/metrics", response_model=RiskMetrics)
async def get_risk_metrics(
    execution_mode: str = Query("PAPER", description="执行模式"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取风险指标

    返回当前用户的风险指标汇总。

    Args:
        execution_mode: 执行模式
        current_user: 当前用户
        db: 数据库会话

    Returns:
        RiskMetrics: 风险指标
    """
    risk_engine = RiskControlEngine()

    metrics = risk_engine._calculate_risk_metrics(
        db=db,
        user_id=str(current_user.id),
        execution_mode=execution_mode
    )

    return metrics


@router.get("/positions/{symbol}/check", response_model=List[RiskCheckResult])
async def check_position_risk(
    symbol: str,
    execution_mode: str = Query("PAPER", description="执行模式"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db)
):
    """
    检查持仓风险

    检查指定持仓的风险状态（如是否触发止损/止盈）。

    Args:
        symbol: 股票代码
        execution_mode: 执行模式
        current_user: 当前用户
        db: 数据库会话

    Returns:
        List[RiskCheckResult]: 风险检查结果
    """
    risk_engine = RiskControlEngine()

    check_results = risk_engine.check_position_risk(
        db=db,
        user_id=str(current_user.id),
        symbol=symbol,
        execution_mode=execution_mode
    )

    return check_results


# ==============================================
# 风控规则配置端点（仅超级用户）
# ==============================================

@router.get("/config", response_model=RiskRuleConfig)
async def get_risk_config(
    current_user: Annotated[User, Depends(get_current_superuser)] = None,
    db: Session = Depends(get_db)
):
    """
    获取风控规则配置

    返回当前系统的风控规则配置（仅超级用户）。
    从数据库读取配置，如果不存在则返回默认配置。

    Args:
        current_user: 当前超级用户
        db: 数据库会话

    Returns:
        RiskRuleConfig: 风控规则配置
    """
    try:
        # 从数据库读取配置
        config_dict = system_config_repo.get_all_dict(db)

        # 将配置字典转换为 RiskRuleConfig
        if config_dict:
            return RiskRuleConfig(**{
                key: float(value) if key.endswith(('_limit', '_threshold', 'rate')) else
                    int(value) if key.endswith('_trades') else
                    value
                for key, value in config_dict.items()
                if key in RiskRuleConfig.model_fields
            })
    except Exception:
        pass

    # 返回默认配置
    return RiskRuleConfig()


@router.put("/config", response_model=RiskRuleConfig)
async def update_risk_config(
    config: RiskRuleConfig,
    current_user: Annotated[User, Depends(get_current_superuser)] = None,
    db: Session = Depends(get_db)
):
    """
    更新风控规则配置

    更新系统的风控规则配置（仅超级用户）。
    配置会保存到数据库中。

    Args:
        config: 新的风控规则配置
        current_user: 当前超级用户
        db: 数据库会话

    Returns:
        RiskRuleConfig: 更新后的风控规则配置
    """
    try:
        # 保存配置到数据库
        config_dict = config.model_dump()

        for key, value in config_dict.items():
            # 确定值类型
            if isinstance(value, float):
                value_type = "number"
            elif isinstance(value, int):
                value_type = "number"
            elif isinstance(value, bool):
                value_type = "boolean"
            else:
                value_type = "string"

            # 使用 upsert 创建或更新配置
            system_config_repo.upsert(
                db,
                key=key,
                value=str(value),
                value_type=value_type,
                category="risk_control",
                description=f"风控配置: {key}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}"
        )

    return config


# ==============================================
# 风控检查端点
# ==============================================

@router.post("/rules/position-limit/check", response_model=RiskCheckResult)
async def check_position_limit(
    order_value: Decimal = Query(..., gt=0, description="订单金额"),
    total_account_value: Decimal = Query(..., gt=0, description="总账户价值"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """
    检查持仓限制

    单独检查订单是否超过持仓限制。

    Args:
        order_value: 订单金额
        total_account_value: 总账户价值
        current_user: 当前用户

    Returns:
        RiskCheckResult: 检查结果
    """
    from src.services.risk.checks import PositionLimitChecker

    config = RiskRuleConfig()
    checker = PositionLimitChecker(config)

    result = checker.check(
        order_value=order_value,
        total_account_value=total_account_value
    )

    return result


@router.post("/rules/stop-loss/check", response_model=RiskCheckResult)
async def check_stop_loss(
    current_price: Decimal = Query(..., gt=0, description="当前价格"),
    entry_price: Decimal = Query(..., gt=0, description="成本价"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """
    检查止损

    单独检查是否触发止损。

    Args:
        current_price: 当前价格
        entry_price: 成本价
        current_user: 当前用户

    Returns:
        RiskCheckResult: 检查结果
    """
    from src.services.risk.checks import StopLossChecker

    config = RiskRuleConfig()
    checker = StopLossChecker(config)

    result = checker.check(
        current_price=current_price,
        entry_price=entry_price
    )

    return result


@router.post("/rules/take-profit/check", response_model=RiskCheckResult)
async def check_take_profit(
    current_price: Decimal = Query(..., gt=0, description="当前价格"),
    entry_price: Decimal = Query(..., gt=0, description="成本价"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """
    检查止盈

    单独检查是否触发止盈。

    Args:
        current_price: 当前价格
        entry_price: 成本价
        current_user: 当前用户

    Returns:
        RiskCheckResult: 检查结果
    """
    from src.services.risk.checks import TakeProfitChecker

    config = RiskRuleConfig()
    checker = TakeProfitChecker(config)

    result = checker.check(
        current_price=current_price,
        entry_price=entry_price
    )

    return result


# ==============================================
# 风控规则列表端点
# ==============================================

@router.get("/rules")
async def get_risk_rules(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db)
):
    """
    获取风控规则列表

    返回系统所有风控规则的列表。

    Args:
        limit: 返回数量限制
        current_user: 当前用户
        db: 数据库会话

    Returns:
        List[Dict]: 风控规则列表
    """
    # 定义默认风控规则
    default_rules = [
        {
            "id": "position_limit",
            "name": "持仓限制",
            "description": "限制单只股票的最大持仓比例",
            "type": "position",
            "enabled": True,
            "threshold": 0.3,
            "severity": "warning",
            "action": "reject",
        },
        {
            "id": "daily_loss_limit",
            "name": "单日亏损限制",
            "description": "限制单日最大亏损比例",
            "type": "loss",
            "enabled": True,
            "threshold": 0.05,
            "severity": "critical",
            "action": "halt_trading",
        },
        {
            "id": "stop_loss",
            "name": "止损规则",
            "description": "自动止损，当亏损达到阈值时触发",
            "type": "loss",
            "enabled": True,
            "threshold": 0.05,
            "severity": "error",
            "action": "auto_sell",
        },
        {
            "id": "take_profit",
            "name": "止盈规则",
            "description": "自动止盈，当盈利达到阈值时触发",
            "type": "profit",
            "enabled": True,
            "threshold": 0.10,
            "severity": "info",
            "action": "auto_sell",
        },
        {
            "id": "max_order_size",
            "name": "最大订单限制",
            "description": "限制单笔订单的最大数量",
            "type": "order",
            "enabled": True,
            "threshold": 10000,
            "severity": "warning",
            "action": "reject",
        },
        {
            "id": "concentration",
            "name": "持仓集中度",
            "description": "限制单一股票占总资产的最大比例",
            "type": "position",
            "enabled": True,
            "threshold": 0.5,
            "severity": "warning",
            "action": "reject",
        },
    ]

    # 尝试从数据库获取配置覆盖默认值
    try:
        config_dict = system_config_repo.get_all_dict(db)

        # 更新规则的阈值
        if config_dict:
            rule_map = {rule["id"]: rule for rule in default_rules}

            if "max_position_ratio" in config_dict:
                rule_map["position_limit"]["threshold"] = float(config_dict["max_position_ratio"])
            if "max_daily_loss_ratio" in config_dict:
                rule_map["daily_loss_limit"]["threshold"] = float(config_dict["max_daily_loss_ratio"])
            if "stop_loss_ratio" in config_dict and config_dict.get("stop_loss_ratio"):
                rule_map["stop_loss"]["threshold"] = float(config_dict["stop_loss_ratio"])
            if "take_profit_ratio" in config_dict and config_dict.get("take_profit_ratio"):
                rule_map["take_profit"]["threshold"] = float(config_dict["take_profit_ratio"])
            if "max_order_size" in config_dict and config_dict.get("max_order_size"):
                rule_map["max_order_size"]["threshold"] = int(config_dict["max_order_size"])
            if "max_concentration_ratio" in config_dict:
                rule_map["concentration"]["threshold"] = float(config_dict["max_concentration_ratio"])
    except Exception:
        pass

    return default_rules[:limit]


# ==============================================
# 风控规则 CRUD 端点
# ==============================================

from pydantic import BaseModel, Field
from typing import Any, Optional


class RiskRuleCreate(BaseModel):
    """创建/更新风控规则的请求模型"""
    id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    type: str = Field(..., description="规则类型")
    enabled: bool = Field(True, description="是否启用")
    threshold: Any = Field(..., description="阈值")
    severity: str = Field("warning", description="严重程度")
    action: str = Field("reject", description="触发动作")


class RiskRuleUpdate(BaseModel):
    """更新风控规则的请求模型"""
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    enabled: Optional[bool] = Field(None, description="是否启用")
    threshold: Optional[Any] = Field(None, description="阈值")
    severity: Optional[str] = Field(None, description="严重程度")
    action: Optional[str] = Field(None, description="触发动作")


@router.post("/rules")
async def create_risk_rule(
    rule: RiskRuleCreate,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db)
):
    """
    创建或更新风控规则

    创建新的风控规则或更新现有规则。

    Args:
        rule: 规则数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        Dict: 创建/更新的规则
    """
    # 规则ID到配置键的映射
    rule_config_mapping = {
        "position_limit": "max_position_ratio",
        "daily_loss_limit": "max_daily_loss_ratio",
        "stop_loss": "stop_loss_ratio",
        "take_profit": "take_profit_ratio",
        "max_order_size": "max_order_size",
        "concentration": "max_concentration_ratio",
    }

    try:
        config_key = rule_config_mapping.get(rule.id)
        if config_key:
            # 保存到数据库
            value_type = "number"
            if isinstance(rule.threshold, float):
                value = str(rule.threshold)
            elif isinstance(rule.threshold, int):
                value = str(rule.threshold)
            else:
                value = str(rule.threshold)
                value_type = "string"

            system_config_repo.upsert(
                db,
                key=config_key,
                value=value,
                value_type=value_type,
                category="risk_control",
                description=rule.description or f"风控配置: {rule.name}"
            )

        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "type": rule.type,
            "enabled": rule.enabled,
            "threshold": rule.threshold,
            "severity": rule.severity,
            "action": rule.action,
            "message": "规则保存成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存规则失败: {str(e)}"
        )


@router.put("/rules/{rule_id}")
async def update_risk_rule(
    rule_id: str,
    rule: RiskRuleUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db)
):
    """
    更新风控规则

    更新指定ID的风控规则。

    Args:
        rule_id: 规则ID
        rule: 更新数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        Dict: 更新后的规则
    """
    # 规则ID到配置键的映射
    rule_config_mapping = {
        "position_limit": "max_position_ratio",
        "daily_loss_limit": "max_daily_loss_ratio",
        "stop_loss": "stop_loss_ratio",
        "take_profit": "take_profit_ratio",
        "max_order_size": "max_order_size",
        "concentration": "max_concentration_ratio",
    }

    try:
        config_key = rule_config_mapping.get(rule_id)
        if config_key and rule.threshold is not None:
            # 更新数据库
            value_type = "number"
            if isinstance(rule.threshold, float):
                value = str(rule.threshold)
            elif isinstance(rule.threshold, int):
                value = str(rule.threshold)
            else:
                value = str(rule.threshold)
                value_type = "string"

            system_config_repo.upsert(
                db,
                key=config_key,
                value=value,
                value_type=value_type,
                category="risk_control",
                description=f"风控配置: {rule_id}"
            )

        return {
            "id": rule_id,
            "message": "规则更新成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新规则失败: {str(e)}"
        )


@router.delete("/rules/{rule_id}")
async def delete_risk_rule(
    rule_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Session = Depends(get_db)
):
    """
    删除风控规则（重置为默认值）

    将指定规则重置为默认值。

    Args:
        rule_id: 规则ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        Dict: 删除结果
    """
    # 规则ID到配置键的映射
    rule_config_mapping = {
        "position_limit": "max_position_ratio",
        "daily_loss_limit": "max_daily_loss_ratio",
        "stop_loss": "stop_loss_ratio",
        "take_profit": "take_profit_ratio",
        "max_order_size": "max_order_size",
        "concentration": "max_concentration_ratio",
    }

    try:
        config_key = rule_config_mapping.get(rule_id)
        if config_key:
            # 删除数据库中的配置（重置为默认值）
            db.execute(
                text(f"DELETE FROM system_config WHERE key = :key"),
                {"key": config_key}
            )
            db.commit()

        return {
            "id": rule_id,
            "message": "规则已重置为默认值"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除规则失败: {str(e)}"
        )
