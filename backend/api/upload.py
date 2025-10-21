"""
多场景文件上传API路由
"""

import os
import sys
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.background import BackgroundTasks

# 添加src路径以使用Pipeline
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ..services.scenario_service import get_scenario_service, ScenarioService
from ..services.document_service import get_document_service, DocumentService
from ..services.progress_manager import get_progress_manager
from ..services.checklist_service import get_checklist_service
from ..middleware.auth_middleware import get_current_user, get_current_tenant, get_current_user_id
from .models import UploadResponse, ProcessingStatus
import logging

logger = logging.getLogger(__name__)

# 导入Pipeline相关
try:
    # 尝试导入Pipeline相关模块
    from src.pipeline import Pipeline, RunConfig
    # 直接从src.config模块导入get_settings
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from config import get_settings
    PIPELINE_AVAILABLE = True
    print("[OK] Pipeline集成已启用")
except ImportError as e:
    print(f"⚠️ Pipeline导入失败: {e}")
    PIPELINE_AVAILABLE = False

router = APIRouter(prefix="/upload", tags=["upload"])

# 上传文件存储目录
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def generate_filename(original_filename: str, scenario_id: str) -> str:
    """生成唯一文件名"""
    file_ext = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())[:8]
    return f"{scenario_id}_{unique_id}_{original_filename}"


def generate_checklist_background(document_id: str, scenario_id: str):
    """后台任务：为文档生成Checklist"""
    try:
        logger.info(f"🔄 开始为文档 {document_id} 生成任务清单（后台任务）")

        checklist_service = get_checklist_service()
        checklist_id = checklist_service.generate_checklist(
            document_id=document_id,
            scenario_id=scenario_id
        )

        if checklist_id:
            logger.info(f"[OK] 文档 {document_id} 的任务清单生成成功: {checklist_id}")
        else:
            logger.error(f"[ERROR] 文档 {document_id} 的任务清单生成失败")

    except Exception as e:
        logger.error(f"[ERROR] 后台生成任务清单失败: {str(e)}", exc_info=True)


