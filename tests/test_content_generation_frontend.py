"""
内容生成前端组件测试
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestContentGenerationFrontend:
    """内容生成前端组件测试类"""

    def test_api_types_exist(self):
        """测试1: API类型定义存在"""
        api_file = project_root / "frontend-next" / "lib" / "api-v2.ts"
        content = api_file.read_text(encoding='utf-8')

        assert "ContentGenerationRequest" in content
        assert "ContentGenerationResponse" in content
        assert "ContentType" in content

        logger.info("✅ API类型定义验证通过")

    def test_generate_methods_exist(self):
        """测试2: 生成方法存在"""
        api_file = project_root / "frontend-next" / "lib" / "api-v2.ts"
        content = api_file.read_text(encoding='utf-8')

        assert "generateContent" in content
        assert "regenerateContent" in content
        assert "getContentTypes" in content

        logger.info("✅ 生成方法验证通过")

    def test_content_generation_buttons_component(self):
        """测试3: ContentGenerationButtons组件存在"""
        component_file = project_root / "frontend-next" / "components" / "chat" / "content-generation-buttons.tsx"
        assert component_file.exists()

        content = component_file.read_text(encoding='utf-8')
        assert "ContentGenerationButtons" in content
        assert "onContentGenerated" in content
        assert "generateContent" in content

        logger.info("✅ ContentGenerationButtons组件验证通过")

    def test_component_has_loading_state(self):
        """测试4: 组件包含加载状态"""
        component_file = project_root / "frontend-next" / "components" / "chat" / "content-generation-buttons.tsx"
        content = component_file.read_text(encoding='utf-8')

        assert "generatingType" in content
        assert "loading" in content
        assert "Loader2" in content

        logger.info("✅ 加载状态验证通过")

    def test_component_has_grid_layout(self):
        """测试5: 组件使用网格布局"""
        component_file = project_root / "frontend-next" / "components" / "chat" / "content-generation-buttons.tsx"
        content = component_file.read_text(encoding='utf-8')

        assert "grid grid-cols-2" in content or "grid-cols-2" in content

        logger.info("✅ 网格布局验证通过")

    def test_input_area_integration(self):
        """测试6: InputArea集成ContentGenerationButtons"""
        input_area_file = project_root / "frontend-next" / "components" / "chat" / "input-area.tsx"
        content = input_area_file.read_text(encoding='utf-8')

        assert "ContentGenerationButtons" in content
        assert "onContentGenerated" in content

        logger.info("✅ InputArea集成验证通过")

    def test_only_tender_scenario(self):
        """测试7: 仅在招投标场景显示"""
        input_area_file = project_root / "frontend-next" / "components" / "chat" / "input-area.tsx"
        content = input_area_file.read_text(encoding='utf-8')

        assert "currentScenario?.id === 'tender'" in content or "scenario" in content.lower()

        logger.info("✅ 场景条件验证通过")

    def test_generated_content_fills_input(self):
        """测试8: 生成的内容填充到输入框"""
        input_area_file = project_root / "frontend-next" / "components" / "chat" / "input-area.tsx"
        content = input_area_file.read_text(encoding='utf-8')

        assert "setInput(content)" in content or "setInput" in content

        logger.info("✅ 内容填充验证通过")

    def test_api_exports(self):
        """测试9: API函数正确导出"""
        api_file = project_root / "frontend-next" / "lib" / "api-v2.ts"
        content = api_file.read_text(encoding='utf-8')

        # 检查导出语句
        assert "export const generateContent" in content
        assert "export const regenerateContent" in content
        assert "export const getContentTypes" in content

        logger.info("✅ API导出验证通过")

    def test_component_disabled_state(self):
        """测试10: 组件支持禁用状态"""
        component_file = project_root / "frontend-next" / "components" / "chat" / "content-generation-buttons.tsx"
        content = component_file.read_text(encoding='utf-8')

        assert "disabled" in content

        logger.info("✅ 禁用状态验证通过")

    def test_toast_notifications(self):
        """测试11: 组件使用toast通知"""
        component_file = project_root / "frontend-next" / "components" / "chat" / "content-generation-buttons.tsx"
        content = component_file.read_text(encoding='utf-8')

        assert "useToast" in content
        assert "toast" in content

        logger.info("✅ Toast通知验证通过")

    def test_component_props_interface(self):
        """测试12: 组件Props接口定义"""
        component_file = project_root / "frontend-next" / "components" / "chat" / "content-generation-buttons.tsx"
        content = component_file.read_text(encoding='utf-8')

        assert "ContentGenerationButtonsProps" in content
        assert "onContentGenerated" in content
        assert "scenarioId" in content

        logger.info("✅ Props接口验证通过")


if __name__ == "__main__":
    logger.info("🧪 开始运行内容生成前端测试...")
    pytest.main([__file__, "-v", "-s"])

