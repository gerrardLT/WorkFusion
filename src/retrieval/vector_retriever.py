"""
向量检索器
封装现有 FAISS 索引，提供标准检索接口
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import faiss

from config import get_settings
from api_requests import APIProcessor

logger = logging.getLogger(__name__)


class VectorRetriever:
    """FAISS 向量检索器"""

    def __init__(self, scenario_id: str):
        """
        初始化向量检索器

        Args:
            scenario_id: 场景ID
        """
        self.scenario_id = scenario_id
        self.settings = get_settings()
        self.api_processor = APIProcessor(provider="dashscope")

        # FAISS 索引和元数据
        self.faiss_indices = {}  # file_id -> FAISS index
        self.chunks_metadata = {}  # file_id -> chunks and metadata

        # 加载 FAISS 索引
        self._load_faiss_indices()

        logger.info(
            f"VectorRetriever initialized for scenario: {scenario_id}, "
            f"loaded {len(self.faiss_indices)} indices"
        )

    def _load_faiss_indices(self):
        """从磁盘加载所有 FAISS 索引"""
        try:
            # 构建向量数据库路径
            vector_dir = Path(self.settings.data_dir) / "databases" / "vector_dbs"

            if not vector_dir.exists():
                logger.warning(f"Vector directory not found: {vector_dir}")
                return

            # 加载所有 .faiss 文件
            faiss_files = list(vector_dir.glob("*.faiss"))

            for faiss_file in faiss_files:
                try:
                    # 加载 FAISS 索引
                    index = faiss.read_index(str(faiss_file))

                    # 提取 file_id
                    file_id = faiss_file.stem.replace("_vector", "")

                    # 加载对应的 chunks 元数据
                    metadata_file = faiss_file.parent / f"{file_id}_chunks.json"
                    if metadata_file.exists():
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)

                        self.faiss_indices[file_id] = index
                        self.chunks_metadata[file_id] = metadata

                        logger.debug(f"Loaded FAISS index: {file_id}")
                    else:
                        logger.warning(f"Metadata file not found: {metadata_file}")

                except Exception as e:
                    logger.error(f"Failed to load {faiss_file}: {e}")

            logger.info(f"Loaded {len(self.faiss_indices)} FAISS indices")

        except Exception as e:
            logger.error(f"Failed to load FAISS indices: {e}")

    def _get_query_embedding(self, query: str) -> np.ndarray:
        """
        生成查询向量

        Args:
            query: 查询文本

        Returns:
            查询向量（已标准化）
        """
        try:
            # 调用 API 获取嵌入向量
            embeddings = self.api_processor.get_embeddings([query])

            if not embeddings:
                raise ValueError("Failed to get embedding for query")

            # 转换为 numpy 数组并标准化
            embedding = np.array(embeddings[0], dtype=np.float32)
            embedding = embedding.reshape(1, -1)
            faiss.normalize_L2(embedding)

            return embedding

        except Exception as e:
            logger.error(f"Failed to get query embedding: {e}")
            raise

    def search(
        self, query: str, k: int = 10, min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        向量检索

        Args:
            query: 查询文本
            k: 返回结果数量
            min_similarity: 最小相似度阈值（余弦相似度，范围0-1）

        Returns:
            检索结果列表，每个结果包含:
                - chunk_id: 块ID
                - text: 文本内容
                - score: 相似度分数
                - page: 页码（如果有）
                - source: 来源 (vector)
        """
        if not self.faiss_indices:
            logger.warning("No FAISS indices loaded")
            return []

        try:
            # 获取查询向量
            query_embedding = self._get_query_embedding(query)

            all_results = []

            # 遍历所有索引文件
            for file_id, faiss_index in self.faiss_indices.items():
                metadata = self.chunks_metadata.get(file_id, {})
                chunks = metadata.get("chunks", [])
                chunk_metadata = metadata.get("chunk_metadata", [])

                if not chunks:
                    continue

                # FAISS 相似度搜索
                # IndexFlatIP 返回的是内积，对于标准化向量等价于余弦相似度
                distances, indices = faiss_index.search(query_embedding, min(k * 2, faiss_index.ntotal))

                # 构建结果
                for dist, idx in zip(distances[0], indices[0]):
                    similarity = float(dist)

                    # 过滤低相似度结果
                    if similarity >= min_similarity and idx < len(chunks):
                        # 获取页码信息
                        page = 0
                        if idx < len(chunk_metadata):
                            page = chunk_metadata[idx].get("page_number", idx + 1)
                        else:
                            page = idx + 1

                        all_results.append({
                            "chunk_id": f"{file_id}_chunk_{idx}",
                            "text": chunks[idx],
                            "score": similarity,
                            "page": page,
                            "source": "vector",
                            "file_id": file_id
                        })

            # 按相似度排序
            all_results.sort(key=lambda x: x["score"], reverse=True)

            # 返回 top-k
            return all_results[:k]

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

