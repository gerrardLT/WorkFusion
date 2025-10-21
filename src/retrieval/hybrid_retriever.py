"""
混合检索引擎
结合 BM25 和 FAISS，使用 RRF 融合重排序
"""

import logging
import time
from typing import List, Dict

from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.vector_retriever import VectorRetriever

logger = logging.getLogger(__name__)


class RRFReranker:
    """Reciprocal Rank Fusion 重排序器"""

    def __init__(self, k: int = 60):
        """
        初始化 RRF 重排序器

        Args:
            k: RRF 参数，控制排名的影响权重
        """
        self.k = k
        logger.debug(f"RRFReranker initialized with k={k}")

    def fuse(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        top_k: int = 10,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> List[Dict]:
        """
        RRF 融合算法

        RRF 公式: score = weight / (k + rank)

        Args:
            bm25_results: BM25 检索结果
            vector_results: 向量检索结果
            top_k: 返回结果数量
            bm25_weight: BM25 权重
            vector_weight: 向量权重

        Returns:
            融合后的结果列表
        """
        # 使用 chunk_id 作为唯一标识
        chunk_scores = {}

        # 1. 计算 BM25 的 RRF 分数
        for rank, result in enumerate(bm25_results, start=1):
            chunk_id = result["chunk_id"]
            rrf_score = bm25_weight / (self.k + rank)

            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = {
                    "text": result["text"],
                    "page": result["page"],
                    "file_id": result.get("file_id", ""),
                    "bm25_score": result["score"],
                    "vector_score": 0.0,
                    "rrf_score": 0.0,
                    "bm25_rank": rank,
                    "vector_rank": None
                }
            chunk_scores[chunk_id]["rrf_score"] += rrf_score

        # 2. 计算向量检索的 RRF 分数
        for rank, result in enumerate(vector_results, start=1):
            chunk_id = result["chunk_id"]
            rrf_score = vector_weight / (self.k + rank)

            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = {
                    "text": result["text"],
                    "page": result["page"],
                    "file_id": result.get("file_id", ""),
                    "bm25_score": 0.0,
                    "vector_score": result["score"],
                    "rrf_score": 0.0,
                    "bm25_rank": None,
                    "vector_rank": rank
                }
            else:
                chunk_scores[chunk_id]["vector_score"] = result["score"]
                chunk_scores[chunk_id]["vector_rank"] = rank

            chunk_scores[chunk_id]["rrf_score"] += rrf_score

        # 3. 排序并返回 top-k
        sorted_chunks = sorted(
            chunk_scores.items(),
            key=lambda x: x[1]["rrf_score"],
            reverse=True
        )[:top_k]

        # 4. 格式化输出
        final_results = []
        for chunk_id, scores in sorted_chunks:
            final_results.append({
                "chunk_id": chunk_id,
                "text": scores["text"],
                "page": scores["page"],
                "file_id": scores["file_id"],
                "bm25_score": scores["bm25_score"],
                "vector_score": scores["vector_score"],
                "rrf_score": scores["rrf_score"],
                "bm25_rank": scores["bm25_rank"],
                "vector_rank": scores["vector_rank"],
                "source": "hybrid"
            })

        logger.debug(
            f"RRF fusion: {len(bm25_results)} BM25 + {len(vector_results)} vector "
            f"→ {len(chunk_scores)} unique → top {len(final_results)}"
        )

        return final_results


class HybridRetriever:
    """混合检索引擎"""

    def __init__(self, scenario_id: str):
        """
        初始化混合检索引擎

        Args:
            scenario_id: 场景ID
        """
        self.scenario_id = scenario_id

        # 初始化子检索器
        self.bm25_retriever = BM25Retriever(scenario_id)
        self.vector_retriever = VectorRetriever(scenario_id)
        self.reranker = RRFReranker(k=60)

        # 统计信息
        self.stats = {
            "total_queries": 0,
            "avg_time": 0.0,
            "bm25_only": 0,
            "vector_only": 0,
            "hybrid": 0,
            "failed": 0
        }

        logger.info(f"HybridRetriever initialized for scenario: {scenario_id}")

    def retrieve(
        self,
        question: str,
        top_k: int = 10,
        use_bm25: bool = True,
        use_vector: bool = True,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ) -> List[Dict]:
        """
        混合检索主接口

        Args:
            question: 查询文本
            top_k: 返回结果数量
            use_bm25: 是否使用 BM25
            use_vector: 是否使用向量检索
            bm25_weight: BM25 权重
            vector_weight: 向量权重

        Returns:
            检索结果列表
        """
        start_time = time.time()

        try:
            bm25_results = []
            vector_results = []

            # 1. BM25 检索（如果启用）
            if use_bm25:
                try:
                    bm25_results = self.bm25_retriever.search(question, k=top_k * 2)
                    logger.info(f"BM25检索: 找到 {len(bm25_results)} 个结果")
                except Exception as e:
                    logger.warning(f"BM25检索失败: {e}")

            # 2. 向量检索（如果启用）
            if use_vector:
                try:
                    vector_results = self.vector_retriever.search(question, k=top_k * 2)
                    logger.info(f"向量检索: 找到 {len(vector_results)} 个结果")
                except Exception as e:
                    logger.warning(f"向量检索失败: {e}")

            # 3. 降级策略
            if not bm25_results and not vector_results:
                logger.error("所有检索方式都失败")
                self.stats["failed"] += 1
                return []

            # 4. 结果处理
            if bm25_results and not vector_results:
                # 只有 BM25 结果
                logger.info("使用纯 BM25 结果")
                self.stats["bm25_only"] += 1
                final_results = bm25_results[:top_k]
            elif vector_results and not bm25_results:
                # 只有向量结果
                logger.info("使用纯向量结果")
                self.stats["vector_only"] += 1
                final_results = vector_results[:top_k]
            else:
                # RRF 融合重排序
                logger.info("使用 RRF 融合重排序")
                self.stats["hybrid"] += 1
                final_results = self.reranker.fuse(
                    bm25_results,
                    vector_results,
                    top_k=top_k,
                    bm25_weight=bm25_weight,
                    vector_weight=vector_weight
                )

            # 5. 更新统计
            elapsed = time.time() - start_time
            self.stats["total_queries"] += 1

            # 更新平均时间
            if self.stats["total_queries"] == 1:
                self.stats["avg_time"] = elapsed
            else:
                self.stats["avg_time"] = (
                    self.stats["avg_time"] * (self.stats["total_queries"] - 1) + elapsed
                ) / self.stats["total_queries"]

            logger.info(
                f"混合检索完成: {len(final_results)} 个结果, "
                f"耗时 {elapsed:.2f}s"
            )

            return final_results

        except Exception as e:
            logger.error(f"混合检索失败: {str(e)}")
            self.stats["failed"] += 1
            return []

    def get_stats(self) -> Dict:
        """
        获取检索统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_queries": self.stats["total_queries"],
            "avg_time": round(self.stats["avg_time"], 3),
            "bm25_only_count": self.stats["bm25_only"],
            "vector_only_count": self.stats["vector_only"],
            "hybrid_count": self.stats["hybrid"],
            "failed_count": self.stats["failed"]
        }

