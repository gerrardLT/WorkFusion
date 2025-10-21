"""
知识库管理服务
负责知识库的CRUD操作、搜索和分类管理
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from backend.database import get_db_session
from backend.models import KnowledgeItem, KnowledgeCategory, KnowledgeStatus

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库服务类"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self.db_session:
            return self.db_session
        return next(get_db_session())

    def create_knowledge_item(
        self,
        scenario_id: str,
        category: KnowledgeCategory,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        document_id: Optional[str] = None,
        issue_date: Optional[date] = None,
        expire_date: Optional[date] = None,
        metadata: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Optional[KnowledgeItem]:
        """
        创建知识库项目

        Args:
            scenario_id: 场景ID
            category: 分类
            title: 标题
            description: 描述
            tags: 标签列表
            document_id: 关联文档ID
            issue_date: 颁发日期
            expire_date: 到期日期
            metadata: 附加元数据
            file_path: 文件路径
            file_size: 文件大小
            file_type: 文件类型
            created_by: 创建人

        Returns:
            创建的KnowledgeItem对象
        """
        db = self._get_db()
        try:
            knowledge_item = KnowledgeItem(
                id=str(uuid.uuid4()),
                scenario_id=scenario_id,
                document_id=document_id,
                category=category,
                title=title,
                description=description,
                tags=tags or [],
                issue_date=issue_date,
                expire_date=expire_date,
                knowledge_metadata=metadata or {},
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                created_by=created_by
            )

            # 自动更新状态
            knowledge_item.update_status()

            db.add(knowledge_item)
            db.commit()
            db.refresh(knowledge_item)

            logger.info(f"✅ 成功创建知识库项目: {knowledge_item.id} - {knowledge_item.title}")
            return knowledge_item

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 创建知识库项目失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """
        根据ID获取知识库项目

        Args:
            item_id: 项目ID

        Returns:
            KnowledgeItem对象或None
        """
        db = self._get_db()
        try:
            item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()

            # 增加查看次数
            if item:
                item.view_count += 1
                db.commit()

            return item
        except Exception as e:
            logger.error(f"❌ 获取知识库项目失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def list_knowledge_items(
        self,
        scenario_id: str,
        category: Optional[KnowledgeCategory] = None,
        tags: Optional[List[str]] = None,
        status: Optional[KnowledgeStatus] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeItem]:
        """
        列出知识库项目

        Args:
            scenario_id: 场景ID
            category: 分类过滤
            tags: 标签过滤
            status: 状态过滤
            search_query: 搜索关键词
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            KnowledgeItem列表
        """
        db = self._get_db()
        try:
            query = db.query(KnowledgeItem).filter(
                KnowledgeItem.scenario_id == scenario_id
            )

            # 分类过滤
            if category:
                query = query.filter(KnowledgeItem.category == category)

            # 状态过滤
            if status:
                query = query.filter(KnowledgeItem.status == status)

            # 标签过滤（包含任意一个标签）
            if tags:
                # SQLite的JSON查询比较复杂，这里简化处理
                # 在实际应用中可能需要更复杂的查询逻辑
                pass

            # 搜索关键词
            if search_query:
                query = query.filter(
                    or_(
                        KnowledgeItem.title.like(f"%{search_query}%"),
                        KnowledgeItem.description.like(f"%{search_query}%")
                    )
                )

            # 排序：最近创建的在前
            query = query.order_by(KnowledgeItem.created_at.desc())

            # 分页
            items = query.limit(limit).offset(offset).all()

            return items

        except Exception as e:
            logger.error(f"❌ 列出知识库项目失败: {str(e)}", exc_info=True)
            return []
        finally:
            db.close()

    def update_knowledge_item(
        self,
        item_id: str,
        updates: Dict[str, Any]
    ) -> Optional[KnowledgeItem]:
        """
        更新知识库项目

        Args:
            item_id: 项目ID
            updates: 更新字段字典

        Returns:
            更新后的KnowledgeItem对象或None
        """
        db = self._get_db()
        try:
            item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()

            if not item:
                logger.warning(f"⚠️ 知识库项目不存在: {item_id}")
                return None

            # 更新字段
            for key, value in updates.items():
                if hasattr(item, key) and key not in ['id', 'created_at', 'created_by']:
                    setattr(item, key, value)

            # 更新时间
            item.updated_at = datetime.now()

            # 自动更新状态
            if 'expire_date' in updates or 'issue_date' in updates:
                item.update_status()

            db.commit()
            db.refresh(item)

            logger.info(f"✅ 成功更新知识库项目: {item_id}")
            return item

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 更新知识库项目失败: {str(e)}", exc_info=True)
            return None
        finally:
            db.close()

    def delete_knowledge_item(self, item_id: str) -> bool:
        """
        删除知识库项目

        Args:
            item_id: 项目ID

        Returns:
            是否删除成功
        """
        db = self._get_db()
        try:
            item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()

            if not item:
                logger.warning(f"⚠️ 知识库项目不存在: {item_id}")
                return False

            db.delete(item)
            db.commit()

            logger.info(f"✅ 成功删除知识库项目: {item_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"❌ 删除知识库项目失败: {str(e)}", exc_info=True)
            return False
        finally:
            db.close()

    def search_knowledge_items(
        self,
        scenario_id: str,
        query: str,
        category: Optional[KnowledgeCategory] = None,
        limit: int = 50
    ) -> List[KnowledgeItem]:
        """
        搜索知识库项目

        Args:
            scenario_id: 场景ID
            query: 搜索关键词
            category: 分类过滤
            limit: 返回数量限制

        Returns:
            KnowledgeItem列表
        """
        return self.list_knowledge_items(
            scenario_id=scenario_id,
            category=category,
            search_query=query,
            limit=limit
        )

    def get_expiring_items(
        self,
        scenario_id: str,
        days: int = 30
    ) -> List[KnowledgeItem]:
        """
        获取即将过期的项目

        Args:
            scenario_id: 场景ID
            days: 天数阈值

        Returns:
            即将过期的KnowledgeItem列表
        """
        db = self._get_db()
        try:
            from datetime import timedelta
            threshold_date = date.today() + timedelta(days=days)

            items = db.query(KnowledgeItem).filter(
                and_(
                    KnowledgeItem.scenario_id == scenario_id,
                    KnowledgeItem.expire_date.isnot(None),
                    KnowledgeItem.expire_date <= threshold_date,
                    KnowledgeItem.expire_date >= date.today()
                )
            ).order_by(KnowledgeItem.expire_date).all()

            return items

        except Exception as e:
            logger.error(f"❌ 获取即将过期项目失败: {str(e)}", exc_info=True)
            return []
        finally:
            db.close()

    def get_statistics(self, scenario_id: str) -> Dict[str, Any]:
        """
        获取知识库统计信息

        Args:
            scenario_id: 场景ID

        Returns:
            统计信息字典
        """
        db = self._get_db()
        try:
            total = db.query(KnowledgeItem).filter(
                KnowledgeItem.scenario_id == scenario_id
            ).count()

            stats = {
                "total": total,
                "by_category": {},
                "by_status": {},
                "expiring_soon": 0
            }

            # 按分类统计
            for category in KnowledgeCategory:
                count = db.query(KnowledgeItem).filter(
                    and_(
                        KnowledgeItem.scenario_id == scenario_id,
                        KnowledgeItem.category == category
                    )
                ).count()
                stats["by_category"][category.value] = count

            # 按状态统计
            for status in KnowledgeStatus:
                count = db.query(KnowledgeItem).filter(
                    and_(
                        KnowledgeItem.scenario_id == scenario_id,
                        KnowledgeItem.status == status
                    )
                ).count()
                stats["by_status"][status.value] = count

            # 即将过期数量
            expiring_items = self.get_expiring_items(scenario_id, days=30)
            stats["expiring_soon"] = len(expiring_items)

            return stats

        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {str(e)}", exc_info=True)
            return {"total": 0, "by_category": {}, "by_status": {}, "expiring_soon": 0}
        finally:
            db.close()


# 单例模式
_knowledge_service_instance = None


def get_knowledge_service() -> KnowledgeService:
    """获取KnowledgeService单例"""
    global _knowledge_service_instance
    if _knowledge_service_instance is None:
        _knowledge_service_instance = KnowledgeService()
    return _knowledge_service_instance

