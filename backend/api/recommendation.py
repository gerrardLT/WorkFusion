# backend/api/recommendation.py
"""
项目推荐API接口
提供基于企业画像的智能项目推荐功能
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from backend.services.recommendation_service import get_recommendation_service, RecommendationService
from backend.models import ProjectStatus
from backend.middleware.auth_middleware import get_current_user, get_current_tenant, get_current_user_id

logger = logging.getLogger(__name__)

# ============= Pydantic模型定义 =============

class RecommendProjectsRequest(BaseModel):
    """为企业推荐项目请求"""
    company_id: str = Field(..., description="企业ID")
    min_score: float = Field(60.0, ge=0, le=100, description="最低匹配分数阈值")
    limit: int = Field(10, ge=1, le=100, description="返回数量限制")
    status: ProjectStatus = Field(ProjectStatus.ACTIVE, description="项目状态过滤")


class RecommendCompaniesRequest(BaseModel):
    """为项目推荐企业请求"""
    project_id: str = Field(..., description="项目ID")
    min_score: float = Field(60.0, ge=0, le=100, description="最低匹配分数阈值")
    limit: int = Field(10, ge=1, le=100, description="返回数量限制")


class BatchRecommendRequest(BaseModel):
    """批量推荐请求"""
    company_ids: List[str] = Field(..., description="企业ID列表")
    min_score: float = Field(70.0, ge=0, le=100, description="最低匹配分数阈值")
    limit_per_company: int = Field(5, ge=1, le=50, description="每个企业的推荐数量")
    status: ProjectStatus = Field(ProjectStatus.ACTIVE, description="项目状态过滤")


class MatchScoreRequest(BaseModel):
    """计算匹配度请求"""
    project_id: str = Field(..., description="项目ID")
    company_id: str = Field(..., description="企业ID")


class ProjectRecommendation(BaseModel):
    """项目推荐结果"""
    project: Dict[str, Any]
    match_score: float
    match_details: Dict[str, Any]
    days_until_deadline: int


class CompanyRecommendation(BaseModel):
    """企业推荐结果"""
    company: Dict[str, Any]
    match_score: float
    match_details: Dict[str, Any]


class RecommendProjectsResponse(BaseModel):
    """推荐项目响应"""
    success: bool
    company_id: str
    total_recommendations: int
    recommendations: List[ProjectRecommendation]


class RecommendCompaniesResponse(BaseModel):
    """推荐企业响应"""
    success: bool
    project_id: str
    total_recommendations: int
    recommendations: List[CompanyRecommendation]


class BatchRecommendResponse(BaseModel):
    """批量推荐响应"""
    success: bool
    total_companies: int
    total_recommendations: int
    results: Dict[str, List[ProjectRecommendation]]  # company_id -> recommendations


class MatchScoreResponse(BaseModel):
    """匹配度计算响应"""
    success: bool
    project_id: str
    company_id: str
    match_score: float
    match_details: Dict[str, Any]


# ============= API路由 =============

router = APIRouter(prefix="/recommendation", tags=["recommendation"])


@router.post("/projects", response_model=RecommendProjectsResponse)
async def recommend_projects_api(
    request: RecommendProjectsRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    rec_service: RecommendationService = Depends(get_recommendation_service)
):
    """
    为企业推荐高匹配度项目

    需要认证，根据租户配置决定推荐范围
    """
    logger.info(f"用户 {current_user['username']} (租户: {tenant_id}) 为企业 {request.company_id} 推荐项目")

    try:
        # TODO: 根据租户配置决定推荐范围
        # 如果配置为"shared"，推荐所有项目；如果为"private"，只推荐本租户项目

        recommendations = rec_service.recommend_projects_for_company(
            company_id=request.company_id,
            min_score=request.min_score,
            limit=request.limit,
            status=request.status,
            tenant_id=tenant_id  # 新增：租户过滤（根据配置决定是否使用）
        )

        return RecommendProjectsResponse(
            success=True,
            company_id=request.company_id,
            total_recommendations=len(recommendations),
            recommendations=[ProjectRecommendation(**rec) for rec in recommendations]
        )
    except Exception as e:
        logger.error(f"推荐项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.post("/companies", response_model=RecommendCompaniesResponse)
async def recommend_companies_api(
    request: RecommendCompaniesRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    rec_service: RecommendationService = Depends(get_recommendation_service)
):
    """
    为项目推荐高匹配度企业

    需要认证，根据租户配置决定推荐范围
    """
    logger.info(f"用户 {current_user['username']} (租户: {tenant_id}) 为项目 {request.project_id} 推荐企业")

    try:
        # TODO: 根据租户配置决定推荐范围
        # 如果配置为"shared"，推荐所有企业；如果为"private"，只推荐本租户企业

        recommendations = rec_service.recommend_companies_for_project(
            project_id=request.project_id,
            min_score=request.min_score,
            limit=request.limit,
            tenant_id=tenant_id  # 新增：租户过滤（根据配置决定是否使用）
        )

        return RecommendCompaniesResponse(
            success=True,
            project_id=request.project_id,
            total_recommendations=len(recommendations),
            recommendations=[CompanyRecommendation(**rec) for rec in recommendations]
        )
    except Exception as e:
        logger.error(f"推荐企业失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.post("/batch", response_model=BatchRecommendResponse)
async def batch_recommend_api(
    request: BatchRecommendRequest,
    background_tasks: BackgroundTasks,
    rec_service: RecommendationService = Depends(get_recommendation_service)
):
    """
    批量为多个企业推荐项目
    适用于定时任务批量推送场景
    """
    logger.info(f"批量推荐：{len(request.company_ids)} 个企业")

    try:
        results = {}
        total_recommendations = 0

        for company_id in request.company_ids:
            recommendations = rec_service.recommend_projects_for_company(
                company_id=company_id,
                min_score=request.min_score,
                limit=request.limit_per_company,
                status=request.status
            )

            if recommendations:
                results[company_id] = [ProjectRecommendation(**rec) for rec in recommendations]
                total_recommendations += len(recommendations)

        logger.info(f"批量推荐完成：共 {total_recommendations} 条推荐")

        return BatchRecommendResponse(
            success=True,
            total_companies=len(request.company_ids),
            total_recommendations=total_recommendations,
            results=results
        )
    except Exception as e:
        logger.error(f"批量推荐失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量推荐失败: {str(e)}")


@router.post("/match-score", response_model=MatchScoreResponse)
async def calculate_match_score_api(
    request: MatchScoreRequest,
    rec_service: RecommendationService = Depends(get_recommendation_service)
):
    """
    计算指定项目与企业的匹配度
    """
    logger.info(f"计算匹配度：项目 {request.project_id} vs 企业 {request.company_id}")

    try:
        from backend.database import get_db_session
        from backend.models import Project, Company

        db = get_db_session()
        try:
            project = db.query(Project).filter(Project.id == request.project_id).first()
            company = db.query(Company).filter(Company.id == request.company_id).first()

            if not project:
                raise HTTPException(status_code=404, detail=f"项目 {request.project_id} 未找到")
            if not company:
                raise HTTPException(status_code=404, detail=f"企业 {request.company_id} 未找到")

            score, details = rec_service.calculate_match_score(project, company)

            return MatchScoreResponse(
                success=True,
                project_id=request.project_id,
                company_id=request.company_id,
                match_score=score,
                match_details=details
            )
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算匹配度失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/projects/{company_id}", response_model=RecommendProjectsResponse)
async def get_recommendations_for_company_api(
    company_id: str,
    min_score: float = Query(60.0, ge=0, le=100, description="最低匹配分数"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    status: ProjectStatus = Query(ProjectStatus.ACTIVE, description="项目状态"),
    rec_service: RecommendationService = Depends(get_recommendation_service)
):
    """
    获取企业的推荐项目列表（GET方式）
    """
    logger.info(f"GET 推荐项目：企业 {company_id}")

    try:
        recommendations = rec_service.recommend_projects_for_company(
            company_id=company_id,
            min_score=min_score,
            limit=limit,
            status=status
        )

        return RecommendProjectsResponse(
            success=True,
            company_id=company_id,
            total_recommendations=len(recommendations),
            recommendations=[ProjectRecommendation(**rec) for rec in recommendations]
        )
    except Exception as e:
        logger.error(f"获取推荐失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")


@router.get("/companies/{project_id}", response_model=RecommendCompaniesResponse)
async def get_recommendations_for_project_api(
    project_id: str,
    min_score: float = Query(60.0, ge=0, le=100, description="最低匹配分数"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    rec_service: RecommendationService = Depends(get_recommendation_service)
):
    """
    获取项目的推荐企业列表（GET方式）
    """
    logger.info(f"GET 推荐企业：项目 {project_id}")

    try:
        recommendations = rec_service.recommend_companies_for_project(
            project_id=project_id,
            min_score=min_score,
            limit=limit
        )

        return RecommendCompaniesResponse(
            success=True,
            project_id=project_id,
            total_recommendations=len(recommendations),
            recommendations=[CompanyRecommendation(**rec) for rec in recommendations]
        )
    except Exception as e:
        logger.error(f"获取推荐失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")

