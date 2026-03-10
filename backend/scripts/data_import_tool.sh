#!/bin/bash
# ==============================================
# 数据导入快速启动脚本
# ==============================================

set -e  # 遇到错误立即退出

PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_PATH"

echo "============================================"
echo "Quant-Trade System 数据导入工具"
echo "============================================"
echo ""

# 显示菜单
show_menu() {
    echo "请选择操作："
    echo "1. 检查数据状态"
    echo "2. 导入单只股票（最近3个月）"
    echo "3. 导入多只股票（最近3个月）"
    echo "4. 导入沪深300成分股（最近3个月）"
    echo "5. 增量更新所有股票"
    echo "6. 检查数据完整性"
    echo "7. 查看数据质量报告"
    echo "0. 退出"
    echo ""
}

# 检查数据状态
check_data_status() {
    echo ">>> 检查数据状态..."
    python3 -c "
import sys
sys.path.insert(0, '.')
from src.core.database import get_db_context
from sqlalchemy import text

with get_db_context() as db:
    # 股票数量
    result = db.execute(text('SELECT COUNT(*) FROM stocks'))
    stock_count = result.scalar()

    # 活跃股票
    result = db.execute(text('SELECT COUNT(*) FROM stocks WHERE status = :status'), {'status': 'active'})
    active_count = result.scalar()

    # 价格数据
    result = db.execute(text('SELECT COUNT(*) FROM stock_prices'))
    price_count = result.scalar()

    # 最新日期
    result = db.execute(text('SELECT MAX(trade_date) FROM stock_prices'))
    latest_date = result.scalar()

    # 数据覆盖范围
    result = db.execute(text('SELECT MIN(trade_date), MAX(trade_date) FROM stock_prices'))
    min_date, max_date = result.fetchone()

    print(f'✅ 股票总数: {stock_count}')
    print(f'✅ 活跃股票: {active_count}')
    print(f'✅ 价格数据: {price_count:,} 条')
    print(f'✅ 最新日期: {latest_date}')
    print(f'✅ 数据范围: {min_date} 到 {max_date}')
" 2>&1 | grep -v "INFO sqlalchemy"
    echo ""
}

# 导入单只股票
import_single_stock() {
    read -p "请输入股票代码（如 000001.SZ）: " symbol

    if [ -z "$symbol" ]; then
        echo "❌ 股票代码不能为空"
        return
    fi

    echo ">>> 开始导入 $symbol ..."
    python3 scripts/batch_import_stock_data.py \
        --symbol "$symbol" \
        --start-date 2024-12-01 \
        --end-date $(date +%Y-%m-%d) \
        2>&1 | grep -v "INFO sqlalchemy"

    echo ""
    echo "✅ 导入完成！"
    echo ""
}

# 导入多只股票
import_multiple_stocks() {
    read -p "请输入股票代码（空格分隔，如 000001.SZ 600000.SH）: " symbols

    if [ -z "$symbols" ]; then
        echo "❌ 股票代码不能为空"
        return
    fi

    echo ">>> 开始导入多只股票..."
    python3 scripts/batch_import_stock_data.py \
        --symbols $symbols \
        --start-date 2024-12-01 \
        --end-date $(date +%Y-%m-%d) \
        2>&1 | grep -v "INFO sqlalchemy"

    echo ""
    echo "✅ 导入完成！"
    echo ""
}

# 导入沪深300成分股
import_hs300() {
    echo ">>> 开始导入沪深300成分股..."

    # 获取前100只活跃股票作为测试
    python3 -c "
import sys
sys.path.insert(0, '.')
from src.core.database import get_db_context
from src.models.stock import Stock

with get_db_context() as db:
    stocks = db.query(Stock).filter(
        Stock.status == 'active'
    ).limit(100).all()

    symbols = [s.symbol for s in stocks]
    print(' '.join(symbols))
" 2>&1 | grep -v "INFO sqlalchemy" | head -1 > /tmp/hs300_symbols.txt

    symbols=$(cat /tmp/hs300_symbols.txt)

    if [ -z "$symbols" ]; then
        echo "❌ 未找到股票列表"
        return
    fi

    echo "将导入以下股票: $symbols"
    read -p "确认继续? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 scripts/batch_import_stock_data.py \
            --symbols $symbols \
            --start-date 2024-12-01 \
            --end-date $(date +%Y-%m-%d) \
            2>&1 | tee logs/import_hs300_$(date +%Y%m%d_%H%M%S).log | grep -v "INFO sqlalchemy"

        echo ""
        echo "✅ 导入完成！日志已保存到 logs/"
        echo ""
    else
        echo "❌ 已取消"
    fi
}

# 增量更新
incremental_update() {
    echo ">>> 开始增量更新所有股票..."
    python3 scripts/incremental_update.py 2>&1 | grep -v "INFO sqlalchemy"
    echo ""
    echo "✅ 更新完成！"
    echo ""
}

# 检查数据完整性
check_completeness() {
    echo ">>> 检查数据完整性..."
    python3 scripts/incremental_update.py --dry-run 2>&1 | grep -v "INFO sqlalchemy"
    echo ""
}

# 数据质量报告
quality_report() {
    echo ">>> 生成数据质量报告..."
    python3 -c "
import sys
sys.path.insert(0, '.')
from src.core.database import get_db_context
from sqlalchemy import text
from datetime import date, timedelta

with get_db_context() as db:
    # 数据覆盖率
    result = db.execute(text('''
        SELECT
            COUNT(DISTINCT symbol) as total_stocks,
            COUNT(DISTINCT CASE WHEN trade_date >= :start_date THEN symbol END) as recent_stocks,
            COUNT(*) as total_records
        FROM stock_prices
    '''), {'start_date': (date.today() - timedelta(days=90)).isoformat()})

    row = result.fetchone()
    coverage = (row[1] / row[0] * 100) if row[0] > 0 else 0

    print(f'数据覆盖率: {coverage:.2f}% ({row[1]}/{row[0]} 只股票有最近90天数据)')
    print(f'总记录数: {row[2]:,}')

    # 缺失数据检查
    result = db.execute(text('''
        SELECT symbol, MAX(trade_date) as latest_date,
               (:today - MAX(trade_date)) as missing_days
        FROM stock_prices
        GROUP BY symbol
        HAVING (:today - MAX(trade_date)) > 5
        ORDER BY missing_days DESC
        LIMIT 10
    '''), {'today': date.today()})

    print('')
    print('缺失数据最多的前10只股票:')
    print('-' * 60)
    for row in result:
        print(f'{row[0]:<12} 最新: {row[1]}  缺失: {row[2]} 天')

    print('')
    print('✅ 数据质量报告生成完成')
" 2>&1 | grep -v "INFO sqlalchemy"
    echo ""
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项 (0-7): " choice

    case $choice in
        1)
            check_data_status
            ;;
        2)
            import_single_stock
            ;;
        3)
            import_multiple_stocks
            ;;
        4)
            import_hs300
            ;;
        5)
            incremental_update
            ;;
        6)
            check_completeness
            ;;
        7)
            quality_report
            ;;
        0)
            echo "👋 再见！"
            exit 0
            ;;
        *)
            echo "❌ 无效选项，请重新选择"
            ;;
    esac

    read -p "按 Enter 键继续..."
    clear
done
