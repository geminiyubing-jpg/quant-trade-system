"""
==============================================
WebSocket 实时行情 - 行情数据服务
==============================================
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional

import akshare as ak
from src.core.config import settings

from src.schemas.market_data import MarketQuote
from src.services.websocket.connection_manager import connection_manager
from src.services.websocket.redis_manager import redis_manager

logger = logging.getLogger(__name__)


class MarketDataService:
    """行情数据服务 - 负责获取、缓存和推送行情数据"""

    def __init__(self):
        """初始化行情数据服务"""
        self.is_running = False
        self.update_task = None
        # 更新间隔（秒）
        self.update_interval = 2  # 2 秒更新一次
        # 模拟模式（如果为 True，生成模拟数据）
        self.simulated_mode = settings.debug  # 开发环境使用模拟数据

        # 预定义股票列表（用于模拟）
        self.simulated_stocks = {
            "000001.SZ": {"name": "平安银行", "base_price": 10.50},
            "000002.SZ": {"name": "万科A", "base_price": 8.75},
            "000858.SZ": {"name": "五粮液", "base_price": 135.20},
            "600000.SH": {"name": "浦发银行", "base_price": 7.85},
            "600036.SH": {"name": "招商银行", "base_price": 32.40},
            "600519.SH": {"name": "贵州茅台", "base_price": 1680.50},
            "600887.SH": {"name": "伊利股份", "base_price": 29.30},
            "000725.SZ": {"name": "京东方A", "base_price": 3.85},
        }

    async def start(self):
        """启动行情更新任务"""
        if self.is_running:
            logger.warning("⚠️  行情服务已在运行中")
            return

        self.is_running = True
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("🚀 行情数据服务已启动")

    async def stop(self):
        """停止行情更新任务"""
        if not self.is_running:
            return

        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 行情数据服务已停止")

    async def _update_loop(self):
        """
        行情更新循环
        """
        logger.info("📈 行情更新循环已启动")
        while self.is_running:
            try:
                await self._update_and_broadcast()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                logger.info("📈 行情更新循环已停止")
                break
            except Exception as e:
                logger.error(f"❌ 行情更新异常: {e}")
                await asyncio.sleep(self.update_interval)

    async def _update_and_broadcast(self):
        """
        更新行情数据并推送给订阅者
        """
        try:
            # 获取所有被订阅的股票
            subscribed_symbols = await self._get_subscribed_symbols()
            if not subscribed_symbols:
                return

            logger.debug(f"🔄 更新 {len(subscribed_symbols)} 只股票的行情")

            # 获取行情数据
            quotes = await self._fetch_quotes(subscribed_symbols)

            # 缓存到 Redis 并推送
            for quote in quotes:
                # 缓存到 Redis
                redis_manager.save_quote(quote.symbol, quote.model_dump(mode='json'), ttl=5)

                # 推送给订阅者
                await connection_manager.broadcast_to_subscribers(
                    quote.symbol, {"type": "quote", "data": quote.model_dump(mode='json')}
                )

        except Exception as e:
            logger.error(f"❌ 更新和广播行情失败: {e}")

    async def _get_subscribed_symbols(self) -> List[str]:
        """
        获取所有被订阅的股票代码

        Returns:
            List[str]: 股票代码列表
        """
        try:
            # 扫描 Redis 中所有的订阅者 key
            # pattern = "market:subscribers:*"
            # keys = redis_manager.redis_client.keys(pattern)
            # symbols = [key.split(":")[-1] for key in keys]
            # 简化：从预定义列表中返回所有（实际应该从 Redis 获取）
            return list(self.simulated_stocks.keys())
        except Exception as e:
            logger.error(f"❌ 获取订阅列表失败: {e}")
            return []

    async def _fetch_quotes(self, symbols: List[str]) -> List[MarketQuote]:
        """
        获取行情数据（支持模拟和真实数据）

        Args:
            symbols: 股票代码列表

        Returns:
            List[MarketQuote]: 行情数据列表
        """
        if self.simulated_mode:
            return await self._fetch_simulated_quotes(symbols)
        else:
            return await self._fetch_real_quotes(symbols)

    async def _fetch_simulated_quotes(self, symbols: List[str]) -> List[MarketQuote]:
        """
        生成模拟行情数据（用于开发测试）

        Args:
            symbols: 股票代码列表

        Returns:
            List[MarketQuote]: 模拟行情数据
        """
        quotes = []
        now = datetime.now()

        for symbol in symbols:
            try:
                # 从预定义数据中获取股票信息
                stock_info = self.simulated_stocks.get(symbol)
                if not stock_info:
                    continue

                base_price = stock_info["base_price"]

                # 随机生成价格变动（-2% ~ +2%）
                change_pct = random.uniform(-2.0, 2.0)
                change = base_price * (change_pct / 100)
                price = base_price + change

                # 生成其他数据
                quote = MarketQuote(
                    symbol=symbol,
                    name=stock_info["name"],
                    price=round(price, 2),
                    change=round(change, 2),
                    change_pct=round(change_pct, 2),
                    volume=random.randint(100000, 5000000),
                    amount=round(random.uniform(1000000, 100000000), 2),
                    bid_price=round(price - 0.01, 2),
                    ask_price=round(price + 0.01, 2),
                    high=round(price * 1.02, 2),
                    low=round(price * 0.98, 2),
                    open=round(base_price * random.uniform(0.98, 1.02), 2),
                    prev_close=base_price,
                    timestamp=now,
                )
                quotes.append(quote)

            except Exception as e:
                logger.error(f"❌ 生成模拟行情失败 {symbol}: {e}")

        return quotes

    async def _fetch_real_quotes(self, symbols: List[str]) -> List[MarketQuote]:
        """
        获取真实行情数据（从 AkShare）

        Args:
            symbols: 股票代码列表

        Returns:
            List[MarketQuote]: 真实行情数据
        """
        quotes = []

        # AkShare 需要同步调用，使用线程池
        loop = asyncio.get_event_loop()

        for symbol in symbols:
            try:
                # 转换股票代码格式（000001.SZ -> sz000001）
                if symbol.endswith(".SZ"):
                    ak_symbol = f"sz{symbol[:6]}"
                elif symbol.endswith(".SH"):
                    ak_symbol = f"sh{symbol[:6]}"
                else:
                    continue

                # 在线程池中调用 AkShare
                df = await loop.run_in_executor(None, ak.stock_zh_a_spot_em)
                stock_data = df[df["代码"] == ak_symbol[:7]]

                if stock_data.empty:
                    logger.warning(f"⚠️  未找到股票数据: {symbol}")
                    continue

                row = stock_data.iloc[0]
                quote = MarketQuote(
                    symbol=symbol,
                    name=row.get("名称", ""),
                    price=float(row.get("最新价", 0)),
                    change=float(row.get("涨跌额", 0)),
                    change_pct=float(row.get("涨跌幅", 0)),
                    volume=int(row.get("成交量", 0)),
                    amount=float(row.get("成交额", 0)),
                    bid_price=float(row.get("买一价", 0)),
                    ask_price=float(row.get("卖一价", 0)),
                    high=float(row.get("最高", 0)),
                    low=float(row.get("最低", 0)),
                    open=float(row.get("今开", 0)),
                    prev_close=float(row.get("昨收", 0)),
                    timestamp=datetime.now(),
                )
                quotes.append(quote)

            except Exception as e:
                logger.error(f"❌ 获取真实行情失败 {symbol}: {e}")

        return quotes

    async def get_current_quotes(self, symbols: List[str]) -> Dict[str, MarketQuote]:
        """
        获取当前行情数据（优先从缓存）

        Args:
            symbols: 股票代码列表

        Returns:
            Dict[str, MarketQuote]: {symbol: quote}
        """
        result = {}

        # 先从 Redis 缓存获取
        cached_data = redis_manager.get_quotes_batch(symbols)

        # 缓存命中的
        for symbol, data in cached_data.items():
            try:
                result[symbol] = MarketQuote(**data)
            except Exception as e:
                logger.error(f"❌ 解析缓存行情失败 {symbol}: {e}")

        # 缓存未命中的，实时获取
        missed_symbols = [s for s in symbols if s not in result]
        if missed_symbols:
            fresh_quotes = await self._fetch_quotes(missed_symbols)
            for quote in fresh_quotes:
                result[quote.symbol] = quote
                # 缓存到 Redis
                redis_manager.save_quote(quote.symbol, quote.model_dump(mode='json'), ttl=5)

        return result

    def get_simulated_stocks(self) -> Dict[str, dict]:
        """
        获取可用的模拟股票列表

        Returns:
            Dict: {symbol: {name, base_price}}
        """
        return self.simulated_stocks.copy()


# 全局行情数据服务实例
market_data_service = MarketDataService()
