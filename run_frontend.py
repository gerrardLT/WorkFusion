#!/usr/bin/env python
"""
前端开发服务器启动脚本
提供简单的HTTP服务器来运行前端页面
"""

import os
import sys
import webbrowser
import threading
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import TCPServer


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, directory=str(Path(__file__).parent / "frontend"), **kwargs
        )

    def end_headers(self):
        # 添加CORS头以支持跨域请求
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        # 处理OPTIONS请求（CORS预检）
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # 自定义日志格式
        print(f"[{self.log_date_time_string()}] {format % args}")


def find_free_port(start_port=3005):
    """查找可用的端口"""
    import socket

    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue

    raise RuntimeError("无法找到可用端口")


def check_backend_status():
    """检查后端服务状态"""
    import urllib.request

    try:
        with urllib.request.urlopen(
            "http://localhost:8000/health", timeout=5
        ) as response:
            return response.getcode() == 200
    except:
        return False


def start_server(port=3005):
    """启动HTTP服务器"""
    try:
        # 查找可用端口
        actual_port = find_free_port(port)

        # 创建服务器
        httpd = HTTPServer(("localhost", actual_port), CustomHTTPRequestHandler)

        print(f"🌐 前端服务器启动成功")
        print(f"📍 访问地址: http://localhost:{actual_port}")
        print(f"📁 服务目录: {Path(__file__).parent / 'frontend'}")

        # 检查后端状态
        if check_backend_status():
            print("✅ 后端服务运行正常")
        else:
            print("⚠️  后端服务未运行，部分功能可能不可用")
            print("💡 请先启动后端服务: python run_backend.py")

        print(f"🔧 按 Ctrl+C 停止服务\n")

        # 延迟打开浏览器
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(f"http://localhost:{actual_port}")

        threading.Thread(target=open_browser, daemon=True).start()

        # 启动服务器
        httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n👋 前端服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")


def main():
    """主函数"""
    print("🎨 投研RAG系统 - 前端开发服务器")
    print("=" * 40)

    # 检查前端文件是否存在
    frontend_dir = Path(__file__).parent / "frontend"
    index_file = frontend_dir / "index.html"

    if not index_file.exists():
        print("❌ 前端文件不存在: frontend/index.html")
        return

    print(f"📁 前端文件检查通过: {frontend_dir}")
    print()

    # 解析命令行参数
    port = 3005
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("⚠️  无效的端口号，使用默认端口 3005")

    # 启动服务器
    start_server(port)


if __name__ == "__main__":
    main()
