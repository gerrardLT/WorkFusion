"""
数据清洗与存储测试
验证T2.1.3任务：数据清洗与存储
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestAdvancedDataCleaner:
    """高级数据清洗器测试"""

    def test_cleaner_exists(self):
        """测试1: 数据清洗器存在"""
        from backend.crawler.data_processor import AdvancedDataCleaner

        cleaner = AdvancedDataCleaner()
        assert cleaner is not None

        logger.info("✅ 数据清洗器验证通过")

    def test_amount_cleaning(self):
        """测试2: 金额清洗"""
        from backend.crawler.data_processor import AdvancedDataCleaner

        cleaner = AdvancedDataCleaner()

        # 测试不同格式
        assert cleaner.clean_amount("100万元") == 100.0
        assert cleaner.clean_amount("1000元") == 0.1
        assert cleaner.clean_amount("10亿元") == 100000.0
        assert abs(cleaner.clean_amount("1,234,567.89元") - 123.4568) < 0.01  # 浮点数精度
        assert abs(cleaner.clean_amount("100.5万") - 100.5) < 0.01

        logger.info("✅ 金额清洗验证通过")

    def test_date_cleaning(self):
        """测试3: 日期清洗"""
        from backend.crawler.data_processor import AdvancedDataCleaner

        cleaner = AdvancedDataCleaner()

        # 测试不同格式
        assert cleaner.clean_date("2024-01-01 12:00:00") == "2024-01-01 12:00:00"
        assert cleaner.clean_date("2024年1月1日") == "2024-01-01"
        assert cleaner.clean_date("2024/01/01") == "2024-01-01"
        assert cleaner.clean_date("20240101") == "2024-01-01"

        logger.info("✅ 日期清洗验证通过")

    def test_province_cleaning(self):
        """测试4: 省份清洗"""
        from backend.crawler.data_processor import AdvancedDataCleaner

        cleaner = AdvancedDataCleaner()

        # 测试不同格式
        assert cleaner.clean_province("北京") == "北京市"
        assert cleaner.clean_province("广东") == "广东省"
        assert cleaner.clean_province("新疆") == "新疆维吾尔自治区"
        assert cleaner.clean_province("北京市") == "北京市"

        logger.info("✅ 省份清洗验证通过")

    def test_text_cleaning(self):
        """测试5: 文本清洗"""
        from backend.crawler.data_processor import AdvancedDataCleaner

        cleaner = AdvancedDataCleaner()

        # 测试文本清洗
        assert cleaner.clean_text("  多余   空白  ") == "多余 空白"
        assert cleaner.clean_text("换行\n\n测试\r\n文本") == "换行\n测试\n文本"

        logger.info("✅ 文本清洗验证通过")

    def test_phone_extraction(self):
        """测试6: 电话提取"""
        from backend.crawler.data_processor import AdvancedDataCleaner

        cleaner = AdvancedDataCleaner()

        # 测试电话提取
        assert cleaner.extract_phone("联系电话：13812345678") == "13812345678"
        assert cleaner.extract_phone("电话：010-12345678") == "010-12345678"

        logger.info("✅ 电话提取验证通过")

    def test_email_extraction(self):
        """测试7: 邮箱提取"""
        from backend.crawler.data_processor import AdvancedDataCleaner

        cleaner = AdvancedDataCleaner()

        # 测试邮箱提取
        assert cleaner.extract_email("联系邮箱：test@example.com") == "test@example.com"
        assert cleaner.extract_email("Email: contact@company.com.cn") == "contact@company.com.cn"

        logger.info("✅ 邮箱提取验证通过")


class TestCrossPlatformDeduplicator:
    """跨平台去重器测试"""

    def test_deduplicator_exists(self):
        """测试8: 去重器存在"""
        from backend.crawler.data_processor import CrossPlatformDeduplicator

        dedup = CrossPlatformDeduplicator()
        assert dedup is not None

        logger.info("✅ 去重器验证通过")

    def test_url_deduplication(self):
        """测试9: URL去重"""
        from backend.crawler.data_processor import CrossPlatformDeduplicator

        dedup = CrossPlatformDeduplicator()

        url = "http://example.com/project/123"
        title = "测试项目"

        # 第一次不重复
        is_dup, reason = dedup.is_duplicate(url, title)
        assert is_dup == False

        # 标记为已见
        dedup.mark_seen(url, title)

        # 第二次重复
        is_dup, reason = dedup.is_duplicate(url, title)
        assert is_dup == True
        assert 'URL' in reason

        logger.info("✅ URL去重验证通过")

    def test_similarity_deduplication(self):
        """测试10: 相似度去重"""
        from backend.crawler.data_processor import CrossPlatformDeduplicator

        dedup = CrossPlatformDeduplicator(similarity_threshold=0.85)

        # 两个相似的标题
        url1 = "http://example.com/p1"
        url2 = "http://example.com/p2"  # 不同URL
        title1 = "某某电力公司招标项目"
        title2 = "某某电力公司招标项目公告"  # 非常相似
        budget = 100.0

        # 第一个项目
        dedup.mark_seen(url1, title1, budget)

        # 第二个项目（标题相似，金额相同）
        is_dup, reason = dedup.is_duplicate(url2, title2, budget)
        assert is_dup == True  # 应该被识别为重复

        logger.info("✅ 相似度去重验证通过")

    def test_similarity_calculation(self):
        """测试11: 相似度计算"""
        from backend.crawler.data_processor import CrossPlatformDeduplicator

        dedup = CrossPlatformDeduplicator()

        # 测试完全相同
        sim1 = dedup._calculate_similarity("测试文本", "测试文本")
        assert sim1 == 1.0

        # 测试完全不同
        sim2 = dedup._calculate_similarity("测试文本", "完全不同")
        assert sim2 < 0.5

        # 测试部分相似
        sim3 = dedup._calculate_similarity("某某公司招标项目", "某某公司招标项目公告")
        assert 0.8 < sim3 < 1.0

        logger.info("✅ 相似度计算验证通过")


class TestDataNormalizer:
    """数据规范化器测试"""

    def test_normalizer_exists(self):
        """测试12: 规范化器存在"""
        from backend.crawler.data_processor import DataNormalizer

        normalizer = DataNormalizer()
        assert normalizer is not None

        logger.info("✅ 规范化器验证通过")

    def test_tender_item_normalization(self):
        """测试13: 招标项目规范化"""
        from backend.crawler.data_processor import DataNormalizer

        normalizer = DataNormalizer()

        # 模拟原始数据
        raw_data = {
            'title': '  某某项目招标  ',
            'budget_text': '100万元',
            'publish_time': '2024年1月1日',
            'province': '北京',
            'city': '北京',
            'content_text': '项目内容\n\n多余空白'
        }

        # 规范化
        normalized = normalizer.normalize_tender_item(raw_data)

        # 验证结果
        assert normalized['title'] == '某某项目招标'
        assert normalized['budget'] == 100.0
        assert normalized['publish_time'] == '2024-01-01'
        assert normalized['province'] == '北京市'
        assert normalized['city'] == '北京市'

        logger.info("✅ 招标项目规范化验证通过")

    def test_duplicate_check_integration(self):
        """测试14: 去重检查集成"""
        from backend.crawler.data_processor import DataNormalizer

        normalizer = DataNormalizer()

        item1 = {
            'source_url': 'http://example.com/p1',
            'title': '测试项目1',
            'budget': 100.0
        }

        item2 = {
            'source_url': 'http://example.com/p2',
            'title': '测试项目1',  # 标题相同
            'budget': 100.0  # 金额相同
        }

        # 第一个不重复
        is_dup1, _ = normalizer.check_duplicate(item1)
        assert is_dup1 == False
        normalizer.mark_processed(item1)

        # 第二个应该重复（标题+金额相似）
        is_dup2, reason = normalizer.check_duplicate(item2)
        assert is_dup2 == True

        logger.info("✅ 去重检查集成验证通过")


class TestEnhancedPipelines:
    """增强版Pipeline测试"""

    def test_enhanced_cleaning_pipeline_exists(self):
        """测试15: 增强版清洗Pipeline存在"""
        from backend.crawler.pipelines import EnhancedDataCleaningPipeline

        pipeline = EnhancedDataCleaningPipeline()
        assert pipeline is not None
        assert hasattr(pipeline, 'process_item')

        logger.info("✅ 增强版清洗Pipeline验证通过")

    def test_cross_platform_duplicates_pipeline_exists(self):
        """测试16: 跨平台去重Pipeline存在"""
        from backend.crawler.pipelines import CrossPlatformDuplicatesPipeline

        pipeline = CrossPlatformDuplicatesPipeline()
        assert pipeline is not None
        assert hasattr(pipeline, 'process_item')

        logger.info("✅ 跨平台去重Pipeline验证通过")

    def test_pipeline_integration(self):
        """测试17: Pipeline完整性验证"""
        # 验证所有增强组件都已创建
        components = [
            project_root / "backend" / "crawler" / "data_processor.py",
            project_root / "backend" / "crawler" / "pipelines.py",
        ]

        for component in components:
            assert component.exists(), f"缺少组件: {component}"

        logger.info("✅ Pipeline完整性验证通过")


if __name__ == "__main__":
    logger.info("🧪 开始运行数据处理测试...")
    pytest.main([__file__, "-v", "-s"])

