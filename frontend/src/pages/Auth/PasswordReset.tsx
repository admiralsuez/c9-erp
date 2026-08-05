import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';
import { authApi } from '../../api/auth';

export default function PasswordReset() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const validatePassword = (pwd: string): string[] => {
    const errors: string[] = [];
    if (pwd.length < 8) errors.push('At least 8 characters');
    if (!/[A-Z]/.test(pwd)) errors.push('One uppercase letter');
    if (!/[a-z]/.test(pwd)) errors.push('One lowercase letter');
    if (!/[0-9]/.test(pwd)) errors.push('One number');
    return errors;
  };

  const passwordErrors = validatePassword(password);
  const isPasswordValid = passwordErrors.length === 0 && password.length >= 8;
  const isFormValid = isPasswordValid && password === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setError('Invalid reset link');
      return;
    }

    if (!isFormValid) {
      setError('Please fix the errors above');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await authApi.resetPassword({
        token,
        new_password: password,
      });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Password reset failed');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900">Invalid Link</h1>
            <p className="mt-2 text-gray-600">
              This password reset link is invalid or has expired.
            </p>
          </div>
          <button
            onClick={() => navigate('/login')}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <CheckCircle className="mx-auto h-12 w-12 text-green-600" />
            <h1 className="mt-4 text-2xl font-bold text-gray-900">
              Password Updated
            </h1>
            <p className="mt-2 text-gray-600">
              Your password has been successfully reset. Redirecting to login...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Reset Password</h1>
          <p className="mt-2 text-gray-600">
            Enter your new password below
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

          {/* New Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              New Password
            </label>
            <div className="mt-1 relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter new password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>

            {/* Password strength indicator */}
            {password && (
              <div className="mt-3 space-y-2">
                <div className="text-sm font-medium text-gray-700">
                  Password must contain:
                </div>
                <div className="space-y-1">
                  {[
                    {
                      label: 'At least 8 characters',
                      met: password.length >= 8,
                    },
                    {
                      label: 'One uppercase letter',
                      met: /[A-Z]/.test(password),
                    },
                    {
                      label: 'One lowercase letter',
                      met: /[a-z]/.test(password),
                    },
                    { label: 'One number', met: /[0-9]/.test(password) },
                  ].map((req) => (
                    <div key={req.label} className="flex items-center text-xs">
                      <div
                        className={`h-2 w-2 rounded-full mr-2 ${
                          req.met ? 'bg-green-500' : 'bg-gray-300'
                        }`}
                      />
                      <span
                        className={req.met ? 'text-green-700' : 'text-gray-500'}
                      >
                        {req.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Confirm Password
            </label>
            <div className="mt-1 relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  confirmPassword &&
                  password !== confirmPassword &&
                  'border-red-500'
                }`}
                placeholder="Confirm new password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
            {confirmPassword && password !== confirmPassword && (
              <p className="mt-1 text-xs text-red-500">
                Passwords do not match
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!isFormValid || loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Resetting...' : 'Reset Password'}
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
