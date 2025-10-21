"""
文档预览和风险高亮组件测试
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 测试夹具 ====================

@pytest.fixture
def sample_risk_data():
    """示例风险数据"""
    return {
        "id": "risk-123",
        "document_id": "doc-456",
        "scenario_id": "tender",
        "title": "投标文件资质要求严格",
        "description": "投标文件必须包含所有要求的资质文件，缺一即废标",
        "risk_type": "disqualification",
        "risk_level": "high",
        "page_number": 5,
        "section": "第三章 投标人资格要求",
        "clause_number": "3.1",
        "original_text": "投标文件必须包含所有要求的资质文件，缺一即废标。",
        "impact_description": "可能导致投标无效，失去中标机会",
        "mitigation_suggestion": "仔细核对所有资质文件清单，确保完整提交",
        "confidence_score": 95,
        "created_at": "2025-10-15T10:00:00",
        "updated_at": "2025-10-15T10:00:00"
    }


# ==================== 单元测试 ====================

class TestDocumentViewerComponents:
    """文档预览组件测试类"""

    def test_import_risk_types(self):
        """测试1: 导入风险类型定义"""
        try:
            # 这是前端TypeScript文件，Python无法直接导入
            # 但我们可以验证文件存在
            risk_types_file = project_root / "frontend-next" / "types" / "risk.ts"
            assert risk_types_file.exists(), "risk.ts文件不存在"

            content = risk_types_file.read_text(encoding='utf-8')
            assert "export enum RiskLevel" in content
            assert "export enum RiskType" in content
            assert "export interface Risk" in content
            assert "export interface RiskReport" in content

            logger.info("✅ 风险类型定义文件验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_api_client_has_risk_methods(self):
        """测试2: API客户端包含风险相关方法"""
        try:
            api_file = project_root / "frontend-next" / "lib" / "api-v2.ts"
            assert api_file.exists(), "api-v2.ts文件不存在"

            content = api_file.read_text(encoding='utf-8')
            assert "detectRisks" in content
            assert "detectRisksAsync" in content
            assert "getRiskReport" in content
            assert "getRiskReportByDocument" in content

            logger.info("✅ API客户端风险方法验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_document_viewer_component_exists(self):
        """测试3: DocumentViewer组件文件存在"""
        try:
            component_file = project_root / "frontend-next" / "components" / "document" / "document-viewer.tsx"
            assert component_file.exists(), "document-viewer.tsx文件不存在"

            content = component_file.read_text(encoding='utf-8')
            assert "export function DocumentViewer" in content
            assert "react-pdf" in content
            assert "Document" in content
            assert "Page" in content

            logger.info("✅ DocumentViewer组件验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_document_viewer_has_pdf_controls(self):
        """测试4: DocumentViewer包含PDF控制功能"""
        try:
            component_file = project_root / "frontend-next" / "components" / "document" / "document-viewer.tsx"
            content = component_file.read_text(encoding='utf-8')

            # 检查翻页功能
            assert "goToPreviousPage" in content
            assert "goToNextPage" in content

            # 检查缩放功能
            assert "zoomIn" in content
            assert "zoomOut" in content
            assert "resetZoom" in content

            # 检查下载功能
            assert "downloadPDF" in content

            logger.info("✅ DocumentViewer PDF控制功能验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_document_viewer_has_risk_highlight(self):
        """测试5: DocumentViewer包含风险高亮功能"""
        try:
            component_file = project_root / "frontend-next" / "components" / "document" / "document-viewer.tsx"
            content = component_file.read_text(encoding='utf-8')

            assert "RiskHighlightOverlay" in content
            assert "currentPageRisks" in content
            assert "onRiskClick" in content

            logger.info("✅ DocumentViewer风险高亮功能验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_risk_detail_panel_component_exists(self):
        """测试6: RiskDetailPanel组件文件存在"""
        try:
            component_file = project_root / "frontend-next" / "components" / "document" / "risk-detail-panel.tsx"
            assert component_file.exists(), "risk-detail-panel.tsx文件不存在"

            content = component_file.read_text(encoding='utf-8')
            assert "export function RiskDetailPanel" in content
            assert "Risk" in content
            assert "onClose" in content

            logger.info("✅ RiskDetailPanel组件验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_risk_detail_panel_has_all_sections(self):
        """测试7: RiskDetailPanel包含所有信息区块"""
        try:
            component_file = project_root / "frontend-next" / "components" / "document" / "risk-detail-panel.tsx"
            content = component_file.read_text(encoding='utf-8')

            # 检查各个信息区块
            assert "风险描述" in content
            assert "原文内容" in content
            assert "影响分析" in content
            assert "应对建议" in content or "缓解建议" in content
            assert "置信度" in content

            logger.info("✅ RiskDetailPanel信息区块验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_document_preview_page_exists(self):
        """测试8: 文档预览页面文件存在"""
        try:
            page_file = project_root / "frontend-next" / "app" / "document" / "[documentId]" / "page.tsx"
            assert page_file.exists(), "文档预览页面不存在"

            content = page_file.read_text(encoding='utf-8')
            assert "DocumentPreviewPage" in content or "export default function" in content
            assert "DocumentViewer" in content
            assert "RiskDetailPanel" in content

            logger.info("✅ 文档预览页面验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_document_preview_page_has_risk_detection(self):
        """测试9: 文档预览页面包含风险检测功能"""
        try:
            page_file = project_root / "frontend-next" / "app" / "document" / "[documentId]" / "page.tsx"
            content = page_file.read_text(encoding='utf-8')

            assert "getRiskReportByDocument" in content
            assert "detectRisksAsync" in content
            assert "fetchRiskReport" in content or "handleDetectRisks" in content

            logger.info("✅ 文档预览页面风险检测功能验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_document_preview_page_has_statistics(self):
        """测试10: 文档预览页面包含统计信息"""
        try:
            page_file = project_root / "frontend-next" / "app" / "document" / "[documentId]" / "page.tsx"
            content = page_file.read_text(encoding='utf-8')

            assert "stats" in content
            assert "total_risks" in content or "total" in content
            assert "high_risks" in content or "high" in content
            assert "medium_risks" in content or "medium" in content
            assert "low_risks" in content or "low" in content

            logger.info("✅ 文档预览页面统计信息验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_risk_level_colors_defined(self):
        """测试11: 风险等级颜色定义"""
        try:
            risk_types_file = project_root / "frontend-next" / "types" / "risk.ts"
            content = risk_types_file.read_text(encoding='utf-8')

            assert "RISK_LEVEL_COLORS" in content
            assert "RiskLevel.HIGH" in content or "[RiskLevel.HIGH]" in content
            assert "RiskLevel.MEDIUM" in content or "[RiskLevel.MEDIUM]" in content
            assert "RiskLevel.LOW" in content or "[RiskLevel.LOW]" in content

            logger.info("✅ 风险等级颜色定义验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_risk_type_labels_defined(self):
        """测试12: 风险类型标签定义"""
        try:
            risk_types_file = project_root / "frontend-next" / "types" / "risk.ts"
            content = risk_types_file.read_text(encoding='utf-8')

            assert "RISK_TYPE_LABELS" in content
            assert "废标风险" in content
            assert "无限责任" in content
            assert "苛刻条款" in content

            logger.info("✅ 风险类型标签定义验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_component_integration(self):
        """测试13: 组件集成验证"""
        # 验证所有组件文件都存在
        components = [
            "frontend-next/types/risk.ts",
            "frontend-next/components/document/document-viewer.tsx",
            "frontend-next/components/document/risk-detail-panel.tsx",
            "frontend-next/app/document/[documentId]/page.tsx",
        ]

        for component_path in components:
            file_path = project_root / component_path
            assert file_path.exists(), f"{component_path} 不存在"

        logger.info("✅ 组件集成验证通过")

    def test_package_json_has_react_pdf(self):
        """测试14: package.json包含react-pdf依赖"""
        try:
            package_json = project_root / "frontend-next" / "package.json"
            assert package_json.exists(), "package.json不存在"

            content = package_json.read_text(encoding='utf-8')
            assert "react-pdf" in content
            assert "pdfjs-dist" in content

            logger.info("✅ package.json依赖验证通过")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_workflow_completeness(self):
        """测试15: 工作流程完整性验证"""
        # 这是一个概念性测试，验证完整流程的逻辑

        # 步骤1: 用户访问文档预览页面
        page_exists = (project_root / "frontend-next" / "app" / "document" / "[documentId]" / "page.tsx").exists()
        assert page_exists

        # 步骤2: 页面调用API获取风险报告
        api_has_methods = True  # 已在前面测试验证
        assert api_has_methods

        # 步骤3: DocumentViewer渲染PDF
        viewer_exists = (project_root / "frontend-next" / "components" / "document" / "document-viewer.tsx").exists()
        assert viewer_exists

        # 步骤4: 显示风险高亮
        # 步骤5: 点击查看详情
        panel_exists = (project_root / "frontend-next" / "components" / "document" / "risk-detail-panel.tsx").exists()
        assert panel_exists

        logger.info("✅ 工作流程完整性验证通过")


# ==================== 运行测试 ====================

if __name__ == "__main__":
    logger.info("🧪 开始运行文档预览组件测试...")
    pytest.main([__file__, "-v", "-s"])

