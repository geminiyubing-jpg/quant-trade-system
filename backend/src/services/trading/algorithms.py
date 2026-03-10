"""
算法交易模块

提供多种算法交易策略：
- TWAP (Time-Weighted Average Price): 时间加权均价
- VWAP (Volume-Weighted Average Price): 成交量加权均价
- POV (Percentage of Volume): 参与率
- Iceberg: 冰山订单

设计目标：
- 减少大单对市场的冲击
- 隐藏真实交易意图
- 获得更好的执行价格
"""

from typing import Dict, List, Optional, Any, Callable, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from decimal import Decimal
from enum import Enum
import asyncio
import logging
import math
import uuid

logger = logging.getLogger(__name__)


# ==============================================
# 枚举类型
# ==============================================

class AlgoType(str, Enum):
    """算法类型"""
    TWAP = "TWAP"           # 时间加权均价
    VWAP = "VWAP"           # 成交量加权均价
    POV = "POV"             # 参与率
    ICEBERG = "ICEBERG"     # 冰山订单
    IS = "IMPLEMENTATION_SHORTFALL"  # 执行落差
    CUSTOM = "CUSTOM"       # 自定义


class AlgoStatus(str, Enum):
    """算法状态"""
    PENDING = "PENDING"           # 待执行
    RUNNING = "RUNNING"           # 执行中
    PAUSED = "PAUSED"             # 已暂停
    COMPLETED = "COMPLETED"       # 已完成
    CANCELLED = "CANCELLED"       # 已取消
    ERROR = "ERROR"               # 错误


# ==============================================
# 数据类
# ==============================================

@dataclass
class AlgoOrder:
    """
    算法订单

    封装算法交易订单的完整信息。
    """
    algo_id: str                              # 算法订单 ID
    algo_type: AlgoType                       # 算法类型
    symbol: str                               # 股票代码
    side: str                                 # 买卖方向
    total_quantity: int                       # 总数量
    filled_quantity: int = 0                  # 已成交数量
    avg_price: Decimal = Decimal("0")         # 平均成交价
    status: AlgoStatus = AlgoStatus.PENDING   # 状态

    # 时间参数
    start_time: Optional[datetime] = None     # 开始时间
    end_time: Optional[datetime] = None       # 结束时间
    created_at: datetime = None               # 创建时间
    updated_at: datetime = None               # 更新时间

    # 子订单
    child_orders: List[str] = field(default_factory=list)  # 子订单 ID 列表

    # 执行参数（根据算法类型使用不同字段）
    params: Dict[str, Any] = field(default_factory=dict)

    # 执行结果
    total_commission: Decimal = Decimal("0")  # 总佣金
    total_slippage: Decimal = Decimal("0")    # 总滑点
    benchmark_price: Decimal = Decimal("0")   # 基准价格（用于计算滑点）

    # 策略 ID
    strategy_id: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def unfilled_quantity(self) -> int:
        """未成交数量"""
        return self.total_quantity - self.filled_quantity

    @property
    def completion_rate(self) -> Decimal:
        """完成率"""
        if self.total_quantity > 0:
            return Decimal(self.filled_quantity) / Decimal(self.total_quantity)
        return Decimal("0")

    @property
    def is_active(self) -> bool:
        """是否仍然活跃"""
        return self.status in [AlgoStatus.PENDING, AlgoStatus.RUNNING, AlgoStatus.PAUSED]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "algo_id": self.algo_id,
            "algo_type": self.algo_type.value,
            "symbol": self.symbol,
            "side": self.side,
            "total_quantity": self.total_quantity,
            "filled_quantity": self.filled_quantity,
            "avg_price": str(self.avg_price),
            "status": self.status.value,
            "completion_rate": f"{float(self.completion_rate) * 100:.2f}%",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


