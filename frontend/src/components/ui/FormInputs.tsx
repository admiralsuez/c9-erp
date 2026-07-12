import React from 'react';
import { clsx } from 'clsx';

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
}

export const TextInput = React.forwardRef<HTMLInputElement, TextInputProps>(
  ({ label, error, hint, icon, className, id, ...props }, ref) => {
    const gid = React.useId();
    const inputId = id || gid;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-neutral-700 mb-1">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-2 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              'px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-full',
              icon && 'pl-7',
              error && 'border-error focus:ring-error',
              className
            )}
            {...props}
          />
        </div>
        {error && <p className="text-xs text-error mt-0.5" role="alert">{error}</p>}
        {hint && <p className="text-xs text-neutral-400 mt-0.5">{hint}</p>}
      </div>
    );
  }
);
TextInput.displayName = 'TextInput';

interface DateInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const DateInput = React.forwardRef<HTMLInputElement, DateInputProps>(
  ({ label, error, className, id, ...props }, ref) => {
    const gid = React.useId();
    const inputId = id || gid;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-neutral-700 mb-1">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          type="date"
          className={clsx(
            'w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500',
            error && 'border-error focus:ring-error',
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-error mt-0.5" role="alert">{error}</p>}
      </div>
    );
  }
);
DateInput.displayName = 'DateInput';

interface CheckboxInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'children'> {
  label: React.ReactNode;
  description?: string;
}

export const CheckboxInput = React.forwardRef<HTMLInputElement, CheckboxInputProps>(
  ({ label, description, className, id, ...props }, ref) => {
    const gid = React.useId();
    const inputId = id || gid;
    return (
      <label htmlFor={inputId} className="flex items-center gap-2 px-2 py-1.5 hover:bg-neutral-50 cursor-pointer text-xs">
        <input
          ref={ref}
          id={inputId}
          type="checkbox"
          className={clsx('w-3.5 h-3.5 rounded border-neutral-300 text-primary-600', className)}
          {...props}
        />
        <span className="text-neutral-700">{label}</span>
        {description && <span className="text-neutral-400">{description}</span>}
      </label>
    );
  }
);
CheckboxInput.displayName = 'CheckboxInput';

interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  placeholder?: string;
}

export const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  ({ placeholder = 'Search...', className, ...props }, ref) => (
    <div className="relative">
      <svg className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        ref={ref}
        type="text"
        placeholder={placeholder}
        className={clsx(
          'w-full pl-7 pr-2 py-1.5 text-xs border border-neutral-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500',
          className
        )}
        {...props}
      />
    </div>
  )
);
SearchInput.displayName = 'SearchInput';
