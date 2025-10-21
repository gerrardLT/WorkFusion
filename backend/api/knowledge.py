"""
知识库管理API路由
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from backend.services.knowledge_service import get_knowledge_service, KnowledgeService
from backend.models import KnowledgeCategory, KnowledgeStatus
from backend.middleware.auth_middleware import get_current_user, get_current_tenant, get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# ==================== Pydantic模型 ====================

class CreateKnowledgeRequest(BaseModel):
    """创建知识库项目请求"""
    scenario_id: str = Field(..., description="场景ID")
    category: KnowledgeCategory = Field(..., description="分类")
    title: str = Field(..., min_length=1, max_length=255, description="标题")
    description: Optional[str] = Field(None, description="描述")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    document_id: Optional[str] = Field(None, description="关联文档ID")
    issue_date: Optional[str] = Field(None, description="颁发日期 (YYYY-MM-DD)")
    expire_date: Optional[str] = Field(None, description="到期日期 (YYYY-MM-DD)")
    metadata: Optional[dict] = Field(default_factory=dict, description="附加元数据")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小")
    file_type: Optional[str] = Field(None, description="文件类型")
    created_by: Optional[str] = Field(None, description="创建人")


class UpdateKnowledgeRequest(BaseModel):
    """更新知识库项目请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    issue_date: Optional[str] = None
    expire_date: Optional[str] = None
    metadata: Optional[dict] = None
    status: Optional[KnowledgeStatus] = None
    updated_by: Optional[str] = None


class KnowledgeItemResponse(BaseModel):
    """知识库项目响应"""
    id: str
    scenario_id: str
    document_id: Optional[str]
    category: str
    title: str
    description: Optional[str]
    tags: List[str]
    status: str
    issue_date: Optional[str]
    expire_date: Optional[str]
    metadata: dict
    file_path: Optional[str]
    file_size: Optional[int]
    file_type: Optional[str]
    view_count: int
    reference_count: int
    created_at: str
    updated_at: str
    created_by: Optional[str]
    updated_by: Optional[str]


class KnowledgeListResponse(BaseModel):
    """知识库列表响应"""
    total: int
    items: List[KnowledgeItemResponse]


class KnowledgeStatsResponse(BaseModel):
    """知识库统计响应"""
    total: int
    by_category: dict
    by_status: dict
    expiring_soon: int


# ==================== API端点 ====================

