"""
添加多租户字段到 chat_sessions 表
迁移脚本：为现有的 chat_sessions 表添加 user_id 和 tenant_id 列
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text


def migrate():
    """执行数据库迁移"""

    # 获取数据库 URL
    db_url = os.getenv("DATABASE_URL", "sqlite:///./data/stock_data/databases/stock_rag.db")

    # 如果是相对路径，转换为绝对路径
    if db_url.startswith("sqlite:///./"):
        db_path = db_url.replace("sqlite:///./", "")
        absolute_path = Path(__file__).parent.parent.parent / db_path
        db_url = f"sqlite:///{absolute_path}"

    print(f"[INFO] 数据库路径: {db_url}")

    engine = create_engine(db_url)

    print("=" * 60)
    print("开始迁移：添加多租户字段到 chat_sessions 表")
    print("=" * 60)

    with engine.connect() as conn:
        try:
            # 检查表是否存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'"
            ))

            if not result.fetchone():
                print("[ERROR] chat_sessions 表不存在，无需迁移")
                return

            print("[OK] 找到 chat_sessions 表")

            # 检查列是否已存在
            result = conn.execute(text("PRAGMA table_info(chat_sessions)"))
            columns = [row[1] for row in result.fetchall()]

            print(f"[INFO] 当前列: {columns}")

            # 需要添加的列
            columns_to_add = []

            if 'user_id' not in columns:
                columns_to_add.append(('user_id', 'VARCHAR(50)'))
                print("[WARN] 需要添加 user_id 列")
            else:
                print("[OK] user_id 列已存在")

            if 'tenant_id' not in columns:
                columns_to_add.append(('tenant_id', 'VARCHAR(50)'))
                print("[WARN] 需要添加 tenant_id 列")
            else:
                print("[OK] tenant_id 列已存在")

            if not columns_to_add:
                print("[OK] 所有必需的列都已存在，无需迁移")
                return

            print("\n" + "=" * 60)
            print("开始添加列...")
            print("=" * 60)

            # SQLite 不支持在一个 ALTER TABLE 中添加多个列，需要分别添加
            for column_name, column_type in columns_to_add:
                try:
                    # 添加列（允许 NULL，因为现有数据没有这个字段）
                    sql = f"ALTER TABLE chat_sessions ADD COLUMN {column_name} {column_type}"
                    print(f"\n执行: {sql}")
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"[OK] 成功添加 {column_name} 列")

                except Exception as e:
                    print(f"[ERROR] 添加 {column_name} 列失败: {str(e)}")
                    raise

            # 获取默认用户和租户（如果存在）
            print("\n" + "=" * 60)
            print("为现有会话设置默认值...")
            print("=" * 60)

            # 获取第一个用户和租户
            result = conn.execute(text("SELECT id FROM users LIMIT 1"))
            default_user = result.fetchone()

            result = conn.execute(text("SELECT id FROM tenants LIMIT 1"))
            default_tenant = result.fetchone()

            if default_user and default_tenant:
                default_user_id = default_user[0]
                default_tenant_id = default_tenant[0]

                print(f"默认用户ID: {default_user_id}")
                print(f"默认租户ID: {default_tenant_id}")

                # 更新现有的会话（如果有）
                result = conn.execute(text("SELECT COUNT(*) FROM chat_sessions"))
                session_count = result.fetchone()[0]

                if session_count > 0:
                    print(f"\n找到 {session_count} 个现有会话，更新它们的 user_id 和 tenant_id...")

                    # 更新 user_id
                    if 'user_id' in [col[0] for col in columns_to_add]:
                        conn.execute(text(
                            f"UPDATE chat_sessions SET user_id = :user_id WHERE user_id IS NULL"
                        ), {"user_id": default_user_id})
                        print(f"[OK] 已将现有会话的 user_id 设置为 {default_user_id}")

                    # 更新 tenant_id
                    if 'tenant_id' in [col[0] for col in columns_to_add]:
                        conn.execute(text(
                            f"UPDATE chat_sessions SET tenant_id = :tenant_id WHERE tenant_id IS NULL"
                        ), {"tenant_id": default_tenant_id})
                        print(f"[OK] 已将现有会话的 tenant_id 设置为 {default_tenant_id}")

                    conn.commit()
                else:
                    print("[INFO] 没有现有会话需要更新")
            else:
                print("[WARN] 警告：没有找到默认用户或租户，现有会话的这些字段将保持为 NULL")

            # 验证迁移结果
            print("\n" + "=" * 60)
            print("验证迁移结果...")
            print("=" * 60)

            result = conn.execute(text("PRAGMA table_info(chat_sessions)"))
            columns_after = [row[1] for row in result.fetchall()]

            print(f"[INFO] 迁移后的列: {columns_after}")

            if 'user_id' in columns_after and 'tenant_id' in columns_after:
                print("[OK] 迁移成功！所有列都已添加")
            else:
                print("[ERROR] 迁移可能不完整")

            # 显示会话统计
            result = conn.execute(text("SELECT COUNT(*) FROM chat_sessions"))
            total_sessions = result.fetchone()[0]

            result = conn.execute(text("SELECT COUNT(*) FROM chat_sessions WHERE user_id IS NOT NULL AND tenant_id IS NOT NULL"))
            valid_sessions = result.fetchone()[0]

            print(f"\n[INFO] 会话统计:")
            print(f"  - 总会话数: {total_sessions}")
            print(f"  - 有效会话数（已设置user_id和tenant_id）: {valid_sessions}")

            print("\n" + "=" * 60)
            print("[OK] 迁移完成！")
            print("=" * 60)

        except Exception as e:
            print(f"\n[ERROR] 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    migrate()