def process_document_sync(
    document_id: str,
    file_path: str,
    scenario_id: str,
    document_service: DocumentService,
    tenant_id: str = "default"  # 新增：租户ID参数
) -> dict:
    """
    同步处理文档并返回结果（只处理本次上传的文件）

    Args:
        document_id: 文档ID
        file_path: 文件路径
        scenario_id: 场景ID
        document_service: 文档服务
        tenant_id: 租户ID（用于索引隔离）
    """
    progress_manager = get_progress_manager()

    try:
        # 开始处理文档
        progress_manager.update_progress(
            document_id,
            stage='parsing',
            progress=0,
            message='开始处理文档...'
        )

        # 更新状态为处理中
        document_service.update_document_status(document_id, "processing")

        if not PIPELINE_AVAILABLE:
            # Pipeline不可用，无法进行真实文档处理
            document_service.update_document_status(document_id, "failed")
            return {
                "success": False,
                "message": "Pipeline不可用，无法进行文档处理",
                "chunks_created": 0,
                "vectors_created": 0
            }

        # 🔧 使用单文件处理模式（只处理本次上传的文件，不重复处理历史文件）
        from src.pdf_parsing_mineru import PDFParsingPipeline
        from src.ingestion import IngestionPipeline

        settings = get_settings()
        data_dir = settings.data_dir

        # 设置输出目录（租户级隔离）
        parsed_output_dir = data_dir / "debug_data" / "parsed_reports"
        vector_output_dir = data_dir / "databases" / "vector_dbs" / tenant_id / scenario_id
        bm25_output_dir = data_dir / "databases" / "bm25" / tenant_id / scenario_id

        parsed_output_dir.mkdir(parents=True, exist_ok=True)
        vector_output_dir.mkdir(parents=True, exist_ok=True)
        bm25_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] 租户级索引目录:")
        print(f"  向量索引: {vector_output_dir}")
        print(f"  BM25索引: {bm25_output_dir}")

        # 1️⃣ 解析本次上传的PDF文件（使用MinerU）
        print(f"📄 开始解析PDF: {Path(file_path).name}")

        # 创建进度回调函数
        def progress_callback(stage, progress, message, total_pages=None, current_page=None):
            progress_manager.update_progress(
                document_id,
                stage=stage,
                progress=progress,
                message=message,
                total_pages=total_pages,
                current_page=current_page
            )

        pdf_parser = PDFParsingPipeline(scenario_id=scenario_id, progress_callback=progress_callback)
        success, parse_result = pdf_parser.parse_pdf_file(
            str(file_path),
            str(parsed_output_dir)
        )

        if not success:
            document_service.update_document_status(document_id, "failed")
            return {
                "success": False,
                "message": f"PDF解析失败: {parse_result.get('error', 'Unknown error')}",
                "chunks_created": 0,
                "vectors_created": 0
            }

        print(f"[OK] PDF解析完成")

        # 2️⃣ 对本次上传的文件进行向量化和BM25索引
        print(f"🔢 开始向量化处理...")

        # 更新进度：开始向量化
        progress_manager.update_progress(
            document_id,
            stage='vectorizing',
            progress=35,
            message='开始向量化处理...'
        )

        # 获取解析结果
        parsed_data = parse_result["parsed_result"]

        # 创建向量化和BM25索引
        ingestion = IngestionPipeline(api_provider="dashscope")

        # 向量化
        progress_manager.update_progress(
            document_id,
            stage='vectorizing',
            progress=50,
            message='正在生成向量索引...'
        )

        vector_success, vector_result = ingestion.vector_ingestor.process_single_report(
            parsed_data,
            vector_output_dir
        )

        # BM25索引
        progress_manager.update_progress(
            document_id,
            stage='vectorizing',
            progress=75,
            message='正在生成 BM25 索引...'
        )

        bm25_success, bm25_result = ingestion.bm25_ingestor.process_single_report(
            parsed_data,
            bm25_output_dir
        )

        print(f"[OK] 向量化完成: vector={vector_success}, bm25={bm25_success}")

        # 统计文档块数量
        chunks_created = len(parsed_data.get("pages", []))

        # 更新文档状态
        if vector_success and bm25_success:
            document_service.update_document_status(document_id, "completed", quality_score=0.9)
            status = "completed"
            message = "文档处理完成"
        else:
            document_service.update_document_status(document_id, "completed", quality_score=0.6)
            status = "partial"
            message = "文档处理部分完成"

        # 更新进度：完成
        progress_manager.update_progress(
            document_id,
            stage='completed',
            progress=100,
            message='文档处理完成！'
        )

        result = {
            "success": True,
            "message": message,
            "status": status,
            "chunks_created": chunks_created,
            "vectors_created": 1 if vector_success else 0,
            "bm25_created": 1 if bm25_success else 0,
            "processing_details": {
                "file_id": parse_result.get("file_id"),
                "parsed_output": parse_result.get("output_path"),
                "vector_output": vector_result if vector_success else None,
                "bm25_output": bm25_result if bm25_success else None
            }
        }

        print(f"[OK] 文档处理完成: {Path(file_path).name}")
        return result

    except Exception as e:
        # 文档处理失败
        import traceback
        traceback.print_exc()

        # 更新状态为失败
        document_service.update_document_status(document_id, "failed")

        # 更新进度：错误
        progress_manager.update_progress(
            document_id,
            stage='error',
            progress=0,
            message=f'处理失败: {str(e)}'
        )

        return {
            "success": False,
            "message": f"文档处理失败: {str(e)}",
            "chunks_created": 0,
            "vectors_created": 0
        }


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    scenario_id: str = Form(...),
    title: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    user_id: str = Depends(get_current_user_id),
    scenario_service: ScenarioService = Depends(get_scenario_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    上传单个文件到指定场景并同步处理

    需要认证，文档自动关联到当前租户和用户
    """
    try:
        print(f"[INFO] 用户 {current_user['username']} (租户: {tenant_id}) 上传文件: {file.filename}")

        # 验证场景
        if not scenario_service.validate_scenario(scenario_id):
            raise HTTPException(status_code=400, detail=f"无效场景: {scenario_id}")

        # 检查文件
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 检查文件扩展名
        allowed_extensions = ['.pdf', '.txt', '.docx', '.doc']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}"
            )

        # 检查文件大小
        file_content = await file.read()
        file_size = len(file_content)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="文件不能为空")

        # 检查文件大小限制 (50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            raise HTTPException(status_code=400, detail=f"文件过大: {file_size/1024/1024:.1f}MB，最大支持50MB")

        # 生成租户级文件路径（避免文件名冲突）
        filename = f"{tenant_id}_{generate_filename(file.filename, scenario_id)}"
        file_path = UPLOAD_DIR / filename

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        print(f"[OK] 文件已保存: {file_path}")

        # 处理文档元数据
        document_title = title or file.filename
        document_id = document_service.process_document(
            scenario_id=scenario_id,
            file_path=str(file_path),
            title=document_title,
            file_size=file_size,
            additional_metadata={
                "original_filename": file.filename,
                "upload_filename": filename,
                "file_extension": file_ext,
                "tenant_id": tenant_id,  # 新增：租户信息
                "uploaded_by": user_id   # 新增：上传者信息
            }
        )

        if not document_id:
            # 删除已保存的文件
            if file_path.exists():
                os.remove(file_path)
            raise HTTPException(status_code=500, detail="文档元数据处理失败")

        # 文档记录已创建

        # 同步处理文档（PDF解析 + 向量化）
        # 注意：需要传递tenant_id以实现租户级索引隔离
        processing_result = process_document_sync(
            document_id,
            str(file_path),
            scenario_id,
            document_service,
            tenant_id=tenant_id  # 新增：租户ID用于索引隔离
        )

        # 【新增】如果文档处理成功，且是招投标场景，自动生成Checklist
        if processing_result["success"] and scenario_id == "tender" and background_tasks:
            logger.info(f"📋 文档处理成功，添加Checklist生成任务到后台队列")
            background_tasks.add_task(
                generate_checklist_background,
                document_id,
                scenario_id
            )

        # 构建响应
        response = {
            "success": processing_result["success"],
            "message": processing_result["message"],
            "document_id": document_id,
            "filename": file.filename,
            "file_size": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "scenario_id": scenario_id,
            "processing_stats": {
                "chunks_created": processing_result.get("chunks_created", 0),
                "vectors_created": processing_result.get("vectors_created", 0),
                "pipeline_ready": processing_result.get("pipeline_ready", False)
            },
            "checklist_generation": "queued" if (processing_result["success"] and scenario_id == "tender") else "skipped"
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        # 清理文件
        if 'file_path' in locals() and Path(file_path).exists():
            os.remove(file_path)

        import traceback
        print(f"[ERROR] 上传处理失败: {str(e)}")
        traceback.print_exc()

        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/status/{document_id}", response_model=ProcessingStatus)
async def get_processing_status(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """获取文档处理状态"""
    try:
        document = document_service.get_document(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 计算进度
        progress = 0.0
        if document["status"] == "pending":
            progress = 0.0
        elif document["status"] == "processing":
            progress = 0.5
        elif document["status"] == "completed":
            progress = 1.0
        elif document["status"] == "failed":
            progress = 0.0

        return ProcessingStatus(
            document_id=document_id,
            status=document["status"],
            progress=progress,
            message=f"文档{document['status']}",
            created_at=document["created_at"],
            updated_at=document["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取处理状态失败: {str(e)}")


@router.get("/documents")
async def get_documents(
    scenario_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    scenario_service: ScenarioService = Depends(get_scenario_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    获取文档列表

    需要认证，仅返回当前租户的文档
    """
    try:
        if scenario_id:
            # 验证场景
            if not scenario_service.validate_scenario(scenario_id):
                raise HTTPException(status_code=400, detail=f"无效场景: {scenario_id}")

            # TODO: 需要修改document_service以支持租户过滤
            # documents = document_service.get_documents_by_scenario_and_tenant(scenario_id, tenant_id, limit)
            documents = document_service.get_documents_by_scenario(scenario_id, limit)

            # 临时过滤：仅返回当前租户的文档
            # 注意：这是临时方案，应该在数据库查询层面实现过滤
            filtered_documents = []
            for doc in documents:
                if hasattr(doc, 'tenant_id') and doc.tenant_id == tenant_id:
                    filtered_documents.append(doc)
                elif not hasattr(doc, 'tenant_id'):
                    # 兼容旧数据（没有tenant_id的文档）
                    filtered_documents.append(doc)

            documents = filtered_documents
        else:
            # 获取当前租户的所有文档
            # TODO: 需要实现get_documents_by_tenant方法
            documents = []

        print(f"[INFO] 用户 {current_user['username']} 获取文档列表: {len(documents)} 个文档")

        return {
            "documents": documents,
            "total": len(documents),
            "scenario_id": scenario_id,
            "tenant_id": tenant_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.post("/batch")
async def upload_files_batch(
    files: List[UploadFile] = File(...),
    scenario_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
    user_id: str = Depends(get_current_user_id),
    scenario_service: ScenarioService = Depends(get_scenario_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    批量上传文件到指定场景并同步处理（只处理本次上传的文件）

    需要认证，文档自动关联到当前租户和用户
    """
    try:
        print(f"[INFO] 用户 {current_user['username']} (租户: {tenant_id}) 批量上传 {len(files)} 个文件")

        # 验证场景
        if not scenario_service.validate_scenario(scenario_id):
            raise HTTPException(status_code=400, detail=f"无效场景: {scenario_id}")

        if not files:
            raise HTTPException(status_code=400, detail="未选择文件")

        print(f"[INFO] 批量上传 {len(files)} 个文件到场景 {scenario_id}")

        results = []
        successful = 0
        failed = 0

        # 处理每个上传的文件
        for file in files:
            try:
                # 检查文件
                if not file.filename:
                    results.append({
                        "filename": "unknown",
                        "success": False,
                        "error": "文件名不能为空"
                    })
                    failed += 1
                    continue

                # 检查文件扩展名
                allowed_extensions = ['.pdf', '.txt', '.docx', '.doc']
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in allowed_extensions:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"不支持的文件类型: {file_ext}"
                    })
                    failed += 1
                    continue

                # 检查文件大小
                file_content = await file.read()
                file_size = len(file_content)

                if file_size == 0:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": "文件不能为空"
                    })
                    failed += 1
                    continue

                max_size = 50 * 1024 * 1024  # 50MB
                if file_size > max_size:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"文件过大: {file_size/1024/1024:.1f}MB"
                    })
                    failed += 1
                    continue

                # 生成租户级文件路径并保存
                filename = f"{tenant_id}_{generate_filename(file.filename, scenario_id)}"
                file_path = UPLOAD_DIR / filename

                with open(file_path, "wb") as f:
                    f.write(file_content)

                print(f"[OK] 文件已保存: {file.filename}")

                # 处理文档元数据
                document_id = document_service.process_document(
                    scenario_id=scenario_id,
                    file_path=str(file_path),
                    title=file.filename,
                    file_size=file_size,
                    additional_metadata={
                        "original_filename": file.filename,
                        "upload_filename": filename,
                        "file_extension": file_ext,
                        "batch_upload": True,
                        "tenant_id": tenant_id,  # 新增：租户信息
                        "uploaded_by": user_id   # 新增：上传者信息
                    }
                )

                if not document_id:
                    if file_path.exists():
                        os.remove(file_path)
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": "文档元数据处理失败"
                    })
                    failed += 1
                    continue

                # 同步处理文档（传递租户ID用于索引隔离）
                processing_result = process_document_sync(
                    document_id,
                    str(file_path),
                    scenario_id,
                    document_service,
                    tenant_id=tenant_id  # 新增：租户ID用于索引隔离
                )

                results.append({
                    "filename": file.filename,
                    "success": processing_result["success"],
                    "document_id": document_id,
                    "file_size_mb": round(file_size / 1024 / 1024, 2),
                    "chunks_created": processing_result.get("chunks_created", 0),
                    "vectors_created": processing_result.get("vectors_created", 0),
                    "message": processing_result.get("message", "")
                })

                if processing_result["success"]:
                    successful += 1
                    print(f"[OK] {file.filename} 处理成功")
                else:
                    failed += 1
                    print(f"[ERROR] {file.filename} 处理失败")

            except Exception as e:
                results.append({
                    "filename": file.filename if file.filename else "unknown",
                    "success": False,
                    "error": str(e)
                })
                failed += 1
                print(f"[ERROR] {file.filename} 处理异常: {str(e)}")

        return {
            "success": failed == 0,
            "total": len(files),
            "successful": successful,
            "failed": failed,
            "results": results,
            "scenario_id": scenario_id,
            "message": f"批量上传完成: 成功 {successful}/{len(files)}"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.get("/progress/{document_id}")
async def get_upload_progress(document_id: str):
    """获取文档处理进度

    Args:
        document_id: 文档ID

    Returns:
        进度信息
    """
    progress_manager = get_progress_manager()
    progress = progress_manager.get_progress(document_id)

    if progress is None:
        raise HTTPException(status_code=404, detail="未找到该文档的进度信息")

    return progress


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """删除文档"""
    try:
        # 获取文档信息
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 删除文件
        file_path = Path(document["file_path"])
        if file_path.exists():
            os.remove(file_path)

        # 删除数据库记录
        success = document_service.delete_document(document_id)

        if not success:
            raise HTTPException(status_code=500, detail="删除文档失败")

        # 清理进度信息
        progress_manager = get_progress_manager()
        progress_manager.remove_progress(document_id)

        return {"message": "文档删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")
