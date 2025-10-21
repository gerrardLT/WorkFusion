"""
动态加载平台爬虫
平台类型：动态加载（AJAX/React/Vue）
技术方案：Selenium + Chrome Headless
"""

import scrapy
import re
import time
from datetime import datetime
from urllib.parse import urljoin
from backend.crawler.items import TenderItem


class DynamicPlatformSpider(scrapy.Spider):
    """
    动态加载平台爬虫（示例）

    特点：
    - 使用AJAX加载数据
    - 页面通过JavaScript渲染
    - 需要等待元素加载
    """

    name = 'dynamic_platform'
    allowed_domains = ['example-dynamic.com']  # 示例域名

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 4,
        'SELENIUM_ENABLED': True,  # 启用Selenium
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_url = 'http://www.example-dynamic.com'
        self.max_pages = kwargs.get('max_pages', 5)

        # Selenium配置
        self.use_selenium = True
        self.wait_time = 10  # 等待时间（秒）

    def start_requests(self):
        """生成初始请求"""
        self.logger.info(f'开始爬取动态加载平台，使用Selenium')

        # 列表页URL
        list_url = f'{self.base_url}/tender/list'

        yield scrapy.Request(
            list_url,
            callback=self.parse_list,
            meta={'use_selenium': True},  # 标记使用Selenium
            errback=self.handle_error
        )

    def parse_list(self, response):
        """
        解析列表页

        注意：此时response已经是Selenium渲染后的HTML
        """
        self.logger.info(f'正在解析列表页：{response.url}')

        # 提取项目链接（根据实际HTML结构调整）
        project_links = response.css('div.project-item a::attr(href)').getall()

        self.logger.info(f'找到 {len(project_links)} 个项目链接')

        for link in project_links:
            detail_url = urljoin(self.base_url, link)
            yield scrapy.Request(
                detail_url,
                callback=self.parse_detail,
                meta={'use_selenium': True},
                errback=self.handle_error
            )

        # 处理分页
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                urljoin(self.base_url, next_page),
                callback=self.parse_list,
                meta={'use_selenium': True},
                errback=self.handle_error
            )

    def parse_detail(self, response):
        """解析详情页"""
        self.logger.info(f'正在解析详情页：{response.url}')

        try:
            item = TenderItem()

            # 基本信息
            item['project_id'] = self._generate_project_id(response.url)
            item['title'] = response.css('h1.project-title::text').get() or '未知标题'
            item['project_number'] = response.css('span.project-number::text').get() or ''
            item['source_platform'] = '动态加载平台（示例）'
            item['source_url'] = response.url

            # 金额信息
            item['budget_text'] = response.css('span.budget::text').get() or ''

            # 时间信息
            item['publish_time'] = response.css('span.publish-time::text').get() or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            item['deadline'] = response.css('span.deadline::text').get() or ''

            # 内容信息
            item['content_text'] = ' '.join(response.css('div.content::text').getall())

            # 元数据
            item['crawled_time'] = datetime.now()
            item['spider_name'] = self.name
            item['status'] = '招标中'

            yield item

        except Exception as e:
            self.logger.error(f'解析详情页失败: {response.url}, 错误: {e}')

    def _generate_project_id(self, url: str) -> str:
        """生成项目唯一ID"""
        import hashlib
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:16]

    def handle_error(self, failure):
        """错误处理"""
        self.logger.error(f'请求失败: {failure.request.url}')

