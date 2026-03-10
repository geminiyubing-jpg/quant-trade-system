"""
==============================================
公共响应格式化工具
==============================================
统一管理 API 响应格式
"""

from typing import Any, Optional, List, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    code: int = 200

    class Config:
        arbitrary_types_allowed = True


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""

    success: bool = True
    data: List[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    message: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200
) -> dict:
    """
    构造成功响应

    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码

    Returns:
        dict: 响应字典
    """
    return {
        "success": True,
        "data": data,
        "message": message,
        "code": code
    }


def error_response(
    message: str = "操作失败",
    code: int = 400,
    data: Any = None
) -> dict:
    """
    构造错误响应

    Args:
        message: 错误消息
        code: 错误码
        data: 附加数据

    Returns:
        dict: 响应字典
    """
    return {
        "success": False,
        "data": data,
        "message": message,
        "code": code
    }


def paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "查询成功"
) -> dict:
    """
    构造分页响应

    Args:
        data: 数据列表
        total: 总数
        page: 当前页码
        page_size: 每页数量
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "message": message
    }


def created_response(
    data: Any = None,
    message: str = "创建成功"
) -> dict:
    """
    构造创建成功响应

    Args:
        data: 创建的数据
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    return success_response(data=data, message=message, code=201)


def updated_response(
    data: Any = None,
    message: str = "更新成功"
) -> dict:
    """
    构造更新成功响应

    Args:
        data: 更新后的数据
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    return success_response(data=data, message=message, code=200)


def deleted_response(
    message: str = "删除成功"
) -> dict:
    """
    构造删除成功响应

    Args:
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    return success_response(data=None, message=message, code=200)


def not_found_response(
    message: str = "资源不存在"
) -> dict:
    """
    构造资源不存在响应

    Args:
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    return error_response(message=message, code=404)


def unauthorized_response(
    message: str = "未授权访问"
) -> dict:
    """
    构造未授权响应

    Args:
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    return error_response(message=message, code=401)


def forbidden_response(
    message: str = "禁止访问"
) -> dict:
    """
    构造禁止访问响应

    Args:
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    return error_response(message=message, code=403)


def validation_error_response(
    message: str = "数据验证失败",
    errors: Any = None
) -> dict:
    """
    构造数据验证失败响应

    Args:
        message: 响应消息
        errors: 验证错误详情

    Returns:
        dict: 响应字典
    """
    return error_response(message=message, code=422, data=errors)


def server_error_response(
    message: str = "服务器内部错误"
) -> dict:
    """
    构造服务器错误响应

    Args:
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    return error_response(message=message, code=500)
