# backend/services/evaluation_service.py
"""
项目评估服务
提供自动生成项目评估报告的功能
"""
import uuid
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from backend.database import get_db_session
from backend.models import (
    EvaluationReport, EvaluationStatus, RecommendationLevel,
    Project, Company, Risk, RiskReport
)
from backend.services.recommendation_service import get_recommendation_service
from backend.services.risk_service import get_risk_service
from src.config import get_settings

logger = logging.getLogger(__name__)


class EvaluationService:
    """项目评估服务类"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.settings = get_settings()
        self.recommendation_service = get_recommendation_service()
        self.risk_service = get_risk_service()

    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self.db_session:
            return self.db_session
        return get_db_session()

    def generate_report(
        self,
        project_id: str,
        company_id: str,
        scenario_id: str = "tender"
    ) -> Optional[EvaluationReport]:
        """
        生成项目评估报告
        Args:
            project_id: 项目ID
            company_id: 企业ID
            scenario_id: 场景ID
        Returns:
            生成的评估报告，失败返回None
        """
        db = self._get_db()
        start_time = time.time()

        try:
            # 获取项目和企业信息
            project = db.query(Project).filter(Project.id == project_id).first()
            company = db.query(Company).filter(Company.id == company_id).first()

            if not project:
                logger.error(f"项目 {project_id} 未找到")
                return None
            if not company:
                logger.error(f"企业 {company_id} 未找到")
                return None

            logger.info(f"开始生成评估报告：项目 '{project.title}' vs 企业 '{company.name}'")

            # 创建报告记录
            report_id = str(uuid.uuid4())
            report = EvaluationReport(
                id=report_id,
                project_id=project_id,
                company_id=company_id,
                scenario_id=scenario_id,
                title=f"{project.title} - {company.name} 评估报告",
                status=EvaluationStatus.PENDING.value
            )
            db.add(report)
            db.flush()

            # 1. 提取项目概况
            project_summary = self._extract_project_summary(project)

            # 2. 分析资质匹配
            qualification_analysis = self._analyze_qualifications(project, company)

            # 3. 分析时间节点
            timeline_analysis = self._analyze_timeline(project)

            # 4. 分析历史数据
            historical_analysis = self._analyze_historical_data(project, company, db)

            # 5. 获取风险摘要
            risk_summary = self._get_risk_summary(project_id, db)

            # 6. 计算匹配度详情
            match_score, match_details_raw = self.recommendation_service.calculate_match_score(project, company)
            match_details = match_details_raw.get("scores", {})

            # 7. 生成综合结论和推荐
            conclusion, recommendation_level, recommendations = self._generate_conclusion(
                match_score,
                qualification_analysis,
                risk_summary,
                historical_analysis
            )

            # 更新报告
            report.status = EvaluationStatus.COMPLETED.value
            report.overall_score = match_score
            report.recommendation_level = recommendation_level
            report.conclusion = conclusion
            report.project_summary = project_summary
            report.qualification_analysis = qualification_analysis
            report.timeline_analysis = timeline_analysis
            report.historical_analysis = historical_analysis
            report.risk_summary = risk_summary
            report.match_details = match_details
            report.recommendations = recommendations

            elapsed = time.time() - start_time
            report.evaluation_metadata = {
                "generation_time": round(elapsed, 2),
                "data_sources": ["项目信息", "企业画像", "匹配算法", "风险识别"],
                "version": "1.0"
            }

            db.commit()
            db.refresh(report)

            logger.info(f"✅ 评估报告生成完成，耗时 {elapsed:.2f} 秒，综合评分: {match_score:.2f}")
            return report

        except Exception as e:
            db.rollback()
            logger.error(f"生成评估报告失败: {str(e)}", exc_info=True)

            # 标记报告为失败
            if 'report' in locals():
                report.status = EvaluationStatus.FAILED.value
                db.commit()

            return None
        finally:
            db.close()

    def _extract_project_summary(self, project: Project) -> Dict[str, Any]:
        """提取项目概况摘要"""
        return {
            "name": project.title,
            "budget": project.budget,
            "area": project.area,
            "industry": project.industry,
            "project_type": project.project_type,
            "deadline": project.deadline.isoformat() if project.deadline else None,
            "publisher": project.publisher,
            "source_platform": project.source_platform,
            "description": project.description[:200] if project.description else None,
            "key_points": []  # 可以后续通过LLM提取关键点
        }

    def _analyze_qualifications(self, project: Project, company: Company) -> Dict[str, Any]:
        """分析资质匹配情况"""
        required_quals = project.required_qualifications or []
        company_quals = company.get_active_qualifications()

        matched = []
        missing = []

        for req_qual in required_quals:
            req_name = req_qual.get("name", "")
            req_level = req_qual.get("level", "")

            # 检查是否匹配
            is_matched = False
            for c_qual in company_quals:
                c_name = c_qual.get("name", "")
                if req_name.lower() in c_name.lower() or c_name.lower() in req_name.lower():
                    is_matched = True
                    break

            qual_item = {
                "name": req_name,
                "level": req_level,
                "matched": is_matched
            }

            if is_matched:
                matched.append(qual_item)
            else:
                missing.append(req_name)

        match_rate = len(matched) / len(required_quals) if required_quals else 1.0

        return {
            "required": required_quals,
            "matched": matched,
            "missing": missing,
            "match_rate": round(match_rate, 2),
            "total_required": len(required_quals),
            "total_matched": len(matched)
        }

    def _analyze_timeline(self, project: Project) -> Dict[str, Any]:
        """分析时间节点"""
        if not project.deadline:
            return {
                "deadline": None,
                "days_remaining": None,
                "urgency_level": "unknown"
            }

        days_remaining = project.days_until_deadline()

        # 判断紧急程度
        if days_remaining < 0:
            urgency_level = "expired"
        elif days_remaining <= 7:
            urgency_level = "critical"
        elif days_remaining <= 30:
            urgency_level = "high"
        elif days_remaining <= 60:
            urgency_level = "medium"
        else:
            urgency_level = "low"

        key_dates = [
            {
                "event": "投标截止时间",
                "date": project.deadline.isoformat(),
                "is_critical": True
            }
        ]

        if project.bid_opening_date:
            key_dates.append({
                "event": "开标时间",
                "date": project.bid_opening_date.isoformat(),
                "is_critical": False
            })

        return {
            "deadline": project.deadline.isoformat(),
            "days_remaining": days_remaining,
            "urgency_level": urgency_level,
            "key_dates": key_dates
        }

    def _analyze_historical_data(
        self,
        project: Project,
        company: Company,
        db: Session
    ) -> Dict[str, Any]:
        """分析历史中标数据"""
        # 简化版：基于企业业绩数据
        achievements = company.achievements or {}

        return {
            "similar_projects_count": achievements.get("total_projects", 0),
            "success_rate": achievements.get("success_rate", 0),
            "average_bid_amount": achievements.get("average_amount", 0),
            "total_amount": achievements.get("total_amount", 0),
            "major_projects": achievements.get("major_projects", [])[:3],  # 只取前3个
            "clients": achievements.get("clients", [])[:5],  # 只取前5个
            "success_factors": ["历史业绩良好", "客户资源丰富"] if achievements.get("success_rate", 0) > 0.7 else []
        }

    def _get_risk_summary(self, project_id: str, db: Session) -> Dict[str, Any]:
        """获取风险摘要"""
        # 风险是基于document的，所以需要找到项目关联的document
        # 由于当前项目模型中没有直接的document关联，我们先返回一个默认的风险摘要
        # TODO: 如果项目有关联的招标文档，可以通过document_id查询风险

        # 暂时返回默认值，后续可以根据项目-文档关系扩展
        return {
            "total_risks": 0,
            "high_risks": 0,
            "medium_risks": 0,
            "low_risks": 0,
            "overall_risk_level": "low",
            "key_risks": []
        }

    def _generate_conclusion(
        self,
        match_score: float,
        qualification_analysis: Dict[str, Any],
        risk_summary: Dict[str, Any],
        historical_analysis: Dict[str, Any]
    ) -> tuple[str, str, List[Dict[str, Any]]]:
        """
        生成综合结论和建议
        Returns:
            (结论文本, 推荐等级, 建议列表)
        """
        # 判断推荐等级
        if match_score >= 85:
            recommendation_level = RecommendationLevel.HIGHLY_RECOMMENDED.value
        elif match_score >= 70:
            recommendation_level = RecommendationLevel.RECOMMENDED.value
        elif match_score >= 60:
            recommendation_level = RecommendationLevel.NEUTRAL.value
        elif match_score >= 40:
            recommendation_level = RecommendationLevel.NOT_RECOMMENDED.value
        else:
            recommendation_level = RecommendationLevel.STRONGLY_NOT_RECOMMENDED.value

        # 生成结论文本
        conclusion_parts = []
        conclusion_parts.append(f"综合评分：{match_score:.1f}/100")
        conclusion_parts.append(f"资质匹配率：{qualification_analysis.get('match_rate', 0)*100:.0f}%")

        if risk_summary.get('high_risks', 0) > 0:
            conclusion_parts.append(f"高风险项：{risk_summary['high_risks']}个")

        success_rate = historical_analysis.get('success_rate', 0)
        if success_rate > 0:
            conclusion_parts.append(f"历史中标率：{success_rate*100:.0f}%")

        conclusion = "，".join(conclusion_parts) + "。"

        # 根据不同等级生成建议
        recommendations = []

        # 资质相关建议
        missing_quals = qualification_analysis.get('missing', [])
        if missing_quals:
            recommendations.append({
                "priority": "high",
                "category": "qualification",
                "action": f"补充缺失资质：{', '.join(missing_quals[:3])}"
            })

        # 风险相关建议
        if risk_summary.get('high_risks', 0) > 0:
            recommendations.append({
                "priority": "high",
                "category": "risk",
                "action": "重点关注高风险项，制定应对措施"
            })

        # 历史业绩建议
        if success_rate < 0.5:
            recommendations.append({
                "priority": "medium",
                "category": "experience",
                "action": "准备类似项目业绩证明材料，增强竞争力"
            })

        # 通用建议
        if match_score >= 70:
            recommendations.append({
                "priority": "medium",
                "category": "preparation",
                "action": "尽早启动投标准备工作，确保文件齐全"
            })

        return conclusion, recommendation_level, recommendations

    def get_report(self, report_id: str) -> Optional[EvaluationReport]:
        """获取评估报告"""
        db = self._get_db()
        try:
            report = db.query(EvaluationReport).filter(
                EvaluationReport.id == report_id
            ).first()
            return report
        finally:
            db.close()

    def list_reports(
        self,
        company_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[EvaluationReport], int]:
        """列出评估报告"""
        db = self._get_db()
        try:
            query = db.query(EvaluationReport)

            if company_id:
                query = query.filter(EvaluationReport.company_id == company_id)
            if project_id:
                query = query.filter(EvaluationReport.project_id == project_id)

            total_count = query.count()
            reports = query.order_by(
                EvaluationReport.created_at.desc()
            ).limit(limit).offset(offset).all()

            return reports, total_count
        finally:
            db.close()

    def delete_report(self, report_id: str) -> bool:
        """删除评估报告"""
        db = self._get_db()
        try:
            report = db.query(EvaluationReport).filter(
                EvaluationReport.id == report_id
            ).first()

            if not report:
                return False

            db.delete(report)
            db.commit()
            logger.info(f"✅ 评估报告 {report_id} 已删除")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"删除评估报告失败: {str(e)}", exc_info=True)
            return False
        finally:
            db.close()


_evaluation_service_instance: Optional[EvaluationService] = None


def get_evaluation_service() -> EvaluationService:
    """获取EvaluationService单例"""
    global _evaluation_service_instance
    if _evaluation_service_instance is None:
        _evaluation_service_instance = EvaluationService()
    return _evaluation_service_instance

