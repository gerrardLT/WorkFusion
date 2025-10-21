#!/usr/bin/env python
"""
系统自动部署脚本
自动化部署投研RAG智能问答系统
"""

import os
import sys
import subprocess
import shutil
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional


class SystemDeployer:
    """系统部署器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)

        # 写入日志文件
        log_file = self.logs_dir / "deploy.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")

    def check_prerequisites(self) -> bool:
        """检查先决条件"""
        self.log("检查部署先决条件...")

        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 8:
            self.log(
                f"Python版本不符合要求: {python_version.major}.{python_version.minor}",
                "ERROR",
            )
            return False

        self.log(
            f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )

        # 检查git
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            self.log("Git可用")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("Git不可用，部分功能可能受限", "WARNING")

        # 检查pip
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                check=True,
                capture_output=True,
            )
            self.log("Pip可用")
        except subprocess.CalledProcessError:
            self.log("Pip不可用", "ERROR")
            return False

        return True

    def setup_environment(self) -> bool:
        """设置环境"""
        self.log("设置部署环境...")

        try:
            # 创建必要目录
            directories = [
                "data/stock_data/pdf_reports",
                "data/stock_data/databases/vector_dbs",
                "data/stock_data/databases/bm25",
                "data/stock_data/debug_data/parsed_reports",
                "logs",
                "docs",
            ]

            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log(f"创建目录: {directory}")

            # 复制环境配置模板
            env_template = self.project_root / "config_template.env"
            env_file = self.project_root / ".env"

            if env_template.exists() and not env_file.exists():
                shutil.copy2(env_template, env_file)
                self.log("复制环境配置模板到.env")
                self.log("请编辑.env文件并设置您的DASHSCOPE_API_KEY", "WARNING")

            return True

        except Exception as e:
            self.log(f"环境设置失败: {e}", "ERROR")
            return False

    def install_dependencies(self) -> bool:
        """安装依赖"""
        self.log("安装项目依赖...")

        try:
            # 升级pip
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
            )

            # 安装requirements.txt中的依赖
            if Path("requirements.txt").exists():
                self.log("从requirements.txt安装依赖...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    self.log(f"依赖安装失败: {result.stderr}", "ERROR")
                    return False

                self.log("依赖安装完成")
            else:
                self.log("未找到requirements.txt文件", "WARNING")

            return True

        except Exception as e:
            self.log(f"依赖安装异常: {e}", "ERROR")
            return False

    def validate_configuration(self) -> bool:
        """验证配置"""
        self.log("验证系统配置...")

        try:
            # 运行配置验证脚本
            validate_script = self.project_root / "validate_config.py"

            if validate_script.exists():
                result = subprocess.run(
                    [sys.executable, str(validate_script)],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    self.log("配置验证通过")
                    return True
                else:
                    self.log("配置验证失败", "ERROR")
                    self.log(result.stdout, "ERROR")
                    return False
            else:
                self.log("配置验证脚本不存在，跳过验证", "WARNING")
                return True

        except Exception as e:
            self.log(f"配置验证异常: {e}", "ERROR")
            return False

    def prepare_sample_data(self) -> bool:
        """准备示例数据"""
        self.log("准备示例数据...")

        try:
            data_dir = self.project_root / "data/stock_data"

            # 创建示例questions.json
            questions_file = data_dir / "questions.json"
            if not questions_file.exists():
                sample_questions = [
                    {
                        "question_id": "sample_001",
                        "question_text": "什么是价值投资策略？",
                        "question_type": "string",
                        "target_companies": [],
                        "category": "投资理论",
                    },
                    {
                        "question_id": "sample_002",
                        "question_text": "中芯国际的主要业务领域有哪些？",
                        "question_type": "string",
                        "target_companies": ["中芯国际"],
                        "category": "公司业务",
                    },
                    {
                        "question_id": "sample_003",
                        "question_text": "如何分析一家公司的财务健康状况？",
                        "question_type": "string",
                        "target_companies": [],
                        "category": "财务分析",
                    },
                ]

                with open(questions_file, "w", encoding="utf-8") as f:
                    json.dump(sample_questions, f, ensure_ascii=False, indent=2)

                self.log("创建示例questions.json")

            # 创建示例subset.csv
            subset_file = data_dir / "subset.csv"
            if not subset_file.exists():
                sample_csv = """report_id,company_name,report_type,file_path,status
