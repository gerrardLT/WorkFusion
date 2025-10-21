#!/usr/bin/env python3
"""
数据迁移脚本：将现有索引文件迁移到租户级目录结构

迁移内容：
1. 向量数据库索引文件 (FAISS)
2. BM25索引文件
3. 相关元数据文件

迁移前结构：
data/stock_data/databases/
├── vector_dbs/
│   ├── tender.index
│   ├── enterprise.index
│   └── ...
└── bm25/
    ├── tender_bm25.pkl
    ├── enterprise_bm25.pkl
    └── ...

迁移后结构：
data/stock_data/databases/
├── vector_dbs/
│   └── default/
│       ├── tender/
│       │   └── tender.index
│       └── enterprise/
│           └── enterprise.index
└── bm25/
    └── default/
        ├── tender/
        │   └── tender_bm25.pkl
        └── enterprise/
            └── enterprise_bm25.pkl
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# 默认租户ID
DEFAULT_TENANT_ID = "default"

# 支持的场景列表
SCENARIOS = ["tender", "enterprise", "admin", "finance", "procurement", "engineering"]


class TenantStructureMigrator:
    """租户结构迁移器"""

    def __init__(self, data_dir: Path = None, dry_run: bool = False):
        """初始化迁移器

        Args:
            data_dir: 数据目录路径
            dry_run: 是否为试运行模式（不实际移动文件）
        """
        self.settings = get_settings()
        self.data_dir = data_dir or self.settings.data_dir
        self.dry_run = dry_run

        # 关键目录路径
        self.databases_dir = self.data_dir / "databases"
        self.vector_dbs_dir = self.databases_dir / "vector_dbs"
        self.bm25_dir = self.databases_dir / "bm25"

        # 迁移统计
        self.migration_stats = {
            "vector_files_moved": 0,
            "bm25_files_moved": 0,
            "metadata_files_moved": 0,
            "directories_created": 0,
            "errors": []
        }

        logger.info(f"迁移器初始化完成")
        logger.info(f"数据目录: {self.data_dir}")
        logger.info(f"试运行模式: {self.dry_run}")

    def check_prerequisites(self) -> bool:
        """检查迁移前提条件

        Returns:
            是否满足迁移条件
        """
        logger.info("检查迁移前提条件...")

        # 检查数据目录是否存在
        if not self.data_dir.exists():
            logger.error(f"数据目录不存在: {self.data_dir}")
            return False

        if not self.databases_dir.exists():
            logger.error(f"数据库目录不存在: {self.databases_dir}")
            return False

        # 检查是否已经迁移过
        default_tenant_dir = self.vector_dbs_dir / DEFAULT_TENANT_ID
        if default_tenant_dir.exists():
            logger.warning(f"检测到默认租户目录已存在: {default_tenant_dir}")
            logger.warning("可能已经迁移过，请确认是否需要重新迁移")

            # 询问用户是否继续
            if not self.dry_run:
                response = input("是否继续迁移？(y/N): ").strip().lower()
                if response != 'y':
                    logger.info("用户取消迁移")
                    return False

        logger.info("前提条件检查通过")
        return True

    def backup_existing_structure(self) -> bool:
        """备份现有目录结构

        Returns:
            备份是否成功
        """
        if self.dry_run:
            logger.info("[DRY RUN] 跳过备份步骤")
            return True

        logger.info("创建现有结构的备份...")

        try:
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.databases_dir.parent / f"databases_backup_{backup_timestamp}"

            # 创建备份目录
            backup_dir.mkdir(exist_ok=True)

            # 备份向量数据库目录
            if self.vector_dbs_dir.exists():
                vector_backup = backup_dir / "vector_dbs"
                shutil.copytree(self.vector_dbs_dir, vector_backup)
                logger.info(f"向量数据库备份完成: {vector_backup}")

            # 备份BM25目录
            if self.bm25_dir.exists():
                bm25_backup = backup_dir / "bm25"
                shutil.copytree(self.bm25_dir, bm25_backup)
                logger.info(f"BM25数据库备份完成: {bm25_backup}")

            logger.info(f"备份完成: {backup_dir}")
            return True

        except Exception as e:
            logger.error(f"备份失败: {e}")
            return False

    def create_tenant_directories(self) -> bool:
        """创建租户级目录结构

        Returns:
            创建是否成功
        """
        logger.info("创建租户级目录结构...")

        try:
            # 为每个场景创建默认租户目录
            for scenario in SCENARIOS:
                # 创建向量数据库租户目录
                vector_tenant_dir = self.vector_dbs_dir / DEFAULT_TENANT_ID / scenario
                if not vector_tenant_dir.exists():
                    if not self.dry_run:
                        vector_tenant_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"创建向量数据库目录: {vector_tenant_dir}")
                    self.migration_stats["directories_created"] += 1

                # 创建BM25租户目录
                bm25_tenant_dir = self.bm25_dir / DEFAULT_TENANT_ID / scenario
                if not bm25_tenant_dir.exists():
                    if not self.dry_run:
                        bm25_tenant_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"创建BM25目录: {bm25_tenant_dir}")
                    self.migration_stats["directories_created"] += 1

            return True

        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            self.migration_stats["errors"].append(f"创建目录失败: {e}")
            return False

    def migrate_vector_databases(self) -> bool:
        """迁移向量数据库文件

        Returns:
            迁移是否成功
        """
        logger.info("迁移向量数据库文件...")

        if not self.vector_dbs_dir.exists():
            logger.warning("向量数据库目录不存在，跳过迁移")
            return True

        try:
            # 查找所有向量数据库文件
            vector_files = []

            # 查找 .index 文件（FAISS索引）
            for index_file in self.vector_dbs_dir.glob("*.index"):
                vector_files.append(index_file)

            # 查找其他相关文件
            for pattern in ["*.json", "*.pkl", "*.npy"]:
                for file in self.vector_dbs_dir.glob(pattern):
                    vector_files.append(file)

            logger.info(f"发现 {len(vector_files)} 个向量数据库文件")

            for file_path in vector_files:
                # 确定目标场景
                scenario = self._determine_scenario_from_filename(file_path.name)
                if not scenario:
                    logger.warning(f"无法确定场景，跳过文件: {file_path.name}")
                    continue

                # 目标路径
                target_dir = self.vector_dbs_dir / DEFAULT_TENANT_ID / scenario
                target_path = target_dir / file_path.name

                # 移动文件
                if not self.dry_run:
                    if target_path.exists():
                        logger.warning(f"目标文件已存在，跳过: {target_path}")
                        continue

                    shutil.move(str(file_path), str(target_path))

                logger.info(f"迁移向量文件: {file_path.name} -> {target_path}")
                self.migration_stats["vector_files_moved"] += 1

            return True

        except Exception as e:
            logger.error(f"迁移向量数据库失败: {e}")
            self.migration_stats["errors"].append(f"迁移向量数据库失败: {e}")
            return False

    def migrate_bm25_databases(self) -> bool:
        """迁移BM25数据库文件

        Returns:
            迁移是否成功
        """
        logger.info("迁移BM25数据库文件...")

        if not self.bm25_dir.exists():
            logger.warning("BM25目录不存在，跳过迁移")
            return True

        try:
            # 查找所有BM25文件
            bm25_files = []

            # 查找 .pkl 文件（BM25索引）
            for pkl_file in self.bm25_dir.glob("*.pkl"):
                bm25_files.append(pkl_file)

            # 查找其他相关文件
            for pattern in ["*.json", "*.txt"]:
                for file in self.bm25_dir.glob(pattern):
                    bm25_files.append(file)

            logger.info(f"发现 {len(bm25_files)} 个BM25文件")

            for file_path in bm25_files:
                # 确定目标场景
                scenario = self._determine_scenario_from_filename(file_path.name)
                if not scenario:
                    logger.warning(f"无法确定场景，跳过文件: {file_path.name}")
                    continue

                # 目标路径
                target_dir = self.bm25_dir / DEFAULT_TENANT_ID / scenario
                target_path = target_dir / file_path.name

                # 移动文件
                if not self.dry_run:
                    if target_path.exists():
                        logger.warning(f"目标文件已存在，跳过: {target_path}")
                        continue

                    shutil.move(str(file_path), str(target_path))

                logger.info(f"迁移BM25文件: {file_path.name} -> {target_path}")
                self.migration_stats["bm25_files_moved"] += 1

            return True

        except Exception as e:
            logger.error(f"迁移BM25数据库失败: {e}")
            self.migration_stats["errors"].append(f"迁移BM25数据库失败: {e}")
            return False

    def _determine_scenario_from_filename(self, filename: str) -> str:
        """从文件名确定场景

        Args:
            filename: 文件名

        Returns:
            场景ID，如果无法确定则返回None
        """
        filename_lower = filename.lower()

        # 直接匹配场景名
        for scenario in SCENARIOS:
            if scenario in filename_lower:
                return scenario

        # 特殊匹配规则
        if "投标" in filename or "招标" in filename:
            return "tender"
        elif "企业" in filename:
            return "enterprise"

        # 默认场景（如果无法确定）
        logger.warning(f"无法从文件名确定场景，使用默认场景 'tender': {filename}")
        return "tender"

    def verify_migration(self) -> bool:
        """验证迁移结果

        Returns:
            验证是否通过
        """
        logger.info("验证迁移结果...")

        if self.dry_run:
            logger.info("[DRY RUN] 跳过验证步骤")
            return True

        try:
            # 检查默认租户目录是否存在
            default_vector_dir = self.vector_dbs_dir / DEFAULT_TENANT_ID
            default_bm25_dir = self.bm25_dir / DEFAULT_TENANT_ID

            if not default_vector_dir.exists():
                logger.error("默认租户向量目录不存在")
                return False

            if not default_bm25_dir.exists():
                logger.error("默认租户BM25目录不存在")
                return False

            # 统计迁移后的文件数量
            total_files = 0
            for scenario in SCENARIOS:
                scenario_vector_dir = default_vector_dir / scenario
                scenario_bm25_dir = default_bm25_dir / scenario

                if scenario_vector_dir.exists():
                    vector_files = list(scenario_vector_dir.glob("*"))
                    total_files += len(vector_files)
                    logger.info(f"场景 {scenario} 向量文件: {len(vector_files)} 个")

                if scenario_bm25_dir.exists():
                    bm25_files = list(scenario_bm25_dir.glob("*"))
                    total_files += len(bm25_files)
                    logger.info(f"场景 {scenario} BM25文件: {len(bm25_files)} 个")

            logger.info(f"迁移后总文件数: {total_files}")

            # 检查原目录是否还有遗留文件
            remaining_vector_files = [f for f in self.vector_dbs_dir.glob("*")
                                    if f.is_file() and f.name != DEFAULT_TENANT_ID]
            remaining_bm25_files = [f for f in self.bm25_dir.glob("*")
                                  if f.is_file() and f.name != DEFAULT_TENANT_ID]

            if remaining_vector_files:
                logger.warning(f"向量目录中还有 {len(remaining_vector_files)} 个未迁移文件")
                for f in remaining_vector_files:
                    logger.warning(f"  未迁移: {f.name}")

            if remaining_bm25_files:
                logger.warning(f"BM25目录中还有 {len(remaining_bm25_files)} 个未迁移文件")
                for f in remaining_bm25_files:
                    logger.warning(f"  未迁移: {f.name}")

            logger.info("迁移验证完成")
            return True

        except Exception as e:
            logger.error(f"验证迁移失败: {e}")
            return False

    def print_migration_summary(self):
        """打印迁移摘要"""
        logger.info("=" * 60)
        logger.info("迁移摘要")
        logger.info("=" * 60)
        logger.info(f"向量文件迁移数量: {self.migration_stats['vector_files_moved']}")
        logger.info(f"BM25文件迁移数量: {self.migration_stats['bm25_files_moved']}")
        logger.info(f"元数据文件迁移数量: {self.migration_stats['metadata_files_moved']}")
        logger.info(f"创建目录数量: {self.migration_stats['directories_created']}")
        logger.info(f"错误数量: {len(self.migration_stats['errors'])}")

        if self.migration_stats['errors']:
            logger.error("错误详情:")
            for error in self.migration_stats['errors']:
                logger.error(f"  - {error}")

        logger.info("=" * 60)

    def run_migration(self) -> bool:
        """运行完整迁移流程

        Returns:
            迁移是否成功
        """
        logger.info("开始租户结构迁移...")

        # 1. 检查前提条件
        if not self.check_prerequisites():
            logger.error("前提条件检查失败，终止迁移")
            return False

        # 2. 备份现有结构
        if not self.backup_existing_structure():
            logger.error("备份失败，终止迁移")
            return False

        # 3. 创建租户目录
        if not self.create_tenant_directories():
            logger.error("创建租户目录失败，终止迁移")
            return False

        # 4. 迁移向量数据库
        if not self.migrate_vector_databases():
            logger.error("迁移向量数据库失败")
            # 继续执行，不终止

        # 5. 迁移BM25数据库
        if not self.migrate_bm25_databases():
            logger.error("迁移BM25数据库失败")
            # 继续执行，不终止

        # 6. 验证迁移结果
        if not self.verify_migration():
            logger.error("迁移验证失败")
            return False

        # 7. 打印摘要
        self.print_migration_summary()

        if self.migration_stats['errors']:
            logger.warning("迁移完成，但存在错误，请检查日志")
            return False
        else:
            logger.info("迁移成功完成！")
            return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="租户结构迁移脚本")
    parser.add_argument("--data-dir", type=str, help="数据目录路径")
    parser.add_argument("--dry-run", action="store_true", help="试运行模式（不实际移动文件）")
    parser.add_argument("--force", action="store_true", help="强制执行（跳过确认）")

    args = parser.parse_args()

    # 创建迁移器
    data_dir = Path(args.data_dir) if args.data_dir else None
    migrator = TenantStructureMigrator(data_dir=data_dir, dry_run=args.dry_run)

    # 确认执行
    if not args.force and not args.dry_run:
        print("\n" + "=" * 60)
        print("租户结构迁移脚本")
        print("=" * 60)
        print("此脚本将:")
        print("1. 备份现有数据库结构")
        print("2. 创建租户级目录结构")
        print("3. 迁移现有索引文件到默认租户目录")
        print("4. 验证迁移结果")
        print("\n注意: 此操作会修改现有目录结构！")
        print("建议先使用 --dry-run 参数进行试运行")
        print("=" * 60)

        response = input("是否继续执行迁移？(y/N): ").strip().lower()
        if response != 'y':
            print("用户取消迁移")
            return

    # 执行迁移
    success = migrator.run_migration()

    if success:
        print("\n🎉 迁移成功完成！")
        if not args.dry_run:
            print("现在可以启动系统测试租户隔离功能")
    else:
        print("\n❌ 迁移失败，请检查日志")
        sys.exit(1)


if __name__ == "__main__":
    main()
