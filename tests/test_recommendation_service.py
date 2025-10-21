# tests/test_recommendation_service.py
"""
推荐服务单元测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.recommendation_service import RecommendationService
from backend.services.company_service import CompanyService
from backend.models import Company, CompanyScale, Project, ProjectStatus
from backend.database import create_tables, get_db_session


class TestRecommendationService:
    """推荐服务测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        create_tables()
        self.service = RecommendationService()
        self.company_service = CompanyService()
        self.db = get_db_session()

    def teardown_method(self):
        """每个测试方法后执行"""
        if self.db:
            self.db.close()

    def _create_test_company(self, name_suffix="", **kwargs) -> Company:
        """创建测试企业"""
        import uuid
        defaults = {
            "name": f"测试企业{name_suffix}_{uuid.uuid4().hex[:8]}",
            "scale": CompanyScale.MEDIUM,
            "qualifications": [
                {"name": "电力工程施工总承包", "level": "二级", "expire_date": "2025-12-31"}
            ],
            "achievements": {
                "total_projects": 50,
                "total_amount": 100000,  # 万元
                "average_amount": 2000,
                "success_rate": 0.75
            },
            "target_areas": ["广东", "江苏"],
            "target_industries": ["电力"],
            "budget_range": {"min": 500, "max": 5000}
        }
        defaults.update(kwargs)
        return self.company_service.create_company(**defaults)

    def _create_test_project(self, title_suffix="", **kwargs) -> Project:
        """创建测试项目"""
        import uuid
        defaults = {
            "id": f"proj_{uuid.uuid4().hex[:12]}",
            "title": f"测试项目{title_suffix}_{uuid.uuid4().hex[:6]}",
            "budget": 2000,  # 万元
            "area": "广东",
            "industry": "电力",
            "required_qualifications": [
                {"name": "电力工程施工总承包", "level": "二级或以上"}
            ],
            "status": ProjectStatus.ACTIVE.value,
            "deadline": datetime.now() + timedelta(days=30)
        }
        defaults.update(kwargs)
        project = Project(**defaults)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def test_qualification_match_perfect(self):
        """测试资质完全匹配"""
        company = self._create_test_company()
        project = self._create_test_project()

        score = self.service._match_qualifications(project, company)
        assert score == 100.0

    def test_qualification_match_partial(self):
        """测试资质部分匹配"""
        company = self._create_test_company(
            qualifications=[
                {"name": "电力工程施工总承包", "level": "二级"},
                # 缺少另一个资质
            ]
        )
        project = self._create_test_project(
            required_qualifications=[
                {"name": "电力工程施工总承包", "level": "二级"},
                {"name": "ISO9001", "level": "认证"}
            ]
        )

        score = self.service._match_qualifications(project, company)
        assert 40 <= score <= 60  # 2个中匹配1个，约50分

    def test_qualification_match_none(self):
        """测试资质完全不匹配"""
        company = self._create_test_company(
            qualifications=[
                {"name": "建筑工程施工总承包", "level": "一级"}
            ]
        )
        project = self._create_test_project(
            required_qualifications=[
                {"name": "电力工程施工总承包", "level": "二级"}
            ]
        )

        score = self.service._match_qualifications(project, company)
        assert score < 30  # 完全不匹配

    def test_achievement_match_perfect(self):
        """测试业绩完全匹配"""
        company = self._create_test_company(
            achievements={
                "average_amount": 2000,  # 与项目预算相同
                "total_projects": 50
            }
        )
        project = self._create_test_project(budget=2000)

        score = self.service._match_achievements(project, company)
        assert score >= 100  # 完美匹配

    def test_achievement_match_too_small(self):
        """测试业绩规模过小"""
        company = self._create_test_company(
            achievements={
                "average_amount": 100,  # 远小于项目预算
                "total_projects": 10
            }
        )
        project = self._create_test_project(budget=5000)

        score = self.service._match_achievements(project, company)
        assert score < 70  # 规模不匹配

    def test_location_match_exact(self):
        """测试地域精确匹配"""
        company = self._create_test_company(target_areas=["广东", "江苏"])
        project = self._create_test_project(area="广东")

        score = self.service._match_location(project, company)
        assert score == 100.0

    def test_location_match_not_in_target(self):
        """测试地域不在目标区域"""
        company = self._create_test_company(target_areas=["北京", "上海"])
        project = self._create_test_project(area="广东")

        score = self.service._match_location(project, company)
        assert score == 30.0  # 不匹配但仍可跨区域投标

    def test_budget_match_in_range(self):
        """测试预算在范围内"""
        company = self._create_test_company(
            budget_range={"min": 500, "max": 5000}
        )
        project = self._create_test_project(budget=2000)

        score = self.service._match_budget(project, company)
        assert score == 100.0

    def test_budget_match_too_low(self):
        """测试预算过低"""
        company = self._create_test_company(
            budget_range={"min": 5000, "max": 10000}
        )
        project = self._create_test_project(budget=1000)

        score = self.service._match_budget(project, company)
        assert score < 80  # 预算过低

    def test_calculate_match_score(self):
        """测试综合匹配度计算"""
        company = self._create_test_company()
        project = self._create_test_project()

        score, details = self.service.calculate_match_score(project, company)

        assert 0 <= score <= 100
        assert "scores" in details
        assert "qualification" in details["scores"]
        assert "achievement" in details["scores"]
        assert "location" in details["scores"]
        assert "budget" in details["scores"]
        assert "weights" in details

        # 清理
        self.company_service.hard_delete_company(company.id)
        self.db.delete(project)
        self.db.commit()

    def test_recommend_projects_for_company(self):
        """测试为企业推荐项目"""
        # 创建企业
        company = self._create_test_company()

        # 创建多个项目
        proj1 = self._create_test_project(
            title_suffix="1",
            budget=2000,  # 匹配
            area="广东"   # 匹配
        )
        proj2 = self._create_test_project(
            title_suffix="2",
            budget=10000,  # 预算过大，可能不匹配
            area="北京"     # 地域不匹配
        )

        # 推荐
        recommendations = self.service.recommend_projects_for_company(
            company.id,
            min_score=50.0,
            limit=10
        )

        assert len(recommendations) >= 1
        assert recommendations[0]["match_score"] >= 50.0
        assert "project" in recommendations[0]
        assert "match_details" in recommendations[0]

        # 验证推荐结果按匹配度降序排列
        if len(recommendations) > 1:
            assert recommendations[0]["match_score"] >= recommendations[1]["match_score"]

        # 清理
        self.company_service.hard_delete_company(company.id)
        self.db.delete(proj1)
        self.db.delete(proj2)
        self.db.commit()

    def test_recommend_companies_for_project(self):
        """测试为项目推荐企业"""
        # 创建项目
        project = self._create_test_project()

        # 创建多个企业
        company1 = self._create_test_company(
            name_suffix="1",
            target_areas=["广东"],  # 匹配
            budget_range={"min": 1000, "max": 3000}  # 匹配
        )
        company2 = self._create_test_company(
            name_suffix="2",
            target_areas=["北京"],  # 不匹配
            budget_range={"min": 10000, "max": 50000}  # 不匹配
        )

        # 推荐
        recommendations = self.service.recommend_companies_for_project(
            project.id,
            min_score=50.0,
            limit=10
        )

        assert len(recommendations) >= 1
        assert recommendations[0]["match_score"] >= 50.0
        assert "company" in recommendations[0]
        assert "match_details" in recommendations[0]

        # 验证推荐结果按匹配度降序排列
        if len(recommendations) > 1:
            assert recommendations[0]["match_score"] >= recommendations[1]["match_score"]

        # 清理
        self.db.delete(project)
        self.company_service.hard_delete_company(company1.id)
        self.company_service.hard_delete_company(company2.id)
        self.db.commit()

    def test_no_projects_available(self):
        """测试没有可推荐项目的情况"""
        company = self._create_test_company()

        recommendations = self.service.recommend_projects_for_company(
            company.id,
            min_score=99.0,  # 设置极高阈值
            limit=10
        )

        # 清理
        self.company_service.hard_delete_company(company.id)

    def test_no_companies_available(self):
        """测试没有可推荐企业的情况"""
        project = self._create_test_project()

        recommendations = self.service.recommend_companies_for_project(
            project.id,
            min_score=99.0,  # 设置极高阈值
            limit=10
        )

        # 清理
        self.db.delete(project)
        self.db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

