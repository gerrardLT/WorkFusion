'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser, logout } from '@/lib/api-v2';

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      setLoading(true);
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error: any) {
      console.error('加载用户信息失败:', error);
      setError('无法加载用户信息');

      // 如果是未认证错误，跳转到登录页
      if (error.response?.status === 401 || error.response?.status === 403) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      localStorage.clear();
      router.push('/login');
    } catch (error) {
      console.error('登出失败:', error);
      // 即使登出失败也清除本地数据
      localStorage.clear();
      router.push('/login');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B1020] flex items-center justify-center">
        <div className="text-white">加载中...</div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="min-h-screen bg-[#0B1020] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || '用户信息不可用'}</p>
          <button
            onClick={() => router.push('/login')}
            className="px-6 py-2 bg-[#6D28D9] hover:bg-[#7C3AED] text-white rounded-lg transition-colors"
          >
            返回登录
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B1020] p-8">
      <div className="max-w-4xl mx-auto">
        {/* 页面标题和返回按钮 */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-white">个人中心</h1>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-white/[0.04] hover:bg-white/[0.08] border border-[#2A2F3A] text-gray-300 rounded-lg transition-colors"
          >
            返回首页
          </button>
        </div>

        <div className="space-y-6">
          {/* 基本信息 */}
          <div className="p-6 bg-white/[0.04] border border-[#2A2F3A] rounded-2xl shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">基本信息</h2>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 text-red-400 rounded-lg transition-colors text-sm"
              >
                退出登录
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center py-3 border-b border-[#2A2F3A]">
                <span className="text-gray-400 w-32">用户名</span>
                <span className="text-white font-medium">{user.username}</span>
              </div>

              <div className="flex items-center py-3 border-b border-[#2A2F3A]">
                <span className="text-gray-400 w-32">用户ID</span>
                <span className="text-gray-300 text-sm font-mono">{user.sub || user.user_id}</span>
              </div>

              <div className="flex items-center py-3 border-b border-[#2A2F3A]">
                <span className="text-gray-400 w-32">角色</span>
                <span className="text-white">
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    user.role === 'admin'
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/50'
                      : 'bg-blue-500/20 text-blue-300 border border-blue-500/50'
                  }`}>
                    {user.role === 'admin' ? '管理员' : '普通用户'}
                  </span>
                </span>
              </div>

              <div className="flex items-center py-3 border-b border-[#2A2F3A]">
                <span className="text-gray-400 w-32">租户ID</span>
                <span className="text-gray-300 text-sm font-mono">{user.tenant_id}</span>
              </div>

              {user.email && (
                <div className="flex items-center py-3 border-b border-[#2A2F3A]">
                  <span className="text-gray-400 w-32">邮箱</span>
                  <span className="text-gray-300">{user.email}</span>
                </div>
              )}

              {user.phone && (
                <div className="flex items-center py-3 border-b border-[#2A2F3A]">
                  <span className="text-gray-400 w-32">手机号</span>
                  <span className="text-gray-300">{user.phone}</span>
                </div>
              )}

              {user.exp && (
                <div className="flex items-center py-3">
                  <span className="text-gray-400 w-32">Token过期时间</span>
                  <span className="text-gray-300 text-sm">
                    {new Date(user.exp * 1000).toLocaleString('zh-CN')}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* 第三方账号绑定（待实现） */}
          <div className="p-6 bg-white/[0.04] border border-[#2A2F3A] rounded-2xl shadow-xl">
            <h2 className="text-xl font-semibold text-white mb-4">第三方账号绑定</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-white/[0.02] border border-[#2A2F3A] rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-[#07C160] rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8.5 11.5c0 .6-.4 1-1 1s-1-.4-1-1 .4-1 1-1 1 .4 1 1zm7 0c0 .6-.4 1-1 1s-1-.4-1-1 .4-1 1-1 1 .4 1 1z"/>
                        <path d="M22 12.4c0-3.8-3.8-6.9-8.5-6.9S5 8.6 5 12.4c0 3.4 3 6.2 7 6.8.3.1.7.2.9.5.2.2.1.6.1.8 0 0 0 .1-.1 1.2 0 .4.2.7.7.5 2.4-1.3 4.3-2.4 5.7-4.2 1.1-1.2 1.7-2.5 1.7-4.1z"/>
                      </svg>
                    </div>
                    <div>
                      <p className="text-white font-medium">微信</p>
                      <p className="text-gray-400 text-sm">未绑定</p>
                    </div>
                  </div>
                  <button className="px-3 py-1 text-sm text-gray-400 border border-[#2A2F3A] rounded hover:border-[#6D28D9] hover:text-[#6D28D9] transition-colors">
                    绑定
                  </button>
                </div>
              </div>

              <div className="p-4 bg-white/[0.02] border border-[#2A2F3A] rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-[#0089FF] rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                        <path d="M12 6c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z"/>
                      </svg>
                    </div>
                    <div>
                      <p className="text-white font-medium">钉钉</p>
                      <p className="text-gray-400 text-sm">未绑定</p>
                    </div>
                  </div>
                  <button className="px-3 py-1 text-sm text-gray-400 border border-[#2A2F3A] rounded hover:border-[#6D28D9] hover:text-[#6D28D9] transition-colors">
                    绑定
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 安全设置（待实现） */}
          <div className="p-6 bg-white/[0.04] border border-[#2A2F3A] rounded-2xl shadow-xl">
            <h2 className="text-xl font-semibold text-white mb-4">安全设置</h2>
            <div className="space-y-3">
              <button className="w-full p-4 bg-white/[0.02] border border-[#2A2F3A] rounded-lg hover:border-[#6D28D9] transition-colors text-left group">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium group-hover:text-[#6D28D9] transition-colors">修改密码</p>
                    <p className="text-gray-400 text-sm mt-1">定期更换密码以保护账号安全</p>
                  </div>
                  <svg className="w-5 h-5 text-gray-400 group-hover:text-[#6D28D9] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>

              <button className="w-full p-4 bg-white/[0.02] border border-[#2A2F3A] rounded-lg hover:border-[#6D28D9] transition-colors text-left group">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium group-hover:text-[#6D28D9] transition-colors">双因素认证</p>
                    <p className="text-gray-400 text-sm mt-1">启用双因素认证增强账号安全</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded">未启用</span>
                    <svg className="w-5 h-5 text-gray-400 group-hover:text-[#6D28D9] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

