"""
自选股管理 API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models import User, WatchlistGroup, WatchlistItem, Stock
from src.schemas.watchlist import (
    WatchlistGroupCreate,
    WatchlistGroupUpdate,
    WatchlistGroupResponse,
    WatchlistGroupListResponse,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
    WatchlistItemWithQuote,
    WatchlistItemListResponse,
    WatchlistItemWithQuoteListResponse,
    BatchAddItemsRequest,
    BatchRemoveItemsRequest,
    BatchMoveItemsRequest,
    BatchOperationResponse,
)

router = APIRouter()


# ==============================================
# 自选股分组 API
# ==============================================

@router.get("/groups", response_model=WatchlistGroupListResponse)
async def get_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的所有自选股分组"""
    groups = (
        db.query(WatchlistGroup)
        .filter(WatchlistGroup.user_id == current_user.id)
        .order_by(WatchlistGroup.sort_order, WatchlistGroup.created_at)
        .all()
    )

    # 计算每个分组的股票数量
    items = []
    for group in groups:
        item_count = db.query(func.count(WatchlistItem.id)).filter(
            WatchlistItem.group_id == group.id
        ).scalar()

        group_dict = {
            "id": group.id,
            "user_id": group.user_id,
            "name": group.name,
            "sort_order": group.sort_order,
            "is_default": group.is_default,
            "item_count": item_count,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
        }
        items.append(WatchlistGroupResponse(**group_dict))

    return WatchlistGroupListResponse(total=len(items), items=items)


