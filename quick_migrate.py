#!/usr/bin/env python3
"""
快速数据迁移脚本
将现有索引文件迁移到租户级目录结构

使用方法:
python quick_migrate.py                    # 试运行
python quick_migrate.py --execute         # 实际执行
python quick_migrate.py --execute --force # 强制执行（跳过确认）
"""

import os
import sys
import shutil
from pathlib import Path

def quick_migrate(execute=False, force=False):
    """快速迁移函数"""

    # 数据目录
    data_dir = Path("data/stock_data/databases")

    if not data_dir.exists():
        print(f"[ERROR] 数据目录不存在: {data_dir}")
        return False

    print("[INFO] 检查现有文件结构...")

    # 检查向量数据库目录
    vector_dir = data_dir / "vector_dbs"
    bm25_dir = data_dir / "bm25"

    # 统计现有文件
    vector_files = []
    bm25_files = []

    if vector_dir.exists():
        vector_files = [f for f in vector_dir.glob("*") if f.is_file()]

    if bm25_dir.exists():
        bm25_files = [f for f in bm25_dir.glob("*") if f.is_file()]

    print(f"[STAT] 发现文件:")
    print(f"  向量数据库文件: {len(vector_files)} 个")
    print(f"  BM25文件: {len(bm25_files)} 个")

    if not vector_files and not bm25_files:
        print("[OK] 没有需要迁移的文件")
        return True

    # 显示文件列表
    if vector_files:
        print(f"\n[FILES] 向量数据库文件:")
        for f in vector_files:
            print(f"  - {f.name}")

    if bm25_files:
        print(f"\n[FILES] BM25文件:")
        for f in bm25_files:
            print(f"  - {f.name}")

    # 检查是否已经迁移
    default_vector_dir = vector_dir / "default"
    default_bm25_dir = bm25_dir / "default"

    if default_vector_dir.exists() or default_bm25_dir.exists():
        print(f"\n[WARN] 检测到默认租户目录已存在，可能已经迁移过")
        if not force:
            response = input("是否继续？(y/N): ").strip().lower()
            if response != 'y':
                print("用户取消迁移")
                return False

    if not execute:
        print(f"\n[DRY-RUN] 试运行模式 - 不会实际移动文件")
        print(f"如需实际执行，请使用: python {sys.argv[0]} --execute")
    else:
        if not force:
            print(f"\n[WARN] 即将开始实际迁移！")
            response = input("确认执行？(y/N): ").strip().lower()
            if response != 'y':
                print("用户取消迁移")
                return False

    print(f"\n[START] 开始迁移...")

    # 场景映射
    scenarios = {
        "tender": ["tender", "招标", "投标"],
        "enterprise": ["enterprise", "企业"],
        "admin": ["admin", "行政"],
        "finance": ["finance", "财务"],
        "procurement": ["procurement", "采购"],
        "engineering": ["engineering", "工程"]
    }

    def determine_scenario(filename):
        """确定文件所属场景"""
        filename_lower = filename.lower()

        for scenario, keywords in scenarios.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return scenario

        # 默认场景
        return "tender"

    # 迁移向量文件
    if vector_files:
        print(f"\n[VECTOR] 迁移向量数据库文件...")

        for file_path in vector_files:
            scenario = determine_scenario(file_path.name)
            target_dir = vector_dir / "default" / scenario
            target_path = target_dir / file_path.name

            print(f"  {file_path.name} -> default/{scenario}/")

            if execute:
                # 创建目标目录
                target_dir.mkdir(parents=True, exist_ok=True)

                # 移动文件
                if target_path.exists():
                    print(f"    [SKIP] 目标文件已存在，跳过")
                    continue

                shutil.move(str(file_path), str(target_path))
                print(f"    [OK] 移动完成")

    # 迁移BM25文件
    if bm25_files:
        print(f"\n[BM25] 迁移BM25文件...")

        for file_path in bm25_files:
            scenario = determine_scenario(file_path.name)
            target_dir = bm25_dir / "default" / scenario
            target_path = target_dir / file_path.name

            print(f"  {file_path.name} -> default/{scenario}/")

            if execute:
                # 创建目标目录
                target_dir.mkdir(parents=True, exist_ok=True)

                # 移动文件
                if target_path.exists():
                    print(f"    [SKIP] 目标文件已存在，跳过")
                    continue

                shutil.move(str(file_path), str(target_path))
                print(f"    [OK] 移动完成")

    # 验证结果
    if execute:
        print(f"\n[VERIFY] 验证迁移结果...")

        total_files = 0
        for scenario in scenarios.keys():
            scenario_vector_dir = vector_dir / "default" / scenario
            scenario_bm25_dir = bm25_dir / "default" / scenario

            vector_count = len(list(scenario_vector_dir.glob("*"))) if scenario_vector_dir.exists() else 0
            bm25_count = len(list(scenario_bm25_dir.glob("*"))) if scenario_bm25_dir.exists() else 0

            if vector_count > 0 or bm25_count > 0:
                print(f"  {scenario}: 向量文件 {vector_count} 个, BM25文件 {bm25_count} 个")
                total_files += vector_count + bm25_count

        print(f"\n[STAT] 迁移完成统计:")
        print(f"  总文件数: {total_files}")

        # 检查是否还有遗留文件
        remaining_vector = [f for f in vector_dir.glob("*") if f.is_file()]
        remaining_bm25 = [f for f in bm25_dir.glob("*") if f.is_file()]

        if remaining_vector or remaining_bm25:
            print(f"  [WARN] 遗留文件: 向量 {len(remaining_vector)} 个, BM25 {len(remaining_bm25)} 个")
        else:
            print(f"  [OK] 无遗留文件")

    print(f"\n[DONE] 迁移{'完成' if execute else '预览完成'}！")

    if execute:
        print(f"\n[STRUCTURE] 新的目录结构:")
        print(f"data/stock_data/databases/")
        print(f"├── vector_dbs/")
        print(f"│   └── default/")
        print(f"│       ├── tender/")
        print(f"│       ├── enterprise/")
        print(f"│       └── ...")
        print(f"└── bm25/")
        print(f"    └── default/")
        print(f"        ├── tender/")
        print(f"        ├── enterprise/")
        print(f"        └── ...")

        print(f"\n[SUCCESS] 现在可以启动系统测试租户隔离功能！")

    return True


def main():
    """主函数"""
    import argparse

    # 设置Windows控制台编码
    if sys.platform.startswith('win'):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

    parser = argparse.ArgumentParser(description="快速租户结构迁移")
    parser.add_argument("--execute", action="store_true", help="实际执行迁移（默认为试运行）")
    parser.add_argument("--force", action="store_true", help="强制执行（跳过确认）")

    args = parser.parse_args()

    print("[MIGRATE] 租户结构快速迁移工具")
    print("=" * 50)

    success = quick_migrate(execute=args.execute, force=args.force)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
