#!/usr/bin/env python3
"""
Quant-Trade System - 扩展测试数据初始化脚本

为以下模块添加测试数据：
- 自选股 (watchlist_items)
- 价格预警 (price_alerts)
- 系统配置 (system_config)
- 每日交易统计 (daily_trade_stats)

用法:
    cd backend
    python database/scripts/seed_extended_data.py
"""

import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from src.core.database import SessionLocal

# ============================================================
# 扩展测试数据配置
# ============================================================

# 自选股配置
WATCHLIST_STOCKS = [
    {'symbol': '300750.SZ', 'name': '宁德时代', 'notes': '新能源龙头，关注产能扩张'},
    {'symbol': '002594.SZ', 'name': '比亚迪', 'notes': '新能源汽车领军企业'},
    {'symbol': '688981.SH', 'name': '中芯国际', 'notes': '半导体核心资产'},
    {'symbol': '000063.SZ', 'name': '中兴通讯', 'notes': '通信设备龙头'},
    {'symbol': '000858.SZ', 'name': '五粮液', 'notes': '白酒龙头，业绩稳定'},
    {'symbol': '600887.SH', 'name': '伊利股份', 'notes': '乳制品龙头'},
    {'symbol': '000568.SZ', 'name': '泸州老窖', 'notes': '高端白酒'},
    {'symbol': '600036.SH', 'name': '招商银行', 'notes': '银行龙头'},
    {'symbol': '601318.SH', 'name': '中国平安', 'notes': '保险龙头'},
    {'symbol': '600030.SH', 'name': '中信证券', 'notes': '券商龙头'},
    {'symbol': '300760.SZ', 'name': '迈瑞医疗', 'notes': '医疗器械龙头'},
    {'symbol': '600276.SH', 'name': '恒瑞医药', 'notes': '创新药龙头'},
    {'symbol': '601012.SH', 'name': '隆基绿能', 'notes': '光伏龙头'},
    {'symbol': '600900.SH', 'name': '长江电力', 'notes': '水电龙头，防御性资产'},
]

# 价格预警配置
PRICE_ALERTS = [
    {'symbol': '300750.SZ', 'alert_type': 'PRICE_ABOVE', 'target_value': 200.00},
    {'symbol': '300750.SZ', 'alert_type': 'PRICE_BELOW', 'target_value': 160.00},
    {'symbol': '000858.SZ', 'alert_type': 'PRICE_ABOVE', 'target_value': 170.00},
    {'symbol': '000858.SZ', 'alert_type': 'PRICE_BELOW', 'target_value': 140.00},
    {'symbol': '600036.SH', 'alert_type': 'PRICE_ABOVE', 'target_value': 40.00},
    {'symbol': '600036.SH', 'alert_type': 'PRICE_BELOW', 'target_value': 30.00},
    {'symbol': '002594.SZ', 'alert_type': 'CHANGE_PCT_ABOVE', 'target_value': 5.00},
    {'symbol': '601318.SH', 'alert_type': 'CHANGE_PCT_BELOW', 'target_value': -3.00},
]

# 系统配置
SYSTEM_CONFIGS = [
    {'key': 'trading.enabled', 'value': 'true', 'description': '是否启用交易功能'},
    {'key': 'trading.paper_mode', 'value': 'true', 'description': '是否为模拟交易模式'},
    {'key': 'trading.market_open_time', 'value': '09:30:00', 'description': '股市开盘时间'},
    {'key': 'trading.market_close_time', 'value': '15:00:00', 'description': '股市收盘时间'},
    {'key': 'risk.max_position_ratio', 'value': '0.8', 'description': '最大持仓比例'},
    {'key': 'risk.default_stop_loss', 'value': '0.05', 'description': '默认止损比例'},
    {'key': 'risk.daily_loss_limit', 'value': '0.03', 'description': '单日最大亏损限制'},
    {'key': 'data.update_interval', 'value': '3000', 'description': '数据更新间隔(毫秒)'},
    {'key': 'notification.email_enabled', 'value': 'true', 'description': '是否启用邮件通知'},
    {'key': 'notification.sms_enabled', 'value': 'false', 'description': '是否启用短信通知'},
    {'key': 'backtest.default_capital', 'value': '1000000', 'description': '回测默认初始资金'},
    {'key': 'backtest.commission_rate', 'value': '0.0003', 'description': '回测佣金费率'},
]


