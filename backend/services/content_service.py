"""
内容生成服务
基于LLM和知识库内容生成标书章节初稿
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashscope_client import DashScopeClient
from src.questions_processing import QuestionsProcessor
from src.config import get_settings

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """内容生成类型枚举"""
    COMPANY_INTRO = "company_intro"  # 公司简介
    TECHNICAL_SOLUTION = "technical_solution"  # 技术方案
    SERVICE_COMMITMENT = "service_commitment"  # 服务承诺
    QUALITY_ASSURANCE = "quality_assurance"  # 质量保证措施
    SAFETY_MEASURES = "safety_measures"  # 安全生产措施
    PROJECT_EXPERIENCE = "project_experience"  # 项目经验
    TEAM_INTRODUCTION = "team_introduction"  # 团队介绍


class ContentService:
    """内容生成服务类"""

    def __init__(self, scenario_id: str = "tender"):
        self.scenario_id = scenario_id
        self.settings = get_settings()
        self.llm_client = DashScopeClient()
        self.qa_processor = QuestionsProcessor(scenario_id=scenario_id)

        # 内容类型对应的提示词模板
        self.prompt_templates = {
            ContentType.COMPANY_INTRO: self._get_company_intro_template(),
            ContentType.TECHNICAL_SOLUTION: self._get_technical_solution_template(),
            ContentType.SERVICE_COMMITMENT: self._get_service_commitment_template(),
            ContentType.QUALITY_ASSURANCE: self._get_quality_assurance_template(),
            ContentType.SAFETY_MEASURES: self._get_safety_measures_template(),
            ContentType.PROJECT_EXPERIENCE: self._get_project_experience_template(),
            ContentType.TEAM_INTRODUCTION: self._get_team_introduction_template(),
        }

    async def generate_content(
        self,
        content_type: ContentType,
        project_name: Optional[str] = None,
        requirements: Optional[str] = None,
        use_knowledge_base: bool = True
    ) -> Dict[str, Any]:
        """
        生成内容

        Args:
            content_type: 内容类型
            project_name: 项目名称
            requirements: 特殊要求
            use_knowledge_base: 是否使用知识库内容

        Returns:
            生成结果字典
        """
        try:
            logger.info(f"📝 开始生成内容: {content_type.value}")

            # 1. 检索相关知识库内容
            context = ""
            if use_knowledge_base:
                context = await self._retrieve_context(content_type, project_name)

            # 2. 构建提示词
            prompt = self._build_prompt(content_type, context, project_name, requirements)

            # 3. 调用LLM生成
            logger.info(f"🤖 调用LLM生成内容...")

            # 根据内容类型调整参数
            temperature = 0.8 if content_type in [ContentType.COMPANY_INTRO, ContentType.PROJECT_EXPERIENCE] else 0.7
            max_tokens = 2500 if content_type == ContentType.TECHNICAL_SOLUTION else 2000

            response = self.llm_client.generate_text(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的招投标文件撰写专家，擅长撰写各类标书章节内容。你的写作风格专业、严谨，善于突出企业优势，语言准确、有说服力。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9  # 添加top_p参数，提高生成质量
            )

            if not response.get("success"):
                raise Exception(f"LLM生成失败: {response.get('error')}")

            generated_content = response.get("text", "")

            logger.info(f"✅ 内容生成成功，长度: {len(generated_content)} 字符")

            return {
                "success": True,
                "content": generated_content,
                "content_type": content_type.value,
                "project_name": project_name,
                "has_context": bool(context),
                "word_count": len(generated_content)
            }

        except Exception as e:
            logger.error(f"❌ 内容生成失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content_type": content_type.value
            }

    async def _retrieve_context(self, content_type: ContentType, project_name: Optional[str]) -> str:
        """
        从知识库检索相关内容

        Args:
            content_type: 内容类型
            project_name: 项目名称

        Returns:
            检索到的上下文内容
        """
        try:
            # 根据内容类型构建检索问题
            query = self._build_retrieval_query(content_type, project_name)

            logger.info(f"🔍 检索知识库: {query}")

            # 使用QuestionsProcessor检索
            result = self.qa_processor.process_question(
                question=query,
                return_context=True
            )

            if result.get("success") and result.get("context"):
                context = result["context"]
                logger.info(f"✅ 检索到上下文，长度: {len(context)} 字符")
                return context
            else:
                logger.warning("⚠️ 未检索到相关上下文")
                return ""

        except Exception as e:
            logger.error(f"❌ 检索上下文失败: {str(e)}", exc_info=True)
            return ""

    def _build_retrieval_query(self, content_type: ContentType, project_name: Optional[str]) -> str:
        """构建检索查询"""
        queries = {
            ContentType.COMPANY_INTRO: "公司简介、企业资质、公司规模、发展历程",
            ContentType.TECHNICAL_SOLUTION: f"技术方案、实施方案、{project_name or '项目'}技术要求",
            ContentType.SERVICE_COMMITMENT: "服务承诺、售后服务、服务保障",
            ContentType.QUALITY_ASSURANCE: "质量保证、质量管理体系、质量控制措施",
            ContentType.SAFETY_MEASURES: "安全生产、安全管理、安全措施",
            ContentType.PROJECT_EXPERIENCE: "项目经验、历史业绩、成功案例",
            ContentType.TEAM_INTRODUCTION: "团队介绍、人员配置、专业团队",
        }
        return queries.get(content_type, "相关信息")

    def _build_prompt(
        self,
        content_type: ContentType,
        context: str,
        project_name: Optional[str],
        requirements: Optional[str]
    ) -> str:
        """构建LLM提示词"""
        template = self.prompt_templates.get(content_type, "")

        # 替换模板变量
        prompt = template.format(
            project_name=project_name or "本项目",
            context=context if context else "（无相关背景信息）",
            requirements=requirements if requirements else "（无特殊要求）"
        )

        return prompt

    # ==================== 提示词模板 ====================

    def _get_company_intro_template(self) -> str:
        return """请根据以下信息，撰写一份专业的公司简介，用于招投标文件。

