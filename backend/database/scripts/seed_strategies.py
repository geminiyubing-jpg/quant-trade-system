#!/usr/bin/env python3
"""
Quant-Trade System - 策略测试数据初始化脚本

添加10条常用量化交易策略到数据库

用法:
    cd backend
    python database/scripts/seed_strategies.py
"""

import uuid
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from src.core.database import SessionLocal

# ============================================================
# 常用策略配置
# ============================================================

STRATEGIES = [
    {
        'id': 'strategy_004',
        'name': '布林带突破策略',
        'description': '基于布林带指标的突破策略。当价格突破上轨时买入，跌破下轨时卖出。适用于震荡市场的趋势捕捉。',
        'type': 'breakout',
        'parameters': {
            'period': 20,
            'std_dev': 2.0,
            'position_size': 0.3,
            'stop_loss': 0.05,
        },
        'is_active': True,
    },
    {
        'id': 'strategy_005',
        'name': '动量反转策略',
        'description': '利用价格动量进行反转交易。当动量指标显示超买/超卖时进行反向操作，适合短线交易。',
        'type': 'reversal',
        'parameters': {
            'lookback_period': 14,
            'overbought_threshold': 0.8,
            'oversold_threshold': -0.8,
            'position_size': 0.2,
        },
        'is_active': True,
    },
    {
        'id': 'strategy_006',
        'name': '均线回归策略',
        'description': '基于均值回归原理，当价格偏离均线过大时进行反向操作。适合震荡行情中的高抛低吸。',
        'type': 'mean_reversion',
        'parameters': {
            'ma_period': 20,
            'deviation_threshold': 0.03,
            'position_size': 0.25,
            'profit_target': 0.05,
        },
        'is_active': True,
    },
    {
        'id': 'strategy_007',
        'name': '多因子选股策略',
        'description': '综合价值、动量、质量、波动率等多因子进行选股。通过因子打分筛选优质股票构建组合。',
        'type': 'multi_factor',
        'parameters': {
            'factors': ['value', 'momentum', 'quality', 'volatility'],
            'weights': [0.25, 0.3, 0.25, 0.2],
            'rebalance_freq': 'monthly',
            'top_n': 20,
        },
        'is_active': True,
    },
    {
        'id': 'strategy_008',
        'name': '网格交易策略',
        'description': '在一定价格区间内设置网格，价格每下跌一定幅度买入，上涨一定幅度卖出。适合震荡行情。',
        'type': 'grid',
        'parameters': {
            'grid_count': 10,
            'grid_spacing': 0.02,
            'base_position': 0.1,
            'price_range': [0.9, 1.1],
        },
        'is_active': True,
    },
    {
        'id': 'strategy_009',
        'name': '趋势跟踪策略',
        'description': '基于ADX指标判断趋势强度，配合均线方向进行趋势跟踪。只在强趋势市场中操作。',
        'type': 'trend',
        'parameters': {
            'adx_threshold': 25,
            'ma_fast': 10,
            'ma_slow': 30,
            'position_size': 0.4,
            'trailing_stop': 0.08,
        },
        'is_active': True,
    },
    {
        'id': 'strategy_010',
        'name': '量价突破策略',
        'description': '结合成交量放量和价格突破进行选股。当放量突破阻力位时买入，缩量跌破支撑位时卖出。',
        'type': 'volume_breakout',
        'parameters': {
            'volume_threshold': 2.0,
            'breakout_pct': 0.03,
            'holding_period': 5,
            'stop_loss': 0.05,
        },
        'is_active': True,
    },
    {
        'id': 'strategy_011',
        'name': '行业轮动策略',
        'description': '基于行业相对强弱进行轮动配置。跟踪强势行业ETF或龙头股，定期调仓。',
        'type': 'sector_rotation',
        'parameters': {
            'lookback_period': 20,
            'top_sectors': 3,
            'rebalance_freq': 'weekly',
            'position_per_sector': 0.33,
        },
        'is_active': True,
    },
    {
        'id': 'strategy_012',
        'name': '事件驱动策略',
        'description': '基于重大事件（财报、并购、政策等）进行短期交易。事件公布前布局，公布后获利了结。',
        'type': 'event_driven',
        'parameters': {
            'event_types': ['earnings', 'merger', 'policy'],
            'holding_days': 3,
            'position_size': 0.15,
            'stop_loss': 0.03,
        },
        'is_active': False,  # 需要人工判断，默认关闭
    },
    {
        'id': 'strategy_013',
        'name': '统计套利策略',
        'description': '基于配对交易的统计套利策略。寻找相关性高的股票对，利用价差回归获利。',
        'type': 'arbitrage',
        'parameters': {
            'correlation_threshold': 0.8,
            'entry_zscore': 2.0,
            'exit_zscore': 0.5,
            'max_holding_days': 10,
        },
        'is_active': True,
    },
]


def get_user_id(db) -> str:
    """获取用户ID"""
    result = db.execute(
        text("SELECT id FROM users WHERE username = 'trader_zhang'")
    )
    user_id = result.scalar()
    if not user_id:
        result = db.execute(text("SELECT id FROM users WHERE username = 'test_user'"))
        user_id = result.scalar()
    return user_id


def seed_strategies(db, user_id: str) -> None:
    """插入策略数据"""
    print("\n🧠 插入策略数据...")

    inserted = 0
    for strategy in STRATEGIES:
        # 检查是否已存在
        result = db.execute(
            text("SELECT id FROM strategies WHERE id = :id"),
            {'id': strategy['id']}
        )
        if result.scalar():
            print(f"   策略 {strategy['name']} 已存在，跳过")
            continue

        db.execute(
            text("""
                INSERT INTO strategies
                (id, name, description, type, parameters, is_active, created_by, created_at, updated_at)
                VALUES
                (:id, :name, :description, :type, CAST(:parameters AS jsonb), :is_active, :created_by, NOW(), NOW())
            """),
            {
                'id': strategy['id'],
                'name': strategy['name'],
                'description': strategy['description'],
                'type': strategy['type'],
                'parameters': str(strategy['parameters']).replace("'", '"'),
                'is_active': strategy['is_active'],
                'created_by': user_id,
            }
        )
        inserted += 1
        status = "✅" if strategy['is_active'] else "⏸️"
        print(f"   {status} 创建策略: {strategy['name']} ({strategy['type']})")

    db.commit()
    print(f"   共插入 {inserted} 条策略记录")


def verify_strategies(db) -> None:
    """验证策略数据"""
    print("\n🔍 验证策略数据...")

    result = db.execute(text("SELECT id, name, type, is_active FROM strategies ORDER BY id"))
    print("   现有策略列表:")
    for row in result:
        status = "🟢" if row[3] else "🔴"
        print(f"     {status} {row[0]}: {row[1]} ({row[2]})")


def main():
    """主函数"""
    print("=" * 60)
    print("🧠 Quant-Trade System - 策略测试数据初始化")
    print("=" * 60)

    db = SessionLocal()
    try:
        user_id = get_user_id(db)
        if not user_id:
            print("❌ 未找到测试用户")
            return

        print(f"📝 使用用户ID: {user_id}")

        # 插入策略
        seed_strategies(db, user_id)

        # 验证
        verify_strategies(db)

        print("\n" + "=" * 60)
        print("✅ 策略测试数据初始化完成！")
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
