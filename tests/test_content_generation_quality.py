"""
内容生成质量验证测试
验证T1.4.3任务：生成质量调优
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestContentGenerationQuality:
    """内容生成质量验证测试类"""

    def test_prompt_templates_have_examples(self):
        """测试1: 提示词模板包含Few-shot示例"""
        from backend.services.content_service import ContentService

        service = ContentService()

        # 检查公司简介模板是否包含示例
        company_intro_template = service._get_company_intro_template()
        assert "参考示例" in company_intro_template or "示例" in company_intro_template
        assert len(company_intro_template) > 500  # 确保模板有足够的内容

        # 检查技术方案模板是否包含示例
        tech_template = service._get_technical_solution_template()
        assert "参考示例" in tech_template or "示例" in tech_template

        logger.info("✅ 提示词模板包含Few-shot示例验证通过")

    def test_system_prompt_enhanced(self):
        """测试2: System prompt已优化"""
        service_file = project_root / "backend" / "services" / "content_service.py"
        content = service_file.read_text(encoding='utf-8')

        # 检查system prompt是否包含更详细的描述
        assert "专业" in content
        assert "招投标" in content

        logger.info("✅ System prompt优化验证通过")

    def test_temperature_parameter_added(self):
        """测试3: temperature参数已添加"""
        service_file = project_root / "backend" / "services" / "content_service.py"
        content = service_file.read_text(encoding='utf-8')

        assert "temperature" in content
        assert "temperature =" in content or "temperature=" in content

        logger.info("✅ Temperature参数验证通过")

    def test_top_p_parameter_added(self):
        """测试4: top_p参数已添加"""
        service_file = project_root / "backend" / "services" / "content_service.py"
        content = service_file.read_text(encoding='utf-8')

        assert "top_p" in content

        logger.info("✅ Top_p参数验证通过")

    def test_max_tokens_parameter_configured(self):
        """测试5: max_tokens参数已配置"""
        service_file = project_root / "backend" / "services" / "content_service.py"
        content = service_file.read_text(encoding='utf-8')

        assert "max_tokens" in content
        assert "2000" in content or "2500" in content  # 检查token数量配置

        logger.info("✅ Max_tokens参数验证通过")

    def test_dynamic_parameters_based_on_content_type(self):
        """测试6: 参数根据内容类型动态调整"""
        service_file = project_root / "backend" / "services" / "content_service.py"
        content = service_file.read_text(encoding='utf-8')

        # 检查是否有根据content_type调整参数的逻辑
        assert "content_type" in content
        assert "if content_type" in content or "根据内容类型" in content

        logger.info("✅ 动态参数调整验证通过")

    def test_company_intro_template_structure(self):
        """测试7: 公司简介模板结构完整"""
        from backend.services.content_service import ContentService

        service = ContentService()
        template = service._get_company_intro_template()

        # 检查必要的结构要素
        assert "公司基本情况" in template
        assert "资质" in template or "荣誉" in template
        assert "规模" in template or "实力" in template
        assert "业务" in template or "优势" in template

        logger.info("✅ 公司简介模板结构验证通过")

    def test_technical_solution_template_structure(self):
        """测试8: 技术方案模板结构完整"""
        from backend.services.content_service import ContentService

        service = ContentService()
        template = service._get_technical_solution_template()

        # 检查必要的结构要素
        assert "需求分析" in template
        assert "技术方案" in template
        assert "架构" in template
        assert "实施" in template or "步骤" in template

        logger.info("✅ 技术方案模板结构验证通过")

    def test_template_variable_placeholders(self):
        """测试9: 模板包含正确的变量占位符"""
        from backend.services.content_service import ContentService

        service = ContentService()
        templates = [
            service._get_company_intro_template(),
            service._get_technical_solution_template(),
        ]

        for template in templates:
            assert "{project_name}" in template
            assert "{context}" in template
            assert "{requirements}" in template

        logger.info("✅ 模板变量占位符验证通过")

    def test_prompt_length_adequate(self):
        """测试10: 提示词长度足够（包含详细指导）"""
        from backend.services.content_service import ContentService

        service = ContentService()

        # 检查各模板长度
        company_intro_len = len(service._get_company_intro_template())
        tech_solution_len = len(service._get_technical_solution_template())

        # 优化后的模板应该更长（包含示例）
        assert company_intro_len > 800  # 原模板约400字符
        assert tech_solution_len > 1000  # 原模板约500字符

        logger.info(f"✅ 提示词长度验证通过 - 公司简介: {company_intro_len}, 技术方案: {tech_solution_len}")

    def test_content_type_enum_complete(self):
        """测试11: 内容类型枚举完整"""
        from backend.services.content_service import ContentType

        # 确保包含所有7种内容类型
        assert ContentType.COMPANY_INTRO
        assert ContentType.TECHNICAL_SOLUTION
        assert ContentType.SERVICE_COMMITMENT
        assert ContentType.QUALITY_ASSURANCE
        assert ContentType.SAFETY_MEASURES
        assert ContentType.PROJECT_EXPERIENCE
        assert ContentType.TEAM_INTRODUCTION

        logger.info("✅ 内容类型枚举完整性验证通过")

    def test_optimization_applied(self):
        """测试12: 综合优化已应用"""
        from backend.services.content_service import ContentService

        service = ContentService()
        service_file = project_root / "backend" / "services" / "content_service.py"
        content = service_file.read_text(encoding='utf-8')

        # 检查关键优化点
        optimizations = [
            "temperature",
            "top_p",
            "max_tokens",
            "参考示例",
            "专业",
        ]

        for opt in optimizations:
            assert opt in content, f"缺少优化: {opt}"

        logger.info("✅ 综合优化应用验证通过")


if __name__ == "__main__":
    logger.info("🧪 开始运行内容生成质量测试...")
    pytest.main([__file__, "-v", "-s"])

