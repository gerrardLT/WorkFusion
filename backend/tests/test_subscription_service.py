# backend/tests/test_subscription_service.py
"""
订阅服务单元测试
"""

import pytest
from datetime import datetime, timedelta
from backend.services.subscription_service import SubscriptionService
from backend.models import Subscription, SubscriptionStatus, Company, Scenario
from backend.database import get_db_session


@pytest.fixture
def subscription_service():
    """创建订阅服务实例"""
    return SubscriptionService()


@pytest.fixture
def test_company(subscription_service):
    """创建测试企业"""
    db = next(get_db_session())
    try:
        company = Company(
            id="test-company-123",
            name="测试企业",
            unified_social_credit_code="91110000MA01234567",
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
def test_scenario(subscription_service):
    """创建测试场景"""
    db = next(get_db_session())
    try:
        scenario = Scenario(
            id="test-scenario",
            name="测试场景",
            status="active"
        )
        db.add(scenario)
        db.commit()
        yield scenario
        db.delete(scenario)
        db.commit()
    finally:
        db.close()


def test_create_subscription(subscription_service, test_company, test_scenario):
    """测试创建订阅"""
    subscription = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="电力工程项目订阅",
        description="订阅100万以上的电力工程项目",
        keywords=["电力", "变电站"],
        regions=["北京", "上海"],
        budget_min=100.0,
        budget_max=500.0,
        match_score_threshold=75
    )

    assert subscription is not None
    assert subscription.name == "电力工程项目订阅"
    assert len(subscription.keywords) == 2
    assert subscription.match_score_threshold == 75
    assert subscription.status == SubscriptionStatus.ACTIVE.value

    # 清理
    subscription_service.delete_subscription(subscription.id)


def test_list_subscriptions(subscription_service, test_company, test_scenario):
    """测试获取订阅列表"""
    # 创建多个订阅
    sub1 = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="订阅1",
        keywords=["电力"]
    )
    sub2 = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="订阅2",
        keywords=["水利"]
    )

    subscriptions, total = subscription_service.list_subscriptions(
        company_id=test_company.id
    )

    assert total >= 2
    assert len(subscriptions) >= 2

    # 清理
    subscription_service.delete_subscription(sub1.id)
    subscription_service.delete_subscription(sub2.id)


def test_update_subscription(subscription_service, test_company, test_scenario):
    """测试更新订阅"""
    subscription = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="原始订阅",
        keywords=["电力"]
    )

    updated = subscription_service.update_subscription(
        subscription_id=subscription.id,
        updates={
            "name": "更新后的订阅",
            "keywords": ["电力", "新能源"],
            "status": SubscriptionStatus.PAUSED.value
        }
    )

    assert updated is not None
    assert updated.name == "更新后的订阅"
    assert len(updated.keywords) == 2
    assert updated.status == SubscriptionStatus.PAUSED.value

    # 清理
    subscription_service.delete_subscription(subscription.id)


def test_match_project_to_subscriptions(subscription_service, test_company, test_scenario):
    """测试项目匹配订阅规则"""
    subscription = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="电力项目订阅",
        keywords=["电力", "变电站"],
        regions=["北京"],
        budget_min=100.0,
        budget_max=500.0,
        match_score_threshold=70
    )

    # 测试匹配的项目
    matching_project = {
        "title": "北京市某区110kV变电站建设项目",
        "description": "新建110kV变电站及配套电力设施",
        "region": "北京市朝阳区",
        "budget": 300.0,
        "match_score": 85
    }

    matched = subscription_service.match_project_to_subscriptions(
        project_dict=matching_project,
        company_id=test_company.id
    )

    assert len(matched) > 0
    assert matched[0].id == subscription.id

    # 测试不匹配的项目（预算太小）
    non_matching_project = {
        "title": "小型电力改造项目",
        "description": "电力线路改造",
        "region": "北京市",
        "budget": 50.0,  # 低于最小预算
        "match_score": 80
    }

    matched2 = subscription_service.match_project_to_subscriptions(
        project_dict=non_matching_project,
        company_id=test_company.id
    )

    assert len(matched2) == 0

    # 清理
    subscription_service.delete_subscription(subscription.id)


def test_subscription_is_active(subscription_service, test_company, test_scenario):
    """测试订阅是否激活"""
    # 创建激活的订阅
    active_sub = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="激活订阅",
        keywords=["电力"]
    )
    assert active_sub.is_active() is True

    # 创建已过期的订阅
    expired_sub = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="过期订阅",
        keywords=["电力"],
        expires_at=datetime.now() - timedelta(days=1)
    )
    assert expired_sub.is_active() is False

    # 清理
    subscription_service.delete_subscription(active_sub.id)
    subscription_service.delete_subscription(expired_sub.id)


def test_increment_counts(subscription_service, test_company, test_scenario):
    """测试增加匹配和通知计数"""
    subscription = subscription_service.create_subscription(
        company_id=test_company.id,
        scenario_id=test_scenario.id,
        name="测试订阅",
        keywords=["电力"]
    )

    initial_match_count = subscription.total_matches or 0
    initial_notif_count = subscription.total_notifications or 0

    # 增加匹配计数
    subscription_service.increment_match_count(subscription.id)
    updated_sub = subscription_service.get_subscription(subscription.id)
    assert updated_sub.total_matches == initial_match_count + 1

    # 增加通知计数
    subscription_service.increment_notification_count(subscription.id)
    updated_sub2 = subscription_service.get_subscription(subscription.id)
    assert updated_sub2.total_notifications == initial_notif_count + 1

    # 清理
    subscription_service.delete_subscription(subscription.id)

