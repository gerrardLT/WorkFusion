"""
数据摄取和向量化模块
负责处理PDF解析结果，创建BM25索引和向量数据库
"""

import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import hashlib
from datetime import datetime
import time

import numpy as np
import faiss
from tqdm import tqdm
from rank_bm25 import BM25Okapi
from tenacity import retry, wait_exponential, stop_after_attempt

from config import get_settings
from api_requests import APIProcessor
from data_models import ReportMetadata, ChunkMetadata, ProcessingStatus

logger = logging.getLogger(__name__)


class BM25Ingestor:
    """BM25索引构建与管理类"""

    def __init__(self):
        """初始化BM25构建器"""
        self.settings = get_settings()
        logger.info("BM25Ingestor初始化完成")

    def create_bm25_index(self, chunks: List[str]) -> BM25Okapi:
        """从文本块列表创建BM25索引

        Args:
            chunks: 文本块列表

        Returns:
            BM25索引对象
        """
        try:
            # 简单的中文分词（按字符和空格分割）
            tokenized_chunks = []
            for chunk in chunks:
                # 对中文按字符分割，对英文按空格分割
                tokens = []
                current_word = ""

                for char in chunk:
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

                tokenized_chunks.append([t for t in tokens if t.strip()])

            logger.debug(f"创建BM25索引，文档数: {len(tokenized_chunks)}")
            return BM25Okapi(tokenized_chunks)

        except Exception as e:
            logger.error(f"创建BM25索引失败: {str(e)}")
            raise

    def process_single_report(
        self, report_data: Dict[str, Any], output_dir: Path
    ) -> Tuple[bool, Optional[str]]:
        """处理单个报告，生成BM25索引

        Args:
            report_data: 解析后的报告数据
            output_dir: 输出目录

        Returns:
            (是否成功, 输出文件路径或错误信息)
        """
        try:
            # 提取文本块
            chunks = []
            if "pages" in report_data:
                for page in report_data["pages"]:
                    if page.get("text"):
                        chunks.append(page["text"])

            # 如果有整体文本内容，也加入
            if "text_content" in report_data and report_data["text_content"]:
                chunks.append(report_data["text_content"])

            if not chunks:
                error_msg = "报告中没有找到文本内容"
                logger.warning(f"BM25索引构建跳过: {error_msg}")
                return False, error_msg

            # 创建BM25索引
            bm25_index = self.create_bm25_index(chunks)

            # 生成文件ID
            file_id = self._generate_file_id(report_data)

            # 使用MD5 hash生成安全文件名（避免中文）
            import hashlib
            safe_filename = hashlib.md5(file_id.encode()).hexdigest()

            # 保存索引
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{safe_filename}_bm25.pkl"

            logger.debug(f"原始file_id: {file_id}, MD5: {safe_filename}")

            with open(output_file, "wb") as f:
                pickle.dump(
                    {
                        "index": bm25_index,
                        "chunks": chunks,
                        "metadata": {
                            "file_id": file_id,
                            "chunk_count": len(chunks),
                            "created_at": datetime.now().isoformat(),
                            "index_type": "BM25Okapi",
                        },
                    },
                    f,
                )

            logger.info(f"BM25索引已保存: {output_file}")
            return True, str(output_file)

        except Exception as e:
            error_msg = f"BM25索引构建失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def batch_process_reports(
        self, reports_dir: Path, output_dir: Path
    ) -> Dict[str, Any]:
        """批量处理报告，生成BM25索引

        Args:
            reports_dir: 报告文件目录
            output_dir: 输出目录

        Returns:
            处理结果统计
        """
        report_files = list(reports_dir.glob("*_parsed.json"))

        logger.info(f"开始批量BM25索引构建，共 {len(report_files)} 个文件")

        results = {
            "total_files": len(report_files),
            "successful": 0,
            "failed": 0,
            "results": [],
        }

        for report_file in tqdm(report_files, desc="BM25索引构建"):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report_data = json.load(f)

                success, result = self.process_single_report(report_data, output_dir)

                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1

                results["results"].append(
                    {
                        "file_path": str(report_file),
                        "success": success,
                        "result": result,
                    }
                )

            except Exception as e:
                results["failed"] += 1
                results["results"].append(
                    {"file_path": str(report_file), "success": False, "result": str(e)}
                )
                logger.error(f"处理文件失败: {report_file}, 错误: {str(e)}")

        logger.info(
            f"BM25批量处理完成: 成功 {results['successful']}, 失败 {results['failed']}"
        )
        return results

    def _generate_file_id(self, report_data: Dict[str, Any]) -> str:
        """生成文件ID"""
        # 使用处理信息中的file_id，或从文件信息生成
        if (
            "processing_info" in report_data
            and "file_id" in report_data["processing_info"]
        ):
            return report_data["processing_info"]["file_id"]

        # 从文档信息生成ID
        doc_info = report_data.get("document_info", {})
        file_name = doc_info.get("file_name", "unknown")
        file_size = doc_info.get("file_size", 0)

        # 生成唯一ID
        content = f"{file_name}_{file_size}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return hashlib.md5(content.encode()).hexdigest()


