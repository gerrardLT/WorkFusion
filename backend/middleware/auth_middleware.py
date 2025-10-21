"""
认证中间件 - 提供FastAPI依赖注入的认证和权限检查
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.services.auth_service import get_auth_service, AuthService


# HTTP Bearer认证方案
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    获取当前登录用户（包含完整用户信息）

    从HTTP Authorization头中提取Bearer Token并验证，
    然后从数据库获取完整的用户信息

    Args:
        credentials: HTTP认证凭证
        auth_service: 认证服务实例

    Returns:
        完整用户信息（包含email, phone, avatar等）

    Raises:
        HTTPException: 401 - Token无效或已过期
    """
    token = credentials.credentials

    try:
        payload = auth_service.verify_token(token)
        user_id = payload["sub"]

        # 从数据库获取完整用户信息
        user = auth_service.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 返回完整用户信息
        return {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "tenant_id": user.tenant_id,
            "role": user.role.name,
            "status": user.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_tenant(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    获取当前租户ID

    Args:
        current_user: 当前用户信息

    Returns:
        租户ID
    """
    return current_user["tenant_id"]


async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    获取当前用户ID

    Args:
        current_user: 当前用户信息

    Returns:
        用户ID
    """
    return current_user["sub"]


async def require_permission(
    resource: str,
    action: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> bool:
    """
    检查当前用户是否有指定资源的操作权限

    Args:
        resource: 资源名称（如 'chat', 'document', 'knowledge'）
        action: 操作名称（如 'create', 'read', 'update', 'delete'）
        current_user: 当前用户信息

    Returns:
        True - 有权限

    Raises:
        HTTPException: 403 - 无权限
    """
    # TODO: 从数据库获取用户角色的详细权限
    # 目前简化处理：管理员有所有权限，普通用户有基础权限

    role = current_user.get("role", "user")

    # 管理员拥有所有权限
    if role == "admin":
        return True

    # 普通用户的基础权限
    user_permissions = {
        "chat": ["create", "read", "update", "delete"],
        "document": ["upload", "read"],
        "knowledge": ["read"],
        "report": ["read"]
    }

    # 检查权限
    if resource in user_permissions:
        if action in user_permissions[resource]:
            return True

    # 无权限
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"无权限执行操作: {resource}.{action}"
    )


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    要求管理员权限

    Args:
        current_user: 当前用户信息

    Returns:
        当前用户信息

    Raises:
        HTTPException: 403 - 非管理员
    """
    role = current_user.get("role", "user")

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user


# 可选的认证（允许未登录用户访问，但如果提供了Token则验证）
class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request) -> Optional[HTTPAuthorizationCredentials]:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None


optional_security = OptionalHTTPBearer()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[Dict[str, Any]]:
    """
    获取当前登录用户（可选）

    如果提供了Token则验证，否则返回None

    Args:
        credentials: HTTP认证凭证（可选）
        auth_service: 认证服务实例

    Returns:
        Token payload或None
    """
    if not credentials:
        return None

    token = credentials.credentials

    try:
        payload = auth_service.verify_token(token)
        return payload
    except ValueError:
        return None

