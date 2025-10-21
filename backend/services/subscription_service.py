# backend/services/subscription_service.py
"""
订阅服务

用于管理用户订阅规则和项目匹配逻辑
"""

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from backend.database import get_db_session
from backend.models import Subscription, SubscriptionStatus, Company, Scenario
from config import get_settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.settings = get_settings()

    def _get_db(self) -> Session:
        if self.db_session:
            return self.db_session
        return get_db_session()

    def create_subscription(
        self,
        company_id: str,
        scenario_id: str,
        name: str,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        match_score_threshold: int = 70,
        notify_system: bool = True,
        notify_email: bool = False,
        notify_webhook: bool = False,
        max_notifications_per_day: int = 10,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Subscription]:
        """
        创建订阅规则

        Args:
            company_id: 企业ID
            scenario_id: 场景ID
            name: 订阅规则名称
            description: 订阅规则描述
            keywords: 关键词列表
            regions: 地域列表
            budget_min: 最小预算
            budget_max: 最大预算
            match_score_threshold: 匹配度阈值
            notify_system: 是否系统通知
            notify_email: 是否邮件通知
            notify_webhook: 是否Webhook通知
            max_notifications_per_day: 每天最多通知次数
            expires_at: 过期时间
            metadata: 额外元数据

        Returns:
            Subscription: 创建的订阅对象，失败返回None
        """
        db = self._get_db()
        try:
            # 验证company_id和scenario_id
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                logger.error(f"企业 {company_id} 不存在")
                return None

            scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
            if not scenario:
                logger.error(f"场景 {scenario_id} 不存在")
                return None

            new_subscription = Subscription(
                id=str(uuid.uuid4()),
                company_id=company_id,
                scenario_id=scenario_id,
                name=name,
                description=description,
                keywords=keywords if keywords else [],
                regions=regions if regions else [],
                budget_min=budget_min,
                budget_max=budget_max,
                match_score_threshold=match_score_threshold,
                notify_system=notify_system,
                notify_email=notify_email,
                notify_webhook=notify_webhook,
                max_notifications_per_day=max_notifications_per_day,
                expires_at=expires_at,
                subscription_metadata=metadata if metadata else {}
            )

            db.add(new_subscription)
            db.commit()
            db.refresh(new_subscription)
            logger.info(f"✅ 订阅规则 '{name}' (ID: {new_subscription.id}) 创建成功")
            return new_subscription

        except Exception as e:
            db.rollback()
            logger.error(f"创建订阅规则失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """获取订阅详情"""
        db = self._get_db()
        try:
            return db.query(Subscription).filter(Subscription.id == subscription_id).first()
        finally:
            db.close()

    def list_subscriptions(
        self,
        company_id: str,
        scenario_id: Optional[str] = None,
        status: Optional[SubscriptionStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Subscription], int]:
        """
        获取订阅列表

        Args:
            company_id: 企业ID
            scenario_id: 场景ID（可选）
            status: 订阅状态（可选）
            limit: 每页数量
            offset: 偏移量

        Returns:
            (订阅列表, 总数)
        """
        db = self._get_db()
        try:
            query = db.query(Subscription).filter(Subscription.company_id == company_id)

            if scenario_id:
                query = query.filter(Subscription.scenario_id == scenario_id)
            if status:
                query = query.filter(Subscription.status == status.value)

            total_count = query.count()
            subscriptions = query.order_by(Subscription.created_at.desc()).limit(limit).offset(offset).all()
            return subscriptions, total_count
        finally:
            db.close()

    def update_subscription(
        self,
        subscription_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Subscription]:
        """更新订阅规则"""
        db = self._get_db()
        try:
            subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if not subscription:
                return None

            for key, value in updates.items():
                if hasattr(subscription, key):
                    if key == "status" and value not in [s.value for s in SubscriptionStatus]:
                        logger.warning(f"无效的订阅状态: {value}")
                        continue
                    setattr(subscription, key, value)

            subscription.updated_at = datetime.now()
            db.commit()
            db.refresh(subscription)
            logger.info(f"✅ 订阅规则 {subscription_id} 更新成功")
            return subscription

        except Exception as e:
            db.rollback()
            logger.error(f"更新订阅规则 {subscription_id} 失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def delete_subscription(self, subscription_id: str) -> bool:
        """删除订阅规则"""
        db = self._get_db()
        try:
            subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if not subscription:
                return False

            db.delete(subscription)
            db.commit()
            logger.info(f"✅ 订阅规则 {subscription_id} 已删除")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"删除订阅规则 {subscription_id} 失败: {str(e)}", exc_info=True)
            return False
        finally:
            db.close()

    def match_project_to_subscriptions(
        self,
        project_dict: Dict[str, Any],
        company_id: Optional[str] = None
    ) -> List[Subscription]:
        """
        将项目与订阅规则匹配

        Args:
            project_dict: 项目字典
            company_id: 企业ID（可选，如果指定则只匹配该企业的订阅）

        Returns:
            匹配的订阅列表
        """
        db = self._get_db()
        try:
            query = db.query(Subscription).filter(
                Subscription.status == SubscriptionStatus.ACTIVE.value
            )

            if company_id:
                query = query.filter(Subscription.company_id == company_id)

            active_subscriptions = query.all()
            matched_subscriptions = []

            for subscription in active_subscriptions:
                # 检查是否已过期
                if not subscription.is_active():
                    continue

                # 检查是否匹配
                if subscription.matches_project(project_dict):
                    matched_subscriptions.append(subscription)
                    logger.info(f"项目 '{project_dict.get('title', 'Unknown')}' 匹配订阅 '{subscription.name}'")

            return matched_subscriptions

        except Exception as e:
            logger.error(f"匹配项目到订阅失败: {str(e)}", exc_info=True)
            return []
        finally:
            db.close()

    def increment_match_count(self, subscription_id: str):
        """增加订阅的匹配计数"""
        db = self._get_db()
        try:
            subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if subscription:
                subscription.total_matches = (subscription.total_matches or 0) + 1
                subscription.last_match_at = datetime.now()
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"增加订阅 {subscription_id} 匹配计数失败: {str(e)}", exc_info=True)
        finally:
            db.close()

    def increment_notification_count(self, subscription_id: str):
        """增加订阅的通知计数"""
        db = self._get_db()
        try:
            subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if subscription:
                subscription.total_notifications = (subscription.total_notifications or 0) + 1
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"增加订阅 {subscription_id} 通知计数失败: {str(e)}", exc_info=True)
        finally:
            db.close()


_subscription_service_instance: Optional[SubscriptionService] = None


def get_subscription_service() -> SubscriptionService:
    global _subscription_service_instance
    if _subscription_service_instance is None:
        _subscription_service_instance = SubscriptionService()
    return _subscription_service_instance

