"""
基础 Repository 类

提供通用的 CRUD 操作，其他 Repository 继承此类。
"""

from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础 Repository 类"""

    def __init__(self, model: Type[ModelType]):
        """
        初始化 Repository

        Args:
            model: SQLAlchemy 模型类
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        根据 ID 获取单个记录

        Args:
            db: 数据库会话
            id: 记录 ID

        Returns:
            模型实例或 None
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """
        获取多个记录（分页）

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            filters: 过滤条件字典

        Returns:
            模型实例列表
        """
        query = db.query(self.model)

        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.offset(skip).limit(limit).all()

    def create(
        self,
        db: Session,
        *,
        obj_in: CreateSchemaType
    ) -> ModelType:
        """
        创建新记录

        Args:
            db: 数据库会话
            obj_in: 创建数据的 Pydantic 模型

        Returns:
            创建的模型实例
        """
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict
    ) -> ModelType:
        """
        更新记录

        Args:
            db: 数据库会话
            db_obj: 数据库中的模型实例
            obj_in: 更新数据的 Pydantic 模型或字典

        Returns:
            更新后的模型实例
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """
        删除记录

        Args:
            db: 数据库会话
            id: 记录 ID

        Returns:
            删除的模型实例或 None
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def count(self, db: Session, *, filters: Optional[dict] = None) -> int:
        """
        统计记录数

        Args:
            db: 数据库会话
            filters: 过滤条件字典

        Returns:
            记录数
        """
        query = db.query(self.model)

        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.count()
