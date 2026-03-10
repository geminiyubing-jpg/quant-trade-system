"""
审计日志服务

记录系统关键操作，用于安全审计和问题追踪。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import json


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self):
        self.log_file = "logs/audit.log"
    
    def log_trading_mode_switch(
        self,
        db: Session,
        user_id: str,
        previous_mode: str,
        new_mode: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录交易模式切换操作
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            previous_mode: 切换前的模式
            new_mode: 切换后的模式
            ip_address: 客户端IP地址
            user_agent: 用户代理字符串
            metadata: 额外的元数据
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "TRADING_MODE_SWITCH",
            "user_id": user_id,
            "previous_mode": previous_mode,
            "new_mode": new_mode,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": metadata or {}
        }
        
        # 写入日志文件
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # 如果写入文件失败，至少打印到控制台
            print(f"Audit log failed: {e}")
    
    def log_permission_denied(
        self,
        db: Session,
        user_id: str,
        action: str,
        reason: str,
        ip_address: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录权限拒绝事件
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            action: 尝试的操作
            reason: 拒绝原因
            ip_address: 客户端IP地址
            metadata: 额外的元数据
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "PERMISSION_DENIED",
            "user_id": user_id,
            "action": action,
            "reason": reason,
            "ip_address": ip_address,
            "metadata": metadata or {}
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Audit log failed: {e}")
    
    def log_security_event(
        self,
        db: Session,
        event_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录安全事件
        
        Args:
            db: 数据库会话
            event_type: 事件类型
            severity: 严重程度（INFO, WARNING, ERROR, CRITICAL）
            message: 消息
            metadata: 额外的元数据
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "metadata": metadata or {}
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Audit log failed: {e}")


# 全局审计日志记录器实例
audit_logger = AuditLogger()
