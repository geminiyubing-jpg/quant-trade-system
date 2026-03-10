#!/usr/bin/env python3
"""
增量更新机制

自动检测并更新股票数据到最新日期。

功能：
1. 自动检测每只股票的最新数据日期
2. 仅更新缺失的数据（增量更新）
3. 支持定时任务（cron/scheduler）
4. 数据完整性检查
5. 失败重试机制

用法:
    # 运行增量更新（更新所有股票）
    python scripts/incremental_update.py

    # 更新指定股票
    python scripts/incremental_update.py --symbols 000001 600000

    # 模拟运行（不实际更新）
    python scripts/incremental_update.py --dry-run

    # 并发更新（加速）
    python scripts/incremental_update.py --parallel 5
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date, datetime, timedelta
from typing import List, Optional, Set
import argparse
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# 配置
# ==============================================

MAX_WORKERS = 3  # 最大并发数（避免被封 IP）
RETRY_COUNT = 3  # 失败重试次数
DELAY_BETWEEN_REQUESTS = 1.0  # 请求间隔（秒）
MAX_MISSING_DAYS = 10  # 最大缺失天数（超过则告警）


# ==============================================
# 核心功能
# ==============================================

def check_data_completeness(
    symbol: str,
    db_session,
    storage_service: DataStorageService
) -> dict:
    """
    检查数据完整性

    Args:
        symbol: 股票代码
        db_session: 数据库会话
        storage_service: 数据入库服务

    Returns:
        数据完整性报告
    """
    try:
        # 获取最新日期
        latest_timestamp = storage_service.get_latest_timestamp(symbol)

        if not latest_timestamp:
            return {
                "symbol": symbol,
                "status": "NO_DATA",
                "latest_date": None,
                "missing_days": None,
                "need_update": True
            }

        latest_date = latest_timestamp.date()
        today = date.today()

        # 计算缺失天数
        missing_days = (today - latest_date).days

        # 判断是否需要更新
        need_update = missing_days > 0

        return {
            "symbol": symbol,
            "status": "OK" if missing_days == 0 else "NEED_UPDATE",
            "latest_date": latest_date,
            "missing_days": missing_days,
            "need_update": need_update
        }

    except Exception as e:
        logger.error(f"检查 {symbol} 数据完整性失败: {e}")
        return {
            "symbol": symbol,
            "status": "ERROR",
            "error": str(e),
            "need_update": False
        }


def incremental_update_single(
    symbol: str,
    db_session,
    storage_service: DataStorageService,
    data_source,
    data_pipeline: DataPipeline,
    retry_count: int = RETRY_COUNT
) -> dict:
    """
    增量更新单只股票

    Args:
        symbol: 股票代码
        db_session: 数据库会话
        storage_service: 数据入库服务
        data_source: 数据源
        data_pipeline: 数据管道
        retry_count: 重试次数

    Returns:
        更新结果
    """
    result = {
        "symbol": symbol,
        "success": False,
        "records_fetched": 0,
        "records_saved": 0,
        "error": None
    }

    # 检查数据完整性
    completeness = check_data_completeness(symbol, db_session, storage_service)

    if not completeness["need_update"]:
        logger.info(f"[{symbol}] 数据已是最新，无需更新")
        result["success"] = True
        result["message"] = "数据已是最新"
        return result

    if completeness["status"] == "NO_DATA":
        # 首次导入，使用默认日期范围
        start_date = date.today() - timedelta(days=30)  # 默认导入最近 1 个月
    else:
        # 增量更新，从最新日期的第二天开始
        start_date = completeness["latest_date"] + timedelta(days=1)

    end_date = date.today()

    # 检查缺失天数
    missing_days = (end_date - start_date).days
    if missing_days > MAX_MISSING_DAYS:
        logger.warning(
            f"[{symbol}] 缺失天数过多（{missing_days} 天），"
            f"可能存在数据问题"
        )

    logger.info(
        f"[{symbol}] 开始增量更新：{start_date} 到 {end_date} "
        f"（缺失 {missing_days} 天）"
    )

    # 重试机制
    for attempt in range(retry_count):
        try:
            # 获取数据
            prices = data_source.get_stock_prices(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )

            if not prices:
                result["error"] = "未获取到数据"
                logger.warning(f"[{symbol}] 未获取到数据（尝试 {attempt + 1}/{retry_count}）")

                if attempt < retry_count - 1:
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                    continue
                else:
                    return result

            result["records_fetched"] = len(prices)

            # 数据清洗
            cleaned_prices = data_pipeline.process_stock_prices(prices)

            if not cleaned_prices:
                result["error"] = "数据清洗后为空"
                logger.warning(f"[{symbol}] 数据清洗后为空")
                return result

            # 保存到数据库
            records_saved = storage_service.save_stock_prices_upsert(cleaned_prices)
            result["records_saved"] = records_saved

            result["success"] = True
            logger.info(
                f"[{symbol}] ✅ 增量更新成功："
                f"{records_saved} 条记录（缺失 {missing_days} 天）"
            )
            break

        except Exception as e:
            result["error"] = str(e)
            logger.error(
                f"[{symbol}] ❌ 增量更新失败：{e} "
                f"（尝试 {attempt + 1}/{retry_count}）"
            )

            if attempt < retry_count - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS)
            else:
                return result

    return result


def incremental_update_batch(
    symbols: List[str],
    db_session,
    parallel: int = 1,
    dry_run: bool = False
) -> dict:
    """
    批量增量更新

    Args:
        symbols: 股票代码列表
        db_session: 数据库会话
        parallel: 并发数
        dry_run: 模拟运行

    Returns:
        更新汇总
    """
    logger.info("=" * 60)
    logger.info("增量更新任务开始")
    logger.info(f"股票数量: {len(symbols)}")
    logger.info(f"并发数: {parallel}")
    logger.info(f"模拟运行: {'是' if dry_run else '否'}")
    logger.info("=" * 60)

    if dry_run:
        logger.info("⚠️ 模拟运行模式，不会实际更新数据")
        # 仅检查数据完整性
        storage_service = DataStorageService(db_session)

        results = []
        for symbol in symbols:
            completeness = check_data_completeness(symbol, db_session, storage_service)
            results.append(completeness)

        # 打印结果
        print("\n" + "=" * 80)
        print("数据完整性检查结果（模拟运行）")
        print("=" * 80)
        print(f"{'股票代码':<10} {'状态':<15} {'最新日期':<12} {'缺失天数':<10}")
        print("-" * 80)

        need_update_count = 0
        for result in results:
            latest_date_str = result.get('latest_date', 'N/A')
            if isinstance(latest_date_str, date):
                latest_date_str = latest_date_str.strftime('%Y-%m-%d')

            missing_days_str = result.get('missing_days', 'N/A')
            if missing_days_str == 'N/A':
                missing_days_str = 'N/A'
            else:
                missing_days_str = f"{missing_days_str} 天"

            print(
                f"{result['symbol']:<10} "
                f"{result['status']:<15} "
                f"{latest_date_str:<12} "
                f"{missing_days_str:<10}"
            )

            if result.get('need_update'):
                need_update_count += 1

        print("-" * 80)
        print(f"需要更新: {need_update_count}/{len(symbols)}")
        print("=" * 80)

        return {
            "total": len(symbols),
            "need_update": need_update_count,
            "success": 0,
            "failed": 0
        }

    # 实际更新
    data_source = get_akshare_source()
    storage_service = DataStorageService(db_session)
    data_pipeline = DataPipeline()

    # 检查数据源
    if not data_source.is_available:
        logger.error("❌ AkShare 数据源不可用")
        return {"total": len(symbols), "success": 0, "failed": len(symbols)}

    # 并发更新
    results = []
    success_count = 0
    failed_count = 0

    if parallel > 1:
        # 使用线程池并发更新
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(
                    incremental_update_single,
                    symbol,
                    db_session,
                    storage_service,
                    data_source,
                    data_pipeline
                ): symbol
                for symbol in symbols
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1

                # 请求间隔
                time.sleep(DELAY_BETWEEN_REQUESTS)
    else:
        # 顺序更新
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"进度: [{i}/{len(symbols)}]")

            result = incremental_update_single(
                symbol=symbol,
                db_session=db_session,
                storage_service=storage_service,
                data_source=data_source,
                data_pipeline=data_pipeline
            )

            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                failed_count += 1

            # 请求间隔
            if i < len(symbols):
                time.sleep(DELAY_BETWEEN_REQUESTS)

    # 打印汇总
    logger.info("\n" + "=" * 60)
    logger.info("增量更新任务完成")
    logger.info(f"成功: {success_count}/{len(symbols)}")
    logger.info(f"失败: {failed_count}/{len(symbols)}")
    logger.info("=" * 60)

    return {
        "total": len(symbols),
        "success": success_count,
        "failed": failed_count,
        "results": results
    }


def get_all_active_symbols(db_session) -> List[str]:
    """
    获取所有活跃股票代码

    Args:
        db_session: 数据库会话

    Returns:
        股票代码列表
    """
    try:
        stocks = db_session.query(Stock).filter(
            Stock.is_active == True
        ).all()

        symbols = [stock.symbol for stock in stocks]
        logger.info(f"获取到 {len(symbols)} 只活跃股票")
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
        description="增量更新股票数据",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--symbols",
        nargs="+",
        help="指定股票代码（如: 000001 600000）"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help=f"并发更新数量（默认: 1，最大推荐: {MAX_WORKERS}）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行（检查数据完整性，不实际更新）"
    )

    args = parser.parse_args()

    # 限制并发数
    parallel = min(args.parallel, MAX_WORKERS)

    # 获取股票列表
    with get_db_context() as db:
        if args.symbols:
            symbols = args.symbols
        else:
            symbols = get_all_active_symbols(db)

        if not symbols:
            logger.error("未找到要更新的股票")
            return 1

        # 执行增量更新
        summary = incremental_update_batch(
            symbols=symbols,
            db_session=db,
            parallel=parallel,
            dry_run=args.dry_run
        )

        # 打印详细结果
        if not args.dry_run and "results" in summary:
            print("\n" + "=" * 80)
            print("更新结果详情")
            print("=" * 80)
            print(f"{'股票代码':<10} {'状态':<8} {'获取':<8} {'保存':<8} {'错误信息'}")
            print("-" * 80)

            for result in summary["results"]:
                status = "✅ 成功" if result["success"] else "❌ 失败"
                error = result.get("error", "") or ""
                message = result.get("message", "")

                print(
                    f"{result['symbol']:<10} "
                    f"{status:<8} "
                    f"{result['records_fetched']:<8} "
                    f"{result['records_saved']:<8} "
                    f"{error or message}"
                )

            print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
