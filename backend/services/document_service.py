"""
多场景文档处理服务
根据不同场景处理和解析文档
"""

import sys
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..database import get_db_session
from ..models import Document, DocumentChunk
from .scenario_service import get_scenario_service


class BaseDocumentProcessor(ABC):
    """文档处理器基类"""

    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.scenario_service = get_scenario_service()
        self.db = get_db_session

    @abstractmethod
    def extract_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """提取场景特定的元数据"""
        pass

    @abstractmethod
    def validate_document(self, file_path: str, file_size: int) -> bool:
        """验证文档是否符合场景要求"""
        pass

    def process_document(self, file_path: str, title: str, file_size: int,
                        additional_metadata: Dict[str, Any] = None) -> Optional[str]:
        """处理文档并保存到数据库"""
        try:
            # 验证文档
            if not self.validate_document(file_path, file_size):
                # 文档验证失败
                return None

            # 生成文档ID
            doc_id = str(uuid.uuid4())

            # 读取文档内容（这里简化处理，实际应该使用PDF解析器）
            content = self._read_document_content(file_path)

            # 提取元数据
            metadata = self.extract_metadata(content, Path(file_path).name)

            # 合并额外的元数据
            if additional_metadata:
                metadata.update(additional_metadata)

            # 保存到数据库
            with self.db() as db:
                document = Document(
                    id=doc_id,
                    scenario_id=self.scenario_id,
                    title=title,
                    file_path=file_path,
                    file_size=file_size,
                    doc_metadata=metadata,
                    status="pending"  # 等待进一步处理
                )

                db.add(document)
                db.commit()
                db.refresh(document)

                # 文档保存成功
                return doc_id

        except Exception as e:
            # 处理文档失败
            return None

    def _read_document_content(self, file_path: str) -> str:
        """读取文档内容（简化版本）"""
        try:
            # 这里应该使用实际的PDF解析器
            # 暂时返回文件名作为内容
            return f"文档内容: {Path(file_path).name}"
        except Exception as e:
            # 读取文档内容失败
            return ""


class InvestmentDocumentProcessor(BaseDocumentProcessor):
    """投研文档处理器"""

    def extract_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """提取投研特定的元数据"""
        metadata = {
            "original_filename": filename,
            "document_type": "investment_research",
            "processed_at": datetime.now().isoformat(),
        }

        # 这里应该实现实际的信息提取逻辑
        # 暂时使用模拟数据
        if "中芯国际" in filename or "中芯国际" in content:
            metadata.update({
                "company_name": "中芯国际",
                "company_code": "688981",
                "industry": "半导体",
                "sector": "科技股"
            })
        elif "比亚迪" in filename or "比亚迪" in content:
            metadata.update({
                "company_name": "比亚迪",
                "company_code": "002594",
                "industry": "新能源汽车",
                "sector": "汽车"
            })
        elif "宁德时代" in filename or "宁德时代" in content:
            metadata.update({
                "company_name": "宁德时代",
                "company_code": "300750",
                "industry": "电池",
                "sector": "新能源"
            })

        # 尝试提取报告类型
        if "深度研究" in filename or "深度研究" in content:
            metadata["report_type"] = "深度研究"
        elif "季报" in filename or "季报" in content:
            metadata["report_type"] = "季报点评"
        elif "年报" in filename or "年报" in content:
            metadata["report_type"] = "年报点评"
        else:
            metadata["report_type"] = "投资研究"

        return metadata

    def validate_document(self, file_path: str, file_size: int) -> bool:
        """验证投研文档"""
        # 检查文件大小
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            print(f"❌ 文件过大: {file_size} > {max_size}")
            return False

        # 检查文件格式
        file_ext = Path(file_path).suffix.lower()
        allowed_extensions = [".pdf", ".docx"]
        if file_ext not in allowed_extensions:
            print(f"❌ 不支持的文件格式: {file_ext}")
            return False

        return True


