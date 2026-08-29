import React from 'react';
import { AlertCircle, X } from 'lucide-react';
import { getErrorDetails } from '../utils/errorMessages';

interface ErrorAlertProps {
  error: any;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ error, onDismiss, className = '' }) => {
  if (!error) return null;

  const errorDetails = getErrorDetails(error);

  return (
    <div className={`bg-error/10 border border-error/20 rounded-lg p-4 ${className}`}>
      <div className="flex gap-3">
        <AlertCircle className="w-5 h-5 text-error flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-error">{errorDetails.title}</h3>
          <p className="text-sm text-error/80 mt-1">{errorDetails.message}</p>
          {errorDetails.suggestion && (
            <p className="text-xs text-error/60 mt-2 italic">💡 {errorDetails.suggestion}</p>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-error/60 hover:text-error transition-colors flex-shrink-0"
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

interface ErrorBannerProps {
  error: any;
  onDismiss?: () => void;
}

/**
 * Full-width error banner (for page-level errors)
 */
export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error, onDismiss }) => {
  if (!error) return null;

  const errorDetails = getErrorDetails(error);

  return (
    <div className="bg-error/5 border-l-4 border-error rounded p-4 mb-6">
      <div className="flex gap-4">
        <AlertCircle className="w-6 h-6 text-error flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-error">{errorDetails.title}</h2>
          <p className="text-error/80 mt-1">{errorDetails.message}</p>
          {errorDetails.suggestion && (
            <p className="text-sm text-error/70 mt-2 bg-error/5 rounded p-2">
              <strong>What to do:</strong> {errorDetails.suggestion}
            </p>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-error/60 hover:text-error transition-colors flex-shrink-0"
            aria-label="Dismiss error"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
};
