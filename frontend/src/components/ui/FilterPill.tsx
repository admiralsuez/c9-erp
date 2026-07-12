import React from 'react';
import { clsx } from 'clsx';

interface FilterPillProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  children: React.ReactNode;
}

export const FilterPill = React.forwardRef<HTMLButtonElement, FilterPillProps>(
  ({ active = false, className, children, ...props }, ref) => (
    <button
      ref={ref}
      type="button"
      className={clsx(
        'px-3 py-1 text-xs font-medium rounded-full border transition-colors',
        active
          ? 'bg-primary-600 text-white border-primary-600'
          : 'border-neutral-300 text-neutral-700 hover:bg-neutral-100',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
);
FilterPill.displayName = 'FilterPill';
