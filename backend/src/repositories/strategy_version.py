"""
策略版本和配置数据访问层

提供策略版本、配置和审计日志的数据访问功能。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ..models import (
    StrategyVersion, StrategyConfig, StrategyAuditLog,
)

from ..models.strategy_version import ChangeType, ActionType

from .base import BaseRepository

from ...core.exceptions import NotFoundError

from ...core.logging import get_logger

from ...schemas.strategy import (
    StrategyVersionCreate, StrategyVersionUpdate,
    StrategyVersionResponse, StrategyConfigCreate, StrategyConfigUpdate,
    StrategyConfigResponse
)
from ...schemas.strategy_version import (
    StrategyAuditLogCreate, StrategyAuditLogUpdate,
    StrategyAuditLogResponse
)


logger = get_logger(__name__)


class StrategyVersionRepository(BaseRepository[StrategyVersion, StrategyVersion]):
    """策略版本数据访问"""

    def get_by_strategy(
        self,
        strategy_id: str,
        include_inactive: bool = False
    ) -> List[StrategyVersion]:
        """获取策略的所有版本"""
        versions = self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id
        ).order_by(desc(StrategyVersion.created_at)).all()

        if not include_inactive:
            versions = [v for v in versions if v.is_active]

        return versions

    def get_active_version(self, strategy_id: str) -> Optional[StrategyVersion]:
        """获取策略当前激活版本"""
        return self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id,
            StrategyVersion.is_active == True
        ).first()

    def get_version(self, version_id: str) -> Optional[StrategyVersion]:
        """获取指定版本"""
        return self.db.query(StrategyVersion).filter(
            StrategyVersion.id == version_id).first()

    def get_version_by_number(
        self,
        strategy_id: str,
        version_number: str
    ) -> Optional[StrategyVersion]:
        """通过版本号获取版本"""
        return self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id,
            StrategyVersion.version_number == version_number
        ).first()

    def create(self, version: StrategyVersion) -> StrategyVersion:
        """创建新版本"""
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def activate_version(self, version_id: str) -> bool:
        """激活指定版本"""
        # 获取目标版本
        target = self.get_version(version_id)
        if not target:
            return False

        # 先停用同一策略的其他版本
        self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == target.strategy_id,
            StrategyVersion.id != version_id,
            StrategyVersion.is_active == True
        ).update({"is_active": False})

        # 激活目标版本
        target.is_active = True
        self.db.commit()
        return True

    def compare_versions(
        self,
        strategy_id: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """比较两个版本"""
        v1 = self.get_version_by_number(strategy_id, version1)
        v2 = self.get_version_by_number(strategy_id, version2)

        if not v1 or not v2:
            return {'error': 'One or both versions not found'}

        return {
            'version1': {
                'number': v1.version_number,
                'code_hash': v1.version_code_hash,
                'change_log': v1.change_log,
                'created_at': v1.created_at.isoformat() if v1.created_at else None
            },
            'version2': {
                'number': v2.version_number,
                'code_hash': v2.version_code_hash,
                'change_log': v2.change_log,
                'created_at': v2.created_at.isoformat() if v2.created_at else None
            },
            'code_changed': v1.version_code_hash != v2.version_code_hash,
        }

    def delete_version(self, version_id: str) -> bool:
        """删除版本"""
        version = self.get_version(version_id)
        if not version:
            return False

        self.db.delete(version)
        self.db.commit()
        return True


class StrategyConfigRepository(BaseRepository[StrategyConfig, StrategyConfig]):
    """策略配置数据访问"""

    def get_by_strategy(
        self,
        strategy_id: str,
        include_inactive: bool = False
    ) -> Optional[StrategyConfig]:
        """获取策略配置"""
        query = self.db.query(StrategyConfig).filter(
            StrategyConfig.strategy_id == strategy_id
        )
        if not include_inactive:
            query = query.filter(StrategyConfig.is_active == True)

        configs = query.all()
        return configs[0] if configs else None

    def get_active_config(self, strategy_id: str) -> Optional[StrategyConfig]:
        """获取当前激活的配置"""
        return self.db.query(StrategyConfig).filter(
            StrategyConfig.strategy_id == strategy_id,
            StrategyConfig.is_active == True
        ).first()

    def create(self, config: StrategyConfig) -> StrategyConfig:
        """创建配置"""
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update(self, config: StrategyConfig) -> StrategyConfig:
        """更新配置"""
        self.db.merge(config)
        self.db.commit()
        return config

    def delete(self, config_id: str) -> bool:
        """删除配置"""
        config = self.get(config_id)
        if not config:
            return False
        self.db.delete(config)
        self.db.commit()
        return True
