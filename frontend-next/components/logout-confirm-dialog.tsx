'use client';

/**
 * 退出登录确认对话框组件
 * 基于 Figma 设计图实现
 */

import * as React from 'react';
import { useState } from 'react';

interface LogoutConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (clearLocalData: boolean) => void;
}

export function LogoutConfirmDialog({ isOpen, onClose, onConfirm }: LogoutConfirmDialogProps) {
  const [clearLocalData, setClearLocalData] = useState(false);

  if (!isOpen) return null;

  const handleLogout = () => {
    onConfirm(clearLocalData);
  };

  return (
    <>
      {/* 背景遮罩 */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          zIndex: 9998,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px'
        }}
        onClick={onClose}
      >
        {/* 对话框容器 */}
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '480px',
            background: '#0D1B2A',
            border: '1px solid #2A2F3A',
            borderRadius: '24px',
            boxShadow: '0px 20px 60px 0px rgba(0, 0, 0, 0.5)',
            overflow: 'hidden'
          }}
        >
          {/* 顶部标题栏 */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px 20px 17px',
            borderBottom: '1px solid #2A2F3A'
          }}>
            <div style={{
              fontFamily: 'WenQuanYi Zen Hei, Inter, sans-serif',
              fontWeight: 600,
              fontSize: '18px',
              lineHeight: '24px',
              color: '#E6EEF8'
            }}>
              确认退出登录
            </div>

            {/* 关闭按钮 */}
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: 0.8,
                transition: 'opacity 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
              onMouseLeave={(e) => e.currentTarget.style.opacity = '0.8'}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5" stroke="#E6EEF8" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>
          </div>

          {/* 主内容区 */}
          <div style={{
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {/* 警告提示框 */}
            <div style={{
              display: 'flex',
              gap: '12px',
              padding: '12px',
              background: '#F59E0B',
              borderRadius: '12px'
            }}>
              {/* 警告图标 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                paddingTop: '2px'
              }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M12 9V13M12 17H12.01M10.29 3.86L1.82002 18C1.64539 18.3024 1.55299 18.6453 1.55201 18.9945C1.55103 19.3437 1.64151 19.6871 1.81445 19.9905C1.98738 20.2939 2.23675 20.5467 2.53773 20.7239C2.83872 20.9012 3.18082 20.9962 3.53002 21H20.47C20.8192 20.9962 21.1613 20.9012 21.4623 20.7239C21.7633 20.5467 22.0127 20.2939 22.1856 19.9905C22.3585 19.6871 22.449 19.3437 22.448 18.9945C22.447 18.6453 22.3546 18.3024 22.18 18L13.71 3.86C13.5318 3.56611 13.2807 3.32312 12.9812 3.15448C12.6817 2.98585 12.3438 2.89726 12 2.89726C11.6562 2.89726 11.3184 2.98585 11.0188 3.15448C10.7193 3.32312 10.4683 3.56611 10.29 3.86Z" stroke="#1A1200" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>

              {/* 提示文本 */}
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                flex: 1
              }}>
                <div style={{
                  fontFamily: 'WenQuanYi Zen Hei, Inter, sans-serif',
                  fontWeight: 600,
                  fontSize: '14px',
                  lineHeight: '17px',
                  color: '#1A1200',
                  marginBottom: '4px'
                }}>
                  是否确定要退出当前账号？
                </div>
                <div style={{
                  fontFamily: 'WenQuanYi Zen Hei, Inter, sans-serif',
                  fontWeight: 400,
                  fontSize: '14px',
                  lineHeight: '18px',
                  color: '#9CA3AF'
                }}>
                  您将无法继续进行智能对话与知识库管理。下次可通过任意方式重新登录。
                </div>
              </div>
            </div>

            {/* 清除本地会话选项 */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 11px',
                background: '#0D1B2A',
                border: '1px solid #2A2F3A',
                borderRadius: '12px',
                cursor: 'pointer'
              }}
              onClick={() => setClearLocalData(!clearLocalData)}
              >
                {/* 复选框 */}
                <div style={{
                  width: '16px',
                  height: '16px',
                  border: '1.33px solid #CFE8FF',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: clearLocalData ? '#CFE8FF' : 'transparent',
                  transition: 'all 0.2s'
                }}>
                  {clearLocalData && (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M2 6L5 9L10 3" stroke="#0D1B2A" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </div>

                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, Inter, sans-serif',
                  fontWeight: 400,
                  fontSize: '13px',
                  lineHeight: '16px',
                  color: '#CFE8FF'
                }}>
                  清除本地会话
                </span>
              </div>

              <div style={{
                fontFamily: 'WenQuanYi Zen Hei, Inter, sans-serif',
                fontWeight: 400,
                fontSize: '12px',
                lineHeight: '15px',
                color: '#9CA3AF'
              }}>
                不影响服务器上的数据
              </div>
            </div>
          </div>

          {/* 底部按钮区 */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '15px 20px 14px',
            borderTop: '1px solid #2A2F3A'
          }}>
            {/* 取消按钮 */}
            <button
              onClick={onClose}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 13px 10.5px',
                background: '#0D1B2A',
                border: '1px solid #2A2F3A',
                borderRadius: '48px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#1A2332'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#0D1B2A'}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M12 4L4 12M4 4L12 12" stroke="#CFE8FF" strokeWidth="1.33" strokeLinecap="round"/>
              </svg>
              <span style={{
                fontFamily: 'WenQuanYi Zen Hei, Inter, sans-serif',
                fontWeight: 500,
                fontSize: '14px',
                lineHeight: '17px',
                color: '#CFE8FF'
              }}>
                取消
              </span>
            </button>

            {/* 右侧按钮组 */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              {/* 仅登出按钮 */}
              <button
                onClick={() => onConfirm(false)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 13px 10.5px',
                  background: '#0D1B2A',
                  border: '1px solid #2A2F3A',
                  borderRadius: '48px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#1A2332'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#0D1B2A'}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M10.6667 11.3333L14 8M14 8L10.6667 4.66667M14 8H6M6 2H5.2C4.0799 2 3.51984 2 3.09202 2.21799C2.71569 2.40973 2.40973 2.71569 2.21799 3.09202C2 3.51984 2 4.0799 2 5.2V10.8C2 11.9201 2 12.4802 2.21799 12.908C2.40973 13.2843 2.71569 13.5903 3.09202 13.782C3.51984 14 4.0799 14 5.2 14H6" stroke="#CFE8FF" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, Inter, sans-serif',
                  fontWeight: 500,
                  fontSize: '14px',
                  lineHeight: '17px',
                  color: '#CFE8FF'
                }}>
                  仅登出
                </span>
              </button>

              {/* 退出并清除按钮（主要操作） */}
              <button
                onClick={handleLogout}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 13px 10.5px',
                  background: '#EF4444',
                  border: 'none',
                  borderRadius: '48px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#DC2626'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#EF4444'}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M5.33333 2H4.53333C3.41323 2 2.85318 2 2.42535 2.21799C2.04903 2.40973 1.74307 2.71569 1.55132 3.09202C1.33333 3.51984 1.33333 4.0799 1.33333 5.2V10.8C1.33333 11.9201 1.33333 12.4802 1.55132 12.908C1.74307 13.2843 2.04903 13.5903 2.42535 13.782C2.85318 14 3.41323 14 4.53333 14H5.33333M6.66667 11.3333L10 8M10 8L6.66667 4.66667M10 8H1.33333M10.6667 2L11.3333 2C12.4534 2 13.0135 2 13.4413 2.21799C13.8176 2.40973 14.1236 2.71569 14.3153 3.09202C14.5333 3.51984 14.5333 4.0799 14.5333 5.2V10.8C14.5333 11.9201 14.5333 12.4802 14.3153 12.908C14.1236 13.2843 13.8176 13.5903 13.4413 13.782C13.0135 14 12.4534 14 11.3333 14H10.6667" stroke="#FFFFFF" strokeWidth="1.33" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, Inter, sans-serif',
                  fontWeight: 500,
                  fontSize: '14px',
                  lineHeight: '17px',
                  color: '#FFFFFF'
                }}>
                  退出并清除
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

