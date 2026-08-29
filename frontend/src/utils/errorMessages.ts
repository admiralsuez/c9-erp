/**
 * User-friendly error message formatter
 * Translates API errors and HTTP status codes into clear, understandable messages
 */

export interface ErrorDetails {
  title: string;
  message: string;
  suggestion?: string;
}

export const getErrorDetails = (error: any): ErrorDetails => {
  // Handle axios/fetch errors
  const status = error?.response?.status;
  const data = error?.response?.data;
  const detail = data?.detail;

  // Extract the error message
  let errorMessage = '';
  if (typeof detail === 'string') {
    errorMessage = detail;
  } else if (detail?.message) {
    errorMessage = detail.message;
  } else if (data?.message) {
    errorMessage = data.message;
  } else if (error?.message) {
    errorMessage = error.message;
  } else {
    errorMessage = 'An unexpected error occurred';
  }

  // Map status codes to user-friendly errors
  switch (status) {
    case 400:
      return {
        title: 'Invalid Input',
        message: errorMessage || 'The information you provided is not valid. Please check and try again.',
        suggestion: 'Review the form fields and make sure all required information is correct.',
      };

    case 401:
      return {
        title: 'Authentication Required',
        message: 'Your session has expired or you are not logged in.',
        suggestion: 'Please log in again to continue.',
      };

    case 403:
      return {
        title: 'Access Denied',
        message: 'You do not have permission to perform this action.',
        suggestion: 'Contact an administrator if you believe you should have access.',
      };

    case 404:
      return {
        title: 'Not Found',
        message: errorMessage || 'The item you are looking for could not be found.',
        suggestion: 'It may have been deleted or the URL might be incorrect.',
      };

    case 409:
      return {
        title: 'Item Already Exists',
        message: errorMessage || 'This item already exists in the system.',
        suggestion: 'Try using a different name or check if the item is already created.',
      };

    case 422:
      return {
        title: 'Validation Error',
        message: errorMessage || 'Some fields have invalid values.',
        suggestion: 'Please review the form and correct any errors.',
      };

    case 429:
      return {
        title: 'Too Many Requests',
        message: 'You are making requests too quickly. Please wait a moment and try again.',
        suggestion: 'Rate limiting is in place to protect the system. Try again in a few seconds.',
      };

    case 500:
      return {
        title: 'Server Error',
        message: 'Something went wrong on the server. The team has been notified.',
        suggestion: 'Please try again in a few moments. If the problem persists, contact support.',
      };

    case 502:
    case 503:
    case 504:
      return {
        title: 'Service Unavailable',
        message: 'The service is temporarily unavailable. Please try again shortly.',
        suggestion: 'This is usually temporary. Wait a moment and try again.',
      };

    default:
      return {
        title: 'Error',
        message: errorMessage || 'An error occurred. Please try again.',
        suggestion: 'If the problem persists, contact support.',
      };
  }
};

/**
 * Format validation errors from API response
 */
export const formatValidationErrors = (detail: any): string[] => {
  if (Array.isArray(detail)) {
    return detail.map((err) => {
      if (typeof err === 'string') return err;
      if (err.msg) return `${err.loc?.join('.')}: ${err.msg}`;
      return 'Validation error';
    });
  }
  return [];
};

/**
 * User-friendly status messages for operations
 */
export const getStatusMessage = (status: string): string => {
  const statusMessages: Record<string, string> = {
    draft: 'Draft - Not yet submitted',
    pending_requisition: 'Awaiting Requisition Approval',
    signed_requisition_uploaded: 'Requisition Signed - Awaiting Final Approval',
    approved: 'Approved - Ready to Dispatch',
    dispatched: 'Dispatched - In Transit',
    delivered: 'Delivered - Completed',
    closed: 'Closed - Order Complete',
    cancelled: 'Cancelled - Order was cancelled',
    returned: 'Returned - Items were returned',
  };

  return statusMessages[status] || status;
};
