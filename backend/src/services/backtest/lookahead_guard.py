"""
防未来函数检查模块

提供回测过程中的未来函数检测功能，确保策略不会使用未来的数据。

核心概念：
- 未来函数：在时刻 T 使用了 T+1 时刻才能获得的数据
- 常见未来函数陷阱：
  - 使用当日收盘价做当日决策
  - 使用复权后的价格（复权需要未来数据）
  - 使用财务数据时未考虑披露延迟
  - 使用指数/行业数据时未考虑发布延迟

检测方法：
- 数据访问时间戳检查
- 指标计算窗口检查
- 财务数据披露日期检查
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import logging
import inspect
import traceback

logger = logging.getLogger(__name__)


# ==============================================
# 违规类型枚举
# ==============================================

class ViolationType(str, Enum):
    """违规类型"""
    FUTURE_PRICE = "future_price"               # 使用未来价格
    FUTURE_VOLUME = "future_volume"             # 使用未来成交量
    FUTURE_INDICATOR = "future_indicator"       # 使用未来指标值
    FUTURE_FINANCIAL = "future_financial"       # 使用未来财务数据
    FUTURE_CORPORATE_ACTION = "future_action"   # 使用未来公司行动
    ADJUSTED_PRICE = "adjusted_price"           # 使用复权价格（隐含未来数据）
    LOOKAHEAD_BIAS = "lookahead_bias"           # 一般性未来函数


class ViolationSeverity(str, Enum):
    """违规严重程度"""
    WARNING = "warning"     # 警告（可能存在问题）
    ERROR = "error"         # 错误（确定存在问题）
    CRITICAL = "critical"   # 严重（会导致回测结果无效）


# ==============================================
# 违规记录
# ==============================================

@dataclass
class LookAheadViolation:
    """
    未来函数违规记录

    记录一次检测到的未来函数使用情况。
    """
    violation_type: ViolationType              # 违规类型
    severity: ViolationSeverity                # 严重程度
    timestamp: datetime                        # 当前回测时间
    data_timestamp: datetime                   # 被访问数据的时间戳
    message: str                               # 违规信息
    symbol: str = ""                           # 相关股票代码
    strategy_id: str = ""                      # 相关策略 ID
    source_location: str = ""                  # 源代码位置
    stack_trace: str = ""                      # 调用栈
    context: Dict[str, Any] = field(default_factory=dict)  # 额外上下文

    def __str__(self) -> str:
        return (
            f"[{self.severity.value.upper()}] {self.violation_type.value}: "
            f"{self.message} (当前时间: {self.timestamp}, 数据时间: {self.data_timestamp})"
        )


# ==============================================
# 数据访问记录
# ==============================================

@dataclass
class DataAccessRecord:
    """
    数据访问记录

    记录策略对数据的访问情况。
    """
    access_time: datetime          # 访问时间（回测当前时间）
    data_time: datetime            # 数据时间戳
    symbol: str                    # 股票代码
    data_type: str                 # 数据类型（price/volume/indicator/financial）
    field: str = ""                # 字段名
    value: Any = None              # 访问的值
    is_valid: bool = True          # 是否有效（非未来函数）


# ==============================================
# 防未来函数守卫
# ==============================================

class LookAheadGuard:
    """
    防未来函数守卫

    在回测过程中监控策略的数据访问，检测并报告未来函数使用。

    使用方式：
        guard = LookAheadGuard()

        # 在回测循环中
        for current_date in backtest_dates:
            guard.set_current_time(current_date)

            # 策略访问数据时检查
            if guard.check_data_access(data_time, symbol):
                # 允许访问
                data = get_data(symbol, data_time)
            else:
                # 拒绝访问或记录违规
                guard.report_violation(...)

        # 获取报告
        report = guard.generate_report()

    检测规则：
    1. 价格数据：不能访问当前时间之后的价格
    2. 成交量数据：不能访问当前时间之后的成交量
    3. 财务数据：需要考虑披露延迟（通常季度报告有 1-2 个月延迟）
    4. 指标数据：检查指标计算窗口是否包含未来数据
    5. 复权价格：前复权/后复权都隐含使用未来数据
    """

    def __init__(
        self,
        strict_mode: bool = True,
        financial_disclosure_delay: int = 45,  # 财务数据披露延迟（天）
        max_violations: int = 1000             # 最大记录违规数
    ):
        """
        初始化防未来函数守卫

        Args:
            strict_mode: 严格模式（更严格的检查）
            financial_disclosure_delay: 财务数据披露延迟天数
            max_violations: 最大记录违规数
        """
        self._current_time: Optional[datetime] = None
        self._strict_mode = strict_mode
        self._financial_disclosure_delay = financial_disclosure_delay
        self._max_violations = max_violations

        # 违规记录
        self._violations: List[LookAheadViolation] = []

        # 数据访问记录
        self._access_records: List[DataAccessRecord] = []

        # 财务数据披露日期缓存
        # {symbol: {period_end_date: disclosure_date}}
        self._disclosure_dates: Dict[str, Dict[date, date]] = {}

        # 统计
        self._total_checks = 0
        self._total_violations = 0

        self.logger = logging.getLogger("LookAheadGuard")

    # ==========================================
    # 时间管理
    # ==========================================

    def set_current_time(self, time: datetime) -> None:
        """
        设置当前回测时间

        Args:
            time: 当前时间
        """
        self._current_time = time
        self.logger.debug(f"设置当前时间: {time}")

    def get_current_time(self) -> Optional[datetime]:
        """获取当前回测时间"""
        return self._current_time

    # ==========================================
    # 数据访问检查
    # ==========================================

    def check_data_access(
        self,
        data_time: datetime,
        symbol: str = "",
        data_type: str = "price",
        field: str = ""
    ) -> bool:
        """
        检查数据访问是否有效

        Args:
            data_time: 数据时间戳
            symbol: 股票代码
            data_type: 数据类型
            field: 字段名

        Returns:
            是否有效（非未来函数）
        """
        self._total_checks += 1

        if self._current_time is None:
            self.logger.warning("未设置当前时间，跳过检查")
            return True

        is_valid = True
        violation_type = None
        message = ""

        # 检查数据时间是否晚于当前时间
        if data_time > self._current_time:
            is_valid = False
            violation_type = ViolationType.LOOKAHEAD_BIAS
            message = f"访问未来数据: 数据时间 {data_time} 晚于当前时间 {self._current_time}"

        # 根据数据类型进行特定检查
        if data_type == "price":
            is_valid = self._check_price_access(data_time, symbol, field)

        elif data_type == "volume":
            is_valid = self._check_volume_access(data_time, symbol)

        elif data_type == "financial":
            is_valid = self._check_financial_access(data_time, symbol)

        elif data_type == "indicator":
            is_valid = self._check_indicator_access(data_time, symbol, field)

        # 记录访问
        record = DataAccessRecord(
            access_time=self._current_time,
            data_time=data_time,
            symbol=symbol,
            data_type=data_type,
            field=field,
            is_valid=is_valid
        )
        self._access_records.append(record)

        return is_valid

    def _check_price_access(
        self,
        data_time: datetime,
        symbol: str,
        field: str
    ) -> bool:
        """
        检查价格数据访问

        规则：
        - 日内数据：不能访问当日的收盘价
        - 日线数据：当日收盘前不能访问当日收盘价

        Args:
            data_time: 数据时间
            symbol: 股票代码
            field: 字段名

        Returns:
            是否有效
        """
        if self._current_time is None:
            return True

        # 检查是否是当日数据
        if data_time.date() > self._current_time.date():
            self._report_violation(
                ViolationType.FUTURE_PRICE,
                ViolationSeverity.ERROR,
                f"访问未来价格数据: {symbol} {field}",
                symbol=symbol,
                data_time=data_time
            )
            return False

        # 严格模式下，检查当日收盘价
        if self._strict_mode and data_time.date() == self._current_time.date():
            # 如果当前时间早于收盘时间（15:00），不能访问收盘价
            market_close = self._current_time.replace(hour=15, minute=0, second=0)
            if self._current_time < market_close and field == "close":
                self._report_violation(
                    ViolationType.FUTURE_PRICE,
                    ViolationSeverity.WARNING,
                    f"在收盘前访问当日收盘价: {symbol}",
                    symbol=symbol,
                    data_time=data_time
                )
                # 警告但不阻止

        return True

    def _check_volume_access(
        self,
        data_time: datetime,
        symbol: str
    ) -> bool:
        """
        检查成交量数据访问

        规则：
        - 不能访问未来成交量

        Args:
            data_time: 数据时间
            symbol: 股票代码

        Returns:
            是否有效
        """
        if self._current_time is None:
            return True

        if data_time > self._current_time:
            self._report_violation(
                ViolationType.FUTURE_VOLUME,
                ViolationSeverity.ERROR,
                f"访问未来成交量数据: {symbol}",
                symbol=symbol,
                data_time=data_time
            )
            return False

        return True

    def _check_financial_access(
        self,
        data_time: datetime,
        symbol: str
    ) -> bool:
        """
        检查财务数据访问

        规则：
        - 需要考虑财务报告的披露延迟
        - 季度报告通常有 1-2 个月的披露延迟

        Args:
            data_time: 财务数据对应的报告期
            symbol: 股票代码

        Returns:
            是否有效
        """
        if self._current_time is None:
            return True

        # 计算披露日期（报告期结束后 N 天）
        disclosure_date = data_time + timedelta(days=self._financial_disclosure_delay)

        if disclosure_date > self._current_time:
            self._report_violation(
                ViolationType.FUTURE_FINANCIAL,
                ViolationSeverity.ERROR,
                f"访问未披露的财务数据: {symbol}, 报告期 {data_time.date()}, 披露日期 {disclosure_date.date()}",
                symbol=symbol,
                data_time=data_time
            )
            return False

        return True

    def _check_indicator_access(
        self,
        data_time: datetime,
        symbol: str,
        indicator_name: str
    ) -> bool:
        """
        检查指标数据访问

        规则：
        - 指标计算不能使用未来数据
        - 指标的值应该在当前时间可计算

        Args:
            data_time: 指标值的时间
            symbol: 股票代码
            indicator_name: 指标名称

        Returns:
            是否有效
        """
        if self._current_time is None:
            return True

        if data_time > self._current_time:
            self._report_violation(
                ViolationType.FUTURE_INDICATOR,
                ViolationSeverity.ERROR,
                f"访问未来指标值: {symbol} {indicator_name}",
                symbol=symbol,
                data_time=data_time
            )
            return False

        return True

    # ==========================================
    # 指标计算验证
    # ==========================================

    def validate_indicator_calculation(
        self,
        indicator_name: str,
        required_data: List[datetime],
        symbol: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        验证指标计算是否使用未来数据

        Args:
            indicator_name: 指标名称
            required_data: 计算指标所需的数据时间戳列表
            symbol: 股票代码

        Returns:
            (是否有效, 错误信息)
        """
        if self._current_time is None:
            return True, None

        future_data = [t for t in required_data if t > self._current_time]

        if future_data:
            error_msg = (
                f"指标 {indicator_name} 计算需要未来数据: "
                f"{len(future_data)} 个数据点晚于当前时间 {self._current_time}"
            )
            self._report_violation(
                ViolationType.FUTURE_INDICATOR,
                ViolationSeverity.ERROR,
                error_msg,
                symbol=symbol,
                data_time=min(future_data)
            )
            return False, error_msg

        return True, None

    def check_adjusted_price(
        self,
        symbol: str,
        adjustment_type: str
    ) -> bool:
        """
        检查复权价格使用

        复权价格隐含使用未来数据（因为复权因子需要未来的公司行动信息）。

        Args:
            symbol: 股票代码
            adjustment_type: 复权类型（qfq/hfq）

        Returns:
            是否有效
        """
        if adjustment_type in ["qfq", "hfq"]:
            self._report_violation(
                ViolationType.ADJUSTED_PRICE,
                ViolationSeverity.WARNING,
                f"使用复权价格（{adjustment_type}）可能隐含未来数据: {symbol}",
                symbol=symbol,
                data_time=self._current_time or datetime.now()
            )
            # 警告但不阻止
            return True

        return True

    # ==========================================
    # 违规报告
    # ==========================================

    def _report_violation(
        self,
        violation_type: ViolationType,
        severity: ViolationSeverity,
        message: str,
        symbol: str = "",
        data_time: datetime = None
    ) -> None:
        """
        内部违规报告方法

        Args:
            violation_type: 违规类型
            severity: 严重程度
            message: 违规信息
            symbol: 股票代码
            data_time: 数据时间
        """
        self._total_violations += 1

        if len(self._violations) >= self._max_violations:
            self.logger.warning("违规记录已达上限，跳过记录")
            return

        # 获取调用栈
        stack = traceback.extract_stack()

        violation = LookAheadViolation(
            violation_type=violation_type,
            severity=severity,
            timestamp=self._current_time or datetime.now(),
            data_timestamp=data_time or datetime.now(),
            message=message,
            symbol=symbol,
            source_location=str(stack[-3]) if len(stack) > 3 else "",
            stack_trace="".join(traceback.format_stack()[-5:-1])
        )

        self._violations.append(violation)

        # 根据严重程度记录日志
        if severity == ViolationSeverity.CRITICAL:
            self.logger.critical(str(violation))
        elif severity == ViolationSeverity.ERROR:
            self.logger.error(str(violation))
        else:
            self.logger.warning(str(violation))

    def report_violation(
        self,
        violation_type: ViolationType,
        message: str,
        severity: ViolationSeverity = ViolationSeverity.ERROR,
        symbol: str = "",
        data_time: datetime = None,
        context: Dict[str, Any] = None
    ) -> None:
        """
        外部违规报告接口

        Args:
            violation_type: 违规类型
            message: 违规信息
            severity: 严重程度
            symbol: 股票代码
            data_time: 数据时间
            context: 额外上下文
        """
        self._report_violation(
            violation_type=violation_type,
            severity=severity,
            message=message,
            symbol=symbol,
            data_time=data_time
        )

        if context and self._violations:
            self._violations[-1].context = context

    # ==========================================
    # 报告生成
    # ==========================================

    def get_violations(
        self,
        severity: ViolationSeverity = None,
        violation_type: ViolationType = None
    ) -> List[LookAheadViolation]:
        """
        获取违规记录

        Args:
            severity: 按严重程度过滤
            violation_type: 按类型过滤

        Returns:
            违规记录列表
        """
        violations = self._violations

        if severity:
            violations = [v for v in violations if v.severity == severity]

        if violation_type:
            violations = [v for v in violations if v.violation_type == violation_type]

        return violations

    def get_violation_count(self) -> int:
        """获取违规总数"""
        return self._total_violations

    def has_critical_violations(self) -> bool:
        """是否有严重违规"""
        return any(
            v.severity == ViolationSeverity.CRITICAL
            for v in self._violations
        )

    def generate_report(self) -> Dict[str, Any]:
        """
        生成检查报告

        Returns:
            报告字典
        """
        # 按类型统计
        type_counts: Dict[ViolationType, int] = {}
        for v in self._violations:
            type_counts[v.violation_type] = type_counts.get(v.violation_type, 0) + 1

        # 按严重程度统计
        severity_counts: Dict[ViolationSeverity, int] = {}
        for v in self._violations:
            severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1

        # 按股票统计
        symbol_counts: Dict[str, int] = {}
        for v in self._violations:
            if v.symbol:
                symbol_counts[v.symbol] = symbol_counts.get(v.symbol, 0) + 1

        return {
            "summary": {
                "total_checks": self._total_checks,
                "total_violations": self._total_violations,
                "violation_rate": self._total_violations / self._total_checks if self._total_checks > 0 else 0,
                "has_critical": self.has_critical_violations(),
            },
            "by_type": {t.value: c for t, c in type_counts.items()},
            "by_severity": {s.value: c for s, c in severity_counts.items()},
            "by_symbol": symbol_counts,
            "violations": [
                {
                    "type": v.violation_type.value,
                    "severity": v.severity.value,
                    "timestamp": v.timestamp.isoformat(),
                    "data_timestamp": v.data_timestamp.isoformat(),
                    "message": v.message,
                    "symbol": v.symbol,
                }
                for v in self._violations[-100:]  # 只返回最近 100 条
            ],
            "is_valid": not self.has_critical_violations(),
        }

    def clear(self) -> None:
        """清除所有记录"""
        self._violations.clear()
        self._access_records.clear()
        self._total_checks = 0
        self._total_violations = 0


# ==============================================
# 上下文管理器
# ==============================================

class LookAheadGuardContext:
    """
    防未来函数守卫上下文管理器

    用于在特定代码块中启用防未来函数检查。

    使用示例：
        with LookAheadGuardContext(guard, current_time) as ctx:
            # 在此代码块中的数据访问会被检查
            data = strategy.on_data(context)
    """

    def __init__(
        self,
        guard: LookAheadGuard,
        current_time: datetime
    ):
        self.guard = guard
        self.current_time = current_time

    def __enter__(self) -> 'LookAheadGuardContext':
        self.guard.set_current_time(self.current_time)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.guard.set_current_time(None)
