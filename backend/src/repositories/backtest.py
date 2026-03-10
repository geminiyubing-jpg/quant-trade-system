"""
回测和系统配置 Repository
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .base import BaseRepository
from ..models.strategy import BacktestJob, BacktestResult
from ..models.risk import SystemConfig


class BacktestJobRepository(BaseRepository[BacktestJob, BacktestJob, BacktestJob]):
    """回测任务 Repository"""

    def create_job(
        self,
        db: Session,
        *,
        job_id: str,
        strategy_id: str,
        name: str,
        config: dict,
        created_by: str = None
    ) -> BacktestJob:
        """
        创建回测任务

        Args:
            db: 数据库会话
            job_id: 任务 ID
            strategy_id: 策略 ID
            name: 任务名称
            config: 回测配置（字典）
            created_by: 创建者 ID

        Returns:
            创建的回测任务实例
        """
        db_obj = BacktestJob(
            id=job_id,
            strategy_id=strategy_id,
            name=name,
            status='PENDING',
            config=config,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(
        self,
        db: Session,
        *,
        job_id: str,
        status: str,
        result: dict = None,
        error_message: str = None
    ) -> BacktestJob:
        """
        更新回测任务状态

        Args:
            db: 数据库会话
            job_id: 任务 ID
            status: 新状态
            result: 回测结果
            error_message: 错误消息

        Returns:
            更新后的回测任务实例
        """
        db_obj = self.get(db, id=job_id)
        if not db_obj:
            return None

        db_obj.status = status
        if result:
            db_obj.result = result
        if error_message:
            db_obj.error_message = error_message

        if status == 'COMPLETED':
            db_obj.completed_at = datetime.utcnow()
        elif status == 'RUNNING':
            db_obj.started_at = datetime.utcnow()

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class BacktestResultRepository(BaseRepository[BacktestResult, BacktestResult, BacktestResult]):
    """回测结果 Repository"""

    def get_by_job_id(self, db: Session, *, job_id: str) -> Optional[BacktestResult]:
        """
        根据任务 ID 获取回测结果

        Args:
            db: 数据库会话
            job_id: 回测任务 ID

        Returns:
            回测结果实例或 None
        """
        return db.query(BacktestResult).filter(BacktestResult.job_id == job_id).first()

    def get_by_strategy_id(
        self,
        db: Session,
        *,
        strategy_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[BacktestResult]:
        """
        获取策略的所有回测结果

        Args:
            db: 数据库会话
            strategy_id: 策略 ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            回测结果实例列表
        """
        return db.query(BacktestResult)\
            .filter(BacktestResult.strategy_id == strategy_id)\
            .order_by(desc(BacktestResult.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_latest_by_strategy(
        self,
        db: Session,
        *,
        strategy_id: str
    ) -> Optional[BacktestResult]:
        """
        获取策略的最新回测结果

        Args:
            db: 数据库会话
            strategy_id: 策略 ID

        Returns:
            最新回测结果实例或 None
        """
        return db.query(BacktestResult)\
            .filter(BacktestResult.strategy_id == strategy_id)\
            .order_by(desc(BacktestResult.created_at))\
            .first()

    def create_from_result(
        self,
        db: Session,
        *,
        job_id: str,
        strategy_id: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        final_capital: float,
        total_return: float,
        annual_return: float,
        sharpe_ratio: float,
        sortino_ratio: float,
        max_drawdown: float,
        win_rate: float,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        avg_trade: float,
        avg_win: float,
        avg_loss: float,
        profit_factor: float,
        equity_curve: dict,
        trades: list
    ) -> BacktestResult:
        """
        从回测结果创建数据库记录

        Args:
            db: 数据库会话
            job_id: 回测任务 ID
            strategy_id: 策略 ID
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            final_capital: 最终资金
            total_return: 总收益率
            annual_return: 年化收益率
            sharpe_ratio: 夏普比率
            sortino_ratio: 索提诺比率
            max_drawdown: 最大回撤
            win_rate: 胜率
            total_trades: 总交易次数
            winning_trades: 盈利交易次数
            losing_trades: 亏损交易次数
            avg_trade: 平均收益
            avg_win: 平均盈利
            avg_loss: 平均亏损
            profit_factor: 盈利因子
            equity_curve: 资金曲线数据
            trades: 交易记录数据

        Returns:
            创建的回测结果实例
        """
        db_obj = BacktestResult(
            job_id=job_id,
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_trade=avg_trade,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            equity_curve=equity_curve,
            trades=trades,
            created_at=datetime.utcnow()
        )

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class SystemConfigRepository(BaseRepository[SystemConfig, SystemConfig, SystemConfig]):
    """系统配置 Repository"""

    def get_by_key(self, db: Session, *, key: str) -> Optional[SystemConfig]:
        """
        根据配置键获取配置

        Args:
            db: 数据库会话
            key: 配置键

        Returns:
            系统配置实例或 None
        """
        return db.query(SystemConfig).filter(SystemConfig.key == key).first()

    def get_by_category(
        self,
        db: Session,
        *,
        category: str
    ) -> List[SystemConfig]:
        """
        获取某个分类的所有配置

        Args:
            db: 数据库会话
            category: 配置分类

        Returns:
            系统配置实例列表
        """
        return db.query(SystemConfig).filter(SystemConfig.category == category).all()

    def upsert(
        self,
        db: Session,
        *,
        key: str,
        value: str,
        value_type: str = "string",
        category: str = "general",
        description: str = None
    ) -> SystemConfig:
        """
        创建或更新配置（存在则更新，不存在则创建）

        Args:
            db: 数据库会话
            key: 配置键
            value: 配置值
            value_type: 值类型
            category: 配置分类
            description: 配置描述

        Returns:
            系统配置实例
        """
        # 尝试获取现有配置
        db_obj = self.get_by_key(db, key=key)

        if db_obj:
            # 更新现有配置
            db_obj.value = value
            db_obj.value_type = value_type
            db_obj.category = category
            db_obj.description = description
            db_obj.updated_at = datetime.utcnow()
        else:
            # 创建新配置
            db_obj = SystemConfig(
                key=key,
                value=value,
                value_type=value_type,
                category=category,
                description=description,
                updated_at=datetime.utcnow()
            )
            db.add(db_obj)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_all_dict(self, db: Session) -> dict:
        """
        获取所有配置为字典

        Args:
            db: 数据库会话

        Returns:
            配置字典 {key: value}
        """
        configs = db.query(SystemConfig).all()
        return {config.key: config.value for config in configs}
