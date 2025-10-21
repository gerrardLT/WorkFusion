#!/usr/bin/env python
"""
多场景AI知识问答系统 - FastAPI后端服务
支持投研、招投标等多个业务场景的智能问答
"""

import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入服务和路由
from backend.database import init_database
from backend.services.scenario_service import get_scenario_service
from backend.api import scenarios, chat, upload, checklist, risk, knowledge, generate, company, recommendation, evaluation, preference, subscription, notification, auth
from backend.api.models import SystemStatus, HealthCheckResponse, ErrorResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("[START] 启动多场景AI知识问答系统...")

    try:
        # 初始化数据库
        if init_database():
            logger.info("[OK] 数据库初始化完成")
        else:
            logger.error("[ERROR] 数据库初始化失败")

        # 确保默认场景存在
        scenario_service = get_scenario_service()
        if scenario_service.ensure_default_scenarios():
            logger.info("[OK] 默认场景检查完成")
        else:
            logger.warning("⚠️ 默认场景检查失败")

        logger.info("🎉 系统启动完成")

    except Exception as e:
        logger.error(f"[ERROR] 系统启动失败: {str(e)}")

    yield

    # 关闭时清理
    logger.info("🔄 系统正在关闭...")
    logger.info("👋 系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="多场景AI知识问答系统",
    description="支持投研、招投标等多个业务场景的智能问答系统",
    version="2.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3005",
        "http://127.0.0.1:3005"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v2")  # 认证路由（无需认证）
app.include_router(scenarios.router, prefix="/api/v2")
app.include_router(chat.router, prefix="/api/v2")
app.include_router(upload.router, prefix="/api/v2")
app.include_router(checklist.router, prefix="/api/v2")
app.include_router(risk.router, prefix="/api/v2")
app.include_router(knowledge.router, prefix="/api/v2")
app.include_router(generate.router, prefix="/api/v2")
app.include_router(company.router, prefix="/api/v2")
app.include_router(recommendation.router, prefix="/api/v2")
app.include_router(evaluation.router, prefix="/api/v2")
app.include_router(preference.router, prefix="/api/v2")
app.include_router(subscription.router, prefix="/api/v2")
app.include_router(notification.router, prefix="/api/v2")

# 挂载静态文件目录（用于访问上传的头像等文件）
uploads_dir = Path("backend/data/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


# ============== 系统管理API ==============

@app.get("/", response_model=Dict[str, Any])
async def root():
    """根路径 - 系统信息"""
    return {
        "name": "多场景AI知识问答系统",
        "version": "2.0.0",
        "description": "支持投研、招投标等多个业务场景的智能问答系统",
        "status": "running",
        "timestamp": time.time(),
        "api_docs": "/docs",
        "api_version": "v2"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """健康检查"""
    try:
        # 检查各个服务状态
        services = {
            "database": "healthy",
            "scenario_service": "healthy",
            "document_service": "healthy"
        }

        # 检查场景服务
        try:
            scenario_service = get_scenario_service()
            scenarios = scenario_service.get_all_scenarios()
            if scenarios:
                services["scenario_service"] = "healthy"
            else:
                services["scenario_service"] = "warning"
        except Exception:
            services["scenario_service"] = "unhealthy"

        overall_status = "healthy"
        if "unhealthy" in services.values():
            overall_status = "unhealthy"
        elif "warning" in services.values():
            overall_status = "warning"

        return HealthCheckResponse(
            status=overall_status,
            timestamp=str(time.time()),
            services=services
        )

    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=str(time.time()),
            services={"error": str(e)}
        )


@app.get("/api/v2/system/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    try:
        scenario_service = get_scenario_service()

        # 获取场景列表
        scenarios = scenario_service.get_all_scenarios()

        # 获取统计信息
        stats = scenario_service.get_scenario_stats()
        total_documents = sum(stat.get("document_count", 0) for stat in stats)
        total_sessions = sum(stat.get("session_count", 0) for stat in stats)

        return SystemStatus(
            status="running",
            version="2.0.0",
            scenarios=[
                {
                    "id": s["id"],
                    "name": s["name"],
                    "status": s["status"],
                    "document_count": s.get("document_type_count", 0)
                } for s in scenarios
            ],
            database_status="connected",
            total_documents=total_documents,
            total_sessions=total_sessions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@app.get("/api/v2/system/info")
async def get_system_info():
    """获取系统详细信息"""
    try:
        scenario_service = get_scenario_service()

        return {
            "system": {
                "name": "多场景AI知识问答系统",
                "version": "2.0.0",
                "description": "支持投研、招投标等多个业务场景的智能问答系统"
            },
            "features": [
                "多场景支持",
                "智能文档处理",
                "上下文对话",
                "文档向量检索",
                "实时问答"
            ],
            "supported_scenarios": [
                {
                    "id": "investment",
                    "name": "投资研究",
                    "description": "专业的投资分析和财务研究"
                },
                {
                    "id": "tender",
                    "name": "招投标",
                    "description": "招标文件分析和投标方案优化"
                }
            ],
            "api": {
                "version": "v2",
                "base_url": "/api/v2",
                "docs_url": "/docs"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")


# ============== 错误处理 ==============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP {exc.status_code}",
            message=exc.detail,
            timestamp=str(time.time())
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="服务器内部错误",
            details={"exception": str(exc)},
            timestamp=str(time.time())
        ).dict()
    )


# ============== 兼容性API ==============

@app.get("/companies")
async def get_companies():
    """获取公司列表（兼容旧版本）"""
    return {
        "companies": [
            {"name": "中芯国际", "code": "688981"},
            {"name": "比亚迪", "code": "002594"},
            {"name": "宁德时代", "code": "300750"}
        ]
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("[START] 启动开发服务器...")
    uvicorn.run(
        "main_multi_scenario:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[
            "start_system.py",
            "start_system_with_logs.py",
            "quick_start.py",
            "*.log",
            "logs/*",
            "data/*",
            ".git/*",
            "frontend-next/*"
        ],
        log_level="info"
    )
