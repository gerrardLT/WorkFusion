"""
会话管理服务
提供会话和消息的CRUD操作，支持多租户隔离
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..database import get_db_session
from ..models.chat import ChatSession, ChatMessage


class ChatService:
    """会话管理服务"""

    def __init__(self):
        self.db = get_db_session

    # ========== 会话管理 ==========

    def create_session(
        self,
        scenario_id: str,
        user_id: str,
        tenant_id: str,
        title: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ChatSession:
        """创建新会话

        Args:
            scenario_id: 场景ID
            user_id: 用户ID
            tenant_id: 租户ID
            title: 会话标题（可选）
            config: 会话配置（可选）

        Returns:
            创建的会话对象
        """
        with self.db() as db:
            session = ChatSession(
                id=self._generate_id(),
                scenario_id=scenario_id,
                user_id=user_id,
                tenant_id=tenant_id,
                title=title or f"新对话 - {datetime.now().strftime('%m-%d %H:%M')}",
                config=config or {}
            )

            db.add(session)
            db.commit()
            db.refresh(session)

            return session

    def get_session(self, session_id: str, tenant_id: str) -> Optional[ChatSession]:
        """获取指定会话（租户隔离）

        Args:
            session_id: 会话ID
            tenant_id: 租户ID

        Returns:
            会话对象或None
        """
        with self.db() as db:
            return db.query(ChatSession).filter(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.tenant_id == tenant_id
                )
            ).first()

    def get_user_sessions(
        self,
        tenant_id: str,
        scenario_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ChatSession]:
        """获取租户的所有会话列表

        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID（可选，用于筛选）
            limit: 返回数量限制

        Returns:
            会话列表
        """
        with self.db() as db:
            query = db.query(ChatSession).filter(
                ChatSession.tenant_id == tenant_id
            )

            if scenario_id:
                query = query.filter(ChatSession.scenario_id == scenario_id)

            return query.order_by(
                desc(ChatSession.updated_at)
            ).limit(limit).all()

    def update_session(
        self,
        session_id: str,
        tenant_id: str,
        title: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatSession]:
        """更新会话

        Args:
            session_id: 会话ID
            tenant_id: 租户ID
            title: 新标题（可选）
            config: 新配置（可选）

        Returns:
            更新后的会话对象或None
        """
        with self.db() as db:
            session = db.query(ChatSession).filter(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.tenant_id == tenant_id
                )
            ).first()

            if not session:
                return None

            if title is not None:
                session.title = title
            if config is not None:
                session.config = config

            session.updated_at = datetime.now()

            db.commit()
            db.refresh(session)

            return session

    def delete_session(self, session_id: str, tenant_id: str) -> bool:
        """删除会话（级联删除消息）

        Args:
            session_id: 会话ID
            tenant_id: 租户ID

        Returns:
            是否删除成功
        """
        with self.db() as db:
            session = db.query(ChatSession).filter(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.tenant_id == tenant_id
                )
            ).first()

            if not session:
                return False

            db.delete(session)
            db.commit()

            return True

    # ========== 消息管理 ==========

    def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """创建消息

        Args:
            session_id: 会话ID
            role: 角色 ('user', 'assistant', 'system')
            content: 消息内容
            metadata: 消息元数据（可选）

        Returns:
            创建的消息对象
        """
        with self.db() as db:
            message = ChatMessage(
                id=self._generate_id(),
                session_id=session_id,
                role=role,
                content=content,
                msg_metadata=metadata or {}
            )

            db.add(message)

            # 更新会话的 updated_at
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            if session:
                session.updated_at = datetime.now()

            db.commit()
            db.refresh(message)

            return message

    def get_session_messages(
        self,
        session_id: str,
        tenant_id: str,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """获取会话的所有消息（租户隔离）

        Args:
            session_id: 会话ID
            tenant_id: 租户ID
            limit: 返回数量限制（可选）

        Returns:
            消息列表
        """
        with self.db() as db:
            # 先验证会话属于该租户
            session = db.query(ChatSession).filter(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.tenant_id == tenant_id
                )
            ).first()

            if not session:
                return []

            query = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.asc())

            if limit:
                query = query.limit(limit)

            return query.all()

    def get_recent_messages(
        self,
        session_id: str,
        tenant_id: str,
        count: int = 10
    ) -> List[ChatMessage]:
        """获取最近的N条消息

        Args:
            session_id: 会话ID
            tenant_id: 租户ID
            count: 消息数量

        Returns:
            最近的消息列表
        """
        messages = self.get_session_messages(session_id, tenant_id)
        return messages[-count:] if messages else []

    def get_message_history_for_context(
        self,
        session_id: str,
        tenant_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """获取消息历史用于LLM上下文（格式化为消息列表）

        Args:
            session_id: 会话ID
            tenant_id: 租户ID
            max_messages: 最大消息数量

        Returns:
            格式化的消息列表 [{"role": "user", "content": "..."}, ...]
        """
        messages = self.get_recent_messages(session_id, tenant_id, max_messages)

        # 格式化为LLM需要的格式
        formatted_messages = []
        for msg in messages:
            if msg.role in ['user', 'assistant', 'system']:
                formatted_messages.append({
                    'role': msg.role,
                    'content': msg.content
                })

        return formatted_messages

    # ========== 统计和查询 ==========

    def get_session_message_count(self, session_id: str, tenant_id: str) -> int:
        """获取会话的消息数量

        Args:
            session_id: 会话ID
            tenant_id: 租户ID

        Returns:
            消息数量
        """
        with self.db() as db:
            # 先验证会话属于该租户
            session = db.query(ChatSession).filter(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.tenant_id == tenant_id
                )
            ).first()

            if not session:
                return 0

            return db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).count()

    def session_exists(self, session_id: str, tenant_id: str) -> bool:
        """检查会话是否存在

        Args:
            session_id: 会话ID
            tenant_id: 租户ID

        Returns:
            是否存在
        """
        with self.db() as db:
            return db.query(ChatSession).filter(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.tenant_id == tenant_id
                )
            ).first() is not None

    # ========== 工具方法 ==========

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return str(uuid.uuid4())


# 全局服务实例
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取会话服务实例（依赖注入）"""
    global _chat_service

    if _chat_service is None:
        _chat_service = ChatService()

    return _chat_service

