'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login, register } from '@/lib/api-v2';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    tenant_name: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let result;

      if (mode === 'login') {
        result = await login(formData.username, formData.password);
      } else {
        result = await register({
          username: formData.username,
          password: formData.password,
          email: formData.email || undefined,
          phone: formData.phone || undefined,
          tenant_name: formData.tenant_name || undefined
        });

        // 注册成功后自动登录
        result = await login(formData.username, formData.password);
      }

      // 保存Token和用户信息
      localStorage.setItem('access_token', result.access_token);
      localStorage.setItem('refresh_token', result.refresh_token);
      localStorage.setItem('user', JSON.stringify(result.user));

      // 跳转到首页
      router.push('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '操作失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthLogin = async (provider: 'wechat' | 'dingtalk') => {
    try {
      // 获取OAuth授权URL
      const redirectUri = `${window.location.origin}/oauth/callback`;
      const state = Math.random().toString(36).substring(7);

      localStorage.setItem('oauth_state', state);
      localStorage.setItem('oauth_provider', provider);

      // 跳转到后端获取授权URL的接口
      const authUrl = `/api/v2/auth/oauth/url/${provider}?redirect_uri=${encodeURIComponent(redirectUri)}&state=${state}`;
      window.location.href = authUrl;
    } catch (err: any) {
      setError('OAuth登录失败，请重试');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0B1020]">
      <div className="w-full max-w-md p-8 bg-white/[0.04] border border-[#2A2F3A] rounded-2xl shadow-2xl">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            {mode === 'login' ? '登录' : '注册'}
          </h1>
          <p className="text-gray-400 text-sm">
            {mode === 'login' ? '欢迎回来！' : '创建新账户'}
          </p>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              用户名
            </label>
            <input
              type="text"
              placeholder="请输入用户名"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              className="w-full px-4 py-3 bg-[#0F1724] border border-[#2A2F3A] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6D28D9] transition-colors"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              密码
            </label>
            <input
              type="password"
              placeholder="请输入密码"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-4 py-3 bg-[#0F1724] border border-[#2A2F3A] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6D28D9] transition-colors"
              required
              disabled={loading}
              minLength={6}
            />
            {mode === 'register' && (
              <p className="mt-1 text-xs text-gray-500">密码至少6个字符</p>
            )}
          </div>

          {mode === 'register' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  邮箱（可选）
                </label>
                <input
                  type="email"
                  placeholder="请输入邮箱"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-4 py-3 bg-[#0F1724] border border-[#2A2F3A] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6D28D9] transition-colors"
                  disabled={loading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  手机号（可选）
                </label>
                <input
                  type="tel"
                  placeholder="请输入手机号"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="w-full px-4 py-3 bg-[#0F1724] border border-[#2A2F3A] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6D28D9] transition-colors"
                  disabled={loading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  团队名称（可选）
                </label>
                <input
                  type="text"
                  placeholder="请输入团队名称"
                  value={formData.tenant_name}
                  onChange={(e) => setFormData({...formData, tenant_name: e.target.value})}
                  className="w-full px-4 py-3 bg-[#0F1724] border border-[#2A2F3A] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6D28D9] transition-colors"
                  disabled={loading}
                />
                <p className="mt-1 text-xs text-gray-500">
                  未填写将自动创建默认团队
                </p>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[#6D28D9] hover:bg-[#7C3AED] disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
          >
            {loading ? '处理中...' : (mode === 'login' ? '登录' : '注册')}
          </button>
        </form>

        {/* 第三方登录 */}
        <div className="mt-6 space-y-3">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#2A2F3A]"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white/[0.04] text-gray-400">或使用第三方登录</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => handleOAuthLogin('wechat')}
              disabled={loading}
              className="flex items-center justify-center gap-2 py-2 px-4 bg-[#07C160] hover:bg-[#06AD56] disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8.5 11.5c0 .6-.4 1-1 1s-1-.4-1-1 .4-1 1-1 1 .4 1 1zm7 0c0 .6-.4 1-1 1s-1-.4-1-1 .4-1 1-1 1 .4 1 1z"/>
                <path d="M22 12.4c0-3.8-3.8-6.9-8.5-6.9S5 8.6 5 12.4c0 3.4 3 6.2 7 6.8.3.1.7.2.9.5.2.2.1.6.1.8 0 0 0 .1-.1 1.2 0 .4.2.7.7.5 2.4-1.3 4.3-2.4 5.7-4.2 1.1-1.2 1.7-2.5 1.7-4.1z"/>
              </svg>
              微信登录
            </button>

            <button
              onClick={() => handleOAuthLogin('dingtalk')}
              disabled={loading}
              className="flex items-center justify-center gap-2 py-2 px-4 bg-[#0089FF] hover:bg-[#0078E8] disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                <path d="M12 6c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z"/>
              </svg>
              钉钉登录
            </button>
          </div>
        </div>

        {/* 切换登录/注册 */}
        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login');
              setError('');
            }}
            disabled={loading}
            className="text-[#6D28D9] hover:text-[#7C3AED] disabled:text-gray-600 disabled:cursor-not-allowed text-sm transition-colors"
          >
            {mode === 'login' ? '没有账号？立即注册' : '已有账号？立即登录'}
          </button>
        </div>
      </div>
    </div>
  );
}

