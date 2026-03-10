"""
策略引擎基础模块

定义策略的基础接口和抽象类。

增强版本 v2.0：
- 新增生命周期方法：on_bar_close, on_order_status, on_trade, on_timer
- 支持参数热加载
- 支持状态持久化
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal
import logging
import copy

if TYPE_CHECKING:
    from .context import IsolatedStrategyContext, Order, Trade

logger = logging.getLogger(__name__)


# ==============================================
# 枚举类型
# ==============================================

class SignalType(str, Enum):
    """信号类型"""
    BUY = "BUY"          # 买入信号
    SELL = "SELL"        # 卖出信号
    HOLD = "HOLD"        # 持有信号
    CLOSE = "CLOSE"      # 平仓信号


class StrategyStatus(str, Enum):
    """策略状态"""
    CREATED = "CREATED"        # 已创建
    RUNNING = "RUNNING"        # 运行中
    PAUSED = "PAUSED"          # 已暂停
    STOPPED = "STOPPED"        # 已停止
    ERROR = "ERROR"            # 错误


# ==============================================
# 数据类
# ==============================================

@dataclass
class Signal:
    """
    交易信号

    策略生成的交易信号。
    """
    symbol: str                      # 股票代码
    signal_type: SignalType          # 信号类型
    timestamp: datetime               # 时间戳
    price: float                     # 价格
    quantity: int                    # 数量
    confidence: float = 1.0          # 信号置信度（0-1）
    reason: str = ""                 # 信号原因
    metadata: Dict[str, Any] = None  # 额外元数据

    def __repr__(self):
        return f"<Signal({self.symbol}, {self.signal_type}, {self.price}, {self.quantity})>"


@dataclass
class StrategyConfig:
    """
    策略配置

    策略的配置参数。
    """
    name: str                         # 策略名称
    description: str = ""             # 策略描述
    parameters: Dict[str, Any] = None # 策略参数
    initial_capital: float = 100000   # 初始资金
    execution_mode: str = "PAPER"     # 执行模式（PAPER/LIVE）

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class BacktestConfig:
    """
    回测配置

    策略回测的配置参数。
    """
    start_date: datetime              # 开始日期
    end_date: datetime                # 结束日期
    initial_capital: float = 100000   # 初始资金
    commission_rate: float = 0.0003   # 手续费率（默认 0.03%）
    slippage_rate: float = 0.001      # 滑点率（默认 0.1%）
    benchmark: Optional[str] = None   # 基准指数


# ==============================================
# 策略基类
# ==============================================

class StrategyBase(ABC):
    """
    策略基类（增强版）

    所有策略都需要继承此类并实现抽象方法。

    生命周期方法：
    - initialize(): 策略初始化时调用
    - on_data(): 每次收到新数据时调用（核心）
    - on_bar_close(): K 线闭合时调用
    - on_order_status(): 订单状态变化时调用
    - on_trade(): 成交时调用
    - on_timer(): 定时器触发时调用
    - finalize(): 策略结束时调用

    使用示例：
        class MyStrategy(StrategyBase):
            def initialize(self, context):
                # 初始化指标
                self.sma_period = self.parameters.get('period', 20)

            def on_data(self, context):
                # 生成信号
                if condition:
                    return [Signal(...)]
                return None

            def on_bar_close(self, context):
                # K线闭合处理
                pass

            def finalize(self, context):
                # 清理资源
                pass
    """

    def __init__(self, config: StrategyConfig):
        """
        初始化策略

        Args:
            config: 策略配置
        """
        self.config = config
        self.name = config.name
        self.description = config.description
        self.parameters = config.parameters or {}
        self.status = StrategyStatus.CREATED
        self.logger = logging.getLogger(f"Strategy.{self.name}")

        # 策略实例 ID（由引擎设置）
        self._instance_id: Optional[str] = None

        # 策略内部状态
        self._internal_state: Dict[str, Any] = {}

        # 参数变更回调
        self._on_params_changed_callbacks: List[callable] = []

    # ==========================================
    # 抽象方法（必须实现）
    # ==========================================

    @abstractmethod
    def initialize(self, context: 'StrategyContext') -> None:
        """
        初始化策略

        在策略开始运行前调用，用于初始化指标、参数等。

        Args:
            context: 策略上下文
        """
        pass

    @abstractmethod
    def on_data(self, context: 'StrategyContext') -> Optional[List[Signal]]:
        """
        处理数据并生成信号（核心方法）

        每次收到新数据时调用，用于生成交易信号。
        这是策略的主要逻辑入口。

        Args:
            context: 策略上下文

        Returns:
            信号列表或 None
        """
        pass

    @abstractmethod
    def finalize(self, context: 'StrategyContext') -> None:
        """
        结束策略

        在策略结束时调用，用于清理资源、计算最终指标等。

        Args:
            context: 策略上下文
        """
        pass

    # ==========================================
    # 生命周期方法（可选重写）
    # ==========================================

    def on_bar_close(self, context: 'StrategyContext') -> Optional[List[Signal]]:
        """
        K 线闭合处理

        当一根 K 线闭合时调用，可用于收盘价确认后的逻辑处理。

        Args:
            context: 策略上下文

        Returns:
            信号列表或 None
        """
        return None

    def on_order_status(self, order: 'Order', old_status: str, new_status: str) -> None:
        """
        订单状态变化回调

        当订单状态发生变化时调用。

        Args:
            order: 订单对象
            old_status: 旧状态
            new_status: 新状态
        """
        self.logger.debug(
            f"订单状态变化: {order.order_id} {old_status} -> {new_status}"
        )

    def on_trade(self, trade: 'Trade', order: 'Order') -> None:
        """
        成交回调

        当订单成交时调用。

        Args:
            trade: 成交记录
            order: 关联订单
        """
        self.logger.info(
            f"成交: {trade.symbol} {trade.side} {trade.quantity}@{trade.price}"
        )

    def on_timer(self, context: 'StrategyContext') -> Optional[List[Signal]]:
        """
        定时器回调

        根据策略配置的定时器触发，用于定时任务（如每日开盘前检查）。

        Args:
            context: 策略上下文

        Returns:
            信号列表或 None
        """
        return None

    def on_error(self, error: Exception, context: 'StrategyContext' = None) -> None:
        """
        错误处理回调

        当策略执行发生错误时调用。

        Args:
            error: 异常对象
            context: 策略上下文（可能为 None）
        """
        self.logger.error(f"策略执行错误: {error}", exc_info=True)
        self.status = StrategyStatus.ERROR

    # ==========================================
    # 参数管理
    # ==========================================

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """
        验证策略参数

        Returns:
            (是否有效, 错误信息)
        """
        return True, None

    def update_parameters(self, new_params: Dict[str, Any]) -> bool:
        """
        热加载参数

        在不重启策略的情况下动态更新参数。

        Args:
            new_params: 新参数字典

        Returns:
            是否成功更新
        """
        # 备份旧参数
        old_params = copy.deepcopy(self.parameters)

        try:
            # 合并参数
            self.parameters.update(new_params)

            # 验证新参数
            is_valid, error_msg = self.validate_parameters()
            if not is_valid:
                # 验证失败，回滚
                self.parameters = old_params
                self.logger.error(f"参数验证失败: {error_msg}")
                return False

            # 触发参数变更回调
            self._on_parameters_changed(old_params, new_params)

            self.logger.info(f"参数已更新: {new_params}")
            return True

        except Exception as e:
            # 发生错误，回滚
            self.parameters = old_params
            self.logger.error(f"参数更新失败: {e}")
            return False

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        获取参数值

        Args:
            key: 参数键
            default: 默认值

        Returns:
            参数值
        """
        return self.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any) -> None:
        """
        设置单个参数

        Args:
            key: 参数键
            value: 参数值
        """
        self.parameters[key] = value

    def _on_parameters_changed(
        self,
        old_params: Dict[str, Any],
        new_params: Dict[str, Any]
    ) -> None:
        """
        参数变更后的处理

        Args:
            old_params: 旧参数
            new_params: 新参数
        """
        for callback in self._on_params_changed_callbacks:
            try:
                callback(old_params, new_params)
            except Exception as e:
                self.logger.error(f"参数变更回调执行失败: {e}")

    def add_params_changed_callback(self, callback: callable) -> None:
        """
        添加参数变更回调

        Args:
            callback: 回调函数，签名: (old_params, new_params) -> None
        """
        self._on_params_changed_callbacks.append(callback)

    # ==========================================
    # 状态管理
    # ==========================================

    def get_state(self) -> Dict[str, Any]:
        """
        获取策略状态

        Returns:
            策略状态字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "parameters": self.parameters,
            "instance_id": self._instance_id,
            "internal_state": self._internal_state,
        }

    def save_state(self) -> Dict[str, Any]:
        """
        保存策略内部状态（用于持久化）

        子类可以重写此方法以保存自定义状态。

        Returns:
            状态字典
        """
        return {
            "parameters": copy.deepcopy(self.parameters),
            "internal_state": copy.deepcopy(self._internal_state),
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """
        加载策略内部状态（从持久化恢复）

        子类可以重写此方法以恢复自定义状态。

        Args:
            state: 状态字典
        """
        if "parameters" in state:
            self.parameters = state["parameters"]
        if "internal_state" in state:
            self._internal_state = state["internal_state"]

    def set_internal_state(self, key: str, value: Any) -> None:
        """
        设置内部状态

        Args:
            key: 状态键
            value: 状态值
        """
        self._internal_state[key] = value

    def get_internal_state(self, key: str, default: Any = None) -> Any:
        """
        获取内部状态

        Args:
            key: 状态键
            default: 默认值

        Returns:
            状态值
        """
        return self._internal_state.get(key, default)

    # ==========================================
    # 辅助方法
    # ==========================================

    def log_info(self, message: str) -> None:
        """记录信息日志"""
        self.logger.info(f"[{self.name}] {message}")

    def log_warning(self, message: str) -> None:
        """记录警告日志"""
        self.logger.warning(f"[{self.name}] {message}")

    def log_error(self, message: str) -> None:
        """记录错误日志"""
        self.logger.error(f"[{self.name}] {message}")

    def log_debug(self, message: str) -> None:
        """记录调试日志"""
        self.logger.debug(f"[{self.name}] {message}")

    def __repr__(self):
        return f"<{self.__class__.__name__}(name={self.name}, status={self.status})>"


# ==============================================
# 策略上下文
# ==============================================

class StrategyContext:
    """
    策略上下文

    提供策略运行时需要的数据和方法。
    """

    def __init__(
        self,
        current_time: datetime,
        current_price: float,
        position: Optional[int] = None,
        cash: Optional[float] = None,
        portfolio_value: Optional[float] = None,
        historical_data: Optional[List[Dict]] = None,
        indicators: Optional[Dict[str, Any]] = None
    ):
        """
        初始化策略上下文

        Args:
            current_time: 当前时间
            current_price: 当前价格
            position: 当前持仓（股数）
            cash: 可用资金
            portfolio_value: 组合价值
            historical_data: 历史数据
            indicators: 技术指标
        """
        self.current_time = current_time
        self.current_price = current_price
        self.position = position or 0
        self.cash = cash or 0.0
        self.portfolio_value = portfolio_value or 0.0
        self.historical_data = historical_data or []
        self.indicators = indicators or {}

        # 自定义数据存储
        self.custom_data: Dict[str, Any] = {}

    def get_indicator(self, name: str, default: Any = None) -> Any:
        """
        获取技术指标

        Args:
            name: 指标名称
            default: 默认值

        Returns:
            指标值
        """
        return self.indicators.get(name, default)

    def set_custom_data(self, key: str, value: Any) -> None:
        """
        设置自定义数据

        Args:
            key: 键
            value: 值
        """
        self.custom_data[key] = value

    def get_custom_data(self, key: str, default: Any = None) -> Any:
        """
        获取自定义数据

        Args:
            key: 键
            default: 默认值

        Returns:
            值
        """
        return self.custom_data.get(key, default)

    def __repr__(self):
        return f"<StrategyContext(time={self.current_time}, price={self.current_price})>"


# ==============================================
# 策略异常
# ==============================================

class StrategyError(Exception):
    """策略错误"""
    pass


class StrategyValidationError(StrategyError):
    """策略验证错误"""
    pass


class StrategyExecutionError(StrategyError):
    """策略执行错误"""
    pass
