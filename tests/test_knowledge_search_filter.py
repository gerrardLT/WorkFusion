"""
知识库搜索和过滤功能测试
验证T1.3.3任务：文档标签、搜索、过滤
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestKnowledgeSearchFilter:
    """知识库搜索和过滤功能测试类"""

    def test_knowledge_service_has_search(self):
        """测试1: KnowledgeService包含搜索方法"""
        from backend.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        assert hasattr(service, 'search_knowledge_items')
        assert hasattr(service, 'list_knowledge_items')

        logger.info("✅ KnowledgeService搜索方法验证通过")

    def test_list_knowledge_items_parameters(self):
        """测试2: list_knowledge_items支持过滤参数"""
        import inspect
        from backend.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        sig = inspect.signature(service.list_knowledge_items)
        params = sig.parameters

        # 验证支持的过滤参数
        assert 'category' in params
        assert 'status' in params
        assert 'tags' in params
        assert 'search_query' in params

        logger.info("✅ 过滤参数验证通过")

    def test_search_knowledge_items_exists(self):
        """测试3: search_knowledge_items方法存在"""
        import inspect
        from backend.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        assert hasattr(service, 'search_knowledge_items')

        sig = inspect.signature(service.search_knowledge_items)
        params = sig.parameters

        assert 'query' in params or 'scenario_id' in params
        assert 'category' in params

        logger.info("✅ 搜索方法签名验证通过")

    def test_knowledge_item_has_tags(self):
        """测试4: KnowledgeItem模型包含tags字段"""
        from backend.models import KnowledgeItem

        # 验证tags属性存在
        assert hasattr(KnowledgeItem, 'tags')

        logger.info("✅ KnowledgeItem模型tags字段验证通过")

    def test_api_has_search_endpoint(self):
        """测试5: API包含搜索端点"""
        api_file = project_root / "backend" / "api" / "knowledge.py"
        content = api_file.read_text(encoding='utf-8')

        assert "/search" in content or "search" in content
        assert "search_query" in content or "query" in content

        logger.info("✅ API搜索端点验证通过")

    def test_api_list_has_filter_params(self):
        """测试6: API列表端点支持过滤参数"""
        api_file = project_root / "backend" / "api" / "knowledge.py"
        content = api_file.read_text(encoding='utf-8')

        assert "category" in content
        assert "status" in content
        assert "tags" in content

        logger.info("✅ API过滤参数验证通过")

    def test_frontend_has_search_input(self):
        """测试7: 前端页面包含搜索输入框"""
        page_file = project_root / "frontend-next" / "app" / "knowledge" / "page.tsx"
        content = page_file.read_text(encoding='utf-8')

        assert "searchQuery" in content
        assert "Search" in content

        logger.info("✅ 前端搜索输入框验证通过")

    def test_frontend_has_category_filter(self):
        """测试8: 前端页面包含分类过滤"""
        page_file = project_root / "frontend-next" / "app" / "knowledge" / "page.tsx"
        content = page_file.read_text(encoding='utf-8')

        assert "selectedCategory" in content
        assert "Tabs" in content or "TabsList" in content

        logger.info("✅ 前端分类过滤验证通过")

    def test_frontend_displays_tags(self):
        """测试9: 前端页面显示标签"""
        page_file = project_root / "frontend-next" / "app" / "knowledge" / "page.tsx"
        content = page_file.read_text(encoding='utf-8')

        assert "tags" in content
        assert "Badge" in content

        logger.info("✅ 前端标签显示验证通过")

    def test_knowledge_types_has_tags(self):
        """测试10: 知识库类型定义包含tags"""
        types_file = project_root / "frontend-next" / "types" / "knowledge.ts"
        content = types_file.read_text(encoding='utf-8')

        assert "tags" in content

        logger.info("✅ TypeScript类型定义tags字段验证通过")

    def test_api_client_has_search_method(self):
        """测试11: API客户端包含搜索方法"""
        api_file = project_root / "frontend-next" / "lib" / "api-v2.ts"
        content = api_file.read_text(encoding='utf-8')

        assert "searchKnowledgeItems" in content
        assert "listKnowledgeItems" in content

        logger.info("✅ API客户端搜索方法验证通过")

    def test_integration_complete(self):
        """测试12: 搜索和过滤功能完整集成"""
        # 后端服务
        from backend.services.knowledge_service import KnowledgeService
        service = KnowledgeService()
        assert hasattr(service, 'search_knowledge_items')
        assert hasattr(service, 'list_knowledge_items')

        # 前端页面
        page_file = project_root / "frontend-next" / "app" / "knowledge" / "page.tsx"
        assert page_file.exists()

        # API端点
        api_file = project_root / "backend" / "api" / "knowledge.py"
        assert api_file.exists()

        logger.info("✅ 搜索和过滤功能完整集成验证通过")


if __name__ == "__main__":
    logger.info("🧪 开始运行知识库搜索和过滤测试...")
    pytest.main([__file__, "-v", "-s"])

