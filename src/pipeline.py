"""
投研RAG系统完整流水线
整合PDF解析、向量化、检索、问答的完整流程
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# 直接导入config.py文件中的get_settings
from config import get_settings
from pdf_parsing_mineru import PDFParsingPipeline
from ingestion import IngestionPipeline
from api_requests import APIProcessor

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """流水线配置类"""

    def __init__(
        self,
        root_path: Path,
        subset_name: str = "subset.csv",
        questions_file_name: str = "questions.json",
        pdf_reports_dir_name: str = "pdf_reports",
    ):
        self.root_path = root_path
        self.subset_path = root_path / subset_name
        self.questions_file_path = root_path / questions_file_name
        self.pdf_reports_dir = root_path / pdf_reports_dir_name

        # 数据库和调试目录
        self.databases_path = root_path / "databases"
        self.debug_data_path = root_path / "debug_data"

        # 子目录
        self.vector_db_dir = self.databases_path / "vector_dbs"
        self.bm25_db_dir = self.databases_path / "bm25"
        self.parsed_reports_path = self.debug_data_path / "parsed_reports"

        # 确保目录存在
        for path in [
            self.databases_path,
            self.debug_data_path,
            self.vector_db_dir,
            self.bm25_db_dir,
            self.parsed_reports_path,
        ]:
            path.mkdir(parents=True, exist_ok=True)


@dataclass
class RunConfig:
    """运行配置类"""

    use_vector_dbs: bool = True
    use_bm25_db: bool = True
    top_n_retrieval: int = 10
    api_provider: str = "dashscope"
    llm_model: str = "qwen-turbo-latest"
    embedding_model: str = "text-embedding-v1"
    parallel_requests: int = 1
    enable_reranking: bool = False
    max_context_length: int = 8000


class Pipeline:
    """多场景RAG系统主流水线"""

    def __init__(
        self,
        root_path: Path,
        subset_name: str = "subset.csv",
        questions_file_name: str = "questions.json",
        pdf_reports_dir_name: str = "pdf_reports",
        run_config: RunConfig = None,
        scenario_id: str = "investment",
        tenant_id: str = "default"  # 新增：租户ID参数
    ):
        """初始化流水线

        Args:
            root_path: 数据根目录路径
            subset_name: 元数据文件名
            questions_file_name: 问题文件名
            pdf_reports_dir_name: PDF报告目录名
            run_config: 运行配置
            scenario_id: 业务场景ID
            tenant_id: 租户ID（用于数据隔离）
        """
        self.run_config = run_config or RunConfig()
        self.scenario_id = scenario_id
        self.tenant_id = tenant_id  # 新增：存储租户ID

        # 创建租户级配置（修改路径结构）
        self.paths = PipelineConfig(
            root_path, subset_name, questions_file_name, pdf_reports_dir_name
        )

        # 重写关键路径以支持租户隔离
        self._setup_tenant_paths()

        self.settings = get_settings()

        # 初始化核心组件（传递租户信息）
        self.pdf_parser = PDFParsingPipeline(scenario_id=scenario_id)
        self.ingestion = IngestionPipeline(
            api_provider=self.run_config.api_provider,
            tenant_id=tenant_id  # 新增：传递租户ID到Ingestion
        )
        self.api_processor = APIProcessor(provider=self.run_config.api_provider)

        # 状态跟踪
        self.is_ready = False
        self.databases_loaded = False

        logger.info(f"Pipeline initialized for tenant: {tenant_id}, scenario: {scenario_id}, path: {root_path}")

    def _setup_tenant_paths(self):
        """设置租户级路径结构

        将原有的路径结构修改为租户隔离的路径：
        - vector_dbs/{tenant_id}/{scenario_id}/
        - bm25/{tenant_id}/{scenario_id}/
        """
        # 重写向量数据库路径（租户级隔离）
        self.paths.vector_db_dir = self.paths.databases_path / "vector_dbs" / self.tenant_id / self.scenario_id

        # 重写BM25数据库路径（租户级隔离）
        self.paths.bm25_db_dir = self.paths.databases_path / "bm25" / self.tenant_id / self.scenario_id

        # 确保租户级目录存在
        self.paths.vector_db_dir.mkdir(parents=True, exist_ok=True)
        self.paths.bm25_db_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Tenant paths setup:")
        logger.info(f"  Vector DB: {self.paths.vector_db_dir}")
        logger.info(f"  BM25 DB: {self.paths.bm25_db_dir}")

    def prepare_documents(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """准备文档：PDF解析 + 向量化

        Args:
            force_rebuild: 是否强制重新构建

        Returns:
            处理结果统计
        """
        logger.info("开始文档准备流程...")

        results = {
            "parsing_results": None,
            "ingestion_results": None,
            "success": True,
            "total_time": 0,
        }

        start_time = time.time()

        try:
            # 检查PDF文件
            pdf_files = list(self.paths.pdf_reports_dir.glob("*.pdf"))
            if not pdf_files:
                logger.warning(f"未找到PDF文件: {self.paths.pdf_reports_dir}")
                results["success"] = False
                results["error"] = "未找到PDF文件"
                return results

            logger.info(f"发现 {len(pdf_files)} 个PDF文件")

            # 检查是否需要重新解析
            parsed_files = list(self.paths.parsed_reports_path.glob("*_parsed.json"))
            if not force_rebuild and len(parsed_files) >= len(pdf_files):
                logger.info("发现已解析文件，跳过PDF解析")
            else:
                # PDF解析
                logger.info("开始PDF解析...")
                parsing_results = self.pdf_parser.batch_parse_pdfs(
                    str(self.paths.pdf_reports_dir), str(self.paths.parsed_reports_path)
                )
                results["parsing_results"] = parsing_results
                logger.info(
                    f"PDF解析完成: {parsing_results['successful']}/{parsing_results['total_files']}"
                )

            # 检查是否需要重新构建索引
            vector_files = list(self.paths.vector_db_dir.glob("*.faiss"))
            bm25_files = list(self.paths.bm25_db_dir.glob("*.pkl"))

            if not force_rebuild and vector_files and bm25_files:
                logger.info("发现已构建索引，跳过数据摄取")
            else:
                # 数据摄取（向量化和BM25索引）
                logger.info("开始数据摄取...")
                ingestion_results = self.ingestion.process_reports(
                    self.paths.parsed_reports_path,
                    self.paths.databases_path,
                    include_bm25=self.run_config.use_bm25_db,
                    include_vector=self.run_config.use_vector_dbs,
                )
                results["ingestion_results"] = ingestion_results
                logger.info(f"数据摄取完成: 成功={ingestion_results['success']}")

            # 标记准备完成
            self.is_ready = True

            # 计算总时间
            results["total_time"] = time.time() - start_time

            logger.info(f"文档准备完成，总耗时: {results['total_time']:.2f}秒")

            return results

        except Exception as e:
            logger.error(f"文档准备失败: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
            results["total_time"] = time.time() - start_time
            return results

    def load_databases(self) -> bool:
        """加载数据库索引到内存"""
        try:
            # 这里可以预加载FAISS索引等
            # 暂时简化，标记为已加载
            self.databases_loaded = True
            logger.info("数据库加载完成")
            return True

        except Exception as e:
            logger.error(f"数据库加载失败: {str(e)}")
            return False

    def answer_question(
        self,
        question: str,
        company: Optional[str] = None,
        question_type: str = "string",
    ) -> Dict[str, Any]:
        """回答单个问题（使用 Agentic RAG）

        Args:
            question: 问题文本
            company: 目标公司（可选）
            question_type: 问题类型

        Returns:
            回答结果
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": "Pipeline未准备就绪，请先调用prepare_documents()",
            }

        start_time = time.time()

        try:
            logger.info(f"🤖 Pipeline处理问题: {question}")

            # ✅ 使用 QuestionsProcessor（集成了完整的 Agentic RAG）
            try:
                from questions_processing import QuestionsProcessor

                processor = QuestionsProcessor(
                    api_provider=self.run_config.api_provider,
                    scenario_id=self.scenario_id,
                    tenant_id=self.tenant_id  # 新增：传递租户ID
                )

                # 调用完整的问题处理流程
                result = processor.process_question(
                    question=question,
                    company=company,
                    question_type=question_type
                )

                logger.info(f"✅ QuestionsProcessor处理完成: success={result.get('success')}")

                return result

            except Exception as e:
                logger.error(f"QuestionsProcessor调用失败: {e}，降级为简单LLM")

                # 降级方案：简单LLM回答
                system_prompt_map = {
                    "investment": "你是专业的投资分析师，请基于你的知识回答用户关于投资和公司分析的问题。请提供准确、客观的分析和建议。",
                    "tender": "你是专业的招投标分析师，请基于你的知识回答用户关于招投标的问题。请提供准确的招投标信息解读和专业建议。",
                    "enterprise": "你是专业的企业管理顾问，请基于你的知识回答用户关于企业管理的问题。请提供专业的建议。"
                }
                system_prompt = system_prompt_map.get(self.scenario_id, "你是专业的AI助手，请基于你的知识回答用户的问题。")

                response = self.api_processor.send_message(
                    system_content=system_prompt,
                human_content=question,
                temperature=0.3,
                max_tokens=500,
            )

                processing_time = time.time() - start_time

                return {
                    "success": True,
                    "answer": response,
                    "question": question,
                    "question_type": question_type,
                    "company": company,
                    "processing_time": processing_time,
                    "reasoning": "Agentic RAG不可用，使用简单LLM回答",
                    "relevant_pages": [],
                    "confidence": 0.5,
                    "agentic_rag_enabled": False
                }

        except Exception as e:
            logger.error(f"问题回答失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "question": question,
                "processing_time": time.time() - start_time,
                "confidence": 0.1
            }

    def batch_answer_questions(
        self, questions_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """批量回答问题

        Args:
            questions_file: 问题文件路径，默认使用配置的文件

        Returns:
            批量处理结果
        """
        if questions_file is None:
            questions_file = self.paths.questions_file_path

        if not questions_file.exists():
            return {"success": False, "error": f"问题文件不存在: {questions_file}"}

        try:
            # 加载问题
            with open(questions_file, "r", encoding="utf-8") as f:
                questions_data = json.load(f)

            logger.info(f"加载 {len(questions_data)} 个问题")

            results = {
                "total_questions": len(questions_data),
                "successful": 0,
                "failed": 0,
                "answers": [],
                "total_time": 0,
            }

            start_time = time.time()

            # 逐个处理问题
            for i, question_item in enumerate(questions_data):
                logger.info(f"处理问题 {i+1}/{len(questions_data)}")

                # 提取问题信息
                question_text = question_item.get("question_text", "")
                question_type = question_item.get("question_type", "string")
                company = question_item.get("target_companies", [None])[0]

                # 回答问题
                answer_result = self.answer_question(
                    question_text, company, question_type
                )

                # 记录结果
                if answer_result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1

                results["answers"].append(
                    {
                        "question_id": question_item.get("question_id", f"q_{i}"),
                        **answer_result,
                    }
                )

            results["total_time"] = time.time() - start_time
            results["success"] = results["failed"] == 0

            logger.info(
                f"批量问答完成: {results['successful']}/{results['total_questions']} 成功"
            )

            return results

        except Exception as e:
            logger.error(f"批量问答失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_questions": 0,
                "successful": 0,
                "failed": 0,
            }

    def get_status(self) -> Dict[str, Any]:
        """获取流水线状态"""
        return {
            "is_ready": self.is_ready,
            "databases_loaded": self.databases_loaded,
            "config": {
                "api_provider": self.run_config.api_provider,
                "llm_model": self.run_config.llm_model,
                "embedding_model": self.run_config.embedding_model,
                "use_vector_dbs": self.run_config.use_vector_dbs,
                "use_bm25_db": self.run_config.use_bm25_db,
            },
            "paths": {
                "pdf_reports": str(self.paths.pdf_reports_dir),
                "databases": str(self.paths.databases_path),
                "questions_file": str(self.paths.questions_file_path),
            },
        }


# 便捷函数
def create_pipeline(data_path: str, api_provider: str = "dashscope", scenario_id: str = "investment") -> Pipeline:
    """创建Pipeline实例的便捷函数"""
    config = RunConfig(api_provider=api_provider)
    return Pipeline(Path(data_path), run_config=config, scenario_id=scenario_id)


def get_default_pipeline() -> Pipeline:
    """获取默认配置的Pipeline"""
    settings = get_settings()
    return create_pipeline(str(settings.data_dir))
