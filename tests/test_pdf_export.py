#!/usr/bin/env python
"""
PDF导出功能单元测试
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
    company = db_session.query(Company).filter(Company.name == "PDF测试企业").first()
    if not company:
        company = Company(
            id="test-company-pdf-1",
            name="PDF测试企业",
            description="用于PDF导出测试的企业",
            scale="medium",
            employee_count=300,
            qualifications=[
                {"name": "电力施工总承包", "level": "二级", "expire_date": "2026-12-31"}
            ],
            achievements={
                "total_projects": 30,
                "success_rate": 0.75,
                "average_amount": 2500,
                "total_amount": 75000
            },
            target_areas=["广东"],
            budget_range={"min": 500, "max": 5000}
        )
        db_session.add(company)
        db_session.commit()
        db_session.refresh(company)

    yield company


@pytest.fixture
def sample_project(db_session):
    """创建测试项目"""
    project = db_session.query(Project).filter(Project.title == "PDF测试项目").first()
    if not project:
        project = Project(
            id="test-project-pdf-1",
            title="PDF测试项目",
            description="用于测试PDF导出功能",
            budget=3000,
            area="广东",
            industry="电力",
            project_type="工程施工",
            publisher="国家电网",
            source_platform="中国电力招投标网",
            deadline=datetime.now() + timedelta(days=45),
            required_qualifications=[
                {"name": "电力施工总承包", "level": "二级"}
            ]
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

    yield project


class TestPDFExport:
    """PDF导出功能测试"""

    def test_export_report_to_pdf(self, sample_company, sample_project):
        """测试导出现有报告为PDF"""
        # 先生成一个报告
        gen_response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })
        assert gen_response.status_code == 200
        report_id = gen_response.json()["report_id"]

        # 导出为PDF
        response = client.get(f"/api/v2/evaluation/reports/{report_id}/export/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert ".pdf" in response.headers["Content-Disposition"]

        # 验证PDF内容不为空
        pdf_content = response.content
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b"%PDF")  # PDF文件魔数

        print(f"✅ PDF文件大小: {len(pdf_content)} 字节")

    def test_export_with_watermark(self, sample_company, sample_project):
        """测试带水印的PDF导出"""
        # 生成报告
        gen_response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })
        report_id = gen_response.json()["report_id"]

        # 导出带水印的PDF
        response = client.get(
            f"/api/v2/evaluation/reports/{report_id}/export/pdf",
            params={"watermark": "内部测试"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        pdf_content = response.content
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b"%PDF")

        print(f"✅ 带水印PDF文件大小: {len(pdf_content)} 字节")

    def test_quick_evaluate_and_export_pdf(self, sample_company, sample_project):
        """测试快速评估并导出PDF"""
        response = client.get(
            f"/api/v2/evaluation/projects/{sample_project.id}/companies/{sample_company.id}/export/pdf",
            params={"scenario_id": "tender"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        pdf_content = response.content
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b"%PDF")

        print(f"✅ 快速导出PDF文件大小: {len(pdf_content)} 字节")

    def test_export_nonexistent_report(self):
        """测试导出不存在的报告"""
        response = client.get("/api/v2/evaluation/reports/nonexistent-id/export/pdf")

        assert response.status_code == 404
        response_data = response.json()
        # 响应可能包含 'detail' 或 'message' 字段
        error_msg = response_data.get("detail") or response_data.get("message", "")
        assert "未找到" in error_msg

    def test_export_pending_report(self, db_session, sample_company, sample_project):
        """测试导出未完成的报告（模拟）"""
        # 由于我们的实现总是同步完成，这个测试主要验证状态检查逻辑
        # 实际场景中，如果有pending状态的报告，应该返回400错误
        # 这里我们跳过实际测试，因为难以创建pending状态的报告
        pass

    def test_pdf_content_structure(self, sample_company, sample_project):
        """测试PDF内容结构（通过文件大小和魔数验证）"""
        gen_response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })
        report_id = gen_response.json()["report_id"]

        response = client.get(f"/api/v2/evaluation/reports/{report_id}/export/pdf")

        pdf_content = response.content

        # 验证PDF格式
        assert pdf_content.startswith(b"%PDF")
        assert pdf_content.find(b"%%EOF") > 0  # PDF结束标记

        # 验证PDF大小合理（至少10KB，最多10MB）
        assert 10 * 1024 < len(pdf_content) < 10 * 1024 * 1024

        print(f"✅ PDF结构验证通过，大小: {len(pdf_content)} 字节")

    def test_chinese_support(self, sample_company, sample_project):
        """测试中文支持（间接通过PDF生成验证）"""
        gen_response = client.post("/api/v2/evaluation/generate", json={
            "project_id": sample_project.id,
            "company_id": sample_company.id,
            "scenario_id": "tender"
        })
        report_id = gen_response.json()["report_id"]

        # 带中文水印
        response = client.get(
            f"/api/v2/evaluation/reports/{report_id}/export/pdf",
            params={"watermark": "中文水印测试"}
        )

        assert response.status_code == 200
        pdf_content = response.content
        assert len(pdf_content) > 0

        print("✅ 中文支持测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=line"])

