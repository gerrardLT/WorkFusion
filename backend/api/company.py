# backend/api/company.py
"""
企业画像API接口
提供企业信息的增删改查、搜索等功能
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from backend.services.company_service import get_company_service, CompanyService
from backend.models import Company, CompanyScale
from backend.middleware.auth_middleware import get_current_user, get_current_tenant, get_current_user_id

logger = logging.getLogger(__name__)

# ============= Pydantic模型定义 =============

class QualificationModel(BaseModel):
    """资质模型"""
    name: str = Field(..., description="资质名称")
    level: Optional[str] = Field(None, description="资质等级")
    number: Optional[str] = Field(None, description="证书编号")
    expire_date: Optional[str] = Field(None, description="过期日期 (YYYY-MM-DD)")


class CapabilitiesModel(BaseModel):
    """能力模型"""
    fields: Optional[List[str]] = Field(None, description="擅长领域")
    advantages: Optional[List[str]] = Field(None, description="技术优势")
    certifications: Optional[List[str]] = Field(None, description="企业认证")
    patents: Optional[int] = Field(None, description="专利数量")
    projects_completed: Optional[int] = Field(None, description="完成项目数")


class MajorProjectModel(BaseModel):
    """重大项目模型"""
    name: str
    amount: int  # 万元
    year: int
    client: str


class AchievementsModel(BaseModel):
    """业绩模型"""
    total_projects: Optional[int] = Field(None, description="总项目数")
    total_amount: Optional[int] = Field(None, description="总金额（万元）")
    average_amount: Optional[int] = Field(None, description="平均金额（万元）")
    success_rate: Optional[float] = Field(None, description="中标率")
    major_projects: Optional[List[MajorProjectModel]] = Field(None, description="重大项目列表")
    clients: Optional[List[str]] = Field(None, description="主要客户")


class BudgetRangeModel(BaseModel):
    """预算范围模型"""
    min: int = Field(..., description="最小预算（万元）")
    max: int = Field(..., description="最大预算（万元）")


class PreferencesModel(BaseModel):
    """偏好设置模型"""
    project_types: Optional[List[str]] = Field(None, description="项目类型")
    contract_types: Optional[List[str]] = Field(None, description="合同类型")
    min_margin: Optional[float] = Field(None, description="最低利润率")
    payment_terms: Optional[List[str]] = Field(None, description="付款条款")
    avoid_keywords: Optional[List[str]] = Field(None, description="排除关键词")


class CreateCompanyRequest(BaseModel):
    """创建企业请求"""
    name: str = Field(..., min_length=1, description="企业名称")
    description: Optional[str] = Field(None, description="企业简介")
    scale: CompanyScale = Field(CompanyScale.MEDIUM, description="企业规模")
    founded_year: Optional[int] = Field(None, ge=1900, le=2100, description="成立年份")
    employee_count: Optional[int] = Field(None, ge=0, description="员工数量")
    registered_capital: Optional[int] = Field(None, ge=0, description="注册资本（万元）")

    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None

    qualifications: Optional[List[QualificationModel]] = None
    capabilities: Optional[CapabilitiesModel] = None
    achievements: Optional[AchievementsModel] = None
    target_areas: Optional[List[str]] = None
    target_industries: Optional[List[str]] = None
    budget_range: Optional[BudgetRangeModel] = None
    preferences: Optional[PreferencesModel] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateCompanyRequest(BaseModel):
    """更新企业请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    scale: Optional[CompanyScale] = None
    founded_year: Optional[int] = Field(None, ge=1900, le=2100)
    employee_count: Optional[int] = Field(None, ge=0)
    registered_capital: Optional[int] = Field(None, ge=0)

    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None

    qualifications: Optional[List[QualificationModel]] = None
    capabilities: Optional[CapabilitiesModel] = None
    achievements: Optional[AchievementsModel] = None
    target_areas: Optional[List[str]] = None
    target_industries: Optional[List[str]] = None
    budget_range: Optional[BudgetRangeModel] = None
    preferences: Optional[PreferencesModel] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CompanyResponse(BaseModel):
    """企业响应模型"""
    id: str
    name: str
    description: Optional[str] = None
    scale: str
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    registered_capital: Optional[int] = None

    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None

    qualifications: List[Dict[str, Any]]
    capabilities: Dict[str, Any]
    achievements: Dict[str, Any]
    target_areas: List[str]
    target_industries: List[str]
    budget_range: Dict[str, Any]
    preferences: Dict[str, Any]
    metadata: Dict[str, Any]

    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """企业列表响应"""
    companies: List[CompanyResponse]
    total_count: int
    limit: int
    offset: int


