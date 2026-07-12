import React from 'react';
import { clsx } from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  isRounded?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, isRounded = true, className, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id || generatedId;
    const errorId = error ? `${inputId}-error` : undefined;
    const hintId = hint ? `${inputId}-hint` : undefined;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="form-label">
            {label}
            {props.required && <span className="text-error ml-1">*</span>}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={errorId || hintId}
          className={clsx(
            'form-input',
            isRounded && 'rounded-full',
            error && 'border-error focus:ring-error',
            !error && 'focus:ring-2 focus:ring-primary-500',
            className
          )}
          {...props}
        />
        {error && <p id={errorId} className="form-error" role="alert">{error}</p>}
        {hint && <p id={hintId} className="text-neutral-500 text-xs mt-1">{hint}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
