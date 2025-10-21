"""
内容生成服务和API测试
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging
from unittest.mock import MagicMock, patch, AsyncMock

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestContentGeneration:
    """内容生成功能测试类"""

    def test_content_service_import(self):
        """测试1: ContentService导入"""
        from backend.services.content_service import ContentService, ContentType, get_content_service
        assert ContentService is not None
        assert ContentType is not None
        assert get_content_service is not None
        logger.info("✅ ContentService导入成功")

    def test_content_type_enum(self):
        """测试2: ContentType枚举验证"""
        from backend.services.content_service import ContentType

        # 验证所有内容类型
        assert ContentType.COMPANY_INTRO.value == "company_intro"
        assert ContentType.TECHNICAL_SOLUTION.value == "technical_solution"
        assert ContentType.SERVICE_COMMITMENT.value == "service_commitment"
        assert ContentType.QUALITY_ASSURANCE.value == "quality_assurance"
        assert ContentType.SAFETY_MEASURES.value == "safety_measures"
        assert ContentType.PROJECT_EXPERIENCE.value == "project_experience"
        assert ContentType.TEAM_INTRODUCTION.value == "team_introduction"

        logger.info("✅ ContentType枚举验证通过")

    def test_generate_api_import(self):
        """测试3: Generate API导入"""
        from backend.api.generate import router, ContentGenerationRequest, ContentGenerationResponse
        assert router is not None
        assert ContentGenerationRequest is not None
        assert ContentGenerationResponse is not None
        logger.info("✅ Generate API导入成功")

    def test_content_generation_request_model(self):
        """测试4: 请求模型验证"""
        from backend.api.generate import ContentGenerationRequest
        from backend.services.content_service import ContentType

        # 创建有效请求
        request = ContentGenerationRequest(
            content_type=ContentType.COMPANY_INTRO,
            project_name="测试项目",
            requirements="重点突出技术实力",
            use_knowledge_base=True,
            scenario_id="tender"
        )

        assert request.content_type == ContentType.COMPANY_INTRO
        assert request.project_name == "测试项目"
        assert request.use_knowledge_base is True

        logger.info("✅ 请求模型验证通过")

    def test_content_service_initialization(self):
        """测试5: ContentService初始化"""
        from backend.services.content_service import ContentService

        service = ContentService(scenario_id="tender")

        assert service.scenario_id == "tender"
        assert service.llm_client is not None
        assert service.qa_processor is not None
        assert len(service.prompt_templates) == 7

        logger.info("✅ ContentService初始化验证通过")

    def test_prompt_templates_exist(self):
        """测试6: 提示词模板存在性"""
        from backend.services.content_service import ContentService, ContentType

        service = ContentService()

        # 验证所有内容类型都有对应的模板
        for content_type in ContentType:
            assert content_type in service.prompt_templates
            template = service.prompt_templates[content_type]
            assert len(template) > 0
            assert "{project_name}" in template
            assert "{context}" in template
            assert "{requirements}" in template

        logger.info("✅ 提示词模板验证通过")

    def test_build_retrieval_query(self):
        """测试7: 检索查询构建"""
        from backend.services.content_service import ContentService, ContentType

        service = ContentService()

        # 测试不同内容类型的查询构建
        query1 = service._build_retrieval_query(ContentType.COMPANY_INTRO, "测试项目")
        assert "公司简介" in query1 or "企业资质" in query1

        query2 = service._build_retrieval_query(ContentType.TECHNICAL_SOLUTION, "智能电网项目")
        assert "技术方案" in query2 or "实施方案" in query2

        logger.info("✅ 检索查询构建验证通过")

    def test_build_prompt(self):
        """测试8: 提示词构建"""
        from backend.services.content_service import ContentService, ContentType

        service = ContentService()

        prompt = service._build_prompt(
            content_type=ContentType.COMPANY_INTRO,
            context="公司成立于2010年，注册资本5000万元",
            project_name="某电力项目",
            requirements="突出电力行业经验"
        )

        assert "某电力项目" in prompt
        assert "公司成立于2010年" in prompt
        assert "突出电力行业经验" in prompt

        logger.info("✅ 提示词构建验证通过")

    @pytest.mark.asyncio
    async def test_generate_content_mock(self):
        """测试9: 内容生成（Mock LLM）"""
        from backend.services.content_service import ContentService, ContentType

        service = ContentService()

        # Mock LLM响应
        mock_response = {
            "success": True,
            "text": "这是一份专业的公司简介...",
            "usage": {"total_tokens": 500}
        }

        with patch.object(service.llm_client, 'generate_text', return_value=mock_response):
            with patch.object(service, '_retrieve_context', new_callable=AsyncMock, return_value="测试上下文"):
                result = await service.generate_content(
                    content_type=ContentType.COMPANY_INTRO,
                    project_name="测试项目",
                    use_knowledge_base=True
                )

        assert result["success"] is True
        assert "content" in result
        assert result["content_type"] == "company_intro"
        assert result["word_count"] > 0

        logger.info("✅ 内容生成（Mock）验证通过")

    def test_api_endpoints_registered(self):
        """测试10: API端点注册"""
        from backend.api.generate import router

        # 获取所有路由
        routes = [route.path for route in router.routes]

        assert "/content" in routes
        assert "/content-types" in routes
        assert "/regenerate" in routes

        logger.info("✅ API端点注册验证通过")

    def test_content_types_endpoint_response(self):
        """测试11: 内容类型列表端点"""
        from backend.api.generate import ContentTypeListResponse

        response = ContentTypeListResponse(
            content_types=[
                {"value": "company_intro", "label": "公司简介", "icon": "🏢"},
                {"value": "technical_solution", "label": "技术方案", "icon": "🔧"}
            ]
        )

        assert len(response.content_types) == 2
        assert response.content_types[0]["value"] == "company_intro"

        logger.info("✅ 内容类型列表端点验证通过")

    def test_integration_with_main_app(self):
        """测试12: 主应用集成"""
        # 验证generate模块已被导入
        from backend.api import generate
        assert generate is not None

        # 验证router存在
        assert hasattr(generate, 'router')

        logger.info("✅ 主应用集成验证通过")


if __name__ == "__main__":
    logger.info("🧪 开始运行内容生成测试...")
    pytest.main([__file__, "-v", "-s"])