class CompanyStatsResponse(BaseModel):
    """企业统计响应"""
    total_companies: int
    scale_distribution: Dict[str, int]
    active_companies: int


class AddQualificationRequest(BaseModel):
    """添加资质请求"""
    qualification: QualificationModel


# ============= API路由 =============

router = APIRouter(prefix="/company", tags=["company"])


@router.post("/", response_model=CompanyResponse)
async def create_company_api(
    request: CreateCompanyRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    user_id: str = Depends(get_current_user_id),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    创建企业画像

    需要认证，根据租户配置决定是否隔离数据
    """
    logger.info(f"用户 {current_user['username']} (租户: {tenant_id}) 创建企业: {request.name}")

    # TODO: 从租户配置中获取data_sharing.company设置
    # 当前假设支持租户隔离，实际需要查询租户配置

    company = company_service.create_company(
        name=request.name,
        description=request.description,
        scale=request.scale,
        founded_year=request.founded_year,
        employee_count=request.employee_count,
        registered_capital=request.registered_capital,
        contact_person=request.contact_person,
        contact_phone=request.contact_phone,
        contact_email=request.contact_email,
        address=request.address,
        website=request.website,
        qualifications=[q.model_dump() for q in request.qualifications] if request.qualifications else None,
        capabilities=request.capabilities.model_dump() if request.capabilities else None,
        achievements=request.achievements.model_dump() if request.achievements else None,
        target_areas=request.target_areas,
        target_industries=request.target_industries,
        budget_range=request.budget_range.model_dump() if request.budget_range else None,
        preferences=request.preferences.model_dump() if request.preferences else None,
        metadata=request.metadata,
        tenant_id=tenant_id,  # 新增：租户ID（根据配置决定是否使用）
        created_by=user_id    # 新增：创建者ID
    )

    if company:
        return CompanyResponse(**company.to_dict())
    raise HTTPException(status_code=400, detail="创建企业失败，可能企业名称已存在")


@router.get("/", response_model=CompanyListResponse)
async def list_companies_api(
    scale: Optional[CompanyScale] = Query(None, description="企业规模过滤"),
    target_area: Optional[str] = Query(None, description="目标区域过滤"),
    target_industry: Optional[str] = Query(None, description="目标行业过滤"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="关键词搜索"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    列出企业列表，支持多种过滤和分页

    需要认证，根据租户配置决定是否按租户过滤
    """
    # TODO: 从租户配置中获取data_sharing.company设置
    # 如果配置为"shared"，则显示所有企业；如果为"private"，则只显示本租户企业

    companies, total_count = company_service.list_companies(
        scale=scale,
        target_area=target_area,
        target_industry=target_industry,
        is_active=is_active,
        search_query=search,
        limit=limit,
        offset=offset,
        tenant_id=tenant_id  # 新增：租户过滤（根据配置决定是否使用）
    )

    logger.info(f"用户 {current_user['username']} 获取企业列表: {len(companies)} 个企业")

    return CompanyListResponse(
        companies=[CompanyResponse(**c.to_dict()) for c in companies],
        total_count=total_count,
        limit=limit,
        offset=offset
    )


@router.get("/search", response_model=List[CompanyResponse])
async def search_companies_api(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    搜索企业
    """
    companies = company_service.search_companies(query=q, limit=limit)
    return [CompanyResponse(**c.to_dict()) for c in companies]


@router.get("/stats", response_model=CompanyStatsResponse)
async def get_company_stats_api(
    company_service: CompanyService = Depends(get_company_service)
):
    """
    获取企业统计信息
    """
    stats = company_service.get_statistics()
    return CompanyStatsResponse(**stats)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_api(
    company_id: str,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    获取企业详情

    需要认证，根据租户配置决定访问权限
    """
    # TODO: 根据租户配置验证访问权限
    company = company_service.get_company(company_id, tenant_id=tenant_id)
    if company:
        return CompanyResponse(**company.to_dict())
    raise HTTPException(status_code=404, detail="企业未找到")


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company_api(
    company_id: str,
    request: UpdateCompanyRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    更新企业信息

    需要认证，验证所有权（如果启用租户隔离）
    """
    # 首先验证企业是否存在且有权限访问
    existing_company = company_service.get_company(company_id, tenant_id=tenant_id)
    if not existing_company:
        raise HTTPException(status_code=404, detail="企业未找到")

    # TODO: 根据租户配置验证修改权限
    # 如果配置为"private"，需要验证所有权

    updates = request.model_dump(exclude_unset=True)

    # 转换嵌套模型
    if "qualifications" in updates and updates["qualifications"]:
        updates["qualifications"] = [q if isinstance(q, dict) else q.model_dump() for q in updates["qualifications"]]
    if "capabilities" in updates and updates["capabilities"]:
        updates["capabilities"] = updates["capabilities"] if isinstance(updates["capabilities"], dict) else updates["capabilities"].model_dump()
    if "achievements" in updates and updates["achievements"]:
        updates["achievements"] = updates["achievements"] if isinstance(updates["achievements"], dict) else updates["achievements"].model_dump()
    if "budget_range" in updates and updates["budget_range"]:
        updates["budget_range"] = updates["budget_range"] if isinstance(updates["budget_range"], dict) else updates["budget_range"].model_dump()
    if "preferences" in updates and updates["preferences"]:
        updates["preferences"] = updates["preferences"] if isinstance(updates["preferences"], dict) else updates["preferences"].model_dump()

    updated_company = company_service.update_company(company_id, updates)
    if updated_company:
        logger.info(f"用户 {current_user['username']} 更新企业: {company_id}")
        return CompanyResponse(**updated_company.to_dict())
    raise HTTPException(status_code=500, detail="更新企业失败或企业未找到")


@router.delete("/{company_id}")
async def delete_company_api(
    company_id: str,
    hard_delete: bool = Query(False, description="是否彻底删除"),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    company_service: CompanyService = Depends(get_company_service)
):
    """
    删除企业（默认软删除，可选物理删除）

    需要认证，验证所有权（如果启用租户隔离）
    """
    # 首先验证企业是否存在且有权限访问
    existing_company = company_service.get_company(company_id, tenant_id=tenant_id)
    if not existing_company:
        raise HTTPException(status_code=404, detail="企业未找到")

    # TODO: 根据租户配置验证删除权限
    # 如果配置为"private"，需要验证所有权

    if hard_delete:
        success = company_service.hard_delete_company(company_id)
    else:
        success = company_service.delete_company(company_id)

    if success:
        logger.info(f"用户 {current_user['username']} 删除企业: {company_id} (hard_delete={hard_delete})")
        return {"success": True, "message": "企业已删除"}
    raise HTTPException(status_code=500, detail="删除企业失败或企业未找到")


@router.post("/{company_id}/qualifications", response_model=CompanyResponse)
async def add_qualification_api(
    company_id: str,
    request: AddQualificationRequest,
    company_service: CompanyService = Depends(get_company_service)
):
    """
    为企业添加资质
    """
    company = company_service.add_qualification(
        company_id,
        request.qualification.model_dump()
    )
    if company:
        return CompanyResponse(**company.to_dict())
    raise HTTPException(status_code=500, detail="添加资质失败或企业未找到")


@router.delete("/{company_id}/qualifications/{qualification_name}", response_model=CompanyResponse)
async def remove_qualification_api(
    company_id: str,
    qualification_name: str,
    company_service: CompanyService = Depends(get_company_service)
):
    """
    移除企业资质
    """
    company = company_service.remove_qualification(company_id, qualification_name)
    if company:
        return CompanyResponse(**company.to_dict())
    raise HTTPException(status_code=500, detail="移除资质失败或企业未找到")

