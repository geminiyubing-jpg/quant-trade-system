"""
==============================================
QuantAI Ecosystem - Celery 任务配置
==============================================

定义异步任务队列，支持：
- 数据同步任务
- 策略计算任务
- 回测执行任务
- 通知发送任务
"""

from celery import Celery
from celery.schedules import crontab
import os

# Celery 配置
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# 创建 Celery 应用
celery_app = Celery(
    "quant_trade",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "src.tasks.data_tasks",
        "src.tasks.strategy_tasks",
        "src.tasks.backtest_tasks",
        "src.tasks.trading_tasks",
        "src.tasks.notification_tasks",
    ]
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务结果配置
    result_expires=3600,  # 结果保留1小时
    task_track_started=True,

    # 任务限流
    task_annotations={
        "src.tasks.backtest_tasks.run_backtest": {
            "rate_limit": "10/m"  # 每分钟最多10个回测任务
        }
    },

    # Worker 配置
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # 任务重试配置
    task_default_retry_delay=60,
    task_max_retries=3,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    # 每日数据同步（交易日 9:00）
    "daily-data-sync": {
        "task": "src.tasks.data_tasks.sync_daily_data",
        "schedule": crontab(hour=9, minute=0, day_of_week="1-5"),
        "options": {"queue": "data"},
    },

    # 实时行情数据缓存刷新（交易时间每分钟）
    "realtime-quote-refresh": {
        "task": "src.tasks.data_tasks.refresh_realtime_cache",
        "schedule": crontab(minute="*", hour="9-15", day_of_week="1-5"),
        "options": {"queue": "data"},
    },

    # 数据质量检查（每日 18:00）
    "data-quality-check": {
        "task": "src.tasks.data_tasks.check_data_quality",
        "schedule": crontab(hour=18, minute=0),
        "options": {"queue": "data"},
    },

    # 策略信号生成（交易时间每5分钟）
    "strategy-signal-generate": {
        "task": "src.tasks.strategy_tasks.generate_signals",
        "schedule": crontab(minute="*/5", hour="9-15", day_of_week="1-5"),
        "options": {"queue": "strategy"},
    },

    # 持仓风险检查（交易时间每分钟）
    "position-risk-check": {
        "task": "src.tasks.trading_tasks.check_position_risk",
        "schedule": crontab(minute="*", hour="9-15", day_of_week="1-5"),
        "options": {"queue": "trading"},
    },

    # 日交易统计（每日 16:00）
    "daily-trade-stats": {
        "task": "src.tasks.trading_tasks.generate_daily_stats",
        "schedule": crontab(hour=16, minute=0, day_of_week="1-5"),
        "options": {"queue": "trading"},
    },

    # 清理过期缓存（每日凌晨 2:00）
    "cleanup-expired-cache": {
        "task": "src.tasks.data_tasks.cleanup_expired_cache",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "maintenance"},
    },
}


# 任务基类
class BaseTask(celery_app.Task):
    """任务基类，提供通用功能"""

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试时的回调"""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"任务重试: {task_id}, 原因: {exc}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"任务失败: {task_id}, 错误: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"任务成功: {task_id}")


# 使用基类
celery_app.Task = BaseTask
