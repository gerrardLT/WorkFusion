"""
风险识别服务
负责自动识别招投标文档中的风险条款
"""

import sys
import uuid
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import get_db_session
from backend.models import Document, Risk, RiskReport, RiskLevel, RiskType
from src.questions_processing import QuestionsProcessor
from src.config import get_settings
import logging

logger = logging.getLogger(__name__)


class RiskService:
    """风险识别服务类"""

    def __init__(self):
        self.settings = get_settings()
        self.db = get_db_session

    def detect_risks(
        self,
        document_id: str,
        scenario_id: str = "tender"
    ) -> Optional[str]:
        """
        为指定文档检测风险

        Args:
            document_id: 文档ID
            scenario_id: 场景ID（默认为招投标场景）

        Returns:
            生成的风险报告ID，失败返回None
        """
        try:
            logger.info(f"开始为文档 {document_id} 检测风险 (场景: {scenario_id})")

            with self.db() as db:
                # 1. 验证文档是否存在
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    logger.error(f"文档 {document_id} 不存在")
                    return None

                # 2. 检查是否已存在风险报告
                existing_report = db.query(RiskReport).filter(
                    RiskReport.document_id == document_id
                ).first()

                if existing_report:
                    logger.warning(f"文档 {document_id} 已存在风险报告，将更新现有报告")
                    report_id = existing_report.id
                    # 删除旧风险项
                    db.query(Risk).filter(Risk.document_id == document_id).delete()
                else:
                    # 创建新报告
                    report_id = str(uuid.uuid4())
                    report = RiskReport(
                        id=report_id,
                        document_id=document_id,
                        scenario_id=scenario_id,
                        title=f"{document.title} - 风险报告",
                        generation_method="auto"
                    )
                    db.add(report)
                    db.commit()

                # 3. 初始化问题处理器
                questions_processor = QuestionsProcessor(
                    api_provider="dashscope",
                    scenario_id=scenario_id
                )

                # 4. 通过LLM识别不同类型的风险
                risks_data = self._detect_all_risk_types(
                    questions_processor,
                    document,
                    scenario_id
                )

                if not risks_data:
                    logger.error(f"未能从文档 {document_id} 识别风险")
                    return None

                # 5. 保存风险项到数据库
                risk_count = 0
                high_count = 0
                medium_count = 0
                low_count = 0

                for risk_data in risks_data:
                    risk = self._create_risk_from_data(
                        document_id=document_id,
                        scenario_id=scenario_id,
                        risk_data=risk_data
                    )
                    db.add(risk)
                    risk_count += 1

                    # 统计各等级风险数量
                    if risk.risk_level == RiskLevel.HIGH:
                        high_count += 1
                    elif risk.risk_level == RiskLevel.MEDIUM:
                        medium_count += 1
                    elif risk.risk_level == RiskLevel.LOW:
                        low_count += 1

                # 6. 更新报告统计信息
                if existing_report:
                    existing_report.total_risks = risk_count
                    existing_report.high_risks = high_count
                    existing_report.medium_risks = medium_count
                    existing_report.low_risks = low_count
                    existing_report.overall_risk_level = self._calculate_overall_risk_level(
                        high_count, medium_count, low_count
                    )
                    existing_report.updated_at = datetime.now()
                else:
                    report.total_risks = risk_count
                    report.high_risks = high_count
                    report.medium_risks = medium_count
                    report.low_risks = low_count
                    report.overall_risk_level = self._calculate_overall_risk_level(
                        high_count, medium_count, low_count
                    )

                db.commit()

                logger.info(f"✅ 成功为文档 {document_id} 检测风险，共识别 {risk_count} 个风险")
                return report_id

        except Exception as e:
            logger.error(f"检测风险失败: {str(e)}", exc_info=True)
            return None

    def _detect_all_risk_types(
        self,
        processor: QuestionsProcessor,
        document: Document,
        scenario_id: str
    ) -> List[Dict[str, Any]]:
        """
        检测所有类型的风险

        Args:
            processor: 问题处理器
            document: 文档对象
            scenario_id: 场景ID

        Returns:
            风险项列表
        """
        all_risks = []

        # 定义不同类型的风险检测问题
        risk_queries = [
            {
                "type": RiskType.DISQUALIFICATION,
                "level": RiskLevel.HIGH,
                "question": "请仔细分析这份招标文件，列出所有可能导致废标的条款。对于每个条款，请提供：1) 条款标题 2) 详细描述 3) 所在页码 4) 原文内容 5) 为什么会导致废标 6) 如何规避"
            },
            {
                "type": RiskType.UNLIMITED_LIABILITY,
                "level": RiskLevel.HIGH,
                "question": "请识别这份招标文件中的无限责任条款或对投标方责任约定过重的条款。对于每个条款，请提供：1) 条款标题 2) 详细描述 3) 所在页码 4) 原文内容 5) 责任范围 6) 建议"
            },
            {
                "type": RiskType.HARSH_TERMS,
                "level": RiskLevel.MEDIUM,
                "question": "请识别这份招标文件中对投标方不利或条件苛刻的条款。对于每个条款，请提供：1) 条款标题 2) 详细描述 3) 所在页码 4) 原文内容 5) 不利之处 6) 应对建议"
            },
            {
                "type": RiskType.HIGH_PENALTY,
                "level": RiskLevel.MEDIUM,
                "question": "请识别这份招标文件中的高额罚款或违约金条款。对于每个条款，请提供：1) 条款标题 2) 详细描述 3) 所在页码 4) 原文内容 5) 罚款金额或比例 6) 规避建议"
            },
            {
                "type": RiskType.TIGHT_DEADLINE,
                "level": RiskLevel.LOW,
                "question": "请识别这份招标文件中时间要求紧迫或可能难以完成的时间节点。对于每个时间要求，请提供：1) 任务名称 2) 时间要求 3) 所在页码 4) 原文内容 5) 为什么紧迫 6) 应对措施"
            }
        ]

        for query_info in risk_queries:
            try:
                logger.info(f"检测风险类型: {query_info['type'].value}")

                # 调用LLM
                result = processor.process_question(
                    question=query_info["question"],
                    use_agentic_rag=True
                )

                if not result or not result.get("success"):
                    logger.warning(f"LLM调用失败: {query_info['type'].value}")
                    continue

                # 解析LLM返回的风险列表
                risks = self._parse_risk_response(
                    result.get("answer", ""),
                    query_info["type"],
                    query_info["level"]
                )

                all_risks.extend(risks)
                logger.info(f"识别到 {len(risks)} 个 {query_info['type'].value} 风险")

            except Exception as e:
                logger.error(f"检测 {query_info['type'].value} 风险失败: {str(e)}")
                continue

        logger.info(f"总共识别 {len(all_risks)} 个风险")
        return all_risks

    def _parse_risk_response(
        self,
        llm_response: str,
        risk_type: RiskType,
        risk_level: RiskLevel
    ) -> List[Dict[str, Any]]:
        """
        解析LLM返回的风险列表

        Args:
            llm_response: LLM的响应文本
            risk_type: 风险类型
            risk_level: 风险等级

        Returns:
            解析后的风险列表
        """
        risks = []

        try:
            # 尝试提取JSON代码块
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_risks = json.loads(json_str)

                if isinstance(parsed_risks, list):
                    for risk in parsed_risks:
                        risk["type"] = risk_type.value
                        risk["level"] = risk_level.value
                        risks.append(risk)
                    return risks

            # 如果没有JSON，尝试解析文本格式
            # 按段落分割
            paragraphs = llm_response.split('\n\n')

            current_risk = {}
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # 尝试识别标题（通常以数字或标题关键词开头）
                if re.match(r'^\d+[\.、]', para) or '条款' in para[:20]:
                    # 保存上一个风险
                    if current_risk and current_risk.get('title'):
                        current_risk["type"] = risk_type.value
                        current_risk["level"] = risk_level.value
                        risks.append(current_risk)

                    # 开始新风险
                    current_risk = {
                        "title": para[:100],  # 取前100字符作为标题
                        "description": para
                    }
                else:
                    # 继续当前风险的描述
                    if current_risk:
                        current_risk["description"] = current_risk.get("description", "") + "\n" + para

                # 尝试提取页码
                page_match = re.search(r'第?\s*(\d+)\s*页', para)
                if page_match and current_risk:
                    current_risk["page_number"] = int(page_match.group(1))

            # 保存最后一个风险
            if current_risk and current_risk.get('title'):
                current_risk["type"] = risk_type.value
                current_risk["level"] = risk_level.value
                risks.append(current_risk)

            # 如果还是没有识别到风险，创建一个通用风险
            if not risks and llm_response.strip():
                risks.append({
                    "title": f"{risk_type.value}风险",
                    "description": llm_response[:500],
                    "type": risk_type.value,
                    "level": risk_level.value
                })

        except Exception as e:
            logger.error(f"解析风险响应失败: {str(e)}")

        return risks

    def _create_risk_from_data(
        self,
        document_id: str,
        scenario_id: str,
        risk_data: Dict[str, Any]
    ) -> Risk:
        """
        从数据字典创建Risk对象

        Args:
            document_id: 文档ID
            scenario_id: 场景ID
            risk_data: 风险数据

        Returns:
            Risk对象
        """
        # 解析风险类型
        risk_type_str = risk_data.get("type", "other")
        try:
            risk_type = RiskType(risk_type_str)
        except ValueError:
            risk_type = RiskType.OTHER

        # 解析风险等级
        risk_level_str = risk_data.get("level", "medium")
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            risk_level = RiskLevel.MEDIUM

        # 创建Risk对象
        risk = Risk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            scenario_id=scenario_id,
            title=risk_data.get("title", "未命名风险")[:255],
            description=risk_data.get("description", ""),
            risk_type=risk_type,
            risk_level=risk_level,
            page_number=risk_data.get("page_number"),
            section=risk_data.get("section"),
            clause_number=risk_data.get("clause_number"),
            original_text=risk_data.get("original_text") or risk_data.get("content"),
            impact_description=risk_data.get("impact") or risk_data.get("impact_description"),
            mitigation_suggestion=risk_data.get("suggestion") or risk_data.get("mitigation"),
            confidence_score=risk_data.get("confidence_score", 80)
        )

        return risk

    def _calculate_overall_risk_level(
        self,
        high_count: int,
        medium_count: int,
        low_count: int
    ) -> RiskLevel:
        """计算整体风险等级"""
        if high_count >= 3:
            return RiskLevel.HIGH
        elif high_count >= 1 or medium_count >= 5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def get_risk_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        获取风险报告详情

        Args:
            report_id: 报告ID

        Returns:
            报告详情字典
        """
        try:
            with self.db() as db:
                report = db.query(RiskReport).filter(RiskReport.id == report_id).first()

                if not report:
                    return None

                # 获取所有风险
                risks = db.query(Risk).filter(
                    Risk.document_id == report.document_id
                ).all()

                return {
                    "id": report.id,
                    "document_id": report.document_id,
                    "scenario_id": report.scenario_id,
                    "title": report.title,
                    "summary": report.summary,
                    "total_risks": report.total_risks,
                    "high_risks": report.high_risks,
                    "medium_risks": report.medium_risks,
                    "low_risks": report.low_risks,
                    "overall_risk_level": report.overall_risk_level.value if report.overall_risk_level else None,
                    "created_at": report.created_at.isoformat(),
                    "updated_at": report.updated_at.isoformat(),
                    "risks": [self._risk_to_dict(risk) for risk in risks]
                }

        except Exception as e:
            logger.error(f"获取风险报告失败: {str(e)}", exc_info=True)
            return None

    def get_risk_report_by_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        根据文档ID获取风险报告

        Args:
            document_id: 文档ID

        Returns:
            报告详情字典
        """
        try:
            with self.db() as db:
                report = db.query(RiskReport).filter(
                    RiskReport.document_id == document_id
                ).first()

                if not report:
                    return None

                return self.get_risk_report(report.id)

        except Exception as e:
            logger.error(f"获取文档风险报告失败: {str(e)}", exc_info=True)
            return None

    def _risk_to_dict(self, risk: Risk) -> Dict[str, Any]:
        """将Risk对象转换为字典"""
        return {
            "id": risk.id,
            "title": risk.title,
            "description": risk.description,
            "risk_type": risk.risk_type.value if risk.risk_type else "other",
            "risk_level": risk.risk_level.value if risk.risk_level else "medium",
            "page_number": risk.page_number,
            "section": risk.section,
            "clause_number": risk.clause_number,
            "original_text": risk.original_text,
            "impact_description": risk.impact_description,
            "mitigation_suggestion": risk.mitigation_suggestion,
            "confidence_score": risk.confidence_score,
            "created_at": risk.created_at.isoformat() if risk.created_at else datetime.now().isoformat(),
            "updated_at": risk.updated_at.isoformat() if risk.updated_at else datetime.now().isoformat()
        }


# 单例模式
_risk_service_instance = None


def get_risk_service() -> RiskService:
    """获取RiskService单例"""
    global _risk_service_instance
    if _risk_service_instance is None:
        _risk_service_instance = RiskService()
    return _risk_service_instance

