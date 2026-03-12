"""
数据验证工具模块
提供统一的验证函数，减少重复代码
"""

import re
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def validate_required(value: Any, field_name: str) -> Any:
    """
    验证必填字段

    Args:
        value: 字段值
        field_name: 字段名称

    Returns:
        验证通过的值

    Raises:
        HTTPException: 400 Bad Request
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name}不能为空"
        )
    return value


def validate_positive(value: Any, field_name: str, allow_zero: bool = False) -> Any:
    """
    验证正数

    Args:
        value: 字段值
        field_name: 字段名称
        allow_zero: 是否允许零值

    Returns:
        验证通过的值

    Raises:
        HTTPException: 400 Bad Request
    """
    if value is None:
        return value

    try:
        num_value = Decimal(str(value))
        if allow_zero:
            if num_value < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field_name}不能为负数"
                )
        else:
            if num_value <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field_name}必须大于0"
                )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name}格式无效"
        )

    return value


def validate_stock_symbol(symbol: str) -> str:
    """
    验证股票代码格式

    Args:
        symbol: 股票代码

    Returns:
        验证通过的股票代码

    Raises:
        HTTPException: 400 Bad Request
    """
    if not symbol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="股票代码不能为空"
        )

    # A股格式: 6位数字 + .SH 或 .SZ
    pattern = r'^\d{6}\.(SH|SZ|sh|sz)$'
    if not re.match(pattern, symbol):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"股票代码格式无效: {symbol}，应为 XXXXXX.SH 或 XXXXXX.SZ"
        )

    return symbol.upper()


def validate_quantity(quantity: int, min_value: int = 1) -> int:
    """
    验证交易数量

    Args:
        quantity: 交易数量
        min_value: 最小值

    Returns:
        验证通过的数量

    Raises:
        HTTPException: 400 Bad Request
    """
    if quantity is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="交易数量不能为空"
        )

    if quantity < min_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"交易数量不能小于 {min_value}"
        )

    return quantity


def validate_price(price: Any, allow_zero: bool = False) -> Decimal:
    """
    验证价格

    Args:
        price: 价格
        allow_zero: 是否允许零值

    Returns:
        验证通过的价格（Decimal）

    Raises:
        HTTPException: 400 Bad Request
    """
    if price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="价格不能为空"
        )

    try:
        price_decimal = Decimal(str(price))
        if allow_zero:
            if price_decimal < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="价格不能为负数"
                )
        else:
            if price_decimal <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="价格必须大于0"
                )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="价格格式无效"
        )

    return price_decimal


def validate_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
    start_field: str = "开始日期",
    end_field: str = "结束日期"
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    验证日期范围

    Args:
        start_date: 开始日期字符串
        end_date: 结束日期字符串
        start_field: 开始日期字段名
        end_field: 结束日期字段名

    Returns:
        (start_datetime, end_datetime) 元组

    Raises:
        HTTPException: 400 Bad Request
    """
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{start_field}格式无效"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{end_field}格式无效"
            )

    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{start_field}不能晚于{end_field}"
        )

    return start_dt, end_dt


def validate_pagination(
    skip: Optional[int] = None,
    limit: Optional[int] = None,
    max_limit: int = 1000
) -> tuple[int, int]:
    """
    验证分页参数

    Args:
        skip: 跳过记录数
        limit: 返回记录数
        max_limit: 最大返回记录数

    Returns:
        (skip, limit) 元组
    """
    skip = max(0, skip or 0)
    limit = min(max(1, limit or 100), max_limit)
    return skip, limit


def validate_in_list(value: Any, valid_values: List[Any], field_name: str) -> Any:
    """
    验证值是否在有效列表中

    Args:
        value: 要验证的值
        valid_values: 有效值列表
        field_name: 字段名称

    Returns:
        验证通过的值

    Raises:
        HTTPException: 400 Bad Request
    """
    if value not in valid_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name}必须是以下值之一: {', '.join(map(str, valid_values))}"
        )
    return value


def validate_db_record(
    db: Session,
    model_class: Any,
    record_id: str,
    entity_name: str = "记录"
) -> Any:
    """
    验证数据库记录是否存在

    Args:
        db: 数据库会话
        model_class: 模型类
        record_id: 记录 ID
        entity_name: 实体名称

    Returns:
        数据库记录

    Raises:
        HTTPException: 404 Not Found
    """
    record = db.query(model_class).filter(model_class.id == record_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name}不存在: {record_id}"
        )

    return record