def get_user_id(db, username: str = 'trader_zhang') -> str:
    """获取用户ID"""
    result = db.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {'username': username}
    )
    user_id = result.scalar()
    if not user_id:
        result = db.execute(text("SELECT id FROM users WHERE username = 'test_user'"))
        user_id = result.scalar()
    return user_id


def seed_watchlist(db, user_id: str) -> None:
    """插入自选股"""
    print("\n⭐ 插入自选股...")

    # 先创建自选股分组
    result = db.execute(
        text("SELECT id FROM watchlist_groups WHERE user_id = :user_id AND name = '默认分组'"),
        {'user_id': user_id}
    )
    group_id = result.scalar()

    if not group_id:
        group_id = str(uuid.uuid4())
        db.execute(
            text("INSERT INTO watchlist_groups (id, user_id, name, sort_order, created_at) VALUES (:id, :user_id, '默认分组', 0, NOW())"),
            {'id': group_id, 'user_id': user_id}
        )

    inserted = 0
    for i, stock in enumerate(WATCHLIST_STOCKS):
        result = db.execute(
            text("SELECT id FROM watchlist_items WHERE group_id = :group_id AND symbol = :symbol"),
            {'group_id': group_id, 'symbol': stock['symbol']}
        )
        if result.scalar():
            continue

        item_id = str(uuid.uuid4())
        db.execute(
            text("INSERT INTO watchlist_items (id, user_id, group_id, symbol, notes, sort_order, created_at) VALUES (:id, :user_id, :group_id, :symbol, :notes, :sort_order, NOW())"),
            {'id': item_id, 'user_id': user_id, 'group_id': group_id, 'symbol': stock['symbol'], 'notes': stock['notes'], 'sort_order': i}
        )
        inserted += 1
        print(f"   ✅ 添加自选股: {stock['symbol']} - {stock['name']}")

    db.commit()
    print(f"   共插入 {inserted} 条自选股记录")


def seed_price_alerts(db, user_id: str) -> None:
    """插入价格预警"""
    print("\n🔔 插入价格预警...")

    inserted = 0
    for alert in PRICE_ALERTS:
        result = db.execute(
            text("SELECT id FROM price_alerts WHERE user_id = :user_id AND symbol = :symbol AND alert_type = :alert_type"),
            {'user_id': user_id, 'symbol': alert['symbol'], 'alert_type': alert['alert_type']}
        )
        if result.scalar():
            continue

        alert_id = str(uuid.uuid4())
        db.execute(
            text("INSERT INTO price_alerts (id, user_id, symbol, alert_type, target_value, is_active, created_at) VALUES (:id, :user_id, :symbol, :alert_type, :target_value, true, NOW())"),
            {'id': alert_id, 'user_id': user_id, 'symbol': alert['symbol'], 'alert_type': alert['alert_type'], 'target_value': Decimal(str(alert['target_value']))}
        )
        inserted += 1
        print(f"   ✅ 创建预警: {alert['symbol']} {alert['alert_type']} {alert['target_value']}")

    db.commit()
    print(f"   共插入 {inserted} 条价格预警")


def seed_system_configs(db) -> None:
    """插入系统配置"""
    print("\n⚙️  插入系统配置...")

    inserted = 0
    for config in SYSTEM_CONFIGS:
        result = db.execute(
            text("SELECT key FROM system_config WHERE key = :key"),
            {'key': config['key']}
        )
        if result.scalar():
            db.execute(
                text("UPDATE system_config SET value = :value, description = :description WHERE key = :key"),
                {'key': config['key'], 'value': config['value'], 'description': config['description']}
            )
        else:
            db.execute(
                text("INSERT INTO system_config (key, value, description) VALUES (:key, :value, :description)"),
                config
            )
            inserted += 1
        print(f"   ✅ 配置: {config['key']} = {config['value']}")

    db.commit()
    print(f"   共插入 {inserted} 条新配置")


