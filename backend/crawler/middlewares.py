"""
Scrapy Middlewares
实现反爬措施和请求处理
"""

import random
import logging
import time
from typing import Optional
from scrapy import signals
from scrapy.http import Request, Response
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

logger = logging.getLogger(__name__)


class RandomUserAgentMiddleware:
    """随机User-Agent中间件"""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def process_request(self, request: Request, spider):
        """为每个请求随机选择User-Agent"""
        user_agent = random.choice(self.USER_AGENTS)
        request.headers['User-Agent'] = user_agent


class RandomDelayMiddleware:
    """随机延迟中间件"""

    def __init__(self, min_delay=1, max_delay=3):
        self.min_delay = min_delay
        self.max_delay = max_delay

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            min_delay=crawler.settings.getfloat('RANDOM_DELAY_MIN', 1),
            max_delay=crawler.settings.getfloat('RANDOM_DELAY_MAX', 3)
        )

    def process_request(self, request: Request, spider):
        """随机延迟，模拟人工操作"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)


class ProxyMiddleware:
    """代理IP中间件"""

    def __init__(self, proxy_list: Optional[list] = None):
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0

    @classmethod
    def from_crawler(cls, crawler):
        # 从配置中读取代理列表
        proxy_list = crawler.settings.getlist('PROXY_LIST', [])
        return cls(proxy_list=proxy_list)

    def process_request(self, request: Request, spider):
        """为请求设置代理"""
        if not self.proxy_list:
            return

        # 轮询使用代理
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)

        request.meta['proxy'] = proxy
        logger.debug(f'使用代理: {proxy}')


class CustomRetryMiddleware(RetryMiddleware):
    """自定义重试中间件"""

    def process_response(self, request: Request, response: Response, spider):
        """处理响应，判断是否需要重试"""
        if request.meta.get('dont_retry', False):
            return response

        # 如果被反爬，尝试重试
        if response.status in [403, 429, 503]:
            reason = response_status_message(response.status)
            logger.warning(f'请求被拒绝 ({response.status}): {reason}，准备重试')
            return self._retry(request, reason, spider) or response

        return response

    def process_exception(self, request: Request, exception, spider):
        """处理异常，判断是否需要重试"""
        if isinstance(exception, Exception):
            logger.warning(f'请求异常: {exception}，准备重试')
            return self._retry(request, str(exception), spider)


class AntiSpiderMiddleware:
    """反反爬中间件"""

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        logger.info(f'Spider {spider.name} 已开启反反爬中间件')

    def process_request(self, request: Request, spider):
        """添加反反爬措施"""
        # 添加常见的请求头
        request.headers.setdefault('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        request.headers.setdefault('Accept-Language', 'zh-CN,zh;q=0.9,en;q=0.8')
        request.headers.setdefault('Accept-Encoding', 'gzip, deflate, br')
        request.headers.setdefault('Connection', 'keep-alive')
        request.headers.setdefault('Upgrade-Insecure-Requests', '1')

        # 添加Referer（如果之前有访问记录）
        if request.meta.get('referrer'):
            request.headers.setdefault('Referer', request.meta['referrer'])


class SeleniumMiddleware:
    """Selenium中间件（用于处理动态加载页面）"""

    def __init__(self, driver_path: Optional[str] = None):
        self.driver_path = driver_path
        self.driver = None

    @classmethod
    def from_crawler(cls, crawler):
        driver_path = crawler.settings.get('SELENIUM_DRIVER_PATH')
        return cls(driver_path=driver_path)

    def process_request(self, request: Request, spider):
        """
        对于需要Selenium的请求进行处理
        使用方法：在Request的meta中设置 use_selenium=True
        """
        if not request.meta.get('use_selenium', False):
            return None

        # 这里简化实现，实际使用时需要初始化Selenium WebDriver
        logger.info(f'使用Selenium处理动态页面: {request.url}')

        # 实际实现应该：
        # 1. 使用Selenium访问页面
        # 2. 等待页面加载完成
        # 3. 执行JavaScript等操作
        # 4. 获取页面源码
        # 5. 返回HtmlResponse

        # 这里返回None表示让Scrapy的下载器继续处理
        return None