项目名称：{project_name}

背景信息：
{context}

特殊要求：
{requirements}

请撰写一份800-1000字的公司简介，包括以下内容：
1. 公司基本情况（成立时间、注册资本、经营范围）
2. 公司资质和荣誉
3. 公司规模和实力
4. 核心业务和优势
5. 发展历程和成就

要求：
- 语言专业、正式
- 突出公司优势和实力
- 数据准确、有说服力
- 符合招投标文件规范

【参考示例】
某某科技有限公司成立于2010年，注册资本5000万元，是一家专注于电力行业智能化解决方案的高新技术企业。公司拥有ISO9001质量管理体系认证、电力工程施工总承包三级资质等多项行业资质，累计获得国家专利20余项。

公司现有员工200余人，其中技术人员占比超过60%，拥有博士、硕士学历50余人。公司总部位于北京，在全国设有8个分支机构，服务网络覆盖全国主要省市。

公司核心业务包括智能电网建设、电力设备监测、能源管理系统等，已成功服务于国家电网、南方电网等大型电力企业，累计完成项目500余个，合同金额超过10亿元。公司以技术创新为驱动，持续投入研发，年研发投入占营收比例超过15%，在行业内建立了良好的品牌形象和市场口碑。

请参考以上示例的结构和风格，结合提供的背景信息，撰写符合要求的公司简介。
"""

    def _get_technical_solution_template(self) -> str:
        return """请根据以下信息，撰写一份技术方案，用于招投标文件。

项目名称：{project_name}

背景信息：
{context}

特殊要求：
{requirements}

请撰写一份1000-1500字的技术方案，包括以下内容：
1. 项目需求分析
2. 技术方案概述
3. 技术架构设计
4. 实施方案和步骤
5. 技术保障措施
6. 预期效果

要求：
- 技术方案切实可行
- 突出技术优势和创新点
- 符合项目实际需求
- 逻辑清晰、结构完整

