"""
创建 user_settings 表的迁移脚本

运行方式：
    python -m src.database.migrations.add_user_settings_table
"""

from src.core.database import engine
from src.models import Base, UserSettings
from sqlalchemy import text
import sys


def upgrade():
    """升级数据库：创建 user_settings 表"""
    print("开始创建 user_settings 表...")

    try:
        # 创建表
        UserSettings.__table__.create(engine, checkfirst=True)
        print("✅ user_settings 表创建成功")

        # 为现有用户创建默认设置
        from src.core.database import SessionLocal
        from src.models.user import User

        db = SessionLocal()
        try:
            users = db.query(User).all()
            print(f"\n找到 {len(users)} 个用户，正在创建默认设置...")

            for user in users:
                # 检查是否已有设置
                existing = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
                if not existing:
                    settings = UserSettings(
                        user_id=user.id,
                        trading_mode="PAPER",
                        live_trading_enabled=False,
                        risk_control_enabled=True,
                        notifications_enabled=True,
                        notification_email=True,
                        notification_sms=False,
                        language='zh_CN',
                        theme='light',
                        preferences={}
                    )
                    db.add(settings)
                    print(f"  ✓ 为用户 {user.username} 创建默认设置")

            db.commit()
            print("✅ 为所有现有用户创建默认设置")

        except Exception as e:
            db.rollback()
            print(f"❌ 创建用户设置失败: {e}")
            raise
        finally:
            db.close()

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)


def downgrade():
    """回滚数据库：删除 user_settings 表"""
    print("\n开始回滚：删除 user_settings 表...")

    try:
        UserSettings.__table__.drop(engine, checkfirst=True)
        print("✅ user_settings 表已删除")

    except Exception as e:
        print(f"❌ 回滚失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="user_settings 表迁移")
    parser.add_argument("--downgrade", action="store_true", help="回滚迁移")
    args = parser.parse_args()

    if args.downgrade:
        downgrade()
    else:
        upgrade()

    print("\n🎉 迁移完成！")
