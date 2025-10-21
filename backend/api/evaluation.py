# backend/api/evaluation.py
"""
项目评估报告API
提供评估报告的生成、查询、删除等功能
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.services.evaluation_service import get_evaluation_service, EvaluationService
from backend.services.pdf_generator import get_pdf_generator, PDFGenerator
from backend.models import EvaluationReport, EvaluationStatus, RecommendationLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


# ============= Pydantic Models =============

class GenerateReportRequest(BaseModel):
    """生成评估报告请求"""
    project_id: str = Field(..., description="项目ID")
    company_id: str = Field(..., description="企业ID")
    scenario_id: str = Field(default="tender", description="场景ID")


class GenerateReportResponse(BaseModel):
    """生成评估报告响应"""
    success: bool
    message: str
    report_id: Optional[str] = None


class ReportSummaryResponse(BaseModel):
    """评估报告摘要响应"""
    id: str
    project_id: str
    company_id: str
    scenario_id: str
    title: str
    status: str
    overall_score: Optional[float] = None
    recommendation_level: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ReportDetailResponse(BaseModel):
    """评估报告详情响应"""
    id: str
    project_id: str
    company_id: str
    scenario_id: str
    title: str
    status: str
    overall_score: Optional[float] = None
    recommendation_level: Optional[str] = None
    conclusion: Optional[str] = None
    project_summary: dict
    qualification_analysis: dict
    timeline_analysis: dict
    historical_analysis: dict
    risk_summary: dict
    match_details: dict
    recommendations: List[dict]
    metadata: dict
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """评估报告列表响应"""
    reports: List[ReportSummaryResponse]
    total_count: int
    limit: int
    offset: int


# ============= API Endpoints =============

@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report_api(
    request: GenerateReportRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    生成项目评估报告（同步）

    - **project_id**: 项目ID
    - **company_id**: 企业ID
    - **scenario_id**: 场景ID，默认为tender

    返回生成的报告ID
    """
    logger.info(f"收到评估报告生成请求：项目 {request.project_id} vs 企业 {request.company_id}")

    report = evaluation_service.generate_report(
        project_id=request.project_id,
        company_id=request.company_id,
        scenario_id=request.scenario_id
    )

    if report:
        return GenerateReportResponse(
            success=True,
            message="评估报告生成成功",
            report_id=report.id
        )
    else:
        raise HTTPException(status_code=500, detail="评估报告生成失败")


@router.post("/generate-async", response_model=GenerateReportResponse)
async def generate_report_async_api(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    异步生成项目评估报告

    - **project_id**: 项目ID
    - **company_id**: 企业ID
    - **scenario_id**: 场景ID，默认为tender

    立即返回，报告将在后台生成
    """
    logger.info(f"收到异步评估报告生成请求：项目 {request.project_id} vs 企业 {request.company_id}")

    # 添加后台任务
    background_tasks.add_task(
        evaluation_service.generate_report,
        project_id=request.project_id,
        company_id=request.company_id,
        scenario_id=request.scenario_id
    )

    return GenerateReportResponse(
        success=True,
        message="评估报告生成任务已提交到后台"
    )


@router.get("/reports/{report_id}", response_model=ReportDetailResponse)
async def get_report_api(
    report_id: str,
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    获取评估报告详情

    - **report_id**: 报告ID

    返回完整的报告内容
    """
    report = evaluation_service.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="评估报告未找到")

    return ReportDetailResponse(
        id=report.id,
        project_id=report.project_id,
        company_id=report.company_id,
        scenario_id=report.scenario_id,
        title=report.title,
        status=report.status,
        overall_score=report.overall_score,
        recommendation_level=report.recommendation_level,
        conclusion=report.conclusion,
        project_summary=report.project_summary or {},
        qualification_analysis=report.qualification_analysis or {},
        timeline_analysis=report.timeline_analysis or {},
        historical_analysis=report.historical_analysis or {},
        risk_summary=report.risk_summary or {},
        match_details=report.match_details or {},
        recommendations=report.recommendations or [],
        metadata=report.evaluation_metadata or {},
        created_at=report.created_at.isoformat() if report.created_at else "",
        updated_at=report.updated_at.isoformat() if report.updated_at else ""
    )