sample_001,示例公司,研究报告,sample_report.pdf,active"""

                with open(subset_file, "w", encoding="utf-8") as f:
                    f.write(sample_csv)

                self.log("创建示例subset.csv")

            return True

        except Exception as e:
            self.log(f"示例数据准备失败: {e}", "ERROR")
            return False

    def setup_git_hooks(self) -> bool:
        """设置Git钩子"""
        self.log("设置Git钩子...")

        try:
            git_dir = self.project_root / ".git"
            if not git_dir.exists():
                self.log("不是Git仓库，跳过Git钩子设置", "WARNING")
                return True

            # 检查pre-commit是否可用
            try:
                subprocess.run(
                    ["pre-commit", "--version"], check=True, capture_output=True
                )

                # 安装pre-commit钩子
                subprocess.run(
                    ["pre-commit", "install"], check=True, capture_output=True
                )
                self.log("Pre-commit钩子安装成功")

            except (subprocess.CalledProcessError, FileNotFoundError):
                self.log("Pre-commit不可用，跳过钩子安装", "WARNING")

            return True

        except Exception as e:
            self.log(f"Git钩子设置失败: {e}", "ERROR")
            return False

    def run_initial_tests(self) -> bool:
        """运行初始测试"""
        self.log("运行初始测试...")

        try:
            # 检查API连接
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key or "your_" in api_key.lower():
                self.log("DASHSCOPE_API_KEY未正确设置，跳过API测试", "WARNING")
                return True

            # 运行系统测试
            test_scripts = [
                "test_dashscope_integration.py",
                "test_backend_api.py",  # 这个可能需要服务运行
            ]

            for test_script in test_scripts:
                script_path = self.project_root / test_script
                if script_path.exists():
                    self.log(f"运行测试: {test_script}")

                    result = subprocess.run(
                        [sys.executable, str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )

                    if result.returncode == 0:
                        self.log(f"测试 {test_script} 通过")
                    else:
                        self.log(f"测试 {test_script} 失败: {result.stderr}", "WARNING")
                        # 不让测试失败阻止部署
                else:
                    self.log(f"测试脚本 {test_script} 不存在", "WARNING")

            return True

        except Exception as e:
            self.log(f"初始测试异常: {e}", "WARNING")
            return True  # 测试失败不阻止部署

    def generate_startup_scripts(self) -> bool:
        """生成启动脚本"""
        self.log("生成启动脚本...")

        try:
            # Linux/Mac启动脚本
            if os.name == "posix":
                startup_script = self.project_root / "start.sh"
                script_content = """#!/bin/bash

echo "🚀 启动投研RAG智能问答系统..."

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 验证配置
echo "验证配置..."
python validate_config.py
if [ $? -ne 0 ]; then
    echo "❌ 配置验证失败"
    exit 1
fi

# 启动系统
echo "启动系统..."
python start_system.py

echo "系统已停止"
"""

                with open(startup_script, "w", encoding="utf-8") as f:
                    f.write(script_content)

                # 设置执行权限
                startup_script.chmod(0o755)
                self.log("创建Linux/Mac启动脚本: start.sh")

            # Windows启动脚本
            if os.name == "nt":
                startup_script = self.project_root / "start.bat"
                script_content = """@echo off

echo 🚀 启动投研RAG智能问答系统...

REM 检查虚拟环境
if exist "venv" (
    echo 激活虚拟环境...
    call venv\\Scripts\\activate.bat
)

REM 验证配置
echo 验证配置...
python validate_config.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 配置验证失败
    exit /b 1
)

REM 启动系统
echo 启动系统...
python start_system.py

echo 系统已停止
pause
"""

                with open(startup_script, "w", encoding="utf-8") as f:
                    f.write(script_content)

                self.log("创建Windows启动脚本: start.bat")

            return True

        except Exception as e:
            self.log(f"启动脚本生成失败: {e}", "ERROR")
            return False

    def create_deployment_summary(self) -> Dict[str, Any]:
        """创建部署摘要"""
        summary = {
            "deployment_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": os.name,
            "next_steps": [],
        }

        # 添加后续步骤
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key or "your_" in api_key.lower():
            summary["next_steps"].append("设置DASHSCOPE_API_KEY环境变量")

        pdf_dir = self.project_root / "data/stock_data/pdf_reports"
        if not any(pdf_dir.glob("*.pdf")):
            summary["next_steps"].append(
                "上传投研报告PDF文件到data/stock_data/pdf_reports/"
            )

        summary["next_steps"].extend(
            [
                "运行系统: python start_system.py",
                "访问前端: http://localhost:3000",
                "查看API文档: http://localhost:8000/docs",
            ]
        )

        return summary

    def deploy(self) -> bool:
        """执行完整部署"""
        self.log("开始系统部署...")
        self.log("=" * 50)

        deployment_steps = [
            ("检查先决条件", self.check_prerequisites),
            ("设置环境", self.setup_environment),
            ("安装依赖", self.install_dependencies),
            ("验证配置", self.validate_configuration),
            ("准备示例数据", self.prepare_sample_data),
            ("设置Git钩子", self.setup_git_hooks),
            ("运行初始测试", self.run_initial_tests),
            ("生成启动脚本", self.generate_startup_scripts),
        ]

        failed_steps = []

        for step_name, step_func in deployment_steps:
            self.log(f"执行步骤: {step_name}")

            try:
                success = step_func()
                if success:
                    self.log(f"✅ {step_name} 完成")
                else:
                    self.log(f"❌ {step_name} 失败", "ERROR")
                    failed_steps.append(step_name)
            except Exception as e:
                self.log(f"💥 {step_name} 异常: {e}", "ERROR")
                failed_steps.append(step_name)

            self.log("-" * 30)

        # 创建部署摘要
        summary = self.create_deployment_summary()
        summary["failed_steps"] = failed_steps
        summary["success"] = len(failed_steps) == 0

        # 保存部署摘要
        summary_file = self.logs_dir / "deployment_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # 显示部署结果
        self.log("=" * 50)
        if len(failed_steps) == 0:
            self.log("🎉 部署成功完成！")
        else:
            self.log(f"⚠️  部署完成，但有 {len(failed_steps)} 个步骤失败")
            for step in failed_steps:
                self.log(f"   - {step}")

        self.log("📄 部署摘要已保存到: logs/deployment_summary.json")

        # 显示后续步骤
        if summary["next_steps"]:
            self.log("\n💡 后续步骤:")
            for step in summary["next_steps"]:
                self.log(f"   {step}")

        self.log("=" * 50)

        return len(failed_steps) == 0


def main():
    """主函数"""
    print("🚀 投研RAG智能问答系统 - 自动部署器")
    print("=" * 60)

    deployer = SystemDeployer()
    success = deployer.deploy()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
