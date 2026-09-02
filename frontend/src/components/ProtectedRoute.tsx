import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { usePermissionGate } from '../hooks/usePermissionGate';

interface ProtectedRouteProps {
  children: React.ReactNode;
  /**
   * Permission codes required to enter the route. When non-empty, every code
   * must be present on the user's role (logical AND). Omit to require
   * authentication only.
   */
  requiredPermissions?: string[];
  /**
   * Role names allowed to enter the route. Omit to allow any authenticated
   * user. Compared case-insensitively.
   */
  allowedRoles?: string[];
}

const LoadingScreen: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-neutral-50">
    <div className="flex flex-col items-center gap-4" role="status" aria-live="polite">
      <div className="w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin" />
      <p className="text-neutral-600">Loading...</p>
    </div>
  </div>
);

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermissions = [],
  allowedRoles = [],
}) => {
  const { user, isLoading } = useAuth();
  const { hasAllPermissions, hasRole } = usePermissionGate(
    requiredPermissions,
    allowedRoles,
  );

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // If the user holds insufficient permissions, bounce them to the dashboard
  // rather than rendering a broken page. (Backend still enforces the same
  // checks — this is purely UX.)
  if (requiredPermissions.length > 0 && !hasAllPermissions) {
    return <Navigate to="/" replace />;
  }

  if (allowedRoles.length > 0 && !hasRole(...allowedRoles)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