@router.get("/reports", response_model=ReportListResponse)
async def list_reports_api(
    company_id: Optional[str] = Query(None, description="按企业ID筛选"),
    project_id: Optional[str] = Query(None, description="按项目ID筛选"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    列出评估报告

    - **company_id**: 可选，按企业ID筛选
    - **project_id**: 可选，按项目ID筛选
    - **limit**: 每页数量，默认20
    - **offset**: 偏移量，默认0

    返回报告列表和总数
    """
    reports, total_count = evaluation_service.list_reports(
        company_id=company_id,
        project_id=project_id,
        limit=limit,
        offset=offset
    )

    report_summaries = []
    for report in reports:
        report_summaries.append(ReportSummaryResponse(
            id=report.id,
            project_id=report.project_id,
            company_id=report.company_id,
            scenario_id=report.scenario_id,
            title=report.title,
            status=report.status,
            overall_score=report.overall_score,
            recommendation_level=report.recommendation_level,
            created_at=report.created_at.isoformat() if report.created_at else "",
            updated_at=report.updated_at.isoformat() if report.updated_at else ""
        ))

    return ReportListResponse(
        reports=report_summaries,
        total_count=total_count,
        limit=limit,
        offset=offset
    )


@router.delete("/reports/{report_id}")
async def delete_report_api(
    report_id: str,
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    删除评估报告

    - **report_id**: 报告ID

    返回删除结果
    """
    success = evaluation_service.delete_report(report_id)

    if success:
        return {"success": True, "message": "评估报告已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除评估报告失败或报告未找到")


@router.get("/projects/{project_id}/evaluate/{company_id}", response_model=ReportDetailResponse)
async def quick_evaluate_api(
    project_id: str,
    company_id: str,
    scenario_id: str = Query("tender", description="场景ID"),
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    快速评估接口：直接生成并返回评估报告

    - **project_id**: 项目ID
    - **company_id**: 企业ID
    - **scenario_id**: 场景ID，默认为tender

    一步完成生成和获取，适合前端快速展示
    """
    logger.info(f"收到快速评估请求：项目 {project_id} vs 企业 {company_id}")

    report = evaluation_service.generate_report(
        project_id=project_id,
        company_id=company_id,
        scenario_id=scenario_id
    )

    if not report:
        raise HTTPException(status_code=500, detail="评估报告生成失败")

    return ReportDetailResponse(
        id=report.id,
        project_id=report.project_id,
        company_id=report.company_id,
        scenario_id=report.scenario_id,
        title=report.title,
        status=report.status,
        overall_score=report.overall_score,
        recommendation_level=report.recommendation_level,
        conclusion=report.conclusion,
        project_summary=report.project_summary or {},
        qualification_analysis=report.qualification_analysis or {},
        timeline_analysis=report.timeline_analysis or {},
        historical_analysis=report.historical_analysis or {},
        risk_summary=report.risk_summary or {},
        match_details=report.match_details or {},
        recommendations=report.recommendations or [],
        metadata=report.evaluation_metadata or {},
        created_at=report.created_at.isoformat() if report.created_at else "",
        updated_at=report.updated_at.isoformat() if report.updated_at else ""
    )


# ============= PDF Export Endpoints =============

@router.get("/reports/{report_id}/export/pdf")
async def export_report_to_pdf(
    report_id: str,
    watermark: Optional[str] = Query(None, description="水印文字"),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    导出评估报告为PDF

    - **report_id**: 报告ID
    - **watermark**: 可选的水印文字

    返回PDF文件流
    """
    # 获取报告
    report = evaluation_service.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="评估报告未找到")

    if report.status != EvaluationStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="报告尚未完成，无法导出")

    try:
        # 生成PDF
        pdf_bytes = pdf_generator.generate_from_report(
            report=report,
            watermark=watermark
        )

        # 生成文件名
        filename = f"evaluation_report_{report_id[:8]}.pdf"

        # 返回PDF文件
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"导出PDF失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出PDF失败: {str(e)}")


@router.get("/projects/{project_id}/companies/{company_id}/export/pdf")
async def quick_evaluate_and_export_pdf(
    project_id: str,
    company_id: str,
    scenario_id: str = Query("tender", description="场景ID"),
    watermark: Optional[str] = Query(None, description="水印文字"),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    快速评估并导出PDF

    - **project_id**: 项目ID
    - **company_id**: 企业ID
    - **scenario_id**: 场景ID，默认为tender
    - **watermark**: 可选的水印文字

    一步完成评估和导出，适合快速生成报告
    """
    logger.info(f"收到快速评估并导出PDF请求：项目 {project_id} vs 企业 {company_id}")

    # 生成报告
    report = evaluation_service.generate_report(
        project_id=project_id,
        company_id=company_id,
        scenario_id=scenario_id
    )

    if not report:
        raise HTTPException(status_code=500, detail="评估报告生成失败")

    try:
        # 生成PDF
        pdf_bytes = pdf_generator.generate_from_report(
            report=report,
            watermark=watermark
        )

        # 生成文件名
        filename = f"evaluation_{project_id[:8]}_{company_id[:8]}.pdf"

        # 返回PDF文件
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"导出PDF失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出PDF失败: {str(e)}")
