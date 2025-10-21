# JWT Token 验证失败处理最佳实践

## 🎯 核心原则

**JWT Token 验证失败时的处理应该根据具体场景采取不同策略，而不是简单粗暴地跳转登录页。**

---

## 📊 Token 失败的常见场景

| 场景 | 原因 | 推荐处理方式 |
|------|------|------------|
| **Token 过期** | Access Token 超过有效期 | ✅ 自动刷新 Token |
| **Token 无效** | 签名错误、格式错误 | ⚠️ 清除 Token + 跳转登录 |
| **Refresh Token 过期** | 两个 Token 都过期 | ⚠️ 跳转登录 |
| **用户被禁用** | 账号状态异常 | ⚠️ 显示提示 + 跳转登录 |
| **权限不足** | 403 错误 | ℹ️ 显示权限不足页面 |

---

## ✅ 推荐的完整处理流程

### 流程图

```
API 请求
  ↓
401 Unauthorized
  ↓
是否有 Refresh Token？
  ├─ 是 → 尝试刷新 Access Token
  │       ├─ 成功 → 重试原请求
  │       └─ 失败 → 清除所有 Token → 跳转登录
  └─ 否 → 清除所有 Token → 跳转登录
```

---

## 💻 前端实现方案

### 1. API 拦截器（推荐方案）

在 `frontend-next/lib/api-client.ts` 中实现：

```typescript
import axios, { AxiosError } from 'axios';
import { useRouter } from 'next/navigation';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// 请求拦截器：自动添加 Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器：处理 Token 失败
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // 场景1: Token 过期（401错误）
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 如果已经在刷新，将请求加入队列
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');

      // 场景1.1: 有 Refresh Token，尝试刷新
      if (refreshToken) {
        try {
          const response = await axios.post(
            `${apiClient.defaults.baseURL}/api/v2/auth/refresh`,
            { refresh_token: refreshToken }
          );

          const { access_token, refresh_token: newRefreshToken } = response.data;

          // 保存新 Token
          localStorage.setItem('access_token', access_token);
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }

          // 更新请求头
          apiClient.defaults.headers.common.Authorization = `Bearer ${access_token}`;
          originalRequest.headers.Authorization = `Bearer ${access_token}`;

          // 处理队列中的请求
          processQueue(null, access_token);
          isRefreshing = false;

          // 重试原请求
          return apiClient(originalRequest);
        } catch (refreshError) {
          // 场景1.2: 刷新失败，清除 Token 并跳转登录
          processQueue(refreshError, null);
          isRefreshing = false;
          handleLogout();
          return Promise.reject(refreshError);
        }
      } else {
        // 场景1.3: 没有 Refresh Token，直接跳转登录
        isRefreshing = false;
        handleLogout();
        return Promise.reject(error);
      }
    }

    // 场景2: 权限不足（403错误）
    if (error.response?.status === 403) {
      // 不跳转登录，而是显示权限不足提示
      console.error('权限不足');
      // 可以触发一个全局的权限不足提示
      return Promise.reject(error);
    }

    // 场景3: 其他错误
    return Promise.reject(error);
  }
);

// 统一的登出处理
function handleLogout() {
  // 清除所有认证信息
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');

  // 跳转到登录页，并保存当前路径（登录后可以返回）
  const currentPath = window.location.pathname;
  if (currentPath !== '/login') {
    window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
  }
}

export default apiClient;
```

---

## 🔧 后端实现方案

### 1. 统一的错误响应格式

在 `backend/middleware/auth_middleware.py` 中：

```python
from fastapi import HTTPException, status

def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    try:
        # Token 验证逻辑
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Token payload invalid",
                    "action": "logout"  # 提示前端应该登出
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查用户是否存在
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "user_not_found",
                    "message": "User no longer exists",
                    "action": "logout"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查用户状态
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "user_disabled",
                    "message": "Your account has been disabled",
                    "action": "contact_support"  # 不是登出，而是联系支持
                }
            )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "token_expired",
                "message": "Token has expired",
                "action": "refresh"  # 提示前端应该刷新 Token
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_signature",
                "message": "Token signature verification failed",
                "action": "logout"  # 签名错误，需要重新登录
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "authentication_failed",
                "message": str(e),
                "action": "logout"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 2. Refresh Token 端点

在 `backend/api/auth.py` 中：

```python
@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """刷新 Access Token"""
    try:
        auth_service = AuthService()
        result = auth_service.refresh_access_token(request.refresh_token)

        return {
            "success": True,
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),  # 可选：轮换 Refresh Token
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_refresh_token",
                "message": str(e),
                "action": "logout"  # Refresh Token 无效，需要重新登录
            }
        )
