"""
AkShare A股数据服务

使用 akshare 库获取 A股市场数据。
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import re

try:
    import akshare as ak
except ImportError:
    ak = None
    logger.warning("akshare 未安装，请运行: pip install akshare")

from .base import DataSourceBase, StockPriceData, StockInfo, DataSourceConnectionError

logger = logging.getLogger(__name__)


class AkShareDataSource(DataSourceBase):
    """
    AkShare 数据源

    支持市场：A股（沪深）
    数据质量：⭐⭐⭐⭐⭐
    更新频率：交易日收盘后
    数据源：新浪财经、东方财富等
    """

    def __init__(self):
        super().__init__()
        self.name = "AkShare"
        self.is_available = ak is not None

    def check_connection(self) -> bool:
        """
        检查 AkShare 连接

        Returns:
            bool: 连接是否正常
        """
        if not self.is_available:
            return False

        try:
            # 测试获取 A股 股票列表
            df = ak.stock_zh_a_spot_em()
            return not df.empty
        except Exception as e:
            logger.error(f"AkShare 连接失败: {e}")
            return False

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码（如: 000001, 600000）

        Returns:
            股票基本信息或 None
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        try:
            # 格式化股票代码
            symbol_formatted = self._format_symbol(symbol)

            # 获取股票基本信息
            info = ak.stock_individual_info_em(symbol=symbol_formatted)

            if info is None or info.empty:
                logger.warning(f"未找到 {symbol} 的信息")
                return None

            # 提取信息
            info_dict = dict(zip(info['item'], info['value']))

            return StockInfo(
                symbol=symbol,
                name=info_dict.get('股票简称', ''),
                sector=info_dict.get('行业', None),
                industry=info_dict.get('所属行业', None),
                market=self._determine_market(symbol)
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
            interval: 时间间隔（仅支持 1d）

        Returns:
            股票价格数据列表
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        if interval != "1d":
            logger.warning("AkShare 仅支持日线数据（interval=1d）")

        try:
            # 格式化股票代码
            symbol_formatted = self._format_symbol(symbol)

            # 格式化日期
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")

            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol_formatted,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq"  # 前复权
            )

            if df.empty:
                logger.warning(f"未获取到 {symbol} 的数据")
                return []

            # 转换为 StockPriceData 列表
            prices = []
            for _, row in df.iterrows():
                # 跳过空数据
                if row.isna().any():
                    continue

                price_data = StockPriceData(
                    symbol=symbol,
                    timestamp=datetime.strptime(str(row['日期']), "%Y-%m-%d"),
                    open=Decimal(str(row['开盘'])),
                    high=Decimal(str(row['最高'])),
                    low=Decimal(str(row['最低'])),
                    close=Decimal(str(row['收盘'])),
                    volume=int(row['成交量']),
                    amount=Decimal(str(row['成交额'])) if '成交额' in row and not row.isna()['成交额'] else None
                )
                prices.append(price_data)

            logger.info(f"成功获取 {symbol} 的 {len(prices)} 条数据")
            return prices

        except Exception as e:
            logger.error(f"获取 {symbol} 价格数据失败: {e}")
            return []

    def get_latest_price(self, symbol: str) -> Optional[StockPriceData]:
        """
        获取最新价格数据（实时行情）

        Args:
            symbol: 股票代码

        Returns:
            最新价格数据或 None
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        try:
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()

            if df.empty:
                return None

            # 查找目标股票
            symbol_formatted = self._format_symbol(symbol)
            row = df[df['代码'] == symbol_formatted]

            if row.empty:
                logger.warning(f"未找到 {symbol} 的实时行情")
                return None

            row = row.iloc[0]

            # 构造价格数据
            now = datetime.now()
            price_data = StockPriceData(
                symbol=symbol,
                timestamp=now,
                open=Decimal(str(row['今开'])),
                high=Decimal(str(row['最高'])),
                low=Decimal(str(row['最低'])),
                close=Decimal(str(row['现价'])),
                volume=int(row['成交量']),
                amount=Decimal(str(row['成交额']))
            )

            return price_data

        except Exception as e:
            logger.error(f"获取 {symbol} 最新价格失败: {e}")
            return None

    def get_stock_list(self, market: str = "all") -> List[StockInfo]:
        """
        获取 A股股票列表

        Args:
            market: 市场选择（all, sh, sz）

        Returns:
            股票列表
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        try:
            df = ak.stock_zh_a_spot_em()

            if df.empty:
                return []

            # 过滤市场
            if market == "sh":
                df = df[df['代码'].str.startswith('6')]
            elif market == "sz":
                df = df[~df['代码'].str.startswith('6')]

            # 转换为 StockInfo 列表
            stocks = []
            for _, row in df.iterrows():
                code = row['代码']
                stock_info = StockInfo(
                    symbol=code,
                    name=row['名称'],
                    market=self._determine_market(code)
                )
                stocks.append(stock_info)

            logger.info(f"成功获取 {len(stocks)} 只股票信息")
            return stocks

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

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
            raise DataSourceConnectionError("akshare 未安装")

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

    def _determine_market(self, symbol: str) -> str:
        """
        确定股票所属市场

        Args:
            symbol: 股票代码

        Returns:
            市场代码（SHSE, SZSE）
        """
        # 上海证券交易所（6开头）
        if symbol.startswith('6'):
            return "SHSE"
        # 深圳证券交易所（0或3开头）
        elif symbol.startswith('0') or symbol.startswith('3'):
            return "SZSE"
        else:
            return "UNKNOWN"

    def _format_symbol(self, symbol: str) -> str:
        """
        格式化股票代码（去除后缀，统一为6位数字）

        Args:
            symbol: 原始股票代码

        Returns:
            格式化后的股票代码
        """
        # 移除所有非数字字符
        symbol_clean = re.sub(r'\D', '', symbol)

        # 补齐6位
        if len(symbol_clean) < 6:
            symbol_clean = symbol_clean.zfill(6)

        return symbol_clean

    @staticmethod
    def format_symbol(symbol: str, market: str = "SZSE") -> str:
        """
        格式化股票代码为标准格式

        Args:
            symbol: 原始股票代码
            market: 目标市场

        Returns:
            格式化后的股票代码
        """
        # 移除所有非数字字符
        symbol_clean = re.sub(r'\D', '', symbol)

        # 补齐6位
        if len(symbol_clean) < 6:
            symbol_clean = symbol_clean.zfill(6)

        # 添加后缀
        if market == "SHSE":
            return f"{symbol_clean}.SH"
        elif market == "SZSE":
            return f"{symbol_clean}.SZ"
        else:
            return symbol_clean

    # ==============================================
    # 板块数据方法
    # ==============================================

    def get_industry_sectors(self) -> List[dict]:
        """
        获取行业板块列表

        Returns:
            行业板块列表
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        try:
            df = ak.stock_board_industry_name_em()

            if df.empty:
                return []

            sectors = []
            for _, row in df.iterrows():
                sectors.append({
                    "name": row['板块名称'],
                    "code": row.get('板块代码', ''),
                    "type": "industry"
                })

            logger.info(f"成功获取 {len(sectors)} 个行业板块")
            return sectors

        except Exception as e:
            logger.error(f"获取行业板块列表失败: {e}")
            return []

    def get_concept_sectors(self) -> List[dict]:
        """
        获取概念板块列表

        Returns:
            概念板块列表
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        try:
            df = ak.stock_board_concept_name_em()

            if df.empty:
                return []

            sectors = []
            for _, row in df.iterrows():
                sectors.append({
                    "name": row['板块名称'],
                    "code": row.get('板块代码', ''),
                    "type": "concept"
                })

            logger.info(f"成功获取 {len(sectors)} 个概念板块")
            return sectors

        except Exception as e:
            logger.error(f"获取概念板块列表失败: {e}")
            return []

    def get_region_sectors(self) -> List[dict]:
        """
        获取地域板块列表

        Returns:
            地域板块列表
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        try:
            df = ak.stock_board_region_name_em()

            if df.empty:
                return []

            sectors = []
            for _, row in df.iterrows():
                sectors.append({
                    "name": row['板块名称'],
                    "code": row.get('板块代码', ''),
                    "type": "region"
                })

            logger.info(f"成功获取 {len(sectors)} 个地域板块")
            return sectors

        except Exception as e:
            logger.error(f"获取地域板块列表失败: {e}")
            return []

    def get_sector_stocks(self, sector_name: str, sector_type: str = "industry") -> List[dict]:
        """
        获取板块成分股

        Args:
            sector_name: 板块名称
            sector_type: 板块类型 (industry, concept, region)

        Returns:
            成分股列表
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        try:
            if sector_type == "industry":
                df = ak.stock_board_industry_cons_em(symbol=sector_name)
            elif sector_type == "concept":
                df = ak.stock_board_concept_cons_em(symbol=sector_name)
            elif sector_type == "region":
                df = ak.stock_board_region_cons_em(symbol=sector_name)
            else:
                logger.warning(f"不支持的板块类型: {sector_type}")
                return []

            if df.empty:
                return []

            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "symbol": row['代码'],
                    "name": row['名称'],
                    "price": float(row['最新价']) if '最新价' in row else 0,
                    "change_pct": float(row['涨跌幅']) if '涨跌幅' in row else 0,
                    "change_amount": float(row['涨跌额']) if '涨跌额' in row else 0,
                    "volume": int(row['成交量']) if '成交量' in row else 0,
                    "amount": float(row['成交额']) if '成交额' in row else 0,
                    "market_cap": float(row['总市值']) if '总市值' in row else 0
                })

            logger.info(f"成功获取板块 {sector_name} 的 {len(stocks)} 只成分股")
            return stocks

        except Exception as e:
            logger.error(f"获取板块成分股失败: {e}")
            return []

    def get_sector_stats(self, sector_name: str, sector_type: str = "industry") -> dict:
        """
        获取板块行情统计

        Args:
            sector_name: 板块名称
            sector_type: 板块类型

        Returns:
            板块统计信息
        """
        stocks = self.get_sector_stocks(sector_name, sector_type)

        if not stocks:
            return {
                "name": sector_name,
                "stock_count": 0,
                "avg_change_pct": 0,
                "up_count": 0,
                "down_count": 0,
                "flat_count": 0,
                "total_amount": 0
            }

        # 计算统计指标
        total_change = sum(s['change_pct'] for s in stocks)
        avg_change = total_change / len(stocks) if stocks else 0

        up_count = len([s for s in stocks if s['change_pct'] > 0])
        down_count = len([s for s in stocks if s['change_pct'] < 0])
        flat_count = len(stocks) - up_count - down_count

        total_amount = sum(s['amount'] for s in stocks)

        return {
            "name": sector_name,
            "stock_count": len(stocks),
            "avg_change_pct": round(avg_change, 2),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "total_amount": round(total_amount, 2)
        }

    def get_all_sectors_stats(self, sector_type: str = "industry") -> List[dict]:
        """
        获取所有板块的行情统计

        Args:
            sector_type: 板块类型

        Returns:
            各板块统计信息列表
        """
        if not self.is_available:
            raise DataSourceConnectionError("akshare 未安装")

        try:
            # 获取板块行情数据
            if sector_type == "industry":
                df = ak.stock_board_industry_spot_em()
            elif sector_type == "concept":
                df = ak.stock_board_concept_spot_em()
            else:
                df = ak.stock_board_industry_spot_em()

            if df.empty:
                return []

            stats = []
            for _, row in df.iterrows():
                stats.append({
                    "name": row['板块名称'],
                    "code": row.get('板块代码', ''),
                    "price": float(row['最新价']) if '最新价' in row else 0,
                    "change_pct": float(row['涨跌幅']) if '涨跌幅' in row else 0,
                    "change_amount": float(row['涨跌额']) if '涨跌额' in row else 0,
                    "up_count": int(row['上涨家数']) if '上涨家数' in row else 0,
                    "down_count": int(row['下跌家数']) if '下跌家数' in row else 0,
                    "total_amount": float(row['总市值']) if '总市值' in row else 0,
                    "leading_stock": row.get('领涨股票', ''),
                    "leading_pct": float(row['领涨股票-涨跌幅']) if '领涨股票-涨跌幅' in row else 0
                })

            logger.info(f"成功获取 {len(stats)} 个板块统计")
            return stats

        except Exception as e:
            logger.error(f"获取板块统计失败: {e}")
            return []


# ==============================================
# 便捷函数
# ==============================================

def get_akshare_source() -> AkShareDataSource:
    """
    获取 AkShare 数据源实例

    Returns:
        AkShareDataSource 实例
    """
    return AkShareDataSource()
