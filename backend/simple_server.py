#!/usr/bin/env python
"""
简化版多场景后端服务 - 用于快速测试
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 简单的数据模型
class QuestionRequest(BaseModel):
    question: str
    scenario_id: str
    session_id: str = None
    company: str = None

class QuestionResponse(BaseModel):
    success: bool
    answer: str
    reasoning: str
    confidence: float
    sources: List[Dict[str, Any]]
    processing_time: float
    scenario_id: str
    session_id: str = None

class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    document_type_count: int
    created_at: str
    updated_at: str
    config: Dict[str, Any]

# 创建FastAPI应用
app = FastAPI(
    title="多场景AI知识问答系统 (简化版)",
    description="支持投研、招投标等多个业务场景的智能问答系统",
    version="2.0.0-simple"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟数据
MOCK_SCENARIOS = [
    {
        "id": "investment",
        "name": "投资研究",
        "description": "专业的投资分析和财务研究",
        "status": "active",
        "document_type_count": 1,
        "created_at": "2025-09-25T12:48:33",
        "updated_at": "2025-09-25T12:48:33",
        "config": {
            "theme": {
                "primaryColor": "blue",
                "gradientFrom": "from-blue-600",
                "gradientTo": "to-purple-600",
                "iconColor": "text-blue-600"
            },
            "ui": {
                "welcomeTitle": "欢迎使用投研RAG智能问答",
                "welcomeMessage": "我是您的专业AI投研分析师，擅长解读财务数据、市场趋势和投资机会",
                "placeholderText": "请输入您的投资研究问题...",
                "uploadAreaTitle": "上传投研文档",
                "uploadAreaDescription": "支持上传研究报告、财务报表等文档"
            },
            "presetQuestions": [
                "中芯国际的最新财务状况如何？",
                "比亚迪和宁德时代在电池技术上的差异",
                "新能源汽车行业的发展趋势",
                "分析一下最新的财务报表"
            ],
            "documentTypes": [
                {
                    "id": "research_report",
                    "name": "投研报告",
                    "extensions": [".pdf", ".docx"],
                    "maxSize": 52428800
                }
            ]
        }
    },
    {
        "id": "tender",
        "name": "招投标",
        "description": "招标文件分析和投标方案优化",
        "status": "active",
        "document_type_count": 1,
        "created_at": "2025-09-25T12:48:33",
        "updated_at": "2025-09-25T12:48:33",
        "config": {
            "theme": {
                "primaryColor": "green",
                "gradientFrom": "from-green-600",
                "gradientTo": "to-teal-600",
                "iconColor": "text-green-600"
            },
            "ui": {
                "welcomeTitle": "欢迎使用招投标智能助手",
                "welcomeMessage": "我是您的专业招投标分析师，帮助您解读招标文件、分析投标要求",
                "placeholderText": "请输入您的招投标相关问题...",
                "uploadAreaTitle": "上传招投标文档",
                "uploadAreaDescription": "支持上传招标文件、投标书、技术方案等文档"
            },
            "presetQuestions": [
                "这个招标项目的主要技术要求是什么？",
                "投标截止时间和开标时间是什么时候？",
                "参与投标需要哪些资质证书？",
                "项目预算范围是多少？"
            ],
            "documentTypes": [
                {
                    "id": "tender_document",
                    "name": "招标文件",
                    "extensions": [".pdf", ".doc", ".docx"],
                    "maxSize": 104857600
                }
            ]
        }
    }
]

# 根路径
@app.get("/")
async def root():
    return {
        "name": "多场景AI知识问答系统 (简化版)",
        "version": "2.0.0-simple",
        "status": "running",
        "timestamp": time.time()
    }

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": str(time.time()),
        "services": {
            "api": "healthy",
            "database": "simulated"
        }
    }

# 场景API
@app.get("/api/v2/scenarios/")
async def get_scenarios():
    return {
        "scenarios": MOCK_SCENARIOS,
        "total": len(MOCK_SCENARIOS)
    }

@app.get("/api/v2/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    scenario = next((s for s in MOCK_SCENARIOS if s["id"] == scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"场景不存在: {scenario_id}")
    return scenario

@app.get("/api/v2/scenarios/{scenario_id}/config")
async def get_scenario_config(scenario_id: str):
    scenario = next((s for s in MOCK_SCENARIOS if s["id"] == scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"场景不存在: {scenario_id}")

    config = scenario["config"]
    return {
        "ui": config["ui"],
        "theme": config["theme"],
        "preset_questions": config["presetQuestions"],
        "document_types": config["documentTypes"]
    }

@app.get("/api/v2/scenarios/{scenario_id}/validate")
async def validate_scenario(scenario_id: str):
    scenario = next((s for s in MOCK_SCENARIOS if s["id"] == scenario_id), None)
    return {
        "scenario_id": scenario_id,
        "valid": scenario is not None,
        "message": "场景有效" if scenario else "场景无效或不存在"
    }

@app.get("/api/v2/scenarios/{scenario_id}/preset-questions")
async def get_preset_questions(scenario_id: str):
    scenario = next((s for s in MOCK_SCENARIOS if s["id"] == scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"场景不存在: {scenario_id}")

    questions = scenario["config"]["presetQuestions"]
    return {
        "scenario_id": scenario_id,
        "preset_questions": questions,
        "count": len(questions)
    }

# 问答API
@app.post("/api/v2/chat/ask")
async def ask_question_v2(request: QuestionRequest):
    start_time = time.time()

    # 验证场景
    scenario = next((s for s in MOCK_SCENARIOS if s["id"] == request.scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=400, detail=f"无效场景: {request.scenario_id}")

    # 生成模拟回答
    if request.scenario_id == "investment":
        answer = f"基于投研场景分析：{request.question}\n\n这是一个模拟的投资研究回答。在实际系统中，这里会调用RAG模型进行智能问答。"
        reasoning = "通过分析相关投资研究报告和财务数据得出结论"
    elif request.scenario_id == "tender":
        answer = f"基于招投标场景分析：{request.question}\n\n这是一个模拟的招投标回答。在实际系统中，这里会调用RAG模型进行智能问答。"
        reasoning = "通过分析招标文件和相关技术要求得出结论"
    else:
        answer = f"基于{request.scenario_id}场景分析：{request.question}\n\n这是一个通用的模拟回答。"
        reasoning = "通过分析相关文档和数据得出结论"

    processing_time = time.time() - start_time

    return QuestionResponse(
        success=True,
        answer=answer,
        reasoning=reasoning,
        confidence=0.85,
        sources=[],
        processing_time=processing_time,
        scenario_id=request.scenario_id,
        session_id=request.session_id
    )

# 兼容旧版API的问答接口
class LegacyQuestionRequest(BaseModel):
    question: str
    question_type: str = "string"
    company: Optional[str] = None
    session_id: Optional[str] = None

class LegacyQuestionResponse(BaseModel):
    success: bool = True
    answer: str
    reasoning: str = ""
    confidence: float = 0.85
    relevant_pages: List[int] = []
    processing_time: float = 0.0
    mode: str = "pure_llm"
    note: str = ""

@app.post("/ask")
async def ask_question_legacy(request: LegacyQuestionRequest):
    """兼容旧版的问答接口 - 支持纯LLM模式"""
    start_time = time.time()

    # 生成基于问题的智能回答
    answer = f"""基于您的问题：{request.question}