@router.post("/", response_model=KnowledgeItemResponse)
async def create_knowledge_item(
    request: CreateKnowledgeRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    创建知识库项目

    需要认证，自动关联到当前租户和用户
    """
    try:
        # 转换日期字符串
        issue_date_obj = None
        expire_date_obj = None

        if request.issue_date:
            try:
                issue_date_obj = date.fromisoformat(request.issue_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="颁发日期格式错误，应为 YYYY-MM-DD")

        if request.expire_date:
            try:
                expire_date_obj = date.fromisoformat(request.expire_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="到期日期格式错误，应为 YYYY-MM-DD")

        print(f"[INFO] 用户 {current_user['username']} (租户: {tenant_id}) 创建知识库项目: {request.title}")

        item = knowledge_service.create_knowledge_item(
            scenario_id=request.scenario_id,
            category=request.category,
            title=request.title,
            description=request.description,
            tags=request.tags,
            document_id=request.document_id,
            issue_date=issue_date_obj,
            expire_date=expire_date_obj,
            metadata=request.metadata,
            file_path=request.file_path,
            file_size=request.file_size,
            file_type=request.file_type,
            created_by=user_id,  # 使用当前用户ID
            tenant_id=tenant_id  # 新增：租户ID（需要KnowledgeService支持）
        )

        if not item:
            raise HTTPException(status_code=500, detail="创建知识库项目失败")

        return _item_to_response(item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建知识库项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/", response_model=KnowledgeListResponse)
async def list_knowledge_items(
    scenario_id: str = Query(..., description="场景ID"),
    category: Optional[KnowledgeCategory] = Query(None, description="分类过滤"),
    status: Optional[KnowledgeStatus] = Query(None, description="状态过滤"),
    tags: Optional[str] = Query(None, description="标签过滤（逗号分隔）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    列出知识库项目

    需要认证，支持公开知识跨租户可见，私有知识仅租户内可见
    """
    try:
        tags_list = tags.split(",") if tags else None

        # TODO: 需要修改KnowledgeService以支持租户过滤和公开知识共享
        items = knowledge_service.list_knowledge_items(
            scenario_id=scenario_id,
            category=category,
            tags=tags_list,
            status=status,
            search_query=search,
            limit=limit,
            offset=offset,
            tenant_id=tenant_id  # 新增：租户过滤（需要KnowledgeService支持）
        )

        print(f"[INFO] 用户 {current_user['username']} 获取知识库列表: {len(items)} 个项目")

        return KnowledgeListResponse(
            total=len(items),
            items=[_item_to_response(item) for item in items]
        )

    except Exception as e:
        logger.error(f"列出知识库项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/search", response_model=KnowledgeListResponse)
async def search_knowledge_items(
    scenario_id: str = Query(..., description="场景ID"),
    q: str = Query(..., min_length=1, description="搜索关键词"),
    category: Optional[KnowledgeCategory] = Query(None, description="分类过滤"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    搜索知识库项目
    """
    try:
        items = knowledge_service.search_knowledge_items(
            scenario_id=scenario_id,
            query=q,
            category=category,
            limit=limit
        )

        return KnowledgeListResponse(
            total=len(items),
            items=[_item_to_response(item) for item in items]
        )

    except Exception as e:
        logger.error(f"搜索知识库项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats(
    scenario_id: str = Query(..., description="场景ID"),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    获取知识库统计信息
    """
    try:
        stats = knowledge_service.get_statistics(scenario_id)
        return KnowledgeStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/expiring", response_model=KnowledgeListResponse)
async def get_expiring_items(
    scenario_id: str = Query(..., description="场景ID"),
    days: int = Query(30, ge=1, le=365, description="天数阈值"),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    获取即将过期的项目
    """
    try:
        items = knowledge_service.get_expiring_items(scenario_id, days)

        return KnowledgeListResponse(
            total=len(items),
            items=[_item_to_response(item) for item in items]
        )

    except Exception as e:
        logger.error(f"获取即将过期项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge_item(
    item_id: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    获取知识库项目详情
    """
    try:
        item = knowledge_service.get_knowledge_item(item_id)

        if not item:
            raise HTTPException(status_code=404, detail="知识库项目未找到")

        return _item_to_response(item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.put("/{item_id}", response_model=KnowledgeItemResponse)
async def update_knowledge_item(
    item_id: str,
    request: UpdateKnowledgeRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    更新知识库项目

    需要认证，验证所有权
    """
    try:
        # 首先验证项目是否存在且属于当前租户
        existing_item = knowledge_service.get_knowledge_item(item_id)
        if not existing_item:
            raise HTTPException(status_code=404, detail="知识库项目未找到")

        # 验证所有权（租户隔离）
        if hasattr(existing_item, 'tenant_id') and existing_item.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="无权修改此知识库项目")

        updates = request.model_dump(exclude_unset=True)

        # 转换日期字符串
        if "issue_date" in updates and updates["issue_date"]:
            try:
                updates["issue_date"] = date.fromisoformat(updates["issue_date"])
            except ValueError:
                raise HTTPException(status_code=400, detail="颁发日期格式错误")

        if "expire_date" in updates and updates["expire_date"]:
            try:
                updates["expire_date"] = date.fromisoformat(updates["expire_date"])
            except ValueError:
                raise HTTPException(status_code=400, detail="到期日期格式错误")

        item = knowledge_service.update_knowledge_item(item_id, updates)

        if not item:
            raise HTTPException(status_code=404, detail="知识库项目未找到")

        print(f"[INFO] 用户 {current_user['username']} 更新知识库项目: {item_id}")

        return _item_to_response(item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新知识库项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{item_id}")
async def delete_knowledge_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    删除知识库项目

    需要认证，验证所有权
    """
    try:
        # 首先验证项目是否存在且属于当前租户
        existing_item = knowledge_service.get_knowledge_item(item_id)
        if not existing_item:
            raise HTTPException(status_code=404, detail="知识库项目未找到")

        # 验证所有权（租户隔离）
        if hasattr(existing_item, 'tenant_id') and existing_item.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="无权删除此知识库项目")

        success = knowledge_service.delete_knowledge_item(item_id)

        if not success:
            raise HTTPException(status_code=404, detail="知识库项目未找到")

        print(f"[INFO] 用户 {current_user['username']} 删除知识库项目: {item_id}")

        return {"success": True, "message": "删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ==================== 辅助函数 ====================

def _item_to_response(item) -> KnowledgeItemResponse:
    """将KnowledgeItem对象转换为响应模型"""
    return KnowledgeItemResponse(
        id=item.id,
        scenario_id=item.scenario_id,
        document_id=item.document_id,
        category=item.category.value,
        title=item.title,
        description=item.description,
        tags=item.tags or [],
        status=item.status.value,
        issue_date=item.issue_date.isoformat() if item.issue_date else None,
        expire_date=item.expire_date.isoformat() if item.expire_date else None,
        metadata=item.knowledge_metadata or {},
        file_path=item.file_path,
        file_size=item.file_size,
        file_type=item.file_type,
        view_count=item.view_count,
        reference_count=item.reference_count,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
        created_by=item.created_by,
        updated_by=item.updated_by
    )

