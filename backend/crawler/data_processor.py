"""
数据处理器
增强的数据清洗、标准化和去重功能
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class AdvancedDataCleaner:
    """
    高级数据清洗器

    功能：
    - 金额标准化（元、万元、亿元 → 万元，ISO标准）
    - 日期标准化（多种格式 → ISO 8601）
    - 地域标准化（省/市/区规范化）
    - 文本清洗（去噪、统一格式）
    """

    def __init__(self):
        # 完整的省份映射表
        self.province_map = {
            # 直辖市
            '北京': '北京市',
            '上海': '上海市',
            '天津': '天津市',
            '重庆': '重庆市',
            # 省份
            '河北': '河北省',
            '山西': '山西省',
            '辽宁': '辽宁省',
            '吉林': '吉林省',
            '黑龙江': '黑龙江省',
            '江苏': '江苏省',
            '浙江': '浙江省',
            '安徽': '安徽省',
            '福建': '福建省',
            '江西': '江西省',
            '山东': '山东省',
            '河南': '河南省',
            '湖北': '湖北省',
            '湖南': '湖南省',
            '广东': '广东省',
            '海南': '海南省',
            '四川': '四川省',
            '贵州': '贵州省',
            '云南': '云南省',
            '陕西': '陕西省',
            '甘肃': '甘肃省',
            '青海': '青海省',
            '台湾': '台湾省',
            # 自治区
            '内蒙古': '内蒙古自治区',
            '广西': '广西壮族自治区',
            '西藏': '西藏自治区',
            '宁夏': '宁夏回族自治区',
            '新疆': '新疆维吾尔自治区',
            # 特别行政区
            '香港': '香港特别行政区',
            '澳门': '澳门特别行政区',
        }

    def clean_amount(self, amount_text: str) -> Optional[float]:
        """
        清洗和标准化金额

        输入示例：
        - "100万元"
        - "1,234,567.89元"
        - "10亿"
        - "100.5万"

        输出：统一为万元（浮点数）
        """
        if not amount_text or not isinstance(amount_text, str):
            return None

        # 移除逗号分隔符
        amount_text = amount_text.replace(',', '')

        # 提取数字（支持小数）
        numbers = re.findall(r'\d+\.?\d*', amount_text)
        if not numbers:
            return None

        amount = float(numbers[0])

        # 判断单位并转换为万元
        if '亿' in amount_text:
            amount = amount * 10000
        elif '万' in amount_text:
            amount = amount
        elif '千' in amount_text or 'k' in amount_text.lower():
            amount = amount * 0.1
        elif '百' in amount_text:
            amount = amount * 0.01
        elif '元' in amount_text or 'rmb' in amount_text.lower() or '¥' in amount_text:
            amount = amount * 0.0001
        else:
            # 默认假设是元
            amount = amount * 0.0001

        return round(amount, 4)

    def clean_date(self, date_text: str) -> Optional[str]:
        """
        清洗和标准化日期

        输入示例：
        - "2024-01-01 12:00:00"
        - "2024年1月1日"
        - "2024/01/01"
        - "20240101"

        输出：ISO 8601格式 "YYYY-MM-DD HH:MM:SS"或"YYYY-MM-DD"
        """
        if not date_text or not isinstance(date_text, str):
            return None

        # 日期格式模式（按优先级排序）
        patterns = [
            # 完整日期时间
            (r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})', True),
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{1,2}):(\d{1,2})', True),
            # 只有日期
            (r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', False),
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', False),
            (r'(\d{8})', False),  # 20240101
        ]

        for pattern, has_time in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    groups = match.groups()

                    if pattern == r'(\d{8})':
                        # 处理紧凑格式 20240101
                        date_str = groups[0]
                        year = int(date_str[0:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])
                        dt = datetime(year, month, day)
                    elif has_time:
                        dt = datetime(
                            int(groups[0]), int(groups[1]), int(groups[2]),
                            int(groups[3]), int(groups[4]), int(groups[5])
                        )
                    else:
                        dt = datetime(int(groups[0]), int(groups[1]), int(groups[2]))

                    # 返回ISO格式
                    if has_time:
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        return dt.strftime('%Y-%m-%d')

                except (ValueError, IndexError) as e:
                    logger.debug(f'日期解析失败: {date_text}, 错误: {e}')
                    continue

        return None

    def clean_province(self, province: str) -> str:
        """
        清洗和标准化省份名称

        输入示例：
        - "北京"
        - "广东省"
        - "新疆"

        输出：标准省份名称（带后缀）
        """
        if not province or not isinstance(province, str):
            return ''

        province = province.strip()

        # 移除常见后缀
        province_base = province.replace('省', '').replace('市', '').replace('自治区', '').replace('特别行政区', '')

        # 使用映射表
        if province_base in self.province_map:
            return self.province_map[province_base]

        # 如果已经是标准格式，直接返回
        if province in self.province_map.values():
            return province

        return province

    def clean_city(self, city: str, province: str = '') -> str:
        """
        清洗和标准化城市名称

        输入示例：
        - "北京"（直辖市）
        - "深圳市"
        - "深圳"

        输出：标准城市名称
        """
        if not city or not isinstance(city, str):
            return ''

        city = city.strip()

        # 直辖市特殊处理
        if city in ['北京', '上海', '天津', '重庆'] and not province:
            return city + '市'

        # 添加"市"后缀（如果没有）
        if city and not city.endswith('市') and not city.endswith('区') and not city.endswith('县'):
            return city + '市'

        return city

    def clean_text(self, text: str) -> str:
        """
        清洗文本

        - 去除多余空白
        - 去除特殊字符
        - 统一换行符
        """
        if not text or not isinstance(text, str):
            return ''

        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 去除多余空白（但保留单个空格和换行）
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n+', '\n', text)

        # 去除首尾空白
        text = text.strip()

        return text

    def extract_phone(self, text: str) -> Optional[str]:
        """
        从文本中提取电话号码

        支持格式：
        - 手机号：13812345678
        - 固话：010-12345678
        - 带区号：(010)12345678
        """
        if not text:
            return None

        # 手机号模式
        mobile_pattern = r'1[3-9]\d{9}'
        # 固话模式
        landline_pattern = r'(?:\d{3,4}[-\s]?)?\d{7,8}'

        # 先尝试匹配手机号
        mobile_match = re.search(mobile_pattern, text)
        if mobile_match:
            return mobile_match.group(0)

        # 再尝试匹配固话
        landline_match = re.search(landline_pattern, text)
        if landline_match:
            return landline_match.group(0)

        return None

    def extract_email(self, text: str) -> Optional[str]:
        """从文本中提取邮箱地址"""
        if not text:
            return None

        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)

        return match.group(0) if match else None


class CrossPlatformDeduplicator:
    """
    跨平台去重器

    功能：
    - 基于URL的精确去重
    - 基于标题+金额的模糊去重
    - 文本相似度计算
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: 相似度阈值（0-1），超过此值视为重复
        """
        self.similarity_threshold = similarity_threshold
        self.seen_urls = set()
        self.seen_items = []  # 存储已见过的项目信息

    def is_duplicate(self, url: str, title: str, budget: Optional[float] = None) -> Tuple[bool, str]:
        """
        检查是否重复

        Args:
            url: 项目URL
            title: 项目标题
            budget: 预算金额（万元）

        Returns:
            (是否重复, 重复原因)
        """
        # 1. URL精确匹配
        if url and url in self.seen_urls:
            return True, 'URL重复'

        # 2. 标题+金额模糊匹配
        if title:
            for seen_item in self.seen_items:
                # 计算标题相似度
                title_similarity = self._calculate_similarity(title, seen_item['title'])

                # 如果标题相似度高
                if title_similarity >= self.similarity_threshold:
                    # 如果都有金额且金额相近
                    if budget and seen_item.get('budget'):
                        budget_diff = abs(budget - seen_item['budget']) / max(budget, seen_item['budget'])
                        if budget_diff < 0.05:  # 金额差异小于5%
                            return True, f'标题+金额相似（相似度={title_similarity:.2f}）'
                    else:
                        # 只有标题，相似度很高就认为重复
                        if title_similarity >= 0.95:
                            return True, f'标题高度相似（相似度={title_similarity:.2f}）'

        return False, ''

    def mark_seen(self, url: str, title: str, budget: Optional[float] = None):
        """标记为已见"""
        if url:
            self.seen_urls.add(url)

        self.seen_items.append({
            'url': url,
            'title': title,
            'budget': budget
        })

        # 限制缓存大小（保留最近10000条）
        if len(self.seen_items) > 10000:
            self.seen_items = self.seen_items[-10000:]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度

        使用SequenceMatcher算法（基于最长公共子序列）

        Returns:
            相似度（0-1）
        """
        if not text1 or not text2:
            return 0.0

        # 统一转小写、去除空格
        text1 = text1.lower().replace(' ', '')
        text2 = text2.lower().replace(' ', '')

        return SequenceMatcher(None, text1, text2).ratio()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'seen_urls_count': len(self.seen_urls),
            'seen_items_count': len(self.seen_items)
        }


