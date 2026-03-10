"""
数据对齐与复权模块

提供数据对齐、时间戳处理和复权计算功能：
- 时间戳对齐（多频率数据对齐）
- 前复权/后复权计算
- 公司行动处理（分红、送股、配股）
- 数据重采样

复权说明：
- 前复权(qfq): 保持当前价格不变，调整历史价格
- 后复权(hfq): 保持上市价格不变，调整当前价格
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from dataclasses import dataclass
import logging

from .engine import CorporateAction, DataFrequency

logger = logging.getLogger(__name__)


# ==============================================
# 复权计算器
# ==============================================

class AdjustmentCalculator:
    """
    复权计算器

    根据公司行动计算复权因子和复权价格。

    复权公式：
    - 前复权价格 = 原价格 × 复权因子
    - 后复权价格 = 原价格 × 累计复权因子

    复权因子计算（每单位）：
    - 送股: 每股增加 bonus_per_share 股
    - 转增: 每股增加 transfer_per_share 股
    - 配股: 每股增加 rights_per_share 股（需要支付配股价）
    - 分红: 每股减少 dividend_per_share 现金
    """

    def __init__(self):
        self.logger = logging.getLogger("AdjustmentCalculator")

    def calculate_adjustment_factor(
        self,
        action: CorporateAction,
        close_price_before: Decimal
    ) -> Decimal:
        """
        计算单次公司行动的复权因子

        Args:
            action: 公司行动
            close_price_before: 除权除息前收盘价

        Returns:
            复权因子
        """
        if close_price_before <= 0:
            return Decimal("1")

        # 计算除权除息价
        # 除权价 = (收盘价 - 每股分红 + 配股价 × 配股比例) / (1 + 送股比例 + 转增比例 + 配股比例)

        total_new_shares = (
            action.bonus_per_share +
            action.transfer_per_share +
            action.rights_per_share
        )

        adjusted_price_numerator = (
            close_price_before -
            action.dividend_per_share +
            action.rights_price * action.rights_per_share
        )

        if total_new_shares > 0:
            ex_right_price = adjusted_price_numerator / (1 + total_new_shares)
        else:
            ex_right_price = adjusted_price_numerator

        # 复权因子 = 除权价 / 原价
        factor = ex_right_price / close_price_before

        return factor

    def calculate_cumulative_factors(
        self,
        actions: List[CorporateAction],
        price_series: List[Dict[str, Any]],
        adjustment_type: str = "qfq"
    ) -> Dict[date, Decimal]:
        """
        计算累积复权因子

        Args:
            actions: 公司行动列表（按时间升序）
            price_series: 价格序列（每条包含 date 和 close）
            adjustment_type: 复权类型（qfq/hfq）

        Returns:
            {date: 累积复权因子}
        """
        if not actions or not price_series:
            return {}

        # 构建日期到收盘价的映射
        price_map = {}
        for bar in price_series:
            bar_date = bar.get("timestamp") or bar.get("date")
            if isinstance(bar_date, datetime):
                bar_date = bar_date.date()
            if bar_date:
                price_map[bar_date] = Decimal(str(bar.get("close", 0)))

        # 按除权日排序
        sorted_actions = sorted(actions, key=lambda x: x.ex_date)

        # 计算每次行动的复权因子
        action_factors = []
        for action in sorted_actions:
            if action.ex_date is None:
                continue

            # 找到除权日前一个交易日的收盘价
            prev_close = self._find_previous_price(price_map, action.ex_date)

            if prev_close and prev_close > 0:
                factor = self.calculate_adjustment_factor(action, prev_close)
                action_factors.append((action.ex_date, factor))

        if not action_factors:
            return {}

        # 计算累积因子
        cumulative_factors = {}

        if adjustment_type == "qfq":
            # 前复权：从最新日期往前累积
            # 当前日期因子为 1，越早的日期因子越小（价格被调低）
            cumulative = Decimal("1")

            for ex_date, factor in reversed(action_factors):
                cumulative = cumulative * factor
                cumulative_factors[ex_date] = cumulative

            # 最新日期因子为 1
            max_date = max(action_factors, key=lambda x: x[0])[0] if action_factors else date.today()
            cumulative_factors[max_date] = Decimal("1")

        else:  # hfq
            # 后复权：从最早日期往后累积
            # 上市日因子为 1，越晚的日期因子越大（价格被调高）
            cumulative = Decimal("1")

            for ex_date, factor in action_factors:
                cumulative_factors[ex_date] = cumulative
                cumulative = cumulative / factor  # 后复权是前复权的逆运算

        return cumulative_factors

    def _find_previous_price(
        self,
        price_map: Dict[date, Decimal],
        target_date: date
    ) -> Optional[Decimal]:
        """
        查找目标日期之前的最近收盘价

        Args:
            price_map: 日期到价格的映射
            target_date: 目标日期

        Returns:
            收盘价或 None
        """
        # 往前查找最多 10 天
        for i in range(1, 11):
            check_date = target_date - timedelta(days=i)
            if check_date in price_map:
                return price_map[check_date]
        return None


# ==============================================
# 数据对齐器
# ==============================================

class DataAligner:
    """
    数据对齐器

    提供数据对齐、重采样和复权功能。
    """

    def __init__(self):
        self.adjustment_calculator = AdjustmentCalculator()
        self.logger = logging.getLogger("DataAligner")

    def align_timestamps(
        self,
        data: List[Dict[str, Any]],
        frequency: DataFrequency,
        timezone: str = "Asia/Shanghai"
    ) -> List[Dict[str, Any]]:
        """
        对齐时间戳

        将数据时间戳对齐到指定频率的边界。

        Args:
            data: 原始数据
            frequency: 目标频率
            timezone: 时区

        Returns:
            对齐后的数据
        """
        if not data:
            return data

        result = []
        for bar in data:
            ts = bar.get("timestamp")
            if ts is None:
                continue

            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)

            # 对齐到频率边界
            aligned_ts = self._align_to_frequency(ts, frequency)

            new_bar = bar.copy()
            new_bar["timestamp"] = aligned_ts
            result.append(new_bar)

        return result

    def _align_to_frequency(
        self,
        ts: datetime,
        frequency: DataFrequency
    ) -> datetime:
        """
        将时间戳对齐到频率边界

        Args:
            ts: 原始时间戳
            frequency: 频率

        Returns:
            对齐后的时间戳
        """
        if frequency in [DataFrequency.DAY, DataFrequency.WEEK, DataFrequency.MONTH]:
            # 日线及以上：对齐到日期开始
            return ts.replace(hour=0, minute=0, second=0, microsecond=0)

        elif frequency == DataFrequency.HOUR_1:
            return ts.replace(minute=0, second=0, microsecond=0)

        elif frequency == DataFrequency.HOUR_4:
            # 4小时对齐
            hour = (ts.hour // 4) * 4
            return ts.replace(hour=hour, minute=0, second=0, microsecond=0)

        elif frequency == DataFrequency.MIN_30:
            minute = (ts.minute // 30) * 30
            return ts.replace(minute=minute, second=0, microsecond=0)

        elif frequency == DataFrequency.MIN_15:
            minute = (ts.minute // 15) * 15
            return ts.replace(minute=minute, second=0, microsecond=0)

        elif frequency == DataFrequency.MIN_5:
            minute = (ts.minute // 5) * 5
            return ts.replace(minute=minute, second=0, microsecond=0)

        elif frequency == DataFrequency.MIN_1:
            return ts.replace(second=0, microsecond=0)

        else:
            return ts

    def resample(
        self,
        data: List[Dict[str, Any]],
        target_frequency: DataFrequency,
        source_frequency: DataFrequency = DataFrequency.MIN_1
    ) -> List[Dict[str, Any]]:
        """
        重采样数据

        将低频数据聚合为高频数据（如分钟线 -> 日线）。

        Args:
            data: 原始数据
            target_frequency: 目标频率
            source_frequency: 源频率

        Returns:
            重采样后的数据
        """
        if not data:
            return data

        # 按时间排序
        sorted_data = sorted(data, key=lambda x: x.get("timestamp", datetime.min))

        # 根据目标频率分组
        groups: Dict[Any, List[Dict]] = {}

        for bar in sorted_data:
            ts = bar.get("timestamp")
            if ts is None:
                continue

            # 计算分组键
            group_key = self._get_group_key(ts, target_frequency)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(bar)

        # 聚合每组数据
        result = []
        for group_key, bars in groups.items():
            if not bars:
                continue

            # 开盘价取第一个，收盘价取最后一个
            # 最高价取最大值，最低价取最小值
            # 成交量、成交额求和
            aggregated = {
                "symbol": bars[0].get("symbol"),
                "timestamp": bars[0].get("timestamp"),  # 使用组内第一个时间戳
                "open": Decimal(str(bars[0].get("open", 0))),
                "high": max(Decimal(str(b.get("high", 0))) for b in bars),
                "low": min(Decimal(str(b.get("low", 0))) for b in bars),
                "close": Decimal(str(bars[-1].get("close", 0))),
                "volume": sum(int(b.get("volume", 0)) for b in bars),
                "amount": sum(Decimal(str(b.get("amount", 0))) for b in bars),
            }

            result.append(aggregated)

        return sorted(result, key=lambda x: x.get("timestamp", datetime.min))

    def _get_group_key(self, ts: datetime, frequency: DataFrequency) -> Any:
        """
        获取分组键

        Args:
            ts: 时间戳
            frequency: 频率

        Returns:
            分组键
        """
        if frequency == DataFrequency.MIN_1:
            return ts.replace(second=0, microsecond=0)
        elif frequency == DataFrequency.MIN_5:
            return ts.replace(minute=(ts.minute // 5) * 5, second=0, microsecond=0)
        elif frequency == DataFrequency.MIN_15:
            return ts.replace(minute=(ts.minute // 15) * 15, second=0, microsecond=0)
        elif frequency == DataFrequency.MIN_30:
            return ts.replace(minute=(ts.minute // 30) * 30, second=0, microsecond=0)
        elif frequency == DataFrequency.HOUR_1:
            return ts.replace(minute=0, second=0, microsecond=0)
        elif frequency == DataFrequency.HOUR_4:
            return (ts.date(), ts.hour // 4)
        elif frequency == DataFrequency.DAY:
            return ts.date()
        elif frequency == DataFrequency.WEEK:
            # 使用周一的日期作为周标识
            monday = ts.date() - timedelta(days=ts.weekday())
            return monday
        elif frequency == DataFrequency.MONTH:
            return (ts.year, ts.month)
        else:
            return ts

    def forward_adjust(
        self,
        data: List[Dict[str, Any]],
        actions: List[CorporateAction]
    ) -> List[Dict[str, Any]]:
        """
        前复权处理

        保持当前价格不变，调整历史价格。

        Args:
            data: 原始价格数据
            actions: 公司行动列表

        Returns:
            前复权后的数据
        """
        return self._apply_adjustment(data, actions, "qfq")

    def backward_adjust(
        self,
        data: List[Dict[str, Any]],
        actions: List[CorporateAction]
    ) -> List[Dict[str, Any]]:
        """
        后复权处理

        保持上市价格不变，调整当前价格。

        Args:
            data: 原始价格数据
            actions: 公司行动列表

        Returns:
            后复权后的数据
        """
        return self._apply_adjustment(data, actions, "hfq")

    def _apply_adjustment(
        self,
        data: List[Dict[str, Any]],
        actions: List[CorporateAction],
        adjustment_type: str
    ) -> List[Dict[str, Any]]:
        """
        应用复权

        Args:
            data: 原始数据
            actions: 公司行动
            adjustment_type: 复权类型

        Returns:
            复权后的数据
        """
        if not data or not actions:
            return data

        # 计算累积复权因子
        cumulative_factors = self.adjustment_calculator.calculate_cumulative_factors(
            actions, data, adjustment_type
        )

        if not cumulative_factors:
            return data

        # 按除权日排序
        sorted_dates = sorted(cumulative_factors.keys())

        result = []
        for bar in data:
            ts = bar.get("timestamp")
            if ts is None:
                result.append(bar)
                continue

            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)

            bar_date = ts.date() if isinstance(ts, datetime) else ts

            # 找到适用的复权因子
            factor = Decimal("1")
            for ex_date in sorted_dates:
                if ex_date <= bar_date:
                    factor = cumulative_factors[ex_date]
                else:
                    break

            # 应用复权因子
            new_bar = bar.copy()
            for field in ["open", "high", "low", "close"]:
                if field in new_bar:
                    new_bar[field] = Decimal(str(new_bar[field])) * factor

            result.append(new_bar)

        return result

    def adjust_for_corporate_actions(
        self,
        data: List[Dict[str, Any]],
        actions: List[CorporateAction],
        adjustment_type: str = "qfq"
    ) -> List[Dict[str, Any]]:
        """
        处理公司行动（复权）

        统一的复权入口。

        Args:
            data: 原始数据
            actions: 公司行动
            adjustment_type: 复权类型（none/qfq/hfq）

        Returns:
            处理后的数据
        """
        if adjustment_type == "none" or not actions:
            return data

        if adjustment_type == "qfq":
            return self.forward_adjust(data, actions)
        elif adjustment_type == "hfq":
            return self.backward_adjust(data, actions)
        else:
            return data

    def align_multiple_series(
        self,
        series_dict: Dict[str, List[Dict[str, Any]]],
        reference_dates: List[date] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        对齐多个数据序列

        确保所有序列具有相同的日期索引。

        Args:
            series_dict: {symbol: data}
            reference_dates: 参考日期列表（如果为 None 则使用并集）

        Returns:
            对齐后的数据字典
        """
        if not series_dict:
            return series_dict

        # 收集所有日期
        all_dates = set()
        symbol_dates: Dict[str, set] = {}

        for symbol, data in series_dict.items():
            dates = set()
            for bar in data:
                ts = bar.get("timestamp")
                if ts is None:
                    continue
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                if isinstance(ts, datetime):
                    bar_date = ts.date()
                else:
                    bar_date = ts
                dates.add(bar_date)
                all_dates.add(bar_date)
            symbol_dates[symbol] = dates

        # 确定参考日期
        if reference_dates:
            target_dates = set(reference_dates)
        else:
            target_dates = all_dates

        # 对齐每个序列
        result = {}
        for symbol, data in series_dict.items():
            # 创建日期到数据的映射
            date_to_bar = {}
            for bar in data:
                ts = bar.get("timestamp")
                if ts is None:
                    continue
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                if isinstance(ts, datetime):
                    bar_date = ts.date()
                else:
                    bar_date = ts
                date_to_bar[bar_date] = bar

            # 只保留目标日期的数据
            aligned = []
            for target_date in sorted(target_dates):
                if target_date in date_to_bar:
                    aligned.append(date_to_bar[target_date])

            result[symbol] = aligned

        return result
