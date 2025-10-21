"""
风险识别API路由
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from backend.services.risk_service import get_risk_service, RiskService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["risk"])


# ==================== Pydantic模型 ====================

class DetectRiskRequest(BaseModel):
    """风险检测请求"""
    document_id: str = Field(..., description="文档ID")
    scenario_id: str = Field(default="tender", description="场景ID")


class DetectRiskResponse(BaseModel):
    """风险检测响应"""
    success: bool
    message: str
    report_id: Optional[str] = None


class RiskItemResponse(BaseModel):
    """单个风险项响应"""
    id: str
    title: str
    description: str
    risk_type: str
    risk_level: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    clause_number: Optional[str] = None
    original_text: Optional[str] = None
    impact_description: Optional[str] = None
    mitigation_suggestion: Optional[str] = None
    confidence_score: Optional[int] = None
    created_at: str
    updated_at: str


class RiskReportResponse(BaseModel):
    """风险报告响应"""
    id: str
    document_id: str
    scenario_id: str
    title: str
    summary: Optional[str] = None
    total_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    overall_risk_level: Optional[str] = None
    created_at: str
    updated_at: str
    risks: list[RiskItemResponse]


# ==================== API端点 ====================

@router.post("/detect", response_model=DetectRiskResponse)
async def detect_risks(
    request: DetectRiskRequest,
    background_tasks: BackgroundTasks,
    risk_service: RiskService = Depends(get_risk_service)
):
    """
    为指定文档检测风险（同步）

    这个端点会同步执行风险检测，可能需要较长时间（30秒-2分钟）
    """
    try:
        logger.info(f"📋 开始为文档 {request.document_id} 检测风险")

        report_id = risk_service.detect_risks(
            document_id=request.document_id,
            scenario_id=request.scenario_id
        )

        if report_id:
            return DetectRiskResponse(
                success=True,
                message="风险检测成功",
                report_id=report_id
            )
        else:
            raise HTTPException(status_code=500, detail="风险检测失败")

    except Exception as e:
        logger.error(f"风险检测失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"风险检测失败: {str(e)}")


@router.post("/detect-async", response_model=DetectRiskResponse)
async def detect_risks_async(
    request: DetectRiskRequest,
    background_tasks: BackgroundTasks,
    risk_service: RiskService = Depends(get_risk_service)
):
    """
    为指定文档检测风险（异步）

    这个端点会在后台异步执行风险检测，立即返回
    """
    try:
        logger.info(f"📋 添加风险检测任务到后台队列: {request.document_id}")

        # 添加后台任务
        background_tasks.add_task(
            risk_service.detect_risks,
            request.document_id,
            request.scenario_id
        )

        return DetectRiskResponse(
            success=True,
            message="风险检测任务已加入队列",
            report_id=None
        )

    except Exception as e:
        logger.error(f"添加风险检测任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"添加风险检测任务失败: {str(e)}")


@router.get("/report/{report_id}", response_model=RiskReportResponse)
async def get_risk_report(
    report_id: str,
    risk_service: RiskService = Depends(get_risk_service)
):
    """
    根据报告ID获取风险报告详情
    """
    try:
        report = risk_service.get_risk_report(report_id)

        if not report:
            raise HTTPException(status_code=404, detail="风险报告未找到")

        return RiskReportResponse(**report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取风险报告失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取风险报告失败: {str(e)}")


@router.get("/document/{document_id}/report", response_model=RiskReportResponse)
async def get_risk_report_by_document(
    document_id: str,
    risk_service: RiskService = Depends(get_risk_service)
):
    """
    根据文档ID获取风险报告
    """
    try:
        report = risk_service.get_risk_report_by_document(document_id)

        if not report:
            raise HTTPException(status_code=404, detail="该文档暂无风险报告")

        return RiskReportResponse(**report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档风险报告失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文档风险报告失败: {str(e)}")


@router.delete("/report/{report_id}")
async def delete_risk_report(
    report_id: str,
    risk_service: RiskService = Depends(get_risk_service)
):
    """
    删除风险报告（预留接口）
    """
    # TODO: 实现删除逻辑
    raise HTTPException(status_code=501, detail="删除功能尚未实现")