@dataclass
class ChildOrder:
    """
    子订单

    算法订单拆分出的子订单。
    """
    child_id: str                         # 子订单 ID
    algo_id: str                          # 关联的算法订单 ID
    symbol: str                           # 股票代码
    side: str                             # 买卖方向
    quantity: int                         # 数量
    price: Decimal                        # 价格
    status: str = "PENDING"               # 状态
    created_at: datetime = None           # 创建时间
    filled_quantity: int = 0              # 成交数量
    filled_price: Decimal = Decimal("0")  # 成交价格

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AlgoResult:
    """
    算法执行结果

    记录算法交易的完整执行结果。
    """
    algo_id: str                              # 算法订单 ID
    success: bool                             # 是否成功
    total_filled: int = 0                     # 总成交数量
    avg_price: Decimal = Decimal("0")         # 平均成交价
    benchmark_price: Decimal = Decimal("0")   # 基准价格
    slippage: Decimal = Decimal("0")          # 滑点
    slippage_bps: Decimal = Decimal("0")      # 滑点（基点）
    commission: Decimal = Decimal("0")        # 佣金
    duration_seconds: int = 0                 # 执行时长（秒）
    child_order_count: int = 0                # 子订单数量
    message: str = ""                         # 消息

    @property
    def implementation_shortfall(self) -> Decimal:
        """执行落差"""
        if self.benchmark_price > 0 and self.total_filled > 0:
            return (self.avg_price - self.benchmark_price) * self.total_filled
        return Decimal("0")


# ==============================================
# TWAP 算法
# ==============================================