class TenderDocumentProcessor(BaseDocumentProcessor):
    """招投标文档处理器"""

    def extract_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """提取招投标特定的元数据"""
        metadata = {
            "original_filename": filename,
            "document_type": "tender_document",
            "processed_at": datetime.now().isoformat(),
        }

        # 这里应该实现实际的信息提取逻辑
        # 暂时使用模拟数据
        if "招标" in filename or "招标" in content:
            metadata.update({
                "tender_type": "public_tender",
                "industry": "建筑工程"
            })

            # 尝试提取招标编号
            if "ZB" in filename:
                metadata["tender_number"] = "ZB2024001"

        # 尝试提取其他信息
        if "技术要求" in content:
            metadata["has_technical_requirements"] = True
        if "资质" in content:
            metadata["has_qualification_requirements"] = True

        return metadata

    def validate_document(self, file_path: str, file_size: int) -> bool:
        """验证招投标文档"""
        # 检查文件大小
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            print(f"❌ 文件过大: {file_size} > {max_size}")
            return False

        # 检查文件格式
        file_ext = Path(file_path).suffix.lower()
        allowed_extensions = [".pdf", ".doc", ".docx"]
        if file_ext not in allowed_extensions:
            print(f"❌ 不支持的文件格式: {file_ext}")
            return False

        return True


class DocumentService:
    """文档处理服务"""

    def __init__(self):
        self.processors = {
            'investment': InvestmentDocumentProcessor,
            'tender': TenderDocumentProcessor
        }
        self.scenario_service = get_scenario_service()
        self.db = get_db_session

    def process_document(self, scenario_id: str, file_path: str, title: str,
                        file_size: int, additional_metadata: Dict[str, Any] = None) -> Optional[str]:
        """根据场景处理文档"""
        try:
            # 验证场景
            if not self.scenario_service.validate_scenario(scenario_id):
                print(f"❌ 无效场景: {scenario_id}")
                return None

            # 获取处理器
            processor_class = self.processors.get(scenario_id)
            if not processor_class:
                print(f"❌ 未找到场景处理器: {scenario_id}")
                return None

            # 创建处理器实例并处理文档
            processor = processor_class(scenario_id)
            return processor.process_document(file_path, title, file_size, additional_metadata)

        except Exception as e:
            # 文档处理服务失败
            return None

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档信息"""
        try:
            with self.db() as db:
                document = db.query(Document).filter(Document.id == document_id).first()

                if not document:
                    return None

                return {
                    "id": document.id,
                    "scenario_id": document.scenario_id,
                    "title": document.title,
                    "file_path": document.file_path,
                    "file_size": document.file_size,
                    "pages": document.pages,
                    "language": document.language,
                    "metadata": document.doc_metadata,
                    "status": document.status,
                    "quality_score": float(document.quality_score) if document.quality_score else None,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat()
                }

        except Exception as e:
            # 获取文档失败
            return None

    def get_documents_by_scenario(self, scenario_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取场景下的文档列表"""
        try:
            with self.db() as db:
                documents = db.query(Document).filter(
                    Document.scenario_id == scenario_id
                ).order_by(Document.created_at.desc()).limit(limit).all()

                result = []
                for doc in documents:
                    result.append({
                        "id": doc.id,
                        "title": doc.title,
                        "file_size": doc.file_size,
                        "status": doc.status,
                        "metadata": doc.doc_metadata,
                        "created_at": doc.created_at.isoformat()
                    })

                return result

        except Exception as e:
            # 获取场景文档列表失败
            return []

    def update_document_status(self, document_id: str, status: str,
                             quality_score: float = None) -> bool:
        """更新文档状态"""
        try:
            with self.db() as db:
                document = db.query(Document).filter(Document.id == document_id).first()

                if not document:
                    return False

                document.status = status
                if quality_score is not None:
                    document.quality_score = quality_score

                if status == "completed":
                    document.processed_at = datetime.now()

                document.updated_at = datetime.now()

                db.commit()
                return True

        except Exception as e:
            # 更新文档状态失败
            return False

    def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            with self.db() as db:
                document = db.query(Document).filter(Document.id == document_id).first()

                if not document:
                    return False

                # 删除相关的文档块
                db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

                # 删除文档
                db.delete(document)
                db.commit()

                return True

        except Exception as e:
            # 删除文档失败
            return False


# 全局服务实例
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """获取文档服务实例"""
    global _document_service

    if _document_service is None:
        _document_service = DocumentService()

    return _document_service

