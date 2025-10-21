"""
内容生成API
提供基于LLM的标书章节内容生成功能
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.services.content_service import (
    ContentService,
    ContentType,
    get_content_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generate"])


# ============= Pydantic模型定义 =============

class ContentGenerationRequest(BaseModel):
    """内容生成请求"""
    content_type: ContentType = Field(..., description="内容类型")
    project_name: Optional[str] = Field(None, description="项目名称")
    requirements: Optional[str] = Field(None, description="特殊要求")
    use_knowledge_base: bool = Field(True, description="是否使用知识库内容")
    scenario_id: str = Field("tender", description="场景ID")

    class Config:
        json_schema_extra = {
            "example": {
                "content_type": "company_intro",
                "project_name": "某电力公司智能电网建设项目",
                "requirements": "重点突出公司在智能电网领域的经验",
                "use_knowledge_base": True,
                "scenario_id": "tender"
            }
        }


class ContentGenerationResponse(BaseModel):
    """内容生成响应"""
    success: bool
    content: Optional[str] = None
    content_type: str
    project_name: Optional[str] = None
    has_context: bool = False
    word_count: int = 0
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "content": "某某公司成立于2010年，是一家专业从事...",
                "content_type": "company_intro",
                "project_name": "某电力公司智能电网建设项目",
                "has_context": True,
                "word_count": 856,
                "error": None
            }
        }


class ContentTypeListResponse(BaseModel):
    """内容类型列表响应"""
    content_types: list[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "content_types": [
                    {"value": "company_intro", "label": "公司简介"},
                    {"value": "technical_solution", "label": "技术方案"}
                ]
            }
        }


# ============= API端点 =============

@router.post("/content", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    content_service: ContentService = Depends(get_content_service)
):
    """
    生成标书章节内容

    根据指定的内容类型，自动生成标书章节初稿。
    可选择是否使用知识库中的相关信息作为参考。

    Args:
        request: 内容生成请求
        content_service: 内容生成服务

    Returns:
        生成的内容
    """
    try:
        logger.info(f"📝 收到内容生成请求: {request.content_type.value}")

        # 调用服务生成内容
        result = await content_service.generate_content(
            content_type=request.content_type,
            project_name=request.project_name,
            requirements=request.requirements,
            use_knowledge_base=request.use_knowledge_base
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"内容生成失败: {result.get('error', '未知错误')}"
            )

        return ContentGenerationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] 内容生成API错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"内容生成失败: {str(e)}"
        )


@router.get("/content-types", response_model=ContentTypeListResponse)
async def get_content_types():
    """
    获取支持的内容类型列表

    返回所有可生成的标书章节类型。

    Returns:
        内容类型列表
    """
    content_types = [
        {"value": ContentType.COMPANY_INTRO.value, "label": "公司简介", "icon": "🏢"},
        {"value": ContentType.TECHNICAL_SOLUTION.value, "label": "技术方案", "icon": "🔧"},
        {"value": ContentType.SERVICE_COMMITMENT.value, "label": "服务承诺", "icon": "🤝"},
        {"value": ContentType.QUALITY_ASSURANCE.value, "label": "质量保证措施", "icon": "[OK]"},
        {"value": ContentType.SAFETY_MEASURES.value, "label": "安全生产措施", "icon": "🛡️"},
        {"value": ContentType.PROJECT_EXPERIENCE.value, "label": "项目经验", "icon": "📊"},
        {"value": ContentType.TEAM_INTRODUCTION.value, "label": "团队介绍", "icon": "👥"},
    ]

    return ContentTypeListResponse(content_types=content_types)


@router.post("/regenerate", response_model=ContentGenerationResponse)
async def regenerate_content(
    request: ContentGenerationRequest,
    content_service: ContentService = Depends(get_content_service)
):
    """
    重新生成内容

    与generate_content功能相同，但语义上表示"重新生成"。
    可用于用户对生成结果不满意时重新生成。

    Args:
        request: 内容生成请求
        content_service: 内容生成服务

    Returns:
        重新生成的内容
    """
    logger.info(f"🔄 重新生成内容: {request.content_type.value}")
    return await generate_content(request, content_service)

