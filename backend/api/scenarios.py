"""
场景管理API路由
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from ..services.scenario_service import get_scenario_service, ScenarioService
from .models import ScenarioResponse, ScenarioListResponse, ScenarioConfigResponse, ErrorResponse

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("/", response_model=ScenarioListResponse)
async def get_scenarios(
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """获取所有场景列表"""
    try:
        scenarios_data = scenario_service.get_all_scenarios()

        scenarios = []
        for scenario_data in scenarios_data:
            scenarios.append(ScenarioResponse(**scenario_data))

        return ScenarioListResponse(
            scenarios=scenarios,
            total=len(scenarios)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取场景列表失败: {str(e)}")


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """获取特定场景信息"""
    try:
        scenario_data = scenario_service.get_scenario(scenario_id)

        if not scenario_data:
            raise HTTPException(status_code=404, detail=f"场景不存在: {scenario_id}")

        return ScenarioResponse(**scenario_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取场景失败: {str(e)}")


@router.get("/{scenario_id}/config", response_model=ScenarioConfigResponse)
async def get_scenario_config(
    scenario_id: str,
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """获取场景配置信息"""
    try:
        # 验证场景存在
        if not scenario_service.validate_scenario(scenario_id):
            raise HTTPException(status_code=404, detail=f"场景不存在: {scenario_id}")

        # 获取各种配置
        ui_config = scenario_service.get_ui_config(scenario_id) or {}
        theme_config = scenario_service.get_theme_config(scenario_id) or {}
        preset_questions = scenario_service.get_preset_questions(scenario_id)
        document_types = scenario_service.get_document_types(scenario_id)

        return ScenarioConfigResponse(
            ui=ui_config,
            theme=theme_config,
            preset_questions=preset_questions,
            document_types=document_types
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取场景配置失败: {str(e)}")


@router.get("/{scenario_id}/validate")
async def validate_scenario(
    scenario_id: str,
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """验证场景是否有效"""
    try:
        is_valid = scenario_service.validate_scenario(scenario_id)

        return {
            "scenario_id": scenario_id,
            "valid": is_valid,
            "message": "场景有效" if is_valid else "场景无效或不存在"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证场景失败: {str(e)}")


@router.get("/{scenario_id}/preset-questions")
async def get_preset_questions(
    scenario_id: str,
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """获取场景预设问题"""
    try:
        # 验证场景存在
        if not scenario_service.validate_scenario(scenario_id):
            raise HTTPException(status_code=404, detail=f"场景不存在: {scenario_id}")

        questions = scenario_service.get_preset_questions(scenario_id)

        return {
            "scenario_id": scenario_id,
            "preset_questions": questions,
            "count": len(questions)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预设问题失败: {str(e)}")


@router.get("/stats/overview")
async def get_scenario_stats(
    scenario_service: ScenarioService = Depends(get_scenario_service)
):
    """获取场景统计信息"""
    try:
        stats = scenario_service.get_scenario_stats()

        return {
            "total_scenarios": len(stats),
            "scenario_stats": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取场景统计失败: {str(e)}")
