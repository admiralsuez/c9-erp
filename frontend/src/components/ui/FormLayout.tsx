import React from 'react';
import { clsx } from 'clsx';

interface FormGroupProps {
  label?: string;
  error?: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}

export const FormGroup: React.FC<FormGroupProps> = ({ label, error, hint, children, className }) => (
  <div className={clsx('w-full', className)}>
    {label && (
      <label className="block text-sm font-medium text-neutral-700 mb-1">
        {label}
      </label>
    )}
    {children}
    {error && <p className="text-xs text-error mt-0.5" role="alert">{error}</p>}
    {hint && <p className="text-xs text-neutral-400 mt-0.5">{hint}</p>}
  </div>
);

interface FormRowProps {
  children: React.ReactNode;
  cols?: 1 | 2 | 3 | 4;
  className?: string;
}

export const FormRow: React.FC<FormRowProps> = ({ children, cols = 2, className }) => {
  const gridCols: Record<number, string> = { 1: 'grid-cols-1', 2: 'grid-cols-1 md:grid-cols-2', 3: 'grid-cols-1 md:grid-cols-3', 4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4' };
  return (
    <div className={clsx('grid gap-4', gridCols[cols], className)}>
      {children}
    </div>
  );
};

interface FormSectionProps {
  title: string;
  description?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

export const FormSection: React.FC<FormSectionProps> = ({ title, description, defaultOpen = true, children }) => {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <div className="border border-neutral-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-neutral-50 hover:bg-neutral-100 transition-colors text-left"
      >
        <div>
          <p className="font-medium text-neutral-900">{title}</p>
          {description && <p className="text-xs text-neutral-500 mt-0.5">{description}</p>}
        </div>
        <svg
          className={clsx('w-4 h-4 text-neutral-500 transition-transform', open && 'rotate-180')}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
};
