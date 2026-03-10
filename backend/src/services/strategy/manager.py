"""
策略管理服务

提供策略版本控制、配置管理和审计日志功能。
"""

import hashlib
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ...models import (
    Strategy, StrategyVersion, StrategyConfig, StrategyAuditLog,
    ChangeType, ActionType
)
from ...models.strategy_version import change_type_enum, action_type_enum


class StrategyManager:
    """策略管理器 - 处理策略版本控制和配置管理"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 版本管理 ====================

    def create_version(
        self,
        strategy_id: str,
        code: str,
        parameters: Dict[str, Any],
        change_log: str,
        change_type: ChangeType = ChangeType.PATCH,
        created_by: Optional[str] = None
    ) -> StrategyVersion:
        """
        创建新版本

        Args:
            strategy_id: 策略ID
            code: 策略代码
            parameters: 策略参数
            change_log: 变更日志
            change_type: 变更类型
            created_by: 创建者ID

        Returns:
            StrategyVersion: 新创建的版本
        """
        # 获取下一个版本号
        version_number = self._get_next_version(strategy_id, change_type)

        # 计算代码哈希
        code_hash = self._calculate_code_hash(code)

        # 创建版本
        version = StrategyVersion(
            strategy_id=strategy_id,
            version_number=version_number,
            version_code_hash=code_hash,
            code=code,
            parameters=parameters,
            change_log=change_log,
            change_type=change_type.value,
            is_active=False,
            created_by=created_by
        )

        self.db.add(version)

        # 记录审计日志
        self._log_action(
            strategy_id=strategy_id,
            action_type=ActionType.VERSION_PUBLISH,
            action_description=f"发布版本 {version_number}",
            new_value={
                'version_number': version_number,
                'change_type': change_type.value,
                'change_log': change_log
            },
            user_id=created_by
        )

        self.db.commit()
        self.db.refresh(version)

        return version

    def get_versions(self, strategy_id: str) -> List[StrategyVersion]:
        """获取策略所有版本"""
        return self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id
        ).order_by(desc(StrategyVersion.created_at)).all()

    def get_version(self, version_id: str) -> Optional[StrategyVersion]:
        """获取指定版本"""
        return self.db.query(StrategyVersion).filter(
            StrategyVersion.id == version_id
        ).first()

    def get_active_version(self, strategy_id: str) -> Optional[StrategyVersion]:
        """获取当前激活版本"""
        return self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id,
            StrategyVersion.is_active == True
        ).first()

    def activate_version(self, version_id: str, user_id: Optional[str] = None) -> bool:
        """
        激活指定版本

        Args:
            version_id: 版本ID
            user_id: 操作用户ID

        Returns:
            bool: 是否成功
        """
        version = self.get_version(version_id)
        if not version:
            return False

        # 停用当前激活版本
        self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == version.strategy_id,
            StrategyVersion.is_active == True
        ).update({'is_active': False})

        # 激活新版本
        version.is_active = True

        # 记录审计日志
        self._log_action(
            strategy_id=str(version.strategy_id),
            action_type=ActionType.VERSION_PUBLISH,
            action_description=f"激活版本 {version.version_number}",
            new_value={'version_id': str(version_id), 'version_number': version.version_number},
            user_id=user_id
        )

        self.db.commit()
        return True

    def rollback_version(
        self,
        strategy_id: str,
        version_number: str,
        user_id: Optional[str] = None
    ) -> Optional[StrategyVersion]:
        """
        回滚到指定版本

        Args:
            strategy_id: 策略ID
            version_number: 目标版本号
            user_id: 操作用户ID

        Returns:
            StrategyVersion: 回滚后的版本
        """
        target_version = self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id,
            StrategyVersion.version_number == version_number
        ).first()

        if not target_version:
            return None

        # 激活目标版本
        self.activate_version(str(target_version.id), user_id)

        # 记录审计日志
        self._log_action(
            strategy_id=strategy_id,
            action_type=ActionType.VERSION_ROLLBACK,
            action_description=f"回滚到版本 {version_number}",
            new_value={'version_number': version_number},
            user_id=user_id
        )

        return target_version

    def compare_versions(
        self,
        strategy_id: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        比较两个版本

        Args:
            strategy_id: 策略ID
            version1: 版本号1
            version2: 版本号2

        Returns:
            Dict: 比较结果
        """
        v1 = self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id,
            StrategyVersion.version_number == version1
        ).first()

        v2 = self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id,
            StrategyVersion.version_number == version2
        ).first()

        if not v1 or not v2:
            return {'error': '版本不存在'}

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
            'params_changed': v1.parameters != v2.parameters
        }

    # ==================== 配置管理 ====================

    def get_config(self, strategy_id: str) -> Optional[StrategyConfig]:
        """获取策略配置"""
        return self.db.query(StrategyConfig).filter(
            StrategyConfig.strategy_id == strategy_id,
            StrategyConfig.is_active == True
        ).first()

    def update_config(
        self,
        strategy_id: str,
        config_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[StrategyConfig]:
        """
        更新策略配置

        Args:
            strategy_id: 策略ID
            config_data: 配置数据
            user_id: 操作用户ID

        Returns:
            StrategyConfig: 更新后的配置
        """
        config = self.get_config(strategy_id)

        if not config:
            # 创建新配置
            config = StrategyConfig(
                strategy_id=strategy_id,
                user_id=user_id,
                **config_data
            )
            self.db.add(config)
        else:
            # 更新配置
            old_config = config.to_dict()
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            # 记录审计日志
            self._log_action(
                strategy_id=strategy_id,
                action_type=ActionType.PARAM_CHANGE,
                action_description="更新策略配置",
                old_value=old_config,
                new_value=config_data,
                user_id=user_id
            )

        self.db.commit()
        self.db.refresh(config)
        return config

    def create_default_config(
        self,
        strategy_id: str,
        user_id: str
    ) -> StrategyConfig:
        """创建默认配置"""
        config = StrategyConfig(
            strategy_id=strategy_id,
            user_id=user_id,
            symbols=[],
            allocation_ratio=Decimal("1.0"),
            max_position_count=10,
            max_single_position_ratio=Decimal("0.2"),
            max_drawdown_limit=Decimal("0.2"),
            daily_loss_limit=Decimal("0.05"),
            execution_mode='PAPER'
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    # ==================== 审计日志 ====================

    def get_audit_log(
        self,
        strategy_id: str,
        action_type: Optional[ActionType] = None,
        limit: int = 100
    ) -> List[StrategyAuditLog]:
        """
        获取审计日志

        Args:
            strategy_id: 策略ID
            action_type: 过滤动作类型
            limit: 限制数量

        Returns:
            List[StrategyAuditLog]: 审计日志列表
        """
        query = self.db.query(StrategyAuditLog).filter(
            StrategyAuditLog.strategy_id == strategy_id
        )

        if action_type:
            query = query.filter(StrategyAuditLog.action_type == action_type.value)

        return query.order_by(desc(StrategyAuditLog.created_at)).limit(limit).all()

    def _log_action(
        self,
        strategy_id: str,
        action_type: ActionType,
        action_description: str,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> StrategyAuditLog:
        """记录审计日志"""
        log = StrategyAuditLog(
            strategy_id=strategy_id,
            user_id=user_id,
            action_type=action_type.value,
            action_description=action_description,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
        self.db.add(log)
        return log

    # ==================== 辅助方法 ====================

    def _get_next_version(self, strategy_id: str, change_type: ChangeType) -> str:
        """获取下一个版本号"""
        latest_version = self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id
        ).order_by(desc(StrategyVersion.created_at)).first()

        if not latest_version:
            return "1.0.0"

        try:
            major, minor, patch = map(int, latest_version.version_number.split('.'))
        except ValueError:
            return "1.0.0"

        if change_type == ChangeType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif change_type == ChangeType.MINOR:
            minor += 1
            patch = 0
        else:  # PATCH
            patch += 1

        return f"{major}.{minor}.{patch}"

    def _calculate_code_hash(self, code: str) -> str:
        """计算代码哈希"""
        return hashlib.sha256(code.encode()).hexdigest()

    def _extract_dependencies(self, code: str) -> List[str]:
        """提取代码依赖"""
        imports = re.findall(
            r'^import\s+(\w+)|^from\s+(\w+)\s+import',
            code, re.MULTILINE
        )
        return list(set([i[0] or i[1] for i in imports if i[0] or i[1]]))
