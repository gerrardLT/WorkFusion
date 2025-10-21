"""
认证API路由 - 处理用户注册、登录、OAuth等
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, status, UploadFile, File
from pydantic import BaseModel, Field
import os
from pathlib import Path
import uuid

from backend.services.auth_service import get_auth_service, AuthService
from backend.middleware.auth_middleware import get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


# ==================== 请求/响应模型 ====================

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    tenant_name: Optional[str] = Field(None, description="租户名称")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class OAuthLoginRequest(BaseModel):
    """OAuth登录请求"""
    provider: str = Field(..., description="OAuth提供者 (wechat/dingtalk/phone)")
    code: str = Field(..., description="授权码")
    state: Optional[str] = Field(None, description="状态参数")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class AuthResponse(BaseModel):
    """认证响应"""
    success: bool
    data: dict
    message: Optional[str] = None


# ==================== API路由 ====================

@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户注册

    自动创建租户，注册用户为租户管理员
    """
    try:
        result = auth_service.register(
            username=request.username,
            password=request.password,
            email=request.email,
            phone=request.phone,
            tenant_name=request.tenant_name
        )
        return AuthResponse(
            success=True,
            data=result,
            message="注册成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request_data: LoginRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录

    返回access_token和refresh_token
    """
    try:
        # 获取客户端IP
        ip_address = http_request.client.host if http_request.client else None

        result = auth_service.login(
            username=request_data.username,
            password=request_data.password,
            ip_address=ip_address
        )
        return AuthResponse(
            success=True,
            data=result,
            message="登录成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/oauth/login", response_model=AuthResponse)
async def oauth_login(
    request: OAuthLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    OAuth登录

    支持微信、钉钉、手机号验证码登录
    """
    try:
        result = auth_service.oauth_login(
            provider=request.provider,
            code=request.code,
            state=request.state
        )
        return AuthResponse(
            success=True,
            data=result,
            message="登录成功"
        )
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth登录失败: {str(e)}"
        )


@router.get("/me", response_model=AuthResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户信息

    需要提供有效的access_token
    """
    return AuthResponse(
        success=True,
        data=current_user,
        message="获取用户信息成功"
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    刷新访问令牌

    使用refresh_token获取新的access_token
    """
    try:
        result = auth_service.refresh_access_token(request.refresh_token)
        return AuthResponse(
            success=True,
            data=result,
            message="Token刷新成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token刷新失败: {str(e)}"
        )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    用户登出

    TODO: 实现Token撤销逻辑（将refresh_token标记为已撤销）
    """
    return AuthResponse(
        success=True,
        data={"user_id": current_user["sub"]},
        message="登出成功"
    )


@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    上传用户头像

    Args:
        file: 上传的图片文件
        current_user: 当前用户
        auth_service: 认证服务

    Returns:
        上传成功的头像URL
    """

    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持 JPG, PNG, WEBP 格式的图片"
        )

    # 验证文件大小（最大 5MB）
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过 5MB"
        )

    # 创建上传目录
    upload_dir = Path("backend/data/uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / filename

    # 保存文件
    with open(file_path, "wb") as f:
        f.write(content)

    # 更新用户头像URL
    avatar_url = f"/uploads/avatars/{filename}"
    try:
        auth_service.update_user_avatar(current_user["sub"], avatar_url)
    except Exception as e:
        # 如果更新失败，删除已上传的文件
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新头像失败: {str(e)}"
        )

    return AuthResponse(
        success=True,
        data={"avatar_url": avatar_url},
        message="头像上传成功"
    )


# ==================== OAuth辅助接口 ====================

@router.get("/oauth/url/{provider}")
async def get_oauth_url(
    provider: str,
    redirect_uri: str,
    state: Optional[str] = None
):
    """
    获取OAuth授权URL

    Args:
        provider: OAuth提供者 (wechat/dingtalk)
        redirect_uri: 回调地址
        state: 状态参数（用于防止CSRF攻击）

    Returns:
        OAuth授权URL
    """
    # TODO: 实现OAuth URL生成逻辑
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth URL生成功能待实现"
    )

