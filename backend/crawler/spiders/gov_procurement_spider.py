"""
中国政府采购网爬虫
平台类型：静态页面
爬取目标：招标公告、中标公告
"""

import scrapy
import re
from datetime import datetime
from urllib.parse import urljoin
from backend.crawler.items import TenderItem, BidResultItem


class GovProcurementSpider(scrapy.Spider):
    """
    中国政府采购网爬虫

    网站：http://www.ccgp.gov.cn
    特点：静态HTML页面，数据结构规范
    """

    name = 'gov_procurement'
    allowed_domains = ['ccgp.gov.cn']

    # 自定义设置
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 8,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 起始URL配置
        self.base_url = 'http://www.ccgp.gov.cn'

        # 招标公告列表页
        self.tender_list_urls = [
            'http://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index={page}&bidSort=0&buyerName=&projectId=&pinMu=0&bidType=0&dbselect=bidx&kw=&start_time=&end_time=&timeType=6&displayZone=&zoneId=&pppStatus=0&agentName=',
        ]

        # 中标公告列表页
        self.bid_result_list_urls = [
            'http://search.ccgp.gov.cn/bxsearch?searchtype=5&page_index={page}&bidSort=0&buyerName=&projectId=&pinMu=0&bidType=0&dbselect=bidx&kw=&start_time=&end_time=&timeType=6&displayZone=&zoneId=&pppStatus=0&agentName=',
        ]

        # 爬取参数
        self.max_pages = kwargs.get('max_pages', 10)  # 最多爬取页数
        self.incremental = kwargs.get('incremental', False)  # 是否增量爬取

    def start_requests(self):
        """生成初始请求"""
        self.logger.info(f'开始爬取中国政府采购网，最多{self.max_pages}页')

        # 爬取招标公告
        for page in range(1, self.max_pages + 1):
            for url_template in self.tender_list_urls:
                url = url_template.format(page=page)
                yield scrapy.Request(
                    url,
                    callback=self.parse_tender_list,
                    meta={'page': page, 'type': 'tender'},
                    errback=self.handle_error
                )

        # 爬取中标公告
        for page in range(1, self.max_pages + 1):
            for url_template in self.bid_result_list_urls:
                url = url_template.format(page=page)
                yield scrapy.Request(
                    url,
                    callback=self.parse_bid_result_list,
                    meta={'page': page, 'type': 'bid_result'},
                    errback=self.handle_error
                )

    def parse_tender_list(self, response):
        """解析招标公告列表页"""
        page = response.meta.get('page', 1)
        self.logger.info(f'正在解析招标公告列表页：第{page}页')

        # 提取所有项目链接
        # 注意：这里使用模拟的选择器，实际使用时需要根据真实HTML结构调整
        project_links = response.css('ul.vT-srch-result-list-bid li a::attr(href)').getall()

        if not project_links:
            # 如果没有找到链接，尝试备用选择器
            project_links = response.xpath('//ul[@class="vT-srch-result-list-bid"]//li//a/@href').getall()

        self.logger.info(f'找到 {len(project_links)} 个招标公告链接')

        for link in project_links:
            detail_url = urljoin(self.base_url, link)
            yield scrapy.Request(
                detail_url,
                callback=self.parse_tender_detail,
                meta={'source_type': 'tender'},
                errback=self.handle_error
            )

    def parse_bid_result_list(self, response):
        """解析中标公告列表页"""
        page = response.meta.get('page', 1)
        self.logger.info(f'正在解析中标公告列表页：第{page}页')

        # 提取所有中标公告链接
        project_links = response.css('ul.vT-srch-result-list-bid li a::attr(href)').getall()

        if not project_links:
            project_links = response.xpath('//ul[@class="vT-srch-result-list-bid"]//li//a/@href').getall()

        self.logger.info(f'找到 {len(project_links)} 个中标公告链接')

        for link in project_links:
            detail_url = urljoin(self.base_url, link)
            yield scrapy.Request(
                detail_url,
                callback=self.parse_bid_result_detail,
                meta={'source_type': 'bid_result'},
                errback=self.handle_error
            )

    def parse_tender_detail(self, response):
        """解析招标公告详情页"""
        self.logger.info(f'正在解析招标公告详情：{response.url}')

        try:
            item = TenderItem()

            # 基本信息
            item['project_id'] = self._generate_project_id(response.url)
            item['title'] = self._extract_title(response)
            item['project_number'] = self._extract_project_number(response)
            item['source_platform'] = '中国政府采购网'
            item['source_url'] = response.url

            # 分类信息
            item['industry'] = self._extract_industry(response)
            item['project_type'] = self._extract_project_type(response)
            item['tender_type'] = self._extract_tender_type(response)

            # 金额信息
            item['budget_text'] = self._extract_budget(response)

            # 地域信息
            province, city = self._extract_location(response)
            item['province'] = province
            item['city'] = city

            # 时间信息
            item['publish_time'] = self._extract_publish_time(response)
            item['deadline'] = self._extract_deadline(response)

            # 内容信息
            item['content'] = self._extract_content_html(response)
            item['content_text'] = self._extract_content_text(response)

            # 联系信息
            item['contact_person'] = self._extract_contact_person(response)
            item['contact_phone'] = self._extract_contact_phone(response)
            item['agent_name'] = self._extract_agent_name(response)

            # 附件信息
            item['attachments'] = self._extract_attachments(response)

            # 状态
            item['status'] = '招标中'

            # 元数据
            item['crawled_time'] = datetime.now()
            item['spider_name'] = self.name

            yield item

        except Exception as e:
            self.logger.error(f'解析招标公告失败: {response.url}, 错误: {e}')

    def parse_bid_result_detail(self, response):
        """解析中标公告详情页"""
        self.logger.info(f'正在解析中标公告详情：{response.url}')

        try:
            item = BidResultItem()

            # 基本信息
            item['project_id'] = self._generate_project_id(response.url)
            item['title'] = self._extract_title(response)
            item['project_number'] = self._extract_project_number(response)
            item['source_platform'] = '中国政府采购网'
            item['source_url'] = response.url

            # 中标信息
            item['winner_name'] = self._extract_winner_name(response)
            item['winner_amount_text'] = self._extract_winner_amount(response)
            item['bid_date'] = self._extract_bid_date(response)

            # 其他投标人
            item['bidders'] = self._extract_other_bidders(response)

            # 内容信息
            item['content'] = self._extract_content_html(response)
            item['content_text'] = self._extract_content_text(response)

            # 元数据
            item['crawled_time'] = datetime.now()
            item['spider_name'] = self.name

            yield item

        except Exception as e:
            self.logger.error(f'解析中标公告失败: {response.url}, 错误: {e}')

    # ==================== 数据提取辅助方法 ====================

    def _generate_project_id(self, url: str) -> str:
        """生成项目唯一ID"""
        import hashlib
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:16]

    def _extract_title(self, response) -> str:
        """提取标题"""
        # 尝试多个选择器
        title = response.css('h2.title::text').get() or \
                response.css('h1::text').get() or \
                response.xpath('//h2[@class="title"]/text()').get() or \
                response.xpath('//title/text()').get()

        return title.strip() if title else '未知标题'

    def _extract_project_number(self, response) -> str:
        """提取项目编号"""
        # 尝试从正文中提取项目编号
        content = response.css('div.vF_detail_content').get() or response.body.decode('utf-8', errors='ignore')

        # 常见项目编号格式
        patterns = [
            r'项目编号[：:]\s*([A-Z0-9-]+)',
            r'招标编号[：:]\s*([A-Z0-9-]+)',
            r'采购项目编号[：:]\s*([A-Z0-9-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return ''

    def _extract_industry(self, response) -> str:
        """提取行业分类"""
        # 从标题或内容中推断行业
        title = self._extract_title(response)

        # 行业关键词映射
        industry_keywords = {
            '电力': ['电力', '电网', '变电', '输电', '配电'],
            '建筑': ['建筑', '工程', '施工', '装修', '房建'],
            'IT': ['软件', '系统', '信息化', '网络', '服务器'],
            '医疗': ['医疗', '医院', '药品', '设备'],
            '教育': ['教育', '学校', '培训', '图书'],
        }

        for industry, keywords in industry_keywords.items():
            if any(keyword in title for keyword in keywords):
                return industry

        return '其他'

    def _extract_project_type(self, response) -> str:
        """提取项目类型"""
        title = self._extract_title(response)

        if '公开招标' in title:
            return '公开招标'
        elif '邀请招标' in title:
            return '邀请招标'
        elif '竞争性谈判' in title:
            return '竞争性谈判'
        elif '询价' in title:
            return '询价'

        return '公开招标'

    def _extract_tender_type(self, response) -> str:
        """提取招标类型"""
        title = self._extract_title(response)

        if '货物' in title:
            return '货物'
        elif '工程' in title:
            return '工程'
        elif '服务' in title:
            return '服务'

        return '货物'

    def _extract_budget(self, response) -> str:
        """提取预算金额"""
        content = response.css('div.vF_detail_content').get() or response.body.decode('utf-8', errors='ignore')

        # 常见金额格式
        patterns = [
            r'预算金额[：:]\s*([\d,.]+)\s*(万元|元)',
            r'采购预算[：:]\s*([\d,.]+)\s*(万元|元)',
            r'项目金额[：:]\s*([\d,.]+)\s*(万元|元)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return f'{match.group(1)}{match.group(2)}'

        return ''

    def _extract_location(self, response) -> tuple:
        """提取地域信息（省份、城市）"""
        content = response.body.decode('utf-8', errors='ignore')

        # 省份列表
        provinces = ['北京', '上海', '天津', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
                    '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
                    '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
                    '内蒙古', '广西', '西藏', '宁夏', '新疆']

        province = ''
        city = ''

        for prov in provinces:
            if prov in content:
                province = prov if prov not in ['北京', '上海', '天津', '重庆'] else f'{prov}市'
                break

        return province, city

    def _extract_publish_time(self, response) -> str:
        """提取发布时间"""
        # 尝试多个选择器
        time_str = response.css('span.time::text').get() or \
                   response.css('div.time::text').get() or \
                   response.xpath('//span[@class="time"]/text()').get()

        if time_str:
            return time_str.strip()

        # 从正文中提取
        content = response.body.decode('utf-8', errors='ignore')
        match = re.search(r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
        if match:
            return match.group(1)

        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _extract_deadline(self, response) -> str:
        """提取截止时间"""
        content = response.body.decode('utf-8', errors='ignore')

        patterns = [
            r'截止时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'投标截止时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return ''

    def _extract_content_html(self, response) -> str:
        """提取HTML内容"""
        content_html = response.css('div.vF_detail_content').get() or \
                       response.css('div.content').get() or \
                       response.xpath('//div[@class="vF_detail_content"]').get()

        return content_html or ''

    def _extract_content_text(self, response) -> str:
        """提取纯文本内容"""
        texts = response.css('div.vF_detail_content::text').getall() or \
                response.css('div.content::text').getall() or \
                response.xpath('//div[@class="vF_detail_content"]//text()').getall()

        return ' '.join(text.strip() for text in texts if text.strip())

    def _extract_contact_person(self, response) -> str:
        """提取联系人"""
        content = response.body.decode('utf-8', errors='ignore')
        match = re.search(r'联系人[：:]\s*([^<\s]+)', content)
        return match.group(1) if match else ''

    def _extract_contact_phone(self, response) -> str:
        """提取联系电话"""
        content = response.body.decode('utf-8', errors='ignore')
        match = re.search(r'联系电话[：:]\s*([\d-]+)', content)
        return match.group(1) if match else ''

    def _extract_agent_name(self, response) -> str:
        """提取代理机构"""
        content = response.body.decode('utf-8', errors='ignore')
        patterns = [
            r'代理机构[：:]\s*([^<\n]+)',
            r'招标代理[：:]\s*([^<\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return ''

    def _extract_attachments(self, response) -> list:
        """提取附件列表"""
        attachments = []

        # 查找所有附件链接
        attachment_links = response.css('a[href$=".pdf"]::attr(href)').getall() + \
                          response.css('a[href$=".doc"]::attr(href)').getall() + \
                          response.css('a[href$=".docx"]::attr(href)').getall()

        for link in attachment_links:
            name = response.css(f'a[href="{link}"]::text').get() or '附件'
            attachments.append({
                'name': name.strip(),
                'url': urljoin(self.base_url, link)
            })

        return attachments

    def _extract_winner_name(self, response) -> str:
        """提取中标单位名称"""
        content = response.body.decode('utf-8', errors='ignore')
        patterns = [
            r'中标单位[：:]\s*([^<\n]+)',
            r'中标供应商[：:]\s*([^<\n]+)',
            r'成交供应商[：:]\s*([^<\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return ''

    def _extract_winner_amount(self, response) -> str:
        """提取中标金额"""
        content = response.body.decode('utf-8', errors='ignore')
        patterns = [
            r'中标金额[：:]\s*([\d,.]+)\s*(万元|元)',
            r'成交金额[：:]\s*([\d,.]+)\s*(万元|元)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return f'{match.group(1)}{match.group(2)}'

        return ''

    def _extract_bid_date(self, response) -> str:
        """提取中标日期"""
        content = response.body.decode('utf-8', errors='ignore')
        match = re.search(r'中标日期[：:]\s*(\d{4}-\d{2}-\d{2})', content)
        return match.group(1) if match else ''

    def _extract_other_bidders(self, response) -> list:
        """提取其他投标人信息"""
        # 这里需要根据实际HTML结构实现
        return []

    def handle_error(self, failure):
        """错误处理"""
        self.logger.error(f'请求失败: {failure.request.url}')
        self.logger.error(f'错误类型: {failure.type}')
        self.logger.error(f'错误信息: {failure.value}')

