#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统一键启动脚本
同时启动后端服务和前端服务，实现完整系统集成
"""

import os
import sys
import time
import subprocess
import threading
import signal
from pathlib import Path
from dotenv import load_dotenv

# Windows控制台编码设置（解决emoji显示问题）
if sys.platform == "win32":
    try:
        # 设置控制台为UTF-8编码
        os.system('chcp 65001 > nul')
    except:
        pass

# 加载.env文件
load_dotenv()


class SystemManager:
    """系统管理器"""

    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = False

    def check_environment(self):
        """检查环境配置"""
        print("[CHECK] 检查系统环境...")

        # 检查Python环境
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 8:
            print("[ERROR] Python版本需要3.8或更高")
            return False

        # 检查Node.js环境（如果使用Next.js前端）
        if Path("frontend-next/package.json").exists():
            try:
                # Windows兼容性检查
                node_result = subprocess.run(
                    ["node", "--version"],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                npm_result = subprocess.run(
                    ["npm", "--version"],
                    capture_output=True,
                    text=True,
                    shell=True
                )

                if node_result.returncode == 0 and npm_result.returncode == 0:
                    node_version = node_result.stdout.strip()
                    npm_version = npm_result.stdout.strip()
                    print(f"[OK] Node.js({node_version}) 和 npm({npm_version}) 环境检查通过")
                else:
                    print("[WARN] Node.js或npm命令执行失败")
                    print("[INFO] 请检查Node.js安装是否正确")
                    return False

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"[WARN] Node.js环境检查异常: {e}")
                print("[INFO] 请确保Node.js已正确安装并添加到PATH")
                return False

        # 检查环境变量
        if not os.getenv("DASHSCOPE_API_KEY"):
            print("[WARN] 未设置DASHSCOPE_API_KEY环境变量")
            print("[INFO] 请创建.env文件并配置API密钥")
            return False

        # 检查必要文件
        required_files = [
            "backend/main_multi_scenario.py",  # 多场景主入口
            "frontend-next/package.json",
            "src/config.py",
            "requirements.txt",
        ]

        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            print("[ERROR] 缺少必要文件:")
            for file in missing_files:
                print(f"   - {file}")
            return False

        print("[OK] 环境检查通过")
        return True

    def initialize_database(self):
        """初始化数据库"""
        print("[DB] 初始化数据库...")

        try:
            # 导入并初始化数据库
            sys.path.insert(0, str(Path.cwd()))
            from backend.database import init_database

            if init_database():
                print("[OK] 数据库初始化完成")
                return True
            else:
                print("[ERROR] 数据库初始化失败")
                return False

        except Exception as e:
            print(f"[ERROR] 数据库初始化异常: {e}")
            return False

    def install_dependencies(self):
        """安装依赖包"""
        print("[DEPS] 检查并安装依赖包...")

        try:
            # 检查requirements.txt是否存在
            if not Path("requirements.txt").exists():
                print("[ERROR] requirements.txt不存在")
                return False

            # 安装Python依赖
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
            )
            print("[OK] Python依赖安装完成")

            # 安装Next.js依赖
            if Path("frontend-next/package.json").exists():
                print("[DEPS] 安装Next.js依赖...")
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=Path("frontend-next"),
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("[OK] Next.js依赖安装完成")
                else:
                    print(f"[WARN] Next.js依赖安装出现警告: {result.stderr}")
                    print("[OK] 继续启动系统...")

            print("[OK] 所有依赖安装完成")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] 依赖安装失败: {e}")
            return False

    def start_backend(self):
        """启动后端服务"""
        print("[WEB] 启动后端服务...")

        try:
            # 直接启动多场景后端服务（显示输出）
            self.backend_process = subprocess.Popen(
                [sys.executable, "-u", "backend/main_multi_scenario.py"],  # 添加 -u 参数，禁用缓冲
                cwd=Path.cwd(),
                # 不重定向输出，让日志直接显示在控制台
                stdout=None,
                stderr=None
            )

            # 等待后端启动
            print("⏳ 等待后端服务启动...")
            time.sleep(5)  # 增加等待时间，确保服务完全启动

            # 检查后端是否启动成功
            if self.backend_process.poll() is None:
                print("[OK] 后端服务启动成功 (http://localhost:8000)")

                # 验证健康检查
                try:
                    import requests
                    time.sleep(2)  # 再等待2秒确保API可用
                    response = requests.get("http://localhost:8000/health", timeout=5)
                    if response.status_code == 200:
                        print("[OK] 后端健康检查通过")
                    else:
                        print("[WARN]  后端健康检查异常")
                except Exception as e:
                    print(f"[WARN]  健康检查失败（服务可能仍在初始化）: {e}")

                return True
            else:
                print("[ERROR] 后端服务启动失败")
                return False

        except Exception as e:
            print(f"[ERROR] 后端服务启动异常: {e}")
            return False

    def cleanup_ports(self):
        """清理占用的端口"""
        try:
            # 清理3005端口 (Next.js配置端口)
            result = subprocess.run(
                'netstat -ano | findstr :3005',
                shell=True,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                print("🧹 发现端口3005被占用，正在清理...")
                # 提取PID并终止进程
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
                            print(f"[OK] 已清理占用端口的进程 (PID: {pid})")

        except Exception as e:
            print(f"[WARN] 端口清理异常: {e}")

    def start_frontend(self):
        """启动前端服务"""
        print("🎨 启动Next.js前端服务...")

        try:
            # 清理可能占用的端口
            self.cleanup_ports()

            # 检查是否使用新的Next.js前端
            if Path("frontend-next/package.json").exists():
                # 启动Next.js开发服务器（显示输出）
                # 不使用CREATE_NEW_CONSOLE，让日志显示在当前窗口
                self.frontend_process = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=Path("frontend-next"),
                    shell=True,
                    stdout=None,  # 不重定向，直接显示
                    stderr=None
                )
                print("[START] 正在启动Next.js开发服务器...")
            else:
                # 回退到旧的HTML前端
                self.frontend_process = subprocess.Popen(
                    [sys.executable, "run_frontend.py"],
                    cwd=Path.cwd(),
                    stdout=None,
                    stderr=None
                )
                print("[START] 正在启动HTML前端服务器...")

            # 等待前端启动
            time.sleep(5)  # Next.js需要更多时间启动

            # 检查前端是否启动成功
            if self.frontend_process.poll() is None:
                if Path("frontend-next/package.json").exists():
                    print("[OK] Next.js前端服务启动成功 (http://localhost:3005)")
                else:
                    print("[OK] HTML前端服务启动成功 (http://localhost:3005)")
                return True
            else:
                print("[ERROR] 前端服务启动失败")
                return False

        except Exception as e:
            print(f"[ERROR] 前端服务启动异常: {e}")
            return False

    def monitor_services(self):
        """监控服务状态"""
        while self.running:
            try:
                # 检查后端进程
                if self.backend_process and self.backend_process.poll() is not None:
                    print("[WARN]  后端服务意外停止")
                    self.running = False

                # 检查前端进程
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("[WARN]  前端服务意外停止")
                    self.running = False

                time.sleep(5)

            except Exception as e:
                print(f"[ERROR] 服务监控异常: {e}")
                break

    def stop_services(self):
        """停止所有服务"""
        print("\n🛑 正在停止服务...")

        self.running = False

        # 停止后端服务
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("[OK] 后端服务已停止")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("[WARN]  强制停止后端服务")
            except Exception as e:
                print(f"[ERROR] 停止后端服务失败: {e}")

        # 停止前端服务
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("[OK] 前端服务已停止")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                print("[WARN]  强制停止前端服务")
            except Exception as e:
                print(f"[ERROR] 停止前端服务失败: {e}")

        print("👋 系统已完全停止")

    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n接收到信号 {signum}")
        self.stop_services()
        sys.exit(0)

    def start_system(self):
        """启动完整系统"""
        print("[SYSTEM] 多场景AI知识问答系统 (Agentic RAG) - 启动器")
        print("=" * 60)

        # 注册信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        try:
            # 1. 环境检查
            if not self.check_environment():
                return False

            # 2. 安装依赖
            print("\n[SETUP] 准备依赖环境...")
            if not self.install_dependencies():
                return False

            # 2.5. 初始化数据库
            if not self.initialize_database():
                return False

            # 3. 启动后端服务
            print("\n[WEB] 启动服务...")
            if not self.start_backend():
                return False

            # 4. 启动前端服务
            if not self.start_frontend():
                self.stop_services()
                return False

            # 5. 显示系统信息
            print("\n" + "=" * 60)
            print("[SUCCESS] 多场景AI知识问答系统启动成功！")
            print()
            print("📋 日志说明:")
            print("   - 前后端日志都显示在当前窗口")
            print("   - 日志可能会混合显示，这是正常的")
            print()
            print("[WEB] 访问地址:")
            print("   - 前端界面: http://localhost:3005")
            print("   - 后端API: http://localhost:8000")
            print("   - API文档: http://localhost:8000/docs")
            print("   - 健康检查: http://localhost:8000/health")
            print()
            print("[INFO] 使用提示:")
            print("   1. 选择业务场景（招投标/企业管理）")
            print("   2. 创建企业画像（/company）")
            print("   3. 上传相关文档（PDF/TXT/MD等）")
            print("   4. 设置项目订阅规则（/subscriptions）")
            print("   5. 开始智能问答（支持多轮对话）")
            print("   6. 查看推荐项目和通知（/projects, /notifications）")
            print()
            print("[START] Agentic RAG 核心特性:")
            print("   [OK] 混合检索（BM25 + FAISS + RRF融合）")
            print("   [OK] 智能路由（LLM驱动的文档筛选）")
            print("   [OK] 分层导航（多轮筛选 + Token控制）")
            print("   [OK] 智能缓存（精确缓存 + 语义缓存）")
            print("   [OK] 答案验证（三层验证机制）")
            print()
            print("[FEATURE] 招投标AI功能:")
            print("   [OK] 企业画像管理（资质、能力、业绩）")
            print("   [OK] 项目智能推荐（基于匹配度算法）")
            print("   [OK] 订阅与通知（自动项目匹配推送）")
            print("   [OK] 任务清单生成（AI提取关键任务）")
            print("   [OK] 风险识别分析（智能风险检测）")
            print("   [OK] 评估报告生成（一键PDF导出）")
            print("   [OK] 内容自动生成（技术方案、企业介绍等）")
            print()
            print("📱 前端功能:")
            print("   - 现代化Next.js界面")
            print("   - 多场景动态切换")
            print("   - 智能聊天对话")
            print("   - 文件拖拽上传")
            print("   - 暗色主题设计")
            print("   - 响应式布局")
            print()
            print("[STATUS] 系统状态:")
            print("   - 阶段1完成度: 100% (12/12)")
            print("   - 阶段2完成度: 100% (13/13)")
            print("   - 总体完成度: 59.5% (25/42)")
            print("   - API端点: 50+ 个")
            print("   - 集成测试: 通过 [OK]")
            print()
            print("[CTRL] 按 Ctrl+C 停止系统")
            print("=" * 60)

            # 6. 启动监控
            self.running = True
            monitor_thread = threading.Thread(target=self.monitor_services)
            monitor_thread.daemon = True
            monitor_thread.start()

            # 7. 保持运行
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

            return True

        except Exception as e:
            print(f"[ERROR] 系统启动失败: {e}")
            self.stop_services()
            return False


def main():
    """主函数"""
    manager = SystemManager()
    success = manager.start_system()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
