"""
自选股相关的 Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# ==============================================
# 自选股分组 Schema
# ==============================================

class WatchlistGroupBase(BaseModel):
    """自选股分组基础 Schema"""
    name: str = Field(..., min_length=1, max_length=50, description="分组名称")
    sort_order: int = Field(0, ge=0, description="排序顺序")


class WatchlistGroupCreate(WatchlistGroupBase):
    """自选股分组创建 Schema"""
    pass


class WatchlistGroupUpdate(BaseModel):
    """自选股分组更新 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="分组名称")
    sort_order: Optional[int] = Field(None, ge=0, description="排序顺序")


class WatchlistGroupResponse(WatchlistGroupBase):
    """自选股分组响应 Schema"""
    id: UUID
    user_id: str
    is_default: bool = False
    item_count: int = 0  # 分组内股票数量
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistGroupListResponse(BaseModel):
    """自选股分组列表响应 Schema"""
    total: int = Field(..., description="总记录数")
    items: List[WatchlistGroupResponse] = Field(..., description="分组列表")


# ==============================================
# 自选股项目 Schema
# ==============================================

class WatchlistItemBase(BaseModel):
    """自选股项目基础 Schema"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class WatchlistItemCreate(WatchlistItemBase):
    """自选股项目创建 Schema"""
    group_id: Optional[UUID] = Field(None, description="分组 ID")


class WatchlistItemUpdate(BaseModel):
    """自选股项目更新 Schema"""
    group_id: Optional[UUID] = Field(None, description="分组 ID")
    notes: Optional[str] = Field(None, max_length=500, description="备注")
    sort_order: Optional[int] = Field(None, ge=0, description="排序顺序")


class WatchlistItemResponse(WatchlistItemBase):
    """自选股项目响应 Schema"""
    id: UUID
    user_id: str
    group_id: Optional[UUID]
    sort_order: int
    created_at: datetime
    updated_at: datetime
    # 股票信息（可选，从关联查询获取）
    stock_name: Optional[str] = None
    stock_market: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WatchlistItemWithQuote(WatchlistItemResponse):
    """自选股项目（带实时行情）响应 Schema"""
    # 实时行情数据
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None


class WatchlistItemListResponse(BaseModel):
    """自选股项目列表响应 Schema"""
    total: int = Field(..., description="总记录数")
    items: List[WatchlistItemResponse] = Field(..., description="自选股列表")


class WatchlistItemWithQuoteListResponse(BaseModel):
    """自选股项目（带实时行情）列表响应 Schema"""
    total: int = Field(..., description="总记录数")
    items: List[WatchlistItemWithQuote] = Field(..., description="自选股列表")


# ==============================================
# 批量操作 Schema
# ==============================================

class BatchAddItemsRequest(BaseModel):
    """批量添加自选股请求 Schema"""
    symbols: List[str] = Field(..., min_length=1, max_length=100, description="股票代码列表")
    group_id: Optional[UUID] = Field(None, description="分组 ID")


class BatchRemoveItemsRequest(BaseModel):
    """批量移除自选股请求 Schema"""
    symbols: List[str] = Field(..., min_length=1, max_length=100, description="股票代码列表")


class BatchMoveItemsRequest(BaseModel):
    """批量移动自选股请求 Schema"""
    symbols: List[str] = Field(..., min_length=1, max_length=100, description="股票代码列表")
    group_id: Optional[UUID] = Field(..., description="目标分组 ID")


class BatchOperationResponse(BaseModel):
    """批量操作响应 Schema"""
    success: bool = Field(..., description="是否成功")
    added: int = Field(0, description="添加数量")
    removed: int = Field(0, description="移除数量")
    failed: List[str] = Field(default_factory=list, description="失败的项目")
    message: str = Field("", description="消息")
