'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { oauthLogin } from '@/lib/api-v2';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('正在处理登录...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const provider = localStorage.getItem('oauth_provider');

        // 验证必要参数
        if (!code) {
          throw new Error('缺少授权码');
        }

        if (!provider) {
          throw new Error('缺少OAuth提供商信息');
        }

        // 验证state（防止CSRF攻击）
        const savedState = localStorage.getItem('oauth_state');
        if (state !== savedState) {
          throw new Error('状态验证失败，可能存在安全风险');
        }

        setMessage('正在验证授权...');

        // 调用后端OAuth登录接口
        const result = await oauthLogin(provider, code, state || undefined);

        // 保存Token和用户信息
        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('refresh_token', result.refresh_token);
        localStorage.setItem('user', JSON.stringify(result.user));

        // 清除OAuth临时数据
        localStorage.removeItem('oauth_state');
        localStorage.removeItem('oauth_provider');

        setStatus('success');
        setMessage('登录成功！正在跳转...');

        // 延迟跳转，让用户看到成功提示
        setTimeout(() => {
          router.push('/');
        }, 1000);

      } catch (error: any) {
        console.error('OAuth登录失败:', error);
        setStatus('error');
        setMessage(error.response?.data?.detail || error.message || '登录失败，请重试');

        // 清除OAuth临时数据
        localStorage.removeItem('oauth_state');
        localStorage.removeItem('oauth_provider');

        // 3秒后跳转回登录页
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0B1020]">
      <div className="w-full max-w-md p-8 bg-white/[0.04] border border-[#2A2F3A] rounded-2xl shadow-2xl">
        <div className="flex flex-col items-center space-y-6">
          {/* 状态图标 */}
          {status === 'loading' && (
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 border-4 border-[#6D28D9] border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}

          {status === 'success' && (
            <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          )}

          {status === 'error' && (
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          )}

          {/* 状态文本 */}
          <div className="text-center">
            <h2 className="text-xl font-semibold text-white mb-2">
              {status === 'loading' && 'OAuth登录'}
              {status === 'success' && '登录成功'}
              {status === 'error' && '登录失败'}
            </h2>
            <p className="text-gray-400 text-sm">{message}</p>
          </div>

          {/* 错误时显示手动返回按钮 */}
          {status === 'error' && (
            <button
              onClick={() => router.push('/login')}
              className="px-6 py-2 bg-[#6D28D9] hover:bg-[#7C3AED] text-white rounded-lg transition-colors"
            >
              返回登录页
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

