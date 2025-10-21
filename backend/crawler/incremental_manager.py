"""
增量更新管理器
实现智能的增量爬取策略
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set, Dict, Any

logger = logging.getLogger(__name__)


class IncrementalManager:
    """
    增量更新管理器

    功能：
    - 记录已爬取的项目
    - 判断是否需要更新
    - 避免重复爬取
    """

    def __init__(self, db_path: str = 'data/stock_data/databases/tender_crawler.db'):
        self.db_path = db_path
        self.db = None
        self._cached_urls: Optional[Set[str]] = None
        self._cached_hashes: Optional[Set[str]] = None
        self._init_db()

    def _init_db(self):
        """初始化数据库连接"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(self.db_path)
            self._create_tables()
            logger.info(f'增量管理器已连接到数据库: {self.db_path}')
        except Exception as e:
            logger.error(f'数据库连接失败: {e}')

    def _create_tables(self):
        """创建必要的表"""
        cursor = self.db.cursor()

        # 已爬取URL记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawled_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                data_hash TEXT,
                spider_name TEXT,
                first_crawled_at DATETIME,
                last_crawled_at DATETIME,
                crawl_count INTEGER DEFAULT 1,
                is_updated BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 爬取历史记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spider_name TEXT,
                crawl_type TEXT,
                start_time DATETIME,
                end_time DATETIME,
                total_items INTEGER DEFAULT 0,
                new_items INTEGER DEFAULT 0,
                updated_items INTEGER DEFAULT 0,
                failed_items INTEGER DEFAULT 0,
                status TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 爬取统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spider_name TEXT UNIQUE,
                total_crawled INTEGER DEFAULT 0,
                last_crawl_time DATETIME,
                success_rate REAL DEFAULT 0.0,
                avg_response_time REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.db.commit()
        logger.info('增量管理器表结构已创建')

    def is_url_crawled(self, url: str, max_age_days: int = 7) -> bool:
        """
        检查URL是否已爬取（且未过期）

        Args:
            url: 待检查的URL
            max_age_days: 最大过期天数，超过此天数视为需要更新

        Returns:
            True表示已爬取且未过期，False表示需要爬取
        """
        if not self.db:
            return False

        cursor = self.db.cursor()
        cursor.execute('''
            SELECT last_crawled_at FROM crawled_urls WHERE url = ?
        ''', (url,))

        result = cursor.fetchone()
        if not result:
            return False

        last_crawled = datetime.fromisoformat(result[0])
        age = datetime.now() - last_crawled

        return age.days < max_age_days

    def is_hash_crawled(self, data_hash: str) -> bool:
        """
        检查数据哈希是否已存在

        Args:
            data_hash: 数据的MD5哈希值

        Returns:
            True表示已存在，False表示新数据
        """
        if not self.db:
            return False

        # 使用缓存加速查询
        if self._cached_hashes is None:
            self._load_hash_cache()

        return data_hash in self._cached_hashes

    def mark_url_crawled(self, url: str, data_hash: str, spider_name: str):
        """
        标记URL已爬取

        Args:
            url: 爬取的URL
            data_hash: 数据哈希
            spider_name: 爬虫名称
        """
        if not self.db:
            return

        cursor = self.db.cursor()
        now = datetime.now().isoformat()

        # 检查是否已存在
        cursor.execute('SELECT id, crawl_count FROM crawled_urls WHERE url = ?', (url,))
        result = cursor.fetchone()

        if result:
            # 更新已存在的记录
            crawl_count = result[1] + 1
            cursor.execute('''
                UPDATE crawled_urls
                SET data_hash = ?,
                    last_crawled_at = ?,
                    crawl_count = ?,
                    is_updated = 1
                WHERE url = ?
            ''', (data_hash, now, crawl_count, url))
        else:
            # 插入新记录
            cursor.execute('''
                INSERT INTO crawled_urls
                (url, data_hash, spider_name, first_crawled_at, last_crawled_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, data_hash, spider_name, now, now))

        self.db.commit()

        # 更新缓存
        if self._cached_urls is not None:
            self._cached_urls.add(url)
        if self._cached_hashes is not None:
            self._cached_hashes.add(data_hash)

    def start_crawl_session(self, spider_name: str, crawl_type: str = 'incremental') -> int:
        """
        开始一次爬取会话

        Args:
            spider_name: 爬虫名称
            crawl_type: 爬取类型（full: 全量, incremental: 增量）

        Returns:
            会话ID
        """
        if not self.db:
            return -1

        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO crawl_history (spider_name, crawl_type, start_time, status)
            VALUES (?, ?, ?, 'running')
        ''', (spider_name, crawl_type, datetime.now().isoformat()))

        self.db.commit()
        session_id = cursor.lastrowid

        logger.info(f'爬取会话已开始: {spider_name} (session_id={session_id}, type={crawl_type})')
        return session_id

    def end_crawl_session(self, session_id: int, stats: Dict[str, Any]):
        """
        结束爬取会话

        Args:
            session_id: 会话ID
            stats: 统计数据
        """
        if not self.db or session_id < 0:
            return

        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE crawl_history
            SET end_time = ?,
                total_items = ?,
                new_items = ?,
                updated_items = ?,
                failed_items = ?,
                status = ?
            WHERE id = ?
        ''', (
            datetime.now().isoformat(),
            stats.get('total_items', 0),
            stats.get('new_items', 0),
            stats.get('updated_items', 0),
            stats.get('failed_items', 0),
            stats.get('status', 'completed'),
            session_id
        ))

        self.db.commit()
        logger.info(f'爬取会话已结束: session_id={session_id}')

    def get_crawl_statistics(self, spider_name: str) -> Optional[Dict[str, Any]]:
        """
        获取爬虫统计信息

        Args:
            spider_name: 爬虫名称

        Returns:
            统计信息字典
        """
        if not self.db:
            return None

        cursor = self.db.cursor()
        cursor.execute('''
            SELECT total_crawled, last_crawl_time, success_rate, avg_response_time
            FROM crawl_statistics
            WHERE spider_name = ?
        ''', (spider_name,))

        result = cursor.fetchone()
        if result:
            return {
                'total_crawled': result[0],
                'last_crawl_time': result[1],
                'success_rate': result[2],
                'avg_response_time': result[3]
            }

        return None

    def get_recent_crawls(self, spider_name: Optional[str] = None, limit: int = 10) -> list:
        """
        获取最近的爬取记录

        Args:
            spider_name: 爬虫名称（可选）
            limit: 返回记录数

        Returns:
            爬取记录列表
        """
        if not self.db:
            return []

        cursor = self.db.cursor()

        if spider_name:
            cursor.execute('''
                SELECT spider_name, crawl_type, start_time, end_time,
                       total_items, new_items, updated_items, status
                FROM crawl_history
                WHERE spider_name = ?
                ORDER BY start_time DESC
                LIMIT ?
            ''', (spider_name, limit))
        else:
            cursor.execute('''
                SELECT spider_name, crawl_type, start_time, end_time,
                       total_items, new_items, updated_items, status
                FROM crawl_history
                ORDER BY start_time DESC
                LIMIT ?
            ''', (limit,))

        results = cursor.fetchall()
        return [
            {
                'spider_name': row[0],
                'crawl_type': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'total_items': row[4],
                'new_items': row[5],
                'updated_items': row[6],
                'status': row[7]
            }
            for row in results
        ]

    def _load_url_cache(self):
        """加载URL缓存"""
        if not self.db:
            self._cached_urls = set()
            return

        cursor = self.db.cursor()
        cursor.execute('SELECT url FROM crawled_urls')
        self._cached_urls = {row[0] for row in cursor.fetchall()}
        logger.info(f'已加载 {len(self._cached_urls)} 个URL到缓存')

    def _load_hash_cache(self):
        """加载哈希缓存"""
        if not self.db:
            self._cached_hashes = set()
            return

        cursor = self.db.cursor()
        cursor.execute('SELECT data_hash FROM crawled_urls WHERE data_hash IS NOT NULL')
        self._cached_hashes = {row[0] for row in cursor.fetchall()}
        logger.info(f'已加载 {len(self._cached_hashes)} 个哈希到缓存')

    def clear_cache(self):
        """清空缓存"""
        self._cached_urls = None
        self._cached_hashes = None
        logger.info('缓存已清空')

    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()
            logger.info('增量管理器已关闭')


# 全局单例
_incremental_manager: Optional[IncrementalManager] = None


def get_incremental_manager() -> IncrementalManager:
    """获取增量管理器单例"""
    global _incremental_manager
    if _incremental_manager is None:
        _incremental_manager = IncrementalManager()
    return _incremental_manager

