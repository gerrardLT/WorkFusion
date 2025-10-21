# backend/api/notification.py
"""
通知管理API
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from backend.services.notification_service import get_notification_service, NotificationService
from backend.models import NotificationType, NotificationStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notification", tags=["notification"])


# ============= Pydantic Models =============

class NotificationResponse(BaseModel):
    id: str
    company_id: str
    subscription_id: Optional[str]
    project_id: Optional[str]
    type: str
    title: str
    content: str
    link_url: Optional[str]
    status: str
    is_sent_email: bool
    is_sent_webhook: bool
    metadata: Optional[Dict[str, Any]]
    created_at: str
    read_at: Optional[str]
    archived_at: Optional[str]

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


# ============= API Endpoints =============

@router.get("/list", response_model=NotificationListResponse)
async def list_notifications(
    company_id: str = Query(..., description="企业ID"),
    status: Optional[NotificationStatus] = Query(None, description="通知状态"),
    notification_type: Optional[NotificationType] = Query(None, description="通知类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """获取通知列表"""
    offset = (page - 1) * page_size
    notifications, total = notification_service.list_notifications(
        company_id=company_id,
        status=status,
        notification_type=notification_type,
        limit=page_size,
        offset=offset
    )

    # 获取未读数量
    unread_count = notification_service.get_unread_count(company_id)

    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=notif.id,
                company_id=notif.company_id,
                subscription_id=notif.subscription_id,
                project_id=notif.project_id,
                type=notif.type,
                title=notif.title,
                content=notif.content,
                link_url=notif.link_url,
                status=notif.status,
                is_sent_email=notif.is_sent_email,
                is_sent_webhook=notif.is_sent_webhook,
                metadata=notif.notification_metadata,
                created_at=notif.created_at.isoformat(),
                read_at=notif.read_at.isoformat() if notif.read_at else None,
                archived_at=notif.archived_at.isoformat() if notif.archived_at else None
            )
            for notif in notifications
        ],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size
    )


@router.get("/unread-count")
async def get_unread_count(
    company_id: str = Query(..., description="企业ID"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """获取未读通知数量"""
    count = notification_service.get_unread_count(company_id)
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """获取通知详情"""
    notification = notification_service.get_notification(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知未找到")

    return NotificationResponse(
        id=notification.id,
        company_id=notification.company_id,
        subscription_id=notification.subscription_id,
        project_id=notification.project_id,
        type=notification.type,
        title=notification.title,
        content=notification.content,
        link_url=notification.link_url,
        status=notification.status,
        is_sent_email=notification.is_sent_email,
        is_sent_webhook=notification.is_sent_webhook,
        metadata=notification.notification_metadata,
        created_at=notification.created_at.isoformat(),
        read_at=notification.read_at.isoformat() if notification.read_at else None,
        archived_at=notification.archived_at.isoformat() if notification.archived_at else None
    )


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """标记通知为已读"""
    success = notification_service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=500, detail="标记通知为已读失败或通知未找到")

    return {"success": True, "message": "通知已标记为已读"}


@router.put("/{notification_id}/archive")
async def mark_notification_as_archived(
    notification_id: str,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """标记通知为已归档"""
    success = notification_service.mark_as_archived(notification_id)
    if not success:
        raise HTTPException(status_code=500, detail="标记通知为已归档失败或通知未找到")

    return {"success": True, "message": "通知已标记为已归档"}


@router.put("/mark-all-read")
async def mark_all_notifications_as_read(
    company_id: str = Query(..., description="企业ID"),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """标记所有未读通知为已读"""
    count = notification_service.mark_all_as_read(company_id)
    return {"success": True, "message": f"已标记{count}条通知为已读", "count": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """删除通知"""
    success = notification_service.delete_notification(notification_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除通知失败或通知未找到")

    return {"success": True, "message": "通知已成功删除"}

