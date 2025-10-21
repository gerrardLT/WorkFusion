"""
爬虫平台对接测试
验证T2.1.2任务：对接2-3个招标平台
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestCrawlerPlatforms:
    """爬虫平台测试类"""

    def test_gov_procurement_spider_exists(self):
        """测试1: 中国政府采购网爬虫存在"""
        spider_file = project_root / "backend" / "crawler" / "spiders" / "gov_procurement_spider.py"
        assert spider_file.exists()

        from backend.crawler.spiders.gov_procurement_spider import GovProcurementSpider
        assert GovProcurementSpider is not None

        spider = GovProcurementSpider()
        assert spider.name == 'gov_procurement'
        assert 'ccgp.gov.cn' in spider.allowed_domains

        logger.info("✅ 中国政府采购网爬虫验证通过")

    def test_gov_procurement_spider_methods(self):
        """测试2: 中国政府采购网爬虫方法完整性"""
        from backend.crawler.spiders.gov_procurement_spider import GovProcurementSpider

        spider = GovProcurementSpider()

        # 检查关键方法
        assert hasattr(spider, 'parse_tender_list')
        assert hasattr(spider, 'parse_bid_result_list')
        assert hasattr(spider, 'parse_tender_detail')
        assert hasattr(spider, 'parse_bid_result_detail')
        assert hasattr(spider, '_extract_title')
        assert hasattr(spider, '_extract_budget')
        assert hasattr(spider, '_extract_location')

        logger.info("✅ 中国政府采购网爬虫方法验证通过")

    def test_dynamic_platform_spider_exists(self):
        """测试3: 动态加载平台爬虫存在"""
        spider_file = project_root / "backend" / "crawler" / "spiders" / "dynamic_platform_spider.py"
        assert spider_file.exists()

        from backend.crawler.spiders.dynamic_platform_spider import DynamicPlatformSpider
        assert DynamicPlatformSpider is not None

        spider = DynamicPlatformSpider()
        assert spider.name == 'dynamic_platform'
        assert spider.use_selenium == True

        logger.info("✅ 动态加载平台爬虫验证通过")

    def test_auth_platform_spider_exists(self):
        """测试4: 需登录平台爬虫存在"""
        spider_file = project_root / "backend" / "crawler" / "spiders" / "auth_platform_spider.py"
        assert spider_file.exists()

        from backend.crawler.spiders.auth_platform_spider import AuthPlatformSpider
        assert AuthPlatformSpider is not None

        spider = AuthPlatformSpider()
        assert spider.name == 'auth_platform'
        assert hasattr(spider, 'login_url')
        assert hasattr(spider, 'cookie_file')

        logger.info("✅ 需登录平台爬虫验证通过")

    def test_auth_spider_cookie_management(self):
        """测试5: 登录爬虫Cookie管理"""
        from backend.crawler.spiders.auth_platform_spider import AuthPlatformSpider

        spider = AuthPlatformSpider()

        # 检查Cookie管理方法
        assert hasattr(spider, '_load_cookies')
        assert hasattr(spider, '_save_cookies')
        assert hasattr(spider, '_is_cookie_expired')
        assert hasattr(spider, '_check_login_success')
        assert hasattr(spider, '_need_relogin')

        logger.info("✅ Cookie管理方法验证通过")

    def test_incremental_manager_exists(self):
        """测试6: 增量更新管理器存在"""
        manager_file = project_root / "backend" / "crawler" / "incremental_manager.py"
        assert manager_file.exists()

        from backend.crawler.incremental_manager import IncrementalManager, get_incremental_manager
        assert IncrementalManager is not None

        manager = get_incremental_manager()
        assert manager is not None
        assert hasattr(manager, 'is_url_crawled')
        assert hasattr(manager, 'mark_url_crawled')

        logger.info("✅ 增量更新管理器验证通过")

    def test_incremental_manager_methods(self):
        """测试7: 增量更新管理器方法"""
        from backend.crawler.incremental_manager import get_incremental_manager

        manager = get_incremental_manager()

        # 测试URL检查（应该未爬取）
        test_url = 'http://test.example.com/project/12345'
        assert manager.is_url_crawled(test_url) == False

        # 测试标记URL
        manager.mark_url_crawled(test_url, 'test_hash_123', 'test_spider')

        # 测试哈希检查
        assert manager.is_hash_crawled('test_hash_123') == True

        logger.info("✅ 增量更新管理器功能验证通过")

    def test_crawler_manager_exists(self):
        """测试8: 爬虫管理器存在"""
        manager_file = project_root / "backend" / "crawler" / "crawler_manager.py"
        assert manager_file.exists()

        from backend.crawler.crawler_manager import CrawlerManager, get_crawler_manager
        assert CrawlerManager is not None

        manager = get_crawler_manager()
        assert manager is not None

        logger.info("✅ 爬虫管理器验证通过")

    def test_crawler_manager_registration(self):
        """测试9: 爬虫管理器注册"""
        from backend.crawler.crawler_manager import get_crawler_manager

        manager = get_crawler_manager()

        # 检查已注册的爬虫
        assert 'gov_procurement' in manager.registered_spiders
        assert 'dynamic_platform' in manager.registered_spiders
        assert 'auth_platform' in manager.registered_spiders
        assert 'demo_tender' in manager.registered_spiders

        logger.info("✅ 爬虫注册验证通过")

    def test_crawler_manager_methods(self):
        """测试10: 爬虫管理器方法"""
        from backend.crawler.crawler_manager import get_crawler_manager

        manager = get_crawler_manager()

        # 检查关键方法
        assert hasattr(manager, 'run_spider')
        assert hasattr(manager, 'run_all_spiders')
        assert hasattr(manager, 'get_spider_list')
        assert hasattr(manager, 'get_spider_status')
        assert hasattr(manager, 'enable_spider')
        assert hasattr(manager, 'disable_spider')

        logger.info("✅ 爬虫管理器方法验证通过")

    def test_get_spider_list(self):
        """测试11: 获取爬虫列表"""
        from backend.crawler.crawler_manager import get_crawler_manager

        manager = get_crawler_manager()
        spider_list = manager.get_spider_list()

        assert len(spider_list) >= 3  # 至少3个爬虫

        # 检查每个爬虫的信息完整性
        for spider_info in spider_list:
            assert 'name' in spider_info
            assert 'description' in spider_info
            assert 'type' in spider_info
            assert 'enabled' in spider_info
            assert 'priority' in spider_info

        logger.info(f"✅ 爬虫列表验证通过，共{len(spider_list)}个爬虫")

    def test_crawler_integration(self):
        """测试12: 爬虫框架完整性验证"""
        # 验证所有核心组件都已创建
        components = [
            project_root / "backend" / "crawler" / "spiders" / "gov_procurement_spider.py",
            project_root / "backend" / "crawler" / "spiders" / "dynamic_platform_spider.py",
            project_root / "backend" / "crawler" / "spiders" / "auth_platform_spider.py",
            project_root / "backend" / "crawler" / "incremental_manager.py",
            project_root / "backend" / "crawler" / "crawler_manager.py",
        ]

        for component in components:
            assert component.exists(), f"缺少组件: {component}"

        logger.info(f"✅ 爬虫平台对接完整性验证通过 - 共{len(components)}个组件")


if __name__ == "__main__":
    logger.info("🧪 开始运行爬虫平台测试...")
    pytest.main([__file__, "-v", "-s"])

