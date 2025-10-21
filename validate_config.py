#!/usr/bin/env python
"""
系统配置验证脚本
验证环境变量、API密钥、文件权限等配置是否正确
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.config import get_settings, validate_dashscope_setup
    from src.dashscope_client import DashScopeClient
except ImportError as e:
    print(f"❌ 导入配置模块失败: {e}")
    sys.exit(1)


class ConfigValidator:
    """配置验证器"""

    def __init__(self):
        self.issues = []
        self.warnings = []

    def add_issue(self, message: str):
        """添加问题"""
        self.issues.append(message)

    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)

    def validate_environment_variables(self) -> bool:
        """验证环境变量"""
        print("🔧 验证环境变量...")

        required_vars = ["DASHSCOPE_API_KEY"]

        optional_vars = ["LOG_LEVEL", "BACKEND_HOST", "BACKEND_PORT"]

        all_valid = True

        # 检查必需的环境变量
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.add_issue(f"缺少必需的环境变量: {var}")
                all_valid = False
            elif value == f"your_{var.lower()}_here" or "your_" in value.lower():
                self.add_issue(f"环境变量 {var} 仍为默认值，请设置实际的值")
                all_valid = False
            else:
                print(f"   ✅ {var}: 已设置")

        # 检查可选的环境变量
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                print(f"   ℹ️  {var}: {value}")
            else:
                self.add_warning(f"可选环境变量 {var} 未设置，将使用默认值")

        return all_valid

    def validate_config_files(self) -> bool:
        """验证配置文件"""
        print("\n📄 验证配置文件...")

        config_files = {
            ".env": "环境变量文件",
            "config_template.env": "环境变量模板",
            "requirements.txt": "Python依赖文件",
        }

        all_valid = True

        for file_path, description in config_files.items():
            path = Path(file_path)
            if path.exists():
                print(f"   ✅ {description}: 存在")

                # 检查文件权限
                if not path.is_file():
                    self.add_issue(f"{file_path} 不是有效文件")
                    all_valid = False
                elif not os.access(path, os.R_OK):
                    self.add_issue(f"{file_path} 无读取权限")
                    all_valid = False
            else:
                if file_path == ".env":
                    self.add_issue(f"缺少{description}: {file_path}")
                    all_valid = False
                else:
                    self.add_warning(f"缺少{description}: {file_path}")

        return all_valid

    def validate_directory_structure(self) -> bool:
        """验证目录结构"""
        print("\n📁 验证目录结构...")

        required_dirs = ["src/", "backend/", "frontend/", "data/", "data/stock_data/"]

        optional_dirs = [
            "data/stock_data/pdf_reports/",
            "data/stock_data/databases/",
            "data/stock_data/debug_data/",
            "logs/",
            "docs/",
        ]

        all_valid = True

        # 检查必需目录
        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                print(f"   ✅ {dir_path}: 存在")
            else:
                self.add_issue(f"缺少必需目录: {dir_path}")
                all_valid = False

        # 检查可选目录
        for dir_path in optional_dirs:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                print(f"   ℹ️  {dir_path}: 存在")
            else:
                self.add_warning(f"可选目录 {dir_path} 不存在，将在需要时创建")

        return all_valid

    def validate_core_files(self) -> bool:
        """验证核心文件"""
        print("\n📦 验证核心文件...")

        required_files = [
            "src/config.py",
            "src/dashscope_client.py",
            "src/api_requests.py",
            "backend/main.py",
            "frontend/index.html",
            "run_backend.py",
            "run_frontend.py",
        ]

        optional_files = [
            "src/pdf_parsing_mineru.py",
            "src/ingestion.py",
            "src/pipeline.py",
            "src/questions_processing.py",
            "data/stock_data/questions.json",
            "data/stock_data/subset.csv",
        ]

        all_valid = True

        # 检查必需文件
        for file_path in required_files:
            path = Path(file_path)
            if path.exists() and path.is_file():
                print(f"   ✅ {file_path}: 存在")

                # 检查文件大小
                size = path.stat().st_size
                if size == 0:
                    self.add_warning(f"{file_path} 文件为空")
                elif size < 100:  # 小于100字节可能有问题
                    self.add_warning(f"{file_path} 文件很小({size}字节)，可能不完整")

            else:
                self.add_issue(f"缺少必需文件: {file_path}")
                all_valid = False

        # 检查可选文件
        for file_path in optional_files:
            path = Path(file_path)
            if path.exists() and path.is_file():
                print(f"   ℹ️  {file_path}: 存在")
            else:
                self.add_warning(f"可选文件 {file_path} 不存在")

        return all_valid

    def validate_api_connection(self) -> bool:
        """验证API连接"""
        print("\n🌐 验证API连接...")

        try:
            # 验证DashScope设置
            if not validate_dashscope_setup():
                self.add_issue("DashScope API设置验证失败")
                return False

            print("   ✅ DashScope API密钥格式验证通过")

            # 测试API连接
            try:
                client = DashScopeClient()

                # 测试简单的文本生成
                result = client.generate_text(
                    prompt="你好", max_tokens=10, temperature=0.1
                )

                if result["success"]:
                    print("   ✅ DashScope LLM连接正常")
                else:
                    self.add_issue(f"DashScope LLM连接失败: {result.get('error')}")
                    return False

                # 测试嵌入向量
                embed_result = client.get_embeddings(["测试文本"])

                if embed_result["success"]:
                    print("   ✅ DashScope Embedding连接正常")
                    embedding_dim = len(embed_result["embeddings"][0])
                    print(f"      向量维度: {embedding_dim}")
                else:
                    self.add_issue(
                        f"DashScope Embedding连接失败: {embed_result.get('error')}"
                    )
                    return False

            except Exception as e:
                self.add_issue(f"API连接测试异常: {str(e)}")
                return False

            return True

        except Exception as e:
            self.add_issue(f"API验证失败: {str(e)}")
            return False

    def validate_python_environment(self) -> bool:
        """验证Python环境"""
        print("\n🐍 验证Python环境...")

        # 检查Python版本
        python_version = sys.version_info
        print(
            f"   Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )

        if python_version.major < 3 or python_version.minor < 8:
            self.add_issue("Python版本需要3.8或更高")
            return False
        else:
            print("   ✅ Python版本符合要求")

        # 检查关键依赖包
        required_packages = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "dashscope",
            "faiss-cpu",
            "numpy",
            "pandas",
        ]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"   ✅ {package}: 已安装")
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            self.add_issue(f"缺少依赖包: {', '.join(missing_packages)}")
            print("   💡 运行: pip install -r requirements.txt")
            return False

        return True

    def validate_file_permissions(self) -> bool:
        """验证文件权限"""
        print("\n🔐 验证文件权限...")

        # 检查写入权限
        writable_dirs = ["data/", "logs/", "."]  # 当前目录

        all_valid = True

        for dir_path in writable_dirs:
            path = Path(dir_path)

            # 确保目录存在
            path.mkdir(parents=True, exist_ok=True)

            # 测试写入权限
            try:
                test_file = path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                print(f"   ✅ {dir_path}: 可写")
            except Exception as e:
                self.add_issue(f"目录 {dir_path} 无写入权限: {e}")
                all_valid = False

        return all_valid

    def run_validation(self) -> Dict[str, Any]:
        """运行完整验证"""
        print("🔍 投研RAG系统配置验证")
        print("=" * 50)

        validation_results = {
            "timestamp": str(Path(__file__).parent.absolute()),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "validations": {},
            "issues": [],
            "warnings": [],
            "overall_valid": False,
        }

        # 执行各项验证
        validations = [
            ("Python环境", self.validate_python_environment),
            ("环境变量", self.validate_environment_variables),
            ("配置文件", self.validate_config_files),
            ("目录结构", self.validate_directory_structure),
            ("核心文件", self.validate_core_files),
            ("文件权限", self.validate_file_permissions),
            ("API连接", self.validate_api_connection),
        ]

        for name, validator in validations:
            try:
                result = validator()
                validation_results["validations"][name] = result

                if result:
                    print(f"✅ {name}: 通过")
                else:
                    print(f"❌ {name}: 失败")

            except Exception as e:
                print(f"💥 {name}: 验证异常 - {e}")
                validation_results["validations"][name] = False
                self.add_issue(f"{name}验证异常: {str(e)}")

        # 汇总结果
        validation_results["issues"] = self.issues
        validation_results["warnings"] = self.warnings
        validation_results["overall_valid"] = len(self.issues) == 0

        # 显示总结
        print("\n" + "=" * 50)
        if validation_results["overall_valid"]:
            print("🎉 配置验证通过！系统已准备就绪。")
        else:
            print("⚠️  配置验证发现问题，请修复后再启动系统。")

        # 显示问题
        if self.issues:
            print(f"\n❌ 发现 {len(self.issues)} 个问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")

        # 显示警告
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        print("=" * 50)

        return validation_results

    def generate_fix_suggestions(self) -> List[str]:
        """生成修复建议"""
        suggestions = []

        if any("DASHSCOPE_API_KEY" in issue for issue in self.issues):
            suggestions.append("1. 创建.env文件并设置正确的DASHSCOPE_API_KEY")
            suggestions.append("   - 可以从config_template.env复制模板")
            suggestions.append("   - 从阿里云DashScope控制台获取API密钥")

        if any("依赖包" in issue for issue in self.issues):
            suggestions.append("2. 安装缺少的依赖包:")
            suggestions.append("   pip install -r requirements.txt")

        if any("目录" in issue for issue in self.issues):
            suggestions.append("3. 创建缺少的目录:")
            suggestions.append(
                "   mkdir -p data/stock_data/{pdf_reports,databases,debug_data}"
            )
            suggestions.append("   mkdir -p logs docs")

        if any("权限" in issue for issue in self.issues):
            suggestions.append("4. 检查文件权限:")
            suggestions.append("   chmod -R 755 .")
            suggestions.append("   chown -R $USER:$USER .")

        return suggestions


def main():
    """主函数"""
    validator = ConfigValidator()
    results = validator.run_validation()

    # 生成修复建议
    if not results["overall_valid"]:
        suggestions = validator.generate_fix_suggestions()

        if suggestions:
            print("\n💡 修复建议:")
            for suggestion in suggestions:
                print(f"   {suggestion}")

    # 保存验证报告
    try:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        report_file = logs_dir / "config_validation.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n📄 验证报告已保存: {report_file}")

    except Exception as e:
        print(f"\n⚠️  保存验证报告失败: {e}")

    # 返回结果
    return results["overall_valid"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