class TWAPAlgo:
    """
    TWAP (Time-Weighted Average Price) 算法

    将大单均匀分配到指定时间段内执行。

    策略：
    - 将总订单量按时间均匀分割
    - 每个时间片执行等量的子订单
    - 适用于需要减少市场冲击的场景

    使用示例：
        twap = TWAPAlgo(
            symbol="000001.SZ",
            side="BUY",
            total_quantity=10000,
            duration_minutes=60,
            interval_seconds=30
        )

        async for child_order in twap.execute(market_data):
            # 处理子订单
            await submit_order(child_order)
    """

    def __init__(
        self,
        symbol: str,
        side: str,
        total_quantity: int,
        duration_minutes: int,
        interval_seconds: int = 60,
        price_limit: Decimal = None,
        randomize: bool = True,
        random_range: float = 0.2
    ):
        """
        初始化 TWAP 算法

        Args:
            symbol: 股票代码
            side: 买卖方向
            total_quantity: 总数量
            duration_minutes: 执行时长（分钟）
            interval_seconds: 下单间隔（秒）
            price_limit: 价格限制（超过此价格不下单）
            randomize: 是否随机化下单量
            random_range: 随机范围（0-1）
        """
        self.symbol = symbol
        self.side = side
        self.total_quantity = total_quantity
        self.duration_minutes = duration_minutes
        self.interval_seconds = interval_seconds
        self.price_limit = price_limit
        self.randomize = randomize
        self.random_range = random_range

        self.algo_id = f"TWAP_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(f"TWAP.{self.algo_id}")

        # 计算切片
        self.total_intervals = max(1, duration_minutes * 60 // interval_seconds)
        self.base_quantity = total_quantity // self.total_intervals
        self.remaining_quantity = total_quantity

    async def execute(
        self,
        get_price: Callable[[], Decimal],
        submit_order: Callable[[ChildOrder], Any]
    ) -> AlgoResult:
        """
        执行 TWAP 算法

        Args:
            get_price: 获取当前价格的函数
            submit_order: 提交订单的函数

        Returns:
            执行结果
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=self.duration_minutes)

        result = AlgoResult(
            algo_id=self.algo_id,
            success=True,
            benchmark_price=await get_price() if get_price else Decimal("0"),
        )

        total_filled = 0
        total_value = Decimal("0")
        child_count = 0

        self.logger.info(
            f"开始 TWAP 执行: {self.symbol} {self.side} {self.total_quantity}, "
            f"时长 {self.duration_minutes} 分钟, {self.total_intervals} 个切片"
        )

        try:
            for i in range(self.total_intervals):
                if datetime.now() >= end_time:
                    self.logger.warning("执行时间已到，停止下单")
                    break

                if self.remaining_quantity <= 0:
                    self.logger.info("所有数量已下单完成")
                    break

                # 获取当前价格
                current_price = await get_price() if get_price else Decimal("0")

                # 检查价格限制
                if self.price_limit and current_price:
                    if self.side == "BUY" and current_price > self.price_limit:
                        self.logger.warning(f"价格 {current_price} 超过限制 {self.price_limit}，跳过")
                        await asyncio.sleep(self.interval_seconds)
                        continue
                    elif self.side == "SELL" and current_price < self.price_limit:
                        self.logger.warning(f"价格 {current_price} 低于限制 {self.price_limit}，跳过")
                        await asyncio.sleep(self.interval_seconds)
                        continue

                # 计算本次下单量
                if i == self.total_intervals - 1:
                    # 最后一次，下剩余所有量
                    order_quantity = self.remaining_quantity
                else:
                    order_quantity = self.base_quantity

                    # 随机化
                    if self.randomize and order_quantity > 0:
                        random_factor = 1 + (random.random() * 2 - 1) * self.random_range
                        order_quantity = max(1, int(order_quantity * random_factor))

                    # 不超过剩余量
                    order_quantity = min(order_quantity, self.remaining_quantity)

                if order_quantity <= 0:
                    continue

                # 创建子订单
                child_order = ChildOrder(
                    child_id=f"{self.algo_id}_{i+1}",
                    algo_id=self.algo_id,
                    symbol=self.symbol,
                    side=self.side,
                    quantity=order_quantity,
                    price=current_price,
                )

                # 提交订单
                try:
                    fill_result = await submit_order(child_order)

                    # 更新统计
                    filled_qty = fill_result.get("filled_quantity", order_quantity)
                    filled_price = Decimal(str(fill_result.get("filled_price", current_price)))

                    total_filled += filled_qty
                    total_value += filled_price * filled_qty
                    self.remaining_quantity -= filled_qty
                    child_count += 1

                    self.logger.debug(
                        f"切片 {i+1}/{self.total_intervals}: "
                        f"下单 {order_quantity}, 成交 {filled_qty}@{filled_price}"
                    )

                except Exception as e:
                    self.logger.error(f"提交子订单失败: {e}")
                    result.success = False

                # 等待下一个间隔
                if i < self.total_intervals - 1:
                    await asyncio.sleep(self.interval_seconds)

        except asyncio.CancelledError:
            self.logger.warning("TWAP 执行被取消")
            result.success = False

        except Exception as e:
            self.logger.error(f"TWAP 执行错误: {e}")
            result.success = False

        # 计算结果
        result.total_filled = total_filled
        result.avg_price = total_value / total_filled if total_filled > 0 else Decimal("0")
        result.child_order_count = child_count
        result.duration_seconds = int((datetime.now() - start_time).total_seconds())

        if result.benchmark_price > 0 and result.avg_price > 0:
            result.slippage = result.avg_price - result.benchmark_price
            result.slippage_bps = result.slippage / result.benchmark_price * Decimal("10000")

        self.logger.info(
            f"TWAP 执行完成: 成交 {total_filled}/{self.total_quantity}, "
            f"均价 {result.avg_price}, 滑点 {result.slippage_bps} bps"
        )

        return result


# ==============================================
# VWAP 算法
# ==============================================

class VWAPAlgo:
    """
    VWAP (Volume-Weighted Average Price) 算法

    按照市场成交量的分布来分配订单。

    策略：
    - 根据历史成交量分布确定每个时段的下单比例
    - 在成交量高的时段下更多的单
    - 适用于希望跟踪市场均价的场景

    使用示例：
        vwap = VWAPAlgo(
            symbol="000001.SZ",
            side="BUY",
            total_quantity=10000,
            volume_profile={...}  # 各时段成交量占比
        )

        result = await vwap.execute(get_price, submit_order)
    """

    def __init__(
        self,
        symbol: str,
        side: str,
        total_quantity: int,
        volume_profile: Dict[int, Decimal] = None,
        duration_minutes: int = 240,  # 默认 4 小时交易日
        participation_rate: Decimal = Decimal("0.1"),  # 参与率 10%
    ):
        """
        初始化 VWAP 算法

        Args:
            symbol: 股票代码
            side: 买卖方向
            total_quantity: 总数量
            volume_profile: 成交量分布 {minute: ratio}
            duration_minutes: 执行时长
            participation_rate: 参与率
        """
        self.symbol = symbol
        self.side = side
        self.total_quantity = total_quantity
        self.duration_minutes = duration_minutes
        self.participation_rate = participation_rate

        self.algo_id = f"VWAP_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(f"VWAP.{self.algo_id}")

        # 默认成交量分布（A股典型分布）
        if volume_profile is None:
            volume_profile = self._get_default_volume_profile()

        self.volume_profile = volume_profile
        self.remaining_quantity = total_quantity

    def _get_default_volume_profile(self) -> Dict[int, Decimal]:
        """
        获取默认成交量分布

        A 股典型分布：
        - 开盘 30 分钟：高成交量
        - 中午：低成交量
        - 收盘 30 分钟：高成交量
        """
        profile = {}

        # 上午 (9:30-11:30, 120 分钟)
        for i in range(120):
            if i < 30:  # 开盘 30 分钟
                profile[i] = Decimal("0.008")  # 0.8% 每分钟
            else:
                profile[i] = Decimal("0.003")  # 0.3% 每分钟

        # 下午 (13:00-15:00, 120 分钟)
        for i in range(120, 240):
            if i >= 210:  # 收盘 30 分钟
                profile[i] = Decimal("0.008")
            else:
                profile[i] = Decimal("0.003")

        return profile

    async def execute(
        self,
        get_price: Callable[[], Decimal],
        get_volume: Callable[[], int],
        submit_order: Callable[[ChildOrder], Any],
        interval_seconds: int = 60
    ) -> AlgoResult:
        """
        执行 VWAP 算法

        Args:
            get_price: 获取当前价格
            get_volume: 获取当前成交量
            submit_order: 提交订单
            interval_seconds: 下单间隔

        Returns:
            执行结果
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=self.duration_minutes)

        result = AlgoResult(
            algo_id=self.algo_id,
            success=True,
            benchmark_price=await get_price() if get_price else Decimal("0"),
        )

        total_filled = 0
        total_value = Decimal("0")
        child_count = 0

        self.logger.info(
            f"开始 VWAP 执行: {self.symbol} {self.side} {self.total_quantity}"
        )

        try:
            current_interval = 0

            while datetime.now() < end_time and self.remaining_quantity > 0:
                # 获取当前时段
                minute_of_day = current_interval % self.duration_minutes

                # 获取成交量比例
                volume_ratio = self.volume_profile.get(minute_of_day, Decimal("0.003"))

                # 获取市场成交量
                market_volume = await get_volume() if get_volume else 10000

                # 计算目标下单量
                target_quantity = int(market_volume * float(self.participation_rate) * float(volume_ratio) * 100)
                target_quantity = min(target_quantity, self.remaining_quantity)

                if target_quantity > 0:
                    # 获取当前价格
                    current_price = await get_price() if get_price else Decimal("0")

                    # 创建子订单
                    child_order = ChildOrder(
                        child_id=f"{self.algo_id}_{current_interval}",
                        algo_id=self.algo_id,
                        symbol=self.symbol,
                        side=self.side,
                        quantity=target_quantity,
                        price=current_price,
                    )

                    try:
                        fill_result = await submit_order(child_order)

                        filled_qty = fill_result.get("filled_quantity", target_quantity)
                        filled_price = Decimal(str(fill_result.get("filled_price", current_price)))

                        total_filled += filled_qty
                        total_value += filled_price * filled_qty
                        self.remaining_quantity -= filled_qty
                        child_count += 1

                    except Exception as e:
                        self.logger.error(f"提交子订单失败: {e}")

                current_interval += 1
                await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            self.logger.warning("VWAP 执行被取消")
            result.success = False

        except Exception as e:
            self.logger.error(f"VWAP 执行错误: {e}")
            result.success = False

        # 计算结果
        result.total_filled = total_filled
        result.avg_price = total_value / total_filled if total_filled > 0 else Decimal("0")
        result.child_order_count = child_count
        result.duration_seconds = int((datetime.now() - start_time).total_seconds())

        if result.benchmark_price > 0 and result.avg_price > 0:
            result.slippage = result.avg_price - result.benchmark_price
            result.slippage_bps = result.slippage / result.benchmark_price * Decimal("10000")

        return result


