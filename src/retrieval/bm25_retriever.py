"""
BM25 检索器
封装现有 BM25 索引，提供标准检索接口
"""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

from config import get_settings

logger = logging.getLogger(__name__)


class BM25Retriever:
    """BM25 关键词检索器"""

    def __init__(self, scenario_id: str):
        """
        初始化 BM25 检索器

        Args:
            scenario_id: 场景ID
        """
        self.scenario_id = scenario_id
        self.settings = get_settings()

        # BM25 索引和元数据
        self.bm25_indices = {}  # file_id -> BM25 index
        self.chunks_metadata = {}  # file_id -> chunks metadata

        # 加载 BM25 索引
        self._load_bm25_indices()

        logger.info(
            f"BM25Retriever initialized for scenario: {scenario_id}, "
            f"loaded {len(self.bm25_indices)} indices"
        )

    def _load_bm25_indices(self):
        """从磁盘加载所有 BM25 索引"""
        try:
            # 构建 BM25 数据库路径
            bm25_dir = Path(self.settings.data_dir) / "databases" / "bm25"

            if not bm25_dir.exists():
                logger.warning(f"BM25 directory not found: {bm25_dir}")
                return

            # 加载所有 .pkl 文件
            bm25_files = list(bm25_dir.glob("*.pkl"))

            for bm25_file in bm25_files:
                try:
                    with open(bm25_file, "rb") as f:
                        data = pickle.load(f)

                    # 提取 file_id
                    file_id = data["metadata"]["file_id"]

                    # 存储索引和元数据
                    self.bm25_indices[file_id] = data["index"]
                    self.chunks_metadata[file_id] = data["chunks"]

                    logger.debug(f"Loaded BM25 index: {file_id}")

                except Exception as e:
                    logger.error(f"Failed to load {bm25_file}: {e}")

            logger.info(f"Loaded {len(self.bm25_indices)} BM25 indices")

        except Exception as e:
            logger.error(f"Failed to load BM25 indices: {e}")

    def _tokenize(self, text: str) -> List[str]:
        """
        中文分词（与 BM25Ingestor 保持一致）

        Args:
            text: 输入文本

        Returns:
            分词结果
        """
        tokens = []
        current_word = ""

        for char in text:
            if "\u4e00" <= char <= "\u9fff":  # 中文字符
                if current_word:
                    tokens.append(current_word)
                    current_word = ""
                tokens.append(char)
            elif char.isalnum():  # 英文数字字符
                current_word += char
            else:  # 标点符号等
                if current_word:
                    tokens.append(current_word)
                    current_word = ""
                if not char.isspace():
                    tokens.append(char)

        if current_word:
            tokens.append(current_word)

        return [t for t in tokens if t.strip()]

    def search(self, query: str, k: int = 10) -> List[Dict]:
        """
        BM25 检索

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            检索结果列表，每个结果包含:
                - chunk_id: 块ID
                - text: 文本内容
                - score: BM25 分数
                - page: 页码（如果有）
                - source: 来源 (bm25)
        """
        if not self.bm25_indices:
            logger.warning("No BM25 indices loaded")
            return []

        try:
            # 对查询分词
            query_tokens = self._tokenize(query)

            if not query_tokens:
                logger.warning("Query tokenization resulted in empty tokens")
                return []

            all_results = []

            # 遍历所有索引文件
            for file_id, bm25_index in self.bm25_indices.items():
                chunks = self.chunks_metadata.get(file_id, [])

                if not chunks:
                    continue

                # BM25 评分
                scores = bm25_index.get_scores(query_tokens)

                # 构建结果
                for idx, (score, chunk_text) in enumerate(zip(scores, chunks)):
                    if score > 0:  # 只保留有得分的结果
                        all_results.append({
                            "chunk_id": f"{file_id}_chunk_{idx}",
                            "text": chunk_text,
                            "score": float(score),
                            "page": idx + 1,  # 假设每个 chunk 对应一页
                            "source": "bm25",
                            "file_id": file_id
                        })

            # 按分数排序
            all_results.sort(key=lambda x: x["score"], reverse=True)

            # 返回 top-k
            return all_results[:k]

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

