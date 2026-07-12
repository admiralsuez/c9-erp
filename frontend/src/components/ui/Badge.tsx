import React from 'react';
import { clsx } from 'clsx';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'success' | 'warning' | 'error' | 'neutral';
  size?: 'sm' | 'md';
  children: React.ReactNode;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'primary', size = 'md', className, children, ...props }, ref) => {
    const variants = {
      primary: 'badge-primary',
      success: 'badge-success',
      warning: 'badge-warning',
      error: 'badge-error',
      neutral: 'bg-neutral-100 text-neutral-700',
    };

    const sizes = {
      sm: 'px-2 py-1 text-xs',
      md: 'px-3 py-1.5 text-sm',
    };

    return (
      <span
        ref={ref}
        className={clsx('badge', variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

// Status Badge - specialized for order/item status
interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: string;
  children?: React.ReactNode;
}

const statusVariants: Record<string, string> = {
  draft: 'bg-neutral-100 text-neutral-700',
  pending_requisition: 'badge-warning',
  signed_requisition_uploaded: 'bg-blue-100 text-blue-700',
  approved: 'bg-blue-100 text-blue-700',
  dispatched: 'badge-primary',
  delivered: 'badge-success',
  closed: 'badge-neutral',
  cancelled: 'badge-error',
  active: 'badge-success',
  inactive: 'badge-neutral',
};

export const StatusBadge = React.forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ status, className, children, ...props }, ref) => (
    <span
      ref={ref}
      className={clsx(
        'status-badge inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold',
        statusVariants[status] || 'badge-neutral',
        className
      )}
      {...props}
    >
      {children || status}
    </span>
  )
);

StatusBadge.displayName = 'StatusBadge';
