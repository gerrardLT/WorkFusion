"""
多场景聊天API路由
"""

import sys
import uuid
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..services.scenario_service import get_scenario_service, ScenarioService
from ..services.chat_service import get_chat_service, ChatService
from ..middleware.auth_middleware import get_current_user, get_current_tenant, get_current_user_id

# 导入Pipeline用于真正的RAG问答
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from pipeline import Pipeline, RunConfig
    from config import get_settings
    PIPELINE_AVAILABLE = True
    print("[OK] Chat API - Pipeline集成已启用")
except ImportError as e:
    print(f"[WARN] Chat API - Pipeline导入失败: {e}")
    PIPELINE_AVAILABLE = False
from .models import (
    QuestionRequest, QuestionResponse,
    CreateSessionRequest, UpdateSessionRequest,
    SessionResponse, SessionsResponse, MessagesResponse,
    ChatSession, ChatMessage
)

router = APIRouter(prefix="/chat", tags=["chat"])

# 注意：会话和消息现在已持久化到数据库，通过 ChatService 管理
# 不再使用内存存储（chat_sessions 和 chat_messages 字典已移除）


def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    scenario_service: ScenarioService = Depends(get_scenario_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    多场景智能问答

    需要认证，会话数据按租户隔离
    """
    try:
        start_time = datetime.now()

        print(f"[INFO] 用户 {current_user['username']} (租户: {tenant_id}) 提问: {request.question[:50]}...")

        # 验证场景
        if not scenario_service.validate_scenario(request.scenario_id):
            raise HTTPException(status_code=400, detail=f"无效场景: {request.scenario_id}")

        # 获取场景配置
        scenario_config = scenario_service.get_scenario_config(request.scenario_id)

        # 初始化返回变量
        answer = ""
        reasoning = ""
        confidence = 0.5
        sources = []

        # 使用真正的Pipeline进行RAG问答
        if PIPELINE_AVAILABLE:
            try:
                print(f"[INFO] 使用Pipeline进行RAG问答: {request.question}")

                # 获取设置
                settings = get_settings()

                # 创建Pipeline实例（启用完整RAG：向量检索 + BM25检索）
                # 重要：传递tenant_id以实现租户级数据隔离
                config = RunConfig(
                    api_provider="dashscope",
                    use_vector_dbs=True,  # 启用向量检索（主要检索方式）
                    use_bm25_db=True,     # 启用BM25检索（补充检索方式）
                    top_n_retrieval=10,
                )

                pipeline = Pipeline(
                    root_path=settings.data_dir,
                    run_config=config,
                    scenario_id=request.scenario_id,  # 传递场景ID
                    tenant_id=tenant_id  # 传递租户ID（实现租户隔离）
                )

                # 检查Pipeline是否就绪
                status = pipeline.get_status()
                print(f"📊 Pipeline状态: {status}")

                # 检查BM25索引是否存在（判断是否有文档）
                bm25_dir = settings.data_dir / "databases" / "bm25"
                bm25_files = list(bm25_dir.glob("*.pkl"))
                has_bm25_data = len(bm25_files) > 0

                # 检查FAISS索引是否存在
                vector_dir = settings.data_dir / "databases" / "vector_dbs"
                vector_files = list(vector_dir.glob("*.index")) if vector_dir.exists() else []
                has_vector_data = len(vector_files) > 0

                # 判断是否有任何文档数据
                has_documents = has_bm25_data or has_vector_data

                print(f"[DEBUG] BM25索引文件数量: {len(bm25_files)}, FAISS索引文件数量: {len(vector_files)}")
                print(f"[DEBUG] 是否有文档数据: {has_documents}")

                if has_documents:
                    # [OK] 直接使用 QuestionsProcessor 进行完整的Agentic RAG
                    print("[INFO] 使用Agentic RAG进行问答")
                    try:
                        from questions_processing import QuestionsProcessor

                        processor = QuestionsProcessor(
                            api_provider="dashscope",
                            scenario_id=request.scenario_id
                        )
                        rag_result = processor.process_question(
                            question=request.question,
                            company=request.company,
                            question_type=request.question_type or "string"
                        )

                        if rag_result.get("success"):
                            answer = rag_result.get("answer", "")
                            reasoning = rag_result.get("reasoning", "")

                            # 使用实际的置信度（来自答案验证）
                            confidence = rag_result.get("confidence", 0.7)
                            if isinstance(confidence, str):
                                confidence_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
                                confidence = confidence_map.get(confidence, 0.6)

                            # 处理来源信息
                            sources = rag_result.get("sources", [])

                            print(f"[OK] RAG问答完成: 置信度={confidence:.2f}")
                        else:
                            answer = "抱歉，暂时无法处理您的问题，请稍后重试。"
                            reasoning = "RAG处理失败"
                            confidence = 0.1
                            sources = []

                    except Exception as rag_error:
                        print(f"[ERROR] RAG调用失败: {str(rag_error)}")
                        answer = "抱歉，系统遇到技术问题，暂时无法回答。"
                        reasoning = "系统技术故障"
                        confidence = 0.1
                        sources = []
                else:
                    # 没有文档数据，直接使用纯LLM模式（快速响应，无需检索）
                    print("⚠️ 无文档数据，使用纯LLM快速响应模式")
                    try:
                        from dashscope_client import DashScopeClient

                        # 直接调用LLM API，跳过检索步骤
                        # DashScopeClient 会自动从 settings 读取所有配置（api_key, llm_model, embedding_model）
                        client = DashScopeClient()

                        # 构建系统提示词
                        system_prompt = f"""你是一个专业的{scenario_config.get('name', '智能')}助手。
请根据你的知识回答用户的问题。如果问题涉及具体文档内容，请提醒用户先上传相关文档以获得更准确的答案。"""

                        # 构建多轮对话消息（支持上下文）
                        messages = [
                            {'role': 'system', 'content': system_prompt}
                        ]

                        # 添加历史对话（最近5轮，避免 token 过多）
                        if request.session_id:
                            # 使用 ChatService 从数据库读取历史消息
                            history = chat_service.get_message_history_for_context(
                                session_id=request.session_id,
                                tenant_id=tenant_id,
                                max_messages=10  # 最近10条消息（5轮对话）
                            )
                            messages.extend(history)
                            print(f"📝 加载了 {len(history)} 条历史消息")

                        # 添加当前问题
                        messages.append({
                            'role': 'user',
                            'content': request.question
                        })

                        # 调用 LLM（使用 messages 模式）
                        llm_result = client.generate_text(
                            messages=messages,
                            temperature=0.7,
                            max_tokens=2000
                        )

                        # 正确处理返回值
                        if llm_result.get("success"):
                            answer = llm_result.get("text", "")
                            reasoning = "无文档数据，使用纯LLM知识快速回答"
                            confidence = 0.5
                            sources = []

                            # 保存到数据库（通过 ChatService）
                            if request.session_id:
                                # 保存用户消息
                                chat_service.create_message(
                                    session_id=request.session_id,
                                    role='user',
                                    content=request.question
                                )

                                # 保存助手回复
                                chat_service.create_message(
                                    session_id=request.session_id,
                                    role='assistant',
                                    content=answer,
                                    metadata={
                                        'reasoning': reasoning,
                                        'confidence': confidence,
                                        'sources': sources,
                                        'mode': 'pure_llm'
                                    }
                                )

                                # 获取消息数量
                                msg_count = chat_service.get_session_message_count(request.session_id, tenant_id)
                                print(f"💾 已保存到会话 {request.session_id}，当前共 {msg_count} 条消息")

                            print(f"[OK] 纯LLM快速响应完成")
                        else:
                            # LLM 调用失败
                            error_msg = llm_result.get("error", "未知错误")
                            print(f"[ERROR] LLM返回失败: {error_msg}")
                            answer = "抱歉，系统遇到技术问题，请稍后重试。"
                            reasoning = f"LLM调用失败: {error_msg}"
                            confidence = 0.1
                            sources = []

                    except Exception as llm_error:
                        print(f"[ERROR] LLM调用异常: {str(llm_error)}")
                        import traceback
                        traceback.print_exc()
                        answer = "抱歉，系统遇到技术问题，请稍后重试。"
                        reasoning = f"LLM调用异常: {str(llm_error)}"
                        confidence = 0.1
                        sources = []

            except Exception as pipeline_error:
                print(f"[ERROR] Pipeline问答失败: {str(pipeline_error)}")
                # 降级到真正的LLM调用
                try:
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
                    from questions_processing import QuestionsProcessor

                    processor = QuestionsProcessor(
                        api_provider="dashscope",
                        scenario_id=request.scenario_id
                    )
                    result = processor.process_question(
                        question=request.question,
                        company=request.company,
                        question_type=request.question_type or "string"
                    )

                    if result.get("success"):
                        answer = result.get("answer", "")
                        reasoning = f"Pipeline失败，使用纯LLM模式回答"
                        confidence = 0.6
                        sources = []
                        print("[OK] 降级到纯LLM成功")
                    else:
                        answer = "抱歉，系统暂时无法处理您的问题。"
                        reasoning = "Pipeline和LLM都失败"
                        confidence = 0.1
                        sources = []

                except Exception as fallback_error:
                    print(f"[ERROR] 降级LLM也失败: {str(fallback_error)}")
                    answer = "抱歉，系统遇到技术问题，请稍后重试。"
                    reasoning = "系统全面故障"
                    confidence = 0.1
                    sources = []
        else:
            # Pipeline不可用，使用真正的LLM API调用
            print("⚠️ Pipeline不可用，使用纯LLM模式")
            try:
                # 导入问题处理器进行纯LLM问答
                sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
                from questions_processing import QuestionsProcessor

                processor = QuestionsProcessor(
                    api_provider="dashscope",
                    scenario_id=request.scenario_id
                )
                result = processor.process_question(
                    question=request.question,
                    company=request.company,
                    question_type=request.question_type or "string"
                )

                if result.get("success"):
                    answer = result.get("answer", "")
                    reasoning = result.get("reasoning", "")
                    confidence = 0.7  # 纯LLM模式置信度
                    sources = []
                    print("[OK] 纯LLM问答成功")
                else:
                    answer = "抱歉，系统暂时无法处理您的问题，请稍后重试。"
                    reasoning = "LLM处理失败"
                    confidence = 0.1
                    sources = []
                    print("[ERROR] 纯LLM问答失败")

            except Exception as llm_error:
                print(f"[ERROR] LLM调用失败: {str(llm_error)}")
                answer = "抱歉，系统遇到技术问题，暂时无法回答您的问题。请检查网络连接或稍后重试。"
                reasoning = "系统技术故障"
                confidence = 0.1
                sources = []

        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()

        # 保存到数据库（通过 ChatService）
        if request.session_id:
            # 保存用户消息
            chat_service.create_message(
                session_id=request.session_id,
                role='user',
                content=request.question,
                metadata={"scenario_id": request.scenario_id}
            )

            # 保存助手回复
            chat_service.create_message(
                session_id=request.session_id,
                role='assistant',
                content=answer,
                metadata={
                    "scenario_id": request.scenario_id,
                    "confidence": 0.85,
                    "processing_time": processing_time,
                    "mode": "rag"
                }
            )

        return QuestionResponse(
            success=True,
            answer=answer,
            reasoning=reasoning,
            confidence=confidence,
            sources=sources,
            processing_time=processing_time,
            scenario_id=request.scenario_id,
            session_id=request.session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")


@router.get("/sessions", response_model=SessionsResponse)
async def get_sessions(
    scenario_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    获取会话列表

    需要认证，仅返回当前租户的会话（租户隔离由 ChatService 保障）
    """
    try:
        # 使用 ChatService 从数据库获取会话（已内置租户隔离）
        sessions = chat_service.get_user_sessions(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            limit=limit
        )

        print(f"[INFO] 用户 {current_user['username']} 获取会话列表: {len(sessions)} 个会话")

        return SessionsResponse(
            sessions=sessions,
            total=len(sessions)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.post("/sessions", response_model=ChatSession)
async def create_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    user_id: str = Depends(get_current_user_id),
    scenario_service: ScenarioService = Depends(get_scenario_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    创建新会话

    需要认证，自动关联用户和租户
    """
    try:
        # 验证场景
        if not scenario_service.validate_scenario(request.scenario_id):
            raise HTTPException(status_code=400, detail=f"无效场景: {request.scenario_id}")

        # 使用 ChatService 创建会话（持久化到数据库）
        session = chat_service.create_session(
            scenario_id=request.scenario_id,
            user_id=user_id,
            tenant_id=tenant_id,
            title=request.title
        )

        print(f"[INFO] 用户 {current_user['username']} 创建会话: {session.title}")

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    获取特定会话和消息

    需要认证，验证所有权（租户隔离由 ChatService 保障）
    """
    try:
        # 使用 ChatService 从数据库获取会话（已内置租户隔离和所有权验证）
        session = chat_service.get_session(session_id, tenant_id)

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或无权访问")

        # 获取消息
        messages = chat_service.get_session_messages(session_id, tenant_id)

        return SessionResponse(
            session=session,
            messages=messages
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


@router.put("/sessions/{session_id}", response_model=ChatSession)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    更新会话信息

    需要认证，验证所有权（租户隔离由 ChatService 保障）
    """
    try:
        # 使用 ChatService 更新会话（已内置租户隔离和所有权验证）
        session = chat_service.update_session(
            session_id=session_id,
            tenant_id=tenant_id,
            title=request.title
        )

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或无权修改")

        print(f"[INFO] 用户 {current_user['username']} 更新会话: {session_id}")

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新会话失败: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    删除会话（级联删除消息）

    需要认证，验证所有权（租户隔离由 ChatService 保障）
    """
    try:
        # 使用 ChatService 删除会话（已内置租户隔离和所有权验证，级联删除消息）
        success = chat_service.delete_session(session_id, tenant_id)

        if not success:
            raise HTTPException(status_code=404, detail="会话不存在或无权删除")

        print(f"[INFO] 用户 {current_user['username']} 删除会话: {session_id}")

        return {"message": "会话删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.get("/sessions/{session_id}/messages", response_model=MessagesResponse)
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话消息列表（租户隔离由 ChatService 保障）"""
    try:
        # 使用 ChatService 从数据库获取消息（已内置租户隔离和权限验证）
        messages = chat_service.get_session_messages(session_id, tenant_id)

        return MessagesResponse(
            messages=messages,
            total=len(messages)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话消息失败: {str(e)}")
