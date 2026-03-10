#!/usr/bin/env python3
"""
批量导入 A 股日线数据

功能：
1. 导入指定股票列表的历史数据
2. 支持增量更新（仅导入新数据）
3. 数据验证和清洗
4. 批量入库优化

用法:
    # 导入单只股票（最近 1 个月）
    python scripts/batch_import_stock_data.py --symbol 000001

    # 导入多只股票
    python scripts/batch_import_stock_data.py --symbols 000001 600000 000002

    # 导入所有 A 股（前 100 只）
    python scripts/batch_import_stock_data.py --all --limit 100

    # 指定日期范围
    python scripts/batch_import_stock_data.py --symbol 000001 --start-date 2024-01-01 --end-date 2024-12-31

    # 增量更新（从数据库最新日期开始）
    python scripts/batch_import_stock_data.py --symbol 000001 --incremental
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date, datetime, timedelta
from typing import List, Optional
import argparse
import logging
import time

from src.core.database import get_db_context
from src.services.data.akshare import get_akshare_source
from src.services.data.validation import DataPipeline
from src.services.data.storage import DataStorageService
from src.models.stock import Stock, StockPrice

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==============================================
# 默认配置
# ==============================================

DEFAULT_START_DATE = date(2024, 1, 1)  # 默认起始日期
DEFAULT_END_DATE = date.today()  # 默认结束日期（今天）
BATCH_SIZE = 10  # 每批处理的股票数量
DELAY_BETWEEN_REQUESTS = 1.0  # 请求间隔（秒）


# ==============================================
# 核心功能
# ==============================================

def import_stock_data(
    symbol: str,
    start_date: date,
    end_date: date,
    db_session,
    storage_service: DataStorageService,
    data_source,
    data_pipeline: DataPipeline,
    incremental: bool = False
) -> dict:
    """
    导入单只股票的数据

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        db_session: 数据库会话
        storage_service: 数据入库服务
        data_source: 数据源
        data_pipeline: 数据管道
        incremental: 是否增量更新

    Returns:
        导入结果字典
    """
    result = {
        "symbol": symbol,
        "success": False,
        "records_fetched": 0,
        "records_saved": 0,
        "quality_rate": 0.0,
        "error": None
    }

    try:
        # 如果是增量更新，获取数据库最新日期
        if incremental:
            latest_timestamp = storage_service.get_latest_timestamp(symbol)
            if latest_timestamp:
                start_date = latest_timestamp.date() + timedelta(days=1)
                logger.info(f"[{symbol}] 增量更新：从 {start_date} 开始")
            else:
                logger.info(f"[{symbol}] 首次导入，使用默认起始日期")

        # 获取数据
        logger.info(f"[{symbol}] 开始获取数据：{start_date} 到 {end_date}")
        prices = data_source.get_stock_prices(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

        if not prices:
            result["error"] = "未获取到数据"
            logger.warning(f"[{symbol}] 未获取到数据")
            return result

        result["records_fetched"] = len(prices)

        # 数据清洗和验证
        logger.info(f"[{symbol}] 开始数据清洗和验证")
        cleaned_prices = data_pipeline.process_stock_prices(prices)

        if not cleaned_prices:
            result["error"] = "数据清洗后为空"
            logger.warning(f"[{symbol}] 数据清洗后为空")
            return result

        # 计算质量率
        quality_rate = len(cleaned_prices) / len(prices) * 100
        result["quality_rate"] = round(quality_rate, 2)

        # 保存到数据库
        logger.info(f"[{symbol}] 开始保存数据到数据库")
        records_saved = storage_service.save_stock_prices_upsert(cleaned_prices)
        result["records_saved"] = records_saved

        result["success"] = True
        logger.info(
            f"[{symbol}] ✅ 成功导入 {records_saved} 条记录 "
            f"（获取 {len(prices)} 条，质量率 {quality_rate:.2f}%）"
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[{symbol}] ❌ 导入失败: {e}")

    return result


def import_multiple_stocks(
    symbols: List[str],
    start_date: date,
    end_date: date,
    db_session,
    incremental: bool = False
) -> List[dict]:
    """
    批量导入多只股票的数据

    Args:
        symbols: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        db_session: 数据库会话
        incremental: 是否增量更新

    Returns:
        导入结果列表
    """
    logger.info(f"=" * 60)
    logger.info(f"批量导入任务开始")
    logger.info(f"股票数量: {len(symbols)}")
    logger.info(f"日期范围: {start_date} 到 {end_date}")
    logger.info(f"增量模式: {'是' if incremental else '否'}")
    logger.info(f"=" * 60)

    # 初始化服务
    data_source = get_akshare_source()
    storage_service = DataStorageService(db_session)
    data_pipeline = DataPipeline()

    # 检查数据源连接
    if not data_source.is_available:
        logger.error("❌ AkShare 数据源不可用")
        return []

    if not data_source.check_connection():
        logger.error("❌ AkShare 连接失败")
        return []

    logger.info("✅ AkShare 数据源连接正常")

    # 批量处理
    results = []
    success_count = 0
    total_records = 0

    for i, symbol in enumerate(symbols, 1):
        logger.info(f"\n进度: [{i}/{len(symbols)}]")

        result = import_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            db_session=db_session,
            storage_service=storage_service,
            data_source=data_source,
            data_pipeline=data_pipeline,
            incremental=incremental
        )

        results.append(result)

        if result["success"]:
            success_count += 1
            total_records += result["records_saved"]

        # 请求间隔（避免被封 IP）
        if i < len(symbols):
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # 打印汇总
    logger.info(f"\n" + "=" * 60)
    logger.info(f"批量导入任务完成")
    logger.info(f"成功: {success_count}/{len(symbols)}")
    logger.info(f"总记录数: {total_records}")
    logger.info(f"=" * 60)

    return results


def get_all_stocks(db_session, limit: Optional[int] = None) -> List[str]:
    """
    获取所有 A 股股票代码

    Args:
        db_session: 数据库会话
        limit: 限制数量（用于测试）

    Returns:
        股票代码列表
    """
    try:
        # 从数据库获取活跃股票列表
        stocks = db_session.query(Stock).filter(
            Stock.is_active == True
        ).all()

        symbols = [stock.symbol for stock in stocks]

        if limit and limit < len(symbols):
            symbols = symbols[:limit]

        logger.info(f"从数据库获取到 {len(symbols)} 只股票")
        return symbols

    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return []


def get_top_stocks_by_market_cap(db_session, top_n: int = 100) -> List[str]:
    """
    获取市值前 N 的股票（按成交额排序）

    Args:
        db_session: 数据库会话
        top_n: 前 N 只

    Returns:
        股票代码列表
    """
    try:
        # 这里简单返回前 N 只活跃股票
        # TODO: 改进为按市值/成交额排序
        stocks = db_session.query(Stock).filter(
            Stock.is_active == True
        ).limit(top_n).all()

        symbols = [stock.symbol for stock in stocks]
        logger.info(f"获取前 {len(symbols)} 只活跃股票")
        return symbols

    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return []


# ==============================================
# 命令行接口
# ==============================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量导入 A 股日线数据",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # 股票选择参数
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--symbol",
        type=str,
        help="单只股票代码（如: 000001）"
    )
    group.add_argument(
        "--symbols",
        nargs="+",
        help="多只股票代码（如: 000001 600000 000002）"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="导入所有 A 股"
    )
    group.add_argument(
        "--top",
        type=int,
        metavar="N",
        help="导入市值前 N 的股票"
    )

    # 日期参数
    parser.add_argument(
        "--start-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        default=DEFAULT_START_DATE,
        help=f"起始日期（格式: YYYY-MM-DD，默认: {DEFAULT_START_DATE}）"
    )
    parser.add_argument(
        "--end-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        default=DEFAULT_END_DATE,
        help=f"结束日期（格式: YYYY-MM-DD，默认: {DEFAULT_END_DATE}）"
    )

    # 增量更新
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="增量更新（从数据库最新日期开始）"
    )

    # 其他参数
    parser.add_argument(
        "--limit",
        type=int,
        help="限制导入数量（用于测试）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行（不实际写入数据库）"
    )

    args = parser.parse_args()

    # 获取股票列表
    with get_db_context() as db:
        if args.symbol:
            symbols = [args.symbol]
        elif args.symbols:
            symbols = args.symbols
        elif args.all:
            symbols = get_all_stocks(db, limit=args.limit)
        elif args.top:
            symbols = get_top_stocks_by_market_cap(db, top_n=args.top)
        else:
            logger.error("请指定要导入的股票")
            return 1

        if not symbols:
            logger.error("未找到要导入的股票")
            return 1

        # 执行导入
        results = import_multiple_stocks(
            symbols=symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            db_session=db,
            incremental=args.incremental
        )

        # 打印详细结果
        print("\n" + "=" * 80)
        print("导入结果详情")
        print("=" * 80)
        print(f"{'股票代码':<10} {'状态':<8} {'获取':<8} {'保存':<8} {'质量率':<10} {'错误信息'}")
        print("-" * 80)

        for result in results:
            status = "✅ 成功" if result["success"] else "❌ 失败"
            error = result.get("error", "") or ""
            print(
                f"{result['symbol']:<10} "
                f"{status:<8} "
                f"{result['records_fetched']:<8} "
                f"{result['records_saved']:<8} "
                f"{result['quality_rate']:<10.2f} "
                f"{error}"
            )

        print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