class DataNormalizer:
    """
    数据规范化器

    统一处理所有数据标准化工作
    """

    def __init__(self):
        self.cleaner = AdvancedDataCleaner()
        self.deduplicator = CrossPlatformDeduplicator()

    def normalize_tender_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        规范化招标项目数据

        Args:
            item_data: 原始项目数据

        Returns:
            规范化后的数据
        """
        normalized = item_data.copy()

        # 清洗标题
        if 'title' in normalized:
            normalized['title'] = self.cleaner.clean_text(normalized['title'])

        # 标准化金额
        if 'budget_text' in normalized and normalized['budget_text']:
            normalized['budget'] = self.cleaner.clean_amount(normalized['budget_text'])

        # 标准化日期
        if 'publish_time' in normalized and normalized['publish_time']:
            normalized['publish_time'] = self.cleaner.clean_date(str(normalized['publish_time']))

        if 'deadline' in normalized and normalized['deadline']:
            normalized['deadline'] = self.cleaner.clean_date(str(normalized['deadline']))

        # 标准化地域
        if 'province' in normalized and normalized['province']:
            normalized['province'] = self.cleaner.clean_province(normalized['province'])

        if 'city' in normalized and normalized['city']:
            normalized['city'] = self.cleaner.clean_city(
                normalized['city'],
                normalized.get('province', '')
            )

        # 清洗内容文本
        if 'content_text' in normalized and normalized['content_text']:
            normalized['content_text'] = self.cleaner.clean_text(normalized['content_text'])

        # 提取联系方式
        if 'contact_phone' not in normalized or not normalized.get('contact_phone'):
            content = normalized.get('content_text', '')
            normalized['contact_phone'] = self.cleaner.extract_phone(content)

        if 'contact_email' not in normalized or not normalized.get('contact_email'):
            content = normalized.get('content_text', '')
            normalized['contact_email'] = self.cleaner.extract_email(content)

        return normalized

    def check_duplicate(self, item_data: Dict[str, Any]) -> Tuple[bool, str]:
        """检查是否重复"""
        url = item_data.get('source_url', '')
        title = item_data.get('title', '')
        budget = item_data.get('budget')

        return self.deduplicator.is_duplicate(url, title, budget)

    def mark_processed(self, item_data: Dict[str, Any]):
        """标记为已处理"""
        url = item_data.get('source_url', '')
        title = item_data.get('title', '')
        budget = item_data.get('budget')

        self.deduplicator.mark_seen(url, title, budget)

