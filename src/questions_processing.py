"""
问题处理模块
负责问题解析、分类、检索和答案生成
集成 Agentic RAG 组件
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from config import get_settings
from api_requests import APIProcessor
from data_models import Question

# Agentic RAG 组件
from src.retrieval.hybrid_retriever import HybridRetriever
from src.agents.routing_agent import RoutingAgent
from src.retrieval.layered_navigator import LayeredNavigator
from src.cache.smart_cache import SmartCache
from src.verification.answer_verifier import AnswerVerifier

logger = logging.getLogger(__name__)


@dataclass
class QuestionContext:
    """问题上下文"""

    question_text: str
    question_type: str
    company: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    relevant_chunks: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None


class QuestionsProcessor:
    """问题处理器"""

    def __init__(self, api_provider: str = "dashscope", scenario_id: str = "investment", tenant_id: str = "default"):
        """初始化问题处理器

        Args:
            api_provider: API提供商名称
            scenario_id: 业务场景ID
            tenant_id: 租户ID（用于数据隔离）
        """
        self.settings = get_settings()
        self.api_provider = api_provider
        self.api_processor = APIProcessor(provider=api_provider)
        self.scenario_id = scenario_id
        self.tenant_id = tenant_id  # 新增：存储租户ID

        # 根据场景设置不同的提示词模板
        self._setup_scenario_prompts()

        # ✅ Agentic RAG 组件初始化（传递租户信息）
        try:
            self.hybrid_retriever = HybridRetriever(scenario_id, tenant_id=tenant_id)  # 新增：传递租户ID
            self.routing_agent = RoutingAgent(scenario_id)
            self.layered_navigator = LayeredNavigator(self.routing_agent)
            self.smart_cache = SmartCache(max_size=1000)
            self.answer_verifier = AnswerVerifier()
            self.agentic_rag_enabled = True
            logger.info(f"✅ Agentic RAG 组件初始化成功 (scenario: {scenario_id}, tenant: {tenant_id})")
        except Exception as e:
            logger.warning(f"⚠️ Agentic RAG 组件初始化失败: {e}，将使用降级模式")
            self.agentic_rag_enabled = False

    def _setup_scenario_prompts(self):
        """根据场景设置提示词模板"""
        if self.scenario_id == "investment":
            self.question_analysis_prompt = """你是专业的投资分析师，请分析以下问题：

问题：{question}

请从以下几个维度分析：
1. 问题类型：是事实查询、分析判断还是预测建议？
2. 涉及公司：如果提及具体公司，请提取公司名称
3. 问题难度：简单、中等还是复杂？
4. 问题类别：财务分析、行业分析、投资建议、风险评估等

请以JSON格式回答：
{{
    "question_type": "string",
    "companies": ["公司名"],
    "difficulty": "medium",
    "category": "财务分析",
    "keywords": ["关键词1", "关键词2"]
}}"""

            self.answer_generation_prompt = """你是专业的投资分析师，请基于提供的信息回答用户问题。

问题：{question}

{context_section}

请提供：
1. 准确、客观的分析
2. 基于事实的判断
3. 如果涉及投资建议，请说明风险
4. 保持专业和中性的语调

回答："""

        elif self.scenario_id == "tender":
            self.question_analysis_prompt = """你是专业的招投标分析师，请分析以下问题：

问题：{question}

请从以下几个维度分析：
1. 问题类型：是招标信息查询、技术要求分析还是投标策略咨询？
2. 涉及项目：如果提及具体项目，请提取项目信息
3. 问题难度：简单、中等还是复杂？
4. 问题类别：招标要求、技术规范、资质条件、时间安排、预算分析等

请以JSON格式回答：
{{
    "question_type": "string",
    "projects": ["项目名"],
    "difficulty": "medium",
    "category": "招标要求",
    "keywords": ["关键词1", "关键词2"]
}}"""

            self.answer_generation_prompt = """你是专业的招投标分析师，请基于提供的招投标文档信息回答用户问题。

问题：{question}

{context_section}

请提供：
1. 准确的招投标信息解读
2. 清晰的技术要求说明
3. 明确的时间节点和流程
4. 必要的合规性提醒
5. 保持专业和严谨的语调

回答："""

        else:
            # 通用场景的提示词
            self.question_analysis_prompt = """请分析以下问题：