def seed_daily_trade_stats(db, user_id: str) -> None:
    """插入每日交易统计"""
    print("\n📊 插入每日交易统计...")

    base_date = datetime.utcnow().date()
    inserted = 0

    for i in range(30):
        date = base_date - timedelta(days=29 - i)

        # 周末不交易
        if date.weekday() >= 5:
            continue

        result = db.execute(
            text("SELECT id FROM daily_trade_stats WHERE user_id = :user_id AND trade_date = :trade_date"),
            {'user_id': user_id, 'trade_date': date}
        )
        if result.scalar():
            continue

        stat_id = str(uuid.uuid4())
        total_orders = random.randint(5, 20)
        filled_orders = int(total_orders * random.uniform(0.8, 1.0))
        buy_count = random.randint(1, filled_orders)
        sell_count = filled_orders - buy_count

        db.execute(
            text("""
                INSERT INTO daily_trade_stats
                (id, user_id, trade_date, execution_mode, total_orders, filled_orders, canceled_orders, rejected_orders,
                 buy_count, sell_count, buy_volume, sell_volume, buy_amount, sell_amount, total_commission,
                 total_stamp_duty, total_transfer_fee, total_fees, realized_pnl, created_at)
                VALUES
                (:id, :user_id, :trade_date, 'PAPER', :total_orders, :filled_orders, :canceled_orders, :rejected_orders,
                 :buy_count, :sell_count, :buy_volume, :sell_volume, :buy_amount, :sell_amount, :total_commission,
                 :total_stamp_duty, :total_transfer_fee, :total_fees, :realized_pnl, NOW())
            """),
            {
                'id': stat_id,
                'user_id': user_id,
                'trade_date': date,
                'total_orders': total_orders,
                'filled_orders': filled_orders,
                'canceled_orders': random.randint(0, 3),
                'rejected_orders': max(0, total_orders - filled_orders - random.randint(0, 2)),
                'buy_count': buy_count,
                'sell_count': sell_count,
                'buy_volume': random.randint(10000, 100000),
                'sell_volume': random.randint(10000, 100000),
                'buy_amount': Decimal(str(random.uniform(50000, 500000))),
                'sell_amount': Decimal(str(random.uniform(50000, 500000))),
                'total_commission': Decimal(str(random.uniform(50, 500))),
                'total_stamp_duty': Decimal(str(random.uniform(30, 300))),
                'total_transfer_fee': Decimal(str(random.uniform(5, 50))),
                'total_fees': Decimal(str(random.uniform(100, 900))),
                'realized_pnl': Decimal(str(random.uniform(-5000, 15000))),
            }
        )
        inserted += 1

    db.commit()
    print(f"   ✅ 插入 {inserted} 条交易统计记录")


def verify_data(db) -> None:
    """验证数据"""
    print("\n🔍 验证测试数据...")

    tables = [
        ('watchlist_groups', '自选股分组'),
        ('watchlist_items', '自选股'),
        ('price_alerts', '价格预警'),
        ('system_config', '系统配置'),
        ('daily_trade_stats', '交易统计'),
        ('strategies', '策略'),
        ('backtest_jobs', '回测任务'),
        ('orders', '订单'),
        ('positions', '持仓'),
    ]

    for table, name in tables:
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"   {name}: {count} 条记录")
        except Exception as e:
            print(f"   {name}: 查询失败 ({e})")


def main():
    """主函数"""
    print("=" * 60)
    print("🌱 Quant-Trade System - 扩展测试数据初始化")
    print("=" * 60)

    db = SessionLocal()
    try:
        user_id = get_user_id(db)
        if not user_id:
            print("❌ 未找到测试用户，请先运行基础测试数据脚本")
            return

        print(f"📝 使用用户ID: {user_id}")

        # 1. 插入自选股
        seed_watchlist(db, user_id)

        # 2. 插入价格预警
        seed_price_alerts(db, user_id)

        # 3. 插入系统配置
        seed_system_configs(db)

        # 4. 插入每日交易统计
        seed_daily_trade_stats(db, user_id)

        # 5. 验证数据
        verify_data(db)

        print("\n" + "=" * 60)
        print("✅ 扩展测试数据初始化完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    main()