这是一个基于纯LLM模式的智能回答。系统当前运行在无文档模式下，提供基于大语言模型的通用知识问答。

如需获得基于特定文档的精准回答，请：
1. 上传相关PDF文档到系统
2. 等待文档处理完成
3. 重新提问以获得RAG增强的回答

当前模式优势：
- 响应速度快
- 覆盖通用知识
- 支持多轮对话

如有具体的投资研究、招投标或企业管理相关问题，建议上传相关文档以获得更准确的专业回答。"""

    processing_time = time.time() - start_time

    return LegacyQuestionResponse(
        success=True,
        answer=answer,
        reasoning="基于大语言模型的通用知识回答",
        confidence=0.75,
        relevant_pages=[],
        processing_time=processing_time,
        mode="pure_llm",
        note="当前为纯LLM模式，如需基于文档的精准回答，请上传相关PDF文档"
    )

# 系统信息
@app.get("/api/v2/system/status")
async def get_system_status():
    return {
        "status": "running",
        "version": "2.0.0-simple",
        "scenarios": [
            {
                "id": s["id"],
                "name": s["name"],
                "status": s["status"],
                "document_count": 0
            } for s in MOCK_SCENARIOS
        ],
        "database_status": "simulated",
        "total_documents": 0,
        "total_sessions": 0
    }

# 兼容性API
@app.get("/companies")
async def get_companies():
    return {
        "companies": [
            {"name": "中芯国际", "code": "688981"},
            {"name": "比亚迪", "code": "002594"},
            {"name": "宁德时代", "code": "300750"}
        ]
    }

if __name__ == "__main__":
    import uvicorn

    print("🚀 启动简化版多场景后端服务...")
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
