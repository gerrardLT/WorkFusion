import * as React from 'react';
import { cva, type VariantProps } from '@/lib/cva';

import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
        secondary: 'border-transparent bg-slate-100 text-slate-700 hover:bg-slate-200',
        destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
        outline: 'text-foreground border-border',
        success: 'border-transparent bg-green-500 text-white hover:bg-green-600',
        warning: 'border-transparent bg-slate-100 text-slate-700 hover:bg-slate-200',
        info: 'border-transparent bg-blue-500 text-white hover:bg-blue-600',
        gradient: 'border-transparent bg-gradient-to-r from-brand-500 to-accent-500 text-white hover:from-brand-600 hover:to-accent-600',
      },
      size: {
        sm: 'px-2.5 py-0.5 text-xs',
        default: 'px-3 py-1 text-sm',
        lg: 'px-4 py-1.5 text-base',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode;
  closable?: boolean;
  onClose?: () => void;
}

function Badge({
  className,
  variant,
  size,
  icon,
  closable = false,
  onClose,
  children,
  ...props
}: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant, size }), className)} {...props}>
      {icon && (
        <span className="mr-1 -ml-0.5">
          {icon}
        </span>
      )}
      {children}
      {closable && onClose && (
        <button
          type="button"
          onClick={onClose}
          className="ml-1 -mr-0.5 hover:bg-black/10 dark:hover:bg-white/10 rounded-full p-0.5 transition-colors"
        >
          <svg
            className="h-3 w-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </div>
  );
}

// Status Badge Component
interface StatusBadgeProps {
  status: 'online' | 'offline' | 'maintenance' | 'loading';
  className?: string;
}

function StatusBadge({ status, className }: StatusBadgeProps) {
  const statusConfig = {
    online: {
      variant: 'success' as const,
      text: '在线',
      icon: (
        <div className="h-2 w-2 bg-success-400 rounded-full animate-pulse" />
      ),
    },
    offline: {
      variant: 'destructive' as const,
      text: '离线',
      icon: (
        <div className="h-2 w-2 bg-destructive rounded-full" />
      ),
    },
    maintenance: {
      variant: 'warning' as const,
      text: '维护中',
      icon: (
        <div className="h-2 w-2 bg-warning-400 rounded-full animate-pulse" />
      ),
    },
    loading: {
      variant: 'secondary' as const,
      text: '连接中',
      icon: (
        <div className="h-2 w-2 bg-muted-foreground rounded-full animate-spin" />
      ),
    },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size="sm" icon={config.icon} className={className}>
      {config.text}
    </Badge>
  );
}

// Confidence Badge Component
interface ConfidenceBadgeProps {
  confidence: 'high' | 'medium' | 'low' | number;
  className?: string;
}

function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  let variant: 'success' | 'secondary' | 'destructive' | 'outline';
  let text: string;
  let percentage: number;

  if (typeof confidence === 'string') {
    switch (confidence) {
      case 'high':
        variant = 'success';
        text = '高置信度';
        percentage = 90;
        break;
      case 'medium':
        variant = 'secondary';  // 改为 secondary（灰色），不使用 warning（黄色）
        text = '中等置信度';
        percentage = 60;
        break;
      case 'low':
        variant = 'destructive';
        text = '低置信度';
        percentage = 30;
        break;
      default:
        variant = 'outline';
        text = '未知';
        percentage = 0;
    }
  } else {
    percentage = Math.round(confidence * 100);
    text = `${percentage}%`;

    if (percentage >= 80) {
      variant = 'success';
    } else if (percentage >= 60) {
      variant = 'secondary';  // 改为 secondary（灰色），不使用 warning（黄色）
    } else {
      variant = 'destructive';
    }
  }

  return (
    <Badge variant={variant} size="sm" className={className}>
      {text}
    </Badge>
  );
}

export { Badge, StatusBadge, ConfidenceBadge, badgeVariants };
