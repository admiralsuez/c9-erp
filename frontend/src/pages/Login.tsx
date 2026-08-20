import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Button, Input, Card } from '../components/ui';
import { loginSchema } from '../utils/validation';
import { useAuth } from '../hooks/useAuth';
import { useSettings } from '../hooks/useSettings';
import { AlertCircle, Eye, EyeOff } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { data: settings } = useSettings();
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  const onSubmit = async (data: any) => {
    setApiError(null);
    setIsLoading(true);

    try {
      await login(data.email, data.password);
      // Login successful, redirect to dashboard
      navigate('/');
    } catch (error) {
      const axiosError = error as AxiosError<any>;
      const errorMessage =
        axiosError.response?.data?.detail ||
        axiosError.response?.data?.message ||
        'Email or password is incorrect';
      setApiError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-neutral-50 to-primary-50 px-4">
      <div className="w-full max-w-md">
        <Card padding="lg" className="shadow-lg">
          {/* Logo & Header */}
          <div className="text-center mb-8">
            {settings?.company_logo_url ? (
              <img
                src={settings.company_logo_url}
                alt={settings.company_name || 'Company Logo'}
                className="h-16 mx-auto mb-2 object-contain"
              />
            ) : (
              <h1 className="text-3xl font-bold text-primary-600 mb-2">{settings?.company_name || 'Cloud9 ERP'}</h1>
            )}
            {!settings?.company_logo_url && <p className="text-neutral-600">Sign in to manage your inventory</p>}
          </div>

          {/* Error Banner */}
          {apiError && (
            <div className="mb-6 p-4 bg-error/10 border border-error rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-error flex-shrink-0 mt-0.5" />
              <p className="text-sm text-error">{apiError}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email Field */}
            <div>
              <Input
                {...register('email')}
                type="email"
                placeholder="Email address"
                label="Email"
                error={errors.email?.message}
                isRounded
                disabled={isLoading}
              />
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">Password</label>
              <div className="relative">
                <Input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  error={errors.password?.message}
                  isRounded
                  disabled={isLoading}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600 disabled:opacity-50"
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
              {errors.password?.message && (
                <p className="mt-1 text-sm text-error">{errors.password.message}</p>
              )}
            </div>

            {/* Remember Me */}
            <div className="flex items-center">
              <input
                {...register('rememberMe')}
                type="checkbox"
                id="rememberMe"
                className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-2 focus:ring-primary-500"
                disabled={isLoading}
              />
              <label htmlFor="rememberMe" className="ml-2 text-sm text-neutral-700">
                Remember me
              </label>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              isLoading={isLoading}
              disabled={isLoading}
              className="w-full mt-6"
            >
              Sign In
            </Button>
          </form>

          {/* Footer Links */}
          <div className="mt-6 text-center">
            <button
              type="button"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
              onClick={() => navigate('/forgot-password')}
              disabled={isLoading}
            >
              Forgot password?
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;
