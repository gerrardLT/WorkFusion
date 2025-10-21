# backend/services/company_service.py
"""
企业画像服务
提供企业信息的CRUD操作、查询、搜索等功能
"""
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from backend.database import get_db_session
from backend.models import Company, CompanyScale
from src.config import get_settings

logger = logging.getLogger(__name__)


class CompanyService:
    """企业画像服务类"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.settings = get_settings()

    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self.db_session:
            return self.db_session
        return get_db_session()

    def create_company(
        self,
        name: str,
        description: Optional[str] = None,
        scale: CompanyScale = CompanyScale.MEDIUM,
        founded_year: Optional[int] = None,
        employee_count: Optional[int] = None,
        registered_capital: Optional[int] = None,
        contact_person: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        address: Optional[str] = None,
        website: Optional[str] = None,
        qualifications: Optional[List[Dict[str, Any]]] = None,
        capabilities: Optional[Dict[str, Any]] = None,
        achievements: Optional[Dict[str, Any]] = None,
        target_areas: Optional[List[str]] = None,
        target_industries: Optional[List[str]] = None,
        budget_range: Optional[Dict[str, int]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Company]:
        """
        创建企业画像
        Args:
            name: 企业名称（必填）
            其他参数见Company模型
        Returns:
            创建的Company对象，失败返回None
        """
        db = self._get_db()
        try:
            # 检查企业名称是否已存在
            existing = db.query(Company).filter(Company.name == name).first()
            if existing:
                logger.warning(f"企业名称 '{name}' 已存在，ID: {existing.id}")
                return None

            new_company = Company(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                scale=scale.value if isinstance(scale, CompanyScale) else scale,
                founded_year=founded_year,
                employee_count=employee_count,
                registered_capital=registered_capital,
                contact_person=contact_person,
                contact_phone=contact_phone,
                contact_email=contact_email,
                address=address,
                website=website,
                qualifications=qualifications or [],
                capabilities=capabilities or {},
                achievements=achievements or {},
                target_areas=target_areas or [],
                target_industries=target_industries or [],
                budget_range=budget_range or {},
                preferences=preferences or {},
                company_metadata=metadata or {},
                is_active=1
            )

            db.add(new_company)
            db.commit()
            db.refresh(new_company)
            logger.info(f"✅ 企业 '{name}' (ID: {new_company.id}) 创建成功")
            return new_company

        except Exception as e:
            db.rollback()
            logger.error(f"创建企业失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def get_company(self, company_id: str) -> Optional[Company]:
        """
        获取企业详情
        Args:
            company_id: 企业ID
        Returns:
            Company对象，未找到返回None
        """
        db = self._get_db()
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            return company
        finally:
            db.close()

    def get_company_by_name(self, name: str) -> Optional[Company]:
        """
        根据名称获取企业
        Args:
            name: 企业名称
        Returns:
            Company对象，未找到返回None
        """
        db = self._get_db()
        try:
            company = db.query(Company).filter(Company.name == name).first()
            return company
        finally:
            db.close()

    def list_companies(
        self,
        scale: Optional[CompanyScale] = None,
        target_area: Optional[str] = None,
        target_industry: Optional[str] = None,
        is_active: Optional[bool] = None,
        search_query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Company], int]:
        """
        列出企业列表，支持多种过滤条件
        Args:
            scale: 企业规模
            target_area: 目标区域
            target_industry: 目标行业
            is_active: 是否启用
            search_query: 关键词搜索（名称、描述）
            limit: 返回数量限制
            offset: 偏移量
        Returns:
            (企业列表, 总数)
        """
        db = self._get_db()
        try:
            query = db.query(Company)

            # 过滤条件
            if scale:
                query = query.filter(Company.scale == scale.value)

            if is_active is not None:
                query = query.filter(Company.is_active == (1 if is_active else 0))

            if target_area:
                # JSON字段查询需要特殊处理
                query = query.filter(Company.target_areas.contains([target_area]))

            if target_industry:
                query = query.filter(Company.target_industries.contains([target_industry]))

            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    or_(
                        Company.name.ilike(search_pattern),
                        Company.description.ilike(search_pattern)
                    )
                )

            total_count = query.count()
            companies = query.order_by(Company.updated_at.desc()).limit(limit).offset(offset).all()

            return companies, total_count

        finally:
            db.close()

    def update_company(
        self,
        company_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Company]:
        """
        更新企业信息
        Args:
            company_id: 企业ID
            updates: 更新字段字典
        Returns:
            更新后的Company对象，失败返回None
        """
        db = self._get_db()
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                logger.warning(f"企业 {company_id} 未找到")
                return None

            # 更新字段
            for key, value in updates.items():
                if hasattr(company, key):
                    if key == "scale" and isinstance(value, str):
                        # 验证CompanyScale枚举值
                        if value in [s.value for s in CompanyScale]:
                            setattr(company, key, value)
                    elif key == "is_active":
                        setattr(company, key, 1 if value else 0)
                    else:
                        setattr(company, key, value)

            company.updated_at = datetime.now()
            db.commit()
            db.refresh(company)
            logger.info(f"✅ 企业 '{company.name}' (ID: {company_id}) 更新成功")
            return company

        except Exception as e:
            db.rollback()
            logger.error(f"更新企业 {company_id} 失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def delete_company(self, company_id: str) -> bool:
        """
        删除企业（软删除，设置is_active=0）
        Args:
            company_id: 企业ID
        Returns:
            是否成功
        """
        db = self._get_db()
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return False

            company.is_active = 0
            company.updated_at = datetime.now()
            db.commit()
            logger.info(f"✅ 企业 '{company.name}' (ID: {company_id}) 已禁用")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"删除企业 {company_id} 失败: {str(e)}", exc_info=True)
            return False
        finally:
            db.close()

    def hard_delete_company(self, company_id: str) -> bool:
        """
        彻底删除企业（物理删除）
        Args:
            company_id: 企业ID
        Returns:
            是否成功
        """
        db = self._get_db()
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return False

            db.delete(company)
            db.commit()
            logger.info(f"✅ 企业 (ID: {company_id}) 已彻底删除")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"彻底删除企业 {company_id} 失败: {str(e)}", exc_info=True)
            return False
        finally:
            db.close()

    def search_companies(
        self,
        query: str,
        limit: int = 10
    ) -> List[Company]:
        """
        搜索企业（按名称和描述）
        Args:
            query: 搜索关键词
            limit: 返回数量限制
        Returns:
            企业列表
        """
        db = self._get_db()
        try:
            search_pattern = f"%{query}%"
            companies = db.query(Company).filter(
                Company.is_active == 1,
                or_(
                    Company.name.ilike(search_pattern),
                    Company.description.ilike(search_pattern)
                )
            ).limit(limit).all()
            return companies

        finally:
            db.close()

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取企业统计信息
        Returns:
            统计数据字典
        """
        db = self._get_db()
        try:
            total_count = db.query(Company).filter(Company.is_active == 1).count()

            scale_counts = db.query(
                Company.scale,
                func.count(Company.id)
            ).filter(Company.is_active == 1).group_by(Company.scale).all()

            return {
                "total_companies": total_count,
                "scale_distribution": {scale: count for scale, count in scale_counts},
                "active_companies": total_count
            }

        finally:
            db.close()

    def add_qualification(
        self,
        company_id: str,
        qualification: Dict[str, Any]
    ) -> Optional[Company]:
        """
        为企业添加资质
        Args:
            company_id: 企业ID
            qualification: 资质信息字典
                示例: {"name": "电力施工", "level": "二级", "number": "A123", "expire_date": "2025-12-31"}
        Returns:
            更新后的Company对象
        """
        db = self._get_db()
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return None

            qualifications = company.qualifications or []
            qualifications.append(qualification)
            company.qualifications = qualifications
            company.updated_at = datetime.now()

            db.commit()
            db.refresh(company)
            logger.info(f"✅ 为企业 '{company.name}' 添加资质: {qualification.get('name')}")
            return company

        except Exception as e:
            db.rollback()
            logger.error(f"添加资质失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def remove_qualification(
        self,
        company_id: str,
        qualification_name: str
    ) -> Optional[Company]:
        """
        移除企业资质
        Args:
            company_id: 企业ID
            qualification_name: 资质名称
        Returns:
            更新后的Company对象
        """
        db = self._get_db()
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return None

            qualifications = company.qualifications or []
            company.qualifications = [q for q in qualifications if q.get('name') != qualification_name]
            company.updated_at = datetime.now()

            db.commit()
            db.refresh(company)
            logger.info(f"✅ 从企业 '{company.name}' 移除资质: {qualification_name}")
            return company

        except Exception as e:
            db.rollback()
            logger.error(f"移除资质失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()


_company_service_instance: Optional[CompanyService] = None


def get_company_service() -> CompanyService:
    """获取CompanyService单例"""
    global _company_service_instance
    if _company_service_instance is None:
        _company_service_instance = CompanyService()
    return _company_service_instance

