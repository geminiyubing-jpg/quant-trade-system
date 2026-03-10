#!/usr/bin/env python3
"""
Quant-Trade System - 测试数据初始化脚本

用法:
    cd backend
    python database/scripts/seed_test_data.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# ============================================================
# 测试数据配置
# ============================================================

# 测试用户
TEST_USERS = [
    {
        'id': 'test-user-001',
        'username': 'admin',
        'email': 'admin@quant-trade.com',
        'full_name': '系统管理员',
        'role': 'admin',
        'is_superuser': True,
        'password': 'admin123',  # 明文密码，会被 hash
    },
    {
        'id': 'test-user-002',
        'username': 'trader_zhang',
        'email': 'zhang@quant-trade.com',
        'full_name': '张三',
        'role': 'trader',
        'password': 'trader123',
    },
    {
        'id': 'test-user-003',
        'username': 'analyst_li',
        'email': 'li@quant-trade.com',
        'full_name': '李四',
        'role': 'analyst',
        'password': 'analyst123',
    },
]

# 测试股票 - 覆盖主要行业
TEST_STOCKS = [
    # 金融
    {'symbol': '000001.SZ', 'name': '平安银行', 'sector': '金融', 'industry': '银行', 'market': 'SZSE'},
    {'symbol': '600036.SH', 'name': '招商银行', 'sector': '金融', 'industry': '银行', 'market': 'SHSE'},
    {'symbol': '601318.SH', 'name': '中国平安', 'sector': '金融', 'industry': '保险', 'market': 'SHSE'},
    {'symbol': '600030.SH', 'name': '中信证券', 'sector': '金融', 'industry': '证券', 'market': 'SHSE'},

    # 科技
    {'symbol': '000063.SZ', 'name': '中兴通讯', 'sector': '科技', 'industry': '通信设备', 'market': 'SZSE'},
    {'symbol': '002415.SZ', 'name': '海康威视', 'sector': '科技', 'industry': '电子设备', 'market': 'SZSE'},
    {'symbol': '300750.SZ', 'name': '宁德时代', 'sector': '科技', 'industry': '新能源', 'market': 'SZSE'},
    {'symbol': '688981.SH', 'name': '中芯国际', 'sector': '科技', 'industry': '半导体', 'market': 'SHSE'},

    # 消费
    {'symbol': '000858.SZ', 'name': '五粮液', 'sector': '消费', 'industry': '白酒', 'market': 'SZSE'},
    {'symbol': '000568.SZ', 'name': '泸州老窖', 'sector': '消费', 'industry': '白酒', 'market': 'SZSE'},
    {'symbol': '600887.SH', 'name': '伊利股份', 'sector': '消费', 'industry': '食品饮料', 'market': 'SHSE'},
    {'symbol': '002304.SZ', 'name': '洋河股份', 'sector': '消费', 'industry': '白酒', 'market': 'SZSE'},

    # 医药
    {'symbol': '000538.SZ', 'name': '云南白药', 'sector': '医药', 'industry': '中药', 'market': 'SZSE'},
    {'symbol': '600276.SH', 'name': '恒瑞医药', 'sector': '医药', 'industry': '化学制药', 'market': 'SHSE'},
    {'symbol': '300760.SZ', 'name': '迈瑞医疗', 'sector': '医药', 'industry': '医疗器械', 'market': 'SZSE'},
    {'symbol': '002007.SZ', 'name': '华兰生物', 'sector': '医药', 'industry': '生物制品', 'market': 'SZSE'},

    # 新能源
    {'symbol': '600900.SH', 'name': '长江电力', 'sector': '新能源', 'industry': '电力', 'market': 'SHSE'},
    {'symbol': '601012.SH', 'name': '隆基绿能', 'sector': '新能源', 'industry': '光伏', 'market': 'SHSE'},
    {'symbol': '002594.SZ', 'name': '比亚迪', 'sector': '新能源', 'industry': '新能源汽车', 'market': 'SZSE'},

    # 地产
    {'symbol': '000002.SZ', 'name': '万科A', 'sector': '房地产', 'industry': '房地产开发', 'market': 'SZSE'},
    {'symbol': '600048.SH', 'name': '保利发展', 'sector': '房地产', 'industry': '房地产开发', 'market': 'SHSE'},

    # 基准指数
    {'symbol': '000001.SH', 'name': '上证指数', 'sector': '指数', 'industry': '宽基指数', 'market': 'SHSE'},
    {'symbol': '399001.SZ', 'name': '深证成指', 'sector': '指数', 'industry': '宽基指数', 'market': 'SZSE'},
    {'symbol': '000300.SH', 'name': '沪深300', 'sector': '指数', 'industry': '宽基指数', 'market': 'SHSE'},
]

# 股票基础价格映射（用于生成合理的价格波动）
STOCK_BASE_PRICES = {
    '000001.SZ': Decimal('12.50'),
    '600036.SH': Decimal('35.80'),
    '601318.SH': Decimal('48.20'),
    '600030.SH': Decimal('22.15'),
    '000063.SZ': Decimal('28.90'),
    '002415.SZ': Decimal('32.50'),
    '300750.SZ': Decimal('185.00'),
    '688981.SH': Decimal('52.30'),
    '000858.SZ': Decimal('158.00'),
    '000568.SZ': Decimal('185.50'),
    '600887.SH': Decimal('28.80'),
    '002304.SZ': Decimal('108.00'),
    '000538.SZ': Decimal('52.80'),
    '600276.SH': Decimal('42.50'),
    '300760.SZ': Decimal('295.00'),
    '002007.SZ': Decimal('25.60'),
    '600900.SH': Decimal('28.50'),
    '601012.SH': Decimal('25.80'),
    '002594.SZ': Decimal('268.00'),
    '000002.SZ': Decimal('8.50'),
    '600048.SH': Decimal('10.20'),
    '000001.SH': Decimal('3150.00'),
    '399001.SZ': Decimal('9850.00'),
    '000300.SH': Decimal('3680.00'),
}

# 测试策略
TEST_STRATEGIES = [
    {
        'name': '双均线交叉策略',
        'description': '基于5日和20日均线交叉的趋势跟踪策略，金叉买入，死叉卖出',
        'status': 'ACTIVE',
        'code': '''
def execute(context):
    """
    双均线交叉策略
    """
    short_ma = get_ma(context.symbol, 5)
    long_ma = get_ma(context.symbol, 20)

    if short_ma > long_ma and context.position == 0:
        # 金叉买入
        buy(context.symbol, context.cash * 0.8)
    elif short_ma < long_ma and context.position > 0:
        # 死叉卖出
        sell(context.symbol, context.position)
''',
        'parameters': {
            'short_period': 5,
            'long_period': 20,
            'position_ratio': 0.8,
            'stop_loss': 0.05,
            'take_profit': 0.15,
        }
    },
    {
        'name': 'RSI超卖反弹策略',
        'description': '利用RSI指标识别超卖反弹机会，RSI低于30买入，高于70卖出',
        'status': 'ACTIVE',
        'code': '''
def execute(context):
    """
    RSI超卖反弹策略
    """
    rsi = get_rsi(context.symbol, 14)

    if rsi < 30 and context.position == 0:
        # 超卖买入
        buy(context.symbol, context.cash * 0.6)
    elif rsi > 70 and context.position > 0:
        # 超买卖出
        sell(context.symbol, context.position)
''',
        'parameters': {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'position_ratio': 0.6,
        }
    },
    {
        'name': '布林带突破策略',
        'description': '基于布林带的突破策略，突破上轨买入，跌破下轨止损',
        'status': 'DRAFT',
        'code': '''
def execute(context):
    """
    布林带突破策略
    """
    upper, middle, lower = get_bollinger(context.symbol, 20, 2)

    if context.close_price > upper and context.position == 0:
        # 突破上轨买入
        buy(context.symbol, context.cash * 0.5)
    elif context.close_price < lower and context.position > 0:
        # 跌破下轨止损
        sell(context.symbol, context.position)
''',
        'parameters': {
            'period': 20,
            'std_dev': 2.0,
            'position_ratio': 0.5,
        }
    },
    {
        'name': 'MACD趋势策略',
        'description': '基于MACD指标的趋势跟踪策略，DIF上穿DEA买入',
        'status': 'ACTIVE',
        'code': '''
def execute(context):
    """
    MACD趋势策略
    """
    dif, dea, macd = get_macd(context.symbol, 12, 26, 9)

    if dif > dea and macd > 0 and context.position == 0:
        # DIF上穿DEA且MACD为正
        buy(context.symbol, context.cash * 0.7)
    elif dif < dea and context.position > 0:
        # DIF下穿DEA
        sell(context.symbol, context.position)
''',
        'parameters': {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'position_ratio': 0.7,
        }
    },
    {
        'name': '多因子量化策略',
        'description': '综合动量、价值、质量等多因子的选股策略',
        'status': 'PAUSED',
        'code': '''
def execute(context):
    """
    多因子量化策略
    """
    factors = {
        'momentum': calc_momentum(context.symbol, 60),
        'value': calc_pe_ratio(context.symbol),
        'quality': calc_roe(context.symbol),
        'volatility': calc_volatility(context.symbol, 20),
    }

    score = (
        factors['momentum'] * 0.3 +
        factors['value'] * 0.25 +
        factors['quality'] * 0.25 +
        (1 - factors['volatility']) * 0.2
    )

    if score > 0.6 and context.position == 0:
        buy(context.symbol, context.cash * 0.8)
    elif score < 0.4 and context.position > 0:
        sell(context.symbol, context.position)
''',
        'parameters': {
            'factors': ['momentum', 'value', 'quality', 'volatility'],
            'weights': [0.3, 0.25, 0.25, 0.2],
            'buy_threshold': 0.6,
            'sell_threshold': 0.4,
        }
    },
]


# ============================================================
# 数据生成函数
# ============================================================

def generate_password_hash(password: str) -> str:
    """生成密码哈希"""
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def generate_stock_prices(symbol: str, base_price: Decimal, days: int = 60) -> list:
    """生成股票历史价格数据"""
    prices = []
    current_price = base_price
    now = datetime.utcnow()

    for i in range(days):
        # 随机波动 -3% 到 +3%
        change = Decimal(str(random.uniform(-0.03, 0.03)))
        current_price = current_price * (1 + change)

        # 确保价格为正
        if current_price <= 0:
            current_price = base_price * Decimal('0.5')

        # 生成日内波动
        high = current_price * Decimal(str(random.uniform(1.005, 1.025)))
        low = current_price * Decimal(str(random.uniform(0.975, 0.995)))
        open_price = current_price * Decimal(str(random.uniform(0.99, 1.01)))

        # 成交量（与价格相关）
        base_volume = random.randint(500000, 5000000)
        volume = int(base_volume * (1 + abs(change) * 10))

        prices.append({
            'symbol': symbol,
            'price_open': round(open_price, 2),
            'price_close': round(current_price, 2),
            'price_high': round(high, 2),
            'price_low': round(low, 2),
            'volume': volume,
            'amount': round(current_price * Decimal(str(volume)), 2),
            'timestamp': now - timedelta(days=days - i - 1),
        })

    return prices


def generate_backtest_results() -> dict:
    """生成回测结果数据"""
    total_return = Decimal(str(random.uniform(-0.2, 0.5)))
    max_drawdown = Decimal(str(random.uniform(0.05, 0.25)))
    sharpe_ratio = Decimal(str(random.uniform(0.5, 2.5)))

    # 生成资金曲线
    equity_curve = []
    capital = Decimal('1000000')
    for i in range(60):
        daily_return = Decimal(str(random.uniform(-0.02, 0.03)))
        capital = capital * (1 + daily_return)
        equity_curve.append({
            'date': (datetime.utcnow() - timedelta(days=59 - i)).strftime('%Y-%m-%d'),
            'equity': float(round(capital, 2)),
        })

    # 生成交易记录
    trades = []
    for i in range(random.randint(10, 30)):
        side = random.choice(['BUY', 'SELL'])
        trades.append({
            'date': (datetime.utcnow() - timedelta(days=random.randint(0, 59))).strftime('%Y-%m-%d'),
            'symbol': random.choice(TEST_STOCKS)['symbol'],
            'side': side,
            'price': round(random.uniform(10, 200), 2),
            'quantity': random.randint(100, 10000),
            'commission': round(random.uniform(5, 50), 2),
        })

    return {
        'total_return': float(total_return),
        'annual_return': float(total_return * 2),
        'max_drawdown': float(max_drawdown),
        'sharpe_ratio': float(sharpe_ratio),
        'sortino_ratio': float(sharpe_ratio * 0.8),
        'win_rate': float(random.uniform(0.45, 0.65)),
        'total_trades': len(trades),
        'winning_trades': int(len(trades) * random.uniform(0.45, 0.65)),
        'equity_curve': equity_curve,
        'trades': trades,
    }


# ============================================================
# 数据库操作
# ============================================================

async def seed_users(session: AsyncSession) -> dict:
    """插入测试用户"""
    print("\n👤 插入测试用户...")

    user_ids = {}
    for user_data in TEST_USERS:
        # 检查用户是否存在
        result = await session.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {'username': user_data['username']}
        )
        existing = result.scalar()

        if existing:
            user_ids[user_data['username']] = existing
            print(f"   用户 {user_data['username']} 已存在，跳过")
            continue

        # 创建新用户
        password_hash = generate_password_hash(user_data.pop('password'))
        user_id = user_data['id']

        await session.execute(
            text("""
                INSERT INTO users (id, username, email, hashed_password, full_name, role, is_active, is_superuser, preferences)
                VALUES (:id, :username, :email, :hashed_password, :full_name, :role, true, :is_superuser, '{}')
            """),
            {
                **user_data,
                'hashed_password': password_hash,
                'is_superuser': user_data.get('is_superuser', False),
            }
        )
        user_ids[user_data['username']] = user_id
        print(f"   ✅ 创建用户: {user_data['username']} ({user_data['full_name']})")

    await session.commit()
    return user_ids


async def seed_stocks(session: AsyncSession) -> None:
    """插入测试股票"""
    print("\n📈 插入测试股票...")

    inserted = 0
    for stock in TEST_STOCKS:
        # 检查股票是否存在
        result = await session.execute(
            text("SELECT symbol FROM stocks WHERE symbol = :symbol"),
            {'symbol': stock['symbol']}
        )
        if result.scalar():
            continue

        await session.execute(
            text("""
                INSERT INTO stocks (symbol, name, sector, industry, market, is_active)
                VALUES (:symbol, :name, :sector, :industry, :market, true)
            """),
            stock
        )
        inserted += 1

    await session.commit()
    print(f"   ✅ 插入 {inserted} 条新股票记录，共 {len(TEST_STOCKS)} 只股票")


async def seed_stock_prices(session: AsyncSession) -> None:
    """插入股票历史价格"""
    print("\n📊 插入股票历史价格...")

    total_records = 0
    for stock in TEST_STOCKS:
        symbol = stock['symbol']
        base_price = STOCK_BASE_PRICES.get(symbol, Decimal('10.00'))

        # 检查是否已有数据
        result = await session.execute(
            text("SELECT COUNT(*) FROM stock_prices WHERE symbol = :symbol"),
            {'symbol': symbol}
        )
        existing_count = result.scalar()
        if existing_count and existing_count > 0:
            continue

        # 生成60天历史数据
        prices = generate_stock_prices(symbol, base_price, days=60)

        for price in prices:
            await session.execute(
                text("""
                    INSERT INTO stock_prices
                    (symbol, price_open, price_close, price_high, price_low, volume, amount, timestamp)
                    VALUES
                    (:symbol, :price_open, :price_close, :price_high, :price_low, :volume, :amount, :timestamp)
                """),
                price
            )
        total_records += len(prices)

    await session.commit()
    print(f"   ✅ 插入 {total_records} 条价格记录")


async def seed_strategies(session: AsyncSession, user_ids: dict) -> dict:
    """插入测试策略"""
    print("\n🧠 插入测试策略...")

    strategy_ids = {}
    trader_id = user_ids.get('trader_zhang', user_ids.get(list(user_ids.keys())[0]))

    for i, strategy in enumerate(TEST_STRATEGIES):
        strategy_id = str(uuid.uuid4())
        strategy_ids[strategy['name']] = strategy_id

        await session.execute(
            text("""
                INSERT INTO strategies
                (id, user_id, name, description, status, code, parameters, created_by, updated_by, version)
                VALUES
                (:id, :user_id, :name, :description, :status::strategy_status, :code, :parameters::jsonb, :created_by, :updated_by, 1)
            """),
            {
                'id': strategy_id,
                'user_id': trader_id,
                'name': strategy['name'],
                'description': strategy['description'],
                'status': strategy['status'],
                'code': strategy['code'],
                'parameters': str(strategy['parameters']).replace("'", '"'),
                'created_by': trader_id,
                'updated_by': trader_id,
            }
        )
        print(f"   ✅ 创建策略: {strategy['name']}")

    await session.commit()
    return strategy_ids


async def seed_backtests(session: AsyncSession, user_ids: dict, strategy_ids: dict) -> None:
    """插入测试回测"""
    print("\n🔬 插入测试回测...")

    trader_id = user_ids.get('trader_zhang', user_ids.get(list(user_ids.keys())[0]))
    strategy_names = list(strategy_ids.keys())

    for i in range(5):
        job_id = f"backtest-job-{i+1:03d}"
        strategy_name = strategy_names[i % len(strategy_names)]
        strategy_id = strategy_ids[strategy_name]

        # 生成回测结果
        results = generate_backtest_results()

        # 插入回测任务
        await session.execute(
            text("""
                INSERT INTO backtest_jobs
                (id, strategy_id, name, status, config, result, progress, created_by, created_at, completed_at)
                VALUES
                (:id, :strategy_id, :name, 'COMPLETED', :config::jsonb, :result::jsonb, 100, :created_by, :created_at, :completed_at)
            """),
            {
                'id': job_id,
                'strategy_id': strategy_id,
                'name': f'{strategy_name} - 历史回测{i+1}',
                'config': str({
                    'start_date': '2024-01-01',
                    'end_date': '2024-12-31',
                    'initial_capital': 1000000,
                }).replace("'", '"'),
                'result': str(results).replace("'", '"'),
                'created_by': trader_id,
                'created_at': datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                'completed_at': datetime.utcnow() - timedelta(days=random.randint(0, 29)),
            }
        )

        # 插入回测结果
        await session.execute(
            text("""
                INSERT INTO backtest_results
                (job_id, strategy_id, start_date, end_date, initial_capital, final_capital,
                 total_return, annual_return, sharpe_ratio, sortino_ratio, max_drawdown,
                 win_rate, total_trades, winning_trades, losing_trades, avg_trade,
                 profit_factor, equity_curve, trades, created_at)
                VALUES
                (:job_id, :strategy_id, :start_date, :end_date, :initial_capital, :final_capital,
                 :total_return, :annual_return, :sharpe_ratio, :sortino_ratio, :max_drawdown,
                 :win_rate, :total_trades, :winning_trades, :losing_trades, :avg_trade,
                 :profit_factor, :equity_curve::jsonb, :trades::jsonb, :created_at)
            """),
            {
                'job_id': job_id,
                'strategy_id': strategy_id,
                'start_date': datetime(2024, 1, 1).date(),
                'end_date': datetime(2024, 12, 31).date(),
                'initial_capital': Decimal('1000000'),
                'final_capital': Decimal(str(1000000 * (1 + results['total_return']))),
                'total_return': Decimal(str(results['total_return'])),
                'annual_return': Decimal(str(results['annual_return'])),
                'sharpe_ratio': Decimal(str(results['sharpe_ratio'])),
                'sortino_ratio': Decimal(str(results['sortino_ratio'])),
                'max_drawdown': Decimal(str(results['max_drawdown'])),
                'win_rate': Decimal(str(results['win_rate'])),
                'total_trades': results['total_trades'],
                'winning_trades': results['winning_trades'],
                'losing_trades': results['total_trades'] - results['winning_trades'],
                'avg_trade': Decimal(str(random.uniform(500, 5000))),
                'profit_factor': Decimal(str(random.uniform(1.1, 2.5))),
                'equity_curve': str(results['equity_curve']).replace("'", '"'),
                'trades': str(results['trades']).replace("'", '"'),
                'created_at': datetime.utcnow(),
            }
        )
        print(f"   ✅ 创建回测: {strategy_name} - 历史回测{i+1}")

    await session.commit()


async def seed_orders(session: AsyncSession, user_ids: dict, strategy_ids: dict) -> None:
    """插入测试订单"""
    print("\n📝 插入测试订单...")

    trader_id = user_ids.get('trader_zhang', user_ids.get(list(user_ids.keys())[0]))
    strategy_id = list(strategy_ids.values())[0]

    order_statuses = ['FILLED', 'FILLED', 'FILLED', 'CANCELED', 'PENDING']
    sides = ['BUY', 'SELL']

    for i in range(10):
        order_id = f"order-{i+1:04d}"
        symbol = random.choice(TEST_STOCKS)['symbol']
        side = random.choice(sides)
        status = random.choice(order_statuses)
        quantity = random.randint(100, 10000)
        price = Decimal(str(random.uniform(10, 200)))

        await session.execute(
            text("""
                INSERT INTO orders
                (id, strategy_id, ts_code, user_id, execution_mode, side, order_type,
                 quantity, price, filled_quantity, avg_price, status, create_time, update_time)
                VALUES
                (:id, :strategy_id, :ts_code, :user_id, 'PAPER', :side, 'LIMIT',
                 :quantity, :price, :filled_quantity, :avg_price, :status, :create_time, :update_time)
            """),
            {
                'id': order_id,
                'strategy_id': strategy_id,
                'ts_code': symbol,
                'user_id': trader_id,
                'side': side,
                'quantity': quantity,
                'price': price,
                'filled_quantity': quantity if status == 'FILLED' else 0,
                'avg_price': price if status == 'FILLED' else None,
                'status': status,
                'create_time': datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                'update_time': datetime.utcnow() - timedelta(days=random.randint(0, 10)),
            }
        )

    await session.commit()
    print(f"   ✅ 插入 10 条订单记录")


async def seed_positions(session: AsyncSession, user_ids: dict, strategy_ids: dict) -> None:
    """插入测试持仓"""
    print("\n💼 插入测试持仓...")

    trader_id = user_ids.get('trader_zhang', user_ids.get(list(user_ids.keys())[0]))
    strategy_id = list(strategy_ids.values())[0]

    # 选择几只股票创建持仓
    position_stocks = random.sample([s for s in TEST_STOCKS if s['sector'] != '指数'], 5)

    for i, stock in enumerate(position_stocks):
        quantity = random.randint(100, 5000)
        avg_cost = STOCK_BASE_PRICES.get(stock['symbol'], Decimal('10.00'))
        current_price = avg_cost * Decimal(str(random.uniform(0.9, 1.2)))
        market_value = current_price * Decimal(str(quantity))
        unrealized_pnl = (current_price - avg_cost) * Decimal(str(quantity))

        await session.execute(
            text("""
                INSERT INTO positions
                (strategy_id, stock_symbol, user_id, execution_mode, quantity, avg_cost,
                 current_price, market_value, unrealized_pnl, opened_at, status)
                VALUES
                (:strategy_id, :stock_symbol, :user_id, 'PAPER', :quantity, :avg_cost,
                 :current_price, :market_value, :unrealized_pnl, :opened_at, 'open')
            """),
            {
                'strategy_id': strategy_id,
                'stock_symbol': stock['symbol'],
                'user_id': trader_id,
                'quantity': quantity,
                'avg_cost': avg_cost,
                'current_price': current_price,
                'market_value': market_value,
                'unrealized_pnl': unrealized_pnl,
                'opened_at': datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            }
        )
        print(f"   ✅ 创建持仓: {stock['symbol']} - {stock['name']}")

    await session.commit()


async def verify_data(session: AsyncSession) -> None:
    """验证数据"""
    print("\n🔍 验证测试数据...")

    tables = [
        ('users', '用户'),
        ('stocks', '股票'),
        ('stock_prices', '股票价格'),
        ('strategies', '策略'),
        ('backtest_jobs', '回测任务'),
        ('backtest_results', '回测结果'),
        ('orders', '订单'),
        ('positions', '持仓'),
    ]

    for table, name in tables:
        try:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"   {name}: {count} 条记录")
        except Exception as e:
            print(f"   {name}: 表不存在或查询失败 ({e})")


# ============================================================
# 主函数
# ============================================================

async def main():
    """主函数"""
    print("=" * 60)
    print("🌱 Quant-Trade System - 测试数据初始化")
    print("=" * 60)

    try:
        from src.core.config import settings

        # 创建数据库连接
        engine = create_async_engine(settings.async_database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # 1. 插入用户
            user_ids = await seed_users(session)

            # 2. 插入股票
            await seed_stocks(session)

            # 3. 插入股票价格
            await seed_stock_prices(session)

            # 4. 插入策略
            strategy_ids = await seed_strategies(session, user_ids)

            # 5. 插入回测
            await seed_backtests(session, user_ids, strategy_ids)

            # 6. 插入订单
            await seed_orders(session, user_ids, strategy_ids)

            # 7. 插入持仓
            await seed_positions(session, user_ids, strategy_ids)

            # 8. 验证数据
            await verify_data(session)

        await engine.dispose()

        print("\n" + "=" * 60)
        print("✅ 测试数据初始化完成！")
        print("=" * 60)
        print("\n📋 测试账号信息:")
        print("-" * 40)
        for user in TEST_USERS:
            password = [u['password'] for u in TEST_USERS if u['username'] == user['username']][0]
            print(f"   用户名: {user['username']}")
            print(f"   密码: {password}")
            print(f"   角色: {user['role']}")
            print("-" * 40)

    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    asyncio.run(main())
