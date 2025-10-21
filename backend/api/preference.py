# backend/api/preference.py
"""
用户偏好设置API
提供项目收藏、忽略等功能
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db_session
from backend.models import UserPreference, PreferenceType

logger = logging.getLogger(__name__)

# Pydantic模型
class SetPreferenceRequest(BaseModel):
    company_id: str
    project_id: str
    preference_type: str  # "favorite" or "ignore"
    is_active: bool = True

class PreferenceResponse(BaseModel):
    company_id: str
    project_id: str
    preference_type: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class PreferenceListResponse(BaseModel):
    preferences: List[PreferenceResponse]
    total: int

router = APIRouter(prefix="/preference", tags=["preference"])


@router.post("/set", response_model=PreferenceResponse)
async def set_preference(
    request: SetPreferenceRequest,
    db: Session = Depends(get_db_session)
):
    """
    设置用户偏好（收藏/忽略）
    """
    try:
        # 验证preference_type
        if request.preference_type not in [PreferenceType.FAVORITE.value, PreferenceType.IGNORE.value]:
            raise HTTPException(status_code=400, detail="无效的偏好类型")

        # 查找是否已存在
        existing = db.query(UserPreference).filter(
            UserPreference.company_id == request.company_id,
            UserPreference.project_id == request.project_id
        ).first()

        if existing:
            # 更新现有记录
            existing.preference_type = request.preference_type
            existing.is_active = request.is_active
            db.commit()
            db.refresh(existing)
            logger.info(f"更新偏好设置: company={request.company_id}, project={request.project_id}, type={request.preference_type}")

            return PreferenceResponse(
                company_id=existing.company_id,
                project_id=existing.project_id,
                preference_type=existing.preference_type,
                is_active=existing.is_active,
                created_at=existing.created_at.isoformat(),
                updated_at=existing.updated_at.isoformat()
            )
        else:
            # 创建新记录
            new_pref = UserPreference(
                company_id=request.company_id,
                project_id=request.project_id,
                preference_type=request.preference_type,
                is_active=request.is_active
            )
            db.add(new_pref)
            db.commit()
            db.refresh(new_pref)
            logger.info(f"创建偏好设置: company={request.company_id}, project={request.project_id}, type={request.preference_type}")

            return PreferenceResponse(
                company_id=new_pref.company_id,
                project_id=new_pref.project_id,
                preference_type=new_pref.preference_type,
                is_active=new_pref.is_active,
                created_at=new_pref.created_at.isoformat(),
                updated_at=new_pref.updated_at.isoformat()
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置偏好失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"设置偏好失败: {str(e)}")


@router.get("/list", response_model=PreferenceListResponse)
async def list_preferences(
    company_id: str,
    preference_type: str = None,
    is_active: bool = True,
    db: Session = Depends(get_db_session)
):
    """
    获取用户偏好列表
    """
    try:
        query = db.query(UserPreference).filter(
            UserPreference.company_id == company_id,
            UserPreference.is_active == is_active
        )

        if preference_type:
            query = query.filter(UserPreference.preference_type == preference_type)

        preferences = query.all()

        return PreferenceListResponse(
            preferences=[
                PreferenceResponse(
                    company_id=pref.company_id,
                    project_id=pref.project_id,
                    preference_type=pref.preference_type,
                    is_active=pref.is_active,
                    created_at=pref.created_at.isoformat(),
                    updated_at=pref.updated_at.isoformat()
                )
                for pref in preferences
            ],
            total=len(preferences)
        )
    except Exception as e:
        logger.error(f"获取偏好列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取偏好列表失败: {str(e)}")


@router.get("/check")
async def check_preference(
    company_id: str,
    project_id: str,
    db: Session = Depends(get_db_session)
):
    """
    检查特定项目的偏好状态
    """
    try:
        pref = db.query(UserPreference).filter(
            UserPreference.company_id == company_id,
            UserPreference.project_id == project_id,
            UserPreference.is_active == True
        ).first()

        if pref:
            return {
                "has_preference": True,
                "preference_type": pref.preference_type,
                "is_favorite": pref.preference_type == PreferenceType.FAVORITE.value,
                "is_ignored": pref.preference_type == PreferenceType.IGNORE.value
            }
        else:
            return {
                "has_preference": False,
                "preference_type": None,
                "is_favorite": False,
                "is_ignored": False
            }
    except Exception as e:
        logger.error(f"检查偏好失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检查偏好失败: {str(e)}")


@router.delete("/remove")
async def remove_preference(
    company_id: str,
    project_id: str,
    db: Session = Depends(get_db_session)
):
    """
    移除偏好设置（软删除）
    """
    try:
        pref = db.query(UserPreference).filter(
            UserPreference.company_id == company_id,
            UserPreference.project_id == project_id
        ).first()

        if pref:
            pref.is_active = False
            db.commit()
            logger.info(f"移除偏好设置: company={company_id}, project={project_id}")
            return {"success": True, "message": "偏好已移除"}
        else:
            return {"success": False, "message": "偏好不存在"}
    except Exception as e:
        logger.error(f"移除偏好失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"移除偏好失败: {str(e)}")

