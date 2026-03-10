"""
==============================================
QuantAI Ecosystem - 交易安全确认服务
==============================================

提供交易操作的二次确认机制，确保交易安全。
支持验证码验证、交易确认、风险评估等功能。
"""

import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class ConfirmationType(str, Enum):
    """确认类型"""
    ORDER_CREATE = "ORDER_CREATE"       # 创建订单
    ORDER_CANCEL = "ORDER_CANCEL"       # 取消订单
    POSITION_CLOSE = "POSITION_CLOSE"   # 平仓
    STRATEGY_START = "STRATEGY_START"   # 启动策略
    STRATEGY_STOP = "STRATEGY_STOP"     # 停止策略
    RISK_OVERRIDE = "RISK_OVERRIDE"     # 风控覆盖


class ConfirmationStatus(str, Enum):
    """确认状态"""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class ConfirmationRequest:
    """确认请求"""
    request_id: str
    confirmation_type: ConfirmationType
    user_id: str
    operation_data: Dict[str, Any]
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    require_2fa: bool = False
    require_sms: bool = False
    require_email: bool = False
    expires_at: datetime = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ConfirmationStatus = ConfirmationStatus.PENDING
    verified_at: Optional[datetime] = None
    verification_code: Optional[str] = None

    def __post_init__(self):
        if self.expires_at is None:
            # 默认5分钟过期
            self.expires_at = datetime.utcnow() + timedelta(minutes=5)


@dataclass
class TradeRiskAssessment:
    """交易风险评估"""
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors: list
    warnings: list
    require_confirmation: bool
    confirmation_methods: list
    estimated_impact: Dict[str, Any]


