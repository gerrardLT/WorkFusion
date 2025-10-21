"""
任务清单API路由
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.checklist_service import get_checklist_service, ChecklistService
from backend.services.document_service import get_document_service, DocumentService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/checklist", tags=["checklist"])


# ==================== Pydantic 模型 ====================

class GenerateChecklistRequest(BaseModel):
    """生成清单请求"""
    document_id: str = Field(..., description="文档ID")
    scenario_id: str = Field(default="tender", description="场景ID")
    generation_config: Optional[Dict[str, Any]] = Field(default=None, description="生成配置")


class GenerateChecklistResponse(BaseModel):
    """生成清单响应"""
    success: bool
    checklist_id: Optional[str] = None
    message: str


class ChecklistResponse(BaseModel):
    """清单详情响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str


class UpdateTaskRequest(BaseModel):
    """更新任务请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None  # high, medium, low
    status: Optional[str] = None  # pending, in_progress, completed, cancelled
    deadline: Optional[str] = None  # ISO格式日期
    assignee: Optional[str] = None
    notes: Optional[str] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None


class UpdateTaskResponse(BaseModel):
    """更新任务响应"""
    success: bool
    message: str


class DeleteChecklistResponse(BaseModel):
    """删除清单响应"""
    success: bool
    message: str


# ==================== API 端点 ====================

@router.post("/generate", response_model=GenerateChecklistResponse)
async def generate_checklist(
    request: GenerateChecklistRequest,
    background_tasks: BackgroundTasks,
    checklist_service: ChecklistService = Depends(get_checklist_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    为指定文档生成任务清单

    - **document_id**: 文档ID
    - **scenario_id**: 场景ID（默认为tender）
    - **generation_config**: 可选的生成配置

    返回清单ID和生成状态
    """
    try:
        logger.info(f"收到生成清单请求: document_id={request.document_id}, scenario_id={request.scenario_id}")

        # 验证文档是否存在
        document = document_service.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"文档 {request.document_id} 不存在")

        # 检查文档是否已处理完成
        if document.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"文档尚未处理完成，当前状态: {document.get('status')}"
            )

        # 生成清单（同步执行，因为需要返回checklist_id）
        checklist_id = checklist_service.generate_checklist(
            document_id=request.document_id,
            scenario_id=request.scenario_id,
            generation_config=request.generation_config
        )

        if not checklist_id:
            return GenerateChecklistResponse(
                success=False,
                message="清单生成失败，请查看日志了解详情"
            )

        return GenerateChecklistResponse(
            success=True,
            checklist_id=checklist_id,
            message="清单生成成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成清单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成清单失败: {str(e)}")


@router.post("/documents/{document_id}/checklist", response_model=GenerateChecklistResponse)
async def generate_checklist_for_document(
    document_id: str,
    scenario_id: str = "tender",
    background_tasks: BackgroundTasks = None,
    checklist_service: ChecklistService = Depends(get_checklist_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    为指定文档生成任务清单（路径参数版本）

    - **document_id**: 文档ID（路径参数）
    - **scenario_id**: 场景ID（查询参数，默认为tender）

    返回清单ID和生成状态
    """
    request = GenerateChecklistRequest(
        document_id=document_id,
        scenario_id=scenario_id
    )
    return await generate_checklist(request, background_tasks, checklist_service, document_service)


@router.get("/{checklist_id}", response_model=ChecklistResponse)
async def get_checklist(
    checklist_id: str,
    checklist_service: ChecklistService = Depends(get_checklist_service)
):
    """
    获取清单详情

    - **checklist_id**: 清单ID

    返回清单详情，包括所有任务项
    """
    try:
        logger.info(f"获取清单详情: checklist_id={checklist_id}")

        checklist_data = checklist_service.get_checklist(checklist_id)

        if not checklist_data:
            raise HTTPException(status_code=404, detail=f"清单 {checklist_id} 不存在")

        return ChecklistResponse(
            success=True,
            data=checklist_data,
            message="获取清单成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取清单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取清单失败: {str(e)}")


@router.get("/documents/{document_id}/checklist", response_model=ChecklistResponse)
async def get_checklist_by_document(
    document_id: str,
    checklist_service: ChecklistService = Depends(get_checklist_service)
):
    """
    根据文档ID获取清单

    - **document_id**: 文档ID

    返回该文档的清单详情
    """
    try:
        logger.info(f"根据文档ID获取清单: document_id={document_id}")

        checklist_data = checklist_service.get_checklist_by_document(document_id)

        if not checklist_data:
            raise HTTPException(status_code=404, detail=f"文档 {document_id} 没有关联的清单")

        return ChecklistResponse(
            success=True,
            data=checklist_data,
            message="获取清单成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取清单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取清单失败: {str(e)}")


@router.put("/tasks/{task_id}", response_model=UpdateTaskResponse)
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    checklist_service: ChecklistService = Depends(get_checklist_service)
):
    """
    更新任务

    - **task_id**: 任务ID
    - **request**: 更新字段（只需提供要更新的字段）

    返回更新状态
    """
    try:
        logger.info(f"更新任务: task_id={task_id}")

        # 将请求转换为字典，排除None值
        updates = {k: v for k, v in request.dict().items() if v is not None}

        if not updates:
            raise HTTPException(status_code=400, detail="没有提供任何更新字段")

        success = checklist_service.update_task(task_id, updates)

        if not success:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在或更新失败")

        return UpdateTaskResponse(
            success=True,
            message="任务更新成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新任务失败: {str(e)}")


@router.delete("/{checklist_id}", response_model=DeleteChecklistResponse)
async def delete_checklist(
    checklist_id: str,
    checklist_service: ChecklistService = Depends(get_checklist_service)
):
    """
    删除清单（级联删除所有任务）

    - **checklist_id**: 清单ID

    返回删除状态
    """
    try:
        logger.info(f"删除清单: checklist_id={checklist_id}")

        success = checklist_service.delete_checklist(checklist_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"清单 {checklist_id} 不存在或删除失败")

        return DeleteChecklistResponse(
            success=True,
            message="清单删除成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除清单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除清单失败: {str(e)}")

