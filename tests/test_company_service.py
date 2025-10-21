# tests/test_company_service.py
"""
企业画像服务单元测试
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.company_service import CompanyService
from backend.models import Company, CompanyScale
from backend.database import create_tables


class TestCompanyService:
    """企业服务测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        # 确保数据表存在
        create_tables()
        self.service = CompanyService()

    def test_create_company_basic(self):
        """测试创建基本企业信息"""
        company = self.service.create_company(
            name=f"测试企业_{pytest.__version__}",
            description="这是一个测试企业",
            scale=CompanyScale.MEDIUM
        )

        assert company is not None
        assert company.name.startswith("测试企业")
        assert company.scale == CompanyScale.MEDIUM.value
        assert company.is_active == 1

        # 清理
        self.service.hard_delete_company(company.id)

    def test_create_company_full(self):
        """测试创建完整企业信息"""
        company = self.service.create_company(
            name=f"完整测试企业_{pytest.__version__}",
            description="完整企业信息测试",
            scale=CompanyScale.LARGE,
            founded_year=2010,
            employee_count=200,
            registered_capital=5000,
            contact_person="张三",
            contact_phone="13800138000",
            contact_email="test@example.com",
            qualifications=[
                {"name": "电力施工", "level": "二级", "number": "A123", "expire_date": "2025-12-31"}
            ],
            capabilities={
                "fields": ["输变电", "配电"],
                "advantages": ["技术创新"]
            },
            target_areas=["广东", "江苏"],
            target_industries=["电力"],
            budget_range={"min": 100, "max": 5000}
        )

        assert company is not None
        assert company.founded_year == 2010
        assert company.employee_count == 200
        assert len(company.qualifications) == 1
        assert company.qualifications[0]["name"] == "电力施工"
        assert "输变电" in company.capabilities["fields"]
        assert "广东" in company.target_areas
        assert company.budget_range["min"] == 100

        # 清理
        self.service.hard_delete_company(company.id)

    def test_create_duplicate_company(self):
        """测试创建重复企业名称"""
        company_name = f"重复企业_{pytest.__version__}"
        company1 = self.service.create_company(name=company_name)
        assert company1 is not None

        company2 = self.service.create_company(name=company_name)
        assert company2 is None  # 应该失败

        # 清理
        self.service.hard_delete_company(company1.id)

    def test_get_company(self):
        """测试获取企业"""
        company = self.service.create_company(name=f"获取测试_{pytest.__version__}")
        assert company is not None

        fetched = self.service.get_company(company.id)
        assert fetched is not None
        assert fetched.id == company.id
        assert fetched.name == company.name

        # 清理
        self.service.hard_delete_company(company.id)

    def test_get_company_by_name(self):
        """测试根据名称获取企业"""
        company_name = f"名称获取测试_{pytest.__version__}"
        company = self.service.create_company(name=company_name)
        assert company is not None

        fetched = self.service.get_company_by_name(company_name)
        assert fetched is not None
        assert fetched.name == company_name

        # 清理
        self.service.hard_delete_company(company.id)

    def test_list_companies(self):
        """测试列出企业"""
        # 创建测试数据
        c1 = self.service.create_company(
            name=f"列表测试1_{pytest.__version__}",
            scale=CompanyScale.SMALL
        )
        c2 = self.service.create_company(
            name=f"列表测试2_{pytest.__version__}",
            scale=CompanyScale.LARGE
        )

        # 测试不过滤
        companies, count = self.service.list_companies(limit=10)
        assert count >= 2

        # 测试按规模过滤
        small_companies, small_count = self.service.list_companies(scale=CompanyScale.SMALL, limit=10)
        assert small_count >= 1

        # 清理
        self.service.hard_delete_company(c1.id)
        self.service.hard_delete_company(c2.id)

    def test_update_company(self):
        """测试更新企业"""
        company = self.service.create_company(name=f"更新测试_{pytest.__version__}")
        assert company is not None

        updated = self.service.update_company(
            company.id,
            {
                "description": "已更新的描述",
                "employee_count": 300,
                "target_areas": ["北京", "上海"]
            }
        )

        assert updated is not None
        assert updated.description == "已更新的描述"
        assert updated.employee_count == 300
        assert "北京" in updated.target_areas

        # 清理
        self.service.hard_delete_company(company.id)

    def test_delete_company(self):
        """测试软删除企业"""
        company = self.service.create_company(name=f"删除测试_{pytest.__version__}")
        assert company is not None
        assert company.is_active == 1

        success = self.service.delete_company(company.id)
        assert success is True

        # 验证软删除
        deleted = self.service.get_company(company.id)
        assert deleted is not None
        assert deleted.is_active == 0

        # 清理
        self.service.hard_delete_company(company.id)

    def test_search_companies(self):
        """测试搜索企业"""
        company = self.service.create_company(
            name=f"搜索测试企业_{pytest.__version__}",
            description="这是一个用于搜索测试的企业"
        )
        assert company is not None

        # 按名称搜索
        results = self.service.search_companies("搜索测试")
        assert len(results) >= 1
        assert any(c.name == company.name for c in results)

        # 按描述搜索
        results2 = self.service.search_companies("搜索测试的企业")
        assert len(results2) >= 1

        # 清理
        self.service.hard_delete_company(company.id)

    def test_add_qualification(self):
        """测试添加资质"""
        company = self.service.create_company(name=f"资质测试_{pytest.__version__}")
        assert company is not None
        assert len(company.qualifications or []) == 0

        qual = {"name": "ISO9001", "level": "认证", "number": "ISO123"}
        updated = self.service.add_qualification(company.id, qual)

        assert updated is not None
        assert len(updated.qualifications) == 1
        assert updated.qualifications[0]["name"] == "ISO9001"

        # 清理
        self.service.hard_delete_company(company.id)

    def test_remove_qualification(self):
        """测试移除资质"""
        company = self.service.create_company(
            name=f"移除资质测试_{pytest.__version__}",
            qualifications=[
                {"name": "资质A", "level": "一级"},
                {"name": "资质B", "level": "二级"}
            ]
        )
        assert company is not None
        assert len(company.qualifications) == 2

        updated = self.service.remove_qualification(company.id, "资质A")
        assert updated is not None
        assert len(updated.qualifications) == 1
        assert updated.qualifications[0]["name"] == "资质B"

        # 清理
        self.service.hard_delete_company(company.id)

    def test_get_statistics(self):
        """测试获取统计信息"""
        # 创建测试数据
        c1 = self.service.create_company(name=f"统计测试1_{pytest.__version__}", scale=CompanyScale.SMALL)
        c2 = self.service.create_company(name=f"统计测试2_{pytest.__version__}", scale=CompanyScale.MEDIUM)

        stats = self.service.get_statistics()

        assert stats is not None
        assert "total_companies" in stats
        assert "scale_distribution" in stats
        assert stats["total_companies"] >= 2

        # 清理
        self.service.hard_delete_company(c1.id)
        self.service.hard_delete_company(c2.id)

    def test_company_methods(self):
        """测试Company模型的辅助方法"""
        company = self.service.create_company(
            name=f"方法测试_{pytest.__version__}",
            qualifications=[
                {"name": "有效资质", "level": "一级", "expire_date": "2025-12-31"},
                {"name": "过期资质", "level": "二级", "expire_date": "2020-01-01"}
            ],
            target_areas=["广东", "江苏"],
            target_industries=["电力"],
            budget_range={"min": 100, "max": 1000}
        )

        # 测试get_active_qualifications
        active_quals = company.get_active_qualifications()
        assert len(active_quals) == 1
        assert active_quals[0]["name"] == "有效资质"

        # 测试is_in_budget_range
        assert company.is_in_budget_range(500) is True
        assert company.is_in_budget_range(50) is False
        assert company.is_in_budget_range(2000) is False

        # 测试is_target_area
        assert company.is_target_area("广东") is True
        assert company.is_target_area("北京") is False

        # 测试is_target_industry
        assert company.is_target_industry("电力") is True
        assert company.is_target_industry("建筑") is False

        # 清理
        self.service.hard_delete_company(company.id)


class TestCompanyIntegration:
    """集成测试"""

    def test_company_crud_flow(self):
        """测试完整的CRUD流程"""
        service = CompanyService()

        # 创建
        company = service.create_company(
            name=f"CRUD流程测试_{pytest.__version__}",
            description="初始描述",
            scale=CompanyScale.MEDIUM,
            target_areas=["广东"]
        )
        assert company is not None
        company_id = company.id

        # 读取
        fetched = service.get_company(company_id)
        assert fetched is not None
        assert fetched.description == "初始描述"

        # 更新
        updated = service.update_company(
            company_id,
            {"description": "更新后的描述", "target_areas": ["广东", "江苏"]}
        )
        assert updated.description == "更新后的描述"
        assert len(updated.target_areas) == 2

        # 软删除
        service.delete_company(company_id)
        deleted = service.get_company(company_id)
        assert deleted.is_active == 0

        # 物理删除
        service.hard_delete_company(company_id)
        final = service.get_company(company_id)
        assert final is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

