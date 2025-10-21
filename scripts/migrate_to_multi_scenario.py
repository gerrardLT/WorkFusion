#!/usr/bin/env python
"""
多场景AI知识问答系统数据迁移脚本
将现有内存数据迁移到新的多场景数据库结构
"""

import os
import sys
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.config import get_settings
except ImportError:
    # 如果导入失败，使用简单的配置
    class SimpleConfig:
        def __init__(self):
            self.project_root = project_root
            self.data_dir = self.project_root / "data" / "stock_data"
            self.pdf_dir = self.data_dir / "pdf_reports"
            self.db_dir = self.data_dir / "databases"

        class DatabaseConfig:
            url = "sqlite:///./data/stock_data/databases/stock_rag.db"

        database = DatabaseConfig()

    def get_settings():
        return SimpleConfig()

class DataMigration:
    """数据迁移工具"""

    def __init__(self, database_path: Optional[str] = None):
        """初始化迁移工具"""
        self.settings = get_settings()

        # 数据库路径
        if database_path:
            self.db_path = Path(database_path)
        else:
            # 从配置中解析数据库路径
            db_url = self.settings.database.url
            if db_url.startswith('sqlite:///'):
                self.db_path = Path(db_url.replace('sqlite:///', ''))
            else:
                # 默认路径
                self.db_path = self.settings.data_dir / "databases" / "stock_rag.db"

        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # SQL脚本路径
        self.sql_script_path = project_root / "scripts" / "create_multi_scenario_tables.sql"

        print(f"📊 数据库路径: {self.db_path}")
        print(f"📜 SQL脚本路径: {self.sql_script_path}")

    def create_database(self) -> bool:
        """创建数据库表结构"""
        try:
            print("🔧 正在创建数据库表结构...")

            if not self.sql_script_path.exists():
                print(f"❌ SQL脚本文件不存在: {self.sql_script_path}")
                return False

            # 读取SQL脚本
            with open(self.sql_script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            # 连接数据库并执行脚本
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(sql_script)
                conn.commit()

            print("✅ 数据库表结构创建完成")
            return True

        except Exception as e:
            print(f"❌ 创建数据库表结构失败: {str(e)}")
            return False

    def verify_database(self) -> bool:
        """验证数据库结构"""
        try:
            print("🔍 正在验证数据库结构...")

            expected_tables = [
                'scenarios', 'document_types', 'documents',
                'chat_sessions', 'chat_messages',
                'document_chunks', 'vector_embeddings',
                'db_version'
            ]

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 检查表是否存在
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                existing_tables = [row[0] for row in cursor.fetchall()]

                print(f"📋 现有表: {existing_tables}")

                # 检查必要的表是否都存在
                missing_tables = set(expected_tables) - set(existing_tables)
                if missing_tables:
                    print(f"❌ 缺少表: {missing_tables}")
                    return False

                # 检查场景数据
                cursor.execute("SELECT COUNT(*) FROM scenarios")
                scenario_count = cursor.fetchone()[0]
                print(f"📊 场景数量: {scenario_count}")

                if scenario_count < 2:
                    print("❌ 场景数据不完整")
                    return False

                # 检查文档类型数据
                cursor.execute("SELECT COUNT(*) FROM document_types")
                doc_type_count = cursor.fetchone()[0]
                print(f"📄 文档类型数量: {doc_type_count}")

                print("✅ 数据库结构验证通过")
                return True

        except Exception as e:
            print(f"❌ 验证数据库结构失败: {str(e)}")
            return False

    def show_scenario_info(self) -> None:
        """显示场景信息"""
        try:
            print("\n📋 场景配置信息:")
            print("-" * 50)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, name, description, status, created_at
                    FROM scenarios
                    ORDER BY created_at
                """)

                scenarios = cursor.fetchall()

                for scenario in scenarios:
                    scenario_id, name, description, status, created_at = scenario
                    print(f"🎯 场景ID: {scenario_id}")
                    print(f"   名称: {name}")
                    print(f"   描述: {description}")
                    print(f"   状态: {status}")
                    print(f"   创建时间: {created_at}")

                    # 获取该场景的文档类型
                    cursor.execute("""
                        SELECT name, description
                        FROM document_types
                        WHERE scenario_id = ?
                    """, (scenario_id,))

                    doc_types = cursor.fetchall()
                    if doc_types:
                        print("   文档类型:")
                        for doc_type in doc_types:
                            print(f"     - {doc_type[0]}: {doc_type[1]}")

                    print()

        except Exception as e:
            print(f"❌ 获取场景信息失败: {str(e)}")

    def migrate_existing_data(self) -> bool:
        """迁移现有数据到多场景结构"""
        try:
            print("🔄 正在检查是否有现有数据需要迁移...")

            # 注意：当前系统使用内存存储，没有持久化数据
            # 这里主要是为了演示迁移逻辑和未来扩展

            # 如果将来有文件数据或其他持久化数据，可以在这里处理
            # 例如：迁移PDF文件信息到documents表

            pdf_dir = self.settings.pdf_dir
            if pdf_dir.exists():
                pdf_files = list(pdf_dir.glob("*.pdf"))
                if pdf_files:
                    print(f"📄 发现 {len(pdf_files)} 个PDF文件，准备迁移...")
                    self._migrate_pdf_files(pdf_files)
                else:
                    print("📄 未发现PDF文件")
            else:
                print("📄 PDF目录不存在")

            print("✅ 数据迁移完成")
            return True

        except Exception as e:
            print(f"❌ 数据迁移失败: {str(e)}")
            return False

    def _migrate_pdf_files(self, pdf_files: List[Path]) -> None:
        """迁移PDF文件信息到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for pdf_file in pdf_files:
                    # 生成文档ID
                    doc_id = str(uuid.uuid4())

                    # 获取文件信息
                    file_size = pdf_file.stat().st_size
                    relative_path = str(pdf_file.relative_to(self.settings.project_root))

                    # 默认分配到投研场景（可以后续调整）
                    scenario_id = 'investment'
                    document_type_id = 'investment_research_report'

                    # 基础元数据
                    metadata = {
                        "original_filename": pdf_file.name,
                        "migrated_from": "existing_files",
                        "migrated_at": datetime.now().isoformat()
                    }

                    # 插入文档记录
                    cursor.execute("""
                        INSERT INTO documents (
                            id, scenario_id, document_type_id, title,
                            file_path, file_size, metadata, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc_id,
                        scenario_id,
                        document_type_id,
                        pdf_file.stem,  # 文件名作为标题
                        relative_path,
                        file_size,
                        json.dumps(metadata),
                        'pending'  # 需要重新处理
                    ))

                conn.commit()
                print(f"✅ 成功迁移 {len(pdf_files)} 个PDF文件信息")

        except Exception as e:
            print(f"❌ 迁移PDF文件失败: {str(e)}")

    def backup_existing_database(self) -> Optional[Path]:
        """备份现有数据库"""
        try:
            if self.db_path.exists():
                backup_path = self.db_path.with_suffix('.backup.' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.db')

                print(f"💾 正在备份现有数据库到: {backup_path}")

                # 复制文件
                import shutil
                shutil.copy2(self.db_path, backup_path)

                print("✅ 数据库备份完成")
                return backup_path
            else:
                print("📄 没有现有数据库需要备份")
                return None

        except Exception as e:
            print(f"❌ 备份数据库失败: {str(e)}")
            return None

    def run_migration(self, force_recreate: bool = False) -> bool:
        """运行完整的迁移流程"""
        try:
            print("🚀 开始多场景数据库迁移...")
            print("=" * 50)

            # 1. 备份现有数据库
            if not force_recreate:
                backup_path = self.backup_existing_database()

            # 2. 创建新的数据库结构
            if not self.create_database():
                return False

            # 3. 验证数据库结构
            if not self.verify_database():
                return False

            # 4. 迁移现有数据
            if not self.migrate_existing_data():
                return False

            # 5. 显示场景信息
            self.show_scenario_info()

            print("=" * 50)
            print("🎉 多场景数据库迁移完成！")
            print()
            print("📋 迁移总结:")
            print("- ✅ 数据库表结构创建完成")
            print("- ✅ 投研和招投标场景配置完成")
            print("- ✅ 文档类型配置完成")
            print("- ✅ 数据迁移完成")
            print()
            print("🔗 下一步:")
            print("1. 更新后端代码使用新的数据库结构")
            print("2. 实现场景服务层")
            print("3. 重构API接口支持多场景")

            return True

        except Exception as e:
            print(f"❌ 迁移过程失败: {str(e)}")
            return False

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='多场景AI知识问答系统数据迁移工具')
    parser.add_argument('--database', '-d', type=str, help='数据库文件路径')
    parser.add_argument('--force', '-f', action='store_true', help='强制重新创建数据库')
    parser.add_argument('--verify-only', '-v', action='store_true', help='仅验证数据库结构')
    parser.add_argument('--show-info', '-i', action='store_true', help='显示场景信息')

    args = parser.parse_args()

    # 创建迁移工具实例
    migration = DataMigration(args.database)

    if args.verify_only:
        # 仅验证数据库
        if migration.verify_database():
            print("✅ 数据库结构验证通过")
            sys.exit(0)
        else:
            print("❌ 数据库结构验证失败")
            sys.exit(1)

    elif args.show_info:
        # 显示场景信息
        migration.show_scenario_info()
        sys.exit(0)

    else:
        # 运行完整迁移
        if migration.run_migration(args.force):
            print("🎉 迁移成功完成！")
            sys.exit(0)
        else:
            print("❌ 迁移失败！")
            sys.exit(1)

if __name__ == "__main__":
    main()
