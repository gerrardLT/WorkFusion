"""
需登录平台爬虫
平台类型：需要登录认证
技术方案：Cookie管理 + Session维持
"""

import scrapy
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from backend.crawler.items import TenderItem


class AuthPlatformSpider(scrapy.Spider):
    """
    需登录平台爬虫（示例）

    特点：
    - 需要登录才能访问
    - 使用Cookie维持会话
    - 定期刷新登录状态
    """

    name = 'auth_platform'
    allowed_domains = ['example-auth.com']  # 示例域名

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 8,
        'COOKIES_ENABLED': True,  # 启用Cookie
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_url = 'http://www.example-auth.com'
        self.login_url = f'{self.base_url}/login'
        self.max_pages = kwargs.get('max_pages', 10)

        # 登录凭据（实际使用时应从配置文件或环境变量读取）
        self.username = kwargs.get('username', os.getenv('AUTH_USERNAME', ''))
        self.password = kwargs.get('password', os.getenv('AUTH_PASSWORD', ''))

        # Cookie存储路径
        self.cookie_file = Path('data/cookies/auth_platform_cookies.json')
        self.cookie_file.parent.mkdir(parents=True, exist_ok=True)

        # 是否已登录
        self.is_logged_in = False

    def start_requests(self):
        """生成初始请求"""
        self.logger.info('开始爬取需登录平台')

        # 尝试加载已保存的Cookie
        if self._load_cookies():
            self.logger.info('使用已保存的Cookie')
            self.is_logged_in = True
            yield from self._start_crawling()
        else:
            # 没有Cookie，需要先登录
            self.logger.info('没有有效Cookie，开始登录')
            yield scrapy.Request(
                self.login_url,
                callback=self.parse_login_page,
                errback=self.handle_error
            )

    def parse_login_page(self, response):
        """解析登录页面，提交登录表单"""
        self.logger.info('正在登录...')

        # 构造登录数据（根据实际表单字段调整）
        login_data = {
            'username': self.username,
            'password': self.password,
            # 可能还需要其他字段，如验证码、csrf_token等
        }

        # 提交登录请求
        yield scrapy.FormRequest.from_response(
            response,
            formdata=login_data,
            callback=self.after_login,
            errback=self.handle_error
        )

    def after_login(self, response):
        """登录后的处理"""
        # 检查是否登录成功
        if self._check_login_success(response):
            self.logger.info('✅ 登录成功')
            self.is_logged_in = True

            # 保存Cookie
            self._save_cookies(response)

            # 开始爬取
            yield from self._start_crawling()
        else:
            self.logger.error('❌ 登录失败')
            # 可以在这里实现重试逻辑

    def _start_crawling(self):
        """开始爬取数据"""
        self.logger.info('开始爬取项目数据')

        # 列表页URL
        list_url = f'{self.base_url}/tender/list'

        for page in range(1, self.max_pages + 1):
            yield scrapy.Request(
                f'{list_url}?page={page}',
                callback=self.parse_list,
                meta={'page': page},
                errback=self.handle_error
            )

    def parse_list(self, response):
        """解析列表页"""
        page = response.meta.get('page', 1)
        self.logger.info(f'正在解析列表页：第{page}页')

        # 检查是否需要重新登录
        if self._need_relogin(response):
            self.logger.warning('会话已过期，需要重新登录')
            self.is_logged_in = False
            yield scrapy.Request(
                self.login_url,
                callback=self.parse_login_page,
                dont_filter=True
            )
            return

        # 提取项目链接
        project_links = response.css('a.project-link::attr(href)').getall()

        self.logger.info(f'找到 {len(project_links)} 个项目链接')

        for link in project_links:
            detail_url = urljoin(self.base_url, link)
            yield scrapy.Request(
                detail_url,
                callback=self.parse_detail,
                errback=self.handle_error
            )

    def parse_detail(self, response):
        """解析详情页"""
        self.logger.info(f'正在解析详情页：{response.url}')

        # 检查是否需要重新登录
        if self._need_relogin(response):
            self.logger.warning('会话已过期')
            return

        try:
            item = TenderItem()

            # 基本信息
            item['project_id'] = self._generate_project_id(response.url)
            item['title'] = response.css('h1.title::text').get() or '未知标题'
            item['project_number'] = response.css('span.number::text').get() or ''
            item['source_platform'] = '需登录平台（示例）'
            item['source_url'] = response.url

            # 金额信息
            item['budget_text'] = response.css('span.budget::text').get() or ''

            # 时间信息
            item['publish_time'] = response.css('span.time::text').get() or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

    # ==================== Cookie管理 ====================

    def _load_cookies(self) -> bool:
        """加载已保存的Cookie"""
        if not self.cookie_file.exists():
            return False

        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)

            # 检查Cookie是否过期
            if self._is_cookie_expired(cookies_data):
                self.logger.info('Cookie已过期')
                return False

            # 加载Cookie到Spider
            # 注意：这里需要在start_requests中通过Request的cookies参数传递
            self.cookies = cookies_data.get('cookies', {})
            return True

        except Exception as e:
            self.logger.error(f'加载Cookie失败: {e}')
            return False

    def _save_cookies(self, response):
        """保存Cookie到文件"""
        try:
            cookies = {}
            for cookie in response.headers.getlist('Set-Cookie'):
                # 解析Cookie（简化实现）
                cookie_str = cookie.decode('utf-8')
                if '=' in cookie_str:
                    name, value = cookie_str.split('=', 1)
                    cookies[name] = value.split(';')[0]

            cookies_data = {
                'cookies': cookies,
                'timestamp': datetime.now().isoformat()
            }

            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f'Cookie已保存到: {self.cookie_file}')

        except Exception as e:
            self.logger.error(f'保存Cookie失败: {e}')

    def _is_cookie_expired(self, cookies_data: dict) -> bool:
        """检查Cookie是否过期"""
        if 'timestamp' not in cookies_data:
            return True

        # 简单实现：超过24小时视为过期
        from datetime import timedelta
        saved_time = datetime.fromisoformat(cookies_data['timestamp'])
        return datetime.now() - saved_time > timedelta(hours=24)

    def _check_login_success(self, response) -> bool:
        """检查登录是否成功"""
        # 根据实际页面特征判断
        # 例如：检查是否包含"退出登录"链接
        return bool(response.css('a.logout').get()) or \
               '退出' in response.text or \
               'logout' in response.url.lower()

    def _need_relogin(self, response) -> bool:
        """检查是否需要重新登录"""
        # 根据实际页面特征判断
        # 例如：检查是否跳转到登录页
        return 'login' in response.url.lower() or \
               '请登录' in response.text or \
               bool(response.css('form#login-form').get())

    def _generate_project_id(self, url: str) -> str:
        """生成项目唯一ID"""
        import hashlib
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:16]

    def handle_error(self, failure):
        """错误处理"""
        self.logger.error(f'请求失败: {failure.request.url}')

    def closed(self, reason):
        """Spider关闭时的清理工作"""
        self.logger.info(f'Spider关闭，原因: {reason}')

