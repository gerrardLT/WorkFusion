"""
招标信息爬虫示例
演示如何使用爬虫框架
"""

import scrapy
from datetime import datetime
from backend.crawler.items import TenderItem


class TenderSpider(scrapy.Spider):
    """招标信息爬虫（示例）"""

    name = 'tender_spider'
    allowed_domains = ['example.com']  # 实际使用时替换为真实域名

    # 起始URL列表
    start_urls = [
        # 'http://www.example.com/tender/list.html',  # 实际使用时替换
    ]

    # 自定义设置
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 8,
    }

    def parse(self, response):
        """
        解析列表页

        这是一个示例方法，实际使用时需要根据目标网站的HTML结构编写
        """
        self.logger.info(f'正在解析列表页: {response.url}')

        # 示例：提取所有项目链接
        for project_link in response.css('a.project-link::attr(href)').getall():
            yield response.follow(project_link, callback=self.parse_detail)

        # 示例：翻页
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_detail(self, response):
        """
        解析详情页

        实际使用时需要根据目标网站的HTML结构提取数据
        """
        self.logger.info(f'正在解析详情页: {response.url}')

        # 创建Item
        item = TenderItem()

        # 示例：提取数据（需要根据实际HTML结构修改选择器）
        item['project_id'] = self._generate_project_id(response.url)
        item['title'] = response.css('h1.title::text').get()
        item['project_number'] = response.css('span.project-number::text').get()
        item['source_platform'] = '示例平台'
        item['source_url'] = response.url

        # 提取分类信息
        item['industry'] = response.css('span.industry::text').get()
        item['project_type'] = response.css('span.project-type::text').get()

        # 提取金额
        item['budget_text'] = response.css('span.budget::text').get()

        # 提取地域
        item['province'] = response.css('span.province::text').get()
        item['city'] = response.css('span.city::text').get()

        # 提取时间
        item['publish_time'] = response.css('span.publish-time::text').get()
        item['deadline'] = response.css('span.deadline::text').get()

        # 提取内容
        item['content'] = response.css('div.content').get()
        item['content_text'] = response.css('div.content::text').getall()
        item['content_text'] = ' '.join(item['content_text']) if item['content_text'] else ''

        # 元数据
        item['crawled_time'] = datetime.now()
        item['spider_name'] = self.name

        yield item

    def _generate_project_id(self, url: str) -> str:
        """生成项目唯一ID"""
        import hashlib
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:16]


class DemoTenderSpider(scrapy.Spider):
    """
    演示爬虫（用于测试框架功能）
    爬取一个简单的测试页面
    """

    name = 'demo_tender'

    def start_requests(self):
        """生成测试数据"""
        # 这是一个演示爬虫，生成测试数据
        self.logger.info('演示爬虫启动，生成测试数据...')

        # 直接yield测试数据
        for i in range(1, 4):
            item = TenderItem()
            item['project_id'] = f'demo_{i}'
            item['title'] = f'测试招标项目{i}'
            item['project_number'] = f'TEST-2024-{i:03d}'
            item['source_platform'] = '测试平台'
            item['source_url'] = f'http://example.com/project/{i}'
            item['industry'] = '电力'
            item['project_type'] = '公开招标'
            item['budget_text'] = f'{i * 100}万元'
            item['province'] = '北京市'
            item['city'] = '北京市'
            item['publish_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            item['content_text'] = f'这是测试项目{i}的详细内容...'
            item['status'] = '招标中'
            item['crawled_time'] = datetime.now()
            item['spider_name'] = self.name

            yield item

        # 返回空Response以满足Scrapy要求
        return []

