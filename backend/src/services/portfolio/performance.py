"""
投资组合绩效分析服务

提供绩效计算、基准管理和归因分析功能。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)


class CustomBenchmark:
    """自定义基准模型（简化版，实际应使用数据库模型）"""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", str(uuid.uuid4()))
        self.portfolio_id = kwargs.get("portfolio_id")
        self.name = kwargs.get("name")
        self.description = kwargs.get("description")
        self.composition = kwargs.get("composition", [])
        self.rebalance_frequency = kwargs.get("rebalance_frequency", "QUARTERLY")
        self.created_at = kwargs.get("created_at", datetime.utcnow())


class PerformanceService:
    """
    投资组合绩效分析服务

    功能：
    - 计算各种绩效指标（夏普比率、索提诺比率等）
    - 自定义基准管理
    - Brinson 归因分析
    """

    # 无风险利率（年化，可配置）
    RISK_FREE_RATE = Decimal("0.03")  # 3%

    # 交易日数（年化）
    TRADING_DAYS_PER_YEAR = 252

    def __init__(self, db: Session):
        self.db = db
        self._benchmarks: Dict[str, CustomBenchmark] = {}

    async def calculate_performance(
        self,
        portfolio_id: str,
        start_date: date,
        end_date: date,
        benchmark_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        计算投资组合绩效指标

        Args:
            portfolio_id: 组合ID
            start_date: 起始日期
            end_date: 结束日期
            benchmark_id: 自定义基准ID

        Returns:
            绩效指标字典
        """
        from src.services.portfolio.manager import PortfolioManager

        manager = PortfolioManager(self.db)

        # 获取组合净值曲线
        nav_series = await self._get_nav_series(portfolio_id, start_date, end_date)

        if not nav_series or len(nav_series) < 2:
            return self._empty_metrics()

        # 计算收益率序列
        returns = self._calculate_returns(nav_series)

        if not returns:
            return self._empty_metrics()

        # 计算各项指标
        total_return = self._calculate_total_return(nav_series)
        annualized_return = self._calculate_annualized_return(total_return, start_date, end_date)
        annualized_volatility = self._calculate_annualized_volatility(returns)
        downside_volatility = self._calculate_downside_volatility(returns)
        max_drawdown = self._calculate_max_drawdown(nav_series)

        # 风险调整收益
        sharpe_ratio = self._calculate_sharpe_ratio(annualized_return, annualized_volatility)
        sortino_ratio = self._calculate_sortino_ratio(annualized_return, downside_volatility)
        calmar_ratio = self._calculate_calmar_ratio(annualized_return, max_drawdown)

        # 获取基准收益
        benchmark_return = None
        alpha = None
        beta = None
        information_ratio = None
        treynor_ratio = None

        if benchmark_id:
            benchmark_data = await self._get_benchmark_returns(benchmark_id, start_date, end_date)
            if benchmark_data:
                benchmark_return = benchmark_data.get("total_return")
                beta = self._calculate_beta(returns, benchmark_data.get("returns", []))
                alpha = self._calculate_alpha(annualized_return, benchmark_return, beta)
                information_ratio = self._calculate_information_ratio(
                    returns, benchmark_data.get("returns", [])
                )
                if beta and beta != 0:
                    treynor_ratio = (annualized_return - self.RISK_FREE_RATE) / beta

        # 胜率和盈亏比
        win_rate = self._calculate_win_rate(returns)
        profit_loss_ratio = self._calculate_profit_loss_ratio(returns)

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "benchmark_return": benchmark_return,
            "annualized_volatility": annualized_volatility,
            "downside_volatility": downside_volatility,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio,
            "information_ratio": information_ratio,
            "treynor_ratio": treynor_ratio,
            "alpha": alpha,
            "beta": beta,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio
        }

    async def create_benchmark(
        self,
        portfolio_id: str,
        name: str,
        composition: List[dict],
        description: Optional[str] = None,
        rebalance_frequency: str = "QUARTERLY"
    ) -> CustomBenchmark:
        """
        创建自定义基准

        Args:
            portfolio_id: 组合ID
            name: 基准名称
            composition: 基准成分（[{"symbol": "000001.SZ", "weight": 0.3}, ...]）
            description: 基准描述
            rebalance_frequency: 再平衡频率

        Returns:
            创建的基准对象
        """
        # 验证权重总和为1
        total_weight = sum(Decimal(str(c.get("weight", 0))) for c in composition)
        if abs(total_weight - Decimal("1")) > Decimal("0.01"):
            raise ValueError(f"基准成分权重总和必须为1，当前为 {total_weight}")

        benchmark = CustomBenchmark(
            portfolio_id=portfolio_id,
            name=name,
            description=description,
            composition=composition,
            rebalance_frequency=rebalance_frequency
        )

        # 存储基准（实际应存入数据库）
        self._benchmarks[benchmark.id] = benchmark

        logger.info(f"创建自定义基准: {name} (ID: {benchmark.id})")
        return benchmark

    def get_benchmarks(self, portfolio_id: str) -> List[CustomBenchmark]:
        """获取组合的所有自定义基准"""
        return [b for b in self._benchmarks.values() if b.portfolio_id == portfolio_id]

    async def calculate_attribution(
        self,
        portfolio_id: str,
        start_date: date,
        end_date: date,
        benchmark_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        计算 Brison 归因分析

        将组合超额收益分解为：
        - 配置效应（Allocation Effect）
        - 选股效应（Selection Effect）
        - 交互效应（Interaction Effect）

        Args:
            portfolio_id: 组合ID
            start_date: 起始日期
            end_date: 结束日期
            benchmark_id: 自定义基准ID

        Returns:
            归因分析结果
        """
        from src.services.portfolio.manager import PortfolioManager

        manager = PortfolioManager(self.db)

        # 获取组合持仓和收益
        positions = manager.get_positions(portfolio_id)
        portfolio_returns = await self._get_position_returns(positions, start_date, end_date)

        # 获取基准收益
        if benchmark_id and benchmark_id in self._benchmarks:
            benchmark = self._benchmarks[benchmark_id]
            benchmark_returns = await self._get_composition_returns(
                benchmark.composition, start_date, end_date
            )
        else:
            # 使用默认基准（沪深300）
            benchmark_returns = await self._get_index_returns("000300.SH", start_date, end_date)

        # 计算归因
        total_return = sum(p.get("return", Decimal("0")) for p in portfolio_returns.values())
        benchmark_return = benchmark_returns.get("total_return", Decimal("0"))
        active_return = total_return - benchmark_return

        # Brison 分解
        allocation_effect = Decimal("0")
        selection_effect = Decimal("0")
        interaction_effect = Decimal("0")

        sector_attribution = []

        # 按行业分组计算归因
        sectors = set()
        for symbol, pos_data in portfolio_returns.items():
            if pos_data.get("sector"):
                sectors.add(pos_data["sector"])

        for sector in sectors:
            # 组合中该行业的权重和收益
            portfolio_sector_weight = sum(
                Decimal(str(p.get("weight", 0)))
                for s, p in portfolio_returns.items()
                if p.get("sector") == sector
            )
            portfolio_sector_return = sum(
                Decimal(str(p.get("return", 0))) * Decimal(str(p.get("weight", 0)))
                for s, p in portfolio_returns.items()
                if p.get("sector") == sector
            )

            # 基准中该行业的权重和收益（简化处理）
            benchmark_sector_weight = portfolio_sector_weight  # 简化
            benchmark_sector_return = benchmark_return * portfolio_sector_weight  # 简化

            # 配置效应 = (组合权重 - 基准权重) * 基准收益
            alloc = (portfolio_sector_weight - benchmark_sector_weight) * benchmark_sector_return
            allocation_effect += alloc

            # 选股效应 = 基准权重 * (组合收益 - 基准收益)
            if benchmark_sector_weight != 0:
                selection = benchmark_sector_weight * (portfolio_sector_return - benchmark_sector_return)
                selection_effect += selection

            sector_attribution.append({
                "sector": sector,
                "portfolio_weight": float(portfolio_sector_weight),
                "portfolio_return": float(portfolio_sector_return),
                "allocation_effect": float(alloc),
                "selection_effect": float(selection) if benchmark_sector_weight != 0 else 0
            })

        # 交互效应 = 主动收益 - 配置效应 - 选股效应
        interaction_effect = active_return - allocation_effect - selection_effect

        return {
            "total_return": total_return,
            "benchmark_return": benchmark_return,
            "active_return": active_return,
            "allocation_effect": allocation_effect,
            "selection_effect": selection_effect,
            "interaction_effect": interaction_effect,
            "sector_attribution": sector_attribution
        }

    # ==============================================
    # 私有方法
    # ==============================================

    async def _get_nav_series(
        self,
        portfolio_id: str,
        start_date: date,
        end_date: date
    ) -> List[Decimal]:
        """获取组合净值曲线"""
        # 简化实现：从数据库或计算获取
        # 实际应从 portfolio_nav_history 表获取
        return [Decimal("1.0"), Decimal("1.05"), Decimal("1.03"), Decimal("1.08"), Decimal("1.12")]

    def _calculate_returns(self, nav_series: List[Decimal]) -> List[Decimal]:
        """计算收益率序列"""
        returns = []
        for i in range(1, len(nav_series)):
            if nav_series[i-1] != 0:
                ret = (nav_series[i] - nav_series[i-1]) / nav_series[i-1]
                returns.append(ret)
        return returns

    def _calculate_total_return(self, nav_series: List[Decimal]) -> Decimal:
        """计算总收益率"""
        if not nav_series or nav_series[0] == 0:
            return Decimal("0")
        return (nav_series[-1] - nav_series[0]) / nav_series[0]

    def _calculate_annualized_return(
        self,
        total_return: Decimal,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """计算年化收益率"""
        days = (end_date - start_date).days
        if days <= 0:
            return Decimal("0")

        years = Decimal(str(days)) / Decimal("365")
        if years == 0:
            return Decimal("0")

        # 年化收益率 = (1 + 总收益率)^(1/年数) - 1
        return ((Decimal("1") + total_return) ** (Decimal("1") / years)) - Decimal("1")

    def _calculate_annualized_volatility(self, returns: List[Decimal]) -> Decimal:
        """计算年化波动率"""
        if not returns:
            return Decimal("0")

        # 计算标准差
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** Decimal("0.5")

        # 年化
        return std_dev * (Decimal(str(self.TRADING_DAYS_PER_YEAR)) ** Decimal("0.5"))

    def _calculate_downside_volatility(self, returns: List[Decimal]) -> Decimal:
        """计算下行波动率"""
        if not returns:
            return Decimal("0")

        # 只计算负收益
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return Decimal("0")

        mean_return = sum(negative_returns) / len(negative_returns)
        variance = sum((r - mean_return) ** 2 for r in negative_returns) / len(negative_returns)
        std_dev = variance ** Decimal("0.5")

        return std_dev * (Decimal(str(self.TRADING_DAYS_PER_YEAR)) ** Decimal("0.5"))

    def _calculate_max_drawdown(self, nav_series: List[Decimal]) -> Decimal:
        """计算最大回撤"""
        if not nav_series:
            return Decimal("0")

        max_nav = nav_series[0]
        max_drawdown = Decimal("0")

        for nav in nav_series:
            if nav > max_nav:
                max_nav = nav

            if max_nav != 0:
                drawdown = (max_nav - nav) / max_nav
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return max_drawdown

    def _calculate_sharpe_ratio(
        self,
        annualized_return: Decimal,
        annualized_volatility: Decimal
    ) -> Decimal:
        """计算夏普比率"""
        if annualized_volatility == 0:
            return Decimal("0")
        return (annualized_return - self.RISK_FREE_RATE) / annualized_volatility

    def _calculate_sortino_ratio(
        self,
        annualized_return: Decimal,
        downside_volatility: Decimal
    ) -> Decimal:
        """计算索提诺比率"""
        if downside_volatility == 0:
            return Decimal("0")
        return (annualized_return - self.RISK_FREE_RATE) / downside_volatility

    def _calculate_calmar_ratio(
        self,
        annualized_return: Decimal,
        max_drawdown: Decimal
    ) -> Decimal:
        """计算卡尔马比率"""
        if max_drawdown == 0:
            return Decimal("0")
        return (annualized_return - self.RISK_FREE_RATE) / max_drawdown

    def _calculate_beta(
        self,
        portfolio_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Optional[Decimal]:
        """计算 Beta"""
        if not portfolio_returns or not benchmark_returns:
            return None

        min_len = min(len(portfolio_returns), len(benchmark_returns))
        if min_len < 2:
            return None

        portfolio_returns = portfolio_returns[:min_len]
        benchmark_returns = benchmark_returns[:min_len]

        # 计算协方差和方差
        mean_portfolio = sum(portfolio_returns) / len(portfolio_returns)
        mean_benchmark = sum(benchmark_returns) / len(benchmark_returns)

        covariance = sum(
            (p - mean_portfolio) * (b - mean_benchmark)
            for p, b in zip(portfolio_returns, benchmark_returns)
        ) / len(portfolio_returns)

        benchmark_variance = sum(
            (b - mean_benchmark) ** 2 for b in benchmark_returns
        ) / len(benchmark_returns)

        if benchmark_variance == 0:
            return None

        return covariance / benchmark_variance

    def _calculate_alpha(
        self,
        portfolio_return: Decimal,
        benchmark_return: Decimal,
        beta: Optional[Decimal]
    ) -> Optional[Decimal]:
        """计算 Alpha"""
        if beta is None:
            return None

        # Alpha = 组合收益 - [无风险收益 + Beta * (基准收益 - 无风险收益)]
        return portfolio_return - (self.RISK_FREE_RATE + beta * (benchmark_return - self.RISK_FREE_RATE))

    def _calculate_information_ratio(
        self,
        portfolio_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Optional[Decimal]:
        """计算信息比率"""
        if not portfolio_returns or not benchmark_returns:
            return None

        min_len = min(len(portfolio_returns), len(benchmark_returns))
        if min_len < 2:
            return None

        # 计算主动收益
        active_returns = [
            p - b for p, b in zip(portfolio_returns[:min_len], benchmark_returns[:min_len])
        ]

        if not active_returns:
            return None

        # 主动收益均值
        mean_active = sum(active_returns) / len(active_returns)

        # 跟踪误差（主动收益标准差）
        variance = sum((r - mean_active) ** 2 for r in active_returns) / len(active_returns)
        tracking_error = variance ** Decimal("0.5")

        if tracking_error == 0:
            return None

        # 年化
        annualized_tracking_error = tracking_error * (Decimal(str(self.TRADING_DAYS_PER_YEAR)) ** Decimal("0.5"))
        annualized_mean_active = mean_active * Decimal(str(self.TRADING_DAYS_PER_YEAR))

        return annualized_mean_active / annualized_tracking_error

    def _calculate_win_rate(self, returns: List[Decimal]) -> Optional[Decimal]:
        """计算胜率"""
        if not returns:
            return None

        positive_count = sum(1 for r in returns if r > 0)
        return Decimal(str(positive_count)) / Decimal(str(len(returns)))

    def _calculate_profit_loss_ratio(self, returns: List[Decimal]) -> Optional[Decimal]:
        """计算盈亏比"""
        if not returns:
            return None

        positive_returns = [r for r in returns if r > 0]
        negative_returns = [r for r in returns if r < 0]

        if not positive_returns or not negative_returns:
            return None

        avg_profit = sum(positive_returns) / len(positive_returns)
        avg_loss = abs(sum(negative_returns) / len(negative_returns))

        if avg_loss == 0:
            return None

        return avg_profit / avg_loss

    async def _get_benchmark_returns(
        self,
        benchmark_id: str,
        start_date: date,
        end_date: date
    ) -> Optional[Dict[str, Any]]:
        """获取基准收益"""
        if benchmark_id not in self._benchmarks:
            return None

        benchmark = self._benchmarks[benchmark_id]
        return await self._get_composition_returns(benchmark.composition, start_date, end_date)

    async def _get_composition_returns(
        self,
        composition: List[dict],
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取组合成分的收益"""
        # 简化实现：返回模拟数据
        # 实际应从数据源获取各成分的收益并加权计算
        return {
            "total_return": Decimal("0.08"),
            "returns": [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01"), Decimal("0.03")]
        }

    async def _get_index_returns(
        self,
        index_code: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取指数收益"""
        # 简化实现：返回模拟数据
        return {
            "total_return": Decimal("0.06"),
            "returns": [Decimal("0.005"), Decimal("0.015"), Decimal("-0.005"), Decimal("0.02")]
        }

    async def _get_position_returns(
        self,
        positions: List[Any],
        start_date: date,
        end_date: date
    ) -> Dict[str, Dict[str, Any]]:
        """获取持仓收益"""
        # 简化实现
        result = {}
        for pos in positions:
            result[pos.symbol] = {
                "weight": pos.weight if hasattr(pos, 'weight') else Decimal("0.1"),
                "return": Decimal("0.05"),
                "sector": pos.sector if hasattr(pos, 'sector') else "Unknown"
            }
        return result

    def _empty_metrics(self) -> Dict[str, Any]:
        """返回空的绩效指标"""
        return {
            "total_return": Decimal("0"),
            "annualized_return": Decimal("0"),
            "benchmark_return": None,
            "annualized_volatility": Decimal("0"),
            "downside_volatility": None,
            "max_drawdown": Decimal("0"),
            "sharpe_ratio": Decimal("0"),
            "sortino_ratio": None,
            "calmar_ratio": None,
            "information_ratio": None,
            "treynor_ratio": None,
            "alpha": None,
            "beta": None,
            "win_rate": None,
            "profit_loss_ratio": None
        }
