# 招标信息爬虫框架

基于Scrapy的招标信息爬虫系统，支持多源数据采集、智能去重和数据清洗。

## 📁 项目结构

```
backend/crawler/
├── __init__.py              # 模块初始化
├── items.py                 # 数据模型定义
├── middlewares.py           # 中间件（反爬措施）
├── pipelines.py             # 数据处理管道
├── settings.py              # Scrapy配置
└── spiders/                 # 爬虫目录
    ├── __init__.py
    └── tender_spider.py     # 示例爬虫
```

## ⚙️ 核心功能

### 1. 数据模型

#### TenderItem（招标信息）
- 基本信息：标题、项目编号、来源平台、URL
- 分类信息：行业、项目类型、招标类型
- 金额信息：预算金额
- 地域信息：省份、城市、区县
- 时间信息：发布时间、截止时间、开标时间
- 内容信息：招标公告正文、摘要
- 联系信息：联系人、电话、邮箱、代理机构

#### BidResultItem（中标结果）
- 关联信息：项目ID、招标项目ID
- 中标信息：中标单位、中标金额、中标日期
- 其他投标人信息

### 2. 反爬中间件

- **RandomUserAgentMiddleware**: 随机User-Agent（6种）
- **RandomDelayMiddleware**: 随机延迟（1-3秒可配置）
- **ProxyMiddleware**: 代理IP轮询
- **CustomRetryMiddleware**: 自定义重试（403/429/503自动重试）
- **AntiSpiderMiddleware**: 反反爬措施（模拟浏览器请求头）
- **SeleniumMiddleware**: 动态页面支持（预留）

### 3. 数据处理Pipeline

- **DataCleaningPipeline**: 数据清洗
  - 文本去噪
  - 金额标准化（元/万元/亿元 → 万元）
  - 日期解析（多种格式）
  - 地域标准化

- **DuplicatesPipeline**: 去重
  - 基于URL+关键字段的MD5哈希
  - 内存去重
  - 统计信息

- **DatabasePipeline**: 数据库存储
  - SQLite存储
  - 自动创建表
  - 支持INSERT OR REPLACE

- **JsonExportPipeline**: JSON备份
  - 导出完整数据到JSON文件

## 🚀 快速开始

### 安装依赖

```bash
pip install scrapy itemadapter
```

### 运行演示爬虫

```bash
# 在项目根目录执行
cd backend/crawler
scrapy crawl demo_tender
```

### 创建新爬虫

```bash
# 创建新爬虫
scrapy genspider my_spider example.com

# 或手动创建Python文件
# backend/crawler/spiders/my_spider.py
```

### 示例爬虫代码

```python
import scrapy
from datetime import datetime
from backend.crawler.items import TenderItem

class MySpider(scrapy.Spider):
    name = 'my_spider'
    allowed_domains = ['example.com']
    start_urls = ['http://www.example.com/tender/list']

    def parse(self, response):
        # 提取列表页链接
        for link in response.css('a.project-link::attr(href)').getall():
            yield response.follow(link, callback=self.parse_detail)

        # 翻页
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_detail(self, response):
        # 创建Item
        item = TenderItem()

        # 提取数据（根据实际HTML结构修改选择器）
        item['title'] = response.css('h1.title::text').get()
        item['project_number'] = response.css('span.number::text').get()
        item['source_platform'] = '示例平台'
        item['source_url'] = response.url
        item['budget_text'] = response.css('span.budget::text').get()
        item['publish_time'] = response.css('span.time::text').get()
        item['content_text'] = ' '.join(response.css('div.content::text').getall())
        item['crawled_time'] = datetime.now()
        item['spider_name'] = self.name

        yield item
```

## 🔧 配置说明

### settings.py 关键配置

```python
# 并发请求数
CONCURRENT_REQUESTS = 16

# 下载延迟（秒）
DOWNLOAD_DELAY = 2

# 随机延迟范围
RANDOM_DELAY_MIN = 1
RANDOM_DELAY_MAX = 3

# 启用的Pipeline
ITEM_PIPELINES = {
    'backend.crawler.pipelines.DataCleaningPipeline': 300,
    'backend.crawler.pipelines.DuplicatesPipeline': 400,
    'backend.crawler.pipelines.DatabasePipeline': 500,
    'backend.crawler.pipelines.JsonExportPipeline': 600,
}

# 数据库路径
DATABASE_PATH = 'data/stock_data/databases/tender_crawler.db'

# JSON导出路径
JSON_EXPORT_PATH = 'data/stock_data/crawler_backup.json'
```

## 📊 数据存储

### SQLite数据库

**tender_projects表**（招标项目）
- project_id: 项目唯一ID
- title: 标题
- project_number: 项目编号
- source_platform: 来源平台
- budget: 预算金额（万元）
- province: 省份
- city: 城市
- publish_time: 发布时间
- deadline: 截止时间
- content_text: 内容文本
- data_hash: 数据哈希（用于去重）

**bid_results表**（中标结果）
- tender_project_id: 关联的项目ID（外键）
- winner_name: 中标单位
- winner_amount: 中标金额（万元）
- bid_date: 中标日期
- data_hash: 数据哈希（用于去重）

## 🧪 测试

运行测试：

```bash
python -m pytest tests/test_crawler_framework.py -v
```

测试覆盖：
- 目录结构验证
- Items模块验证
- Middlewares模块验证
- Pipelines模块验证
- Settings配置验证
- Spider模块验证
- 框架完整性验证

## 🛡️ 反爬策略

1. **User-Agent轮换**: 6种主流浏览器UA随机选择
2. **请求延迟**: 1-3秒随机延迟，模拟人工操作
3. **代理IP**: 支持代理IP池轮询（需配置）
4. **自动重试**: 遇到403/429/503自动重试
5. **请求头伪装**: 添加完整的浏览器请求头
6. **限速机制**: AutoThrottle自动调节请求速度

## ⚠️ 注意事项

1. **遵守robots.txt**: 生产环境建议设置 `ROBOTSTXT_OBEY = True`
2. **合理控制并发**: 避免对目标网站造成压力
3. **代理IP**: 如需大量爬取，建议配置代理IP池
4. **动态页面**: 对于JS渲染页面，启用Selenium中间件
5. **数据备份**: 建议同时启用数据库和JSON导出

## 📈 性能优化

- 启用HTTP缓存（24小时）
- 使用AutoThrottle自动限速
- 支持分布式爬取（Scrapy-Redis，需配置）
- 数据库批量插入优化

## 🔗 扩展功能

### 分布式爬取（可选）

安装依赖：
```bash
pip install scrapy-redis
```

修改settings.py：
```python
REDIS_URL = 'redis://localhost:6379'
SCHEDULER = 'scrapy_redis.scheduler.Scheduler'
DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'
```

### Selenium支持（可选）

安装依赖：
```bash
pip install selenium
```

配置WebDriver路径：
```python
SELENIUM_DRIVER_PATH = '/path/to/chromedriver'
```

使用方法：
```python
# 在Request的meta中设置
yield scrapy.Request(url, meta={'use_selenium': True})
```

## 📝 开发规范

1. **新爬虫命名**: 使用小写+下划线，如 `my_tender_spider`
2. **选择器优先级**: CSS选择器 > XPath
3. **数据验证**: 在Spider中进行基本验证，Pipeline中进行深度清洗
4. **日志记录**: 使用 `self.logger` 记录关键信息
5. **异常处理**: 捕获并记录异常，避免爬虫崩溃

## 📄 许可证

MIT License

## 👥 维护者

招投标AI系统开发团队

---

**最后更新**: 2025年10月15日