# ==============================================
# 冰山订单
# ==============================================

class IcebergAlgo:
    """
    冰山订单算法

    只显示部分订单量，隐藏真实交易意图。

    策略：
    - 设置显示数量和总数量
    - 当显示部分成交后，自动补充新的订单
    - 适用于隐藏大单意图的场景

    使用示例：
        iceberg = IcebergAlgo(
            symbol="000001.SZ",
            side="BUY",
            total_quantity=10000,
            display_quantity=500,
            price=Decimal("10.0")
        )

        result = await iceberg.execute(check_fill, submit_order)
    """

    def __init__(
        self,
        symbol: str,
        side: str,
        total_quantity: int,
        display_quantity: int,
        price: Decimal,
        price_variance: Decimal = Decimal("0"),  # 价格波动范围
        refresh_interval: int = 5,  # 刷新间隔（秒）
    ):
        """
        初始化冰山订单

        Args:
            symbol: 股票代码
            side: 买卖方向
            total_quantity: 总数量
            display_quantity: 显示数量
            price: 目标价格
            price_variance: 价格波动范围
            refresh_interval: 刷新间隔
        """
        self.symbol = symbol
        self.side = side
        self.total_quantity = total_quantity
        self.display_quantity = display_quantity
        self.price = price
        self.price_variance = price_variance
        self.refresh_interval = refresh_interval

        self.algo_id = f"ICEBERG_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(f"Iceberg.{self.algo_id}")

        self.remaining_quantity = total_quantity
        self.current_display_quantity = 0
        self.current_order_id = None

    async def execute(
        self,
        check_fill: Callable[[str], Dict[str, Any]],
        submit_order: Callable[[ChildOrder], str],
        cancel_order: Callable[[str], bool] = None
    ) -> AlgoResult:
        """
        执行冰山订单

        Args:
            check_fill: 检查订单成交状态
            submit_order: 提交订单
            cancel_order: 撤销订单

        Returns:
            执行结果
        """
        start_time = datetime.now()
        benchmark_price = self.price

        result = AlgoResult(
            algo_id=self.algo_id,
            success=True,
            benchmark_price=benchmark_price,
        )

        total_filled = 0
        total_value = Decimal("0")
        child_count = 0

        self.logger.info(
            f"开始冰山订单执行: {self.symbol} {self.side} "
            f"总量 {self.total_quantity}, 显示量 {self.display_quantity}"
        )

        try:
            while self.remaining_quantity > 0:
                # 计算本次显示量
                self.current_display_quantity = min(
                    self.display_quantity,
                    self.remaining_quantity
                )

                # 计算价格（可能有波动）
                import random
                price_offset = float(self.price_variance) * (random.random() * 2 - 1)
                order_price = self.price * Decimal(str(1 + price_offset))

                # 创建子订单
                child_order = ChildOrder(
                    child_id=f"{self.algo_id}_{child_count}",
                    algo_id=self.algo_id,
                    symbol=self.symbol,
                    side=self.side,
                    quantity=self.current_display_quantity,
                    price=order_price,
                )

                # 提交订单
                self.current_order_id = await submit_order(child_order)
                child_count += 1

                if not self.current_order_id:
                    self.logger.error("提交订单失败")
                    continue

                # 等待成交
                filled = False
                while not filled and self.remaining_quantity > 0:
                    fill_status = await check_fill(self.current_order_id)

                    if fill_status.get("status") == "FILLED":
                        filled_qty = fill_status.get("filled_quantity", 0)
                        filled_price = Decimal(str(fill_status.get("filled_price", order_price)))

                        total_filled += filled_qty
                        total_value += filled_price * filled_qty
                        self.remaining_quantity -= filled_qty
                        filled = True

                        self.logger.debug(
                            f"冰山切片成交: {filled_qty}@{filled_price}, "
                            f"剩余 {self.remaining_quantity}"
                        )

                    elif fill_status.get("status") in ["CANCELLED", "REJECTED"]:
                        self.logger.warning(f"订单被取消或拒绝")
                        break

                    else:
                        # 部分成交
                        partial_filled = fill_status.get("filled_quantity", 0)
                        if partial_filled > 0:
                            partial_price = Decimal(str(fill_status.get("filled_price", order_price)))
                            total_filled += partial_filled
                            total_value += partial_price * partial_filled
                            self.remaining_quantity -= partial_filled

                        await asyncio.sleep(self.refresh_interval)

        except asyncio.CancelledError:
            self.logger.warning("冰山订单被取消")
            if cancel_order and self.current_order_id:
                await cancel_order(self.current_order_id)
            result.success = False

        except Exception as e:
            self.logger.error(f"冰山订单执行错误: {e}")
            result.success = False

        # 计算结果
        result.total_filled = total_filled
        result.avg_price = total_value / total_filled if total_filled > 0 else Decimal("0")
        result.child_order_count = child_count
        result.duration_seconds = int((datetime.now() - start_time).total_seconds())

        if result.benchmark_price > 0 and result.avg_price > 0:
            result.slippage = result.avg_price - result.benchmark_price
            result.slippage_bps = result.slippage / result.benchmark_price * Decimal("10000")

        return result


