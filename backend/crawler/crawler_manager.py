"""
爬虫管理器
统一调度和管理多个爬虫
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.crawler.incremental_manager import get_incremental_manager

logger = logging.getLogger(__name__)


class CrawlerManager:
    """
    爬虫管理器

    功能：
    - 统一调度多个爬虫
    - 监控爬取状态
    - 收集统计信息
    """

    def __init__(self):
        self.incremental_manager = get_incremental_manager()
        self.project_root = Path(__file__).parent.parent.parent

        # 已注册的爬虫
        self.registered_spiders = {
            'gov_procurement': {
                'name': 'gov_procurement',
                'description': '中国政府采购网',
                'type': 'static',
                'enabled': True,
                'priority': 1,
            },
            'dynamic_platform': {
                'name': 'dynamic_platform',
                'description': '动态加载平台',
                'type': 'dynamic',
                'enabled': False,  # 示例爬虫，默认禁用
                'priority': 2,
            },
            'auth_platform': {
                'name': 'auth_platform',
                'description': '需登录平台',
                'type': 'auth',
                'enabled': False,  # 示例爬虫，默认禁用
                'priority': 3,
            },
            'demo_tender': {
                'name': 'demo_tender',
                'description': '演示爬虫',
                'type': 'demo',
                'enabled': True,
                'priority': 10,
            },
        }

    def run_spider(self,
                   spider_name: str,
                   crawl_type: str = 'incremental',
                   max_pages: int = 10,
                   **kwargs) -> Dict[str, Any]:
        """
        运行单个爬虫

        Args:
            spider_name: 爬虫名称
            crawl_type: 爬取类型（full: 全量, incremental: 增量）
            max_pages: 最大爬取页数
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        if spider_name not in self.registered_spiders:
            logger.error(f'爬虫 {spider_name} 未注册')
            return {'success': False, 'error': f'爬虫 {spider_name} 未注册'}

        spider_info = self.registered_spiders[spider_name]

        if not spider_info['enabled']:
            logger.warning(f'爬虫 {spider_name} 已禁用')
            return {'success': False, 'error': f'爬虫 {spider_name} 已禁用'}

        logger.info(f'开始运行爬虫: {spider_name} ({crawl_type})')

        # 开始爬取会话
        session_id = self.incremental_manager.start_crawl_session(spider_name, crawl_type)

        try:
            # 构建Scrapy命令
            cmd = self._build_scrapy_command(spider_name, max_pages, **kwargs)

            # 执行爬虫
            start_time = datetime.now()
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root / 'backend' / 'crawler'),
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            end_time = datetime.now()

            # 解析输出
            stats = self._parse_spider_output(result.stdout)
            stats['start_time'] = start_time.isoformat()
            stats['end_time'] = end_time.isoformat()
            stats['duration_seconds'] = (end_time - start_time).total_seconds()
            stats['status'] = 'completed' if result.returncode == 0 else 'failed'

            if result.returncode != 0:
                logger.error(f'爬虫 {spider_name} 执行失败')
                logger.error(f'错误输出: {result.stderr}')
                stats['error'] = result.stderr
            else:
                logger.info(f'爬虫 {spider_name} 执行成功')

            # 结束爬取会话
            self.incremental_manager.end_crawl_session(session_id, stats)

            return {
                'success': result.returncode == 0,
                'spider_name': spider_name,
                'session_id': session_id,
                'stats': stats
            }

        except subprocess.TimeoutExpired:
            logger.error(f'爬虫 {spider_name} 执行超时')
            stats = {'status': 'timeout', 'error': '执行超时'}
            self.incremental_manager.end_crawl_session(session_id, stats)
            return {
                'success': False,
                'spider_name': spider_name,
                'error': '执行超时'
            }
        except Exception as e:
            logger.error(f'爬虫 {spider_name} 执行异常: {e}')
            stats = {'status': 'error', 'error': str(e)}
            self.incremental_manager.end_crawl_session(session_id, stats)
            return {
                'success': False,
                'spider_name': spider_name,
                'error': str(e)
            }

    def run_all_spiders(self,
                       crawl_type: str = 'incremental',
                       max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        运行所有已启用的爬虫

        Args:
            crawl_type: 爬取类型
            max_pages: 最大爬取页数

        Returns:
            所有爬虫的执行结果列表
        """
        logger.info(f'开始运行所有爬虫 (type={crawl_type})')

        results = []

        # 按优先级排序
        sorted_spiders = sorted(
            [(name, info) for name, info in self.registered_spiders.items() if info['enabled']],
            key=lambda x: x[1]['priority']
        )

        for spider_name, spider_info in sorted_spiders:
            logger.info(f'运行爬虫: {spider_name} (优先级={spider_info["priority"]})')
            result = self.run_spider(spider_name, crawl_type, max_pages)
            results.append(result)

        logger.info(f'所有爬虫运行完成，共 {len(results)} 个')
        return results

    def get_spider_list(self) -> List[Dict[str, Any]]:
        """
        获取所有已注册的爬虫列表

        Returns:
            爬虫信息列表
        """
        return [
            {
                'name': name,
                **info,
                'statistics': self.incremental_manager.get_crawl_statistics(name)
            }
            for name, info in self.registered_spiders.items()
        ]

    def get_spider_status(self, spider_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定爬虫的状态

        Args:
            spider_name: 爬虫名称

        Returns:
            爬虫状态信息
        """
        if spider_name not in self.registered_spiders:
            return None

        spider_info = self.registered_spiders[spider_name]
        statistics = self.incremental_manager.get_crawl_statistics(spider_name)
        recent_crawls = self.incremental_manager.get_recent_crawls(spider_name, limit=5)

        return {
            'name': spider_name,
            **spider_info,
            'statistics': statistics,
            'recent_crawls': recent_crawls
        }

    def enable_spider(self, spider_name: str) -> bool:
        """启用爬虫"""
        if spider_name in self.registered_spiders:
            self.registered_spiders[spider_name]['enabled'] = True
            logger.info(f'爬虫 {spider_name} 已启用')
            return True
        return False

    def disable_spider(self, spider_name: str) -> bool:
        """禁用爬虫"""
        if spider_name in self.registered_spiders:
            self.registered_spiders[spider_name]['enabled'] = False
            logger.info(f'爬虫 {spider_name} 已禁用')
            return True
        return False

    def _build_scrapy_command(self, spider_name: str, max_pages: int, **kwargs) -> List[str]:
        """
        构建Scrapy命令

        Args:
            spider_name: 爬虫名称
            max_pages: 最大页数
            **kwargs: 其他参数

        Returns:
            命令列表
        """
        cmd = [
            sys.executable,
            '-m', 'scrapy',
            'crawl',
            spider_name,
            '-a', f'max_pages={max_pages}'
        ]

        # 添加其他参数
        for key, value in kwargs.items():
            cmd.extend(['-a', f'{key}={value}'])

        # 添加日志级别
        cmd.extend(['-L', 'INFO'])

        return cmd

    def _parse_spider_output(self, output: str) -> Dict[str, Any]:
        """
        解析爬虫输出，提取统计信息

        Args:
            output: 爬虫标准输出

        Returns:
            统计信息字典
        """
        stats = {
            'total_items': 0,
            'new_items': 0,
            'updated_items': 0,
            'failed_items': 0
        }

        # 从输出中提取统计信息
        # Scrapy会输出类似 "item_scraped_count: 100" 的信息
        import re

        patterns = {
            'total_items': r'item_scraped_count[:\s]+(\d+)',
            'failed_items': r'item_dropped_count[:\s]+(\d+)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                stats[key] = int(match.group(1))

        return stats


# 全局单例
_crawler_manager: Optional[CrawlerManager] = None


def get_crawler_manager() -> CrawlerManager:
    """获取爬虫管理器单例"""
    global _crawler_manager
    if _crawler_manager is None:
        _crawler_manager = CrawlerManager()
    return _crawler_manager

