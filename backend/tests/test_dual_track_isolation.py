"""
双轨隔离集成测试套件

测试双轨隔离机制的完整性和正确性：
1. 用户隔离 - 用户A无法访问用户B的数据
2. 模式隔离 - PAPER 数据不会混入 LIVE 模式
3. 边界条件 - 无效参数的处理
4. 性能测试 - 索引不影响查询性能
"""

import sys
import os
import time
import uuid
from datetime import datetime
from decimal import Decimal

# 切换到 backend 目录
os.chdir('/Users/yubing/quant-trade-system/backend')
sys.path.insert(0, '/Users/yubing/quant-trade-system/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import get_db, engine
from src.models.trading import Order, Position
from src.models.user import User
from src.repositories.trading import OrderRepository, PositionRepository


class DualTrackIsolationTest:
    """双轨隔离集成测试类"""

    def __init__(self):
        """初始化测试环境"""
        self.db = next(get_db())
        self.order_repo = OrderRepository(Order)
        self.position_repo = PositionRepository(Position)
        self.test_data = []

    def setup_test_data(self):
        """创建测试数据"""
        print("=" * 80)
        print("🔧 设置测试数据...")
        print("=" * 80)

        # 创建两个测试用户
        self.user_a_id = "test_user_a_" + str(uuid.uuid4())[:8]
        self.user_b_id = "test_user_b_" + str(uuid.uuid4())[:8]

        # 为两个用户创建不同模式的订单
        test_orders = [
            # User A 的 PAPER 订单
            Order(
                id=f"order_a_paper_{uuid.uuid4().hex[:12]}",
                user_id=self.user_a_id,
                execution_mode="PAPER",
                strategy_id=None,  # 使用 NULL 避免外键约束
                ts_code="000001.SZ",
                side="BUY",
                order_type="LIMIT",
                quantity=100,
                price=Decimal("10.50"),
                filled_quantity=0,
                avg_price=Decimal("0.00"),
                status="PENDING",
                create_time=datetime.now(),
                update_time=datetime.now(),
                filled_time=None
            ),
            # User A 的 LIVE 订单
            Order(
                id=f"order_a_live_{uuid.uuid4().hex[:12]}",
                user_id=self.user_a_id,
                execution_mode="LIVE",
                strategy_id=None,  # 使用 NULL 避免外键约束
                ts_code="000002.SZ",
                side="BUY",
                order_type="LIMIT",
                quantity=200,
                price=Decimal("15.50"),
                filled_quantity=0,
                avg_price=Decimal("0.00"),
                status="PENDING",
                create_time=datetime.now(),
                update_time=datetime.now(),
                filled_time=None
            ),
            # User B 的 PAPER 订单
            Order(
                id=f"order_b_paper_{uuid.uuid4().hex[:12]}",
                user_id=self.user_b_id,
                execution_mode="PAPER",
                strategy_id=None,  # 使用 NULL 避免外键约束
                ts_code="000001.SZ",
                side="SELL",
                order_type="LIMIT",
                quantity=50,
                price=Decimal("11.00"),
                filled_quantity=0,
                avg_price=Decimal("0.00"),
                status="PENDING",
                create_time=datetime.now(),
                update_time=datetime.now(),
                filled_time=None
            ),
            # User B 的 LIVE 订单
            Order(
                id=f"order_b_live_{uuid.uuid4().hex[:12]}",
                user_id=self.user_b_id,
                execution_mode="LIVE",
                strategy_id=None,  # 使用 NULL 避免外键约束
                ts_code="000003.SZ",
                side="BUY",
                order_type="LIMIT",
                quantity=150,
                price=Decimal("20.00"),
                filled_quantity=0,
                avg_price=Decimal("0.00"),
                status="PENDING",
                create_time=datetime.now(),
                update_time=datetime.now(),
                filled_time=None
            ),
        ]

        # 创建测试持仓
        test_positions = [
            # User A 的 PAPER 持仓
            Position(
                id=None,  # 自增
                user_id=self.user_a_id,
                execution_mode="PAPER",
                strategy_id=None,  # 使用 NULL 避免外键约束
                stock_symbol="000001.SZ",
                quantity=1000,
                avg_cost=Decimal("10.00"),
                current_price=Decimal("10.50"),
                market_value=Decimal("10500.00"),
                unrealized_pnl=Decimal("500.00"),
                opened_at=datetime.now(),
                closed_at=None,
                status="open"
            ),
            # User A 的 LIVE 持仓
            Position(
                id=None,
                user_id=self.user_a_id,
                execution_mode="LIVE",
                strategy_id=None,  # 使用 NULL 避免外键约束
                stock_symbol="000002.SZ",
                quantity=500,
                avg_cost=Decimal("15.00"),
                current_price=Decimal("15.50"),
                market_value=Decimal("7750.00"),
                unrealized_pnl=Decimal("250.00"),
                opened_at=datetime.now(),
                closed_at=None,
                status="open"
            ),
            # User B 的 PAPER 持仓
            Position(
                id=None,
                user_id=self.user_b_id,
                execution_mode="PAPER",
                strategy_id=None,  # 使用 NULL 避免外键约束
                stock_symbol="000001.SZ",
                quantity=200,
                avg_cost=Decimal("11.00"),
                current_price=Decimal("11.50"),
                market_value=Decimal("2300.00"),
                unrealized_pnl=Decimal("100.00"),
                opened_at=datetime.now(),
                closed_at=None,
                status="open"
            ),
            # User B 的 LIVE 持仓
            Position(
                id=None,
                user_id=self.user_b_id,
                execution_mode="LIVE",
                strategy_id=None,  # 使用 NULL 避免外键约束
                stock_symbol="000004.SZ",
                quantity=300,
                avg_cost=Decimal("8.00"),
                current_price=Decimal("8.50"),
                market_value=Decimal("2550.00"),
                unrealized_pnl=Decimal("150.00"),
                opened_at=datetime.now(),
                closed_at=None,
                status="open"
            ),
        ]

        try:
            # 插入测试数据
            self.db.add_all(test_orders)
            self.db.add_all(test_positions)
            self.db.commit()

            self.test_data = test_orders + test_positions

            print(f"✅ 创建 {len(test_orders)} 条测试订单")
            print(f"✅ 创建 {len(test_positions)} 条测试持仓")
            print(f"✅ User A ID: {self.user_a_id}")
            print(f"✅ User B ID: {self.user_b_id}")
            print()

        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"❌ 创建测试数据失败: {e}")
            raise

    def cleanup_test_data(self):
        """清理测试数据"""
        print("=" * 80)
        print("🧹 清理测试数据...")
        print("=" * 80)

        try:
            # 删除测试订单
            for order in self.test_data:
                if isinstance(order, Order):
                    self.db.query(Order).filter(Order.id == order.id).delete()
                    self.db.query(Position).filter(
                        Position.user_id == order.user_id,
                        Position.execution_mode == order.execution_mode
                    ).delete()

            self.db.commit()
            print("✅ 测试数据已清理")
            print()

        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"⚠️  清理测试数据失败: {e}")
            print()

    # ============================================================
    # 测试 1: 用户隔离
    # ============================================================

    def test_user_isolation_orders(self):
        """测试订单的用户隔离"""
        print("=" * 80)
        print("🔒 测试 1.1: 订单用户隔离")
        print("=" * 80)

        # 获取 User A 的订单
        user_a_orders = self.order_repo.get_user_orders(
            self.db,
            user_id=self.user_a_id,
            execution_mode=None,  # 获取所有模式
            skip=0,
            limit=100
        )

        # 获取 User B 的订单
        user_b_orders = self.order_repo.get_user_orders(
            self.db,
            user_id=self.user_b_id,
            execution_mode=None,
            skip=0,
            limit=100
        )

        print(f"User A 订单数: {len(user_a_orders)}")
        print(f"User B 订单数: {len(user_b_orders)}")

        # 验证隔离
        user_a_order_ids = {order.id for order in user_a_orders}
        user_b_order_ids = {order.id for order in user_b_orders}

        assert len(user_a_orders) == 2, f"❌ User A 应该有 2 条订单，实际: {len(user_a_orders)}"
        assert len(user_b_orders) == 2, f"❌ User B 应该有 2 条订单，实际: {len(user_b_orders)}"

        # 验证没有交集
        intersection = user_a_order_ids & user_b_order_ids
        assert len(intersection) == 0, f"❌ 用户订单不应该有交集: {intersection}"

        # 验证所有订单的 user_id 正确
        for order in user_a_orders:
            assert order.user_id == self.user_a_id, f"❌ 订单 {order.id} 的 user_id 不正确"

        for order in user_b_orders:
            assert order.user_id == self.user_b_id, f"❌ 订单 {order.id} 的 user_id 不正确"

        print("✅ 用户隔离测试通过：User A 和 User B 的订单完全隔离")
        print()

    def test_user_isolation_positions(self):
        """测试持仓的用户隔离"""
        print("=" * 80)
        print("🔒 测试 1.2: 持仓用户隔离")
        print("=" * 80)

        # 获取 User A 的持仓
        user_a_positions = self.position_repo.get_user_positions(
            self.db,
            user_id=self.user_a_id,
            execution_mode="PAPER",
            skip=0,
            limit=100
        )

        # 获取 User B 的持仓
        user_b_positions = self.position_repo.get_user_positions(
            self.db,
            user_id=self.user_b_id,
            execution_mode="PAPER",
            skip=0,
            limit=100
        )

        print(f"User A PAPER 持仓数: {len(user_a_positions)}")
        print(f"User B PAPER 持仓数: {len(user_b_positions)}")

        # 验证隔离
        assert len(user_a_positions) == 1, f"❌ User A 应该有 1 条 PAPER 持仓，实际: {len(user_a_positions)}"
        assert len(user_b_positions) == 1, f"❌ User B 应该有 1 条 PAPER 持仓，实际: {len(user_b_positions)}"

        # 验证 user_id 正确
        for position in user_a_positions:
            assert position.user_id == self.user_a_id, f"❌ 持仓 {position.id} 的 user_id 不正确"

        for position in user_b_positions:
            assert position.user_id == self.user_b_id, f"❌ 持仓 {position.id} 的 user_id 不正确"

        print("✅ 用户隔离测试通过：User A 和 User B 的持仓完全隔离")
        print()

    # ============================================================
    # 测试 2: 模式隔离
    # ============================================================

    def test_mode_isolation_orders(self):
        """测试订单的模式隔离"""
        print("=" * 80)
        print("🔀 测试 2.1: 订单模式隔离")
        print("=" * 80)

        # 获取 User A 的 PAPER 订单
        user_a_paper = self.order_repo.get_user_orders(
            self.db,
            user_id=self.user_a_id,
            execution_mode="PAPER",
            skip=0,
            limit=100
        )

        # 获取 User A 的 LIVE 订单
        user_a_live = self.order_repo.get_user_orders(
            self.db,
            user_id=self.user_a_id,
            execution_mode="LIVE",
            skip=0,
            limit=100
        )

        print(f"User A PAPER 订单数: {len(user_a_paper)}")
        print(f"User A LIVE 订单数: {len(user_a_live)}")

        # 验证隔离
        assert len(user_a_paper) == 1, f"❌ User A 应该有 1 条 PAPER 订单，实际: {len(user_a_paper)}"
        assert len(user_a_live) == 1, f"❌ User A 应该有 1 条 LIVE 订单，实际: {len(user_a_live)}"

        # 验证模式正确
        for order in user_a_paper:
            assert order.execution_mode == "PAPER", f"❌ 订单 {order.id} 的 execution_mode 不是 PAPER"

        for order in user_a_live:
            assert order.execution_mode == "LIVE", f"❌ 订单 {order.id} 的 execution_mode 不是 LIVE"

        # 验证没有交集
        paper_ids = {order.id for order in user_a_paper}
        live_ids = {order.id for order in user_a_live}
        assert len(paper_ids & live_ids) == 0, "❌ PAPER 和 LIVE 订单不应该有交集"

        print("✅ 模式隔离测试通过：PAPER 和 LIVE 订单完全隔离")
        print()

    def test_mode_isolation_positions(self):
        """测试持仓的模式隔离"""
        print("=" * 80)
        print("🔀 测试 2.2: 持仓模式隔离")
        print("=" * 80)

        # 获取 User A 的 PAPER 持仓
        user_a_paper = self.position_repo.get_user_positions(
            self.db,
            user_id=self.user_a_id,
            execution_mode="PAPER",
            skip=0,
            limit=100
        )

        # 获取 User A 的 LIVE 持仓
        user_a_live = self.position_repo.get_user_positions(
            self.db,
            user_id=self.user_a_id,
            execution_mode="LIVE",
            skip=0,
            limit=100
        )

        print(f"User A PAPER 持仓数: {len(user_a_paper)}")
        print(f"User A LIVE 持仓数: {len(user_a_live)}")

        # 验证隔离
        assert len(user_a_paper) == 1, f"❌ User A 应该有 1 条 PAPER 持仓，实际: {len(user_a_paper)}"
        assert len(user_a_live) == 1, f"❌ User A 应该有 1 条 LIVE 持仓，实际: {len(user_a_live)}"

        # 验证模式正确
        for position in user_a_paper:
            assert position.execution_mode == "PAPER", f"❌ 持仓 {position.id} 的 execution_mode 不是 PAPER"

        for position in user_a_live:
            assert position.execution_mode == "LIVE", f"❌ 持仓 {position.id} 的 execution_mode 不是 LIVE"

        # 验证股票代码不同
        paper_symbols = {p.stock_symbol for p in user_a_paper}
        live_symbols = {p.stock_symbol for p in user_a_live}
        assert len(paper_symbols & live_symbols) == 0, "❌ PAPER 和 LIVE 持仓的股票代码应该不同"

        print("✅ 模式隔离测试通过：PAPER 和 LIVE 持仓完全隔离")
        print()

    # ============================================================
    # 测试 3: 边界条件
    # ============================================================

    def test_invalid_user_id(self):
        """测试无效 user_id 的处理"""
        print("=" * 80)
        print("⚠️  测试 3.1: 无效 user_id 处理")
        print("=" * 80)

        # 使用不存在的 user_id
        fake_user_id = "nonexistent_user_" + str(uuid.uuid4())[:8]

        orders = self.order_repo.get_user_orders(
            self.db,
            user_id=fake_user_id,
            execution_mode="PAPER",
            skip=0,
            limit=100
        )

        positions = self.position_repo.get_user_positions(
            self.db,
            user_id=fake_user_id,
            execution_mode="PAPER",
            skip=0,
            limit=100
        )

        print(f"不存在的 user_id 查询订单数: {len(orders)}")
        print(f"不存在的 user_id 查询持仓数: {len(positions)}")

        assert len(orders) == 0, "❌ 不存在的 user_id 应该返回 0 条订单"
        assert len(positions) == 0, "❌ 不存在的 user_id 应该返回 0 条持仓"

        print("✅ 无效 user_id 处理正确：返回空列表")
        print()

    def test_invalid_execution_mode(self):
        """测试无效 execution_mode 的处理"""
        print("=" * 80)
        print("⚠️  测试 3.2: 无效 execution_mode 处理")
        print("=" * 80)

        # 使用不存在的 execution_mode
        orders = self.order_repo.get_user_orders(
            self.db,
            user_id=self.user_a_id,
            execution_mode="INVALID_MODE",
            skip=0,
            limit=100
        )

        print(f"无效的 execution_mode 查询订单数: {len(orders)}")

        # 应该返回 0 条，因为没有数据使用这个模式
        assert len(orders) == 0, "❌ 无效的 execution_mode 应该返回 0 条订单"

        print("✅ 无效 execution_mode 处理正确：返回空列表")
        print()

    def test_null_parameters(self):
        """测试空值参数的处理"""
        print("=" * 80)
        print("⚠️  测试 3.3: 空值参数处理")
        print("=" * 80)

        # execution_mode=None 应该返回所有模式的订单
        all_orders = self.order_repo.get_user_orders(
            self.db,
            user_id=self.user_a_id,
            execution_mode=None,
            skip=0,
            limit=100
        )

        print(f"execution_mode=None 查询订单数: {len(all_orders)}")

        assert len(all_orders) == 2, f"❌ User A 应该有 2 条订单（所有模式），实际: {len(all_orders)}"

        # 验证包含 PAPER 和 LIVE
        modes = {order.execution_mode for order in all_orders}
        assert "PAPER" in modes, "❌ 应该包含 PAPER 订单"
        assert "LIVE" in modes, "❌ 应该包含 LIVE 订单"

        print("✅ 空值参数处理正确：返回所有模式的数据")
        print()

    # ============================================================
    # 测试 4: 性能测试
    # ============================================================

    def test_query_performance(self):
        """测试查询性能"""
        print("=" * 80)
        print("⚡ 测试 4: 查询性能")
        print("=" * 80)

        # 测试订单查询性能
        start_time = time.time()
        orders = self.order_repo.get_user_orders(
            self.db,
            user_id=self.user_a_id,
            execution_mode="PAPER",
            skip=0,
            limit=100
        )
        order_query_time = (time.time() - start_time) * 1000  # 转换为毫秒

        print(f"订单查询时间: {order_query_time:.2f} ms")

        # 测试持仓查询性能
        start_time = time.time()
        positions = self.position_repo.get_user_positions(
            self.db,
            user_id=self.user_a_id,
            execution_mode="PAPER",
            skip=0,
            limit=100
        )
        position_query_time = (time.time() - start_time) * 1000

        print(f"持仓查询时间: {position_query_time:.2f} ms")

        # 验证性能（应该 < 100ms）
        assert order_query_time < 100, f"❌ 订单查询时间过长: {order_query_time:.2f} ms"
        assert position_query_time < 100, f"❌ 持仓查询时间过长: {position_query_time:.2f} ms"

        print("✅ 性能测试通过：查询速度符合要求（< 100ms）")
        print()

    def test_index_usage(self):
        """测试索引使用情况"""
        print("=" * 80)
        print("📊 测试 4.2: 索引使用情况")
        print("=" * 80)

        # 使用 EXPLAIN ANALYZE 检查查询计划
        from sqlalchemy import text

        # 检查订单查询是否使用索引
        sql = text("""
            EXPLAIN ANALYZE
            SELECT * FROM orders
            WHERE user_id = :user_id AND execution_mode = :execution_mode
        """)

        result = self.db.execute(sql, {
            "user_id": self.user_a_id,
            "execution_mode": "PAPER"
        }).fetchall()

        # 检查是否使用了索引
        explain_str = str(result)
        uses_index = "idx_orders_user_mode" in explain_str or "Index Scan" in explain_str

        print(f"订单查询计划: {explain_str[:200]}...")

        if uses_index:
            print("✅ 订单查询使用了索引")
        else:
            print("⚠️  订单查询可能没有使用索引（数据量小时可能使用 Seq Scan）")

        print()

    # ============================================================
    # 运行所有测试
    # ============================================================

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("🧪 双轨隔离集成测试套件")
        print("=" * 80 + "\n")

        try:
            # 设置测试数据
            self.setup_test_data()

            # 测试 1: 用户隔离
            self.test_user_isolation_orders()
            self.test_user_isolation_positions()

            # 测试 2: 模式隔离
            self.test_mode_isolation_orders()
            self.test_mode_isolation_positions()

            # 测试 3: 边界条件
            self.test_invalid_user_id()
            self.test_invalid_execution_mode()
            self.test_null_parameters()

            # 测试 4: 性能测试
            self.test_query_performance()
            self.test_index_usage()

            # 清理测试数据
            self.cleanup_test_data()

            print("=" * 80)
            print("✅ 所有测试通过！双轨隔离机制工作正常！")
            print("=" * 80)
            return 0

        except AssertionError as e:
            print(f"\n❌ 测试失败: {e}")
            self.cleanup_test_data()
            return 1
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup_test_data()
            return 1


def main():
    """主函数"""
    test_suite = DualTrackIsolationTest()
    return test_suite.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
