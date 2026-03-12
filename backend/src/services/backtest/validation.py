"""
回测验证服务

提供全面的回测验证功能，包括：
- 前视偏差检测（Look-ahead Bias）
- 过拟合检测（Overfitting Detection）
- 数据泄露检测（Data Leakage）
- 样本外测试（Out-of-Sample Testing）
- 幸存者偏差检测（Survivorship Bias）
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
import logging

from .lookahead_guard import LookAheadGuard, ViolationSeverity

logger = logging.getLogger(__name__)


# ==============================================
# 验证结果类型
# ==============================================

class ValidationStatus(str, Enum):
    """验证状态"""
    PASSED = "passed"               # 通过
    WARNING = "warning"             # 警告
    FAILED = "failed"               # 失败
    CRITICAL = "critical"           # 严重失败


class ValidationCategory(str, Enum):
    """验证类别"""
    LOOKAHEAD_BIAS = "lookahead_bias"       # 前视偏差
    OVERFITTING = "overfitting"             # 过拟合
    DATA_LEAKAGE = "data_leakage"           # 数据泄露
    SURVIVORSHIP_BIAS = "survivorship_bias" # 幸存者偏差
    SAMPLE_BIAS = "sample_bias"             # 样本偏差
    STATIONARITY = "stationarity"           # 平稳性


@dataclass
class ValidationResult:
    """验证结果"""
    category: ValidationCategory
    status: ValidationStatus
    score: float  # 0-100，越高越好
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "status": self.status.value,
            "score": self.score,
            "message": self.message,
            "details": self.details,
            "recommendations": self.recommendations,
        }


@dataclass
class BacktestValidationReport:
    """回测验证报告"""
    backtest_id: str
    overall_status: ValidationStatus
    overall_score: float
    validation_results: List[ValidationResult]
    summary: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backtest_id": self.backtest_id,
            "overall_status": self.overall_status.value,
            "overall_score": self.overall_score,
            "validation_results": [r.to_dict() for r in self.validation_results],
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
        }


# ==============================================
# 回测验证服务
# ==============================================

class BacktestValidationService:
    """
    回测验证服务

    提供全面的回测验证功能，确保回测结果的可靠性。
    """

    def __init__(self):
        self.logger = logging.getLogger("BacktestValidationService")

    def validate_backtest(
        self,
        backtest_id: str,
        equity_curve: List[float],
        daily_returns: List[float],
        trades: List[Dict],
        signals: List[Dict] = None,
        in_sample_period: Tuple[date, date] = None,
        out_sample_period: Tuple[date, date] = None,
        benchmark_returns: List[float] = None,
        lookahead_guard: LookAheadGuard = None
    ) -> BacktestValidationReport:
        """
        执行完整的回测验证

        Args:
            backtest_id: 回测ID
            equity_curve: 资金曲线
            daily_returns: 日收益率
            trades: 交易记录
            signals: 信号记录
            in_sample_period: 样本内期间
            out_sample_period: 样本外期间
            benchmark_returns: 基准收益率
            lookahead_guard: 前视偏差守卫

        Returns:
            BacktestValidationReport: 验证报告
        """
        results = []

        # 1. 前视偏差检测
        if lookahead_guard:
            lookahead_result = self._validate_lookahead_bias(lookahead_guard)
            results.append(lookahead_result)

        # 2. 过拟合检测
        if daily_returns and in_sample_period and out_sample_period:
            overfitting_result = self._validate_overfitting(
                daily_returns, in_sample_period, out_sample_period
            )
            results.append(overfitting_result)
        else:
            # 简化的过拟合检测
            overfitting_result = self._validate_overfitting_simple(daily_returns, trades)
            results.append(overfitting_result)

        # 3. 数据泄露检测
        data_leakage_result = self._validate_data_leakage(trades, signals)
        results.append(data_leakage_result)

        # 4. 幸存者偏差检测
        survivorship_result = self._validate_survivorship_bias(trades)
        results.append(survivorship_result)

        # 5. 样本偏差检测
        sample_bias_result = self._validate_sample_bias(daily_returns, benchmark_returns)
        results.append(sample_bias_result)

        # 6. 平稳性检测
        stationarity_result = self._validate_stationarity(daily_returns)
        results.append(stationarity_result)

        # 计算总体状态和分数
        overall_score = np.mean([r.score for r in results])
        overall_status = self._determine_overall_status(results)

        summary = {
            "total_validations": len(results),
            "passed": sum(1 for r in results if r.status == ValidationStatus.PASSED),
            "warnings": sum(1 for r in results if r.status == ValidationStatus.WARNING),
            "failed": sum(1 for r in results if r.status == ValidationStatus.FAILED),
            "critical": sum(1 for r in results if r.status == ValidationStatus.CRITICAL),
        }

        return BacktestValidationReport(
            backtest_id=backtest_id,
            overall_status=overall_status,
            overall_score=overall_score,
            validation_results=results,
            summary=summary
        )

    def _validate_lookahead_bias(self, guard: LookAheadGuard) -> ValidationResult:
        """验证前视偏差"""
        report = guard.generate_report()
        has_critical = report.get("has_critical", False)
        violation_rate = report.get("violation_rate", 0)

        if has_critical:
            status = ValidationStatus.CRITICAL
            score = 0
            message = "检测到严重的前视偏差问题，回测结果不可靠"
        elif violation_rate > 0.1:
            status = ValidationStatus.FAILED
            score = 30
            message = f"前视偏差违规率过高 ({violation_rate:.1%})"
        elif violation_rate > 0.01:
            status = ValidationStatus.WARNING
            score = 70
            message = f"存在少量前视偏差警告 ({violation_rate:.1%})"
        else:
            status = ValidationStatus.PASSED
            score = 100
            message = "未检测到前视偏差问题"

        return ValidationResult(
            category=ValidationCategory.LOOKAHEAD_BIAS,
            status=status,
            score=score,
            message=message,
            details=report,
            recommendations=self._get_lookahead_recommendations(report)
        )

    def _validate_overfitting(
        self,
        daily_returns: List[float],
        in_sample_period: Tuple[date, date],
        out_sample_period: Tuple[date, date]
    ) -> ValidationResult:
        """
        验证过拟合（样本内 vs 样本外）
        """
        # 简化实现：假设已经分好了样本内和样本外
        # 实际应用中需要根据日期分割数据
        returns = np.array(daily_returns)

        # 使用前70%作为样本内，后30%作为样本外
        split_point = int(len(returns) * 0.7)
        in_sample = returns[:split_point]
        out_sample = returns[split_point:]

        if len(in_sample) < 30 or len(out_sample) < 30:
            return ValidationResult(
                category=ValidationCategory.OVERFITTING,
                status=ValidationStatus.WARNING,
                score=50,
                message="数据量不足以进行可靠的过拟合检测",
                details={"in_sample_count": len(in_sample), "out_sample_count": len(out_sample)},
                recommendations=["增加回测数据量"]
            )

        # 计算样本内和样本外的夏普比率
        in_sharpe = self._calculate_sharpe(in_sample)
        out_sharpe = self._calculate_sharpe(out_sample)

        # 计算夏普比率衰减
        if in_sharpe != 0:
            decay_ratio = (in_sharpe - out_sharpe) / abs(in_sharpe)
        else:
            decay_ratio = 0

        details = {
            "in_sample_sharpe": float(in_sharpe),
            "out_sample_sharpe": float(out_sharpe),
            "decay_ratio": float(decay_ratio),
            "in_sample_return": float(np.mean(in_sample) * 252),
            "out_sample_return": float(np.mean(out_sample) * 252),
        }

        if decay_ratio > 0.5:
            status = ValidationStatus.CRITICAL
            score = 20
            message = f"严重过拟合：样本外夏普比率衰减 {decay_ratio:.1%}"
        elif decay_ratio > 0.3:
            status = ValidationStatus.FAILED
            score = 40
            message = f"存在过拟合：样本外夏普比率衰减 {decay_ratio:.1%}"
        elif decay_ratio > 0.1:
            status = ValidationStatus.WARNING
            score = 70
            message = f"轻微过拟合迹象：样本外夏普比率衰减 {decay_ratio:.1%}"
        else:
            status = ValidationStatus.PASSED
            score = 100
            message = "未检测到明显过拟合"

        return ValidationResult(
            category=ValidationCategory.OVERFITTING,
            status=status,
            score=score,
            message=message,
            details=details,
            recommendations=self._get_overfitting_recommendations(decay_ratio)
        )

    def _validate_overfitting_simple(
        self,
        daily_returns: List[float],
        trades: List[Dict]
    ) -> ValidationResult:
        """简化的过拟合检测"""
        if not daily_returns or len(daily_returns) < 30:
            return ValidationResult(
                category=ValidationCategory.OVERFITTING,
                status=ValidationStatus.WARNING,
                score=50,
                message="数据量不足以进行过拟合检测",
                recommendations=["增加回测数据量"]
            )

        returns = np.array(daily_returns)

        # 计算收益分布的正态性
        if len(returns) >= 30:
            _, p_value = stats.normaltest(returns)
            is_normal = p_value > 0.05
        else:
            is_normal = True

        # 计算收益的自相关
        if len(returns) >= 10:
            autocorr = pd.Series(returns).autocorr()
        else:
            autocorr = 0

        # 计算交易次数与收益的关系
        trade_count = len(trades) if trades else 0
        trading_days = len(daily_returns)
        trade_frequency = trade_count / trading_days if trading_days > 0 else 0

        details = {
            "is_normal": is_normal,
            "autocorrelation": float(autocorr) if not np.isnan(autocorr) else 0,
            "trade_frequency": float(trade_frequency),
            "return_skewness": float(stats.skew(returns)),
            "return_kurtosis": float(stats.kurtosis(returns)),
        }

        # 判断过拟合风险
        warnings = []
        score = 100

        if not is_normal:
            warnings.append("收益分布非正态")
            score -= 10

        if abs(autocorr) > 0.3:
            warnings.append(f"收益存在较强自相关 ({autocorr:.2f})")
            score -= 15

        if trade_frequency > 1:
            warnings.append(f"交易频率过高 ({trade_frequency:.1f} 次/天)")
            score -= 10

        # 峰度过高可能意味着尾部风险被低估
        if details["return_kurtosis"] > 5:
            warnings.append("收益分布峰度过高，可能低估尾部风险")
            score -= 10

        if score >= 80:
            status = ValidationStatus.PASSED
            message = "未检测到明显过拟合迹象"
        elif score >= 60:
            status = ValidationStatus.WARNING
            message = f"存在过拟合风险: {'; '.join(warnings)}"
        else:
            status = ValidationStatus.FAILED
            message = f"高风险过拟合: {'; '.join(warnings)}"

        return ValidationResult(
            category=ValidationCategory.OVERFITTING,
            status=status,
            score=max(0, score),
            message=message,
            details=details,
            recommendations=["进行样本外测试", "减少参数数量", "使用交叉验证"]
        )

    def _validate_data_leakage(
        self,
        trades: List[Dict],
        signals: List[Dict] = None
    ) -> ValidationResult:
        """验证数据泄露"""
        leakage_indicators = []
        score = 100

        if not trades:
            return ValidationResult(
                category=ValidationCategory.DATA_LEAKAGE,
                status=ValidationStatus.WARNING,
                score=70,
                message="无交易记录，无法检测数据泄露",
                recommendations=["确保回测生成了交易记录"]
            )

        # 检查交易时间合理性
        trade_times = [t.get("timestamp") or t.get("trade_date") for t in trades]
        if trade_times:
            # 检查是否有周末交易
            weekend_trades = 0
            for t in trade_times:
                if isinstance(t, str):
                    t = datetime.fromisoformat(t.replace("Z", "+00:00"))
                if t.weekday() >= 5:  # 周六或周日
                    weekend_trades += 1

            if weekend_trades > 0:
                leakage_indicators.append(f"发现 {weekend_trades} 笔周末交易")
                score -= 20

        # 检查信号与交易的时间关系
        if signals:
            # 如果信号时间晚于交易时间，可能存在数据泄露
            early_trades = 0
            for trade in trades:
                trade_time = trade.get("timestamp") or trade.get("trade_date")
                if trade_time:
                    for signal in signals:
                        signal_time = signal.get("timestamp") or signal.get("date")
                        if signal_time and trade_time < signal_time:
                            early_trades += 1
                            break

            if early_trades > 0:
                leakage_indicators.append(f"发现 {early_trades} 笔交易早于信号生成")
                score -= 30

        # 检查异常高的胜率
        if trades:
            winning = sum(1 for t in trades if t.get("pnl", 0) > 0)
            win_rate = winning / len(trades)
            if win_rate > 0.8:
                leakage_indicators.append(f"异常高的胜率 ({win_rate:.1%})")
                score -= 25

        if score >= 80:
            status = ValidationStatus.PASSED
            message = "未检测到数据泄露问题"
        elif score >= 60:
            status = ValidationStatus.WARNING
            message = f"可能存在数据泄露: {'; '.join(leakage_indicators)}"
        else:
            status = ValidationStatus.FAILED
            message = f"检测到数据泄露: {'; '.join(leakage_indicators)}"

        return ValidationResult(
            category=ValidationCategory.DATA_LEAKAGE,
            status=status,
            score=max(0, score),
            message=message,
            details={"leakage_indicators": leakage_indicators},
            recommendations=self._get_leakage_recommendations(leakage_indicators)
        )

    def _validate_survivorship_bias(self, trades: List[Dict]) -> ValidationResult:
        """验证幸存者偏差"""
        if not trades:
            return ValidationResult(
                category=ValidationCategory.SURVIVORSHIP_BIAS,
                status=ValidationStatus.WARNING,
                score=70,
                message="无交易记录，无法检测幸存者偏差",
                recommendations=["确保股票池包含已退市股票"]
            )

        # 获取交易过的股票
        symbols = set(t.get("symbol") for t in trades if t.get("symbol"))

        # 简化检测：检查股票代码分布
        # 实际应用中应该检查股票池是否包含已退市股票
        details = {
            "unique_symbols": len(symbols),
            "total_trades": len(trades),
        }

        # 如果股票数量很少，可能存在幸存者偏差
        if len(symbols) < 10:
            status = ValidationStatus.WARNING
            score = 60
            message = f"股票池较小 ({len(symbols)} 只)，可能存在幸存者偏差"
            recommendations = ["扩大股票池范围", "包含已退市股票"]
        elif len(symbols) < 50:
            status = ValidationStatus.WARNING
            score = 75
            message = f"股票池一般 ({len(symbols)} 只)，建议扩大范围"
            recommendations = ["考虑使用全市场股票池"]
        else:
            status = ValidationStatus.PASSED
            score = 90
            message = f"股票池足够大 ({len(symbols)} 只)"
            recommendations = ["确保包含已退市股票以完全避免幸存者偏差"]

        return ValidationResult(
            category=ValidationCategory.SURVIVORSHIP_BIAS,
            status=status,
            score=score,
            message=message,
            details=details,
            recommendations=recommendations
        )

    def _validate_sample_bias(
        self,
        daily_returns: List[float],
        benchmark_returns: List[float] = None
    ) -> ValidationResult:
        """验证样本偏差"""
        if not daily_returns:
            return ValidationResult(
                category=ValidationCategory.SAMPLE_BIAS,
                status=ValidationStatus.WARNING,
                score=50,
                message="无收益数据"
            )

        returns = np.array(daily_returns)

        # 检查样本期间是否包含特殊时期（如牛熊市）
        # 计算收益分布特征
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # 计算正收益比例
        positive_ratio = np.sum(returns > 0) / len(returns)

        # 计算连续正/负收益天数
        consecutive_pos = self._max_consecutive(returns > 0)
        consecutive_neg = self._max_consecutive(returns < 0)

        details = {
            "mean_return": float(mean_return),
            "std_return": float(std_return),
            "positive_ratio": float(positive_ratio),
            "max_consecutive_positive": consecutive_pos,
            "max_consecutive_negative": consecutive_neg,
            "sample_size": len(returns),
        }

        # 与基准对比（如果有）
        if benchmark_returns and len(benchmark_returns) == len(returns):
            benchmark = np.array(benchmark_returns)
            correlation = np.corrcoef(returns, benchmark)[0, 1]
            details["benchmark_correlation"] = float(correlation)

        warnings = []
        score = 100

        # 检查样本量
        if len(returns) < 252:  # 少于一年
            warnings.append(f"样本量较小 ({len(returns)} 天)")
            score -= 15

        # 检查极端收益比例
        if positive_ratio > 0.65 or positive_ratio < 0.35:
            warnings.append(f"正收益比例异常 ({positive_ratio:.1%})")
            score -= 10

        # 检查连续收益
        if consecutive_pos > 20 or consecutive_neg > 20:
            warnings.append(f"存在较长连续涨/跌 ({consecutive_pos}/{consecutive_neg} 天)")
            score -= 10

        if score >= 80:
            status = ValidationStatus.PASSED
            message = "样本分布合理"
        elif score >= 60:
            status = ValidationStatus.WARNING
            message = f"样本可能存在偏差: {'; '.join(warnings)}"
        else:
            status = ValidationStatus.FAILED
            message = f"样本偏差严重: {'; '.join(warnings)}"

        return ValidationResult(
            category=ValidationCategory.SAMPLE_BIAS,
            status=status,
            score=max(0, score),
            message=message,
            details=details,
            recommendations=["延长回测期间", "包含不同市场周期"]
        )

    def _validate_stationarity(self, daily_returns: List[float]) -> ValidationResult:
        """验证平稳性（使用ADF检验）"""
        if not daily_returns or len(daily_returns) < 30:
            return ValidationResult(
                category=ValidationCategory.STATIONARITY,
                status=ValidationStatus.WARNING,
                score=50,
                message="数据量不足以进行平稳性检验"
            )

        returns = np.array(daily_returns)

        try:
            # ADF 检验
            adf_result = stats.adfuller(returns, autolag='AIC')
            adf_statistic = adf_result[0]
            p_value = adf_result[1]

            is_stationary = p_value < 0.05

            details = {
                "adf_statistic": float(adf_statistic),
                "p_value": float(p_value),
                "is_stationary": is_stationary,
            }

            if is_stationary:
                status = ValidationStatus.PASSED
                score = 100
                message = "收益序列平稳，统计特性可靠"
            else:
                status = ValidationStatus.WARNING
                score = 60
                message = f"收益序列非平稳 (p={p_value:.4f})，统计特性可能不可靠"

            return ValidationResult(
                category=ValidationCategory.STATIONARITY,
                status=status,
                score=score,
                message=message,
                details=details,
                recommendations=[] if is_stationary else ["考虑使用差分后的收益", "检查是否存在结构性变化"]
            )

        except Exception as e:
            return ValidationResult(
                category=ValidationCategory.STATIONARITY,
                status=ValidationStatus.WARNING,
                score=70,
                message=f"平稳性检验失败: {str(e)}",
                recommendations=["检查数据质量"]
            )

    def _calculate_sharpe(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0

        annual_return = np.mean(returns) * 252
        annual_std = np.std(returns) * np.sqrt(252)

        if annual_std == 0:
            return 0

        return (annual_return - risk_free_rate) / annual_std

    def _max_consecutive(self, condition: np.ndarray) -> int:
        """计算最大连续满足条件的天数"""
        max_count = 0
        current_count = 0

        for c in condition:
            if c:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count

    def _determine_overall_status(self, results: List[ValidationResult]) -> ValidationStatus:
        """确定总体状态"""
        if any(r.status == ValidationStatus.CRITICAL for r in results):
            return ValidationStatus.CRITICAL
        elif any(r.status == ValidationStatus.FAILED for r in results):
            return ValidationStatus.FAILED
        elif any(r.status == ValidationStatus.WARNING for r in results):
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.PASSED

    def _get_lookahead_recommendations(self, report: Dict) -> List[str]:
        """获取前视偏差修复建议"""
        recommendations = []

        by_type = report.get("by_type", {})

        if by_type.get("future_price", 0) > 0:
            recommendations.append("确保交易决策不使用当日收盘价")

        if by_type.get("future_financial", 0) > 0:
            recommendations.append("使用财务数据时考虑披露延迟")

        if by_type.get("adjusted_price", 0) > 0:
            recommendations.append("避免使用复权价格，或使用实时复权")

        if not recommendations:
            recommendations.append("继续保持良好的数据访问规范")

        return recommendations

    def _get_overfitting_recommendations(self, decay_ratio: float) -> List[str]:
        """获取过拟合修复建议"""
        if decay_ratio > 0.3:
            return [
                "减少策略参数数量",
                "使用交叉验证进行参数选择",
                "增加样本外测试期间",
                "考虑使用正则化方法",
            ]
        elif decay_ratio > 0.1:
            return [
                "进行样本外测试验证",
                "监控实盘表现与回测差异",
            ]
        else:
            return ["继续保持当前的参数管理方式"]

    def _get_leakage_recommendations(self, indicators: List[str]) -> List[str]:
        """获取数据泄露修复建议"""
        recommendations = []

        for indicator in indicators:
            if "周末" in indicator:
                recommendations.append("检查交易日历，排除非交易日")
            elif "信号" in indicator:
                recommendations.append("确保交易时间晚于信号生成时间")
            elif "胜率" in indicator:
                recommendations.append("检查策略逻辑是否存在未来函数")

        if not recommendations:
            recommendations.append("继续保持良好的数据管理规范")

        return recommendations
