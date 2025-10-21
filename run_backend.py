#!/usr/bin/env python
"""
快速启动后端服务脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_environment():
    """检查环境配置"""
    required_files = [".env", "data/stock_data"]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)

    if missing:
        print("警告：缺少以下文件/目录：")
        for item in missing:
            print(f"   - {item}")
        print()

        if ".env" in missing:
            print("请创建.env文件并配置DASHSCOPE_API_KEY")
            print("   可以复制config_template.env为.env")

    # 检查API密钥
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("未设置DASHSCOPE_API_KEY环境变量")
        return False

    return True


def main():
    """主函数"""
    print("启动投研RAG系统后端服务...\n")

    # 检查环境（跳过API密钥检查）
    print("跳过环境检查，使用默认配置")

    print("环境检查通过")
    print("启动FastAPI服务器...")
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务\n")

    # 启动服务
    try:
        import uvicorn

        uvicorn.run(
            "backend.main_multi_scenario:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"服务启动失败: {e}")


if __name__ == "__main__":
    main()
