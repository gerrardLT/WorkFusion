# backend/services/recommendation_service.py
"""
招标项目推荐服务
基于企业画像和项目信息，计算匹配度并推荐高匹配度项目
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher

from sqlalchemy.orm import Session
from backend.database import get_db_session
from backend.models import Company, Project, ProjectStatus
from src.config import get_settings

logger = logging.getLogger(__name__)


class RecommendationService:
    """推荐服务类"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.settings = get_settings()

        # 匹配权重配置
        self.weights = {
            "qualification": 0.4,  # 资质匹配权重 40%
            "achievement": 0.3,    # 业绩匹配权重 30%
            "location": 0.2,       # 地域匹配权重 20%
            "budget": 0.1          # 预算匹配权重 10%
        }

    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self.db_session:
            return self.db_session
        return get_db_session()

    def calculate_match_score(
        self,
        project: Project,
        company: Company
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算项目与企业的匹配度
        Args:
            project: 招标项目
            company: 企业画像
        Returns:
            (匹配度分数 0-100, 详细分数明细)
        """
        scores = {}

        # 1. 资质匹配（40%）
        qualification_score = self._match_qualifications(project, company)
        scores["qualification"] = qualification_score

        # 2. 业绩匹配（30%）
        achievement_score = self._match_achievements(project, company)
        scores["achievement"] = achievement_score

        # 3. 地域匹配（20%）
        location_score = self._match_location(project, company)
        scores["location"] = location_score

        # 4. 预算匹配（10%）
        budget_score = self._match_budget(project, company)
        scores["budget"] = budget_score

        # 计算加权总分
        total_score = (
            qualification_score * self.weights["qualification"] +
            achievement_score * self.weights["achievement"] +
            location_score * self.weights["location"] +
            budget_score * self.weights["budget"]
        )

        details = {
            "total_score": round(total_score, 2),
            "scores": scores,
            "weights": self.weights,
            "project_id": project.id,
            "project_title": project.title,
            "company_id": company.id,
            "company_name": company.name
        }

        return total_score, details

    def _match_qualifications(self, project: Project, company: Company) -> float:
        """
        资质匹配（0-100分）
        逻辑：
        - 项目要求的资质企业全部具备：100分
        - 部分具备：按比例计分
        - 完全不具备：0分
        """
        required_quals = project.required_qualifications or []
        if not required_quals:
            return 100.0  # 无资质要求，满分

        company_quals = company.get_active_qualifications()
        if not company_quals:
            return 0.0  # 企业无有效资质

        # 提取企业资质名称列表
        company_qual_names = {q.get("name", "").lower() for q in company_quals}

        matched_count = 0
        for req_qual in required_quals:
            req_name = req_qual.get("name", "").lower()

            # 精确匹配
            if req_name in company_qual_names:
                matched_count += 1
            else:
                # 模糊匹配（关键词包含）
                for c_name in company_qual_names:
                    if req_name in c_name or c_name in req_name:
                        matched_count += 0.5  # 模糊匹配算0.5分
                        break

        score = (matched_count / len(required_quals)) * 100
        return min(score, 100.0)

    def _match_achievements(self, project: Project, company: Company) -> float:
        """
        业绩匹配（0-100分）
        逻辑：
        - 比较企业历史项目金额与当前项目预算
        - 企业平均项目金额在项目预算的 0.5-2倍之间：100分
        - 过小或过大：按比例扣分
        """
        if not project.budget:
            return 80.0  # 项目无预算信息，给中等分数

        achievements = company.achievements or {}
        avg_amount = achievements.get("average_amount", 0)
        total_projects = achievements.get("total_projects", 0)

        if not avg_amount or total_projects == 0:
            return 50.0  # 企业无业绩记录，给低分

        # 计算业绩匹配度
        ratio = avg_amount / project.budget

        if 0.5 <= ratio <= 2.0:
            # 理想范围：企业平均项目规模与当前项目接近
            score = 100.0
        elif 0.3 <= ratio < 0.5 or 2.0 < ratio <= 3.0:
            # 可接受范围：略小或略大
            score = 80.0
        elif 0.1 <= ratio < 0.3 or 3.0 < ratio <= 5.0:
            # 勉强接受：明显不匹配
            score = 60.0
        else:
            # 严重不匹配
            score = 40.0

        # 根据历史项目数量调整分数（项目越多，信誉越高）
        if total_projects >= 100:
            score += 5
        elif total_projects >= 50:
            score += 3
        elif total_projects >= 20:
            score += 1

        return min(score, 100.0)

    def _match_location(self, project: Project, company: Company) -> float:
        """
        地域匹配（0-100分）
        逻辑：
        - 项目地点在企业目标区域内：100分
        - 不在但相邻：70分
        - 完全不匹配：30分（仍有可能跨区域投标）
        """
        if not project.area:
            return 80.0  # 项目无地域信息

        target_areas = company.target_areas or []
        if not target_areas:
            return 80.0  # 企业无区域限制，视为可以接受

        # 精确匹配
        if project.area in target_areas:
            return 100.0

        # 定义相邻省份（简化版，实际可以用更完整的地理关系）
        adjacent_provinces = {
            "北京": ["天津", "河北"],
            "天津": ["北京", "河北"],
            "上海": ["江苏", "浙江"],
            "广东": ["广西", "福建", "江西", "湖南", "海南"],
            "江苏": ["上海", "浙江", "安徽", "山东"],
            "浙江": ["上海", "江苏", "安徽", "福建", "江西"],
            # 可扩展更多...
        }

        # 检查相邻省份
        project_adjacent = adjacent_provinces.get(project.area, [])
        for target in target_areas:
            if target in project_adjacent:
                return 70.0

        # 完全不匹配，但仍可跨区域投标
        return 30.0

    def _match_budget(self, project: Project, company: Company) -> float:
        """
        预算匹配（0-100分）
        逻辑：
        - 项目预算在企业目标预算范围内：100分
        - 超出范围：按偏离程度扣分
        """
        if not project.budget:
            return 80.0  # 项目无预算信息

        budget_range = company.budget_range or {}
        if not budget_range:
            return 80.0  # 企业无预算限制

        min_budget = budget_range.get("min", 0)
        max_budget = budget_range.get("max", float('inf'))

        if min_budget <= project.budget <= max_budget:
            return 100.0

        # 计算偏离程度
        if project.budget < min_budget:
            ratio = project.budget / min_budget
            if ratio >= 0.7:
                return 80.0
            elif ratio >= 0.5:
                return 60.0
            else:
                return 40.0
        else:  # project.budget > max_budget
            ratio = max_budget / project.budget
            if ratio >= 0.7:
                return 80.0
            elif ratio >= 0.5:
                return 60.0
            else:
                return 40.0

    def recommend_projects_for_company(
        self,
        company_id: str,
        min_score: float = 60.0,
        limit: int = 10,
        status: ProjectStatus = ProjectStatus.ACTIVE
    ) -> List[Dict[str, Any]]:
        """
        为企业推荐高匹配度项目
        Args:
            company_id: 企业ID
            min_score: 最低匹配分数阈值
            limit: 返回数量限制
            status: 项目状态过滤
        Returns:
            推荐项目列表（按匹配度降序）
        """
        db = self._get_db()
        try:
            # 获取企业信息
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                logger.warning(f"企业 {company_id} 未找到")
                return []

            # 获取候选项目
            projects_query = db.query(Project).filter(Project.status == status.value)

            # 如果企业有目标行业，优先推荐相关行业项目
            if company.target_industries:
                projects_query = projects_query.filter(
                    Project.industry.in_(company.target_industries)
                )

            projects = projects_query.all()

            if not projects:
                logger.info(f"没有找到符合条件的项目")
                return []

            # 计算每个项目的匹配度
            recommendations = []
            for project in projects:
                score, details = self.calculate_match_score(project, company)

                if score >= min_score:
                    recommendations.append({
                        "project": project.to_dict(),
                        "match_score": score,
                        "match_details": details,
                        "days_until_deadline": project.days_until_deadline()
                    })

            # 按匹配度降序排序
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)

            logger.info(f"为企业 '{company.name}' 推荐了 {len(recommendations[:limit])} 个项目")
            return recommendations[:limit]

        finally:
            db.close()

    def recommend_companies_for_project(
        self,
        project_id: str,
        min_score: float = 60.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        为项目推荐高匹配度企业
        Args:
            project_id: 项目ID
            min_score: 最低匹配分数阈值
            limit: 返回数量限制
        Returns:
            推荐企业列表（按匹配度降序）
        """
        db = self._get_db()
        try:
            # 获取项目信息
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                logger.warning(f"项目 {project_id} 未找到")
                return []

            # 获取所有活跃企业
            companies = db.query(Company).filter(Company.is_active == 1).all()

            if not companies:
                logger.info(f"没有找到活跃企业")
                return []

            # 计算每个企业的匹配度
            recommendations = []
            for company in companies:
                score, details = self.calculate_match_score(project, company)

                if score >= min_score:
                    recommendations.append({
                        "company": company.to_dict(),
                        "match_score": score,
                        "match_details": details
                    })

            # 按匹配度降序排序
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)

            logger.info(f"为项目 '{project.title}' 推荐了 {len(recommendations[:limit])} 个企业")
            return recommendations[:limit]

        finally:
            db.close()


_recommendation_service_instance: Optional[RecommendationService] = None


def get_recommendation_service() -> RecommendationService:
    """获取RecommendationService单例"""
    global _recommendation_service_instance
    if _recommendation_service_instance is None:
        _recommendation_service_instance = RecommendationService()
    return _recommendation_service_instance

