import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle, Mail } from 'lucide-react';
import { authApi } from '../../api/auth';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await authApi.requestPasswordReset({ email });
      setSuccess(true);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Failed to send password reset email'
      );
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <CheckCircle className="mx-auto h-12 w-12 text-green-600" />
            <h1 className="mt-4 text-2xl font-bold text-gray-900">
              Email Sent
            </h1>
            <p className="mt-2 text-gray-600">
              Check your email for a password reset link. The link will expire
              in 1 hour.
            </p>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 font-medium"
            >
              Back to Login
            </button>
            <button
              onClick={() => {
                setSuccess(false);
                setEmail('');
              }}
              className="w-full bg-gray-200 text-gray-900 py-2 rounded-lg hover:bg-gray-300 font-medium"
            >
              Reset
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Mail className="mx-auto h-12 w-12 text-blue-600" />
          <h1 className="mt-4 text-2xl font-bold text-gray-900">
            Forgot Password?
          </h1>
          <p className="mt-2 text-gray-600">
            Enter your email address and we'll send you a link to reset your
            password.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {error && (
            <div className="rounded-md bg-red-50 p-4 flex items-start">
              <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="your@email.com"
            />
          </div>

          <button
            type="submit"
            disabled={!email || loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>

          <div className="text-center text-sm text-gray-600">
            Remember your password?{' '}
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-blue-600 hover:underline"
            >
              Back to Login
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
