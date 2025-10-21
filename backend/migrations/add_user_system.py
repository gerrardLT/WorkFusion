"""
用户系统数据迁移脚本
为现有数据添加默认租户和用户，并更新现有会话和文档数据
"""

import sys
from pathlib import Path
import bcrypt

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from backend.database import DATABASE_URL
from backend.models.user import Tenant, User, Role
from backend.models.chat import ChatSession
from backend.models.document import Document


def generate_id(length: int = 32) -> str:
    """生成唯一ID"""
    return str(uuid.uuid4()).replace('-', '')[:length]


def migrate_existing_data():
    """迁移现有数据"""
    print("=" * 60)
    print("开始用户系统数据迁移")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ==================== 步骤1：创建默认租户 ====================
        print("\n[1/6] 创建默认租户...")

        existing_tenant = session.query(Tenant).filter(Tenant.code == "DEFAULT").first()
        if existing_tenant:
            print(f"  ⚠️  默认租户已存在: {existing_tenant.name}")
            default_tenant_id = existing_tenant.id
        else:
            default_tenant = Tenant(
                id="default-tenant",
                name="默认组织",
                code="DEFAULT",
                status="active",
                config={"data_sharing": {"company": "shared", "project": "shared"}},
                max_users=100,
                max_storage_mb=10000
            )
            session.add(default_tenant)
            session.flush()
            default_tenant_id = default_tenant.id
            print(f"  ✅ 默认租户创建成功: {default_tenant.name}")

        # ==================== 步骤2：创建系统角色 ====================
        print("\n[2/6] 创建系统角色...")

        # 管理员角色
        admin_role = session.query(Role).filter(
            Role.name == "admin",
            Role.is_system == True
        ).first()

        if not admin_role:
            admin_role = Role(
                id="role-admin",
                name="admin",
                display_name="管理员",
                description="租户管理员，拥有所有权限",
                permissions={
                    "chat": ["create", "read", "update", "delete"],
                    "document": ["upload", "read", "delete"],
                    "knowledge": ["create", "read", "update", "delete"],
                    "report": ["generate", "read", "export"],
                    "user": ["create", "read", "update", "delete"],
                    "tenant": ["read", "update"]
                },
                is_system=True
            )
            session.add(admin_role)
            print("  ✅ 管理员角色创建成功")
        else:
            print("  ⚠️  管理员角色已存在")

        # 普通用户角色
        user_role = session.query(Role).filter(
            Role.name == "user",
            Role.is_system == True
        ).first()

        if not user_role:
            user_role = Role(
                id="role-user",
                name="user",
                display_name="普通用户",
                description="普通用户，拥有基础使用权限",
                permissions={
                    "chat": ["create", "read", "update", "delete"],
                    "document": ["upload", "read"],
                    "knowledge": ["read"],
                    "report": ["read"]
                },
                is_system=True
            )
            session.add(user_role)
            print("  ✅ 普通用户角色创建成功")
        else:
            print("  ⚠️  普通用户角色已存在")

        session.flush()

        # ==================== 步骤3：创建默认管理员用户 ====================
        print("\n[3/6] 创建默认管理员用户...")

        existing_admin = session.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print(f"  ⚠️  管理员用户已存在: {existing_admin.username}")
            default_user_id = existing_admin.id
        else:
            password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            admin_user = User(
                id="default-admin",
                tenant_id=default_tenant_id,
                username="admin",
                password_hash=password_hash,
                nickname="系统管理员",
                email="admin@example.com",
                role_id=admin_role.id,
                status="active",
                is_verified=True
            )
            session.add(admin_user)
            session.flush()
            default_user_id = admin_user.id
            print("  ✅ 默认管理员创建成功")
            print("     用户名: admin")
            print("     密码: admin123")
            print("     ⚠️  请在生产环境中及时修改默认密码！")

        # ==================== 步骤4：更新现有会话数据 ====================
        print("\n[4/6] 更新现有会话数据...")

        # 检查表是否存在以及是否有tenant_id列
        try:
            sessions = session.query(ChatSession).all()
            updated_count = 0

            for s in sessions:
                # 如果会话没有user_id或tenant_id，设置为默认值
                if not hasattr(s, 'user_id') or not s.user_id:
                    s.user_id = default_user_id
                    updated_count += 1
                if not hasattr(s, 'tenant_id') or not s.tenant_id:
                    s.tenant_id = default_tenant_id
                    updated_count += 1

            if updated_count > 0:
                print(f"  ✅ 更新了 {len(sessions)} 个会话的用户和租户信息")
            else:
                print(f"  ℹ️  {len(sessions)} 个会话已经有用户和租户信息")

        except Exception as e:
            print(f"  ⚠️  会话数据更新跳过（可能是新表）: {str(e)}")

        # ==================== 步骤5：更新现有文档数据 ====================
        print("\n[5/6] 更新现有文档数据...")

        try:
            documents = session.query(Document).all()
            updated_count = 0

            for doc in documents:
                # 如果文档没有tenant_id或uploaded_by，设置为默认值
                if not hasattr(doc, 'tenant_id') or not doc.tenant_id:
                    doc.tenant_id = default_tenant_id
                    updated_count += 1
                if not hasattr(doc, 'uploaded_by') or not doc.uploaded_by:
                    doc.uploaded_by = default_user_id
                    updated_count += 1

            if updated_count > 0:
                print(f"  ✅ 更新了 {len(documents)} 个文档的租户和上传者信息")
            else:
                print(f"  ℹ️  {len(documents)} 个文档已经有租户和上传者信息")

        except Exception as e:
            print(f"  ⚠️  文档数据更新跳过（可能是新表）: {str(e)}")

        # ==================== 步骤6：提交事务 ====================
        print("\n[6/6] 提交事务...")
        session.commit()
        print("  ✅ 所有更改已提交")

        print("\n" + "=" * 60)
        print("✅ 数据迁移完成！")
        print("=" * 60)
        print("\n默认登录信息：")
        print("  用户名: admin")
        print("  密码: admin123")
        print("\n⚠️  重要提醒：")
        print("  1. 请在生产环境中立即修改默认密码")
        print("  2. 建议为每个实际用户创建独立账号")
        print("  3. 现有数据已关联到默认租户")
        print()

    except Exception as e:
        session.rollback()
        print("\n" + "=" * 60)
        print(f"❌ 数据迁移失败: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate_existing_data()

