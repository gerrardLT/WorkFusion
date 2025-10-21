"""
爬虫框架测试
验证T2.1.1任务：爬虫框架搭建
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestCrawlerFramework:
    """爬虫框架测试类"""

    def test_crawler_directory_exists(self):
        """测试1: 爬虫目录存在"""
        crawler_dir = project_root / "backend" / "crawler"
        assert crawler_dir.exists()
        assert crawler_dir.is_dir()

        spiders_dir = crawler_dir / "spiders"
        assert spiders_dir.exists()

        logger.info("✅ 爬虫目录结构验证通过")

    def test_items_module_exists(self):
        """测试2: Items模块存在"""
        items_file = project_root / "backend" / "crawler" / "items.py"
        assert items_file.exists()

        from backend.crawler.items import TenderItem, BidResultItem
        assert TenderItem is not None
        assert BidResultItem is not None

        logger.info("✅ Items模块验证通过")

    def test_tender_item_fields(self):
        """测试3: TenderItem字段完整性"""
        from backend.crawler.items import TenderItem

        required_fields = [
            'project_id', 'title', 'source_platform', 'source_url',
            'industry', 'budget', 'province', 'city',
            'publish_time', 'deadline', 'content_text'
        ]

        item = TenderItem()
        for field in required_fields:
            assert field in item.fields

        logger.info(f"✅ TenderItem包含{len(required_fields)}个必需字段")

    def test_middlewares_module_exists(self):
        """测试4: Middlewares模块存在"""
        middlewares_file = project_root / "backend" / "crawler" / "middlewares.py"
        assert middlewares_file.exists()

        from backend.crawler.middlewares import (
            RandomUserAgentMiddleware,
            RandomDelayMiddleware,
            ProxyMiddleware,
            AntiSpiderMiddleware
        )

        assert RandomUserAgentMiddleware is not None
        assert RandomDelayMiddleware is not None
        assert ProxyMiddleware is not None
        assert AntiSpiderMiddleware is not None

        logger.info("✅ Middlewares模块验证通过")

    def test_user_agent_middleware(self):
        """测试5: User-Agent中间件"""
        from backend.crawler.middlewares import RandomUserAgentMiddleware

        middleware = RandomUserAgentMiddleware()
        assert hasattr(middleware, 'USER_AGENTS')
        assert len(middleware.USER_AGENTS) > 0

        logger.info(f"✅ User-Agent中间件包含{len(middleware.USER_AGENTS)}个UA")

    def test_pipelines_module_exists(self):
        """测试6: Pipelines模块存在"""
        pipelines_file = project_root / "backend" / "crawler" / "pipelines.py"
        assert pipelines_file.exists()

        from backend.crawler.pipelines import (
            DataCleaningPipeline,
            DuplicatesPipeline,
            DatabasePipeline,
            JsonExportPipeline
        )

        assert DataCleaningPipeline is not None
        assert DuplicatesPipeline is not None
        assert DatabasePipeline is not None
        assert JsonExportPipeline is not None

        logger.info("✅ Pipelines模块验证通过")

    def test_data_cleaning_pipeline(self):
        """测试7: 数据清洗Pipeline"""
        from backend.crawler.pipelines import DataCleaningPipeline

        pipeline = DataCleaningPipeline()

        # 测试金额解析
        assert pipeline._parse_amount("100万元") == 100.0
        assert pipeline._parse_amount("1000元") == 0.1
        assert pipeline._parse_amount("10亿元") == 100000.0

        logger.info("✅ 数据清洗Pipeline验证通过")

    def test_settings_module_exists(self):
        """测试8: Settings模块存在"""
        settings_file = project_root / "backend" / "crawler" / "settings.py"
        assert settings_file.exists()

        logger.info("✅ Settings模块验证通过")

    def test_settings_configuration(self):
        """测试9: Settings配置验证"""
        from backend.crawler import settings

        assert hasattr(settings, 'BOT_NAME')
        assert hasattr(settings, 'ITEM_PIPELINES')
        assert hasattr(settings, 'DOWNLOADER_MIDDLEWARES')

        logger.info("✅ Settings配置验证通过")

    def test_spider_module_exists(self):
        """测试10: Spider模块存在"""
        spider_file = project_root / "backend" / "crawler" / "spiders" / "tender_spider.py"
        assert spider_file.exists()

        from backend.crawler.spiders.tender_spider import TenderSpider, DemoTenderSpider
        assert TenderSpider is not None
        assert DemoTenderSpider is not None

        logger.info("✅ Spider模块验证通过")

    def test_demo_spider_attributes(self):
        """测试11: DemoSpider属性"""
        from backend.crawler.spiders.tender_spider import DemoTenderSpider

        spider = DemoTenderSpider()
        assert spider.name == 'demo_tender'
        assert hasattr(spider, 'start_requests')

        logger.info("✅ DemoSpider属性验证通过")

    def test_framework_integration(self):
        """测试12: 框架完整性验证"""
        # 验证所有核心组件都已创建
        components = [
            project_root / "backend" / "crawler" / "__init__.py",
            project_root / "backend" / "crawler" / "items.py",
            project_root / "backend" / "crawler" / "middlewares.py",
            project_root / "backend" / "crawler" / "pipelines.py",
            project_root / "backend" / "crawler" / "settings.py",
            project_root / "backend" / "crawler" / "spiders" / "__init__.py",
            project_root / "backend" / "crawler" / "spiders" / "tender_spider.py",
        ]

        for component in components:
            assert component.exists(), f"缺少组件: {component}"

        logger.info(f"✅ 框架完整性验证通过 - 共{len(components)}个组件")


if __name__ == "__main__":
    logger.info("🧪 开始运行爬虫框架测试...")
    pytest.main([__file__, "-v", "-s"])

