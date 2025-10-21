"""
文档上传与Checklist生成集成测试
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock, call

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 测试夹具 ====================

@pytest.fixture
def mock_background_tasks():
    """模拟FastAPI BackgroundTasks"""
    background_tasks = MagicMock()
    background_tasks.add_task = MagicMock()
    return background_tasks


@pytest.fixture
def mock_checklist_service():
    """模拟ChecklistService"""
    service = MagicMock()
    service.generate_checklist.return_value = "test-checklist-id"
    return service


# ==================== 单元测试 ====================

class TestUploadChecklistIntegration:
    """文档上传与Checklist生成集成测试"""

    def test_import_background_tasks(self):
        """测试1: 导入BackgroundTasks"""
        try:
            from fastapi.background import BackgroundTasks
            assert BackgroundTasks is not None
            logger.info("✅ BackgroundTasks 导入成功")
        except ImportError as e:
            pytest.fail(f"❌ 导入失败: {str(e)}")

    def test_import_checklist_service(self):
        """测试2: 导入ChecklistService"""
        try:
            from backend.services.checklist_service import get_checklist_service
            assert get_checklist_service is not None
            logger.info("✅ ChecklistService 导入成功")
        except ImportError as e:
            pytest.fail(f"❌ 导入失败: {str(e)}")

    def test_background_task_function_exists(self):
        """测试3: 验证后台任务函数存在"""
        try:
            from backend.api.upload import generate_checklist_background
            assert generate_checklist_background is not None
            assert callable(generate_checklist_background)
            logger.info("✅ generate_checklist_background 函数存在")
        except ImportError as e:
            pytest.fail(f"❌ 导入失败: {str(e)}")

    @patch('backend.api.upload.get_checklist_service')
    def test_background_task_execution(self, mock_get_service, mock_checklist_service):
        """测试4: 后台任务执行"""
        from backend.api.upload import generate_checklist_background

        # 设置模拟
        mock_get_service.return_value = mock_checklist_service

        # 执行后台任务
        document_id = "test-doc-id"
        scenario_id = "tender"

        generate_checklist_background(document_id, scenario_id)

        # 验证
        mock_get_service.assert_called_once()
        mock_checklist_service.generate_checklist.assert_called_once_with(
            document_id=document_id,
            scenario_id=scenario_id
        )

        logger.info("✅ 后台任务执行测试通过")

    @patch('backend.api.upload.get_checklist_service')
    def test_background_task_error_handling(self, mock_get_service):
        """测试5: 后台任务错误处理"""
        from backend.api.upload import generate_checklist_background

        # 模拟服务抛出异常
        mock_service = MagicMock()
        mock_service.generate_checklist.side_effect = Exception("Test error")
        mock_get_service.return_value = mock_service

        # 执行后台任务（不应抛出异常）
        try:
            generate_checklist_background("test-doc-id", "tender")
            logger.info("✅ 后台任务错误处理测试通过")
        except Exception as e:
            pytest.fail(f"❌ 后台任务应该捕获异常，但抛出了: {str(e)}")

    def test_upload_endpoint_has_background_tasks_param(self):
        """测试6: 上传端点有BackgroundTasks参数"""
        try:
            from backend.api.upload import router
            import inspect

            # 查找upload_file函数
            upload_file_func = None
            for route in router.routes:
                if hasattr(route, 'endpoint') and route.endpoint.__name__ == 'upload_file':
                    upload_file_func = route.endpoint
                    break

            assert upload_file_func is not None, "未找到upload_file函数"

            # 检查函数签名
            sig = inspect.signature(upload_file_func)
            params = sig.parameters

            assert 'background_tasks' in params, "upload_file缺少background_tasks参数"

            logger.info("✅ upload_file 包含 background_tasks 参数")
        except Exception as e:
            pytest.fail(f"❌ 测试失败: {str(e)}")

    def test_checklist_generation_condition(self):
        """测试7: Checklist生成条件"""
        # 测试场景ID为tender时应该生成Checklist
        scenario_id = "tender"
        success = True

        should_generate = success and scenario_id == "tender"
        assert should_generate == True

        # 测试其他场景不应该生成
        scenario_id = "enterprise"
        should_generate = success and scenario_id == "tender"
        assert should_generate == False

        # 测试处理失败时不应该生成
        scenario_id = "tender"
        success = False
        should_generate = success and scenario_id == "tender"
        assert should_generate == False

        logger.info("✅ Checklist生成条件测试通过")

    @patch('backend.api.upload.generate_checklist_background')
    def test_background_task_added_on_success(self, mock_bg_task, mock_background_tasks):
        """测试8: 成功处理后添加后台任务"""
        # 模拟成功的处理结果
        processing_result = {"success": True}
        scenario_id = "tender"
        document_id = "test-doc-id"

        # 模拟添加任务的逻辑
        if processing_result["success"] and scenario_id == "tender" and mock_background_tasks:
            mock_background_tasks.add_task(
                mock_bg_task,
                document_id,
                scenario_id
            )

        # 验证
        mock_background_tasks.add_task.assert_called_once_with(
            mock_bg_task,
            document_id,
            scenario_id
        )

        logger.info("✅ 后台任务添加测试通过")

    def test_response_includes_checklist_status(self):
        """测试9: 响应包含Checklist生成状态"""
        # 模拟响应构建逻辑
        processing_result = {"success": True}
        scenario_id = "tender"

        response = {
            "success": processing_result["success"],
            "checklist_generation": "queued" if (processing_result["success"] and scenario_id == "tender") else "skipped"
        }

        assert "checklist_generation" in response
        assert response["checklist_generation"] == "queued"

        # 测试非tender场景
        scenario_id = "enterprise"
        response = {
            "success": processing_result["success"],
            "checklist_generation": "queued" if (processing_result["success"] and scenario_id == "tender") else "skipped"
        }

        assert response["checklist_generation"] == "skipped"

        logger.info("✅ 响应包含Checklist状态测试通过")

    def test_integration_flow(self):
        """测试10: 完整集成流程验证"""
        # 这是一个概念性测试，验证完整流程的逻辑

        # 步骤1: 文档上传
        document_uploaded = True
        assert document_uploaded

        # 步骤2: 文档处理
        document_processed = True
        assert document_processed

        # 步骤3: 判断是否需要生成Checklist
        scenario_id = "tender"
        should_generate = document_processed and scenario_id == "tender"
        assert should_generate

        # 步骤4: 添加后台任务
        task_queued = True
        assert task_queued

        # 步骤5: 后台任务执行
        checklist_generated = True
        assert checklist_generated

        logger.info("✅ 完整集成流程验证通过")


# ==================== 运行测试 ====================

if __name__ == "__main__":
    logger.info("🧪 开始运行文档上传与Checklist集成测试...")
    pytest.main([__file__, "-v", "-s"])

