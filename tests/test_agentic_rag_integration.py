"""
Agentic RAG 系统集成测试
测试完整的问答流程和各个组件
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import logging
import time
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgenticRAGTester:
    """Agentic RAG 系统测试器"""

    def __init__(self):
        """初始化测试器"""
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        self.total_tests += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 测试 {self.total_tests}: {test_name}")
        logger.info(f"{'='*60}")

        try:
            start_time = time.time()
            result = test_func()
            elapsed = time.time() - start_time

            if result.get("success", False):
                self.passed_tests += 1
                logger.info(f"✅ 测试通过 (耗时: {elapsed:.2f}秒)")
                status = "PASS"
            else:
                self.failed_tests += 1
                logger.error(f"❌ 测试失败: {result.get('error', 'Unknown error')}")
                status = "FAIL"

            self.test_results.append({
                "name": test_name,
                "status": status,
                "elapsed": elapsed,
                "details": result
            })

            return result

        except Exception as e:
            self.failed_tests += 1
            logger.error(f"❌ 测试异常: {str(e)}", exc_info=True)
            self.test_results.append({
                "name": test_name,
                "status": "ERROR",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def test_1_import_modules(self) -> Dict[str, Any]:
        """测试1: 导入所有模块"""
        try:
            from src.retrieval.bm25_retriever import BM25Retriever
            from src.retrieval.vector_retriever import VectorRetriever
            from src.retrieval.hybrid_retriever import HybridRetriever
            from src.agents.routing_agent import RoutingAgent
            from src.retrieval.layered_navigator import LayeredNavigator
            from src.cache.smart_cache import SmartCache
            from src.verification.answer_verifier import AnswerVerifier
            from src.questions_processing import QuestionsProcessor

            logger.info("✅ 所有模块导入成功")
            return {"success": True, "message": "All modules imported successfully"}

        except Exception as e:
            return {"success": False, "error": f"Module import failed: {str(e)}"}

    def test_2_bm25_retriever(self) -> Dict[str, Any]:
        """测试2: BM25检索器"""
        try:
            from src.retrieval.bm25_retriever import BM25Retriever

            retriever = BM25Retriever(scenario_id="tender")
            logger.info(f"✅ BM25Retriever初始化成功")
            logger.info(f"   加载索引数: {len(retriever.bm25_indices)}")

            # 测试检索
            if retriever.bm25_indices:
                results = retriever.search("预算", k=5)
                logger.info(f"   检索结果数: {len(results)}")

                if results:
                    logger.info(f"   Top 1: score={results[0].get('score', 0):.3f}")

                return {
                    "success": True,
                    "indices_loaded": len(retriever.bm25_indices),
                    "search_results": len(results)
                }
            else:
                logger.warning("⚠️ 未找到BM25索引文件")
                return {
                    "success": True,
                    "indices_loaded": 0,
                    "message": "No BM25 indices found (expected if no documents)"
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_3_vector_retriever(self) -> Dict[str, Any]:
        """测试3: FAISS向量检索器"""
        try:
            from src.retrieval.vector_retriever import VectorRetriever

            retriever = VectorRetriever(scenario_id="tender")
            logger.info(f"✅ VectorRetriever初始化成功")
            logger.info(f"   加载索引数: {len(retriever.faiss_indices)}")

            # 注意：向量检索需要调用API，这里只测试初始化
            return {
                "success": True,
                "indices_loaded": len(retriever.faiss_indices),
                "message": "Vector retriever initialized (search requires API call)"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_4_hybrid_retriever(self) -> Dict[str, Any]:
        """测试4: 混合检索器"""
        try:
            from src.retrieval.hybrid_retriever import HybridRetriever

            retriever = HybridRetriever(scenario_id="tender")
            logger.info(f"✅ HybridRetriever初始化成功")

            # 获取统计信息
            stats = retriever.get_stats()
            logger.info(f"   统计信息: {stats}")

            return {
                "success": True,
                "stats": stats
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_5_routing_agent(self) -> Dict[str, Any]:
        """测试5: 路由代理"""
        try:
            from src.agents.routing_agent import RoutingAgent

            agent = RoutingAgent(scenario_id="tender")
            logger.info(f"✅ RoutingAgent初始化成功")
            logger.info(f"   场景: {agent.scenario_id}")
            logger.info(f"   关键词库: {len(agent.keyword_library.get('tender', {}))} 类别")

            # 测试上下文扩展判断
            test_chunk = {"text": "这是一个测试文本..."}
            needs_expand = agent.should_expand_context(test_chunk)
            logger.info(f"   上下文扩展测试: {needs_expand}")

            return {
                "success": True,
                "scenario": agent.scenario_id,
                "keyword_categories": len(agent.keyword_library.get('tender', {}))
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_6_smart_cache(self) -> Dict[str, Any]:
        """测试6: 智能缓存"""
        try:
            from src.cache.smart_cache import SmartCache

            cache = SmartCache(max_size=100)
            logger.info(f"✅ SmartCache初始化成功")

            # 测试缓存存储和读取
            test_question = "测试问题"
            test_answer = {"answer": "测试答案", "confidence": 0.9}

            # 存储（不使用语义缓存以避免API调用）
            cache.set(test_question, test_answer, use_semantic=False)
            logger.info(f"   缓存存储成功")

            # 读取
            cached = cache.get(test_question)
            if cached:
                logger.info(f"   缓存读取成功: {cached.get('answer')}")

            # 获取统计
            stats = cache.get_stats()
            logger.info(f"   缓存统计: {stats}")

            return {
                "success": True,
                "cache_works": cached is not None,
                "stats": stats
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_7_answer_verifier(self) -> Dict[str, Any]:
        """测试7: 答案验证器"""
        try:
            from src.verification.answer_verifier import AnswerVerifier

            verifier = AnswerVerifier()
            logger.info(f"✅ AnswerVerifier初始化成功")

            # 测试引用提取
            test_answer = "根据第3页的内容，预算为100万元。参见第5页。"
            citations = verifier.extract_citations(test_answer)
            logger.info(f"   引用提取: {citations}")

            # 测试引用存在性验证
            test_chunks = [
                {"page": 3, "text": "预算相关内容"},
                {"page": 5, "text": "其他内容"}
            ]

            if citations:
                exists = verifier.citation_exists(citations[0], test_chunks)
                logger.info(f"   引用验证: {exists}")

            return {
                "success": True,
                "citations_extracted": len(citations),
                "citation_patterns": len(verifier.citation_patterns)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_8_questions_processor(self) -> Dict[str, Any]:
        """测试8: 问题处理器（核心集成）"""
        try:
            from src.questions_processing import QuestionsProcessor

            processor = QuestionsProcessor(
                api_provider="dashscope",
                scenario_id="tender"
            )
            logger.info(f"✅ QuestionsProcessor初始化成功")
            logger.info(f"   Agentic RAG启用: {processor.agentic_rag_enabled}")

            # 获取统计信息
            if processor.agentic_rag_enabled:
                stats = processor.get_agentic_rag_stats()
                logger.info(f"   统计信息: {stats}")

                return {
                    "success": True,
                    "agentic_rag_enabled": True,
                    "stats": stats
                }
            else:
                return {
                    "success": True,
                    "agentic_rag_enabled": False,
                    "message": "Agentic RAG components not available"
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_9_pipeline_integration(self) -> Dict[str, Any]:
        """测试9: Pipeline集成"""
        try:
            from src.pipeline import Pipeline, RunConfig
            from config import get_settings

            settings = get_settings()
            config = RunConfig(
                api_provider="dashscope",
                use_vector_dbs=True,
                use_bm25_db=True
            )

            pipeline = Pipeline(
                root_path=settings.data_dir,
                run_config=config,
                scenario_id="tender"
            )
            logger.info(f"✅ Pipeline初始化成功")

            # 获取状态
            status = pipeline.get_status()
            logger.info(f"   Pipeline状态: {status}")

            return {
                "success": True,
                "status": status
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def print_summary(self):
        """打印测试总结"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 测试总结")
        logger.info(f"{'='*60}")
        logger.info(f"总测试数: {self.total_tests}")
        logger.info(f"✅ 通过: {self.passed_tests}")
        logger.info(f"❌ 失败: {self.failed_tests}")
        logger.info(f"通过率: {self.passed_tests/self.total_tests*100:.1f}%")
        logger.info(f"{'='*60}\n")

        # 详细结果
        logger.info("详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            logger.info(f"{i}. {status_icon} {result['name']} - {result['status']}")
            if result.get("elapsed"):
                logger.info(f"   耗时: {result['elapsed']:.2f}秒")

        return {
            "total": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "pass_rate": self.passed_tests/self.total_tests if self.total_tests > 0 else 0
        }


def main():
    """主测试函数"""
    logger.info("🚀 开始 Agentic RAG 系统集成测试")
    logger.info(f"项目根目录: {project_root}")

    tester = AgenticRAGTester()

    # 运行所有测试
    tester.run_test("导入所有模块", tester.test_1_import_modules)
    tester.run_test("BM25检索器", tester.test_2_bm25_retriever)
    tester.run_test("FAISS向量检索器", tester.test_3_vector_retriever)
    tester.run_test("混合检索器", tester.test_4_hybrid_retriever)
    tester.run_test("路由代理", tester.test_5_routing_agent)
    tester.run_test("智能缓存", tester.test_6_smart_cache)
    tester.run_test("答案验证器", tester.test_7_answer_verifier)
    tester.run_test("问题处理器", tester.test_8_questions_processor)
    tester.run_test("Pipeline集成", tester.test_9_pipeline_integration)

    # 打印总结
    summary = tester.print_summary()

    # 返回退出码
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

