"""
Yahoo Finance 数据服务

使用 yfinance 库获取美股、港股等市场数据。
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

try:
    import yfinance as yf
except ImportError:
    yf = None
    print("警告: yfinance 未安装，请运行: pip install yfinance")

from .base import DataSourceBase, StockPriceData, StockInfo, DataSourceConnectionError

logger = logging.getLogger(__name__)


class YahooFinanceDataSource(DataSourceBase):
    """
    Yahoo Finance 数据源

    支持市场：美股、港股、部分 ADR
    数据质量：⭐⭐⭐⭐
    更新频率：实时延迟
    """

    def __init__(self):
        super().__init__()
        self.name = "Yahoo Finance"
        self.is_available = yf is not None

    def check_connection(self) -> bool:
        """
        检查 Yahoo Finance 连接

        Returns:
            bool: 连接是否正常
        """
        if not self.is_available:
            return False

        try:
            # 测试获取 Apple 股票数据
            ticker = yf.Ticker("AAPL")
            data = ticker.history(period="1d")
            return not data.empty
        except Exception as e:
            logger.error(f"Yahoo Finance 连接失败: {e}")
            return False

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码（如: AAPL, TSLA）

        Returns:
            股票基本信息或 None
        """
        if not self.is_available:
            raise DataSourceConnectionError("yfinance 未安装")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return None

            # 确定市场
            market = self._determine_market(symbol, info)

            return StockInfo(
                symbol=symbol.upper(),
                name=info.get("longName", info.get("shortName", "")),
                sector=info.get("sector"),
                industry=info.get("industry"),
                market=market
            )
        except Exception as e:
            logger.error(f"获取 {symbol} 信息失败: {e}")
            return None

    def get_stock_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> List[StockPriceData]:
        """
        获取股票价格数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔（1d, 1wk, 1mo）

        Returns:
            股票价格数据列表
        """
        if not self.is_available:
            raise DataSourceConnectionError("yfinance 未安装")

        try:
            ticker = yf.Ticker(symbol)

            # 转换为 datetime
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            # 获取历史数据
            df = ticker.history(start=start_dt, end=end_dt, interval=interval)

            if df.empty:
                logger.warning(f"未获取到 {symbol} 的数据")
                return []

            # 转换为 StockPriceData 列表
            prices = []
            for timestamp, row in df.iterrows():
                # 跳过空数据
                if row.isna().any():
                    continue

                price_data = StockPriceData(
                    symbol=symbol.upper(),
                    timestamp=timestamp.to_pydatetime(),
                    open=Decimal(str(row['Open'])),
                    high=Decimal(str(row['High'])),
                    low=Decimal(str(row['Low'])),
                    close=Decimal(str(row['Close'])),
                    volume=int(row['Volume']),
                    amount=Decimal(str(row['Close'] * row['Volume'])) if 'Volume' in row else None
                )
                prices.append(price_data)

            logger.info(f"成功获取 {symbol} 的 {len(prices)} 条数据")
            return prices

        except Exception as e:
            logger.error(f"获取 {symbol} 价格数据失败: {e}")
            return []

    def get_latest_price(self, symbol: str) -> Optional[StockPriceData]:
        """
        获取最新价格数据

        Args:
            symbol: 股票代码

        Returns:
            最新价格数据或 None
        """
        if not self.is_available:
            raise DataSourceConnectionError("yfinance 未安装")

        try:
            # 获取最近 5 天的数据
            end_date = date.today()
            start_date = end_date - timedelta(days=5)

            prices = self.get_stock_prices(symbol, start_date, end_date)

            if not prices:
                return None

            # 返回最新的数据
            return prices[-1]

        except Exception as e:
            logger.error(f"获取 {symbol} 最新价格失败: {e}")
            return None

    def get_multiple_stocks_prices(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> dict[str, List[StockPriceData]]:
        """
        批量获取多只股票的价格数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔

        Returns:
            {symbol: [StockPriceData]}
        """
        if not self.is_available:
            raise DataSourceConnectionError("yfinance 未安装")

        results = {}

        for symbol in symbols:
            try:
                prices = self.get_stock_prices(symbol, start_date, end_date, interval)
                if prices:
                    results[symbol] = prices
            except Exception as e:
                logger.error(f"批量获取 {symbol} 数据失败: {e}")
                continue

        return results

    def _determine_market(self, symbol: str, info: dict) -> str:
        """
        确定股票所属市场

        Args:
            symbol: 股票代码
            info: 股票信息字典

        Returns:
            市场代码
        """
        # 根据股票代码后缀判断
        if symbol.endswith(".HK") or ".H" in symbol:
            return "HKEX"
        elif symbol.endswith(".TO") or ".V" in symbol:
            return "TSX"  # 多伦多证券交易所
        elif symbol.endswith(".L"):
            return "LSE"  # 伦敦证券交易所
        elif symbol.endswith(".DE"):
            return "FSE"  # 法兰克福证券交易所
        elif symbol.endswith(".PA"):
            return "EPA"  # 巴黎证券交易所
        elif symbol.endswith(".T") or symbol.endswith(".O") or symbol.endswith(".N"):
            return "US"  # 美股
        else:
            # 默认为美股
            return "US"

    @staticmethod
    def format_symbol(symbol: str, market: str = "US") -> str:
        """
        格式化股票代码

        Args:
            symbol: 原始股票代码
            market: 目标市场

        Returns:
            格式化后的股票代码
        """
        symbol = symbol.upper().strip()

        if market == "HKEX":
            if not symbol.endswith(".HK"):
                symbol = symbol.replace(".H", ".HK")
        elif market == "US":
            # 移除可能的后缀
            for suffix in [".HK", ".H", ".TO", ".L", ".DE", ".PA"]:
                if suffix in symbol:
                    symbol = symbol.replace(suffix, "")

        return symbol


# ==============================================
# 便捷函数
# ==============================================

def get_yahoo_finance_source() -> YahooFinanceDataSource:
    """
    获取 Yahoo Finance 数据源实例

    Returns:
        YahooFinanceDataSource 实例
    """
    return YahooFinanceDataSource()
