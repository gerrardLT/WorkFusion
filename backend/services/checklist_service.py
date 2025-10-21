"""
任务清单服务
负责自动生成和管理招投标任务清单
"""

import sys
import uuid
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import get_db_session
from backend.models import Document, Checklist, Task, TaskPriority, TaskStatus
from src.questions_processing import QuestionsProcessor
from src.config import get_settings
import logging

logger = logging.getLogger(__name__)


class ChecklistService:
    """任务清单服务类"""

    def __init__(self):
        self.settings = get_settings()
        self.db = get_db_session

    def generate_checklist(
        self,
        document_id: str,
        scenario_id: str = "tender",
        generation_config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        为指定文档自动生成任务清单

        Args:
            document_id: 文档ID
            scenario_id: 场景ID（默认为招投标场景）
            generation_config: 生成配置参数

        Returns:
            生成的清单ID，失败返回None
        """
        try:
            logger.info(f"开始为文档 {document_id} 生成任务清单 (场景: {scenario_id})")

            with self.db() as db:
                # 1. 验证文档是否存在
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    logger.error(f"文档 {document_id} 不存在")
                    return None

                # 2. 检查是否已存在清单
                existing_checklist = db.query(Checklist).filter(
                    Checklist.document_id == document_id
                ).first()

                if existing_checklist:
                    logger.warning(f"文档 {document_id} 已存在清单，将更新现有清单")
                    checklist_id = existing_checklist.id
                    # 删除旧任务
                    db.query(Task).filter(Task.checklist_id == checklist_id).delete()
                else:
                    # 创建新清单
                    checklist_id = str(uuid.uuid4())
                    checklist = Checklist(
                        id=checklist_id,
                        document_id=document_id,
                        scenario_id=scenario_id,
                        title=f"{document.title} - 任务清单",
                        description="自动生成的招投标任务清单",
                        generation_method="auto",
                        generation_config=generation_config or {}
                    )
                    db.add(checklist)
                    db.commit()

                # 3. 初始化问题处理器
                questions_processor = QuestionsProcessor(
                    api_provider="dashscope",
                    scenario_id=scenario_id
                )

                # 4. 通过LLM提取任务项
                tasks_data = self._extract_tasks_from_document(
                    questions_processor,
                    document,
                    generation_config
                )

                if not tasks_data:
                    logger.error(f"未能从文档 {document_id} 提取任务项")
                    return None

                # 5. 保存任务项到数据库
                task_count = 0
                for idx, task_data in enumerate(tasks_data):
                    task = self._create_task_from_data(
                        checklist_id=checklist_id,
                        task_data=task_data,
                        order_index=idx
                    )
                    db.add(task)
                    task_count += 1

                # 6. 更新清单统计信息
                if existing_checklist:
                    existing_checklist.total_tasks = task_count
                    existing_checklist.updated_at = datetime.now()
                else:
                    checklist.total_tasks = task_count

                db.commit()

                logger.info(f"✅ 成功为文档 {document_id} 生成清单，包含 {task_count} 个任务")
                return checklist_id

        except Exception as e:
            logger.error(f"生成任务清单失败: {str(e)}", exc_info=True)
            return None

    def _extract_tasks_from_document(
        self,
        processor: QuestionsProcessor,
        document: Document,
        config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        通过LLM从文档中提取任务项

        Args:
            processor: 问题处理器
            document: 文档对象
            config: 生成配置

        Returns:
            任务项列表
        """
        try:
            # 构建提示词
            extraction_prompt = self._build_extraction_prompt(document, config)

            # 调用LLM
            logger.info(f"调用LLM提取任务项...")
            result = processor.process_question(
                question=extraction_prompt,
                use_agentic_rag=True
            )

            if not result or not result.get("success"):
                logger.error(f"LLM调用失败: {result.get('error') if result else 'No result'}")
                return []

            # 解析LLM返回的任务列表
            tasks = self._parse_llm_response(result.get("answer", ""))

            logger.info(f"成功提取 {len(tasks)} 个任务项")
            return tasks

        except Exception as e:
            logger.error(f"提取任务项失败: {str(e)}", exc_info=True)
            return []

    def _build_extraction_prompt(
        self,
        document: Document,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建任务提取提示词"""

        # 默认配置
        default_categories = [
            "资质文件准备",
            "技术方案编写",
            "商务文件准备",
            "时间节点管理",
            "合规性检查"
        ]

        categories = config.get("categories", default_categories) if config else default_categories

        prompt = f"""请仔细分析这份招投标文档《{document.title}》，提取所有需要完成的任务项。

请按照以下分类提取任务：
{chr(10).join([f'{i+1}. {cat}' for i, cat in enumerate(categories)])}

对于每个任务，请提供以下信息：
1. 任务标题（简洁明确）
2. 任务描述（详细说明）
3. 任务分类（从上述分类中选择）
4. 优先级（high/medium/low）
5. 截止时间（如果文档中有明确时间节点）
6. 预计工时（小时）
7. 来源页码（如果能确定）
8. 原文内容（相关的原文摘录）
9. 置信度（0-100，表示你对这个任务提取的确定程度）

请以JSON数组格式返回，每个任务为一个对象：
```json
[
  {{
    "title": "提交企业营业执照副本",
    "description": "需提供企业营业执照副本复印件，加盖公章",
    "category": "资质文件准备",
    "priority": "high",
    "deadline": "2025-11-01",
    "estimated_hours": 2,
    "source_page": 5,
    "source_content": "投标人须提供有效的企业营业执照副本...",
    "confidence_score": 95
  }},
  ...
]
```

注意：
- 只提取明确的、可执行的任务
- 优先级判断依据：涉及资质/合规的为high，技术核心内容为medium，辅助材料为low
- 如果文档中没有明确时间，deadline可以为null
- 确保至少提取10个任务项
- 按照任务的逻辑顺序排列

请开始分析并提取任务。"""

        return prompt

    def _parse_llm_response(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        解析LLM返回的任务列表

        Args:
            llm_response: LLM的响应文本

        Returns:
            解析后的任务列表
        """
        try:
            # 尝试提取JSON代码块
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = llm_response

            # 解析JSON
            tasks = json.loads(json_str)

            if not isinstance(tasks, list):
                logger.error("LLM返回的不是数组格式")
                return []

            # 验证和清理任务数据
            validated_tasks = []
            for task in tasks:
                if self._validate_task_data(task):
                    validated_tasks.append(task)

            return validated_tasks

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            logger.debug(f"原始响应: {llm_response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"解析LLM响应失败: {str(e)}", exc_info=True)
            return []

    def _validate_task_data(self, task_data: Dict[str, Any]) -> bool:
        """验证任务数据的完整性"""
        required_fields = ["title", "category"]

        for field in required_fields:
            if field not in task_data or not task_data[field]:
                logger.warning(f"任务缺少必需字段: {field}")
                return False

        return True

    def _create_task_from_data(
        self,
        checklist_id: str,
        task_data: Dict[str, Any],
        order_index: int
    ) -> Task:
        """
        从数据字典创建Task对象

        Args:
            checklist_id: 清单ID
            task_data: 任务数据
            order_index: 排序索引

        Returns:
            Task对象
        """
        # 解析优先级
        priority_str = task_data.get("priority", "medium").lower()
        priority = TaskPriority.MEDIUM
        if priority_str == "high":
            priority = TaskPriority.HIGH
        elif priority_str == "low":
            priority = TaskPriority.LOW

        # 解析截止时间
        deadline = None
        if task_data.get("deadline"):
            try:
                deadline = datetime.fromisoformat(task_data["deadline"])
            except (ValueError, TypeError):
                logger.warning(f"无效的截止时间格式: {task_data.get('deadline')}")

        # 创建Task对象
        task = Task(
            id=str(uuid.uuid4()),
            checklist_id=checklist_id,
            title=task_data["title"],
            description=task_data.get("description", ""),
            category=task_data["category"],
            priority=priority,
            status=TaskStatus.PENDING,
            deadline=deadline,
            estimated_hours=task_data.get("estimated_hours"),
            source_page=task_data.get("source_page"),
            source_content=task_data.get("source_content"),
            confidence_score=task_data.get("confidence_score", 80),
            order_index=order_index
        )

        return task

    def get_checklist(self, checklist_id: str) -> Optional[Dict[str, Any]]:
        """
        获取清单详情

        Args:
            checklist_id: 清单ID

        Returns:
            清单详情字典
        """
        try:
            with self.db() as db:
                checklist = db.query(Checklist).filter(Checklist.id == checklist_id).first()

                if not checklist:
                    return None

                # 获取所有任务
                tasks = db.query(Task).filter(
                    Task.checklist_id == checklist_id
                ).order_by(Task.order_index).all()

                return {
                    "id": checklist.id,
                    "document_id": checklist.document_id,
                    "scenario_id": checklist.scenario_id,
                    "title": checklist.title,
                    "description": checklist.description,
                    "total_tasks": checklist.total_tasks,
                    "completed_tasks": checklist.completed_tasks,
                    "generation_method": checklist.generation_method,
                    "created_at": checklist.created_at.isoformat(),
                    "updated_at": checklist.updated_at.isoformat(),
                    "tasks": [self._task_to_dict(task) for task in tasks]
                }

        except Exception as e:
            logger.error(f"获取清单失败: {str(e)}", exc_info=True)
            return None

    def update_task(
        self,
        task_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        更新任务

        Args:
            task_id: 任务ID
            updates: 更新字段

        Returns:
            是否成功
        """
        try:
            with self.db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()

                if not task:
                    logger.error(f"任务 {task_id} 不存在")
                    return False

                # 更新允许的字段
                allowed_fields = [
                    "title", "description", "priority", "status",
                    "deadline", "assignee", "notes", "estimated_hours", "actual_hours"
                ]

                old_status = task.status

                for field, value in updates.items():
                    if field in allowed_fields and hasattr(task, field):
                        # 特殊处理枚举类型
                        if field == "priority" and isinstance(value, str):
                            value = TaskPriority[value.upper()]
                        elif field == "status" and isinstance(value, str):
                            value = TaskStatus[value.upper()]
                        elif field == "deadline" and isinstance(value, str):
                            value = datetime.fromisoformat(value)

                        setattr(task, field, value)

                # 如果状态变为完成，记录完成时间
                if task.status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                    task.completed_at = datetime.now()

                    # 更新清单的完成任务数
                    checklist = db.query(Checklist).filter(
                        Checklist.id == task.checklist_id
                    ).first()
                    if checklist:
                        completed_count = db.query(Task).filter(
                            Task.checklist_id == task.checklist_id,
                            Task.status == TaskStatus.COMPLETED
                        ).count()
                        checklist.completed_tasks = completed_count

                task.updated_at = datetime.now()
                db.commit()

                logger.info(f"✅ 任务 {task_id} 更新成功")
                return True

        except Exception as e:
            logger.error(f"更新任务失败: {str(e)}", exc_info=True)
            return False

    def delete_checklist(self, checklist_id: str) -> bool:
        """
        删除清单（级联删除所有任务）

        Args:
            checklist_id: 清单ID

        Returns:
            是否成功
        """
        try:
            with self.db() as db:
                checklist = db.query(Checklist).filter(Checklist.id == checklist_id).first()

                if not checklist:
                    logger.error(f"清单 {checklist_id} 不存在")
                    return False

                db.delete(checklist)
                db.commit()

                logger.info(f"✅ 清单 {checklist_id} 删除成功")
                return True

        except Exception as e:
            logger.error(f"删除清单失败: {str(e)}", exc_info=True)
            return False

    def get_checklist_by_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        根据文档ID获取清单

        Args:
            document_id: 文档ID

        Returns:
            清单详情字典
        """
        try:
            with self.db() as db:
                checklist = db.query(Checklist).filter(
                    Checklist.document_id == document_id
                ).first()

                if not checklist:
                    return None

                return self.get_checklist(checklist.id)

        except Exception as e:
            logger.error(f"获取文档清单失败: {str(e)}", exc_info=True)
            return None

    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """将Task对象转换为字典"""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "priority": task.priority.value if task.priority else "medium",
            "status": task.status.value if task.status else "pending",
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "assignee": task.assignee,
            "source_page": task.source_page,
            "source_content": task.source_content,
            "confidence_score": task.confidence_score,
            "notes": task.notes,
            "order_index": task.order_index,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }


# 单例模式
_checklist_service_instance = None


def get_checklist_service() -> ChecklistService:
    """获取ChecklistService单例"""
    global _checklist_service_instance
    if _checklist_service_instance is None:
        _checklist_service_instance = ChecklistService()
    return _checklist_service_instance