@router.post("/groups", response_model=WatchlistGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: WatchlistGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """创建新的自选股分组"""
    # 检查分组名称是否已存在
    existing = (
        db.query(WatchlistGroup)
        .filter(
            WatchlistGroup.user_id == current_user.id,
            WatchlistGroup.name == group_data.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"分组名称 '{group_data.name}' 已存在",
        )

    # 创建分组
    group = WatchlistGroup(
        user_id=current_user.id,
        name=group_data.name,
        sort_order=group_data.sort_order,
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    return WatchlistGroupResponse(
        id=group.id,
        user_id=group.user_id,
        name=group.name,
        sort_order=group.sort_order,
        is_default=group.is_default,
        item_count=0,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.put("/groups/{group_id}", response_model=WatchlistGroupResponse)
async def update_group(
    group_id: str,
    group_data: WatchlistGroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新自选股分组"""
    group = (
        db.query(WatchlistGroup)
        .filter(
            WatchlistGroup.id == group_id,
            WatchlistGroup.user_id == current_user.id,
        )
        .first()
    )
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在",
        )

    # 更新字段
    if group_data.name is not None:
        # 检查新名称是否已存在
        existing = (
            db.query(WatchlistGroup)
            .filter(
                WatchlistGroup.user_id == current_user.id,
                WatchlistGroup.name == group_data.name,
                WatchlistGroup.id != group_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"分组名称 '{group_data.name}' 已存在",
            )
        group.name = group_data.name

    if group_data.sort_order is not None:
        group.sort_order = group_data.sort_order

    db.commit()
    db.refresh(group)

    item_count = db.query(func.count(WatchlistItem.id)).filter(
        WatchlistItem.group_id == group.id
    ).scalar()

    return WatchlistGroupResponse(
        id=group.id,
        user_id=group.user_id,
        name=group.name,
        sort_order=group.sort_order,
        is_default=group.is_default,
        item_count=item_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """删除自选股分组（分组内的股票移动到未分组）"""
    group = (
        db.query(WatchlistGroup)
        .filter(
            WatchlistGroup.id == group_id,
            WatchlistGroup.user_id == current_user.id,
        )
        .first()
    )
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在",
        )

    # 将分组内的股票移动到未分组（设置 group_id 为 None）
    db.query(WatchlistItem).filter(
        WatchlistItem.group_id == group_id
    ).update({"group_id": None})

    # 删除分组
    db.delete(group)
    db.commit()


# ==============================================
# 自选股项目 API
# ==============================================

@router.get("/items", response_model=WatchlistItemListResponse)
async def get_items(
    group_id: Optional[str] = Query(None, description="分组 ID，不传则获取所有"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的自选股列表"""
    query = db.query(WatchlistItem).filter(WatchlistItem.user_id == current_user.id)

    if group_id:
        query = query.filter(WatchlistItem.group_id == group_id)

    items = query.order_by(WatchlistItem.sort_order, WatchlistItem.created_at).all()

    # 获取股票信息
    result = []
    for item in items:
        stock = db.query(Stock).filter(Stock.symbol == item.symbol).first()
        item_dict = {
            "id": item.id,
            "user_id": item.user_id,
            "group_id": item.group_id,
            "symbol": item.symbol,
            "sort_order": item.sort_order,
            "notes": item.notes,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "stock_name": stock.name if stock else None,
            "stock_market": stock.market if stock else None,
        }
        result.append(WatchlistItemResponse(**item_dict))

    return WatchlistItemListResponse(total=len(result), items=result)


@router.post("/items", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    item_data: WatchlistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """添加股票到自选股"""
    # 检查股票是否存在
    stock = db.query(Stock).filter(Stock.symbol == item_data.symbol).first()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"股票 {item_data.symbol} 不存在",
        )

    # 检查是否已在自选中
    existing = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol == item_data.symbol,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"股票 {item_data.symbol} 已在自选中",
        )

    # 检查分组是否存在（如果指定了分组）
    if item_data.group_id:
        group = (
            db.query(WatchlistGroup)
            .filter(
                WatchlistGroup.id == item_data.group_id,
                WatchlistGroup.user_id == current_user.id,
            )
            .first()
        )
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分组不存在",
            )

    # 添加自选股
    item = WatchlistItem(
        user_id=current_user.id,
        group_id=item_data.group_id,
        symbol=item_data.symbol,
        notes=item_data.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return WatchlistItemResponse(
        id=item.id,
        user_id=item.user_id,
        group_id=item.group_id,
        symbol=item.symbol,
        sort_order=item.sort_order,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
        stock_name=stock.name,
        stock_market=stock.market,
    )


@router.put("/items/{symbol}", response_model=WatchlistItemResponse)
async def update_item(
    symbol: str,
    item_data: WatchlistItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新自选股项目"""
    item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol == symbol,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"股票 {symbol} 不在自选中",
        )

    # 更新字段
    if item_data.group_id is not None:
        # 检查分组是否存在
        if item_data.group_id:
            group = (
                db.query(WatchlistGroup)
                .filter(
                    WatchlistGroup.id == item_data.group_id,
                    WatchlistGroup.user_id == current_user.id,
                )
                .first()
            )
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="分组不存在",
                )
        item.group_id = item_data.group_id

    if item_data.notes is not None:
        item.notes = item_data.notes

    if item_data.sort_order is not None:
        item.sort_order = item_data.sort_order

    db.commit()
    db.refresh(item)

    stock = db.query(Stock).filter(Stock.symbol == item.symbol).first()

    return WatchlistItemResponse(
        id=item.id,
        user_id=item.user_id,
        group_id=item.group_id,
        symbol=item.symbol,
        sort_order=item.sort_order,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
        stock_name=stock.name if stock else None,
        stock_market=stock.market if stock else None,
    )


@router.delete("/items/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """从自选股移除股票"""
    item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol == symbol,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"股票 {symbol} 不在自选中",
        )

    db.delete(item)
    db.commit()


# ==============================================
# 批量操作 API
# ==============================================

@router.post("/items/batch/add", response_model=BatchOperationResponse)
async def batch_add_items(
    data: BatchAddItemsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """批量添加自选股"""
    added = 0
    failed = []

    # 检查分组是否存在
    if data.group_id:
        group = (
            db.query(WatchlistGroup)
            .filter(
                WatchlistGroup.id == data.group_id,
                WatchlistGroup.user_id == current_user.id,
            )
            .first()
        )
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分组不存在",
            )

    for symbol in data.symbols:
        try:
            # 检查股票是否存在
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                failed.append(f"{symbol}: 股票不存在")
                continue

            # 检查是否已在自选中
            existing = (
                db.query(WatchlistItem)
                .filter(
                    WatchlistItem.user_id == current_user.id,
                    WatchlistItem.symbol == symbol,
                )
                .first()
            )
            if existing:
                failed.append(f"{symbol}: 已在自选中")
                continue

            # 添加
            item = WatchlistItem(
                user_id=current_user.id,
                group_id=data.group_id,
                symbol=symbol,
            )
            db.add(item)
            added += 1
        except Exception as e:
            failed.append(f"{symbol}: {str(e)}")

    db.commit()

    return BatchOperationResponse(
        success=True,
        added=added,
        failed=failed,
        message=f"成功添加 {added} 只股票" + (f"，{len(failed)} 只失败" if failed else ""),
    )


@router.post("/items/batch/remove", response_model=BatchOperationResponse)
async def batch_remove_items(
    data: BatchRemoveItemsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """批量移除自选股"""
    removed = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol.in_(data.symbols),
        )
        .delete(synchronize_session=False)
    )
    db.commit()

    return BatchOperationResponse(
        success=True,
        removed=removed,
        message=f"成功移除 {removed} 只股票",
    )


@router.post("/items/batch/move", response_model=BatchOperationResponse)
async def batch_move_items(
    data: BatchMoveItemsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """批量移动自选股到指定分组"""
    # 检查分组是否存在
    if data.group_id:
        group = (
            db.query(WatchlistGroup)
            .filter(
                WatchlistGroup.id == data.group_id,
                WatchlistGroup.user_id == current_user.id,
            )
            .first()
        )
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分组不存在",
            )

    updated = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == current_user.id,
            WatchlistItem.symbol.in_(data.symbols),
        )
        .update({"group_id": data.group_id}, synchronize_session=False)
    )
    db.commit()

    return BatchOperationResponse(
        success=True,
        added=updated,
        message=f"成功移动 {updated} 只股票",
    )
