"""
统一异常处理模块
提供简洁的 API 错误处理函数，减少重复代码
"""

from typing import Optional, Any
from fastapi import HTTPException, status


def not_found(entity: str, identifier: Any = None) -> None:
    """
    抛出 404 错误

    Args:
        entity: 实体名称（如 "用户"、"订单"）
        identifier: 实体标识符（可选）

    Raises:
        HTTPException: 404 Not Found
    """
    detail = f"{entity}不存在"
    if identifier is not None:
        detail = f"{entity}不存在: {identifier}"

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )


def bad_request(detail: str) -> None:
    """
    抛出 400 错误

    Args:
        detail: 错误详情

    Raises:
        HTTPException: 400 Bad Request
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )


def unauthorized(detail: str = "未授权访问") -> None:
    """
    抛出 401 错误

    Args:
        detail: 错误详情

    Raises:
        HTTPException: 401 Unauthorized
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden(detail: str = "权限不足") -> None:
    """
    抛出 403 错误

    Args:
        detail: 错误详情

    Raises:
        HTTPException: 403 Forbidden
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )


def conflict(detail: str) -> None:
    """
    抛出 409 冲突错误

    Args:
        detail: 错误详情

    Raises:
        HTTPException: 409 Conflict
    """
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )


def internal_error(operation: str, error: Exception = None) -> None:
    """
    抛出 500 内部服务器错误

    Args:
        operation: 操作名称
        error: 原始异常（可选）

    Raises:
        HTTPException: 500 Internal Server Error
    """
    detail = f"{operation}失败"
    if error:
        detail = f"{operation}失败: {str(error)}"

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )


def verify_exists(entity: Any, entity_name: str = "记录", identifier: Any = None) -> Any:
    """
    验证实体是否存在，不存在则抛出 404

    Args:
        entity: 要验证的实体
        entity_name: 实体名称
        identifier: 实体标识符（可选）

    Returns:
        原实体（如果存在）

    Raises:
        HTTPException: 404 Not Found
    """
    if entity is None:
        not_found(entity_name, identifier)
    return entity


def verify_ownership(user_id: str, owner_id: str, entity_name: str = "资源") -> None:
    """
    验证用户是否拥有资源的所有权

    Args:
        user_id: 当前用户 ID
        owner_id: 资源所有者 ID
        entity_name: 资源名称

    Raises:
        HTTPException: 403 Forbidden
    """
    if str(user_id) != str(owner_id):
        forbidden(f"无权访问此{entity_name}")


class APIException(Exception):
    """
    自定义 API 异常基类
    可用于全局异常处理器
    """

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "请求处理失败",
        **extra_data
    ):
        self.status_code = status_code
        self.detail = detail
        self.extra_data = extra_data
        super().__init__(detail)


class NotFoundError(APIException):
    """资源不存在异常"""

    def __init__(self, entity: str = "资源", identifier: Any = None):
        detail = f"{entity}不存在"
        if identifier is not None:
            detail = f"{entity}不存在: {identifier}"
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class BadRequestError(APIException):
    """错误请求异常"""

    def __init__(self, detail: str = "请求参数错误"):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class UnauthorizedError(APIException):
    """未授权异常"""

    def __init__(self, detail: str = "未授权访问"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


class ForbiddenError(APIException):
    """禁止访问异常"""

    def __init__(self, detail: str = "权限不足"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class ConflictError(APIException):
    """冲突异常"""

    def __init__(self, detail: str = "资源冲突"):
        super().__init__(status.HTTP_409_CONFLICT, detail)
