"""
基于MinerU的PDF解析模块
替换原项目的Docling解析，提供更好的中文支持
支持命令行并行解析优化
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import tempfile
from datetime import datetime
import time
import os

import subprocess
import shutil

# 检查 mineru 命令行工具是否可用
MINERU_CLI_AVAILABLE = shutil.which("mineru") is not None

import fitz  # PyMuPDF
import pdfplumber

from config import get_settings

logger = logging.getLogger(__name__)


class MinerUPDFParser:
    """基于MinerU的PDF解析器，支持命令行并行解析优化"""

    def __init__(self, scenario_id: str = "investment", progress_callback=None):
        self.settings = get_settings()
        self.scenario_id = scenario_id
        self.progress_callback = progress_callback  # 进度回调函数

    def parse_pdf_with_mineru(self, pdf_path: str) -> Dict[str, Any]:
        """智能解析PDF文档（优先使用 PyMuPDF + pdfplumber，需要时才用 MinerU OCR）

        Args:
            pdf_path: PDF文件路径

        Returns:
            解析结果字典
        """
        # 获取页数
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()

        logger.info(f"📄 PDF 文件: {Path(pdf_path).name}，总页数: {total_pages}")

        # 报告进度：开始解析
        if self.progress_callback:
            self.progress_callback(
                stage='parsing',
                progress=5,
                message=f'开始解析 PDF（共 {total_pages} 页）',
                total_pages=total_pages,
                current_page=0
            )

        # 🔍 步骤1: 先用 PyMuPDF + pdfplumber 尝试解析
        logger.info("🚀 使用 PyMuPDF + pdfplumber 解析...")
        result = self._hybrid_parse(pdf_path, total_pages)

        # 🔍 步骤2: 检测是否需要 OCR
        needs_ocr = self._check_needs_ocr(result, pdf_path)

        if needs_ocr and MINERU_CLI_AVAILABLE:
            logger.warning(f"⚠️ 检测到扫描件或文本提取不足，使用 MinerU OCR 重新解析")

            # 报告进度：切换到 OCR
            if self.progress_callback:
                self.progress_callback(
                    stage='parsing',
                    progress=10,
                    message=f'检测到扫描件，使用 OCR 解析...',
                    total_pages=total_pages,
                    current_page=0
                )

            # 使用 MinerU OCR
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"🔥 MinerU OCR 使用设备: {device}")
            result = self._parse_with_ocr(pdf_path, device, total_pages)
        else:
            logger.info(f"✅ 使用混合方案成功解析（无需 OCR）")

        # 报告进度：解析完成
        if self.progress_callback:
            self.progress_callback(
                stage='parsing',
                progress=30,
                message=f'PDF 解析完成（共 {total_pages} 页）',
                total_pages=total_pages,
                current_page=total_pages
            )

        return result

    def _hybrid_parse(self, pdf_path: str, total_pages: int) -> Dict[str, Any]:
        """混合解析方法：PyMuPDF 提取文本 + pdfplumber 提取表格

        Args:
            pdf_path: PDF文件路径
            total_pages: 总页数

        Returns:
            解析结果字典
        """
        logger.info(f"使用混合方案解析PDF: {pdf_path}")

        # 获取基本文档信息
        doc_info = self._extract_document_info(pdf_path)

        pages_content = []
        tables = []

        try:
            # 1️⃣ PyMuPDF 提取文本（快速）
            logger.info(f"📝 使用 PyMuPDF 提取文本（共 {total_pages} 页）...")
            start_text_time = time.time()

            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()

                    # 报告进度
                    if self.progress_callback and page_num % 10 == 0:
                        progress = 5 + int((page_num / total_pages) * 15)  # 5% -> 20%
                        self.progress_callback(
                            stage='parsing',
                            progress=progress,
                            message=f'提取文本中...',
                            total_pages=total_pages,
                            current_page=page_num
                        )

                    page_content = {
                        "page_number": page_num + 1,
                        "text": text,
                        "tables": [],
                        "images": [],
                        "layout": {},
                        "metadata": {},
                    }
                    pages_content.append(page_content)

            text_elapsed = time.time() - start_text_time
            logger.info(f"✅ 文本提取完成，耗时 {text_elapsed:.2f} 秒")

            # 2️⃣ pdfplumber 提取表格（精确）
            logger.info(f"📊 使用 pdfplumber 提取表格（共 {total_pages} 页）...")
            start_table_time = time.time()

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 报告进度
                    if self.progress_callback and page_num % 10 == 0:
                        progress = 20 + int((page_num / total_pages) * 8)  # 20% -> 28%
                        self.progress_callback(
                            stage='parsing',
                            progress=progress,
                            message=f'提取表格中...',
                            total_pages=total_pages,
                            current_page=page_num
                        )

                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_idx, table in enumerate(page_tables):
                            table_data = {
                                "table_id": f"table_{page_num}_{table_idx}",
                                "page_number": page_num + 1,
                                "data": table,
                                "bbox": None,
                                "metadata": {},
                            }
                            tables.append(table_data)
                            pages_content[page_num]["tables"].append(table_data)

            table_elapsed = time.time() - start_table_time
            logger.info(f"✅ 表格提取完成，耗时 {table_elapsed:.2f} 秒，共提取 {len(tables)} 个表格")

        except Exception as e:
            logger.error(f"混合解析失败: {pdf_path}, 错误: {str(e)}")
            # 返回最小可用结果
            pages_content = [
                {
                    "page_number": 1,
                    "text": "",
                    "tables": [],
                    "images": [],
                    "layout": {},
                    "metadata": {"error": str(e)},
                }
            ]

        # 构建结果
        all_text = "\n".join([page["text"] for page in pages_content])

        parsed_result = {
            "document_info": doc_info,
            "pages": pages_content,
            "tables": tables,
            "images": [],
            "text_content": all_text,
            "metadata": {
                "parser": "Hybrid (PyMuPDF + pdfplumber)",
                "parser_version": "latest",
                "parse_time": datetime.now().isoformat(),
                "total_pages": len(pages_content),
                "has_tables": len(tables) > 0,
                "has_images": False,
            },
        }

        # 输出解析统计
        logger.info(f"📊 混合解析统计:")
        logger.info(f"   - 总页数: {len(pages_content)}")
        logger.info(f"   - 总字符数: {len(all_text)}")
        logger.info(f"   - 表格数: {len(tables)}")
        logger.info(f"   - 平均每页字符数: {len(all_text) / len(pages_content):.0f}")

        return parsed_result

    def _check_needs_ocr(self, parsed_result: Dict[str, Any], pdf_path: str) -> bool:
        """检测PDF是否需要OCR

        判断标准：
        1. 文本提取量过少（可能是扫描件）
        2. 文本密度过低

        Args:
            parsed_result: 解析结果
            pdf_path: PDF文件路径

        Returns:
            是否需要OCR
        """
        text_content = parsed_result.get("text_content", "")
        total_pages = parsed_result["metadata"]["total_pages"]

        # 计算文本量
        text_length = len(text_content.strip())
        avg_text_per_page = text_length / total_pages if total_pages > 0 else 0

        logger.info(f"📊 文本统计: 总字符数={text_length}, 平均每页={avg_text_per_page:.0f}字符")

        # 判断标准：平均每页少于100个字符，可能是扫描件
        if avg_text_per_page < 100:
            logger.warning(f"⚠️ 文本密度过低（{avg_text_per_page:.0f}字符/页），判定为扫描件")
            return True

        # 检查是否有大量乱码或特殊字符
        import re
        # 统计中文、英文、数字的比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text_content))
        english_chars = len(re.findall(r'[a-zA-Z]', text_content))
        digits = len(re.findall(r'\d', text_content))
        valid_chars = chinese_chars + english_chars + digits

        valid_ratio = valid_chars / text_length if text_length > 0 else 0

        logger.info(f"📊 有效字符比例: {valid_ratio:.2%} (中文={chinese_chars}, 英文={english_chars}, 数字={digits})")

        # 如果有效字符比例低于30%，可能需要OCR
        if valid_ratio < 0.3 and text_length > 100:
            logger.warning(f"⚠️ 有效字符比例过低（{valid_ratio:.2%}），可能需要OCR")
            return True

        logger.info(f"✅ 文本提取正常，无需OCR")
        return False

    def _parse_with_ocr(self, pdf_path: str, device: str, total_pages: int) -> Dict[str, Any]:
        """使用 MinerU OCR 解析（扫描件）"""
        temp_dir = tempfile.mkdtemp(prefix="mineru_ocr_")

        try:
            start_time = time.time()

            cmd = [
                "mineru",
                "-p", pdf_path,
                "-o", temp_dir,
                "-m", "ocr",    # 使用 OCR 模式
                "-b", "pipeline",
                "-d", device,
                "-f", "false",  # 关闭公式识别
                "-t", "true",   # 保留表格识别
            ]

            logger.info(f"执行 OCR 命令: {' '.join(cmd)}")

            # 使用 Popen 以便实时更新进度
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 模拟进度更新
            import threading
            progress_stop = threading.Event()

            def update_progress_periodically():
                """定期更新进度（OCR 较慢）"""
                current_progress = 12
                while not progress_stop.is_set() and current_progress < 28:
                    time.sleep(3)  # OCR 较慢，每3秒更新一次
                    if not progress_stop.is_set():
                        current_progress += 2
                        if self.progress_callback and total_pages > 0:
                            estimated_page = int((current_progress - 10) / 20 * total_pages)
                            self.progress_callback(
                                stage='parsing',
                                progress=current_progress,
                                message=f'OCR 识别中...',
                                total_pages=total_pages,
                                current_page=estimated_page
                            )

            # 启动进度更新线程
            if self.progress_callback and total_pages > 0:
                progress_thread = threading.Thread(target=update_progress_periodically, daemon=True)
                progress_thread.start()

            # 等待进程完成
            try:
                stdout, stderr = process.communicate(timeout=1200)  # OCR 超时时间更长：20分钟
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                progress_stop.set()
                logger.error(f"❌ MinerU OCR 超时（>1200秒）")
                # OCR 失败，返回之前的混合解析结果
                return self._hybrid_parse(pdf_path, total_pages)
            finally:
                progress_stop.set()

            if returncode != 0:
                logger.error(f"❌ MinerU OCR 失败: {stderr[:500]}")
                # OCR 失败，返回之前的混合解析结果
                return self._hybrid_parse(pdf_path, total_pages)

            parsed_content = self._read_mineru_output(temp_dir, pdf_path)

            # 更新 metadata 标记为 OCR
            parsed_content["metadata"]["parser"] = "MinerU OCR"
            parsed_content["metadata"]["ocr_used"] = True

            elapsed = time.time() - start_time
            logger.info(f"✅ OCR 解析完成，耗时 {elapsed:.2f} 秒")

            return parsed_content

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _parse_serial(self, pdf_path: str, device: str, total_pages: int = 0) -> Dict[str, Any]:
        """串行解析（小文件或 GPU 模式）"""
        temp_dir = tempfile.mkdtemp(prefix="mineru_serial_")

        try:
            start_time = time.time()

            cmd = [
                "mineru",
                "-p", pdf_path,
                "-o", temp_dir,
                "-m", "txt",    # 使用文本模式（不使用 OCR）→ 速度提升 10 倍
                "-b", "pipeline",
                "-d", device,
                "-f", "false",  # 关闭公式识别
                "-t", "true",   # 保留表格识别
            ]

            logger.info(f"执行命令: {' '.join(cmd)}")

            # 使用 Popen 以便实时更新进度
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 模拟进度更新（因为 MinerU 没有实时进度输出）
            import threading
            progress_stop = threading.Event()

            def update_progress_periodically():
                """定期更新进度（模拟）"""
                current_progress = 10
                while not progress_stop.is_set() and current_progress < 28:
                    time.sleep(2)  # 每2秒更新一次
                    if not progress_stop.is_set():
                        current_progress += 2
                        if self.progress_callback and total_pages > 0:
                            # 估算当前页数
                            estimated_page = int((current_progress - 5) / 25 * total_pages)
                            self.progress_callback(
                                stage='parsing',
                                progress=current_progress,
                                message=f'正在解析 PDF...',
                                total_pages=total_pages,
                                current_page=estimated_page
                            )

            # 启动进度更新线程
            if self.progress_callback and total_pages > 0:
                progress_thread = threading.Thread(target=update_progress_periodically, daemon=True)
                progress_thread.start()

            # 等待进程完成
            try:
                stdout, stderr = process.communicate(timeout=600)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                progress_stop.set()
                logger.error(f"❌ MinerU 解析超时（>600秒）")
                return self._fallback_parse(pdf_path)
            finally:
                progress_stop.set()

            if returncode != 0:
                logger.error(f"❌ MinerU 解析失败: {stderr[:500]}")
                return self._fallback_parse(pdf_path)

            parsed_content = self._read_mineru_output(temp_dir, pdf_path)

            elapsed = time.time() - start_time
            logger.info(f"✅ 串行解析完成，耗时 {elapsed:.2f} 秒")

            return parsed_content

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _read_mineru_output(self, output_dir: str, pdf_path: str) -> Dict[str, Any]:
        """读取 MinerU 2.5.4+ 输出的文件并转换为统一格式

        Args:
            output_dir: MinerU 输出目录
            pdf_path: 原始 PDF 文件路径

        Returns:
            标准化的解析结果
        """
        import os
        import glob

        # 获取基本文档信息
        doc_info = self._extract_document_info(pdf_path)

        # mineru 2.5.4 输出结构：
        # output_dir/
        #   {pdf_basename}/        ← PDF文件名（不含扩展名）
        #     auto/                ← 模式目录（auto/txt/ocr）
        #       {pdf_basename}.md  ← Markdown文件
        #       images/            ← 图片目录

        pdf_basename = Path(pdf_path).stem  # 不含扩展名的文件名

        # 按优先级查找输出文件
        search_patterns = [
            # 模式1: {output_dir}/{pdf_basename}/auto/{pdf_basename}.md
            os.path.join(output_dir, pdf_basename, "auto", f"{pdf_basename}.md"),
            # 模式2: {output_dir}/{pdf_basename}/txt/{pdf_basename}.md
            os.path.join(output_dir, pdf_basename, "txt", f"{pdf_basename}.md"),
            # 模式3: {output_dir}/{pdf_basename}/ocr/{pdf_basename}.md
            os.path.join(output_dir, pdf_basename, "ocr", f"{pdf_basename}.md"),
            # 模式4: 递归查找所有 .md 文件
            os.path.join(output_dir, "**", "*.md"),
        ]

        md_files = []
        for pattern in search_patterns:
            if "**" in pattern:
                # 使用 glob 递归查找
                md_files = glob.glob(pattern, recursive=True)
            else:
                # 直接检查文件是否存在
                if os.path.exists(pattern):
                    md_files = [pattern]

            if md_files:
                logger.info(f"找到 Markdown 文件: {md_files[0]}")
                break

        if not md_files:
            # 列出实际生成的文件，帮助调试
            all_files = []
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    all_files.append(os.path.join(root, f))

            logger.error(f"MinerU输出目录结构:")
            for f in all_files[:20]:  # 只显示前20个文件
                logger.error(f"  - {os.path.relpath(f, output_dir)}")

            raise FileNotFoundError(
                f"未找到 MinerU 输出的 Markdown 文件。"
                f"输出目录: {output_dir}，"
                f"PDF basename: {pdf_basename}，"
                f"实际文件数: {len(all_files)}"
            )

        # 读取 Markdown 内容
        md_content = ""
        for md_file in md_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content += f.read() + "\n\n"

        # 简化处理：将 Markdown 按段落分页
        pages_content = []
        paragraphs = md_content.split('\n\n')

        for idx, para in enumerate(paragraphs):
            if para.strip():
                pages_content.append({
                    "page_number": idx + 1,
                    "text": para.strip(),
                    "tables": [],
                    "images": [],
                    "layout": [],
                    "metadata": {},
                })

        # 构建标准化输出
        parsed_result = {
            "document_info": doc_info,
            "pages": pages_content,
            "tables": [],
            "images": [],
            "text_content": md_content,
            "metadata": {
                "parser": "MinerU-CLI",
                "parser_version": "1.3.12",
                "parse_time": datetime.now().isoformat(),
                "total_pages": len(pages_content),
                "has_tables": False,
                "has_images": False,
                "language": "zh",
            },
        }

        return parsed_result

    def _fallback_parse(self, pdf_path: str) -> Dict[str, Any]:
        """备用PDF解析方法（使用PyMuPDF + pdfplumber）

        Args:
            pdf_path: PDF文件路径

        Returns:
            解析结果字典
        """
        logger.info(f"使用备用方法解析PDF: {pdf_path}")

        # 获取基本文档信息
        doc_info = self._extract_document_info(pdf_path)

        # 使用PyMuPDF提取文本
        pages_content = []
        tables = []

        try:
            # PyMuPDF解析文本
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()

                    page_content = {
                        "page_number": page_num + 1,
                        "text": text,
                        "tables": [],
                        "images": [],
                        "layout": {},
                        "metadata": {},
                    }
                    pages_content.append(page_content)

            # 使用pdfplumber提取表格
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_idx, table in enumerate(page_tables):
                            table_data = {
                                "table_id": f"table_{page_num}_{table_idx}",
                                "page_number": page_num + 1,
                                "data": table,
                                "bbox": None,  # pdfplumber不直接提供bbox
                                "metadata": {},
                            }
                            tables.append(table_data)
                            pages_content[page_num]["tables"].append(table_data)

        except Exception as e:
            logger.error(f"备用解析也失败: {pdf_path}, 错误: {str(e)}")
            # 返回最小可用结果
            pages_content = [
                {
                    "page_number": 1,
                    "text": "",
                    "tables": [],
                    "images": [],
                    "layout": {},
                    "metadata": {"error": str(e)},
                }
            ]

        # 构建结果
        all_text = "\n".join([page["text"] for page in pages_content])

        parsed_result = {
            "document_info": doc_info,
            "pages": pages_content,
            "tables": tables,
            "images": [],
            "text_content": all_text,
            "metadata": {
                "parser": "Fallback (PyMuPDF + pdfplumber)",
                "parser_version": "latest",
                "parse_time": datetime.now().isoformat(),
                "total_pages": len(pages_content),
                "has_tables": len(tables) > 0,
                "has_images": False,
                "language": "zh",
            },
        }

        return parsed_result

    def _extract_document_info(self, pdf_path: str) -> Dict[str, Any]:
        """提取PDF文档基本信息

        Args:
            pdf_path: PDF文件路径

        Returns:
            文档信息字典
        """
        file_path = Path(pdf_path)
        doc_info = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "creation_time": datetime.fromtimestamp(
                file_path.stat().st_ctime
            ).isoformat(),
            "modification_time": datetime.fromtimestamp(
                file_path.stat().st_mtime
            ).isoformat(),
        }

        # 尝试获取PDF元数据
        try:
            with fitz.open(pdf_path) as doc:
                metadata = doc.metadata
                doc_info.update(
                    {
                        "title": metadata.get("title", ""),
                        "author": metadata.get("author", ""),
                        "subject": metadata.get("subject", ""),
                        "creator": metadata.get("creator", ""),
                        "producer": metadata.get("producer", ""),
                        "creation_date": metadata.get("creationDate", ""),
                        "modification_date": metadata.get("modDate", ""),
                        "total_pages": doc.page_count,
                    }
                )
        except Exception as e:
            logger.warning(f"无法获取PDF元数据: {pdf_path}, 错误: {str(e)}")
            doc_info["total_pages"] = 0

        return doc_info


class PDFParsingPipeline:
    """PDF解析流水线"""

    def __init__(self, scenario_id: str = "investment", progress_callback=None):
        self.parser = MinerUPDFParser(scenario_id=scenario_id, progress_callback=progress_callback)
        self.settings = get_settings()
        self.scenario_id = scenario_id

    def parse_pdf_file(
        self, pdf_path: str, output_dir: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """解析单个PDF文件

        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录，默认为debug_data/parsed_reports

        Returns:
            (是否成功, 解析结果或错误信息)
        """
        try:
            # 设置输出目录
            if output_dir is None:
                output_dir = self.settings.debug_dir / "parsed_reports"
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件ID
            file_id = self._generate_file_id(pdf_path)

            # 执行解析
            logger.info(f"开始解析PDF文件: {pdf_path}")
            parsed_result = self.parser.parse_pdf_with_mineru(pdf_path)

            # 添加处理信息
            parsed_result["processing_info"] = {
                "file_id": file_id,
                "input_path": pdf_path,
                "processed_at": datetime.now().isoformat(),
                "processor": "MinerUPDFParser",
                "scenario_id": self.scenario_id,
            }

            # 根据场景进行特定处理
            if self.scenario_id == "tender":
                parsed_result = self._extract_tender_metadata(parsed_result)
            elif self.scenario_id == "investment":
                parsed_result = self._extract_investment_metadata(parsed_result)

            # 保存解析结果
            output_file = output_dir / f"{file_id}_parsed.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(parsed_result, f, ensure_ascii=False, indent=2)

            logger.info(f"PDF解析完成: {pdf_path} -> {output_file}")

            return True, {
                "file_id": file_id,
                "output_path": str(output_file),
                "parsed_result": parsed_result,
            }

        except Exception as e:
            error_msg = f"PDF解析失败: {pdf_path}, 错误: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}

    def batch_parse_pdfs(
        self, pdf_directory: str, output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量解析PDF文件

        Args:
            pdf_directory: PDF文件目录
            output_dir: 输出目录

        Returns:
            批量处理结果
        """
        pdf_dir = Path(pdf_directory)
        pdf_files = list(pdf_dir.glob("*.pdf"))

        logger.info(f"发现 {len(pdf_files)} 个PDF文件待处理")

        results = {
            "total_files": len(pdf_files),
            "successful": 0,
            "failed": 0,
            "results": [],
        }

        for pdf_file in pdf_files:
            success, result = self.parse_pdf_file(str(pdf_file), output_dir)

            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1

            results["results"].append(
                {"file_path": str(pdf_file), "success": success, "result": result}
            )

        logger.info(
            f"批量处理完成: 成功 {results['successful']}, 失败 {results['failed']}"
        )
        return results

    def _generate_file_id(self, pdf_path: str) -> str:
        """生成文件ID

        Args:
            pdf_path: PDF文件路径

        Returns:
            文件ID
        """
        file_path = Path(pdf_path)
        # 使用文件名和时间戳生成唯一ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = file_path.stem
        # 移除特殊字符，保留中文、英文、数字、下划线
        clean_name = "".join(
            c for c in base_name if c.isalnum() or c in ["_", "-", "中"]
        )
        return f"{clean_name}_{timestamp}"

    def _extract_tender_metadata(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取招投标文档的特定元数据"""
        try:
            text_content = parsed_result.get("text_content", "")
            metadata = parsed_result.get("metadata", {})

            # 招投标特定信息提取
            tender_metadata = {
                "document_type": "tender",
                "extracted_info": {}
            }

            # 提取招标编号
            import re
            tender_number_patterns = [
                r'招标编号[：:]\s*([A-Z0-9\-_]+)',
                r'项目编号[：:]\s*([A-Z0-9\-_]+)',
                r'标书编号[：:]\s*([A-Z0-9\-_]+)'
            ]

            for pattern in tender_number_patterns:
                match = re.search(pattern, text_content)
                if match:
                    tender_metadata["extracted_info"]["tender_number"] = match.group(1)
                    break

            # 提取截止时间
            time_patterns = [
                r'投标截止时间[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日.*?\d{1,2}[:：]\d{2})',
                r'开标时间[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日.*?\d{1,2}[:：]\d{2})',
                r'递交投标文件截止时间[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日.*?\d{1,2}[:：]\d{2})'
            ]

            for pattern in time_patterns:
                match = re.search(pattern, text_content)
                if match:
                    tender_metadata["extracted_info"]["deadline"] = match.group(1)
                    break

            # 提取预算信息
            budget_patterns = [
                r'预算金额[：:]\s*([\d,]+\.?\d*)\s*万?元',
                r'投资总额[：:]\s*([\d,]+\.?\d*)\s*万?元',
                r'项目总投资[：:]\s*([\d,]+\.?\d*)\s*万?元'
            ]

            for pattern in budget_patterns:
                match = re.search(pattern, text_content)
                if match:
                    tender_metadata["extracted_info"]["budget"] = match.group(1)
                    break

            # 提取资质要求
            if "资质要求" in text_content or "投标人资格" in text_content:
                tender_metadata["extracted_info"]["has_qualification_requirements"] = True

            # 提取技术要求
            if "技术要求" in text_content or "技术规范" in text_content:
                tender_metadata["extracted_info"]["has_technical_requirements"] = True

            # 合并到原有元数据
            metadata.update(tender_metadata)
            parsed_result["metadata"] = metadata

            logger.info(f"招投标元数据提取完成: {tender_metadata['extracted_info']}")

        except Exception as e:
            logger.error(f"招投标元数据提取失败: {str(e)}")

        return parsed_result

    def _extract_investment_metadata(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取投研文档的特定元数据"""
        try:
            text_content = parsed_result.get("text_content", "")
            metadata = parsed_result.get("metadata", {})

            # 投研特定信息提取
            investment_metadata = {
                "document_type": "investment",
                "extracted_info": {}
            }

            # 提取公司信息
            import re
            company_patterns = [
                r'([^，。\s]+)(?:股份有限公司|有限公司|集团|科技|电子|新能源)',
                r'公司名称[：:]\s*([^，。\n]+)',
                r'标的公司[：:]\s*([^，。\n]+)'
            ]

            for pattern in company_patterns:
                matches = re.findall(pattern, text_content)
                if matches:
                    investment_metadata["extracted_info"]["companies"] = list(set(matches))
                    break

            # 提取投资评级
            rating_patterns = [
                r'投资评级[：:]\s*(买入|增持|持有|减持|卖出)',
                r'评级[：:]\s*(买入|增持|持有|减持|卖出)',
                r'建议[：:]\s*(买入|增持|持有|减持|卖出)'
            ]

            for pattern in rating_patterns:
                match = re.search(pattern, text_content)
                if match:
                    investment_metadata["extracted_info"]["rating"] = match.group(1)
                    break

            # 提取目标价格
            price_patterns = [
                r'目标价[：:]\s*([\d.]+)\s*元',
                r'目标价格[：:]\s*([\d.]+)\s*元',
                r'合理价值[：:]\s*([\d.]+)\s*元'
            ]

            for pattern in price_patterns:
                match = re.search(pattern, text_content)
                if match:
                    investment_metadata["extracted_info"]["target_price"] = float(match.group(1))
                    break

            # 提取报告类型
            if "深度研究" in text_content:
                investment_metadata["extracted_info"]["report_type"] = "深度研究"
            elif "季报" in text_content:
                investment_metadata["extracted_info"]["report_type"] = "季报点评"
            elif "年报" in text_content:
                investment_metadata["extracted_info"]["report_type"] = "年报点评"

            # 合并到原有元数据
            metadata.update(investment_metadata)
            parsed_result["metadata"] = metadata

            logger.info(f"投研元数据提取完成: {investment_metadata['extracted_info']}")

        except Exception as e:
            logger.error(f"投研元数据提取失败: {str(e)}")

        return parsed_result


# 便捷函数
def parse_single_pdf(pdf_path: str, output_dir: Optional[str] = None, scenario_id: str = "investment") -> Dict[str, Any]:
    """解析单个PDF文件的便捷函数

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
        scenario_id: 场景ID，默认为投研场景

    Returns:
        解析结果
    """
    pipeline = PDFParsingPipeline(scenario_id=scenario_id)
    success, result = pipeline.parse_pdf_file(pdf_path, output_dir)

    if success:
        return result
    else:
        raise Exception(result.get("error", "PDF解析失败"))


def batch_parse_pdfs(
    pdf_directory: str, output_dir: Optional[str] = None, scenario_id: str = "investment"
) -> Dict[str, Any]:
    """批量解析PDF文件的便捷函数

    Args:
        pdf_directory: PDF文件目录
        output_dir: 输出目录
        scenario_id: 场景ID，默认为投研场景

    Returns:
        批量处理结果
    """
    pipeline = PDFParsingPipeline(scenario_id=scenario_id)
    return pipeline.batch_parse_pdfs(pdf_directory, output_dir)
