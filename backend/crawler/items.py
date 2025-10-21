"""
Scrapy Items定义
定义招标信息的数据结构
"""

import scrapy
from datetime import datetime


class TenderItem(scrapy.Item):
    """招标信息Item"""

    # 基本信息
    project_id = scrapy.Field()          # 项目唯一ID（由爬虫生成）
    title = scrapy.Field()                # 项目标题
    project_number = scrapy.Field()       # 项目编号
    source_platform = scrapy.Field()      # 来源平台（如：某省公共资源交易中心）
    source_url = scrapy.Field()           # 原始URL

    # 分类信息
    industry = scrapy.Field()             # 行业类别（电力、建筑、IT等）
    project_type = scrapy.Field()         # 项目类型（公开招标、邀请招标等）
    tender_type = scrapy.Field()          # 招标类型（货物、工程、服务）

    # 金额信息
    budget = scrapy.Field()               # 预算金额（万元）
    budget_text = scrapy.Field()          # 原始预算文本

    # 地域信息
    province = scrapy.Field()             # 省份
    city = scrapy.Field()                 # 城市
    district = scrapy.Field()             # 区县
    region_code = scrapy.Field()          # 地区编码

    # 时间信息
    publish_time = scrapy.Field()         # 发布时间
    deadline = scrapy.Field()             # 截止时间
    opening_time = scrapy.Field()         # 开标时间

    # 内容信息
    content = scrapy.Field()              # 招标公告正文（HTML或纯文本）
    content_text = scrapy.Field()         # 纯文本内容
    summary = scrapy.Field()              # 摘要

    # 联系信息
    contact_person = scrapy.Field()       # 联系人
    contact_phone = scrapy.Field()        # 联系电话
    contact_email = scrapy.Field()        # 联系邮箱
    agent_name = scrapy.Field()           # 招标代理机构

    # 附件信息
    attachments = scrapy.Field()          # 附件列表 [{"name": "xx.pdf", "url": "http://..."}]

    # 状态信息
    status = scrapy.Field()               # 状态（招标中、已开标、已中标等）

    # 元数据
    crawled_time = scrapy.Field()         # 爬取时间
    spider_name = scrapy.Field()          # 爬虫名称
    data_hash = scrapy.Field()            # 数据哈希（用于去重）


class BidResultItem(scrapy.Item):
    """中标结果Item"""

    # 关联信息
    project_id = scrapy.Field()           # 关联的项目ID
    tender_project_id = scrapy.Field()    # 招标项目ID

    # 基本信息
    title = scrapy.Field()                # 标题
    project_number = scrapy.Field()       # 项目编号
    source_platform = scrapy.Field()      # 来源平台
    source_url = scrapy.Field()           # 原始URL

    # 中标信息
    winner_name = scrapy.Field()          # 中标单位名称
    winner_amount = scrapy.Field()        # 中标金额（万元）
    winner_amount_text = scrapy.Field()   # 原始金额文本
    bid_date = scrapy.Field()             # 中标日期

    # 其他投标人信息
    bidders = scrapy.Field()              # 其他投标人列表
    # [{"name": "公司名", "amount": 金额, "rank": 排名}]

    # 内容信息
    content = scrapy.Field()              # 中标公告正文
    content_text = scrapy.Field()         # 纯文本内容

    # 元数据
    crawled_time = scrapy.Field()         # 爬取时间
    spider_name = scrapy.Field()          # 爬虫名称
    data_hash = scrapy.Field()            # 数据哈希（用于去重）

