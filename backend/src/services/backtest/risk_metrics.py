"""
风险度量服务

提供全面的风险分析功能：
- VaR (Value at Risk)
- CVaR (Conditional VaR / Expected Shortfall)
- 压力测试
- 风险分解
- 下行风险分析
- 波动率分析
- 相关性风险
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger(__name__)


# ==============================================
# 数据类定义
# ==============================================

@dataclass
class VaRResult:
    """VaR结果"""
    var_95: float  # 95%置信度VaR
    var_99: float  # 99%置信度VaR
    cvar_95: float  # 95%置信度CVaR
    cvar_99: float  # 99%置信度CVaR
    method: str  # 计算方法
    daily_var: float  # 日度VaR
    annual_var: float  # 年化VaR


@dataclass
class StressTestResult:
    """压力测试结果"""
    scenario_name: str
    description: str
    portfolio_impact: float  # 组合影响（收益率）
    worst_case_impact: float
    best_case_impact: float
    affected_positions: List[Dict[str, Any]]
    recovery_days: int  # 预计恢复天数


@dataclass
class RiskDecomposition:
    """风险分解结果"""
    total_risk: float  # 总风险
    systematic_risk: float  # 系统性风险
    idiosyncratic_risk: float  # 特质风险
    factor_contributions: Dict[str, float]  # 因子贡献
    concentration_risk: float  # 集中度风险


@dataclass
class DownsideRiskResult:
    """下行风险结果"""
    downside_deviation: float
    semi_variance: float
    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float
    recovery_factor: float
    pain_index: float


@dataclass
class VolatilityAnalysis:
    """波动率分析结果"""
    total_volatility: float
    upside_volatility: float
    downside_volatility: float
    volatility_ratio: float  # 上行/下行波动率比
    garch_volatility: float = 0  # GARCH模型估计
    parkinson_volatility: float = 0  # Parkinson估计（基于高低价）


@dataclass
class ComprehensiveRiskResult:
    """综合风险分析结果"""
    var_result: VaRResult
    stress_test_results: List[StressTestResult]
    risk_decomposition: RiskDecomposition
    downside_risk: DownsideRiskResult
    volatility_analysis: VolatilityAnalysis
    risk_summary: Dict[str, Any]
    risk_rating: str  # 风险等级 (Low/Medium/High/Critical)
    created_at: datetime = field(default_factory=datetime.utcnow)


# ==============================================
# 风险度量服务
# ==============================================

class RiskMetricsService:
    """
    风险度量服务

    提供全面的风险分析功能。
    """

    def __init__(self, confidence_levels: List[float] = None):
        """
        初始化

        Args:
            confidence_levels: 置信水平列表，默认 [0.95, 0.99]
        """
        self.confidence_levels = confidence_levels or [0.95, 0.99]
        self.logger = logging.getLogger("RiskMetricsService")

    def analyze_risk(
        self,
        daily_returns: List[float],
        positions: Dict[str, float] = None,
        benchmark_returns: List[float] = None,
        factor_exposures: Dict[str, float] = None,
        price_data: List[Dict] = None
    ) -> ComprehensiveRiskResult:
        """
        执行综合风险分析

        Args:
            daily_returns: 日收益率序列
            positions: 持仓 {symbol: weight}
            benchmark_returns: 基准收益率
            factor_exposures: 因子暴露
            price_data: 价格数据（用于Parkinson波动率）

        Returns:
            ComprehensiveRiskResult: 综合风险分析结果
        """
        self.logger.info("开始风险分析")

        returns = np.array(daily_returns)

        # 1. VaR/CVaR分析
        var_result = self._calculate_var(returns)

        # 2. 压力测试
        stress_results = self._run_stress_tests(returns, positions)

        # 3. 风险分解
        risk_decomp = self._decompose_risk(
            returns, benchmark_returns, factor_exposures, positions
        )

        # 4. 下行风险
        downside_risk = self._analyze_downside_risk(returns)

        # 5. 波动率分析
        volatility = self._analyze_volatility(returns, price_data)

        # 6. 生成风险摘要和评级
        risk_summary = self._generate_risk_summary(
            var_result, stress_results, risk_decomp, downside_risk, volatility
        )
        risk_rating = self._determine_risk_rating(
            var_result, downside_risk, volatility
        )

        return ComprehensiveRiskResult(
            var_result=var_result,
            stress_test_results=stress_results,
            risk_decomposition=risk_decomp,
            downside_risk=downside_risk,
            volatility_analysis=volatility,
            risk_summary=risk_summary,
            risk_rating=risk_rating
        )

    def _calculate_var(
        self,
        returns: np.ndarray,
        method: str = "historical"
    ) -> VaRResult:
        """
        计算VaR和CVaR

        Args:
            returns: 收益率序列
            method: 计算方法 (historical/parametric/monte_carlo)

        Returns:
            VaRResult: VaR结果
        """
        if len(returns) < 30:
            return VaRResult(
                var_95=0, var_99=0, cvar_95=0, cvar_99=0,
                method="insufficient_data", daily_var=0, annual_var=0
            )

        if method == "historical":
            var_95, cvar_95 = self._historical_var_cvar(returns, 0.95)
            var_99, cvar_99 = self._historical_var_cvar(returns, 0.99)
        elif method == "parametric":
            var_95, cvar_95 = self._parametric_var_cvar(returns, 0.95)
            var_99, cvar_99 = self._parametric_var_cvar(returns, 0.99)
        else:
            # 默认使用历史模拟
            var_95, cvar_95 = self._historical_var_cvar(returns, 0.95)
            var_99, cvar_99 = self._historical_var_cvar(returns, 0.99)

        # 计算年化VaR（假设252个交易日）
        annual_var_95 = var_95 * np.sqrt(252)

        return VaRResult(
            var_95=float(-var_95),  # 转为正值（损失）
            var_99=float(-var_99),
            cvar_95=float(-cvar_95),
            cvar_99=float(-cvar_99),
            method=method,
            daily_var=float(-var_95),
            annual_var=float(-annual_var_95)
        )

    def _historical_var_cvar(
        self,
        returns: np.ndarray,
        confidence: float
    ) -> Tuple[float, float]:
        """
        历史模拟法计算VaR和CVaR

        VaR: 在置信水平下的最大损失
        CVaR: 超过VaR的平均损失（期望损失）
        """
        sorted_returns = np.sort(returns)
        index = int((1 - confidence) * len(sorted_returns))

        var = sorted_returns[index]
        cvar = np.mean(sorted_returns[:index + 1])

        return var, cvar

    def _parametric_var_cvar(
        self,
        returns: np.ndarray,
        confidence: float
    ) -> Tuple[float, float]:
        """
        参数法计算VaR和CVaR

        假设收益服从正态分布。
        """
        mean = np.mean(returns)
        std = np.std(returns)

        # VaR = μ - z * σ
        z = stats.norm.ppf(1 - confidence)
        var = mean + z * std

        # CVaR (对于正态分布)
        # CVaR = μ - σ * φ(z) / (1-α)
        phi_z = stats.norm.pdf(z)
        cvar = mean - std * phi_z / (1 - confidence)

        return var, cvar

    def _run_stress_tests(
        self,
        returns: np.ndarray,
        positions: Dict[str, float] = None
    ) -> List[StressTestResult]:
        """
        执行压力测试

        模拟极端市场情况下的组合表现。
        """
        results = []

        # 定义压力情景
        scenarios = [
            {
                "name": "市场崩盘",
                "description": "2008年式市场崩盘，股票下跌40%",
                "shock": -0.40,
                "affected": ["股票"]
            },
            {
                "name": "流动性危机",
                "description": "流动性枯竭，买卖价差扩大3倍",
                "shock": -0.15,
                "affected": ["所有资产"]
            },
            {
                "name": "利率冲击",
                "description": "利率快速上升200基点",
                "shock": -0.10,
                "affected": ["债券", "成长股"]
            },
            {
                "name": "尾部风险",
                "description": "5个标准差负面冲击",
                "shock": -5 * np.std(returns) if len(returns) > 0 else -0.25,
                "affected": ["所有资产"]
            },
            {
                "name": "相关性崩溃",
                "description": "资产相关性突然趋近于1",
                "shock": -0.25,
                "affected": ["多元化组合"]
            },
        ]

        for scenario in scenarios:
            shock = scenario["shock"]

            # 计算组合影响
            portfolio_impact = shock

            # 最坏情况（额外10%冲击）
            worst_case = shock * 1.1

            # 最好情况（冲击减半）
            best_case = shock * 0.5

            # 预计恢复天数（基于历史波动率）
            if len(returns) > 0:
                avg_return = np.mean(returns)
                if avg_return > 0:
                    recovery_days = int(abs(shock) / (avg_return * 5))  # 假设每周恢复一点
                else:
                    recovery_days = 999  # 无法恢复
            else:
                recovery_days = 30

            results.append(StressTestResult(
                scenario_name=scenario["name"],
                description=scenario["description"],
                portfolio_impact=float(portfolio_impact),
                worst_case_impact=float(worst_case),
                best_case_impact=float(best_case),
                affected_positions=[{"type": t} for t in scenario["affected"]],
                recovery_days=recovery_days
            ))

        return results

    def _decompose_risk(
        self,
        returns: np.ndarray,
        benchmark_returns: np.ndarray = None,
        factor_exposures: Dict[str, float] = None,
        positions: Dict[str, float] = None
    ) -> RiskDecomposition:
        """
        风险分解

        将总风险分解为系统性风险和特质风险。
        """
        total_risk = float(np.std(returns) * np.sqrt(252)) if len(returns) > 0 else 0

        systematic_risk = 0
        idiosyncratic_risk = total_risk
        factor_contributions = {}
        concentration_risk = 0

        # 如果有基准数据，计算系统性风险
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            benchmark = np.array(benchmark_returns)

            # 计算Beta
            cov_matrix = np.cov(returns, benchmark)
            var_benchmark = np.var(benchmark)

            if var_benchmark > 0:
                beta = cov_matrix[0, 1] / var_benchmark
                systematic_risk = abs(beta) * np.std(benchmark) * np.sqrt(252)

                # 特质风险 = sqrt(总风险^2 - 系统性风险^2)
                idiosyncratic_risk = np.sqrt(max(0, total_risk ** 2 - systematic_risk ** 2))

        # 因子贡献
        if factor_exposures:
            for factor, exposure in factor_exposures.items():
                # 简化：假设每个因子的波动率为5%
                factor_vol = 0.05
                factor_contributions[factor] = abs(exposure) * factor_vol

        # 集中度风险（基于持仓）
        if positions:
            weights = np.array(list(positions.values()))
            if len(weights) > 0:
                # 使用HHI指数衡量集中度
                hhi = np.sum(weights ** 2)
                concentration_risk = float(hhi * total_risk)

        return RiskDecomposition(
            total_risk=total_risk,
            systematic_risk=float(systematic_risk),
            idiosyncratic_risk=float(idiosyncratic_risk),
            factor_contributions=factor_contributions,
            concentration_risk=concentration_risk
        )

    def _analyze_downside_risk(self, returns: np.ndarray) -> DownsideRiskResult:
        """
        下行风险分析
        """
        if len(returns) == 0:
            return DownsideRiskResult(
                downside_deviation=0, semi_variance=0, max_drawdown=0,
                max_drawdown_duration=0, avg_drawdown=0,
                recovery_factor=0, pain_index=0
            )

        # 下行偏差（只考虑负收益）
        negative_returns = returns[returns < 0]
        downside_deviation = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0

        # 半方差
        semi_variance = np.mean(negative_returns ** 2) if len(negative_returns) > 0 else 0

        # 最大回撤
        cumulative = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative)
        drawdowns = (peak - cumulative) / peak

        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0
        avg_drawdown = float(np.mean(drawdowns[drawdowns > 0])) if np.any(drawdowns > 0) else 0

        # 最大回撤持续时间
        max_dd_duration = self._calculate_max_drawdown_duration(drawdowns)

        # 恢复因子
        total_return = float(cumulative[-1] - 1) if len(cumulative) > 0 else 0
        recovery_factor = abs(total_return / max_drawdown) if max_drawdown > 0 else 0

        # Pain Index（平均回撤）
        pain_index = float(np.mean(drawdowns)) if len(drawdowns) > 0 else 0

        return DownsideRiskResult(
            downside_deviation=float(downside_deviation),
            semi_variance=float(semi_variance),
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            avg_drawdown=avg_drawdown,
            recovery_factor=float(recovery_factor),
            pain_index=pain_index
        )

    def _calculate_max_drawdown_duration(self, drawdowns: np.ndarray) -> int:
        """计算最大回撤持续时间"""
        max_duration = 0
        current_duration = 0

        for dd in drawdowns:
            if dd > 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_duration

    def _analyze_volatility(
        self,
        returns: np.ndarray,
        price_data: List[Dict] = None
    ) -> VolatilityAnalysis:
        """
        波动率分析
        """
        if len(returns) == 0:
            return VolatilityAnalysis(
                total_volatility=0, upside_volatility=0,
                downside_volatility=0, volatility_ratio=0
            )

        # 总波动率（年化）
        total_vol = float(np.std(returns) * np.sqrt(252))

        # 上行波动率
        positive_returns = returns[returns > 0]
        upside_vol = float(np.std(positive_returns) * np.sqrt(252)) if len(positive_returns) > 1 else 0

        # 下行波动率
        negative_returns = returns[returns < 0]
        downside_vol = float(np.std(negative_returns) * np.sqrt(252)) if len(negative_returns) > 1 else 0

        # 波动率比
        vol_ratio = upside_vol / downside_vol if downside_vol > 0 else 0

        # Parkinson波动率（如果有高低价数据）
        parkinson_vol = 0
        if price_data and len(price_data) > 0:
            parkinson_vol = self._calculate_parkinson_volatility(price_data)

        return VolatilityAnalysis(
            total_volatility=total_vol,
            upside_volatility=upside_vol,
            downside_volatility=downside_vol,
            volatility_ratio=float(vol_ratio),
            parkinson_volatility=parkinson_vol
        )

    def _calculate_parkinson_volatility(self, price_data: List[Dict]) -> float:
        """
        计算Parkinson波动率

        基于日内高低价，对波动率更敏感。
        公式：σ = sqrt(1/(4*n*ln2) * Σ(ln(H/L))^2)
        """
        if not price_data:
            return 0

        hl_logs = []
        for bar in price_data:
            high = bar.get('high', 0)
            low = bar.get('low', 0)
            if high > 0 and low > 0 and high > low:
                hl_logs.append(np.log(high / low) ** 2)

        if not hl_logs:
            return 0

        n = len(hl_logs)
        variance = 1 / (4 * n * np.log(2)) * sum(hl_logs)
        daily_vol = np.sqrt(variance)

        return float(daily_vol * np.sqrt(252))

    def _generate_risk_summary(
        self,
        var_result: VaRResult,
        stress_results: List[StressTestResult],
        risk_decomp: RiskDecomposition,
        downside_risk: DownsideRiskResult,
        volatility: VolatilityAnalysis
    ) -> Dict[str, Any]:
        """生成风险摘要"""
        # 最严重的压力测试情景
        worst_stress = min(stress_results, key=lambda x: x.portfolio_impact) if stress_results else None

        return {
            "key_metrics": {
                "var_95": f"{abs(var_result.var_95):.2%}",
                "cvar_95": f"{abs(var_result.cvar_95):.2%}",
                "max_drawdown": f"{downside_risk.max_drawdown:.2%}",
                "annual_volatility": f"{volatility.total_volatility:.2%}",
            },
            "risk_breakdown": {
                "systematic": f"{risk_decomp.systematic_risk:.2%}",
                "idiosyncratic": f"{risk_decomp.idiosyncratic_risk:.2%}",
                "concentration": f"{risk_decomp.concentration_risk:.2%}",
            },
            "worst_case_scenario": {
                "name": worst_stress.scenario_name if worst_stress else "N/A",
                "impact": f"{worst_stress.portfolio_impact:.2%}" if worst_stress else "N/A",
            } if worst_stress else None,
            "risk_alerts": self._generate_risk_alerts(
                var_result, downside_risk, volatility
            ),
        }

    def _generate_risk_alerts(
        self,
        var_result: VaRResult,
        downside_risk: DownsideRiskResult,
        volatility: VolatilityAnalysis
    ) -> List[str]:
        """生成风险警报"""
        alerts = []

        if abs(var_result.var_95) > 0.05:
            alerts.append("VaR(95%)超过5%，存在较高尾部风险")

        if downside_risk.max_drawdown > 0.3:
            alerts.append("最大回撤超过30%，建议优化止损策略")

        if volatility.total_volatility > 0.3:
            alerts.append("年化波动率超过30%，组合风险较高")

        if volatility.volatility_ratio < 0.5:
            alerts.append("下行波动率显著高于上行波动率，风险收益不对称")

        if downside_risk.recovery_factor < 1:
            alerts.append("恢复因子小于1，回撤恢复能力较弱")

        return alerts

    def _determine_risk_rating(
        self,
        var_result: VaRResult,
        downside_risk: DownsideRiskResult,
        volatility: VolatilityAnalysis
    ) -> str:
        """确定风险评级"""
        risk_score = 0

        # VaR贡献
        if abs(var_result.var_95) > 0.08:
            risk_score += 40
        elif abs(var_result.var_95) > 0.05:
            risk_score += 25
        elif abs(var_result.var_95) > 0.03:
            risk_score += 15
        else:
            risk_score += 5

        # 回撤贡献
        if downside_risk.max_drawdown > 0.4:
            risk_score += 40
        elif downside_risk.max_drawdown > 0.25:
            risk_score += 25
        elif downside_risk.max_drawdown > 0.15:
            risk_score += 15
        else:
            risk_score += 5

        # 波动率贡献
        if volatility.total_volatility > 0.35:
            risk_score += 20
        elif volatility.total_volatility > 0.25:
            risk_score += 15
        elif volatility.total_volatility > 0.15:
            risk_score += 10
        else:
            risk_score += 5

        # 确定评级
        if risk_score >= 80:
            return "Critical"
        elif risk_score >= 60:
            return "High"
        elif risk_score >= 40:
            return "Medium"
        else:
            return "Low"
