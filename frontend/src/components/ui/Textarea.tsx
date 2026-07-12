import React from 'react';
import { clsx } from 'clsx';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const generatedId = React.useId();
    const textareaId = id || generatedId;
    const errorId = error ? `${textareaId}-error` : undefined;
    const hintId = hint ? `${textareaId}-hint` : undefined;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={textareaId} className="form-label">
            {label}
            {props.required && <span className="text-error ml-1">*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          aria-invalid={!!error}
          aria-describedby={errorId || hintId}
          className={clsx(
            'form-input resize-vertical',
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

Textarea.displayName = 'Textarea';
