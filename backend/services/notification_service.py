# backend/services/notification_service.py
"""
通知服务

用于生成和管理系统通知
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.database import get_db_session
from backend.models import Notification, NotificationType, NotificationStatus, Subscription, Project
from config import get_settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.settings = get_settings()

    def _get_db(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_db_session()

    def create_notification(
        self,
        company_id: str,
        title: str,
        content: str,
        notification_type: NotificationType = NotificationType.PROJECT_MATCH,
        subscription_id: Optional[str] = None,
        project_id: Optional[str] = None,
        link_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Notification]:
        """
        创建通知

        Args:
            company_id: 企业ID
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型
            subscription_id: 订阅ID（可选）
            project_id: 项目ID（可选）
            link_url: 跳转链接（可选）
            metadata: 额外元数据（可选）

        Returns:
            Notification: 创建的通知对象，失败返回None
        """
        db = self._get_db()
        try:
            new_notification = Notification(
                id=str(uuid.uuid4()),
                company_id=company_id,
                subscription_id=subscription_id,
                project_id=project_id,
                type=notification_type.value,
                title=title,
                content=content,
                link_url=link_url,
                notification_metadata=metadata if metadata else {}
            )

            db.add(new_notification)
            db.commit()
            db.refresh(new_notification)
            logger.info(f"✅ 通知 '{title}' (ID: {new_notification.id}) 创建成功")
            return new_notification

        except Exception as e:
            db.rollback()
            logger.error(f"创建通知失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def create_project_match_notification(
        self,
        company_id: str,
        subscription: Subscription,
        project: Project,
        match_score: int
    ) -> Optional[Notification]:
        """
        创建项目匹配通知

        Args:
            company_id: 企业ID
            subscription: 订阅对象
            project: 项目对象
            match_score: 匹配度分数

        Returns:
            Notification: 创建的通知对象
        """
        # 检查订阅的通知设置
        if not subscription.notify_system:
            logger.info(f"订阅 '{subscription.name}' 未开启系统通知，跳过通知创建")
            return None

        # 检查今天的通知次数
        db = self._get_db()
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_notification_count = db.query(func.count(Notification.id)).filter(
                and_(
                    Notification.subscription_id == subscription.id,
                    Notification.created_at >= today_start
                )
            ).scalar()

            if today_notification_count >= subscription.max_notifications_per_day:
                logger.warning(f"订阅 '{subscription.name}' 今天的通知次数已达上限({subscription.max_notifications_per_day})，跳过通知创建")
                return None

        except Exception as e:
            logger.error(f"检查通知次数失败: {str(e)}", exc_info=True)
        finally:
            db.close()

        title = f"🎯 发现高匹配度项目：{project.title[:30]}..."
        content = (
            f"根据您的订阅规则「{subscription.name}」，发现一个高度匹配的项目：\n\n"
            f"📌 项目名称：{project.title}\n"
            f"📍 项目地区：{project.region}\n"
            f"💰 项目预算：{project.budget}万元\n"
            f"📊 匹配度：{match_score}分\n"
            f"⏰ 截止时间：{project.deadline.strftime('%Y-%m-%d %H:%M') if project.deadline else '未知'}\n\n"
            f"点击查看详情，快速评估此项目的投标价值。"
        )
        link_url = f"/projects/{project.id}"

        notification = self.create_notification(
            company_id=company_id,
            title=title,
            content=content,
            notification_type=NotificationType.PROJECT_MATCH,
            subscription_id=subscription.id,
            project_id=project.id,
            link_url=link_url,
            metadata={
                "match_score": match_score,
                "project_title": project.title,
                "project_budget": project.budget,
                "subscription_name": subscription.name
            }
        )

        # 更新订阅的通知计数
        if notification:
            from backend.services.subscription_service import get_subscription_service
            subscription_service = get_subscription_service()
            subscription_service.increment_notification_count(subscription.id)

        return notification

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """获取通知详情"""
        db = self._get_db()
        try:
            return db.query(Notification).filter(Notification.id == notification_id).first()
        finally:
            db.close()

    def list_notifications(
        self,
        company_id: str,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Notification], int]:
        """
        获取通知列表

        Args:
            company_id: 企业ID
            status: 通知状态（可选）
            notification_type: 通知类型（可选）
            limit: 每页数量
            offset: 偏移量

        Returns:
            (通知列表, 总数)
        """
        db = self._get_db()
        try:
            query = db.query(Notification).filter(Notification.company_id == company_id)

            if status:
                query = query.filter(Notification.status == status.value)
            if notification_type:
                query = query.filter(Notification.type == notification_type.value)

            total_count = query.count()
            notifications = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()
            return notifications, total_count
        finally:
            db.close()

    def mark_as_read(self, notification_id: str) -> bool:
        """标记通知为已读"""
        db = self._get_db()
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                return False

            notification.mark_as_read()
            db.commit()
            logger.info(f"✅ 通知 {notification_id} 已标记为已读")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"标记通知 {notification_id} 为已读失败: {str(e)}", exc_info=True)
            return False
        finally:
            db.close()

    def mark_as_archived(self, notification_id: str) -> bool:
        """标记通知为已归档"""
        db = self._get_db()
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                return False

            notification.mark_as_archived()
            db.commit()
            logger.info(f"✅ 通知 {notification_id} 已标记为已归档")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"标记通知 {notification_id} 为已归档失败: {str(e)}", exc_info=True)
            return False
        finally:
            db.close()

    def delete_notification(self, notification_id: str) -> bool:
        """删除通知"""
        db = self._get_db()
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                return False

            db.delete(notification)
            db.commit()
            logger.info(f"✅ 通知 {notification_id} 已删除")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"删除通知 {notification_id} 失败: {str(e)}", exc_info=True)
            return False
        finally:
            db.close()

    def get_unread_count(self, company_id: str) -> int:
        """获取未读通知数量"""
        db = self._get_db()
        try:
            return db.query(func.count(Notification.id)).filter(
                and_(
                    Notification.company_id == company_id,
                    Notification.status == NotificationStatus.UNREAD.value
                )
            ).scalar()
        finally:
            db.close()

    def mark_all_as_read(self, company_id: str) -> int:
        """标记所有未读通知为已读"""
        db = self._get_db()
        try:
            unread_notifications = db.query(Notification).filter(
                and_(
                    Notification.company_id == company_id,
                    Notification.status == NotificationStatus.UNREAD.value
                )
            ).all()

            count = len(unread_notifications)
            for notification in unread_notifications:
                notification.mark_as_read()

            db.commit()
            logger.info(f"✅ 已标记 {count} 条未读通知为已读")
            return count

        except Exception as e:
            db.rollback()
            logger.error(f"标记所有未读通知为已读失败: {str(e)}", exc_info=True)
            return 0
        finally:
            db.close()


_notification_service_instance: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService()
    return _notification_service_instance

