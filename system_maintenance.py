#!/usr/bin/env python
"""
系统维护脚本
提供日常维护、清理、备份、诊断等功能
"""

import os
import sys
import shutil
import json
import time
import tarfile
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class SystemMaintainer:
    """系统维护器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.data_dir = self.project_root / "data/stock_data"
        self.logs_dir = self.project_root / "logs"
        self.backup_dir = self.project_root / "backups"

        # 确保目录存在
        self.logs_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)

        # 写入维护日志
        log_file = self.logs_dir / "maintenance.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "disk_usage": {},
            "file_counts": {},
            "log_size": {},
            "database_size": {},
        }

        try:
            # 磁盘使用情况
            disk_usage = shutil.disk_usage(self.project_root)
            status["disk_usage"] = {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "usage_percent": round((disk_usage.used / disk_usage.total) * 100, 2),
            }

            # 文件统计
            if self.data_dir.exists():
                pdf_files = list(self.data_dir.glob("pdf_reports/*.pdf"))
                parsed_files = list(self.data_dir.glob("debug_data/*/*.json"))
                vector_files = list(self.data_dir.glob("databases/vector_dbs/*.faiss"))
                bm25_files = list(self.data_dir.glob("databases/bm25/*.pkl"))

                status["file_counts"] = {
                    "pdf_reports": len(pdf_files),
                    "parsed_files": len(parsed_files),
                    "vector_files": len(vector_files),
                    "bm25_files": len(bm25_files),
                }

            # 日志大小
            if self.logs_dir.exists():
                log_files = list(self.logs_dir.glob("*.log"))
                total_log_size = sum(f.stat().st_size for f in log_files)

                status["log_size"] = {
                    "total_mb": round(total_log_size / (1024**2), 2),
                    "file_count": len(log_files),
                }

            # 数据库大小
            if self.data_dir.exists():
                db_dirs = [
                    "databases/vector_dbs",
                    "databases/bm25",
                    "databases/chunked_reports",
                ]
                total_db_size = 0

                for db_dir in db_dirs:
                    db_path = self.data_dir / db_dir
                    if db_path.exists():
                        for file_path in db_path.rglob("*"):
                            if file_path.is_file():
                                total_db_size += file_path.stat().st_size

                status["database_size"] = {
                    "total_mb": round(total_db_size / (1024**2), 2)
                }

        except Exception as e:
            status["error"] = str(e)

        return status

    def clean_logs(self, keep_days: int = 7) -> Dict[str, Any]:
        """清理日志文件"""
        self.log(f"清理 {keep_days} 天前的日志文件...")

        result = {"cleaned_files": [], "cleaned_size": 0, "error": None}

        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)

            for log_file in self.logs_dir.glob("*.log"):
                try:
                    # 检查文件修改时间
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)

                    if file_time < cutoff_date and log_file.name != "maintenance.log":
                        file_size = log_file.stat().st_size
                        log_file.unlink()

                        result["cleaned_files"].append(log_file.name)
                        result["cleaned_size"] += file_size

                        self.log(f"删除日志文件: {log_file.name}")

                except Exception as e:
                    self.log(f"删除日志文件失败 {log_file}: {e}", "ERROR")

            if result["cleaned_files"]:
                size_mb = round(result["cleaned_size"] / (1024**2), 2)
                self.log(
                    f"日志清理完成: 删除 {len(result['cleaned_files'])} 个文件，释放 {size_mb}MB"
                )
            else:
                self.log("没有需要清理的日志文件")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"日志清理失败: {e}", "ERROR")

        return result

    def clean_temp_files(self) -> Dict[str, Any]:
        """清理临时文件"""
        self.log("清理临时文件...")

        result = {"cleaned_files": [], "cleaned_size": 0, "error": None}

        try:
            # 要清理的临时文件模式
            temp_patterns = [
                "*.tmp",
                "*.temp",
                "*~",
                "*.bak",
                "*.pyc",
                "__pycache__",
                ".DS_Store",
                "Thumbs.db",
            ]

            for pattern in temp_patterns:
                for temp_file in self.project_root.rglob(pattern):
                    try:
                        if temp_file.is_file():
                            file_size = temp_file.stat().st_size
                            temp_file.unlink()

                            result["cleaned_files"].append(str(temp_file))
                            result["cleaned_size"] += file_size
                        elif temp_file.is_dir() and pattern == "__pycache__":
                            shutil.rmtree(temp_file)
                            result["cleaned_files"].append(str(temp_file))

                    except Exception as e:
                        self.log(f"删除临时文件失败 {temp_file}: {e}", "WARNING")

            if result["cleaned_files"]:
                size_mb = round(result["cleaned_size"] / (1024**2), 2)
                self.log(
                    f"临时文件清理完成: 删除 {len(result['cleaned_files'])} 个项目，释放 {size_mb}MB"
                )
            else:
                self.log("没有需要清理的临时文件")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"临时文件清理失败: {e}", "ERROR")

        return result

    def backup_data(self, include_logs: bool = False) -> Dict[str, Any]:
        """备份数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"stock_rag_backup_{timestamp}"

        self.log(f"开始数据备份: {backup_name}")

        result = {
            "backup_file": None,
            "backup_size": 0,
            "included_items": [],
            "error": None,
        }

        try:
            backup_file = self.backup_dir / f"{backup_name}.tar.gz"

            with tarfile.open(backup_file, "w:gz") as tar:
                # 备份数据目录
                if self.data_dir.exists():
                    tar.add(self.data_dir, arcname="data")
                    result["included_items"].append("data/")

                # 备份配置文件
                config_files = [".env", "config_template.env", "requirements.txt"]
                for config_file in config_files:
                    file_path = self.project_root / config_file
                    if file_path.exists():
                        tar.add(file_path, arcname=config_file)
                        result["included_items"].append(config_file)

                # 备份日志（如果选择）
                if include_logs and self.logs_dir.exists():
                    tar.add(self.logs_dir, arcname="logs")
                    result["included_items"].append("logs/")

                # 备份重要脚本
                important_scripts = [
                    "start_system.py",
                    "system_monitor.py",
                    "validate_config.py",
                    "deploy_system.py",
                ]

                for script in important_scripts:
                    script_path = self.project_root / script
                    if script_path.exists():
                        tar.add(script_path, arcname=script)
                        result["included_items"].append(script)

            # 获取备份文件大小
            result["backup_file"] = str(backup_file)
            result["backup_size"] = backup_file.stat().st_size

            size_mb = round(result["backup_size"] / (1024**2), 2)
            self.log(f"备份完成: {backup_file.name} ({size_mb}MB)")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"数据备份失败: {e}", "ERROR")

        return result

    def restore_backup(self, backup_file: str) -> Dict[str, Any]:
        """恢复备份"""
        self.log(f"开始恢复备份: {backup_file}")

        result = {"restored_items": [], "error": None}

        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                # 尝试在备份目录中查找
                backup_path = self.backup_dir / backup_file

            if not backup_path.exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")

            # 创建恢复前的备份
            pre_restore_backup = self.backup_data(include_logs=True)
            if pre_restore_backup.get("backup_file"):
                self.log(f"恢复前备份已创建: {pre_restore_backup['backup_file']}")

            with tarfile.open(backup_path, "r:gz") as tar:
                # 获取备份内容
                members = tar.getnames()

                # 恢复数据
                tar.extractall(path=self.project_root)
                result["restored_items"] = members

            self.log(f"备份恢复完成: 恢复了 {len(result['restored_items'])} 个项目")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"备份恢复失败: {e}", "ERROR")

        return result

    def check_disk_space(self, warn_threshold: float = 80.0) -> Dict[str, Any]:
        """检查磁盘空间"""
        self.log("检查磁盘空间...")

        result = {"disk_usage": {}, "warnings": [], "recommendations": []}

        try:
            disk_usage = shutil.disk_usage(self.project_root)
            usage_percent = (disk_usage.used / disk_usage.total) * 100

            result["disk_usage"] = {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "usage_percent": round(usage_percent, 2),
            }

            if usage_percent > warn_threshold:
                warning = (
                    f"磁盘使用率超过阈值: {usage_percent:.1f}% > {warn_threshold}%"
                )
                result["warnings"].append(warning)
                self.log(warning, "WARNING")

                # 提供建议
                if usage_percent > 90:
                    result["recommendations"].extend(
                        [
                            "立即清理临时文件",
                            "删除旧的日志文件",
                            "压缩或删除旧的备份文件",
                            "考虑增加磁盘空间",
                        ]
                    )
                else:
                    result["recommendations"].extend(
                        [
                            "清理临时文件和日志",
                            "定期备份并删除旧数据",
                            "监控磁盘使用趋势",
                        ]
                    )
            else:
                self.log(f"磁盘空间充足: {usage_percent:.1f}%")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"磁盘空间检查失败: {e}", "ERROR")

        return result

    def optimize_databases(self) -> Dict[str, Any]:
        """优化数据库"""
        self.log("优化数据库...")

        result = {"optimized_items": [], "space_saved": 0, "error": None}

        try:
            # 清理重复的向量文件
            vector_dir = self.data_dir / "databases/vector_dbs"
            if vector_dir.exists():
                vector_files = list(vector_dir.glob("*.faiss"))

                # 按文件大小分组，查找可能的重复文件
                size_groups = {}
                for vf in vector_files:
                    size = vf.stat().st_size
                    if size not in size_groups:
                        size_groups[size] = []
                    size_groups[size].append(vf)

                for size, files in size_groups.items():
                    if len(files) > 1:
                        # 保留最新的，删除其他的
                        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        for duplicate in files[1:]:
                            result["space_saved"] += duplicate.stat().st_size
                            duplicate.unlink()
                            result["optimized_items"].append(
                                f"删除重复向量文件: {duplicate.name}"
                            )

            # 压缩旧的调试数据
            debug_dir = self.data_dir / "debug_data"
            if debug_dir.exists():
                old_files = []
                cutoff_time = time.time() - (7 * 24 * 3600)  # 7天前

                for debug_file in debug_dir.rglob("*.json"):
                    if debug_file.stat().st_mtime < cutoff_time:
                        old_files.append(debug_file)

                if old_files:
                    # 创建压缩文件
                    archive_name = (
                        debug_dir
                        / f"old_debug_data_{datetime.now().strftime('%Y%m%d')}.zip"
                    )

                    with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as zf:
                        for old_file in old_files:
                            zf.write(old_file, old_file.relative_to(debug_dir))
                            result["space_saved"] += old_file.stat().st_size
                            old_file.unlink()

                    result["optimized_items"].append(
                        f"压缩旧调试文件: {len(old_files)} 个文件 -> {archive_name.name}"
                    )

            if result["optimized_items"]:
                saved_mb = round(result["space_saved"] / (1024**2), 2)
                self.log(f"数据库优化完成: 节省空间 {saved_mb}MB")
            else:
                self.log("数据库无需优化")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"数据库优化失败: {e}", "ERROR")

        return result

    def generate_maintenance_report(self) -> Dict[str, Any]:
        """生成维护报告"""
        self.log("生成维护报告...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "system_status": self.get_system_status(),
            "maintenance_actions": [],
            "recommendations": [],
        }

        try:
            # 执行维护操作
            self.log("执行维护操作...")

            # 清理日志
            log_cleanup = self.clean_logs(keep_days=7)
            if log_cleanup.get("cleaned_files"):
                report["maintenance_actions"].append(
                    {"action": "日志清理", "result": log_cleanup}
                )

            # 清理临时文件
            temp_cleanup = self.clean_temp_files()
            if temp_cleanup.get("cleaned_files"):
                report["maintenance_actions"].append(
                    {"action": "临时文件清理", "result": temp_cleanup}
                )

            # 检查磁盘空间
            disk_check = self.check_disk_space()
            if disk_check.get("warnings"):
                report["maintenance_actions"].append(
                    {"action": "磁盘空间检查", "result": disk_check}
                )
                report["recommendations"].extend(disk_check.get("recommendations", []))

            # 优化数据库
            db_optimization = self.optimize_databases()
            if db_optimization.get("optimized_items"):
                report["maintenance_actions"].append(
                    {"action": "数据库优化", "result": db_optimization}
                )

            # 生成通用建议
            status = report["system_status"]
            if status.get("file_counts", {}).get("pdf_reports", 0) == 0:
                report["recommendations"].append("上传PDF报告文件以使用完整功能")

            if status.get("log_size", {}).get("total_mb", 0) > 100:
                report["recommendations"].append("日志文件较大，考虑更频繁的清理")

            # 保存报告
            report_file = (
                self.logs_dir
                / f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.log(f"维护报告已保存: {report_file}")

        except Exception as e:
            report["error"] = str(e)
            self.log(f"维护报告生成失败: {e}", "ERROR")

        return report


def main():
    """主函数"""
    maintainer = SystemMaintainer()

    if len(sys.argv) < 2:
        print("🔧 投研RAG系统维护工具")
        print("=" * 40)
        print("使用方法:")
        print("  python system_maintenance.py <command>")
        print()
        print("可用命令:")
        print("  status       - 查看系统状态")
        print("  clean-logs   - 清理日志文件")
        print("  clean-temp   - 清理临时文件")
        print("  backup       - 备份数据")
        print("  restore <file> - 恢复备份")
        print("  check-disk   - 检查磁盘空间")
        print("  optimize     - 优化数据库")
        print("  report       - 生成维护报告")
        print("  full         - 执行完整维护")
        return

    command = sys.argv[1].lower()

    if command == "status":
        status = maintainer.get_system_status()
        print("系统状态:")
        print(json.dumps(status, ensure_ascii=False, indent=2))

    elif command == "clean-logs":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        result = maintainer.clean_logs(keep_days=days)
        print(f"日志清理结果: {result}")

    elif command == "clean-temp":
        result = maintainer.clean_temp_files()
        print(f"临时文件清理结果: {result}")

    elif command == "backup":
        include_logs = "--include-logs" in sys.argv
        result = maintainer.backup_data(include_logs=include_logs)
        print(f"备份结果: {result}")

    elif command == "restore":
        if len(sys.argv) < 3:
            print("请提供备份文件路径")
            sys.exit(1)

        backup_file = sys.argv[2]
        result = maintainer.restore_backup(backup_file)
        print(f"恢复结果: {result}")

    elif command == "check-disk":
        threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 80.0
        result = maintainer.check_disk_space(warn_threshold=threshold)
        print(f"磁盘检查结果: {result}")

    elif command == "optimize":
        result = maintainer.optimize_databases()
        print(f"数据库优化结果: {result}")

    elif command == "report":
        report = maintainer.generate_maintenance_report()
        print("维护报告已生成")

    elif command == "full":
        print("🔧 执行完整系统维护...")
        report = maintainer.generate_maintenance_report()

        print("\n📊 维护摘要:")
        if report.get("maintenance_actions"):
            for action in report["maintenance_actions"]:
                print(f"  ✅ {action['action']}")

        if report.get("recommendations"):
            print("\n💡 建议:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")

        print("\n✅ 完整维护完成")

    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