问题：{question}

请以JSON格式分析：
{{
    "question_type": "string",
    "difficulty": "medium",
    "category": "general",
    "keywords": ["关键词1", "关键词2"]
}}"""

            self.answer_generation_prompt = """请基于提供的信息回答用户问题。

问题：{question}

{context_section}

回答："""

        logger.info(f"QuestionsProcessor initialized with provider: {self.api_provider}, scenario: {self.scenario_id}")

    def analyze_question(self, question: str) -> Dict[str, Any]:
        """分析问题特征

        Args:
            question: 问题文本

        Returns:
            问题分析结果
        """
        try:
            logger.debug(f"分析问题: {question}")

            prompt = self.question_analysis_prompt.format(question=question)

            response = self.api_processor.send_message(
                system_content="你是专业的问题分析助手",
                human_content=prompt,
                temperature=0.1,
                max_tokens=200,
            )

            # 尝试解析JSON响应
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回基本分析
                analysis = {
                    "question_type": "string",
                    "companies": [],
                    "difficulty": "medium",
                    "category": "general",
                    "keywords": question.split()[:5],
                }
                logger.warning("问题分析JSON解析失败，使用默认分析")

            logger.debug(f"问题分析完成: {analysis}")
            return analysis

        except Exception as e:
            logger.error(f"问题分析失败: {str(e)}")
            return {
                "question_type": "string",
                "companies": [],
                "difficulty": "medium",
                "category": "general",
                "keywords": [],
                "error": str(e),
            }

    def retrieve_relevant_context(
        self, question: str, question_analysis: Dict[str, Any], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索相关上下文（Agentic RAG 完整实现）

        Args:
            question: 问题文本
            question_analysis: 问题分析结果
            top_k: 返回的文档数量

        Returns:
            相关文档列表
        """
        try:
            logger.info(f"🔍 开始检索相关上下文: {question[:50]}")

            # 如果 Agentic RAG 未启用，返回空列表
            if not self.agentic_rag_enabled:
                logger.warning("Agentic RAG 未启用，跳过检索")
                return []

            # ✅ 第一步：检查缓存
            cached_result = self.smart_cache.get(question)
            if cached_result:
                logger.info("✅ 缓存命中，直接返回")
                # 缓存中存储的是完整答案，这里需要返回文档块
                # 如果缓存中有 source_chunks，返回它
                if "source_chunks" in cached_result:
                    return cached_result["source_chunks"]
                # 否则返回空（纯LLM答案）
                return []

            # ✅ 第二步：混合检索（BM25 + FAISS + RRF）
            logger.info("🔎 执行混合检索...")
            retrieval_results = self.hybrid_retriever.retrieve(
                question=question,
                top_k=top_k * 3,  # 初始检索更多候选
                use_bm25=True,
                use_vector=True
            )

            if not retrieval_results:
                logger.warning("混合检索未找到相关文档")
                return []

            logger.info(f"混合检索完成: 找到 {len(retrieval_results)} 个候选文档")

            # ✅ 第三步：路由代理智能筛选
            logger.info("🧠 执行智能路由...")
            routing_result = self.routing_agent.route_documents(
                chunks=retrieval_results,
                question=question,
                history="",
                top_k=top_k * 2  # 路由后保留更多文档供分层导航
            )

            if not routing_result.get("success") or not routing_result.get("chunks"):
                logger.warning("路由代理筛选失败，使用原始检索结果")
                selected_chunks = retrieval_results[:top_k * 2]
            else:
                selected_chunks = routing_result["chunks"]
                logger.info(
                    f"路由完成: 选中 {len(selected_chunks)} 个文档 "
                    f"(置信度: {routing_result.get('confidence', 0):.2f})"
                )

            # ✅ 第四步：分层导航（Token 控制）
            logger.info("📊 执行分层导航...")
            final_chunks = self.layered_navigator.navigate(
                chunks=selected_chunks,
                question=question,
                max_rounds=3,
                target_tokens=2000
            )

            logger.info(f"分层导航完成: 最终 {len(final_chunks)} 个文档块")

            # 返回最终结果
            return final_chunks[:top_k]  # 确保不超过 top_k

        except Exception as e:
            logger.error(f"检索相关上下文失败: {str(e)}", exc_info=True)
            return []

    def generate_answer(
        self,
        question: str,
        context_docs: List[Dict[str, Any]] = None,
        question_type: str = "string",
    ) -> Dict[str, Any]:
        """生成答案（集成答案验证和缓存）

        Args:
            question: 问题文本
            context_docs: 相关文档上下文
            question_type: 问题类型

        Returns:
            答案生成结果
        """
        try:
            logger.info(f"💬 生成答案: {question[:50]}")

            start_time = time.time()

            # 构建上下文部分
            if context_docs:
                context_section = "参考信息：\n"
                for i, doc in enumerate(context_docs[:5]):  # 最多使用5个文档
                    page = doc.get('page', '未知')
                    text = doc.get('text', '')[:300]  # 限制长度
                    context_section += f"\n【文档{i+1}】(第{page}页)\n{text}...\n"
            else:
                context_section = "请基于你的专业知识回答。"

            # 生成完整提示词
            prompt = self.answer_generation_prompt.format(
                question=question, context_section=context_section
            )

            # 根据场景选择system content
            system_content_map = {
                "tender": "你是专业的招投标分析师",
                "enterprise": "你是专业的企业管理顾问",
                "investment": "你是专业的投资分析师"
            }
            system_content = system_content_map.get(self.scenario_id, "你是专业的AI助手")

            # 调用LLM生成答案（使用 qwen-plus 平衡质量和成本）
            response = self.api_processor.send_message(
                system_content=system_content,
                human_content=prompt,
                temperature=0.3,
                max_tokens=1000,
                model="qwen-plus"  # 使用 qwen-plus
            )

            processing_time = time.time() - start_time

            # ✅ 答案验证（如果启用 Agentic RAG）
            verification_result = None
            if self.agentic_rag_enabled and context_docs:
                try:
                    logger.info("🔍 执行答案验证...")
                    verification_result = self.answer_verifier.verify_answer(
                        answer=response,
                        source_chunks=context_docs,
                        question=question
                    )
                    logger.info(
                        f"验证完成: valid={verification_result.get('is_valid')}, "
                        f"confidence={verification_result.get('confidence')}"
                    )
                except Exception as e:
                    logger.warning(f"答案验证失败: {e}")
                    verification_result = None

            # 计算最终置信度
            if verification_result:
                confidence = verification_result.get("confidence", 0.7)
            else:
                # 基于文档数量的简单置信度
                if context_docs:
                    confidence = min(0.8, 0.5 + len(context_docs) * 0.05)
                else:
                    confidence = 0.5

            relevant_pages = [doc.get("page", 0) for doc in (context_docs or [])]

            result = {
                "success": True,
                "answer": response,
                "reasoning": verification_result.get("reasoning", "基于LLM分析生成") if verification_result else "基于LLM分析生成",
                "relevant_pages": relevant_pages,
                "confidence": confidence,
                "processing_time": processing_time,
                "context_docs_count": len(context_docs) if context_docs else 0,
                "verification": verification_result if verification_result else {"status": "skipped"}
            }

            # ✅ 存入缓存（如果启用 Agentic RAG）
            if self.agentic_rag_enabled:
                try:
                    cache_data = {
                        **result,
                        "source_chunks": context_docs,
                        "question": question
                    }
                    self.smart_cache.set(question, cache_data, use_semantic=True)
                    logger.debug("✅ 答案已缓存")
                except Exception as e:
                    logger.warning(f"缓存存储失败: {e}")

            logger.info(f"答案生成完成，耗时: {processing_time:.2f}秒, 置信度: {confidence:.2f}")

            return result

        except Exception as e:
            logger.error(f"答案生成失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "answer": "",
                "reasoning": "",
                "relevant_pages": [],
                "confidence": 0.1,
                "processing_time": 0,
                "context_docs_count": 0,
            }

    def process_question(
        self,
        question: str,
        company: Optional[str] = None,
        question_type: str = "string",
    ) -> Dict[str, Any]:
        """完整的问题处理流程

        Args:
            question: 问题文本
            company: 目标公司
            question_type: 问题类型

        Returns:
            完整的处理结果
        """
        start_time = time.time()

        try:
            logger.info(f"开始处理问题: {question}")

            # 1. 问题分析
            analysis = self.analyze_question(question)

            # 2. 检索相关上下文
            context_docs = self.retrieve_relevant_context(question, analysis)

            # 3. 生成答案
            answer_result = self.generate_answer(question, context_docs, question_type)

            # 4. 整合结果
            total_time = time.time() - start_time

            result = {
                "question": question,
                "company": company,
                "question_type": question_type,
                "analysis": analysis,
                "total_processing_time": total_time,
                **answer_result,
            }

            logger.info(f"问题处理完成，总耗时: {total_time:.2f}秒")

            return result

        except Exception as e:
            logger.error(f"问题处理失败: {str(e)}")
            return {
                "question": question,
                "company": company,
                "question_type": question_type,
                "success": False,
                "error": str(e),
                "answer": "",
                "reasoning": "",
                "relevant_pages": [],
                "confidence": "low",
                "total_processing_time": time.time() - start_time,
            }

    def get_agentic_rag_stats(self) -> Dict[str, Any]:
        """
        获取 Agentic RAG 组件统计信息

        Returns:
            统计信息字典
        """
        if not self.agentic_rag_enabled:
            return {"enabled": False, "message": "Agentic RAG 未启用"}

        try:
            return {
                "enabled": True,
                "cache_stats": self.smart_cache.get_stats(),
                "retrieval_stats": self.hybrid_retriever.get_stats(),
                "scenario_id": self.scenario_id
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"enabled": True, "error": str(e)}

    def batch_process_questions(
        self, questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量处理问题

        Args:
            questions: 问题列表

        Returns:
            批量处理结果
        """
        logger.info(f"开始批量处理 {len(questions)} 个问题")

        results = {
            "total_questions": len(questions),
            "successful": 0,
            "failed": 0,
            "answers": [],
            "total_time": 0,
        }

        start_time = time.time()

        for i, question_item in enumerate(questions):
            try:
                logger.info(f"处理问题 {i+1}/{len(questions)}")

                # 提取问题信息
                question_text = question_item.get("question_text", "")
                question_type = question_item.get("question_type", "string")
                company = question_item.get("target_companies", [None])[0]

                # 处理问题
                result = self.process_question(question_text, company, question_type)

                # 添加问题ID
                result["question_id"] = question_item.get("question_id", f"q_{i}")

                # 记录结果
                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1

                results["answers"].append(result)

            except Exception as e:
                logger.error(f"处理问题 {i+1} 失败: {str(e)}")
                results["failed"] += 1
                results["answers"].append(
                    {
                        "question_id": question_item.get("question_id", f"q_{i}"),
                        "question": question_item.get("question_text", ""),
                        "success": False,
                        "error": str(e),
                    }
                )

        results["total_time"] = time.time() - start_time
        results["success"] = results["failed"] == 0

        logger.info(
            f"批量处理完成: {results['successful']}/{results['total_questions']} 成功"
        )

        return results

    def load_questions_from_file(self, questions_file: Path) -> List[Dict[str, Any]]:
        """从文件加载问题

        Args:
            questions_file: 问题文件路径

        Returns:
            问题列表
        """
        try:
            with open(questions_file, "r", encoding="utf-8") as f:
                questions = json.load(f)

            logger.info(f"从文件加载 {len(questions)} 个问题: {questions_file}")
            return questions

        except Exception as e:
            logger.error(f"加载问题文件失败: {str(e)}")
            return []

    def save_answers(self, results: Dict[str, Any], output_file: Path):
        """保存答案到文件

        Args:
            results: 处理结果
            output_file: 输出文件路径
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logger.info(f"答案已保存到: {output_file}")

        except Exception as e:
            logger.error(f"保存答案失败: {str(e)}")


# 便捷函数
def process_single_question(
    question: str, company: Optional[str] = None, api_provider: str = "dashscope", scenario_id: str = "investment"
) -> Dict[str, Any]:
    """处理单个问题的便捷函数"""
    processor = QuestionsProcessor(api_provider=api_provider, scenario_id=scenario_id)
    return processor.process_question(question, company)


def create_questions_processor(api_provider: str = "dashscope", scenario_id: str = "investment") -> QuestionsProcessor:
    """创建问题处理器的便捷函数"""
    return QuestionsProcessor(api_provider=api_provider, scenario_id=scenario_id)
