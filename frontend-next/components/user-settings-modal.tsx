'use client';

/**
 * 用户设置模态框组件
 * 基于 Figma 设计图：https://www.figma.com/design/rvcno018uktGPovdhJ7tJw/AI多场景智能顾问?node-id=7-2
 *
 * 功能：
 * - 用户信息展示（头像、用户名、邮箱、验证状态）
 * - 语言切换
 * - 主题切换（深色/浅色/跟随系统）
 * - 通知开关
 * - 快捷键设置
 * - 退出登录
 * - 保存更改
 */

import * as React from 'react';
import { useState, useEffect } from 'react';
import NextImage from 'next/image';
import { logout, getCurrentUser, uploadAvatar } from '@/lib/api-v2';
import { useToast } from '@/components/ui/use-toast';
import { Toaster } from '@/components/ui/toaster';
import { LogoutConfirmDialog } from '@/components/logout-confirm-dialog';

interface UserSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  userInfo?: {
    username: string;
    email?: string;
    avatar?: string;
    isVerified?: boolean;
  };
}

export function UserSettingsModal({ isOpen, onClose, userInfo: initialUserInfo }: UserSettingsModalProps) {
  // Toast 提示
  const { toast } = useToast();

  // 状态管理
  const [userInfo, setUserInfo] = useState(initialUserInfo || {
    username: 'Alex',
    email: 'alex@example.com',
    avatar: '/images/alex-avatar-56586a.png',
    isVerified: true
  });

  const [language, setLanguage] = useState('简体中文');
  const [theme, setTheme] = useState<'dark' | 'light' | 'system'>('dark');
  const [notificationEnabled, setNotificationEnabled] = useState(true);
  const [enterToSend, setEnterToSend] = useState(true);
  const [showLanguageDropdown, setShowLanguageDropdown] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [userPlan, setUserPlan] = useState<'free' | 'pro'>('free'); // 用户计划类型
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);

  // 加载用户信息
  useEffect(() => {
    if (isOpen && !initialUserInfo) {
      loadUserInfo();
    }
  }, [isOpen, initialUserInfo]);

  const loadUserInfo = async () => {
    try {
      const user = await getCurrentUser();
      console.log('Loaded user info:', user);
      setUserInfo({
        username: user.username || 'Alex',
        email: user.email || user.phone || 'alex@example.com',
        avatar: '/images/alex-avatar-56586a.png',
        isVerified: user.is_verified !== undefined ? user.is_verified : true
      });

      // 设置用户计划（从用户数据中获取，默认为免费版）
      setUserPlan(user.plan || user.subscription || 'free');
    } catch (error) {
      console.error('Failed to load user info:', error);
      // 保持默认值
    }
  };

  // 关闭模态框
  const handleClose = () => {
    if (hasChanges) {
      if (confirm('您有未保存的更改，确定要关闭吗？')) {
        onClose();
        setHasChanges(false);
      }
    } else {
      onClose();
    }
  };

  // 显示退出登录对话框
  const handleLogoutClick = () => {
    setShowLogoutDialog(true);
  };

  // 退出登录（带清除选项）
  const handleLogout = async (clearLocalData: boolean) => {
    try {
      await logout();

      if (clearLocalData) {
        // 清除所有本地数据
        localStorage.clear();
        sessionStorage.clear();
      } else {
        // 仅清除认证相关数据
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      }

      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
      // 即使接口失败，也清除本地数据并跳转
      if (clearLocalData) {
        localStorage.clear();
        sessionStorage.clear();
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      }
      window.location.href = '/login';
    } finally {
      setShowLogoutDialog(false);
    }
  };

  // 删除账号
  const handleDeleteAccount = () => {
    toast({
      title: '删除账号功能暂未开放',
      description: '如需删除账号请联系管理员'
    });
  };

  // 头像上传处理
  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      toast({
        variant: 'destructive',
        title: '文件类型错误',
        description: '请选择图片文件（JPG、PNG、WEBP）'
      });
      return;
    }

    // 验证文件大小（5MB）
    if (file.size > 5 * 1024 * 1024) {
      toast({
        variant: 'destructive',
        title: '文件过大',
        description: '文件大小不能超过 5MB'
      });
      return;
    }

    setIsUploadingAvatar(true);

    try {
      // 创建预览
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string);
      };
      reader.readAsDataURL(file);

      // 上传文件
      const result = await uploadAvatar(file);

      // 更新用户信息
      setUserInfo({
        ...userInfo,
        avatar: result.avatar_url
      });

      setHasChanges(true);
      toast({
        title: '头像上传成功',
        description: '您的头像已更新'
      });

      // 重新加载用户信息以更新页面其他地方的头像
      await loadUserInfo();
    } catch (err) {
      console.error('Avatar upload failed:', err);
      toast({
        variant: 'destructive',
        title: '头像上传失败',
        description: '请检查网络连接后重试'
      });
      setAvatarPreview(null);
    } finally {
      setIsUploadingAvatar(false);
    }
  };

  // 保存更改
  const handleSaveChanges = async () => {
    setIsLoading(true);
    try {
      // 保存设置到 localStorage
      localStorage.setItem('user_settings', JSON.stringify({
        language,
        theme,
        notificationEnabled,
        enterToSend
      }));

      // TODO: 调用后端 API 保存用户偏好设置
      // await updateUserPreferences({ language, theme, notificationEnabled, enterToSend });

      setHasChanges(false);
      toast({
        title: '设置已保存',
        description: '您的偏好设置已更新'
      });
    } catch (err) {
      console.error('Failed to save settings:', err);
      toast({
        variant: 'destructive',
        title: '保存失败',
        description: '请稍后重试'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 标记有更改
  const markAsChanged = () => {
    setHasChanges(true);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Toast 提示容器 */}
      <Toaster />

      {/* 退出登录确认对话框 */}
      <LogoutConfirmDialog
        isOpen={showLogoutDialog}
        onClose={() => setShowLogoutDialog(false)}
        onConfirm={handleLogout}
      />

      {/* 背景遮罩 */}
      <div
        className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center"
        style={{ padding: '24px' }}
        onClick={handleClose}
      >
        {/* 模态框主容器 */}
        <div
          className="relative"
          style={{
            width: '520px',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid #2A2F3A',
            borderRadius: '24px',
            boxShadow: '0px 20px 60px rgba(0, 0, 0, 0.5)',
            padding: '1px'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* 头部 */}
          <div
            className="flex items-center justify-between"
            style={{
              padding: '16px 20px 17px',
              borderBottom: '1px solid #2A2F3A'
            }}
          >
            <div style={{ padding: '1px 0px 2px' }}>
              <h2 style={{
                fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                fontWeight: 600,
                fontSize: '18px',
                lineHeight: '24.29px',
                color: '#E6EEF8'
              }}>
                账号与设置
              </h2>
            </div>

            {/* 关闭按钮 */}
            <button
              onClick={handleClose}
              className="hover:opacity-80 transition-opacity"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M4.5 4.5L13.5 13.5M4.5 13.5L13.5 4.5" stroke="#E6EEF8" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>
          </div>

          {/* 内容区 */}
          <div style={{
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {/* 用户信息 */}
            <div className="flex items-center gap-3">
              {/* 头像（可点击上传） */}
              <div className="relative">
                <input
                  type="file"
                  id="avatar-upload"
                  accept="image/*"
                  className="hidden"
                  onChange={handleAvatarUpload}
                  disabled={isUploadingAvatar}
                />
                <label
                  htmlFor="avatar-upload"
                  className="cursor-pointer group relative block"
                  title="点击上传头像"
                >
                  <NextImage
                    src={avatarPreview || userInfo.avatar || '/images/alex-avatar-56586a.png'}
                    alt={userInfo.username}
                    width={40}
                    height={40}
                    className="rounded-full transition-opacity group-hover:opacity-70"
                  />
                  {/* 上传提示 */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/50 rounded-full">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <path d="M10 5V15M5 10H15" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  </div>

                  {/* 加载中 */}
                  {isUploadingAvatar && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/70 rounded-full">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                    </div>
                  )}
                </label>
              </div>

              <div style={{ width: '336px' }}>
                <div style={{
                  fontFamily: 'Inter, sans-serif',
                  fontWeight: 600,
                  fontSize: '14px',
                  lineHeight: '16.94px',
                  color: '#E6EEF8'
                }}>
                  {userInfo.username}
                </div>
              </div>

              {/* 验证状态徽章 */}
              {userInfo.isVerified && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6.5px 10px',
                  background: '#0D1B2A',
                  borderRadius: '48px',
                  whiteSpace: 'nowrap'
                }}>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M5.33325 8.00008L7.33325 10.0001L10.6666 6.66675" stroke="#CFE8FF" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round"/>
                    <circle cx="8" cy="8" r="6.33" stroke="#CFE8FF" strokeWidth="1.33"/>
                  </svg>
                  <span style={{
                    fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                    fontSize: '12px',
                    lineHeight: '16.20px',
                    color: '#CFE8FF'
                  }}>
                    已验证
                  </span>
                </div>
              )}
            </div>

            {/* 邮箱 */}
            <div className="flex items-center gap-3">
              <div style={{ width: '92px', padding: '0px 0px 2px' }}>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '14px',
                  lineHeight: '18.89px',
                  color: '#9CA3AF'
                }}>
                  邮箱
                </span>
              </div>

              <div style={{
                width: '374px',
                padding: '11px 13px',
                background: '#0F1724',
                border: '1px solid #2A2F3A',
                borderRadius: '12px'
              }}>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '14px',
                  lineHeight: '18.89px',
                  color: '#E6EEF8'
                }}>
                  {userInfo.email}
                </span>
              </div>
            </div>

            {/* 语言 */}
            <div className="flex items-center gap-3">
              <div style={{ width: '92px', padding: '0px 0px 2px' }}>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '14px',
                  lineHeight: '18.89px',
                  color: '#9CA3AF'
                }}>
                  语言
                </span>
              </div>

              <div
                className="relative cursor-pointer"
                style={{
                  width: '374px',
                  padding: '11px 13px',
                  background: '#0F1724',
                  border: '1px solid #2A2F3A',
                  borderRadius: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
                onClick={() => {
                  setShowLanguageDropdown(!showLanguageDropdown);
                  markAsChanged();
                }}
              >
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '14px',
                  lineHeight: '18.89px',
                  color: '#E6EEF8'
                }}>
                  {language}
                </span>

                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M4 6L8 10L12 6" stroke="#E6EEF8" strokeWidth="1.33"/>
                </svg>

                {/* 下拉菜单 */}
                {showLanguageDropdown && (
                  <div
                    className="absolute top-full left-0 mt-2 w-full"
                    style={{
                      background: '#0F1724',
                      border: '1px solid #2A2F3A',
                      borderRadius: '12px',
                      overflow: 'hidden',
                      zIndex: 10
                    }}
                  >
                    {['简体中文', 'English'].map((lang) => (
                      <div
                        key={lang}
                        className="hover:bg-[#1A2332] cursor-pointer"
                        style={{
                          padding: '11px 13px',
                          fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                          fontSize: '14px',
                          color: language === lang ? '#CFE8FF' : '#E6EEF8'
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setLanguage(lang);
                          setShowLanguageDropdown(false);
                        }}
                      >
                        {lang}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 主题 */}
            <div className="flex items-center gap-3">
              <div style={{ width: '92px', padding: '0px 0px 2px' }}>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '14px',
                  lineHeight: '18.89px',
                  color: '#9CA3AF'
                }}>
                  主题
                </span>
              </div>

              <div className="flex gap-2">
                {[
                  { value: 'dark', label: '深色', icon: '🌙' },
                  { value: 'light', label: '浅色', icon: '☀️' },
                  { value: 'system', label: '跟随系统', icon: '💻' }
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setTheme(option.value as any);
                      markAsChanged();
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 10px',
                      background: theme === option.value ? '#6D28D9' : '#0D1B2A',
                      borderRadius: '48px',
                      fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                      fontSize: '12px',
                      lineHeight: '16.20px',
                      color: '#CFE8FF',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <span>{option.icon}</span>
                    <span>{option.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 通知 */}
            <div className="flex items-center gap-3">
              <div style={{ width: '92px', padding: '0px 0px 2px' }}>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '14px',
                  lineHeight: '18.89px',
                  color: '#9CA3AF'
                }}>
                  通知
                </span>
              </div>

              <button
                onClick={() => {
                  setNotificationEnabled(!notificationEnabled);
                  markAsChanged();
                }}
                style={{
                  width: '70px',
                  height: '30px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  background: notificationEnabled ? '#10B981' : '#0D1B2A',
                  borderRadius: '48px',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  {notificationEnabled ? (
                    <path d="M5.33325 8.00008L7.33325 10.0001L10.6666 6.66675" stroke="#CFE8FF" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round"/>
                  ) : (
                    <path d="M4 4L12 12M4 12L12 4" stroke="#CFE8FF" strokeWidth="1.33" strokeLinecap="round"/>
                  )}
                </svg>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '13px',
                  lineHeight: '17.54px',
                  color: '#CFE8FF'
                }}>
                  {notificationEnabled ? '开启' : '关闭'}
                </span>
              </button>
            </div>

            {/* 快捷键 */}
            <div className="flex items-center gap-3">
              <div style={{ width: '92px', padding: '0px 0px 2px' }}>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '14px',
                  lineHeight: '18.89px',
                  color: '#9CA3AF'
                }}>
                  快捷键
                </span>
              </div>

              <div style={{
                display: 'flex',
                gap: '3.94px',
                width: '374px'
              }}>
                <button
                  onClick={() => {
                    setEnterToSend(true);
                    markAsChanged();
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6.5px 10px',
                    background: enterToSend ? '#6D28D9' : '#0D1B2A',
                    borderRadius: '48px',
                    border: 'none',
                    cursor: 'pointer',
                    fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                    fontSize: '12px',
                    lineHeight: '16.20px',
                    color: '#CFE8FF',
                    transition: 'all 0.2s'
                  }}
                >
                  <span>⏎</span>
                  <span>回车发送</span>
                </button>

                <button
                  onClick={() => {
                    setEnterToSend(false);
                    markAsChanged();
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6.5px 10px',
                    background: !enterToSend ? '#6D28D9' : '#0D1B2A',
                    borderRadius: '48px',
                    border: 'none',
                    cursor: 'pointer',
                    fontFamily: 'Inter, sans-serif',
                    fontSize: '12px',
                    lineHeight: '14.52px',
                    color: '#CFE8FF',
                    transition: 'all 0.2s'
                  }}
                >
                  <span>⇧</span>
                  <span>Shift+Enter 换行</span>
                </button>
              </div>
            </div>

            {/* 计划 */}
            <div className="flex items-center gap-3">
              <div style={{ width: '92px', padding: '0px 0px 2px' }}>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontSize: '14px',
                  lineHeight: '18.89px',
                  color: '#9CA3AF'
                }}>
                  计划
                </span>
              </div>

              <div style={{
                width: '374px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                {userPlan === 'pro' ? (
                  <>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6.5px 10px',
                      background: '#10B981',
                      borderRadius: '48px',
                      whiteSpace: 'nowrap'
                    }}>
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M8 2V8L11 11" stroke="#061618" strokeWidth="1.33" strokeLinecap="round"/>
                        <circle cx="8" cy="8" r="6.33" stroke="#061618" strokeWidth="1.33"/>
                      </svg>
                      <span style={{
                        fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                        fontSize: '12px',
                        lineHeight: '16.20px',
                        color: '#061618',
                        fontWeight: 600
                      }}>
                        专业版
                      </span>
                    </div>
                    <span style={{
                      fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                      fontSize: '12px',
                      lineHeight: '16.20px',
                      color: '#9CA3AF'
                    }}>
                      包含多场景、知识库与批量上传等功能
                    </span>
                  </>
                ) : (
                  <>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6.5px 10px',
                      background: '#6B7280',
                      borderRadius: '48px',
                      whiteSpace: 'nowrap'
                    }}>
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <circle cx="8" cy="8" r="6.33" stroke="#FFFFFF" strokeWidth="1.33"/>
                        <path d="M8 5V8" stroke="#FFFFFF" strokeWidth="1.33" strokeLinecap="round"/>
                        <circle cx="8" cy="10.5" r="0.5" fill="#FFFFFF"/>
                      </svg>
                      <span style={{
                        fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                        fontSize: '12px',
                        lineHeight: '16.20px',
                        color: '#FFFFFF',
                        fontWeight: 600
                      }}>
                        免费版
                      </span>
                    </div>
                    <span style={{
                      fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                      fontSize: '12px',
                      lineHeight: '16.20px',
                      color: '#9CA3AF'
                    }}>
                      基础功能，单场景使用
                    </span>
                    <button
                      onClick={() => toast({
                        title: '升级功能即将开放',
                        description: '敬请期待！'
                      })}
                      style={{
                        padding: '4px 10px',
                        background: '#6D28D9',
                        borderRadius: '48px',
                        border: 'none',
                        cursor: 'pointer',
                        fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                        fontSize: '11px',
                        color: '#FFFFFF',
                        fontWeight: 500,
                        whiteSpace: 'nowrap'
                      }}
                      className="hover:bg-[#7C3AED] transition-colors"
                    >
                      升级
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* 底部操作区 */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '15px 20px 14px',
            borderTop: '1px solid #2A2F3A',
            gap: '8px'
          }}>
            {/* 退出登录 */}
            <button
              onClick={handleLogoutClick}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 12px',
                background: '#0D1B2A',
                border: '1px solid #2A2F3A',
                borderRadius: '48px',
                cursor: 'pointer',
                fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                fontWeight: 500,
                fontSize: '13px',
                lineHeight: '1',
                color: '#CFE8FF',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap'
              }}
              className="hover:bg-[#111827]"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M10 2H13C13.55 2 14 2.45 14 3V13C14 13.55 13.55 14 13 14H10M7 11L10 8M10 8L7 5M10 8H2" stroke="#CFE8FF" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>退出登录</span>
            </button>

            <div className="flex items-center gap-2">
              {/* 删除账号 */}
              <button
                onClick={handleDeleteAccount}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 12px',
                  background: '#0D1B2A',
                  border: '1px solid #2A2F3A',
                  borderRadius: '48px',
                  cursor: 'pointer',
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontWeight: 500,
                  fontSize: '13px',
                  lineHeight: '1',
                  color: '#CFE8FF',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap'
                }}
                className="hover:bg-[#111827]"
              >
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <path d="M3 4H13M5 4V3C5 2.45 5.45 2 6 2H10C10.55 2 11 2.45 11 3V4M5 7V11M8 7V11M11 7V11M4 4H12V13C12 13.55 11.55 14 11 14H5C4.45 14 4 13.55 4 13V4Z" stroke="#CFE8FF" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span>删除账号</span>
              </button>

              {/* 保存更改 */}
              <button
                onClick={handleSaveChanges}
                disabled={!hasChanges || isLoading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 12px',
                  background: hasChanges ? '#6D28D9' : '#4B2F7E',
                  borderRadius: '48px',
                  border: 'none',
                  cursor: hasChanges ? 'pointer' : 'not-allowed',
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontWeight: 500,
                  fontSize: '13px',
                  lineHeight: '1',
                  color: '#FFFFFF',
                  opacity: hasChanges ? 1 : 0.5,
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap'
                }}
                className={hasChanges ? 'hover:bg-[#7C3AED]' : ''}
              >
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <path d="M5.33325 8.00008L7.33325 10.0001L10.6666 6.66675" stroke="#FFFFFF" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span>{isLoading ? '保存中...' : '保存更改'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

