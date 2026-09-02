import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Top-level error boundary.
 *
 * NOTE on navigation: this boundary sits ABOVE the BrowserRouter in the
 * component tree (App.tsx), so ``useNavigate`` is not available here. We
 * use ``window.location.assign`` for the recovery button — by the time a
 * user clicks "Go to Home" the React tree has already failed, so a hard
 * reload is the simplest correct recovery. Prefer ``useNavigate`` for any
 * navigation that originates inside a healthy React tree (see
 * AuthContext.logout, app pages, etc.).
 */
export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50 p-8">
          <div className="max-w-md text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-error-100 flex items-center justify-center">
              <span className="text-2xl text-error-600">!</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Something went wrong
            </h1>
            <p className="text-gray-600 mb-6 text-sm">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.assign('/');
              }}
              className="btn-primary"
            >
              Go to Home
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
