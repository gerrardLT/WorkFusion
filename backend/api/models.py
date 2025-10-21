"""
API数据模型定义
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============== 场景相关模型 ==============

class ScenarioResponse(BaseModel):
    """场景响应模型"""
    id: str
    name: str
    description: str
    status: str
    document_type_count: Optional[int] = 0
    created_at: str
    updated_at: str
    # 扁平化的配置字段
    theme: Dict[str, Any] = {}
    ui: Dict[str, Any] = {}
    presetQuestions: List[str] = []
    documentTypes: List[Dict[str, Any]] = []


class ScenarioListResponse(BaseModel):
    """场景列表响应模型"""
    scenarios: List[ScenarioResponse]
    total: int


class ScenarioConfigResponse(BaseModel):
    """场景配置响应模型"""
    ui: Dict[str, str]
    theme: Dict[str, str]
    preset_questions: List[str]
    document_types: List[Dict[str, Any]]


# ============== 问答相关模型 ==============

class QuestionRequest(BaseModel):
    """问答请求模型"""
    question: str
    scenario_id: str = Field(..., description="场景ID")
    session_id: Optional[str] = None
    company: Optional[str] = None
    question_type: Optional[str] = "string"


class QuestionResponse(BaseModel):
    """问答响应模型"""
    success: bool
    answer: str
    reasoning: str
    confidence: float
    sources: List[Dict[str, Any]]
    processing_time: float
    scenario_id: str
    session_id: Optional[str] = None


# ============== 上传相关模型 ==============

class ProcessingStats(BaseModel):
    """处理统计信息"""
    chunks_created: int
    vectors_created: int
    pipeline_ready: bool

class UploadResponse(BaseModel):
    """上传响应模型"""
    success: bool
    message: str
    document_id: Optional[str] = None
    filename: str
    file_size: int
    file_size_mb: float
    scenario_id: str
    processing_stats: ProcessingStats


class ProcessingStatus(BaseModel):
    """处理状态模型"""
    document_id: str
    status: str  # pending, processing, completed, failed
    progress: float
    message: str
    created_at: str
    updated_at: str


# ============== 会话相关模型 ==============

class ChatMessage(BaseModel):
    """聊天消息模型"""
    id: str
    content: str
    role: str  # user, assistant, system
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ChatSession(BaseModel):
    """聊天会话模型"""
    id: str
    scenario_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    config: Optional[Dict[str, Any]] = None


class CreateSessionRequest(BaseModel):
    """创建会话请求模型"""
    scenario_id: str
    title: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    """更新会话请求模型"""
    title: Optional[str] = None


class SessionResponse(BaseModel):
    """会话响应模型"""
    session: ChatSession
    messages: List[ChatMessage]


class SessionsResponse(BaseModel):
    """会话列表响应模型"""
    sessions: List[ChatSession]
    total: int


class MessagesResponse(BaseModel):
    """消息列表响应模型"""
    messages: List[ChatMessage]
    total: int


# ============== 文档相关模型 ==============

class DocumentInfo(BaseModel):
    """文档信息模型"""
    id: str
    scenario_id: str
    title: str
    file_size: int
    pages: Optional[int] = None
    language: str = "zh"
    status: str
    quality_score: Optional[float] = None
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    documents: List[DocumentInfo]
    total: int


# ============== 系统相关模型 ==============

class SystemStatus(BaseModel):
    """系统状态模型"""
    status: str
    version: str
    scenarios: List[Dict[str, Any]]
    database_status: str
    total_documents: int
    total_sessions: int


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    services: Dict[str, str]


# ============== 错误响应模型 ==============

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str


# ============== 成功响应模型 ==============

class SuccessResponse(BaseModel):
    """成功响应模型"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
