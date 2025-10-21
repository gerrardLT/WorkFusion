#!/usr/bin/env python
"""
系统状态监控脚本
监控前后端服务状态、数据库连接、API响应等
"""

import sys
import time
import requests
import psutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.monitoring = False

    def check_service_health(
        self, name: str, url: str, timeout: int = 5
    ) -> Dict[str, Any]:
        """检查服务健康状态"""
        try:
            start_time = time.time()
            response = requests.get(
                f"{url}/health" if "backend" in name.lower() else url, timeout=timeout
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return {
                    "name": name,
                    "status": "healthy",
                    "response_time": round(response_time * 1000, 2),  # ms
                    "status_code": response.status_code,
                    "url": url,
                }
            else:
                return {
                    "name": name,
                    "status": "unhealthy",
                    "response_time": round(response_time * 1000, 2),
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}",
                    "url": url,
                }

        except requests.exceptions.ConnectionError:
            return {
                "name": name,
                "status": "offline",
                "response_time": 0,
                "error": "Connection refused",
                "url": url,
            }
        except requests.exceptions.Timeout:
            return {
                "name": name,
                "status": "timeout",
                "response_time": timeout * 1000,
                "error": "Request timeout",
                "url": url,
            }
        except Exception as e:
            return {
                "name": name,
                "status": "error",
                "response_time": 0,
                "error": str(e),
                "url": url,
            }

    def check_backend_api(self) -> Dict[str, Any]:
        """检查后端API详细状态"""
        try:
            # 检查系统状态端点
            response = requests.get(f"{self.backend_url}/status", timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "api_status": "healthy",
                    "system_ready": data.get("is_ready", False),
                    "databases_loaded": data.get("databases_loaded", False),
                    "uptime": data.get("uptime", 0),
                    "statistics": data.get("statistics", {}),
                    "config": data.get("config", {}),
                }
            else:
                return {
                    "api_status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                }

        except Exception as e:
            return {"api_status": "error", "error": str(e)}

    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()

            # 磁盘使用情况
            disk = psutil.disk_usage(".")

            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": round(memory.total / (1024**3), 2),  # GB
                    "used": round(memory.used / (1024**3), 2),
                    "available": round(memory.available / (1024**3), 2),
                    "percent": memory.percent,
                },
                "disk": {
                    "total": round(disk.total / (1024**3), 2),  # GB
                    "used": round(disk.used / (1024**3), 2),
                    "free": round(disk.free / (1024**3), 2),
                    "percent": round((disk.used / disk.total) * 100, 2),
                },
            }

        except Exception as e:
            return {"error": str(e)}

    def check_data_files(self) -> Dict[str, Any]:
        """检查数据文件状态"""
        try:
            data_dir = Path("data/stock_data")

            result = {
                "data_directory_exists": data_dir.exists(),
                "pdf_reports": 0,
                "parsed_files": 0,
                "vector_files": 0,
                "bm25_files": 0,
            }

            if data_dir.exists():
                # PDF报告文件
                pdf_dir = data_dir / "pdf_reports"
                if pdf_dir.exists():
                    result["pdf_reports"] = len(list(pdf_dir.glob("*.pdf")))

                # 解析文件
                debug_dir = data_dir / "debug_data" / "parsed_reports"
                if debug_dir.exists():
                    result["parsed_files"] = len(list(debug_dir.glob("*_parsed.json")))

                # 向量文件
                vector_dir = data_dir / "databases" / "vector_dbs"
                if vector_dir.exists():
                    result["vector_files"] = len(list(vector_dir.glob("*.faiss")))

                # BM25文件
                bm25_dir = data_dir / "databases" / "bm25"
                if bm25_dir.exists():
                    result["bm25_files"] = len(list(bm25_dir.glob("*.pkl")))

            return result

        except Exception as e:
            return {"error": str(e)}

    def get_process_info(self) -> List[Dict[str, Any]]:
        """获取相关进程信息"""
        try:
            processes = []

            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_percent"]
            ):
                try:
                    cmdline = (
                        " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""
                    )

                    # 查找相关进程
                    if any(
                        keyword in cmdline.lower()
                        for keyword in ["uvicorn", "fastapi", "python", "stock-rag"]
                    ):
                        if (
                            "backend" in cmdline
                            or "main.py" in cmdline
                            or "run_backend" in cmdline
                        ):
                            processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": "Backend Service",
                                    "cmdline": (
                                        cmdline[:100] + "..."
                                        if len(cmdline) > 100
                                        else cmdline
                                    ),
                                    "cpu_percent": proc.info["cpu_percent"] or 0,
                                    "memory_percent": round(
                                        proc.info["memory_percent"] or 0, 2
                                    ),
                                }
                            )
                        elif "frontend" in cmdline or "run_frontend" in cmdline:
                            processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": "Frontend Service",
                                    "cmdline": (
                                        cmdline[:100] + "..."
                                        if len(cmdline) > 100
                                        else cmdline
                                    ),
                                    "cpu_percent": proc.info["cpu_percent"] or 0,
                                    "memory_percent": round(
                                        proc.info["memory_percent"] or 0, 2
                                    ),
                                }
                            )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return processes

        except Exception as e:
            return [{"error": str(e)}]

    def run_health_check(self) -> Dict[str, Any]:
        """运行完整的健康检查"""
        print("🏥 运行系统健康检查...")

        health_report = {
            "timestamp": datetime.now().isoformat(),
            "services": [],
            "backend_details": {},
            "system_resources": {},
            "data_files": {},
            "processes": [],
            "overall_status": "unknown",
        }

        # 1. 检查服务状态
        print("   📡 检查服务连接...")
        services = [
            ("Backend API", self.backend_url),
            ("Frontend Web", self.frontend_url),
        ]

        for name, url in services:
            service_health = self.check_service_health(name, url)
            health_report["services"].append(service_health)

            status_icon = {
                "healthy": "✅",
                "unhealthy": "⚠️",
                "offline": "❌",
                "timeout": "⏱️",
                "error": "💥",
            }.get(service_health["status"], "❓")

            print(f"      {status_icon} {name}: {service_health['status']}")
            if "response_time" in service_health:
                print(f"         响应时间: {service_health['response_time']}ms")

        # 2. 检查后端API详情
        print("   🔍 检查后端API详情...")
        backend_details = self.check_backend_api()
        health_report["backend_details"] = backend_details

        if backend_details.get("api_status") == "healthy":
            print(f"      ✅ API状态: 正常")
            print(f"      🔗 系统就绪: {backend_details.get('system_ready')}")
            print(f"      💾 数据库加载: {backend_details.get('databases_loaded')}")
            if backend_details.get("uptime"):
                print(f"      ⏰ 运行时间: {backend_details['uptime']:.1f}秒")
        else:
            print(f"      ❌ API状态: {backend_details.get('error', '异常')}")

        # 3. 检查系统资源
        print("   💻 检查系统资源...")
        resources = self.check_system_resources()
        health_report["system_resources"] = resources

        if "error" not in resources:
            print(f"      🖥️  CPU使用率: {resources['cpu_percent']}%")
            print(
                f"      💾 内存使用: {resources['memory']['used']}GB / {resources['memory']['total']}GB ({resources['memory']['percent']}%)"
            )
            print(
                f"      💿 磁盘使用: {resources['disk']['used']}GB / {resources['disk']['total']}GB ({resources['disk']['percent']}%)"
            )
        else:
            print(f"      ❌ 资源检查失败: {resources['error']}")

        # 4. 检查数据文件
        print("   📂 检查数据文件...")
        data_files = self.check_data_files()
        health_report["data_files"] = data_files

        if "error" not in data_files:
            print(f"      📄 PDF报告: {data_files['pdf_reports']} 个")
            print(f"      🔍 已解析: {data_files['parsed_files']} 个")
            print(f"      📊 向量文件: {data_files['vector_files']} 个")
            print(f"      🔍 BM25文件: {data_files['bm25_files']} 个")
        else:
            print(f"      ❌ 数据检查失败: {data_files['error']}")

        # 5. 检查进程信息
        print("   🔄 检查运行进程...")
        processes = self.get_process_info()
        health_report["processes"] = processes

        for proc in processes:
            if "error" not in proc:
                print(f"      🔹 {proc['name']} (PID: {proc['pid']})")
                print(
                    f"         CPU: {proc['cpu_percent']}%, 内存: {proc['memory_percent']}%"
                )

        # 6. 评估整体状态
        healthy_services = sum(
            1 for s in health_report["services"] if s["status"] == "healthy"
        )
        total_services = len(health_report["services"])

        if healthy_services == total_services:
            health_report["overall_status"] = "healthy"
        elif healthy_services > 0:
            health_report["overall_status"] = "partial"
        else:
            health_report["overall_status"] = "unhealthy"

        return health_report

    def save_health_report(self, report: Dict[str, Any], filename: str = None):
        """保存健康检查报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"

        try:
            reports_dir = Path("logs")
            reports_dir.mkdir(exist_ok=True)

            report_file = reports_dir / filename
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"📄 健康报告已保存: {report_file}")
            return str(report_file)

        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return None

    def continuous_monitor(self, interval: int = 30):
        """持续监控模式"""
        print(f"🔄 开始持续监控 (间隔: {interval}秒)")
        print("按 Ctrl+C 停止监控\n")

        self.monitoring = True

        try:
            while self.monitoring:
                report = self.run_health_check()

                # 显示简要状态
                overall_status = report["overall_status"]
                status_icon = {"healthy": "🟢", "partial": "🟡", "unhealthy": "🔴"}.get(
                    overall_status, "⚪"
                )

                print(f"\n{status_icon} 整体状态: {overall_status.upper()}")
                print(f"⏰ 检查时间: {report['timestamp']}")
                print("-" * 40)

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n👋 停止监控")
            self.monitoring = False


def main():
    """主函数"""
    monitor = SystemMonitor()

    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # 持续监控模式
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        monitor.continuous_monitor(interval)
    else:
        # 单次健康检查
        print("🏥 投研RAG系统健康检查")
        print("=" * 50)

        report = monitor.run_health_check()

        # 保存报告
        report_file = monitor.save_health_report(report)

        # 显示总结
        print("\n" + "=" * 50)
        overall_status = report["overall_status"]
        status_icon = {"healthy": "🟢", "partial": "🟡", "unhealthy": "🔴"}.get(
            overall_status, "⚪"
        )

        print(f"{status_icon} 整体系统状态: {overall_status.upper()}")

        if overall_status == "healthy":
            print("✅ 系统运行正常，所有服务健康")
        elif overall_status == "partial":
            print("⚠️  系统部分正常，请检查失败的服务")
        else:
            print("❌ 系统异常，请检查服务状态")

        print("=" * 50)


if __name__ == "__main__":
    main()
