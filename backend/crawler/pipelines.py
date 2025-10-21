"""
Scrapy Pipelines
实现数据清洗、去重和存储
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Optional
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from backend.crawler.data_processor import DataNormalizer, AdvancedDataCleaner, CrossPlatformDeduplicator

logger = logging.getLogger(__name__)


class DataCleaningPipeline:
    """数据清洗Pipeline"""

    def process_item(self, item, spider):
        """清洗和标准化数据"""
        adapter = ItemAdapter(item)

        # 清洗标题
        if adapter.get('title'):
            adapter['title'] = self._clean_text(adapter['title'])

        # 清洗内容
        if adapter.get('content_text'):
            adapter['content_text'] = self._clean_text(adapter['content_text'])

        # 标准化金额
        if adapter.get('budget_text'):
            adapter['budget'] = self._parse_amount(adapter['budget_text'])

        if adapter.get('winner_amount_text'):
            adapter['winner_amount'] = self._parse_amount(adapter['winner_amount_text'])

        # 标准化日期
        if adapter.get('publish_time') and isinstance(adapter['publish_time'], str):
            adapter['publish_time'] = self._parse_date(adapter['publish_time'])

        if adapter.get('deadline') and isinstance(adapter['deadline'], str):
            adapter['deadline'] = self._parse_date(adapter['deadline'])

        # 标准化地域
        if adapter.get('province'):
            adapter['province'] = self._standardize_province(adapter['province'])

        return item

    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ''

        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 去除首尾空白
        text = text.strip()
        return text

    def _parse_amount(self, amount_text: str) -> Optional[float]:
        """
        解析金额文本，统一为万元
        例如：
        - "100万元" -> 100.0
        - "1000元" -> 0.1
        - "10亿元" -> 100000.0
        """
        if not amount_text:
            return None

        # 移除非数字字符（保留小数点）
        numbers = re.findall(r'\d+\.?\d*', amount_text)
        if not numbers:
            return None

        amount = float(numbers[0])

        # 判断单位
        if '亿' in amount_text:
            amount = amount * 10000  # 转为万元
        elif '万' in amount_text:
            amount = amount  # 已经是万元
        elif '千' in amount_text:
            amount = amount * 0.1  # 千元转万元
        elif '元' in amount_text:
            amount = amount * 0.0001  # 元转万元

        return round(amount, 2)

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """解析日期文本"""
        if not date_text:
            return None

        # 尝试多种日期格式
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',  # 2024-01-01 12:00:00
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-01
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2024年01月01日
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 6:  # 包含时间
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]),
                                      int(groups[3]), int(groups[4]), int(groups[5]))
                    else:  # 只有日期
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                except ValueError:
                    continue

        return None

    def _standardize_province(self, province: str) -> str:
        """标准化省份名称"""
        # 省份映射表
        province_map = {
            '北京': '北京市',
            '上海': '上海市',
            '天津': '天津市',
            '重庆': '重庆市',
            # 其他省份可以根据需要添加
        }

        province = province.strip()
        return province_map.get(province, province)


class EnhancedDataCleaningPipeline:
    """增强版数据清洗Pipeline（使用AdvancedDataCleaner）"""

    def __init__(self):
        self.normalizer = DataNormalizer()
        self.stats = {
            'total': 0,
            'cleaned': 0,
            'failed': 0
        }

    def process_item(self, item, spider):
        """清洗和规范化数据"""
        adapter = ItemAdapter(item)
        self.stats['total'] += 1

        try:
            # 转换为字典
            item_dict = dict(adapter)

            # 规范化数据
            normalized_dict = self.normalizer.normalize_tender_item(item_dict)

            # 更新adapter
            for key, value in normalized_dict.items():
                adapter[key] = value

            self.stats['cleaned'] += 1
            return item

        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f'数据清洗失败: {e}')
            return item

    def close_spider(self, spider):
        """Spider关闭时打印统计信息"""
        logger.info(f'数据清洗统计 - 总数: {self.stats["total"]}, '
                   f'成功: {self.stats["cleaned"]}, '
                   f'失败: {self.stats["failed"]}')


class CrossPlatformDuplicatesPipeline:
    """跨平台去重Pipeline（使用标题+金额相似度）"""

    def __init__(self):
        self.deduplicator = CrossPlatformDeduplicator(similarity_threshold=0.85)
        self.stats = {
            'total': 0,
            'url_duplicates': 0,
            'similarity_duplicates': 0,
            'saved': 0
        }

    def process_item(self, item, spider):
        """检查跨平台去重"""
        adapter = ItemAdapter(item)
        self.stats['total'] += 1

        url = adapter.get('source_url', '')
        title = adapter.get('title', '')
        budget = adapter.get('budget')

        # 检查是否重复
        is_dup, reason = self.deduplicator.is_duplicate(url, title, budget)

        if is_dup:
            if 'URL' in reason:
                self.stats['url_duplicates'] += 1
            else:
                self.stats['similarity_duplicates'] += 1

            logger.debug(f'跨平台去重: {title[:30]}... - {reason}')
            raise DropItem(f'跨平台重复: {reason}')

        # 标记为已见
        self.deduplicator.mark_seen(url, title, budget)
        self.stats['saved'] += 1

        return item

    def close_spider(self, spider):
        """Spider关闭时打印统计信息"""
        logger.info(f'跨平台去重统计 - 总数: {self.stats["total"]}, '
                   f'URL重复: {self.stats["url_duplicates"]}, '
                   f'相似度重复: {self.stats["similarity_duplicates"]}, '
                   f'保存: {self.stats["saved"]}')


class DuplicatesPipeline:
    """去重Pipeline（保留用于向后兼容）"""

    def __init__(self):
        self.seen_hashes = set()
        self.stats = {'total': 0, 'duplicates': 0, 'saved': 0}

    def process_item(self, item, spider):
        """检查并去重"""
        adapter = ItemAdapter(item)

        # 生成数据哈希
        data_hash = self._generate_hash(item)
        adapter['data_hash'] = data_hash

        self.stats['total'] += 1

        # 检查是否重复
        if data_hash in self.seen_hashes:
            self.stats['duplicates'] += 1
            logger.debug(f'发现重复数据: {adapter.get("title", "Unknown")}')
            raise DropItem(f'重复数据: {data_hash}')

        self.seen_hashes.add(data_hash)
        self.stats['saved'] += 1

        return item

    def _generate_hash(self, item) -> str:
        """生成数据哈希用于去重"""
        adapter = ItemAdapter(item)

        # 使用关键字段生成哈希
        key_fields = []

        # 优先使用URL
        if adapter.get('source_url'):
            key_fields.append(adapter['source_url'])
        else:
            # 否则使用标题+项目编号
            if adapter.get('title'):
                key_fields.append(adapter['title'])
            if adapter.get('project_number'):
                key_fields.append(adapter['project_number'])

        # 生成MD5哈希
        hash_string = '|'.join(str(f) for f in key_fields)
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    def close_spider(self, spider):
        """Spider关闭时打印统计信息"""
        logger.info(f'去重统计 - 总数: {self.stats["total"]}, '
                   f'重复: {self.stats["duplicates"]}, '
                   f'保存: {self.stats["saved"]}')


class DatabasePipeline:
    """数据库存储Pipeline"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = None
        self.stats = {'saved': 0, 'failed': 0}

    @classmethod
    def from_crawler(cls, crawler):
        db_path = crawler.settings.get('DATABASE_PATH', 'data/stock_data/databases/tender_crawler.db')
        return cls(db_path=db_path)

    def open_spider(self, spider):
        """Spider开启时初始化数据库连接"""
        try:
            import sqlite3
            self.db = sqlite3.connect(self.db_path)
            self._create_tables()
            logger.info(f'数据库连接成功: {self.db_path}')
        except Exception as e:
            logger.error(f'数据库连接失败: {e}')

    def close_spider(self, spider):
        """Spider关闭时关闭数据库连接"""
        if self.db:
            self.db.close()
            logger.info(f'数据存储统计 - 成功: {self.stats["saved"]}, 失败: {self.stats["failed"]}')

    def process_item(self, item, spider):
        """保存数据到数据库"""
        if not self.db:
            return item

        try:
            adapter = ItemAdapter(item)

            # 根据item类型选择表
            if adapter.get('winner_name'):  # BidResultItem
                self._save_bid_result(adapter)
            else:  # TenderItem
                self._save_tender(adapter)

            self.stats['saved'] += 1

        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f'保存数据失败: {e}')

        return item

    def _create_tables(self):
        """创建数据库表"""
        cursor = self.db.cursor()

        # 招标信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tender_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE,
                title TEXT,
                project_number TEXT,
                source_platform TEXT,
                source_url TEXT,
                industry TEXT,
                project_type TEXT,
                budget REAL,
                province TEXT,
                city TEXT,
                publish_time DATETIME,
                deadline DATETIME,
                content_text TEXT,
                status TEXT,
                crawled_time DATETIME,
                data_hash TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 中标结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tender_project_id TEXT,
                title TEXT,
                winner_name TEXT,
                winner_amount REAL,
                bid_date DATETIME,
                content_text TEXT,
                crawled_time DATETIME,
                data_hash TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tender_project_id) REFERENCES tender_projects(project_id)
            )
        ''')

        self.db.commit()

    def _save_tender(self, adapter):
        """保存招标信息"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tender_projects
            (project_id, title, project_number, source_platform, source_url, industry,
             project_type, budget, province, city, publish_time, deadline, content_text,
             status, crawled_time, data_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            adapter.get('project_id'),
            adapter.get('title'),
            adapter.get('project_number'),
            adapter.get('source_platform'),
            adapter.get('source_url'),
            adapter.get('industry'),
            adapter.get('project_type'),
            adapter.get('budget'),
            adapter.get('province'),
            adapter.get('city'),
            adapter.get('publish_time'),
            adapter.get('deadline'),
            adapter.get('content_text'),
            adapter.get('status'),
            adapter.get('crawled_time', datetime.now()),
            adapter.get('data_hash')
        ))
        self.db.commit()

    def _save_bid_result(self, adapter):
        """保存中标结果"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO bid_results
            (tender_project_id, title, winner_name, winner_amount, bid_date,
             content_text, crawled_time, data_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            adapter.get('tender_project_id'),
            adapter.get('title'),
            adapter.get('winner_name'),
            adapter.get('winner_amount'),
            adapter.get('bid_date'),
            adapter.get('content_text'),
            adapter.get('crawled_time', datetime.now()),
            adapter.get('data_hash')
        ))
        self.db.commit()


class JsonExportPipeline:
    """JSON导出Pipeline（备份）"""

    def __init__(self, export_path: str):
        self.export_path = export_path
        self.file = None
        self.items = []

    @classmethod
    def from_crawler(cls, crawler):
        export_path = crawler.settings.get('JSON_EXPORT_PATH', 'data/stock_data/crawler_backup.json')
        return cls(export_path=export_path)

    def open_spider(self, spider):
        """Spider开启时打开文件"""
        self.items = []

    def close_spider(self, spider):
        """Spider关闭时写入文件"""
        if self.items:
            with open(self.export_path, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f'已导出{len(self.items)}条数据到: {self.export_path}')

    def process_item(self, item, spider):
        """收集数据"""
        self.items.append(dict(item))
        return item

