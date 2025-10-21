"use client"

/**
 * Toaster UI 组件
 * 配合 use-toast.tsx 使用，显示 Toast 提示
 * 基于项目现有的 UI 组件体系
 */

import { useToast } from "@/components/ui/use-toast"

export function Toaster() {
  const { toasts } = useToast()

  return (
    <div
      style={{
        position: 'fixed',
        top: '24px',
        right: '24px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        pointerEvents: 'none'
      }}
    >
      {toasts.map((toast) => {
        // 根据 variant 确定样式
        const isDestructive = toast.variant === 'destructive'

        return (
          <div
            key={toast.id}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              padding: '12px 16px',
              background: isDestructive
                ? 'rgba(239, 68, 68, 0.1)'
                : 'rgba(59, 130, 246, 0.1)',
              border: `1px solid ${isDestructive ? '#EF4444' : '#3B82F6'}`,
              borderRadius: '8px',
              backdropFilter: 'blur(8px)',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              minWidth: '300px',
              maxWidth: '500px',
              animation: 'slideIn 0.3s ease-out',
              pointerEvents: 'auto'
            }}
          >
            {/* 图标 */}
            <div style={{ flexShrink: 0, marginTop: '2px' }}>
              {isDestructive ? (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 6.66667V10M10 13.3333H10.0083" stroke="#EF4444" strokeWidth="1.67" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="10" cy="10" r="7.5" stroke="#EF4444" strokeWidth="1.67"/>
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 13.3333V10M10 6.66667H10.0083" stroke="#3B82F6" strokeWidth="1.67" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="10" cy="10" r="7.5" stroke="#3B82F6" strokeWidth="1.67"/>
                </svg>
              )}
            </div>

            {/* 内容 */}
            <div style={{ flex: 1 }}>
              {toast.title && (
                <div style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: '14px',
                  fontWeight: 600,
                  lineHeight: '20px',
                  color: '#E6EEF8',
                  marginBottom: toast.description ? '4px' : 0
                }}>
                  {toast.title}
                </div>
              )}
              {toast.description && (
                <div style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: '13px',
                  lineHeight: '18px',
                  color: '#9CA3AF'
                }}>
                  {toast.description}
                </div>
              )}
              {toast.action}
            </div>

            {/* 关闭按钮 */}
            <button
              onClick={() => toast.onOpenChange?.(false)}
              style={{
                flexShrink: 0,
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: 0.6,
                transition: 'opacity 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
              onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M12 4L4 12M4 4L12 12" stroke="#E6EEF8" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
        )
      })}

      <style jsx>{`
        @keyframes slideIn {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  )
}