# ==============================================
# 算法交易引擎
# ==============================================

class AlgorithmicTradingEngine:
    """
    算法交易引擎

    统一管理所有算法交易订单。

    功能：
    - 创建和管理算法订单
    - 执行算法策略
    - 监控执行状态
    - 暂停/恢复/取消

    使用示例：
        engine = AlgorithmicTradingEngine()

        # 创建 TWAP 订单
        algo_order = await engine.create_twap_order(
            symbol="000001.SZ",
            side="BUY",
            quantity=10000,
            duration_minutes=60
        )

        # 执行
        result = await engine.execute(algo_order.algo_id)
    """

    def __init__(self):
        """初始化算法交易引擎"""
        self._algo_orders: Dict[str, AlgoOrder] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._logger = logging.getLogger("AlgoEngine")

    def create_order(
        self,
        algo_type: AlgoType,
        symbol: str,
        side: str,
        quantity: int,
        **params
    ) -> AlgoOrder:
        """
        创建算法订单

        Args:
            algo_type: 算法类型
            symbol: 股票代码
            side: 买卖方向
            quantity: 数量
            **params: 算法参数

        Returns:
            算法订单对象
        """
        algo_id = f"{algo_type.value}_{uuid.uuid4().hex[:8]}"

        algo_order = AlgoOrder(
            algo_id=algo_id,
            algo_type=algo_type,
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            params=params,
        )

        self._algo_orders[algo_id] = algo_order
        self._logger.info(f"创建算法订单: {algo_id}")

        return algo_order

    def create_twap_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        duration_minutes: int,
        **kwargs
    ) -> AlgoOrder:
        """创建 TWAP 订单"""
        return self.create_order(
            AlgoType.TWAP,
            symbol,
            side,
            quantity,
            duration_minutes=duration_minutes,
            **kwargs
        )

    def create_vwap_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        duration_minutes: int = 240,
        **kwargs
    ) -> AlgoOrder:
        """创建 VWAP 订单"""
        return self.create_order(
            AlgoType.VWAP,
            symbol,
            side,
            quantity,
            duration_minutes=duration_minutes,
            **kwargs
        )

    def create_iceberg_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        display_quantity: int,
        price: Decimal,
        **kwargs
    ) -> AlgoOrder:
        """创建冰山订单"""
        return self.create_order(
            AlgoType.ICEBERG,
            symbol,
            side,
            quantity,
            display_quantity=display_quantity,
            price=price,
            **kwargs
        )

    def get_order(self, algo_id: str) -> Optional[AlgoOrder]:
        """获取算法订单"""
        return self._algo_orders.get(algo_id)

    def list_orders(self, status: AlgoStatus = None) -> List[AlgoOrder]:
        """列出算法订单"""
        orders = list(self._algo_orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders

    async def execute(
        self,
        algo_id: str,
        get_price: Callable,
        submit_order: Callable,
        **callbacks
    ) -> AlgoResult:
        """
        执行算法订单

        Args:
            algo_id: 算法订单 ID
            get_price: 获取价格函数
            submit_order: 提交订单函数
            **callbacks: 其他回调函数

        Returns:
            执行结果
        """
        algo_order = self._algo_orders.get(algo_id)
        if algo_order is None:
            raise ValueError(f"算法订单不存在: {algo_id}")

        algo_order.status = AlgoStatus.RUNNING
        algo_order.start_time = datetime.now()

        result = AlgoResult(algo_id=algo_id, success=False)

        try:
            if algo_order.algo_type == AlgoType.TWAP:
                twap = TWAPAlgo(
                    symbol=algo_order.symbol,
                    side=algo_order.side,
                    total_quantity=algo_order.total_quantity,
                    **algo_order.params
                )
                result = await twap.execute(get_price, submit_order)

            elif algo_order.algo_type == AlgoType.VWAP:
                vwap = VWAPAlgo(
                    symbol=algo_order.symbol,
                    side=algo_order.side,
                    total_quantity=algo_order.total_quantity,
                    **algo_order.params
                )
                get_volume = callbacks.get("get_volume")
                result = await vwap.execute(get_price, get_volume, submit_order)

            elif algo_order.algo_type == AlgoType.ICEBERG:
                iceberg = IcebergAlgo(
                    symbol=algo_order.symbol,
                    side=algo_order.side,
                    total_quantity=algo_order.total_quantity,
                    **algo_order.params
                )
                check_fill = callbacks.get("check_fill")
                cancel_order = callbacks.get("cancel_order")
                result = await iceberg.execute(check_fill, submit_order, cancel_order)

            # 更新订单状态
            algo_order.filled_quantity = result.total_filled
            algo_order.avg_price = result.avg_price
            algo_order.status = AlgoStatus.COMPLETED if result.success else AlgoStatus.ERROR

        except asyncio.CancelledError:
            algo_order.status = AlgoStatus.CANCELLED
            result.success = False

        except Exception as e:
            self._logger.error(f"执行算法订单失败: {e}")
            algo_order.status = AlgoStatus.ERROR
            result.message = str(e)

        algo_order.end_time = datetime.now()
        algo_order.updated_at = datetime.now()

        return result

    def cancel(self, algo_id: str) -> bool:
        """
        取消算法订单

        Args:
            algo_id: 算法订单 ID

        Returns:
            是否成功
        """
        algo_order = self._algo_orders.get(algo_id)
        if algo_order is None:
            return False

        # 取消正在执行的任务
        if algo_id in self._running_tasks:
            task = self._running_tasks.pop(algo_id)
            task.cancel()

        algo_order.status = AlgoStatus.CANCELLED
        algo_order.updated_at = datetime.now()

        self._logger.info(f"取消算法订单: {algo_id}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        status_counts = {}
        for order in self._algo_orders.values():
            status = order.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_orders": len(self._algo_orders),
            "running_tasks": len(self._running_tasks),
            "by_status": status_counts,
        }
