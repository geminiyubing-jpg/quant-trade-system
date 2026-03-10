"""
==============================================
QuantAI Ecosystem - 数据质量监控服务
==============================================

提供全面的数据质量监控、报告和告警功能。
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

logger = logging.getLogger(__name__)


# ==============================================
# 数据模型
# ==============================================

class QualityLevel(str, Enum):
    """质量等级"""
    EXCELLENT = "EXCELLENT"  # 优秀 (>98%)
    GOOD = "GOOD"  # 良好 (95-98%)
    WARNING = "WARNING"  # 警告 (80-95%)
    CRITICAL = "CRITICAL"  # 严重 (<80%)


class MetricType(str, Enum):
    """指标类型"""
    COMPLETENESS = "COMPLETENESS"  # 完整性
    ACCURACY = "ACCURACY"  # 准确性
    TIMELINESS = "TIMELINESS"  # 及时性
    CONSISTENCY = "CONSISTENCY"  # 一致性
    UNIQUENESS = "UNIQUENESS"  # 唯一性
    VALIDITY = "VALIDITY"  # 有效性


@dataclass
class QualityMetric:
    """质量指标"""
    metric_type: MetricType
    score: Decimal  # 0-100
    level: QualityLevel
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DataSourceHealth:
    """数据源健康状态"""
    source_name: str
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    last_update: datetime
    latency_ms: int
    success_rate: Decimal
    error_count: int
    total_count: int
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataQualityReport:
    """数据质量报告"""
    report_id: str
    report_time: datetime
    overall_score: Decimal
    overall_level: QualityLevel
    metrics: List[QualityMetric]
    source_health: List[DataSourceHealth]
    recommendations: List[str]
    alerts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DataQualityAlert:
    """数据质量告警"""
    alert_id: str
    alert_type: str
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    source: Optional[str]
    metric_value: Optional[Decimal]
    threshold: Optional[Decimal]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False


# ==============================================
# 数据质量监控器
# ==============================================

class DataQualityMonitor:
    """
    数据质量监控器

    监控数据源的完整性、准确性、及时性等质量指标。
    """

    def __init__(
        self,
        db: Session,
        check_interval: int = 300  # 检查间隔（秒）
    ):
        self.db = db
        self.check_interval = check_interval

        # 质量阈值配置
        self.thresholds = {
            "completeness_excellent": Decimal("98"),
            "completeness_good": Decimal("95"),
            "completeness_warning": Decimal("80"),
            "accuracy_excellent": Decimal("99"),
            "accuracy_good": Decimal("95"),
            "accuracy_warning": Decimal("90"),
            "timeliness_excellent": 60,  # 秒
            "timeliness_good": 300,
            "timeliness_warning": 900,
        }

        # 告警历史
        self.alerts: List[DataQualityAlert] = []

        # 指标历史
        self.metric_history: Dict[str, List[QualityMetric]] = defaultdict(list)

        # 数据源状态
        self.source_status: Dict[str, DataSourceHealth] = {}

    async def check_completeness(
        self,
        table_name: str,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> QualityMetric:
        """
        检查数据完整性

        Args:
            table_name: 表名
            symbol: 股票代码（可选）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            QualityMetric: 完整性指标
        """
        try:
            # 获取预期数据点数量（交易日）
            if start_date and end_date:
                expected_days = self._count_trading_days(start_date, end_date)
            else:
                expected_days = 250  # 假设一年250个交易日

            # 查询实际数据点数量
            actual_count = self._query_data_count(table_name, symbol, start_date, end_date)

            # 计算完整性分数
            if expected_days > 0:
                score = Decimal(str(min(100, (actual_count / expected_days) * 100)))
            else:
                score = Decimal("100")

            # 确定质量等级
            level = self._get_quality_level(score, "completeness")

            return QualityMetric(
                metric_type=MetricType.COMPLETENESS,
                score=score,
                level=level,
                details={
                    "table": table_name,
                    "symbol": symbol,
                    "expected_count": expected_days,
                    "actual_count": actual_count,
                    "coverage": float(score)
                }
            )

        except Exception as e:
            logger.error(f"Completeness check error: {e}")
            return QualityMetric(
                metric_type=MetricType.COMPLETENESS,
                score=Decimal("0"),
                level=QualityLevel.CRITICAL,
                details={"error": str(e)}
            )

    async def check_accuracy(
        self,
        table_name: str,
        sample_size: int = 100
    ) -> QualityMetric:
        """
        检查数据准确性

        Args:
            table_name: 表名
            sample_size: 抽样数量

        Returns:
            QualityMetric: 准确性指标
        """
        try:
            # 抽样检查数据准确性
            errors = []

            # 检查价格逻辑（high >= low, close 在 high 和 low 之间等）
            price_errors = await self._check_price_logic(table_name, sample_size)
            errors.extend(price_errors)

            # 检查数据范围
            range_errors = await self._check_data_range(table_name, sample_size)
            errors.extend(range_errors)

            # 计算准确性分数
            total_checks = sample_size * 3  # 每条数据3个检查项
            error_count = len(errors)
            if total_checks > 0:
                score = Decimal(str(max(0, (1 - error_count / total_checks) * 100)))
            else:
                score = Decimal("100")

            level = self._get_quality_level(score, "accuracy")

            return QualityMetric(
                metric_type=MetricType.ACCURACY,
                score=score,
                level=level,
                details={
                    "table": table_name,
                    "total_checks": total_checks,
                    "error_count": error_count,
                    "errors": errors[:10]  # 只保留前10个错误
                }
            )

        except Exception as e:
            logger.error(f"Accuracy check error: {e}")
            return QualityMetric(
                metric_type=MetricType.ACCURACY,
                score=Decimal("0"),
                level=QualityLevel.CRITICAL,
                details={"error": str(e)}
            )

    async def check_timeliness(
        self,
        source_name: str,
        max_delay_seconds: int = 300
    ) -> QualityMetric:
        """
        检查数据及时性

        Args:
            source_name: 数据源名称
            max_delay_seconds: 最大延迟秒数

        Returns:
            QualityMetric: 及时性指标
        """
        try:
            # 获取数据源最后更新时间
            last_update = await self._get_last_update_time(source_name)

            if last_update is None:
                return QualityMetric(
                    metric_type=MetricType.TIMELINESS,
                    score=Decimal("0"),
                    level=QualityLevel.CRITICAL,
                    details={"error": "No data found"}
                )

            # 计算延迟
            delay = (datetime.utcnow() - last_update).total_seconds()

            # 计算及时性分数
            if delay <= self.thresholds["timeliness_excellent"]:
                score = Decimal("100")
            elif delay <= self.thresholds["timeliness_good"]:
                score = Decimal("90")
            elif delay <= self.thresholds["timeliness_warning"]:
                score = Decimal("70")
            else:
                score = Decimal("50")

            level = self._get_quality_level(score, "timeliness")

            return QualityMetric(
                metric_type=MetricType.TIMELINESS,
                score=score,
                level=level,
                details={
                    "source": source_name,
                    "last_update": last_update.isoformat(),
                    "delay_seconds": delay,
                    "threshold_seconds": max_delay_seconds
                }
            )

        except Exception as e:
            logger.error(f"Timeliness check error: {e}")
            return QualityMetric(
                metric_type=MetricType.TIMELINESS,
                score=Decimal("0"),
                level=QualityLevel.CRITICAL,
                details={"error": str(e)}
            )

    async def check_consistency(
        self,
        table_name: str,
        symbols: List[str]
    ) -> QualityMetric:
        """
        检查数据一致性

        Args:
            table_name: 表名
            symbols: 股票代码列表

        Returns:
            QualityMetric: 一致性指标
        """
        try:
            inconsistencies = []

            for symbol in symbols[:10]:  # 最多检查10只股票
                # 检查价格跳跃（异常波动）
                jumps = await self._check_price_jumps(table_name, symbol)
                inconsistencies.extend(jumps)

                # 检查成交量异常
                volume_anomalies = await self._check_volume_anomalies(table_name, symbol)
                inconsistencies.extend(volume_anomalies)

            # 计算一致性分数
            total_checks = len(symbols[:10]) * 2
            error_count = len(inconsistencies)

            if total_checks > 0:
                score = Decimal(str(max(0, (1 - error_count / total_checks) * 100)))
            else:
                score = Decimal("100")

            level = self._get_quality_level(score, "accuracy")

            return QualityMetric(
                metric_type=MetricType.CONSISTENCY,
                score=score,
                level=level,
                details={
                    "table": table_name,
                    "symbols_checked": len(symbols[:10]),
                    "inconsistencies": inconsistencies[:10]
                }
            )

        except Exception as e:
            logger.error(f"Consistency check error: {e}")
            return QualityMetric(
                metric_type=MetricType.CONSISTENCY,
                score=Decimal("0"),
                level=QualityLevel.CRITICAL,
                details={"error": str(e)}
            )

    async def check_uniqueness(
        self,
        table_name: str
    ) -> QualityMetric:
        """
        检查数据唯一性

        Args:
            table_name: 表名

        Returns:
            QualityMetric: 唯一性指标
        """
        try:
            # 检查重复数据
            duplicates = await self._check_duplicates(table_name)

            # 获取总数据量
            total_count = self._query_data_count(table_name)

            # 计算唯一性分数
            if total_count > 0:
                unique_count = total_count - len(duplicates)
                score = Decimal(str((unique_count / total_count) * 100))
            else:
                score = Decimal("100")

            level = self._get_quality_level(score, "completeness")

            return QualityMetric(
                metric_type=MetricType.UNIQUENESS,
                score=score,
                level=level,
                details={
                    "table": table_name,
                    "total_count": total_count,
                    "duplicate_count": len(duplicates),
                    "unique_rate": float(score)
                }
            )

        except Exception as e:
            logger.error(f"Uniqueness check error: {e}")
            return QualityMetric(
                metric_type=MetricType.UNIQUENESS,
                score=Decimal("0"),
                level=QualityLevel.CRITICAL,
                details={"error": str(e)}
            )

    async def generate_report(
        self,
        sources: Optional[List[str]] = None
    ) -> DataQualityReport:
        """
        生成数据质量报告

        Args:
            sources: 要检查的数据源列表

        Returns:
            DataQualityReport: 质量报告
        """
        import uuid

        report_id = str(uuid.uuid4())
        metrics = []
        source_health = []
        alerts = []
        recommendations = []

        # 检查各个指标
        completeness = await self.check_completeness("stock_prices")
        metrics.append(completeness)

        accuracy = await self.check_accuracy("stock_prices")
        metrics.append(accuracy)

        timeliness = await self.check_timeliness("akshare")
        metrics.append(timeliness)

        consistency = await self.check_consistency("stock_prices", ["000001.SZ"])
        metrics.append(consistency)

        uniqueness = await self.check_uniqueness("stock_prices")
        metrics.append(uniqueness)

        # 计算总体分数
        scores = [m.score for m in metrics]
        overall_score = sum(scores) / len(scores) if scores else Decimal("0")
        overall_level = self._get_overall_level(overall_score)

        # 生成告警
        for metric in metrics:
            if metric.level in [QualityLevel.WARNING, QualityLevel.CRITICAL]:
                alert = DataQualityAlert(
                    alert_id=f"ALERT_{metric.metric_type.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    alert_type=metric.metric_type.value,
                    severity="WARNING" if metric.level == QualityLevel.WARNING else "ERROR",
                    message=f"{metric.metric_type.value} quality is {metric.level.value}: {metric.score:.1f}%",
                    source=None,
                    metric_value=metric.score,
                    threshold=Decimal(str(self._get_threshold(metric.metric_type)))
                )
                self.alerts.append(alert)
                alerts.append({
                    "alert_id": alert.alert_id,
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message
                })

        # 生成建议
        recommendations = self._generate_recommendations(metrics)

        return DataQualityReport(
            report_id=report_id,
            report_time=datetime.utcnow(),
            overall_score=overall_score,
            overall_level=overall_level,
            metrics=metrics,
            source_health=source_health,
            recommendations=recommendations,
            alerts=alerts
        )

    def get_alerts(
        self,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取告警列表

        Args:
            severity: 严重程度过滤
            acknowledged: 确认状态过滤
            limit: 返回数量限制

        Returns:
            List[Dict]: 告警列表
        """
        alerts = self.alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        return [
            {
                "alert_id": a.alert_id,
                "type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "source": a.source,
                "timestamp": a.timestamp.isoformat(),
                "acknowledged": a.acknowledged
            }
            for a in alerts[-limit:]
        ]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        确认告警

        Args:
            alert_id: 告警ID

        Returns:
            bool: 是否成功
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_metric_history(
        self,
        metric_type: Optional[MetricType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取指标历史

        Args:
            metric_type: 指标类型过滤
            limit: 返回数量限制

        Returns:
            List[Dict]: 指标历史
        """
        history = []

        for mtype, metrics in self.metric_history.items():
            if metric_type is None or mtype == metric_type.value:
                for m in metrics[-limit:]:
                    history.append({
                        "type": m.metric_type.value,
                        "score": float(m.score),
                        "level": m.level.value,
                        "timestamp": m.timestamp.isoformat(),
                        "details": m.details
                    })

        return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]

    # ==============================================
    # 内部方法
    # ==============================================

    def _count_trading_days(self, start_date: date, end_date: date) -> int:
        """计算交易日数量（简化实现）"""
        days = (end_date - start_date).days
        # 粗略估计：一年约250个交易日
        return int(days * 250 / 365)

    def _query_data_count(
        self,
        table_name: str,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """查询数据数量"""
        # TODO: 实现实际数据库查询
        # 这里返回模拟数据
        import random
        return random.randint(200, 250)

    async def _check_price_logic(self, table_name: str, sample_size: int) -> List[Dict]:
        """检查价格逻辑"""
        errors = []
        # TODO: 实现实际检查
        return errors

    async def _check_data_range(self, table_name: str, sample_size: int) -> List[Dict]:
        """检查数据范围"""
        errors = []
        # TODO: 实现实际检查
        return errors

    async def _get_last_update_time(self, source_name: str) -> Optional[datetime]:
        """获取最后更新时间"""
        # TODO: 实现实际查询
        return datetime.utcnow() - timedelta(minutes=5)

    async def _check_price_jumps(self, table_name: str, symbol: str) -> List[Dict]:
        """检查价格跳跃"""
        inconsistencies = []
        # TODO: 实现实际检查
        return inconsistencies

    async def _check_volume_anomalies(self, table_name: str, symbol: str) -> List[Dict]:
        """检查成交量异常"""
        anomalies = []
        # TODO: 实现实际检查
        return anomalies

    async def _check_duplicates(self, table_name: str) -> List[Dict]:
        """检查重复数据"""
        duplicates = []
        # TODO: 实现实际检查
        return duplicates

    def _get_quality_level(self, score: Decimal, metric_category: str) -> QualityLevel:
        """获取质量等级"""
        if metric_category == "completeness":
            if score >= self.thresholds["completeness_excellent"]:
                return QualityLevel.EXCELLENT
            elif score >= self.thresholds["completeness_good"]:
                return QualityLevel.GOOD
            elif score >= self.thresholds["completeness_warning"]:
                return QualityLevel.WARNING
            else:
                return QualityLevel.CRITICAL
        else:  # accuracy
            if score >= self.thresholds["accuracy_excellent"]:
                return QualityLevel.EXCELLENT
            elif score >= self.thresholds["accuracy_good"]:
                return QualityLevel.GOOD
            elif score >= self.thresholds["accuracy_warning"]:
                return QualityLevel.WARNING
            else:
                return QualityLevel.CRITICAL

    def _get_overall_level(self, score: Decimal) -> QualityLevel:
        """获取总体质量等级"""
        if score >= 98:
            return QualityLevel.EXCELLENT
        elif score >= 95:
            return QualityLevel.GOOD
        elif score >= 80:
            return QualityLevel.WARNING
        else:
            return QualityLevel.CRITICAL

    def _get_threshold(self, metric_type: MetricType) -> float:
        """获取指标阈值"""
        if metric_type == MetricType.COMPLETENESS:
            return float(self.thresholds["completeness_good"])
        elif metric_type == MetricType.ACCURACY:
            return float(self.thresholds["accuracy_good"])
        elif metric_type == MetricType.TIMELINESS:
            return float(self.thresholds["timeliness_good"])
        else:
            return 95.0

    def _generate_recommendations(self, metrics: List[QualityMetric]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        for metric in metrics:
            if metric.level == QualityLevel.CRITICAL:
                if metric.metric_type == MetricType.COMPLETENESS:
                    recommendations.append("URGENT: Data completeness is critically low. Check data ingestion pipeline.")
                elif metric.metric_type == MetricType.ACCURACY:
                    recommendations.append("URGENT: Data accuracy issues detected. Review data validation rules.")
                elif metric.metric_type == MetricType.TIMELINESS:
                    recommendations.append("URGENT: Data is severely delayed. Check data source connectivity.")
            elif metric.level == QualityLevel.WARNING:
                if metric.metric_type == MetricType.COMPLETENESS:
                    recommendations.append("WARNING: Some data gaps detected. Monitor data sources.")
                elif metric.metric_type == MetricType.ACCURACY:
                    recommendations.append("WARNING: Minor data accuracy issues. Review recent changes.")

        if not recommendations:
            recommendations.append("All quality metrics are within acceptable ranges.")

        return recommendations


# ==============================================
# 全局实例
# ==============================================

_monitor_instance: Optional[DataQualityMonitor] = None


def get_data_quality_monitor(db: Session) -> DataQualityMonitor:
    """获取数据质量监控器实例"""
    global _monitor_instance
    if _monitor_instance is None or _monitor_instance.db != db:
        _monitor_instance = DataQualityMonitor(db)
    return _monitor_instance