class VectorDBIngestor:
    """向量数据库构建与管理类"""

    def __init__(self, api_provider: str = "dashscope"):
        """初始化向量数据库构建器

        Args:
            api_provider: API提供商名称
        """
        self.settings = get_settings()
        self.api_processor = APIProcessor(provider=api_provider)
        # 🚀 性能优化：增加批次大小，减少延迟
        self.batch_size = 25       # 从5提升到25，减少API调用次数
        self.base_delay = 0.1      # 从0.5s减少到0.1s
        self.max_delay = 1.0       # 从5.0s减少到1.0s
        # 单文件模式下不需要文件间延迟

        logger.info(f"VectorDBIngestor初始化完成，provider: {api_provider}, batch_size: {self.batch_size}")

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=30), stop=stop_after_attempt(5)
    )
    def get_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """获取文本嵌入向量，支持重试和批处理

        Args:
            texts: 文本列表
            model: 嵌入模型名称

        Returns:
            嵌入向量列表
        """
        if not texts:
            return []

        # 过滤空文本
        valid_texts = [text.strip() for text in texts if text.strip()]
        if not valid_texts:
            raise ValueError("所有输入文本都为空")

        try:
            logger.debug(f"获取嵌入向量，文本数量: {len(valid_texts)}")

            all_embeddings = []

            # 分批处理
            for i in range(0, len(valid_texts), self.batch_size):
                batch = valid_texts[i : i + self.batch_size]

                logger.debug(
                    f"处理批次 {i//self.batch_size + 1}, 文本数量: {len(batch)}"
                )

                # 调用API获取嵌入向量
                embeddings = self.api_processor.get_embeddings(batch, model)
                all_embeddings.extend(embeddings)

                # 动态延迟，避免API限制
                if i + self.batch_size < len(valid_texts):
                    # 根据批次数量动态调整延迟
                    batch_number = i // self.batch_size + 1
                    delay = min(self.base_delay * batch_number, self.max_delay)
                    logger.debug(f"批次间延迟: {delay:.2f}秒")
                    time.sleep(delay)

            logger.info(f"成功获取 {len(all_embeddings)} 个嵌入向量")
            return all_embeddings

        except Exception as e:
            logger.error(f"获取嵌入向量失败: {str(e)}")
            raise

    def create_vector_index(self, embeddings: List[List[float]]) -> faiss.IndexFlatIP:
        """创建FAISS向量索引

        Args:
            embeddings: 嵌入向量列表

        Returns:
            FAISS索引对象
        """
        if not embeddings:
            raise ValueError("嵌入向量列表不能为空")

        try:
            # 转换为numpy数组
            embeddings_array = np.array(embeddings, dtype=np.float32)

            # 检查维度一致性
            if len(embeddings_array.shape) != 2:
                raise ValueError("嵌入向量格式错误")

            # 标准化向量（用于余弦相似度）
            faiss.normalize_L2(embeddings_array)

            # 创建内积索引（适用于标准化后的向量）
            dimension = embeddings_array.shape[1]
            index = faiss.IndexFlatIP(dimension)

            # 添加向量到索引
            index.add(embeddings_array)

            logger.info(
                f"创建FAISS索引成功，维度: {dimension}, 向量数量: {len(embeddings)}"
            )
            return index

        except Exception as e:
            logger.error(f"创建FAISS索引失败: {str(e)}")
            raise

    def process_single_report(
        self, report_data: Dict[str, Any], output_dir: Path, model: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """处理单个报告，生成向量数据库

        Args:
            report_data: 解析后的报告数据
            output_dir: 输出目录
            model: 嵌入模型名称

        Returns:
            (是否成功, 输出文件路径或错误信息)
        """
        try:
            # 提取文本块
            chunks = []
            chunk_metadata = []

            if "pages" in report_data:
                for page_idx, page in enumerate(report_data["pages"]):
                    if page.get("text"):
                        chunks.append(page["text"])
                        chunk_metadata.append(
                            {
                                "type": "page_text",
                                "page_number": page.get("page_number", page_idx + 1),
                                "word_count": len(page["text"].split()),
                            }
                        )

            # 处理表格内容
            if "tables" in report_data:
                for table_idx, table in enumerate(report_data["tables"]):
                    # 将表格转换为文本
                    if "data" in table and table["data"]:
                        table_text = self._table_to_text(table["data"])
                        chunks.append(table_text)
                        chunk_metadata.append(
                            {
                                "type": "table",
                                "table_id": table.get("table_id", f"table_{table_idx}"),
                                "page_number": table.get("page_number"),
                                "word_count": len(table_text.split()),
                            }
                        )

            if not chunks:
                error_msg = "报告中没有找到有效的文本内容"
                logger.warning(f"向量化跳过: {error_msg}")
                return False, error_msg

            # 获取嵌入向量
            embeddings = self.get_embeddings(chunks, model)

            # 创建向量索引
            vector_index = self.create_vector_index(embeddings)

            # 生成文件ID
            file_id = self._generate_file_id(report_data)

            # 保存结果
            output_dir.mkdir(parents=True, exist_ok=True)

            # 保存FAISS索引 - 彻底使用MD5文件名避免中文路径问题
            import hashlib

            # 使用MD5 hash生成纯英文安全文件名
            safe_filename = hashlib.md5(file_id.encode()).hexdigest()

            # 确保目标目录存在
            output_dir.mkdir(parents=True, exist_ok=True)

            # 直接使用MD5文件名保存（无需临时目录）
            faiss_file = output_dir / f"{safe_filename}_vector.faiss"

            try:
                logger.debug(f"保存FAISS索引到: {faiss_file}")
                logger.debug(f"原始file_id: {file_id}, MD5: {safe_filename}")

                # 直接写入FAISS文件（文件名已是纯英文）
                faiss.write_index(vector_index, str(faiss_file))
                logger.info(f"✅ FAISS索引保存成功: {faiss_file.name}")

            except Exception as faiss_error:
                logger.error(f"FAISS文件保存失败: {faiss_error}")
                raise faiss_error

            # 保存块信息和元数据（也使用MD5文件名保持一致）
            metadata_file = output_dir / f"{safe_filename}_chunks.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "file_id": file_id,
                        "chunks": chunks,
                        "chunk_metadata": chunk_metadata,
                        "vector_info": {
                            "dimension": vector_index.d,
                            "total_vectors": vector_index.ntotal,
                            "index_type": "FlatIP",
                        },
                        "processing_info": {
                            "model": model or self.settings.dashscope.embedding_model,
                            "created_at": datetime.now().isoformat(),
                            "batch_size": self.batch_size,
                        },
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            logger.info(f"向量化完成: {faiss_file}")
            return True, str(faiss_file)

        except Exception as e:
            error_msg = f"向量化处理失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def batch_process_reports(
        self, reports_dir: Path, output_dir: Path, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量处理报告，生成向量数据库

        Args:
            reports_dir: 报告文件目录
            output_dir: 输出目录
            model: 嵌入模型名称

        Returns:
            处理结果统计
        """
        report_files = list(reports_dir.glob("*_parsed.json"))

        logger.info(f"开始批量向量化，共 {len(report_files)} 个文件")

        results = {
            "total_files": len(report_files),
            "successful": 0,
            "failed": 0,
            "results": [],
        }

        for idx, report_file in enumerate(tqdm(report_files, desc="向量化处理"), 1):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report_data = json.load(f)

                logger.info(f"处理文件 {idx}/{len(report_files)}: {report_file.name}")

                success, result = self.process_single_report(
                    report_data, output_dir, model
                )

                if success:
                    results["successful"] += 1
                    logger.info(f"✅ 文件 {idx} 向量化成功")
                else:
                    results["failed"] += 1
                    logger.warning(f"❌ 文件 {idx} 向量化失败: {result}")

                results["results"].append(
                    {
                        "file_path": str(report_file),
                        "success": success,
                        "result": result,
                    }
                )

                # 文件间延迟，避免API调用过于密集
                if idx < len(report_files):
                    file_delay = min(2.0 + (idx * 0.5), 10.0)  # 文件间延迟逐渐增加
                    logger.debug(f"文件间延迟: {file_delay:.2f}秒")
                    time.sleep(file_delay)

            except Exception as e:
                results["failed"] += 1
                results["results"].append(
                    {"file_path": str(report_file), "success": False, "result": str(e)}
                )
                logger.error(f"处理文件失败: {report_file}, 错误: {str(e)}")

                # 出错时也要延迟，避免连续失败
                time.sleep(2.0)

        logger.info(
            f"向量化批量处理完成: 成功 {results['successful']}, 失败 {results['failed']}"
        )
        return results

    def _table_to_text(self, table_data: List[List[Any]]) -> str:
        """将表格数据转换为文本"""
        if not table_data:
            return ""

        text_rows = []
        for row in table_data:
            # 将每行转换为字符串并连接
            row_text = " | ".join([str(cell) for cell in row if cell is not None])
            text_rows.append(row_text)

        return "\n".join(text_rows)

    def _generate_file_id(self, report_data: Dict[str, Any]) -> str:
        """生成文件ID"""
        # 使用处理信息中的file_id，或从文件信息生成
        if (
            "processing_info" in report_data
            and "file_id" in report_data["processing_info"]
        ):
            return report_data["processing_info"]["file_id"]

        # 从文档信息生成ID
        doc_info = report_data.get("document_info", {})
        file_name = doc_info.get("file_name", "unknown")
        file_size = doc_info.get("file_size", 0)

        # 生成唯一ID
        content = f"{file_name}_{file_size}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return hashlib.md5(content.encode()).hexdigest()


class IngestionPipeline:
    """数据摄取流水线，整合BM25和向量数据库构建"""

    def __init__(self, api_provider: str = "dashscope", tenant_id: str = "default"):
        """初始化数据摄取流水线

        Args:
            api_provider: API提供商名称
            tenant_id: 租户ID（用于数据隔离）
        """
        self.settings = get_settings()
        self.tenant_id = tenant_id  # 新增：存储租户ID
        self.bm25_ingestor = BM25Ingestor()
        self.vector_ingestor = VectorDBIngestor(api_provider)

        logger.info(f"数据摄取流水线初始化完成 (租户: {tenant_id})")

    def process_reports(
        self,
        reports_dir: Path,
        output_dir: Optional[Path] = None,
        model: Optional[str] = None,
        include_bm25: bool = True,
        include_vector: bool = True,
    ) -> Dict[str, Any]:
        """完整的报告处理流程

        Args:
            reports_dir: 解析后的报告目录
            output_dir: 输出目录，默认为数据库目录
            model: 嵌入模型名称
            include_bm25: 是否构建BM25索引
            include_vector: 是否构建向量数据库

        Returns:
            处理结果统计
        """
        if output_dir is None:
            output_dir = self.settings.db_dir

        output_dir = Path(output_dir)

        logger.info(f"开始完整数据摄取流程")
        logger.info(f"输入目录: {reports_dir}")
        logger.info(f"输出目录: {output_dir}")
        logger.info(f"BM25索引: {include_bm25}, 向量数据库: {include_vector}")

        results = {
            "input_dir": str(reports_dir),
            "output_dir": str(output_dir),
            "bm25_results": None,
            "vector_results": None,
            "total_time": 0,
            "success": True,
        }

        start_time = time.time()

        try:
            # BM25索引构建
            if include_bm25:
                logger.info("开始BM25索引构建...")
                bm25_output = output_dir / "bm25"
                bm25_results = self.bm25_ingestor.batch_process_reports(
                    reports_dir, bm25_output
                )
                results["bm25_results"] = bm25_results
                logger.info(
                    f"BM25索引构建完成: {bm25_results['successful']}/{bm25_results['total_files']}"
                )

            # 向量数据库构建
            if include_vector:
                logger.info("开始向量数据库构建...")
                vector_output = output_dir / "vector_dbs"
                vector_results = self.vector_ingestor.batch_process_reports(
                    reports_dir, vector_output, model
                )
                results["vector_results"] = vector_results
                logger.info(
                    f"向量数据库构建完成: {vector_results['successful']}/{vector_results['total_files']}"
                )

            # 计算总时间
            end_time = time.time()
            results["total_time"] = end_time - start_time

            # 判断整体成功状态
            bm25_success = not include_bm25 or (
                results["bm25_results"] and results["bm25_results"]["failed"] == 0
            )
            vector_success = not include_vector or (
                results["vector_results"] and results["vector_results"]["failed"] == 0
            )

            results["success"] = bm25_success and vector_success

            logger.info(f"数据摄取流水线完成，总耗时: {results['total_time']:.2f}秒")

            return results

        except Exception as e:
            logger.error(f"数据摄取流水线失败: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
            results["total_time"] = time.time() - start_time
            return results


# 便捷函数
def create_bm25_index(chunks: List[str]) -> BM25Okapi:
    """创建BM25索引的便捷函数"""
    ingestor = BM25Ingestor()
    return ingestor.create_bm25_index(chunks)


def get_embeddings(
    texts: List[str], api_provider: str = "dashscope"
) -> List[List[float]]:
    """获取嵌入向量的便捷函数"""
    ingestor = VectorDBIngestor(api_provider)
    return ingestor.get_embeddings(texts)


def process_reports_pipeline(
    reports_dir: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """完整报告处理流程的便捷函数"""
    pipeline = IngestionPipeline()
    return pipeline.process_reports(
        Path(reports_dir), Path(output_dir) if output_dir else None, **kwargs
    )
