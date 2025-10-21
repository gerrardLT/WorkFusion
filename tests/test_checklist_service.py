"""
任务清单服务单元测试
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import pytest
import uuid
import logging
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 测试夹具 ====================

@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.filter.return_value.count.return_value = 0
    return session


@pytest.fixture
def mock_document():
    """模拟文档对象"""
    from backend.models import Document
    doc = Mock(spec=Document)
    doc.id = str(uuid.uuid4())
    doc.title = "测试招标文件"
    doc.scenario_id = "tender"
    doc.status = "completed"
    return doc


@pytest.fixture
def mock_questions_processor():
    """模拟问题处理器"""
    processor = MagicMock()

    # 模拟LLM返回的任务列表
    mock_response = {
        "success": True,
        "answer": """```json
[
  {
    "title": "提交企业营业执照副本",
    "description": "需提供企业营业执照副本复印件，加盖公章",
    "category": "资质文件准备",
    "priority": "high",
    "deadline": "2025-11-01",
    "estimated_hours": 2,
    "source_page": 5,
    "source_content": "投标人须提供有效的企业营业执照副本...",
    "confidence_score": 95
  },
  {
    "title": "编写技术方案",
    "description": "根据招标要求编写详细的技术实施方案",
    "category": "技术方案编写",
    "priority": "high",
    "deadline": "2025-11-05",
    "estimated_hours": 40,
    "source_page": 12,
    "source_content": "投标人应提供完整的技术方案...",
    "confidence_score": 90
  },
  {
    "title": "准备商务报价单",
    "description": "按照招标文件要求格式准备商务报价单",
    "category": "商务文件准备",
    "priority": "medium",
    "deadline": "2025-11-08",
    "estimated_hours": 8,
    "source_page": 20,
    "source_content": "商务报价单应包含...",
    "confidence_score": 85
  }
]
```"""
    }

    processor.process_question.return_value = mock_response
    return processor


@pytest.fixture
def sample_tasks_data():
    """示例任务数据"""
    return [
        {
            "title": "提交企业营业执照副本",
            "description": "需提供企业营业执照副本复印件，加盖公章",
            "category": "资质文件准备",
            "priority": "high",
            "deadline": "2025-11-01",
            "estimated_hours": 2,
            "source_page": 5,
            "source_content": "投标人须提供有效的企业营业执照副本...",
            "confidence_score": 95
        },
        {
            "title": "编写技术方案",
            "description": "根据招标要求编写详细的技术实施方案",
            "category": "技术方案编写",
            "priority": "high",
            "deadline": "2025-11-05",
            "estimated_hours": 40,
            "source_page": 12,
            "source_content": "投标人应提供完整的技术方案...",
            "confidence_score": 90
        }
    ]


# ==================== 单元测试 ====================

class TestChecklistService:
    """ChecklistService 单元测试"""

    def test_import_checklist_service(self):
        """测试1: 导入ChecklistService"""
        try:
            from backend.services.checklist_service import ChecklistService, get_checklist_service
            assert ChecklistService is not None
            assert get_checklist_service is not None
            logger.info("✅ ChecklistService 导入成功")
        except ImportError as e:
            pytest.fail(f"❌ 导入失败: {str(e)}")

    def test_import_models(self):
        """测试2: 导入数据模型"""
        try:
            from backend.models import Checklist, Task, TaskPriority, TaskStatus
            assert Checklist is not None
            assert Task is not None
            assert TaskPriority is not None
            assert TaskStatus is not None
            logger.info("✅ 数据模型导入成功")
        except ImportError as e:
            pytest.fail(f"❌ 导入失败: {str(e)}")

    def test_validate_task_data(self, sample_tasks_data):
        """测试3: 验证任务数据"""
        from backend.services.checklist_service import ChecklistService

        service = ChecklistService()

        # 测试有效数据
        valid_task = sample_tasks_data[0]
        assert service._validate_task_data(valid_task) == True

        # 测试缺少必需字段
        invalid_task = {"description": "测试"}
        assert service._validate_task_data(invalid_task) == False

        logger.info("✅ 任务数据验证测试通过")

    def test_parse_llm_response(self, mock_questions_processor):
        """测试4: 解析LLM响应"""
        from backend.services.checklist_service import ChecklistService

        service = ChecklistService()

        # 获取模拟响应
        mock_response = mock_questions_processor.process_question.return_value
        llm_answer = mock_response["answer"]

        # 解析响应
        tasks = service._parse_llm_response(llm_answer)

        assert len(tasks) == 3
        assert tasks[0]["title"] == "提交企业营业执照副本"
        assert tasks[0]["category"] == "资质文件准备"
        assert tasks[0]["priority"] == "high"

        logger.info(f"✅ LLM响应解析测试通过，提取了 {len(tasks)} 个任务")

    def test_create_task_from_data(self, sample_tasks_data):
        """测试5: 从数据创建Task对象"""
        from backend.services.checklist_service import ChecklistService
        from backend.models import TaskPriority, TaskStatus

        service = ChecklistService()
        checklist_id = str(uuid.uuid4())

        task = service._create_task_from_data(
            checklist_id=checklist_id,
            task_data=sample_tasks_data[0],
            order_index=0
        )

        assert task.checklist_id == checklist_id
        assert task.title == "提交企业营业执照副本"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.estimated_hours == 2
        assert task.order_index == 0

        logger.info("✅ Task对象创建测试通过")

    def test_build_extraction_prompt(self, mock_document):
        """测试6: 构建提取提示词"""
        from backend.services.checklist_service import ChecklistService

        service = ChecklistService()

        prompt = service._build_extraction_prompt(mock_document, None)

        assert "招投标文档" in prompt
        assert mock_document.title in prompt
        assert "资质文件准备" in prompt
        assert "技术方案编写" in prompt
        assert "JSON数组格式" in prompt

        logger.info("✅ 提取提示词构建测试通过")

    @patch('backend.services.checklist_service.get_db_session')
    @patch('backend.services.checklist_service.QuestionsProcessor')
    def test_generate_checklist_success(
        self,
        mock_processor_class,
        mock_db_session_func,
        mock_document,
        mock_questions_processor
    ):
        """测试7: 成功生成清单"""
        from backend.services.checklist_service import ChecklistService
        from backend.models import Checklist

        # 设置模拟
        mock_processor_class.return_value = mock_questions_processor

        mock_session = MagicMock()
        mock_db_session_func.return_value.__enter__.return_value = mock_session

        # 模拟数据库查询
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_document,  # 第一次查询：文档存在
            None  # 第二次查询：清单不存在
        ]

        # 执行测试
        service = ChecklistService()
        checklist_id = service.generate_checklist(
            document_id=mock_document.id,
            scenario_id="tender"
        )

        # 验证结果
        assert checklist_id is not None
        assert mock_session.add.called
        assert mock_session.commit.called

        logger.info(f"✅ 清单生成测试通过，checklist_id: {checklist_id}")

    @patch('backend.services.checklist_service.get_db_session')
    def test_get_checklist(self, mock_db_session_func, mock_document):
        """测试8: 获取清单详情"""
        from backend.services.checklist_service import ChecklistService
        from backend.models import Checklist, Task, TaskPriority, TaskStatus

        # 创建模拟清单和任务
        mock_checklist = Mock(spec=Checklist)
        mock_checklist.id = str(uuid.uuid4())
        mock_checklist.document_id = mock_document.id
        mock_checklist.scenario_id = "tender"
        mock_checklist.title = "测试清单"
        mock_checklist.description = "测试描述"
        mock_checklist.total_tasks = 2
        mock_checklist.completed_tasks = 0
        mock_checklist.generation_method = "auto"
        mock_checklist.created_at = datetime.now()
        mock_checklist.updated_at = datetime.now()

        mock_task1 = Mock(spec=Task)
        mock_task1.id = str(uuid.uuid4())
        mock_task1.title = "任务1"
        mock_task1.description = "描述1"
        mock_task1.category = "资质文件准备"
        mock_task1.priority = TaskPriority.HIGH
        mock_task1.status = TaskStatus.PENDING
        mock_task1.deadline = None
        mock_task1.estimated_hours = 2
        mock_task1.actual_hours = None
        mock_task1.assignee = None
        mock_task1.source_page = 5
        mock_task1.source_content = "原文内容"
        mock_task1.confidence_score = 95
        mock_task1.notes = None
        mock_task1.order_index = 0
        mock_task1.created_at = datetime.now()
        mock_task1.updated_at = datetime.now()
        mock_task1.completed_at = None

        # 设置模拟
        mock_session = MagicMock()
        mock_db_session_func.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter.return_value.first.return_value = mock_checklist
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task1]

        # 执行测试
        service = ChecklistService()
        result = service.get_checklist(mock_checklist.id)

        # 验证结果
        assert result is not None
        assert result["id"] == mock_checklist.id
        assert result["title"] == "测试清单"
        assert result["total_tasks"] == 2
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "任务1"

        logger.info("✅ 获取清单详情测试通过")

    @patch('backend.services.checklist_service.get_db_session')
    def test_update_task(self, mock_db_session_func):
        """测试9: 更新任务"""
        from backend.services.checklist_service import ChecklistService
        from backend.models import Task, TaskStatus, Checklist

        # 创建模拟任务
        mock_task = Mock(spec=Task)
        mock_task.id = str(uuid.uuid4())
        mock_task.checklist_id = str(uuid.uuid4())
        mock_task.status = TaskStatus.PENDING
        mock_task.updated_at = datetime.now()

        mock_checklist = Mock(spec=Checklist)
        mock_checklist.id = mock_task.checklist_id
        mock_checklist.completed_tasks = 0

        # 设置模拟
        mock_session = MagicMock()
        mock_db_session_func.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter.side_effect = [
            MagicMock(first=MagicMock(return_value=mock_task)),
            MagicMock(first=MagicMock(return_value=mock_checklist)),
            MagicMock(count=MagicMock(return_value=1))
        ]

        # 执行测试
        service = ChecklistService()
        updates = {
            "status": "completed",
            "notes": "任务已完成"
        }
        success = service.update_task(mock_task.id, updates)

        # 验证结果
        assert success == True
        assert mock_session.commit.called

        logger.info("✅ 更新任务测试通过")

    @patch('backend.services.checklist_service.get_db_session')
    def test_delete_checklist(self, mock_db_session_func):
        """测试10: 删除清单"""
        from backend.services.checklist_service import ChecklistService
        from backend.models import Checklist

        # 创建模拟清单
        mock_checklist = Mock(spec=Checklist)
        mock_checklist.id = str(uuid.uuid4())

        # 设置模拟
        mock_session = MagicMock()
        mock_db_session_func.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter.return_value.first.return_value = mock_checklist

        # 执行测试
        service = ChecklistService()
        success = service.delete_checklist(mock_checklist.id)

        # 验证结果
        assert success == True
        assert mock_session.delete.called
        assert mock_session.commit.called

        logger.info("✅ 删除清单测试通过")


# ==================== 集成测试 ====================

class TestChecklistAPI:
    """Checklist API 集成测试（需要运行后端服务）"""

    @pytest.mark.skip(reason="需要运行后端服务")
    def test_api_generate_checklist(self):
        """测试API: 生成清单"""
        import requests

        # 这里需要一个真实的document_id
        document_id = "test-document-id"

        response = requests.post(
            "http://localhost:8000/api/v2/checklist/generate",
            json={
                "document_id": document_id,
                "scenario_id": "tender"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "checklist_id" in data

        logger.info(f"✅ API生成清单测试通过")

    @pytest.mark.skip(reason="需要运行后端服务")
    def test_api_get_checklist(self):
        """测试API: 获取清单"""
        import requests

        # 这里需要一个真实的checklist_id
        checklist_id = "test-checklist-id"

        response = requests.get(
            f"http://localhost:8000/api/v2/checklist/{checklist_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data

        logger.info(f"✅ API获取清单测试通过")


# ==================== 运行测试 ====================

if __name__ == "__main__":
    logger.info("🧪 开始运行 ChecklistService 单元测试...")
    pytest.main([__file__, "-v", "-s"])

