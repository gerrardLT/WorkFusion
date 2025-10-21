"""
Scrapy Settings
爬虫配置文件
"""

# Scrapy项目设置
BOT_NAME = 'tender_crawler'
SPIDER_MODULES = ['backend.crawler.spiders']
NEWSPIDER_MODULE = 'backend.crawler.spiders'

# 遵守robots.txt规则（生产环境建议设为True）
ROBOTSTXT_OBEY = False

# 并发请求数
CONCURRENT_REQUESTS = 16

# 下载延迟（秒）
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# 随机延迟范围
RANDOM_DELAY_MIN = 1
RANDOM_DELAY_MAX = 3

# 并发域名请求数
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# 禁用Cookies（某些站点需要启用）
COOKIES_ENABLED = False

# 禁用Telnet Console
TELNETCONSOLE_ENABLED = False

# 默认请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 启用或禁用爬虫中间件
SPIDER_MIDDLEWARES = {
    'backend.crawler.middlewares.AntiSpiderMiddleware': 543,
}

# 启用或禁用下载器中间件
DOWNLOADER_MIDDLEWARES = {
    'backend.crawler.middlewares.RandomUserAgentMiddleware': 400,
    'backend.crawler.middlewares.RandomDelayMiddleware': 410,
    'backend.crawler.middlewares.ProxyMiddleware': 420,
    'backend.crawler.middlewares.CustomRetryMiddleware': 550,
}

# 启用或禁用扩展
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}

# 配置Item Pipeline
# 注意：数字越小优先级越高
ITEM_PIPELINES = {
    'backend.crawler.pipelines.EnhancedDataCleaningPipeline': 300,  # 增强版数据清洗
    'backend.crawler.pipelines.CrossPlatformDuplicatesPipeline': 400,  # 跨平台去重
    'backend.crawler.pipelines.DatabasePipeline': 500,  # 数据库存储
    'backend.crawler.pipelines.JsonExportPipeline': 600,  # JSON备份
}

# 启用和配置AutoThrottle扩展（自动限速）
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# 启用和配置HTTP缓存
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24小时
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 408, 429]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# 超时设置
DOWNLOAD_TIMEOUT = 30

# 代理列表（示例，实际使用时需要配置真实代理）
PROXY_LIST = [
    # 'http://proxy1.example.com:8080',
    # 'http://proxy2.example.com:8080',
]

# 数据库路径
DATABASE_PATH = 'data/stock_data/databases/tender_crawler.db'

# JSON导出路径
JSON_EXPORT_PATH = 'data/stock_data/crawler_backup.json'

# Selenium WebDriver路径（可选）
SELENIUM_DRIVER_PATH = None

# 日志设置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# 请求指纹（去重）
DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'

# 设置User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Redis配置（用于分布式爬取，可选）
# REDIS_URL = 'redis://localhost:6379'
# SCHEDULER = 'scrapy_redis.scheduler.Scheduler'
# DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'