【参考示例片段】
一、项目需求分析
本项目旨在构建智能电网监控平台，实现对电力设备的实时监测、故障预警和智能调度。根据招标文件要求，系统需支持10000+监测点位，数据采集频率达到秒级，并具备99.9%的系统可用性。

二、技术方案概述
我公司采用"云边协同"架构，结合物联网、大数据和人工智能技术，构建分布式智能监控平台。边缘端部署数据采集网关，云端部署数据处理和分析平台，实现数据的高效采集、传输、存储和分析。

三、技术架构设计
1. 边缘层：采用工业级数据采集网关，支持Modbus、OPC等多种协议
2. 网络层：采用4G/5G+光纤专网混合组网，保证数据传输稳定性
3. 平台层：基于微服务架构，采用Kubernetes容器编排，支持弹性扩展
4. 应用层：提供WEB端和移动端应用，支持多终端访问

请参考以上示例的结构，结合技术细节和项目特点，撰写完整的技术方案。
"""

    def _get_service_commitment_template(self) -> str:
        return """请根据以下信息，撰写服务承诺内容，用于招投标文件。

项目名称：{project_name}

背景信息：
{context}

特殊要求：
{requirements}

请撰写一份600-800字的服务承诺，包括以下内容：
1. 服务宗旨和原则
2. 服务内容和范围
3. 服务响应时间
4. 售后服务保障
5. 服务质量承诺
6. 违约责任

要求：
- 承诺具体、可量化
- 体现服务优势
- 符合行业规范
- 语言严谨、负责
"""

    def _get_quality_assurance_template(self) -> str:
        return """请根据以下信息，撰写质量保证措施，用于招投标文件。

项目名称：{project_name}

背景信息：
{context}

特殊要求：
{requirements}

请撰写一份800-1000字的质量保证措施，包括以下内容：
1. 质量管理体系
2. 质量控制流程
3. 质量检测标准
4. 质量保证措施
5. 质量问题处理机制
6. 质量改进措施

要求：
- 措施具体、可执行
- 符合质量管理标准
- 体现质量管理能力
- 逻辑严密、专业
"""

    def _get_safety_measures_template(self) -> str:
        return """请根据以下信息，撰写安全生产措施，用于招投标文件。

项目名称：{project_name}

背景信息：
{context}

特殊要求：
{requirements}

请撰写一份800-1000字的安全生产措施，包括以下内容：
1. 安全管理体系
2. 安全责任制度
3. 安全操作规程
4. 安全防护措施
5. 应急预案
6. 安全培训计划

要求：
- 措施全面、具体
- 符合安全生产规范
- 体现安全管理能力
- 重点突出、可操作
"""

    def _get_project_experience_template(self) -> str:
        return """请根据以下信息，撰写项目经验介绍，用于招投标文件。

项目名称：{project_name}

背景信息：
{context}

特殊要求：
{requirements}

请撰写一份800-1000字的项目经验介绍，包括以下内容：
1. 典型项目案例（3-5个）
2. 项目规模和复杂度
3. 项目成果和效益
4. 客户评价和反馈
5. 经验总结和优势

要求：
- 案例真实、有代表性
- 突出项目成功经验
- 数据准确、有说服力
- 与本项目相关性强
"""

    def _get_team_introduction_template(self) -> str:
        return """请根据以下信息，撰写团队介绍，用于招投标文件。

项目名称：{project_name}

背景信息：
{context}

特殊要求：
{requirements}

请撰写一份600-800字的团队介绍，包括以下内容：
1. 团队规模和结构
2. 核心成员介绍
3. 专业能力和资质
4. 项目经验和业绩
5. 团队优势和特点

要求：
- 突出团队专业能力
- 体现团队协作优势
- 符合项目人员要求
- 真实可信、有说服力
"""


# 单例模式
_content_service_instance = None


def get_content_service(scenario_id: str = "tender") -> ContentService:
    """获取ContentService单例"""
    global _content_service_instance
    if _content_service_instance is None:
        _content_service_instance = ContentService(scenario_id=scenario_id)
    return _content_service_instance

