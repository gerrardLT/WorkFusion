"""
智能缓存系统
实现精确缓存和语义缓存，提升检索性能和降低API成本
"""

import logging
import hashlib
import time
from typing import Dict, Any, Optional, List
from collections import OrderedDict
import numpy as np

from api_requests import APIProcessor
from config import get_settings

logger = logging.getLogger(__name__)


class SmartCache:
    """
    智能缓存系统

    两层缓存机制：
    1. 精确缓存 - MD5 hash匹配，7天过期
    2. 语义缓存 - 向量相似度匹配（>0.95），3天过期
    """

    def __init__(
        self,
        max_size: int = 1000,
        exact_ttl: int = 7 * 24 * 3600,  # 7天
        semantic_ttl: int = 3 * 24 * 3600,  # 3天
        semantic_threshold: float = 0.95
    ):
        """
        初始化智能缓存

        Args:
            max_size: 最大缓存条目数
            exact_ttl: 精确缓存过期时间（秒）
            semantic_ttl: 语义缓存过期时间（秒）
            semantic_threshold: 语义相似度阈值
        """
        self.max_size = max_size
        self.exact_ttl = exact_ttl
        self.semantic_ttl = semantic_ttl
        self.semantic_threshold = semantic_threshold

        # 精确缓存：key = question_hash, value = (answer_data, timestamp)
        self.exact_cache = OrderedDict()

        # 语义缓存：key = question_hash, value = (question, embedding, answer_data, timestamp)
        self.semantic_cache = OrderedDict()

        # 统计信息
        self.stats = {
            "exact_hits": 0,
            "semantic_hits": 0,
            "misses": 0,
            "evictions": 0
        }

        # API处理器（用于生成嵌入向量）
        self.settings = get_settings()
        self.api_processor = APIProcessor(provider="dashscope")

        logger.info(
            f"SmartCache initialized: max_size={max_size}, "
            f"exact_ttl={exact_ttl}s, semantic_ttl={semantic_ttl}s, "
            f"threshold={semantic_threshold}"
        )

    def get(self, question: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存答案

        Args:
            question: 用户问题

        Returns:
            缓存的答案数据，如果未命中返回 None
        """
        if not question:
            return None

        try:
            # 第一层：精确匹配
            exact_result = self._get_exact(question)
            if exact_result:
                self.stats["exact_hits"] += 1
                logger.info(f"精确缓存命中: {question[:30]}")
                return exact_result

            # 第二层：语义匹配
            semantic_result = self._get_semantic(question)
            if semantic_result:
                self.stats["semantic_hits"] += 1
                logger.info(f"语义缓存命中: {question[:30]}")
                return semantic_result

            # 缓存未命中
            self.stats["misses"] += 1
            logger.debug(f"缓存未命中: {question[:30]}")
            return None

        except Exception as e:
            logger.error(f"缓存读取失败: {e}")
            return None

    def set(
        self,
        question: str,
        answer_data: Dict[str, Any],
        use_semantic: bool = True
    ):
        """
        存储缓存

        Args:
            question: 用户问题
            answer_data: 答案数据（包含answer, reasoning等）
            use_semantic: 是否同时存储到语义缓存
        """
        if not question or not answer_data:
            return

        try:
            current_time = time.time()

            # 存储到精确缓存
            question_hash = self._hash_question(question)
            self.exact_cache[question_hash] = (answer_data, current_time)
            self._move_to_end(self.exact_cache, question_hash)

            # 存储到语义缓存（需要生成嵌入向量）
            if use_semantic:
                try:
                    embedding = self._get_embedding(question)
                    self.semantic_cache[question_hash] = (
                        question,
                        embedding,
                        answer_data,
                        current_time
                    )
                    self._move_to_end(self.semantic_cache, question_hash)
                except Exception as e:
                    logger.warning(f"语义缓存存储失败: {e}")

            # LRU淘汰
            self._evict_if_needed()

            logger.debug(f"缓存已存储: {question[:30]}")

        except Exception as e:
            logger.error(f"缓存写入失败: {e}")

    def _get_exact(self, question: str) -> Optional[Dict]:
        """精确缓存查询"""
        question_hash = self._hash_question(question)

        if question_hash in self.exact_cache:
            answer_data, timestamp = self.exact_cache[question_hash]

            # 检查是否过期
            if time.time() - timestamp > self.exact_ttl:
                logger.debug("精确缓存已过期")
                del self.exact_cache[question_hash]
                return None

            # 命中，移到最后（LRU）
            self._move_to_end(self.exact_cache, question_hash)
            return answer_data

        return None

    def _get_semantic(self, question: str) -> Optional[Dict]:
        """语义缓存查询"""
        if not self.semantic_cache:
            return None

        try:
            # 生成查询嵌入
            query_embedding = self._get_embedding(question)

            # 遍历语义缓存
            best_match = None
            best_similarity = 0.0

            for cache_hash, (cache_q, cache_emb, cache_ans, timestamp) in list(self.semantic_cache.items()):
                # 检查是否过期
                if time.time() - timestamp > self.semantic_ttl:
                    logger.debug(f"语义缓存已过期: {cache_q[:30]}")
                    del self.semantic_cache[cache_hash]
                    continue

                # 计算相似度
                similarity = self._cosine_similarity(query_embedding, cache_emb)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (cache_hash, cache_ans)

            # 检查是否达到阈值
            if best_match and best_similarity >= self.semantic_threshold:
                cache_hash, cache_ans = best_match
                logger.debug(f"语义相似度: {best_similarity:.3f}")
                self._move_to_end(self.semantic_cache, cache_hash)
                return cache_ans

            return None

        except Exception as e:
            logger.error(f"语义缓存查询失败: {e}")
            return None

    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本嵌入向量"""
        embeddings = self.api_processor.get_embeddings([text])
        if embeddings:
            return np.array(embeddings[0], dtype=np.float32)
        raise ValueError("Failed to get embedding")

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)

        if norm_product == 0:
            return 0.0

        return float(dot_product / norm_product)

    def _hash_question(self, question: str) -> str:
        """生成问题的hash值"""
        return hashlib.md5(question.encode('utf-8')).hexdigest()

    def _move_to_end(self, cache: OrderedDict, key: str):
        """移动到末尾（LRU最近使用）"""
        if key in cache:
            cache.move_to_end(key)

    def _evict_if_needed(self):
        """LRU淘汰策略"""
        # 淘汰精确缓存
        while len(self.exact_cache) > self.max_size:
            evicted_key = next(iter(self.exact_cache))
            del self.exact_cache[evicted_key]
            self.stats["evictions"] += 1
            logger.debug(f"精确缓存淘汰: {evicted_key[:16]}")

        # 淘汰语义缓存
        while len(self.semantic_cache) > self.max_size // 2:  # 语义缓存占一半
            evicted_key = next(iter(self.semantic_cache))
            del self.semantic_cache[evicted_key]
            self.stats["evictions"] += 1
            logger.debug(f"语义缓存淘汰: {evicted_key[:16]}")

    def get_hit_rate(self) -> float:
        """
        计算缓存命中率

        Returns:
            命中率（0-1）
        """
        total = sum([
            self.stats["exact_hits"],
            self.stats["semantic_hits"],
            self.stats["misses"]
        ])

        if total == 0:
            return 0.0

        hits = self.stats["exact_hits"] + self.stats["semantic_hits"]
        return hits / total

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total = sum([
            self.stats["exact_hits"],
            self.stats["semantic_hits"],
            self.stats["misses"]
        ])

        return {
            "exact_hits": self.stats["exact_hits"],
            "semantic_hits": self.stats["semantic_hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "total_queries": total,
            "hit_rate": self.get_hit_rate(),
            "exact_cache_size": len(self.exact_cache),
            "semantic_cache_size": len(self.semantic_cache),
            "total_cache_size": len(self.exact_cache) + len(self.semantic_cache)
        }

    def clear(self, cache_type: str = "all"):
        """
        清空缓存

        Args:
            cache_type: 缓存类型 ("exact", "semantic", "all")
        """
        if cache_type in ("exact", "all"):
            self.exact_cache.clear()
            logger.info("精确缓存已清空")

        if cache_type in ("semantic", "all"):
            self.semantic_cache.clear()
            logger.info("语义缓存已清空")

        if cache_type == "all":
            self.stats = {
                "exact_hits": 0,
                "semantic_hits": 0,
                "misses": 0,
                "evictions": 0
            }
            logger.info("缓存统计已重置")

    def warm_up(self, qa_pairs: List[Dict[str, str]]):
        """
        预热缓存（批量加载常见问答）

        Args:
            qa_pairs: 问答对列表，每个元素包含 question 和 answer
        """
        logger.info(f"开始预热缓存: {len(qa_pairs)} 个问答对")

        for pair in qa_pairs:
            question = pair.get("question", "")
            answer = pair.get("answer", "")

            if question and answer:
                answer_data = {
                    "answer": answer,
                    "cached": True,
                    "warm_up": True
                }
                self.set(question, answer_data, use_semantic=True)

        logger.info(f"缓存预热完成: {len(self.exact_cache)} 条精确缓存, {len(self.semantic_cache)} 条语义缓存")
