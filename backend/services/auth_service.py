"""
认证服务 - 处理用户注册、登录、Token管理
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import bcrypt
from sqlalchemy.orm import Session

from backend.models.user import User, Tenant, Role, RefreshToken, OAuthAccount
from backend.database import get_db_session


def generate_id(length: int = 32) -> str:
    """生成唯一ID"""
    return str(uuid.uuid4()).replace('-', '')[:length]


class AuthService:
    """认证服务"""

    # 从环境变量读取，如果没有则使用默认值（生产环境必须修改）
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_db_session()

    def register(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        tenant_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        用户注册（自动创建租户）

        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            phone: 手机号（可选）
            tenant_name: 租户名称（可选）

        Returns:
            包含user_id, tenant_id, username的字典

        Raises:
            ValueError: 用户名已存在
        """
        # 检查用户名是否存在
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError("用户名已存在")

        # 检查邮箱是否已被使用
        if email:
            existing_email = self.db.query(User).filter(User.email == email).first()
            if existing_email:
                raise ValueError("邮箱已被使用")

        # 检查手机号是否已被使用
        if phone:
            existing_phone = self.db.query(User).filter(User.phone == phone).first()
            if existing_phone:
                raise ValueError("手机号已被使用")

        # 创建租户
        tenant_id = generate_id()
        tenant = Tenant(
            id=tenant_id,
            name=tenant_name or f"{username}的团队",
            code=f"T{tenant_id[:8]}",
            config={"data_sharing": {"company": "private", "project": "private"}}
        )
        self.db.add(tenant)

        # 获取或创建管理员角色
        admin_role = self.db.query(Role).filter(
            Role.name == "admin",
            Role.is_system == True
        ).first()

        if not admin_role:
            admin_role = Role(
                id=generate_id(),
                name="admin",
                display_name="管理员",
                description="租户管理员，拥有所有权限",
                permissions={
                    "chat": ["create", "read", "update", "delete"],
                    "document": ["upload", "read", "delete"],
                    "knowledge": ["create", "read", "update", "delete"],
                    "report": ["generate", "read", "export"],
                    "user": ["create", "read", "update", "delete"],
                    "tenant": ["read", "update"]
                },
                is_system=True
            )
            self.db.add(admin_role)
            self.db.flush()  # 确保角色ID可用

        # 创建用户
        user_id = generate_id()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user = User(
            id=user_id,
            tenant_id=tenant_id,
            username=username,
            email=email,
            phone=phone,
            password_hash=password_hash,
            nickname=username,
            role_id=admin_role.id,
            status="active",
            is_verified=True
        )
        self.db.add(user)
        self.db.commit()

        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "username": username
        }

    def login(self, username: str, password: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码
            ip_address: 登录IP地址（可选）

        Returns:
            包含access_token, refresh_token, user信息的字典

        Raises:
            ValueError: 用户名或密码错误，或账号被禁用
        """
        user = self.db.query(User).filter(User.username == username).first()

        if not user or not user.password_hash:
            raise ValueError("用户名或密码错误")

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise ValueError("用户名或密码错误")

        if user.status != "active":
            raise ValueError("账号已被禁用")

        # 生成Token
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(user)

        # 更新登录信息
        user.last_login_at = datetime.now()
        if ip_address:
            user.last_login_ip = ip_address
        self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": self._user_to_dict(user)
        }

    def oauth_login(
        self,
        provider: str,
        code: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        OAuth登录（微信/钉钉/手机号）

        Args:
            provider: OAuth提供者 (wechat/dingtalk/phone)
            code: 授权码
            state: 状态参数（可选）

        Returns:
            包含access_token, refresh_token, user信息的字典
        """
        # TODO: 实现OAuth登录逻辑
        # 1. 使用code换取access_token
        # 2. 获取用户信息
        # 3. 查找或创建用户
        # 4. 创建OAuth绑定
        # 5. 生成系统Token
        raise NotImplementedError("OAuth登录功能待实现")

    def refresh_access_token(self, refresh_token_str: str) -> Dict[str, Any]:
        """
        刷新访问令牌

        Args:
            refresh_token_str: 刷新令牌

        Returns:
            包含新的access_token的字典

        Raises:
            ValueError: 刷新令牌无效或已过期
        """
        refresh_token = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token_str,
            RefreshToken.is_revoked == False
        ).first()

        if not refresh_token:
            raise ValueError("刷新令牌无效")

        if refresh_token.expires_at < datetime.now():
            raise ValueError("刷新令牌已过期")

        # 获取用户
        user = self.db.query(User).filter(User.id == refresh_token.user_id).first()
        if not user or user.status != "active":
            raise ValueError("用户不存在或已被禁用")

        # 生成新的访问令牌
        access_token = self._create_access_token(user)

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证访问令牌

        Args:
            token: JWT访问令牌

        Returns:
            Token payload（包含user_id, username, tenant_id, role等）

        Raises:
            ValueError: Token无效或已过期
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token已过期")
        except jwt.JWTError as e:
            raise ValueError(f"Token无效: {str(e)}")

    def _create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user.id,
            "username": user.username,
            "tenant_id": user.tenant_id,
            "role": user.role.name,
            "exp": expire
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def _create_refresh_token(self, user: User) -> str:
        """创建刷新令牌"""
        token_id = generate_id()
        token_str = generate_id(length=64)
        expire = datetime.now() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token = RefreshToken(
            id=token_id,
            user_id=user.id,
            token=token_str,
            expires_at=expire
        )
        self.db.add(refresh_token)
        self.db.commit()

        return token_str

    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """将User对象转换为字典"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "tenant_id": user.tenant_id,
            "tenant_name": user.tenant.name if user.tenant else None,
            "role": user.role.name if user.role else None,
            "role_display_name": user.role.display_name if user.role else None,
            "status": user.status,
            "is_verified": user.is_verified,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据用户ID获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            User对象或None
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def update_user_avatar(self, user_id: str, avatar_url: str) -> bool:
        """
        更新用户头像

        Args:
            user_id: 用户ID
            avatar_url: 新的头像URL

        Returns:
            是否更新成功

        Raises:
            ValueError: 用户不存在
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        user.avatar_url = avatar_url
        user.updated_at = datetime.now()
        self.db.commit()
        return True

    def close(self):
        """关闭数据库会话"""
        if self.db:
            self.db.close()


# 单例模式
_auth_service_instance = None


def get_auth_service() -> AuthService:
    """获取AuthService实例"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance

