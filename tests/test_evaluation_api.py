#!/usr/bin/env python
"""
评估报告API单元测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main_multi_scenario import app
from backend.models import Company, Project, EvaluationReport
from backend.database import get_db_session, init_database

# 确保数据库已初始化
init_database()

client = TestClient(app)


@pytest.fixture
def db_session():
    """获取数据库会话"""
    session = get_db_session()
    yield session
    session.close()


@pytest.fixture
def sample_company(db_session):
    """创建测试企业"""
    company = db_session.query(Company).filter(Company.name == "测试科技有限公司").first()
    if not company:
        company = Company(
            id="test-company-eval-1",
            name="测试科技有限公司",
            description="一家专业的电力工程公司",
            scale="medium",
            employee_count=500,
            qualifications=[
                {"name": "电力施工总承包", "level": "二级", "expire_date": "2026-12-31"}
            ],
            achievements={
                "total_projects": 50,
                "success_rate": 0.8,
                "average_amount": 3000,
                "total_amount": 150000
            },
            target_areas=["广东", "江苏"],
            budget_range={"min": 1000, "max": 10000}
        )
        db_session.add(company)
        db_session.commit()
        db_session.refresh(company)

    yield company

    # 清理（可选）
    # db_session.delete(company)
    # db_session.commit()


@pytest.fixture
def sample_project(db_session):
    """创建测试项目"""
    project = db_session.query(Project).filter(Project.title == "XX变电站建设项目-测试").first()
    if not project:
        project = Project(
            id="test-project-eval-1",
            title="XX变电站建设项目-测试",
            description="新建500kV变电站一座",
            budget=5000,
            area="广东",
            industry="电力",
            project_type="工程施工",
            publisher="国家电网",
            source_platform="中国电力招投标网",
            deadline=datetime.now() + timedelta(days=60),
            required_qualifications=[
                {"name": "电力施工总承包", "level": "二级"}
            ]
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

    yield project

    # 清理（可选）
    # db_session.delete(project)
    # db_session.commit()


class TestEvaluationAPI:
    """评估报告API测试"""

    def test_generate_report(self, sample_company, sample_project):
        """测试生成评估报告"""
        response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "评估报告生成成功"
        assert "report_id" in data
        assert data["report_id"] is not None

        # 保存报告ID用于后续测试
        return data["report_id"]

    def test_get_report(self, sample_company, sample_project):
        """测试获取评估报告"""
        # 先生成一个报告
        gen_response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })
        report_id = gen_response.json()["report_id"]

        # 获取报告详情
        response = client.get(f"/api/v2/evaluation/reports/{report_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
        assert data["project_id"] == sample_project.id
        assert data["company_id"] == sample_company.id
        assert data["scenario_id"] == "tender"
        assert data["status"] == "completed"
        assert "overall_score" in data
        assert "recommendation_level" in data
        assert "conclusion" in data
        assert "project_summary" in data
        assert "qualification_analysis" in data
        assert "timeline_analysis" in data
        assert "historical_analysis" in data
        assert "risk_summary" in data
        assert "match_details" in data
        assert "recommendations" in data

    def test_list_reports(self, sample_company, sample_project):
        """测试列出评估报告"""
        # 生成2个报告
        for _ in range(2):
            client.post("/api/v2/evaluation/generate", json={
                "project_id": sample_project.id,
                "company_id": sample_company.id,
                "scenario_id": "tender"
            })

        # 列出所有报告
        response = client.get("/api/v2/evaluation/reports")

        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert "total_count" in data
        assert data["total_count"] >= 2
        assert len(data["reports"]) >= 2

        # 按企业筛选
        response = client.get(f"/api/v2/evaluation/reports?company_id={sample_company.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 2
        for report in data["reports"]:
            assert report["company_id"] == sample_company.id

    def test_quick_evaluate(self, sample_company, sample_project):
        """测试快速评估接口"""
        response = client.get(
            f"/api/v2/evaluation/projects/{sample_project.id}/evaluate/{sample_company.id}",
            params={"scenario_id": "tender"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project.id
        assert data["company_id"] == sample_company.id
        assert data["status"] == "completed"
        assert "overall_score" in data
        assert data["overall_score"] is not None
        assert "recommendation_level" in data

    def test_delete_report(self, sample_company, sample_project):
        """测试删除评估报告"""
        # 先生成一个报告
        gen_response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })
        report_id = gen_response.json()["report_id"]

        # 删除报告
        response = client.delete(f"/api/v2/evaluation/reports/{report_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证报告已删除
        get_response = client.get(f"/api/v2/evaluation/reports/{report_id}")
        assert get_response.status_code == 404

    def test_async_generate_report(self, sample_company, sample_project):
        """测试异步生成评估报告"""
        response = client.post("/api/v2/evaluation/generate-async", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "评估报告生成任务已提交到后台"

    def test_report_content_quality(self, sample_company, sample_project):
        """测试报告内容质量"""
        # 生成报告
        gen_response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })
        report_id = gen_response.json()["report_id"]

        # 获取报告
        response = client.get(f"/api/v2/evaluation/reports/{report_id}")
        data = response.json()

        # 验证项目概况
        assert "name" in data["project_summary"]
        assert data["project_summary"]["name"] == sample_project.title

        # 验证资质分析
        assert "required" in data["qualification_analysis"]
        assert "match_rate" in data["qualification_analysis"]
        assert 0 <= data["qualification_analysis"]["match_rate"] <= 1

        # 验证时间节点分析
        assert "deadline" in data["timeline_analysis"]
        assert "days_remaining" in data["timeline_analysis"]
        assert "urgency_level" in data["timeline_analysis"]

        # 验证历史分析
        assert "similar_projects_count" in data["historical_analysis"]
        assert "success_rate" in data["historical_analysis"]

        # 验证匹配详情
        assert isinstance(data["match_details"], dict)

        # 验证建议列表
        assert isinstance(data["recommendations"], list)
        if len(data["recommendations"]) > 0:
            rec = data["recommendations"][0]
            assert "priority" in rec
            assert "action" in rec

    def test_invalid_project_id(self, sample_company):
        """测试无效的项目ID"""
        response = client.post("/api/v2/evaluation/generate", json={
            "project_id": "non-existent-project",
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })

        assert response.status_code == 500

    def test_invalid_company_id(self, sample_project):
        """测试无效的企业ID"""
        response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": "non-existent-company",
            "scenario_id": "tender"
        })

        assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=line"])

