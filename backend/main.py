#!/usr/bin/env python
"""
投研RAG智能问答系统 - FastAPI后端服务
提供RESTful API接口，支持PDF上传、问答查询、系统管理等功能
"""

import sys
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.pipeline import Pipeline, RunConfig
from src.questions_processing import QuestionsProcessor
from src.config import get_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============== 数据模型定义 ==============


class QuestionRequest(BaseModel):
    """问答请求模型"""

    question: str
    company: Optional[str] = None
    question_type: Optional[str] = "string"
    session_id: Optional[str] = None


class QuestionResponse(BaseModel):
    """问答响应模型"""

    success: bool
    answer: str
    reasoning: str
    relevant_pages: List[int]
    confidence: str
    processing_time: float
    question: str
    company: Optional[str]
    error: Optional[str] = None


class UploadResponse(BaseModel):
    """文件上传响应模型"""

    success: bool
    message: str
    filename: str
    file_size: int
    upload_time: float
    error: Optional[str] = None


class SystemStatus(BaseModel):
    """系统状态模型"""

    status: str
    is_ready: bool
    databases_loaded: bool
    config: Dict[str, Any]
    statistics: Dict[str, Any]
    uptime: float


class BatchQuestionRequest(BaseModel):
    """批量问答请求模型"""

    questions: List[Dict[str, str]]
    process_async: bool = True


class ChatSession(BaseModel):
    """对话会话模型"""

    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class ChatMessage(BaseModel):
    """对话消息模型"""

    id: str
    session_id: str
    content: str
    role: str  # 'user' | 'assistant'
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class CreateSessionRequest(BaseModel):
    """创建会话请求"""

    title: str


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""

    title: Optional[str] = None


# ============== 全局变量和初始化 ==============

# 全局变量
pipeline: Optional[Pipeline] = None
processor: Optional[QuestionsProcessor] = None
app_start_time = time.time()
settings = get_settings()

