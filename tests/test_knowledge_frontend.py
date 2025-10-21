"""
知识库前端组件测试
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestKnowledgeFrontend:
    """知识库前端组件测试类"""

    def test_knowledge_types_exist(self):
        """测试1: TypeScript类型定义文件存在"""
        types_file = project_root / "frontend-next" / "types" / "knowledge.ts"
        assert types_file.exists()
        content = types_file.read_text(encoding='utf-8')
        assert "export enum KnowledgeCategory" in content
        assert "export enum KnowledgeStatus" in content
        assert "export interface KnowledgeItem" in content
        logger.info("✅ 知识库类型定义验证通过")

    def test_api_client_has_knowledge_methods(self):
        """测试2: API客户端包含知识库方法"""
        api_file = project_root / "frontend-next" / "lib" / "api-v2.ts"
        content = api_file.read_text(encoding='utf-8')
        assert "createKnowledgeItem" in content
        assert "listKnowledgeItems" in content
        assert "getKnowledgeStats" in content
        logger.info("✅ API客户端知识库方法验证通过")

    def test_knowledge_page_exists(self):
        """测试3: 知识库管理页面存在"""
        page_file = project_root / "frontend-next" / "app" / "knowledge" / "page.tsx"
        assert page_file.exists()
        content = page_file.read_text(encoding='utf-8')
        assert "KnowledgePage" in content or "export default function" in content
        logger.info("✅ 知识库管理页面验证通过")

    def test_knowledge_page_has_tabs(self):
        """测试4: 页面包含分类Tab"""
        page_file = project_root / "frontend-next" / "app" / "knowledge" / "page.tsx"
        content = page_file.read_text(encoding='utf-8')
        assert "Tabs" in content
        assert "TabsList" in content
        logger.info("✅ 分类Tab验证通过")

    def test_knowledge_page_has_view_modes(self):
        """测试5: 页面支持卡片和列表视图"""
        page_file = project_root / "frontend-next" / "app" / "knowledge" / "page.tsx"
        content = page_file.read_text(encoding='utf-8')
        assert "viewMode" in content
        assert "card" in content
        assert "list" in content
        logger.info("✅ 视图模式验证通过")

    def test_knowledge_page_has_search(self):
        """测试6: 页面包含搜索功能"""
        page_file = project_root / "frontend-next" / "app" / "knowledge" / "page.tsx"
        content = page_file.read_text(encoding='utf-8')
        assert "searchQuery" in content
        assert "Search" in content
        logger.info("✅ 搜索功能验证通过")

    def test_component_integration(self):
        """测试7: 组件集成验证"""
        components = [
            "frontend-next/types/knowledge.ts",
            "frontend-next/app/knowledge/page.tsx",
        ]
        for component_path in components:
            file_path = project_root / component_path
            assert file_path.exists(), f"{component_path} 不存在"
        logger.info("✅ 组件集成验证通过")


if __name__ == "__main__":
    logger.info("🧪 开始运行知识库前端测试...")
    pytest.main([__file__, "-v", "-s"])