```

---

## 🎨 用户体验优化

### 1. 优雅的提示信息

```typescript
// 在前端显示友好的提示
const handleAuthError = (error: any) => {
  const detail = error.response?.data?.detail;

  if (typeof detail === 'object') {
    switch (detail.action) {
      case 'refresh':
        // Token 过期，正在自动刷新...
        console.log('Token expired, refreshing...');
        break;

      case 'logout':
        // 显示提示：您的登录已过期，请重新登录
        toast.warning('登录已过期，请重新登录');
        break;

      case 'contact_support':
        // 显示提示：您的账号已被禁用，请联系管理员
        toast.error('账号已被禁用，请联系管理员');
        break;
    }
  }
};
```

### 2. 保存重定向路径

```typescript
// 登录成功后返回原页面
function handleLogout() {
  const currentPath = window.location.pathname;

  // 清除 Token
  localStorage.clear();

  // 跳转登录，保存重定向路径
  if (currentPath !== '/login') {
    window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
  } else {
    window.location.href = '/login';
  }
}

// 登录页面
function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectPath = searchParams.get('redirect') || '/';

  const handleLoginSuccess = () => {
    // 登录成功后跳转到原页面
    router.push(redirectPath);
  };
}
```

### 3. Loading 状态

```typescript
const [isRefreshing, setIsRefreshing] = useState(false);

// 显示刷新中的状态
if (isRefreshing) {
  return <div>正在刷新登录状态...</div>;
}
```

---

## 🔒 安全性考虑

### 1. Token 有效期设置

```env
# 短有效期的 Access Token（推荐 15-120 分钟）
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 较长有效期的 Refresh Token（推荐 7-30 天）
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2. Refresh Token 轮换

每次刷新时生成新的 Refresh Token，并使旧的失效：

```python
def refresh_access_token(self, refresh_token: str):
    # 验证旧 Refresh Token
    # ...

    # 生成新的 Access Token 和 Refresh Token
    new_access_token = self.create_access_token(user_id)
    new_refresh_token = self.create_refresh_token(user_id)

    # 使旧的 Refresh Token 失效
    self.revoke_refresh_token(refresh_token)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }
```

### 3. 黑名单机制

对于登出的 Token，应该加入黑名单：

```python
# 用户登出时
def logout(self, access_token: str, refresh_token: str):
    # 将 Token 加入黑名单（Redis）
    self.add_to_blacklist(access_token)
    self.revoke_refresh_token(refresh_token)
```

---

## 📋 完整的处理策略总结

| 错误类型 | HTTP状态码 | 前端行为 | 用户体验 |
|---------|-----------|---------|---------|
| **Token 过期** | 401 | 自动刷新 → 重试请求 | 无感知（后台自动处理） |
| **Refresh Token 过期** | 401 | 跳转登录 + 保存重定向 | "登录已过期，请重新登录" |
| **Token 签名错误** | 401 | 清除 Token + 跳转登录 | "登录状态异常，请重新登录" |
| **用户被禁用** | 403 | 显示提示 | "账号已被禁用，请联系管理员" |
| **权限不足** | 403 | 显示权限不足页面 | "您没有权限访问此资源" |

---

## ✅ 推荐的实现步骤

### 阶段1：基础实现（当前）
- [x] 简单的 Token 验证
- [x] 401 错误时跳转登录
- [ ] 实现 Refresh Token 刷新

### 阶段2：优化体验
- [ ] 自动刷新 Token
- [ ] 保存重定向路径
- [ ] 友好的错误提示

### 阶段3：高级功能
- [ ] Token 轮换机制
- [ ] Token 黑名单
- [ ] 多设备登录管理

---

## 🎯 对于您当前项目的建议

**当前阶段（MVP）**：
- ✅ Token 验证失败时，跳转登录页（简单可靠）
- ✅ 清除所有 Token 和用户信息
- ⚠️ 暂时不实现自动刷新（可以后续添加）

**下一阶段（优化）**：
- 实现 Refresh Token 自动刷新
- 添加友好的错误提示
- 保存重定向路径

**生产环境（必须）**：
- 实现完整的 Token 刷新机制
- 添加 Token 黑名单
- 实现安全的登出

---

## 📝 快速实现代码

### 最简单的实现（当前推荐）

```typescript
// frontend-next/lib/api-client.ts

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401 错误：清除 Token 并跳转登录
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');

      // 跳转登录
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);
```

**优点**：
- ✅ 简单可靠
- ✅ 不会出现死循环
- ✅ 安全性好

**缺点**：
- ⚠️ 用户体验稍差（需要重新登录）
- ⚠️ 没有自动刷新

---

**总结**：对于当前的 MVP 阶段，**简单地跳转登录页是正确且安全的做法**。后续可以逐步优化为自动刷新 Token 的方案。