# 简单的内存存储（生产环境应该使用数据库）
chat_sessions: Dict[str, Dict] = {}
chat_messages: Dict[str, List[Dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动投研RAG系统...")

    global pipeline, processor

    try:
        # 先初始化问题处理器（纯LLM模式必需）
        logger.info("初始化问题处理器...")
        processor = QuestionsProcessor(api_provider="dashscope")
        logger.info("✅ 问题处理器初始化完成")

        # 尝试初始化Pipeline（RAG模式，可选）
        try:
            logger.info("初始化Pipeline...")
            config = RunConfig(
                api_provider="dashscope",
                use_vector_dbs=True,
                use_bm25_db=True,
                top_n_retrieval=10,
            )

            pipeline = Pipeline(root_path=settings.data_dir, run_config=config)

            # 检查并准备文档（如果需要）
            logger.info("检查文档状态...")
            status = pipeline.get_status()

            if not status["is_ready"]:
                logger.info("系统未准备就绪，将在后台准备文档...")
                # 这里可以选择是否自动准备文档

            logger.info("✅ Pipeline初始化完成")
        except Exception as pe:
            logger.warning(f"⚠️ Pipeline初始化失败: {str(pe)}")
            logger.info("系统将以纯LLM模式运行")
            pipeline = None

        logger.info("✅ 系统初始化完成")

    except Exception as e:
        logger.error(f"❌ 系统初始化失败: {str(e)}")
        logger.error(f"详细错误信息: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        # 即使初始化失败，也要启动服务，但标记为未准备
        pass

    yield

    # 关闭时清理
    logger.info("🛑 关闭投研RAG系统...")


# ============== FastAPI应用配置 ==============

app = FastAPI(
    title="投研RAG智能问答系统",
    description="基于DashScope API和MinerU的投资研究报告智能问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3005",  # React开发服务器
        "http://127.0.0.1:3005",
        "http://localhost:5173",  # Vite开发服务器
        settings.frontend.cors_origins[0] if settings.frontend.cors_origins else "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== 工具函数 ==============


def validate_system_ready():
    """验证系统是否准备就绪"""
    if not processor:
        raise HTTPException(status_code=503, detail="系统正在初始化，请稍后重试")

    # Pipeline可以为空，此时使用纯LLM模式
    return True


# ============== API路由定义 ==============


@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径，返回API信息"""
    return {
        "message": "投研RAG智能问答系统API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.time() - app_start_time,
    }


@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    try:
        if not pipeline:
            return SystemStatus(
                status="initializing",
                is_ready=False,
                databases_loaded=False,
                config={},
                statistics={},
                uptime=time.time() - app_start_time,
            )

        status = pipeline.get_status()

        # 添加统计信息
        statistics = {
            "pdf_files": (
                len(list(settings.pdf_dir.glob("*.pdf")))
                if settings.pdf_dir.exists()
                else 0
            ),
            "parsed_files": (
                len(list((settings.debug_dir / "parsed_reports").glob("*_parsed.json")))
                if (settings.debug_dir / "parsed_reports").exists()
                else 0
            ),
            "vector_files": (
                len(list((settings.db_dir / "vector_dbs").glob("*.faiss")))
                if (settings.db_dir / "vector_dbs").exists()
                else 0
            ),
            "bm25_files": (
                len(list((settings.db_dir / "bm25").glob("*.pkl")))
                if (settings.db_dir / "bm25").exists()
                else 0
            ),
        }

        # 确定当前工作模式
        has_documents = pipeline and status["is_ready"]
        mode = "rag" if has_documents else "pure_llm"

        return SystemStatus(
            status="ready",  # 系统总是可用的
            is_ready=True,   # 至少支持纯LLM模式
            databases_loaded=status["databases_loaded"] if pipeline else False,
            config={
                **status["config"],
                "mode": mode,
                "documents_available": has_documents,
                "note": "RAG模式需要上传PDF文档" if not has_documents else "RAG模式已就绪"
            },
            statistics=statistics,
            uptime=time.time() - app_start_time,
        )

    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return SystemStatus(
            status="error",
            is_ready=False,
            databases_loaded=False,
            config={},
            statistics={},
            uptime=time.time() - app_start_time,
        )


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """问答接口"""
    validate_system_ready()

    try:
        logger.info(f"收到问题: {request.question}")

        # 检查是否有Pipeline和文档数据
        has_documents = pipeline and pipeline.is_ready

        if has_documents:
            # 使用RAG模式：Pipeline + 问题处理器
            logger.info("使用RAG模式处理问题")
            result = pipeline.answer_question(
                question=request.question,
                company=request.company,
                question_type=request.question_type,
            )
        else:
            # 使用纯LLM模式：仅问题处理器
            logger.info("使用纯LLM模式处理问题（无文档数据）")
            result = processor.process_question(
                question=request.question,
                company=request.company,
                question_type=request.question_type,
            )
            # 添加模式提示
            result["mode"] = "pure_llm"
            result["note"] = "当前为纯LLM模式，如需基于文档的精准回答，请上传相关PDF文档"

        # 如果提供了session_id，保存消息到会话
        if request.session_id and request.session_id in chat_sessions:
            import uuid
            from datetime import datetime

            now = datetime.now().isoformat()

            # 添加用户消息
            user_message = {
                "id": str(uuid.uuid4()),
                "session_id": request.session_id,
                "content": request.question,
                "role": "user",
                "timestamp": now,
                "metadata": {
                    "company": request.company,
                    "question_type": request.question_type
                }
            }

            # 添加助手回复
            assistant_message = {
                "id": str(uuid.uuid4()),
                "session_id": request.session_id,
                "content": result.get("answer", ""),
                "role": "assistant",
                "timestamp": now,
                "metadata": {
                    "reasoning": result.get("reasoning", ""),
                    "relevant_pages": result.get("relevant_pages", []),
                    "confidence": result.get("confidence", "medium"),
                    "processing_time": result.get("total_processing_time", 0)
                }
            }

            # 保存消息
            if request.session_id not in chat_messages:
                chat_messages[request.session_id] = []

            chat_messages[request.session_id].extend([user_message, assistant_message])

            # 更新会话时间
            chat_sessions[request.session_id]["updated_at"] = now
            chat_sessions[request.session_id]["message_count"] = len(chat_messages[request.session_id])

        return QuestionResponse(
            success=result["success"],
            answer=result.get("answer", ""),
            reasoning=result.get("reasoning", ""),
            relevant_pages=result.get("relevant_pages", []),
            confidence=result.get("confidence", "medium"),
            processing_time=result.get("total_processing_time", 0),
            question=request.question,
            company=request.company,
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"问答处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """PDF文件上传接口"""
    start_time = time.time()

    try:
        # 验证文件类型
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="只支持PDF文件上传")

        # 保存上传的文件
        pdf_dir = settings.pdf_dir
        pdf_dir.mkdir(parents=True, exist_ok=True)

        file_path = pdf_dir / file.filename

        # 写入文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        file_size = len(content)
        upload_time = time.time() - start_time

        logger.info(f"文件上传成功: {file.filename}, 大小: {file_size} bytes")

        # 后台任务：触发文档重新处理
        if pipeline:
            background_tasks.add_task(trigger_document_processing, file_path)

        return UploadResponse(
            success=True,
            message=f"文件 {file.filename} 上传成功",
            filename=file.filename,
            file_size=file_size,
            upload_time=upload_time,
        )

    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        return UploadResponse(
            success=False,
            message="文件上传失败",
            filename=file.filename,
            file_size=0,
            upload_time=time.time() - start_time,
            error=str(e),
        )


@app.post("/batch_ask")
async def batch_ask_questions(request: BatchQuestionRequest):
    """批量问答接口"""
    validate_system_ready()

    try:
        logger.info(f"收到批量问题: {len(request.questions)} 个")

        if request.process_async:
            # 异步处理
            # 这里可以实现真正的异步任务队列
            # 简化版本直接处理
            pass

        # 处理批量问题
        results = processor.batch_process_questions(request.questions)

        return {
            "success": True,
            "task_id": f"batch_{int(time.time())}",
            "total_questions": results["total_questions"],
            "successful": results["successful"],
            "failed": results["failed"],
            "processing_time": results["total_time"],
            "results": results["answers"],
        }

    except Exception as e:
        logger.error(f"批量问答失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prepare_documents")
async def prepare_documents(
    background_tasks: BackgroundTasks, force_rebuild: bool = False
):
    """准备文档接口（解析+向量化）"""
    validate_system_ready()

    try:
        logger.info("开始文档准备流程...")

        # 添加后台任务
        background_tasks.add_task(run_document_preparation, force_rebuild)

        return {
            "success": True,
            "message": "文档准备流程已启动，请查看系统状态",
            "force_rebuild": force_rebuild,
        }

    except Exception as e:
        logger.error(f"文档准备失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/companies")
async def get_companies():
    """获取可用的公司列表"""
    try:
        # 从subset.csv或其他数据源读取公司列表
        companies = []

        # 检查是否有subset.csv文件
        subset_file = settings.data_dir / "subset.csv"
        if subset_file.exists():
            import pandas as pd
            df = pd.read_csv(subset_file)
            if 'company_name' in df.columns:
                companies = df['company_name'].unique().tolist()

        # 如果没有数据文件，返回默认的公司列表
        if not companies:
            companies = [
                "中芯国际", "宁德时代", "比亚迪", "腾讯控股", "阿里巴巴",
                "美团", "小米集团", "京东", "网易", "百度"
            ]

        return {"companies": companies}

    except Exception as e:
        logger.error(f"获取公司列表失败: {str(e)}")
        # 返回默认列表
        return {"companies": ["中芯国际", "宁德时代", "比亚迪"]}


# ============== 对话管理接口 ==============

@app.get("/sessions")
async def get_sessions():
    """获取所有对话会话"""
    try:
        sessions = []
        for session_id, session_data in chat_sessions.items():
            message_count = len(chat_messages.get(session_id, []))
            sessions.append({
                **session_data,
                "message_count": message_count
            })

        # 按更新时间排序
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return {"sessions": sessions}

    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """创建新的对话会话"""
    try:
        import uuid
        from datetime import datetime

        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        session_data = {
            "id": session_id,
            "title": request.title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0
        }

        chat_sessions[session_id] = session_data
        chat_messages[session_id] = []

        logger.info(f"创建新会话: {session_id} - {request.title}")
        return session_data

    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取特定会话信息"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        session_data = chat_sessions[session_id].copy()
        messages = chat_messages.get(session_id, [])
        session_data["messages"] = messages
        session_data["message_count"] = len(messages)

        return session_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    """更新会话信息"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        from datetime import datetime

        session_data = chat_sessions[session_id]

        if request.title:
            session_data["title"] = request.title

        session_data["updated_at"] = datetime.now().isoformat()

        logger.info(f"更新会话: {session_id}")
        return session_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 删除会话和相关消息
        del chat_sessions[session_id]
        if session_id in chat_messages:
            del chat_messages[session_id]

        logger.info(f"删除会话: {session_id}")
        return {"success": True, "message": "会话已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """获取会话的所有消息"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        messages = chat_messages.get(session_id, [])
        return {"messages": messages}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/docs")
async def get_api_docs():
    """获取API文档（重定向到Swagger UI）"""
    return {"message": "请访问 /docs 查看完整API文档"}


# ============== 后台任务 ==============


async def trigger_document_processing(file_path: Path):
    """触发文档处理的后台任务"""
    try:
        logger.info(f"开始处理新上传的文件: {file_path}")

        if pipeline:
            # 重新准备文档（增量处理）
            results = pipeline.prepare_documents(force_rebuild=False)

            if results["success"]:
                logger.info("新文档处理完成")
            else:
                logger.error(f"新文档处理失败: {results.get('error')}")

    except Exception as e:
        logger.error(f"后台文档处理失败: {str(e)}")


async def run_document_preparation(force_rebuild: bool = False):
    """运行文档准备的后台任务"""
    try:
        logger.info(f"开始文档准备（强制重建: {force_rebuild}）")

        if pipeline:
            results = pipeline.prepare_documents(force_rebuild=force_rebuild)

            if results["success"]:
                logger.info(f"文档准备完成，耗时: {results['total_time']:.2f}秒")
            else:
                logger.error(f"文档准备失败: {results.get('error')}")

    except Exception as e:
        logger.error(f"文档准备后台任务失败: {str(e)}")


# ============== 错误处理 ==============


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404, content={"error": "API端点未找到", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    logger.error(f"内部服务器错误: {str(exc)}")
    return JSONResponse(
        status_code=500, content={"error": "内部服务器错误", "detail": str(exc)}
    )


# ============== 启动配置 ==============

if __name__ == "__main__":
    import uvicorn

    # 从配置获取端口，如果配置不可用则使用默认值
    try:
        host = settings.api.host
        port = settings.api.port
        debug = settings.api.debug
    except Exception:
        host = "0.0.0.0"
        port = 8000
        debug = False

    logger.info(f"🚀 启动FastAPI服务器: {host}:{port}")

    uvicorn.run("main:app", host=host, port=port, reload=debug, log_level="info")
