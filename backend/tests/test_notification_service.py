# backend/tests/test_notification_service.py
"""
通知服务单元测试
"""

import pytest
from datetime import datetime
from backend.services.notification_service import NotificationService
from backend.services.subscription_service import SubscriptionService
from backend.models import (
    Notification, NotificationType, NotificationStatus,
    Company, Scenario, Subscription, Project, ProjectStatus
)
from backend.database import get_db_session


@pytest.fixture
def notification_service():
    """创建通知服务实例"""
    return NotificationService()


@pytest.fixture
def subscription_service():
    """创建订阅服务实例"""
    return SubscriptionService()


@pytest.fixture
def test_company(notification_service):
    """创建测试企业"""
    db = next(get_db_session())
    try:
        company = Company(
            id="test-company-notif",
            name="测试企业-通知",
            unified_social_credit_code="91110000MA01234568",
            is_active=True
        )
        db.add(company)
        db.commit()
        yield company
        db.delete(company)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def test_scenario(notification_service):
    """创建测试场景"""
    db = next(get_db_session())
    try:
        scenario = Scenario(
            id="test-scenario-notif",
            name="测试场景-通知",
            status="active"
        )
        db.add(scenario)
        db.commit()
        yield scenario
        db.delete(scenario)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def test_subscription(subscription_service, test_company, test_scenario):
    """创建测试订阅"""
    subscription = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="测试订阅-通知",
        keywords=["电力"],
        notify_system=True,
        max_notifications_per_day=10
    )
    yield subscription
    subscription_service.delete_subscription(subscription.id)


@pytest.fixture
def test_project(notification_service, test_scenario):
    """创建测试项目"""
    db = next(get_db_session())
    try:
        project = Project(
            id="test-project-notif",
            scenario_id=test_scenario.id,
            title="测试电力项目",
            description="测试项目描述",
            region="北京市",
            budget=300.0,
            status=ProjectStatus.PUBLISHED.value
        )
        db.add(project)
        db.commit()
        yield project
        db.delete(project)
        db.commit()
    finally:
        db.close()


def test_create_notification(notification_service, test_company):
    """测试创建通知"""
    notification = notification_service.create_notification(
        company_id=test_company.id,
        title="测试通知",
        content="这是一条测试通知",
        notification_type=NotificationType.SYSTEM_ALERT,
        link_url="/test"
    )

    assert notification is not None
    assert notification.title == "测试通知"
    assert notification.type == NotificationType.SYSTEM_ALERT.value
    assert notification.status == NotificationStatus.UNREAD.value

    # 清理
    notification_service.delete_notification(notification.id)


def test_create_project_match_notification(
    notification_service,
    test_company,
    test_subscription,
    test_project
):
    """测试创建项目匹配通知"""
    notification = notification_service.create_project_match_notification(
        company_id=test_company.id,
        subscription=test_subscription,
        project=test_project,
        match_score=85
    )

    assert notification is not None
    assert notification.type == NotificationType.PROJECT_MATCH.value
    assert notification.project_id == test_project.id
    assert notification.subscription_id == test_subscription.id
    assert "85分" in notification.content

    # 清理
    notification_service.delete_notification(notification.id)


def test_list_notifications(notification_service, test_company):
    """测试获取通知列表"""
    # 创建多个通知
    notif1 = notification_service.create_notification(
        company_id=test_company.id,
        title="通知1",
        content="内容1",
        notification_type=NotificationType.PROJECT_MATCH
    )
    notif2 = notification_service.create_notification(
        company_id=test_company.id,
        title="通知2",
        content="内容2",
        notification_type=NotificationType.SYSTEM_ALERT
    )

    notifications, total = notification_service.list_notifications(
        company_id=test_company.id
    )

    assert total >= 2
    assert len(notifications) >= 2

    # 清理
    notification_service.delete_notification(notif1.id)
    notification_service.delete_notification(notif2.id)


def test_mark_as_read(notification_service, test_company):
    """测试标记通知为已读"""
    notification = notification_service.create_notification(
        company_id=test_company.id,
        title="未读通知",
        content="测试内容"
    )

    assert notification.status == NotificationStatus.UNREAD.value

    success = notification_service.mark_as_read(notification.id)
    assert success is True

    updated = notification_service.get_notification(notification.id)
    assert updated.status == NotificationStatus.READ.value
    assert updated.read_at is not None

    # 清理
    notification_service.delete_notification(notification.id)


def test_mark_as_archived(notification_service, test_company):
    """测试标记通知为已归档"""
    notification = notification_service.create_notification(
        company_id=test_company.id,
        title="待归档通知",
        content="测试内容"
    )

    success = notification_service.mark_as_archived(notification.id)
    assert success is True

    updated = notification_service.get_notification(notification.id)
    assert updated.status == NotificationStatus.ARCHIVED.value
    assert updated.archived_at is not None

    # 清理
    notification_service.delete_notification(notification.id)


def test_get_unread_count(notification_service, test_company):
    """测试获取未读通知数量"""
    # 创建未读通知
    notif1 = notification_service.create_notification(
        company_id=test_company.id,
        title="未读1",
        content="内容1"
    )
    notif2 = notification_service.create_notification(
        company_id=test_company.id,
        title="未读2",
        content="内容2"
    )

    count = notification_service.get_unread_count(test_company.id)
    assert count >= 2

    # 标记一个为已读
    notification_service.mark_as_read(notif1.id)

    count_after = notification_service.get_unread_count(test_company.id)
    assert count_after == count - 1

    # 清理
    notification_service.delete_notification(notif1.id)
    notification_service.delete_notification(notif2.id)


def test_mark_all_as_read(notification_service, test_company):
    """测试标记所有通知为已读"""
    # 创建多个未读通知
    notif1 = notification_service.create_notification(
        company_id=test_company.id,
        title="未读1",
        content="内容1"
    )
    notif2 = notification_service.create_notification(
        company_id=test_company.id,
        title="未读2",
        content="内容2"
    )

    initial_unread = notification_service.get_unread_count(test_company.id)
    assert initial_unread >= 2

    count = notification_service.mark_all_as_read(test_company.id)
    assert count >= 2

    final_unread = notification_service.get_unread_count(test_company.id)
    assert final_unread == 0

    # 清理
    notification_service.delete_notification(notif1.id)
    notification_service.delete_notification(notif2.id)


def test_notification_daily_limit(
    notification_service,
    subscription_service,
    test_company,
    test_scenario,
    test_project
):
    """测试通知每日限制"""
    # 创建订阅，设置每天最多2条通知
    subscription = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="限制订阅",
        keywords=["电力"],
        notify_system=True,
        max_notifications_per_day=2
    )

    # 创建第1条通知
    notif1 = notification_service.create_project_match_notification(
        company_id=test_company.id,
        subscription=subscription,
        project=test_project,
        match_score=85
    )
    assert notif1 is not None

    # 创建第2条通知
    notif2 = notification_service.create_project_match_notification(
        company_id=test_company.id,
        subscription=subscription,
        project=test_project,
        match_score=90
    )
    assert notif2 is not None

    # 尝试创建第3条通知，应该被限制
    notif3 = notification_service.create_project_match_notification(
        company_id=test_company.id,
        subscription=subscription,
        project=test_project,
        match_score=95
    )
    assert notif3 is None  # 超过每日限制，不应该创建

    # 清理
    if notif1:
        notification_service.delete_notification(notif1.id)
    if notif2:
        notification_service.delete_notification(notif2.id)
    subscription_service.delete_subscription(subscription.id)

