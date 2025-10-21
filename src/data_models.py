"""
投研报告数据模型定义
定义投研报告的元数据结构和问题类型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ReportType(str, Enum):
    """报告类型枚举"""

    DEPTH_RESEARCH = "深度研究"  # 深度研究报告
    QUARTERLY_REVIEW = "季报点评"  # 季报点评
    ANNUAL_REVIEW = "年报点评"  # 年报点评
    INDUSTRY_ANALYSIS = "行业分析"  # 行业分析
    COMPANY_VISIT = "公司调研"  # 公司调研纪要
    INVESTMENT_STRATEGY = "投资策略"  # 投资策略
    MARKET_OUTLOOK = "市场展望"  # 市场展望
    RISK_WARNING = "风险提示"  # 风险提示
    EARNINGS_FORECAST = "业绩预测"  # 业绩预测
    VALUATION_ANALYSIS = "估值分析"  # 估值分析


class QuestionType(str, Enum):
    """问题类型枚举"""

    STRING = "string"  # 开放式问答
    MULTIPLE_CHOICE = "multiple_choice"  # 多选题
    SINGLE_CHOICE = "single_choice"  # 单选题
    NUMERICAL = "numerical"  # 数值型
    BOOLEAN = "boolean"  # 是否型
    COMPARISON = "comparison"  # 比较型


class Language(str, Enum):
    """语言类型枚举"""

    CHINESE = "中文"
    ENGLISH = "英文"
    BILINGUAL = "中英文"


class ReportMetadata(BaseModel):
    """投研报告元数据模型"""

    file_id: str = Field(..., description="文件唯一标识符")
    company_name: str = Field(..., description="公司名称")
    company_code: Optional[str] = Field(None, description="股票代码")
    report_type: ReportType = Field(..., description="报告类型")
    publish_date: datetime = Field(..., description="发布日期")
    analyst: str = Field(..., description="分析师姓名")
    analyst_team: Optional[List[str]] = Field(None, description="分析师团队")
    institution: str = Field(..., description="研究机构")
    title: str = Field(..., description="报告标题")
    subtitle: Optional[str] = Field(None, description="报告副标题")

    # 文件信息
    file_path: str = Field(..., description="文件相对路径")
    file_size: int = Field(..., description="文件大小(字节)")
    pages: int = Field(..., description="页数")
    language: Language = Field(Language.CHINESE, description="语言")

    # 内容摘要
    abstract: Optional[str] = Field(None, description="报告摘要")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    investment_rating: Optional[str] = Field(None, description="投资评级")
    target_price: Optional[float] = Field(None, description="目标价格")

    # 行业信息
    industry: Optional[str] = Field(None, description="所属行业")
    sector: Optional[str] = Field(None, description="所属板块")

    # 处理状态
    processed: bool = Field(False, description="是否已处理")
    processing_date: Optional[datetime] = Field(None, description="处理日期")

    # 质量评分
    quality_score: Optional[float] = Field(None, description="报告质量评分(0-10)")
    readability_score: Optional[float] = Field(None, description="可读性评分(0-10)")

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class Question(BaseModel):
    """问题模型"""

    question_id: str = Field(..., description="问题唯一标识符")
    question_text: str = Field(..., description="问题文本")
    question_type: QuestionType = Field(..., description="问题类型")

    # 问题分类
    category: Optional[str] = Field(None, description="问题分类")
    difficulty: Optional[str] = Field(None, description="难度等级: easy/medium/hard")

    # 针对性设置
    target_companies: Optional[List[str]] = Field(None, description="目标公司列表")
    target_industries: Optional[List[str]] = Field(None, description="目标行业列表")

    # 选择题选项（如果适用）
    choices: Optional[List[str]] = Field(None, description="选择题选项")

    # 预期答案类型
    expected_answer_format: Optional[str] = Field(None, description="预期答案格式")

    # 评分标准
    scoring_criteria: Optional[Dict[str, Any]] = Field(None, description="评分标准")

    class Config:
        use_enum_values = True


class ProcessingStatus(BaseModel):
    """处理状态模型"""

    file_id: str = Field(..., description="文件标识符")
    step_name: str = Field(..., description="处理步骤名称")
    status: str = Field(..., description="状态: pending/processing/completed/failed")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    output_path: Optional[str] = Field(None, description="输出文件路径")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ChunkMetadata(BaseModel):
    """文本块元数据模型"""

    chunk_id: str = Field(..., description="文本块唯一标识符")
    file_id: str = Field(..., description="源文件标识符")
    chunk_index: int = Field(..., description="文本块索引")

    # 位置信息
    page_number: Optional[int] = Field(None, description="页码")
    start_position: Optional[int] = Field(None, description="起始位置")
    end_position: Optional[int] = Field(None, description="结束位置")

    # 内容信息
    text_content: str = Field(..., description="文本内容")
    content_type: Optional[str] = Field(None, description="内容类型: text/table/image")
    word_count: int = Field(..., description="词数")

    # 嵌入向量信息
    embedding_model: Optional[str] = Field(None, description="嵌入模型名称")
    embedding_vector: Optional[List[float]] = Field(None, description="嵌入向量")

    # 语义信息
    semantic_tags: Optional[List[str]] = Field(None, description="语义标签")
    importance_score: Optional[float] = Field(None, description="重要性评分")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# 预定义的报告类型和问题类别映射
REPORT_TYPE_CATEGORIES = {
    ReportType.DEPTH_RESEARCH: ["公司基本面", "财务分析", "竞争优势", "风险因素"],
    ReportType.QUARTERLY_REVIEW: ["财务表现", "业绩亮点", "同比分析", "展望"],
    ReportType.ANNUAL_REVIEW: ["年度总结", "财务分析", "战略回顾", "未来规划"],
    ReportType.INDUSTRY_ANALYSIS: ["行业趋势", "市场规模", "竞争格局", "政策影响"],
    ReportType.COMPANY_VISIT: ["管理层访谈", "业务进展", "战略规划", "市场反馈"],
    ReportType.INVESTMENT_STRATEGY: ["投资主题", "配置建议", "风险收益", "时机把握"],
}

# 预定义的问题难度等级
DIFFICULTY_LEVELS = {
    "easy": "基础信息查询",
    "medium": "分析性问题",
    "hard": "综合性判断",
}
