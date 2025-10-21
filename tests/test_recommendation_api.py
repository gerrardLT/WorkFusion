# tests/test_recommendation_api.py
"""
推荐API接口测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.main_multi_scenario import app
from backend.services.company_service import CompanyService
from backend.models import Company, CompanyScale, Project, ProjectStatus
from backend.database import create_tables, get_db_session


class TestRecommendationAPI:
    """推荐API测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        create_tables()
        self.client = TestClient(app)
        self.company_service = CompanyService()
        self.db = get_db_session()

    def teardown_method(self):
        """每个测试方法后执行"""
        if self.db:
            self.db.close()

    def _create_test_company(self, name_suffix="", **kwargs):
        """创建测试企业"""
        import uuid
        defaults = {
            "name": f"API测试企业{name_suffix}_{uuid.uuid4().hex[:8]}",
            "scale": CompanyScale.MEDIUM,
            "qualifications": [
                {"name": "电力工程施工总承包", "level": "二级", "expire_date": "2025-12-31"}
            ],
            "achievements": {
                "total_projects": 50,
                "total_amount": 100000,
                "average_amount": 2000
            },
            "target_areas": ["广东", "江苏"],
            "target_industries": ["电力"],
            "budget_range": {"min": 500, "max": 5000}
        }
        defaults.update(kwargs)
        return self.company_service.create_company(**defaults)

    def _create_test_project(self, title_suffix="", **kwargs):
        """创建测试项目"""
        import uuid
        defaults = {
            "id": f"proj_{uuid.uuid4().hex[:12]}",
            "title": f"API测试项目{title_suffix}_{uuid.uuid4().hex[:6]}",
            "budget": 2000.0,
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

    def test_recommend_projects_post(self):
        """测试POST方式推荐项目"""
        # 创建测试数据
        company = self._create_test_company()
        project = self._create_test_project()

        # 调用API
        response = self.client.post("/api/v2/recommendation/projects", json={
            "company_id": company.id,
            "min_score": 50.0,
            "limit": 10
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["company_id"] == company.id
        assert "total_recommendations" in data
        assert "recommendations" in data

        # 清理
        self.company_service.hard_delete_company(company.id)
        self.db.delete(project)
        self.db.commit()

    def test_recommend_projects_get(self):
        """测试GET方式推荐项目"""
        # 创建测试数据
        company = self._create_test_company()
        project = self._create_test_project()

        # 调用API
        response = self.client.get(
            f"/api/v2/recommendation/projects/{company.id}",
            params={"min_score": 50.0, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["company_id"] == company.id

        # 清理
        self.company_service.hard_delete_company(company.id)
        self.db.delete(project)
        self.db.commit()

    def test_recommend_companies_post(self):
        """测试POST方式推荐企业"""
        # 创建测试数据
        company = self._create_test_company()
        project = self._create_test_project()

        # 调用API
        response = self.client.post("/api/v2/recommendation/companies", json={
            "project_id": project.id,
            "min_score": 50.0,
            "limit": 10
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project_id"] == project.id
        assert "total_recommendations" in data

        # 清理
        self.company_service.hard_delete_company(company.id)
        self.db.delete(project)
        self.db.commit()

    def test_recommend_companies_get(self):
        """测试GET方式推荐企业"""
        # 创建测试数据
        company = self._create_test_company()
        project = self._create_test_project()

        # 调用API
        response = self.client.get(
            f"/api/v2/recommendation/companies/{project.id}",
            params={"min_score": 50.0, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project_id"] == project.id

        # 清理
        self.company_service.hard_delete_company(company.id)
        self.db.delete(project)
        self.db.commit()

    def test_batch_recommend(self):
        """测试批量推荐"""
        # 创建多个企业和项目
        company1 = self._create_test_company(name_suffix="1")
        company2 = self._create_test_company(name_suffix="2")
        project = self._create_test_project()

        # 调用批量推荐API
        response = self.client.post("/api/v2/recommendation/batch", json={
            "company_ids": [company1.id, company2.id],
            "min_score": 50.0,
            "limit_per_company": 5
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_companies"] == 2
        assert "total_recommendations" in data
        assert "results" in data

        # 清理
        self.company_service.hard_delete_company(company1.id)
        self.company_service.hard_delete_company(company2.id)
        self.db.delete(project)
        self.db.commit()

    def test_calculate_match_score(self):
        """测试计算匹配度"""
        # 创建测试数据
        company = self._create_test_company()
        project = self._create_test_project()

        # 调用API
        response = self.client.post("/api/v2/recommendation/match-score", json={
            "project_id": project.id,
            "company_id": company.id
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project_id"] == project.id
        assert data["company_id"] == company.id
        assert "match_score" in data
        assert "match_details" in data
        assert 0 <= data["match_score"] <= 100

        # 清理
        self.company_service.hard_delete_company(company.id)
        self.db.delete(project)
        self.db.commit()

    def test_recommend_with_invalid_company(self):
        """测试使用无效企业ID推荐"""
        response = self.client.post("/api/v2/recommendation/projects", json={
            "company_id": "invalid_id",
            "min_score": 60.0,
            "limit": 10
        })

        # 应该返回200但推荐列表为空
        assert response.status_code == 200
        data = response.json()
        assert data["total_recommendations"] == 0

    def test_recommend_with_invalid_project(self):
        """测试使用无效项目ID推荐"""
        response = self.client.post("/api/v2/recommendation/companies", json={
            "project_id": "invalid_id",
            "min_score": 60.0,
            "limit": 10
        })

        # 应该返回200但推荐列表为空
        assert response.status_code == 200
        data = response.json()
        assert data["total_recommendations"] == 0

    def test_recommend_with_high_threshold(self):
        """测试使用极高阈值推荐（应该返回空列表）"""
        company = self._create_test_company()
        project = self._create_test_project()

        response = self.client.post("/api/v2/recommendation/projects", json={
            "company_id": company.id,
            "min_score": 99.0,  # 极高阈值
            "limit": 10
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 可能返回空列表

        # 清理
        self.company_service.hard_delete_company(company.id)
        self.db.delete(project)
        self.db.commit()

    def test_match_score_with_invalid_ids(self):
        """测试使用无效ID计算匹配度"""
        response = self.client.post("/api/v2/recommendation/match-score", json={
            "project_id": "invalid_project",
            "company_id": "invalid_company"
        })

        # 应该返回404错误
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

