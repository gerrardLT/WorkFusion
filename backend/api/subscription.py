# backend/api/subscription.py
"""
订阅管理API
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from backend.services.subscription_service import get_subscription_service, SubscriptionService
from backend.models import SubscriptionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["subscription"])


# ============= Pydantic Models =============

class CreateSubscriptionRequest(BaseModel):
    company_id: str
    scenario_id: str = "tender"
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    match_score_threshold: int = Field(70, ge=0, le=100)
    notify_system: bool = True
    notify_email: bool = False
    notify_webhook: bool = False
    max_notifications_per_day: int = Field(10, ge=1, le=100)
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateSubscriptionRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    match_score_threshold: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[SubscriptionStatus] = None
    notify_system: Optional[bool] = None
    notify_email: Optional[bool] = None
    notify_webhook: Optional[bool] = None
    max_notifications_per_day: Optional[int] = Field(None, ge=1, le=100)
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionResponse(BaseModel):
    id: str
    company_id: str
    scenario_id: str
    name: str
    description: Optional[str]
    status: str
    keywords: List[str]
    regions: List[str]
    budget_min: Optional[float]
    budget_max: Optional[float]
    match_score_threshold: int
    notify_system: bool
    notify_email: bool
    notify_webhook: bool
    max_notifications_per_day: int
    total_matches: int
    total_notifications: int
    last_match_at: Optional[str]
    created_at: str
    updated_at: str
    expires_at: Optional[str]

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    subscriptions: List[SubscriptionResponse]
    total: int
    page: int
    page_size: int


# ============= API Endpoints =============

@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """创建订阅规则"""
    logger.info(f"收到创建订阅请求，企业ID: {request.company_id}, 名称: {request.name}")

    subscription = subscription_service.create_subscription(
        company_id=request.company_id,
        scenario_id=request.scenario_id,
        name=request.name,
        description=request.description,
        keywords=request.keywords,
        regions=request.regions,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        match_score_threshold=request.match_score_threshold,
        notify_system=request.notify_system,
        notify_email=request.notify_email,
        notify_webhook=request.notify_webhook,
        max_notifications_per_day=request.max_notifications_per_day,
        expires_at=request.expires_at,
        metadata=request.metadata
    )

    if not subscription:
        raise HTTPException(status_code=500, detail="创建订阅失败")

    return SubscriptionResponse(
        id=subscription.id,
        company_id=subscription.company_id,
        scenario_id=subscription.scenario_id,
        name=subscription.name,
        description=subscription.description,
        status=subscription.status,
        keywords=subscription.keywords or [],
        regions=subscription.regions or [],
        budget_min=subscription.budget_min,
        budget_max=subscription.budget_max,
        match_score_threshold=subscription.match_score_threshold,
        notify_system=subscription.notify_system,
        notify_email=subscription.notify_email,
        notify_webhook=subscription.notify_webhook,
        max_notifications_per_day=subscription.max_notifications_per_day,
        total_matches=subscription.total_matches or 0,
        total_notifications=subscription.total_notifications or 0,
        last_match_at=subscription.last_match_at.isoformat() if subscription.last_match_at else None,
        created_at=subscription.created_at.isoformat(),
        updated_at=subscription.updated_at.isoformat(),
        expires_at=subscription.expires_at.isoformat() if subscription.expires_at else None
    )


@router.get("/list", response_model=SubscriptionListResponse)
async def list_subscriptions(
    company_id: str = Query(..., description="企业ID"),
    scenario_id: Optional[str] = Query(None, description="场景ID"),
    status: Optional[SubscriptionStatus] = Query(None, description="订阅状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """获取订阅列表"""
    offset = (page - 1) * page_size
    subscriptions, total = subscription_service.list_subscriptions(
        company_id=company_id,
        scenario_id=scenario_id,
        status=status,
        limit=page_size,
        offset=offset
    )

    return SubscriptionListResponse(
        subscriptions=[
            SubscriptionResponse(
                id=sub.id,
                company_id=sub.company_id,
                scenario_id=sub.scenario_id,
                name=sub.name,
                description=sub.description,
                status=sub.status,
                keywords=sub.keywords or [],
                regions=sub.regions or [],
                budget_min=sub.budget_min,
                budget_max=sub.budget_max,
                match_score_threshold=sub.match_score_threshold,
                notify_system=sub.notify_system,
                notify_email=sub.notify_email,
                notify_webhook=sub.notify_webhook,
                max_notifications_per_day=sub.max_notifications_per_day,
                total_matches=sub.total_matches or 0,
                total_notifications=sub.total_notifications or 0,
                last_match_at=sub.last_match_at.isoformat() if sub.last_match_at else None,
                created_at=sub.created_at.isoformat(),
                updated_at=sub.updated_at.isoformat(),
                expires_at=sub.expires_at.isoformat() if sub.expires_at else None
            )
            for sub in subscriptions
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """获取订阅详情"""
    subscription = subscription_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="订阅未找到")

    return SubscriptionResponse(
        id=subscription.id,
        company_id=subscription.company_id,
        scenario_id=subscription.scenario_id,
        name=subscription.name,
        description=subscription.description,
        status=subscription.status,
        keywords=subscription.keywords or [],
        regions=subscription.regions or [],
        budget_min=subscription.budget_min,
        budget_max=subscription.budget_max,
        match_score_threshold=subscription.match_score_threshold,
        notify_system=subscription.notify_system,
        notify_email=subscription.notify_email,
        notify_webhook=subscription.notify_webhook,
        max_notifications_per_day=subscription.max_notifications_per_day,
        total_matches=subscription.total_matches or 0,
        total_notifications=subscription.total_notifications or 0,
        last_match_at=subscription.last_match_at.isoformat() if subscription.last_match_at else None,
        created_at=subscription.created_at.isoformat(),
        updated_at=subscription.updated_at.isoformat(),
        expires_at=subscription.expires_at.isoformat() if subscription.expires_at else None
    )


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    updates: UpdateSubscriptionRequest,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """更新订阅规则"""
    subscription = subscription_service.update_subscription(
        subscription_id=subscription_id,
        updates=updates.model_dump(exclude_unset=True)
    )

    if not subscription:
        raise HTTPException(status_code=500, detail="更新订阅失败或订阅未找到")

    return SubscriptionResponse(
        id=subscription.id,
        company_id=subscription.company_id,
        scenario_id=subscription.scenario_id,
        name=subscription.name,
        description=subscription.description,
        status=subscription.status,
        keywords=subscription.keywords or [],
        regions=subscription.regions or [],
        budget_min=subscription.budget_min,
        budget_max=subscription.budget_max,
        match_score_threshold=subscription.match_score_threshold,
        notify_system=subscription.notify_system,
        notify_email=subscription.notify_email,
        notify_webhook=subscription.notify_webhook,
        max_notifications_per_day=subscription.max_notifications_per_day,
        total_matches=subscription.total_matches or 0,
        total_notifications=subscription.total_notifications or 0,
        last_match_at=subscription.last_match_at.isoformat() if subscription.last_match_at else None,
        created_at=subscription.created_at.isoformat(),
        updated_at=subscription.updated_at.isoformat(),
        expires_at=subscription.expires_at.isoformat() if subscription.expires_at else None
    )


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """删除订阅"""
    success = subscription_service.delete_subscription(subscription_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除订阅失败或订阅未找到")

    return {"success": True, "message": "订阅已成功删除"}