class TradeConfirmationService:
    """
    交易安全确认服务

    功能：
    - 交易风险评估
    - 确认请求管理
    - 验证码生成和验证
    - 多因素认证支持
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        # 内存存储（无 Redis 时使用）
        self._pending_requests: Dict[str, ConfirmationRequest] = {}
        self._verification_codes: Dict[str, Dict] = {}

        # 风险阈值配置
        self.risk_thresholds = {
            "order_value_low": 10000,       # 低风险订单金额
            "order_value_medium": 50000,    # 中风险订单金额
            "order_value_high": 200000,     # 高风险订单金额
            "daily_loss_limit": 50000,      # 日亏损限制
            "position_concentration": 0.3,   # 持仓集中度限制
        }

    def assess_trade_risk(
        self,
        user_id: str,
        operation_type: str,
        operation_data: Dict[str, Any],
        user_context: Optional[Dict] = None
    ) -> TradeRiskAssessment:
        """
        评估交易风险等级

        Args:
            user_id: 用户ID
            operation_type: 操作类型
            operation_data: 操作数据
            user_context: 用户上下文（持仓、资金等）

        Returns:
            TradeRiskAssessment: 风险评估结果
        """
        risk_factors = []
        warnings = []
        risk_score = 0

        # 1. 订单金额风险评估
        if operation_type in ["ORDER_CREATE", "ORDER_MODIFY"]:
            order_value = float(operation_data.get("estimated_value", 0))

            if order_value > self.risk_thresholds["order_value_high"]:
                risk_factors.append("订单金额超过高风险阈值")
                risk_score += 40
                warnings.append(f"订单金额 ¥{order_value:,.2f} 较大，请确认")
            elif order_value > self.risk_thresholds["order_value_medium"]:
                risk_factors.append("订单金额超过中风险阈值")
                risk_score += 20
            elif order_value > self.risk_thresholds["order_value_low"]:
                risk_factors.append("订单金额超过低风险阈值")
                risk_score += 10

        # 2. 持仓集中度风险
        if user_context and "positions" in user_context:
            total_value = user_context.get("total_value", 0)
            symbol = operation_data.get("symbol", "")
            position_value = sum(
                p.get("value", 0) for p in user_context["positions"]
                if p.get("symbol") == symbol
            )

            if total_value > 0:
                concentration = position_value / total_value
                if concentration > self.risk_thresholds["position_concentration"]:
                    risk_factors.append(f"持仓集中度过高: {concentration:.1%}")
                    risk_score += 25
                    warnings.append("该股票持仓已较集中，请注意风险分散")

        # 3. 策略操作风险
        if operation_type in ["STRATEGY_START", "STRATEGY_STOP"]:
            risk_factors.append("策略状态变更")
            risk_score += 15

            if operation_type == "STRATEGY_STOP":
                warnings.append("停止策略将暂停所有自动交易")

        # 4. 风控覆盖风险
        if operation_type == "RISK_OVERRIDE":
            risk_factors.append("风控规则覆盖")
            risk_score += 50
            warnings.append("覆盖风控规则可能导致更大风险暴露")

        # 5. 市场状态检查
        if operation_data.get("market_volatility", 0) > 0.03:
            risk_factors.append("市场波动较大")
            risk_score += 15
            warnings.append("当前市场波动较大，请谨慎操作")

        # 确定风险等级
        if risk_score >= 70:
            risk_level = "CRITICAL"
            require_confirmation = True
            confirmation_methods = ["2fa", "sms", "email"]
        elif risk_score >= 50:
            risk_level = "HIGH"
            require_confirmation = True
            confirmation_methods = ["2fa", "sms"]
        elif risk_score >= 30:
            risk_level = "MEDIUM"
            require_confirmation = True
            confirmation_methods = ["password"]
        else:
            risk_level = "LOW"
            require_confirmation = False
            confirmation_methods = []

        # 计算预估影响
        estimated_impact = {
            "risk_score": risk_score,
            "potential_loss": operation_data.get("estimated_value", 0) * 0.1,  # 假设10%潜在损失
            "position_change": operation_data.get("quantity", 0),
        }

        return TradeRiskAssessment(
            risk_level=risk_level,
            risk_factors=risk_factors,
            warnings=warnings,
            require_confirmation=require_confirmation,
            confirmation_methods=confirmation_methods,
            estimated_impact=estimated_impact
        )

    def create_confirmation_request(
        self,
        user_id: str,
        confirmation_type: ConfirmationType,
        operation_data: Dict[str, Any],
        risk_assessment: Optional[TradeRiskAssessment] = None
    ) -> ConfirmationRequest:
        """
        创建确认请求

        Args:
            user_id: 用户ID
            confirmation_type: 确认类型
            operation_data: 操作数据
            risk_assessment: 风险评估结果

        Returns:
            ConfirmationRequest: 确认请求
        """
        request_id = f"confirm_{secrets.token_hex(8)}"

        # 根据风险等级确定确认方式
        require_2fa = False
        require_sms = False
        require_email = False

        if risk_assessment:
            methods = risk_assessment.confirmation_methods
            require_2fa = "2fa" in methods
            require_sms = "sms" in methods
            require_email = "email" in methods

        request = ConfirmationRequest(
            request_id=request_id,
            confirmation_type=confirmation_type,
            user_id=user_id,
            operation_data=operation_data,
            risk_level=risk_assessment.risk_level if risk_assessment else "MEDIUM",
            require_2fa=require_2fa,
            require_sms=require_sms,
            require_email=require_email,
        )

        # 生成验证码（如果需要）
        if require_sms or require_email:
            code = self._generate_verification_code()
            request.verification_code = code
            self._store_verification_code(request_id, code, request.expires_at)

        # 存储请求
        self._store_request(request)

        logger.info(
            f"创建确认请求: {request_id}, 类型: {confirmation_type}, "
            f"风险等级: {request.risk_level}, 用户: {user_id}"
        )

        return request

    def verify_confirmation(
        self,
        request_id: str,
        user_id: str,
        verification_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        验证确认请求

        Args:
            request_id: 请求ID
            user_id: 用户ID
            verification_data: 验证数据（密码、验证码等）

        Returns:
            Tuple[bool, str]: (是否验证成功, 消息)
        """
        request = self._get_request(request_id)

        if not request:
            return False, "确认请求不存在"

        if request.user_id != user_id:
            return False, "无权验证此请求"

        if request.status != ConfirmationStatus.PENDING:
            return False, f"请求状态无效: {request.status}"

        if datetime.utcnow() > request.expires_at:
            request.status = ConfirmationStatus.EXPIRED
            self._store_request(request)
            return False, "确认请求已过期，请重新发起"

        # 验证密码
        if "password" in verification_data:
            # 这里应该调用用户服务验证密码
            # 简化实现，实际应该验证密码哈希
            password_valid = verification_data.get("password_valid", False)
            if not password_valid:
                return False, "密码验证失败"

        # 验证短信/邮箱验证码
        if request.require_sms or request.require_email:
            code = verification_data.get("verification_code")
            if not code:
                return False, "请输入验证码"

            if not self._verify_code(request_id, code):
                return False, "验证码错误或已过期"

        # 验证 2FA
        if request.require_2fa:
            totp_code = verification_data.get("totp_code")
            if not totp_code:
                return False, "请输入双因素认证码"
            # 这里应该验证 TOTP 码
            # 简化实现

        # 验证成功
        request.status = ConfirmationStatus.CONFIRMED
        request.verified_at = datetime.utcnow()
        self._store_request(request)

        logger.info(f"确认请求验证成功: {request_id}, 用户: {user_id}")

        return True, "验证成功"

    def reject_confirmation(
        self,
        request_id: str,
        user_id: str,
        reason: str = ""
    ) -> bool:
        """拒绝确认请求"""
        request = self._get_request(request_id)

        if not request or request.user_id != user_id:
            return False

        request.status = ConfirmationStatus.REJECTED
        self._store_request(request)

        logger.info(f"确认请求已拒绝: {request_id}, 原因: {reason}")
        return True

    def get_pending_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """获取待确认请求"""
        return self._get_request(request_id)

    def _generate_verification_code(self, length: int = 6) -> str:
        """生成验证码"""
        return ''.join(secrets.choice('0123456789') for _ in range(length))

    def _store_verification_code(self, request_id: str, code: str, expires_at: datetime):
        """存储验证码"""
        if self.redis:
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            self.redis.setex(
                f"verification_code:{request_id}",
                ttl,
                hashlib.sha256(code.encode()).hexdigest()
            )
        else:
            self._verification_codes[request_id] = {
                "code_hash": hashlib.sha256(code.encode()).hexdigest(),
                "expires_at": expires_at
            }

    def _verify_code(self, request_id: str, code: str) -> bool:
        """验证验证码"""
        if self.redis:
            stored_hash = self.redis.get(f"verification_code:{request_id}")
            if not stored_hash:
                return False
            return stored_hash.decode() == hashlib.sha256(code.encode()).hexdigest()
        else:
            stored = self._verification_codes.get(request_id)
            if not stored:
                return False
            if datetime.utcnow() > stored["expires_at"]:
                del self._verification_codes[request_id]
                return False
            return stored["code_hash"] == hashlib.sha256(code.encode()).hexdigest()

    def _store_request(self, request: ConfirmationRequest):
        """存储确认请求"""
        if self.redis:
            ttl = int((request.expires_at - datetime.utcnow()).total_seconds())
            self.redis.setex(
                f"confirmation_request:{request.request_id}",
                ttl,
                str(request.__dict__)
            )
        else:
            self._pending_requests[request.request_id] = request

    def _get_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """获取确认请求"""
        if self.redis:
            data = self.redis.get(f"confirmation_request:{request_id}")
            if data:
                # 简化实现，实际应该反序列化
                return self._pending_requests.get(request_id)
        return self._pending_requests.get(request_id)


# 单例实例
_trade_confirmation_service: Optional[TradeConfirmationService] = None


def get_trade_confirmation_service() -> TradeConfirmationService:
    """获取交易确认服务实例"""
    global _trade_confirmation_service
    if _trade_confirmation_service is None:
        _trade_confirmation_service = TradeConfirmationService()
    return _trade_confirmation_service
