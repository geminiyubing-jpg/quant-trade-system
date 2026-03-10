"""
数据质量监控 API 端点

提供数据质量检查、报告和告警等功能。
"""

from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from loguru import logger

from src.core.database import get_db
from sqlalchemy.orm import Session

from src.services.data.quality_monitor import (
    DataQualityMonitor,
    DataQualityReport,
    DataQualityAlert,
    QualityLevel,
    MetricType,
    get_data_quality_monitor
)


router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


# ========================================
# Pydantic 模型
# ========================================

class QualityReportResponse(BaseModel):
    """质量报告响应"""
    report_id: str
    report_time: datetime
    overall_score: float
    overall_level: str
    metrics: List[dict]
    recommendations: List[str]
    alerts: List[dict]


class AlertResponse(BaseModel):
    """告警响应"""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    source: Optional[str]
    timestamp: datetime
    acknowledged: bool


class MetricHistoryResponse(BaseModel):
    """指标历史响应"""
    type: str
    score: float
    level: str
    timestamp: datetime
    details: dict


class QualitySummaryResponse(BaseModel):
    """质量摘要响应"""
    overall_score: float
    overall_level: str
    metric_count: int
    alert_count: int
    last_update: datetime


# ========================================
# 依赖注入
# ========================================

def get_monitor(
    db: Session = Depends(get_db)
) -> DataQualityMonitor:
    """获取数据质量监控器"""
    return get_data_quality_monitor(db)


# ========================================
# API 端点
# ========================================

@router.get("/report", response_model=QualityReportResponse)
async def get_quality_report(
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    获取数据质量报告

    生成完整的数据质量报告，包含：
    - 完整性指标
    - 准确性指标
    - 及时性指标
    - 一致性指标
    - 唯一性指标
    - 改进建议
    """
    try:
        report = await monitor.generate_report()

        return QualityReportResponse(
            report_id=report.report_id,
            report_time=report.report_time,
            overall_score=float(report.overall_score),
            overall_level=report.overall_level.value,
            metrics=[
                {
                    "type": m.metric_type.value,
                    "score": float(m.score),
                    "level": m.level.value,
                    "details": m.details
                }
                for m in report.metrics
            ],
            recommendations=report.recommendations,
            alerts=report.alerts
        )

    except Exception as e:
        logger.error(f"Quality report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{metric_type}")
async def get_metric_detail(
    metric_type: str,
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    获取特定指标的详细信息

    Args:
        metric_type: 指标类型 (completeness, accuracy, timeliness, consistency, uniqueness, validity)
    """
    try:
        # 验证指标类型
        try:
            mtype = MetricType(metric_type.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric type: {metric_type}"
            )

        # 执行检查
        if mtype == MetricType.COMPLETENESS:
            metric = await monitor.check_completeness("stock_prices")
        elif mtype == MetricType.ACCURACY:
            metric = await monitor.check_accuracy("stock_prices")
        elif mtype == MetricType.TIMELINESS:
            metric = await monitor.check_timeliness("akshare")
        elif mtype == MetricType.CONSISTENCY:
            metric = await monitor.check_consistency("stock_prices", ["000001.SZ"])
        elif mtype == MetricType.UNIQUENESS:
            metric = await monitor.check_uniqueness("stock_prices")
        else:
            metric = await monitor.check_completeness("stock_prices")

        return {
            "success": True,
            "data": {
                "type": metric.metric_type.value,
                "score": float(metric.score),
                "level": metric.level.value,
                "details": metric.details,
                "timestamp": metric.timestamp.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metric detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[str] = Query(default=None, description="严重程度过滤 (INFO, WARNING, ERROR, CRITICAL)"),
    acknowledged: Optional[bool] = Query(default=None, description="确认状态过滤"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量限制"),
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    获取告警列表

    Args:
        severity: 严重程度过滤
        acknowledged: 确认状态过滤
        limit: 返回数量限制
    """
    try:
        alerts = monitor.get_alerts(severity=severity, acknowledged=acknowledged, limit=limit)

        return [
            AlertResponse(
                alert_id=a["alert_id"],
                alert_type=a["type"],
                severity=a["severity"],
                message=a["message"],
                source=a.get("source"),
                timestamp=datetime.fromisoformat(a["timestamp"]),
                acknowledged=a["acknowledged"]
            )
            for a in alerts
        ]

    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    确认告警

    Args:
        alert_id: 告警ID
    """
    try:
        success = monitor.acknowledge_alert(alert_id)

        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {
            "success": True,
            "message": f"Alert {alert_id} acknowledged"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Acknowledge alert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[MetricHistoryResponse])
async def get_metric_history(
    metric_type: Optional[str] = Query(default=None, description="指标类型过滤"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量限制"),
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    获取指标历史

    Args:
        metric_type: 指标类型过滤
        limit: 返回数量限制
    """
    try:
        mtype = None
        if metric_type:
            try:
                mtype = MetricType(metric_type.upper())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid metric type: {metric_type}"
                )

        history = monitor.get_metric_history(metric_type=mtype, limit=limit)

        return [
            MetricHistoryResponse(
                type=h["type"],
                score=h["score"],
                level=h["level"],
                timestamp=datetime.fromisoformat(h["timestamp"]),
                details=h.get("details", {})
            )
            for h in history
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metric history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=QualitySummaryResponse)
async def get_quality_summary(
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    获取质量摘要

    返回当前数据质量的快速概览。
    """
    try:
        # 生成报告并提取摘要
        report = await monitor.generate_report()

        return QualitySummaryResponse(
            overall_score=float(report.overall_score),
            overall_level=report.overall_level.value,
            metric_count=len(report.metrics),
            alert_count=len(report.alerts),
            last_update=report.report_time
        )

    except Exception as e:
        logger.error(f"Quality summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check/completeness")
async def check_completeness(
    table_name: str = Query(default="stock_prices", description="表名"),
    symbol: Optional[str] = Query(default=None, description="股票代码"),
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    检查数据完整性

    Args:
        table_name: 表名
        symbol: 股票代码（可选）
    """
    try:
        metric = await monitor.check_completeness(table_name, symbol)

        return {
            "success": True,
            "data": {
                "type": metric.metric_type.value,
                "score": float(metric.score),
                "level": metric.level.value,
                "details": metric.details
            }
        }

    except Exception as e:
        logger.error(f"Completeness check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check/accuracy")
async def check_accuracy(
    table_name: str = Query(default="stock_prices", description="表名"),
    sample_size: int = Query(default=100, ge=10, le=1000, description="抽样数量"),
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    检查数据准确性

    Args:
        table_name: 表名
        sample_size: 抽样数量
    """
    try:
        metric = await monitor.check_accuracy(table_name, sample_size)

        return {
            "success": True,
            "data": {
                "type": metric.metric_type.value,
                "score": float(metric.score),
                "level": metric.level.value,
                "details": metric.details
            }
        }

    except Exception as e:
        logger.error(f"Accuracy check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check/timeliness")
async def check_timeliness(
    source_name: str = Query(default="akshare", description="数据源名称"),
    monitor: DataQualityMonitor = Depends(get_monitor)
):
    """
    检查数据及时性

    Args:
        source_name: 数据源名称
    """
    try:
        metric = await monitor.check_timeliness(source_name)

        return {
            "success": True,
            "data": {
                "type": metric.metric_type.value,
                "score": float(metric.score),
                "level": metric.level.value,
                "details": metric.details
            }
        }

    except Exception as e:
        logger.error(f"Timeliness check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
