"""
文件处理进度管理器
用于跟踪和存储文档处理进度
"""

from typing import Dict, Optional
from datetime import datetime
import threading


class ProgressManager:
    """进度管理器（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._progress_store = {}
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_progress_store'):
            self._progress_store: Dict[str, Dict] = {}

    def update_progress(
        self,
        document_id: str,
        stage: str,
        progress: int,
        message: str,
        total_pages: Optional[int] = None,
        current_page: Optional[int] = None
    ):
        """更新文档处理进度

        Args:
            document_id: 文档ID
            stage: 当前阶段 ('uploading', 'parsing', 'chunking', 'vectorizing', 'completed', 'error')
            progress: 进度百分比 (0-100)
            message: 进度消息
            total_pages: 总页数（可选）
            current_page: 当前处理到的页数（可选）
        """
        self._progress_store[document_id] = {
            'stage': stage,
            'progress': progress,
            'message': message,
            'total_pages': total_pages,
            'current_page': current_page,
            'updated_at': datetime.now().isoformat()
        }

    def get_progress(self, document_id: str) -> Optional[Dict]:
        """获取文档处理进度

        Args:
            document_id: 文档ID

        Returns:
            进度信息字典，如果不存在则返回 None
        """
        return self._progress_store.get(document_id)

    def remove_progress(self, document_id: str):
        """移除文档进度记录

        Args:
            document_id: 文档ID
        """
        if document_id in self._progress_store:
            del self._progress_store[document_id]

    def clear_all(self):
        """清空所有进度记录"""
        self._progress_store.clear()


# 全局单例实例
_progress_manager = ProgressManager()


def get_progress_manager() -> ProgressManager:
    """获取进度管理器实例"""
    return _progress_manager

