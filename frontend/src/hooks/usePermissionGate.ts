/**
 * Permission + role check helpers.
 *
 * The backend's RBAC model is permission-code based (e.g. ``orders.cancel``,
 * ``inventory.delete``) and the ``/auth/me`` response embeds the user's role
 * with all granted permissions. Frontend route guards use these helpers so
 * the same permission codes that the API checks are enforced client-side.
 */
import { useMemo } from 'react';
import { useAuth } from '../hooks/useAuth';
import type { Permission, User } from '../types';

export interface PermissionGateResult {
  /** True when the user holds every code in ``requiredPermissions``. */
  hasAllPermissions: boolean;
  /** True when the user holds at least one code in ``requiredPermissions``. */
  hasAnyPermission: boolean;
  /** Direct accessor for a single code. */
  hasPermission: (code: string) => boolean;
  /** True when the user's role name matches any of ``allowedRoles``. */
  hasRole: (...roles: string[]) => boolean;
  /** Convenience: true when the role is "Admin" (case-insensitive). */
  isAdmin: boolean;
}

/**
 * Build a permission gate from the current auth state.
 *
 * Pass an empty array for ``requiredPermissions`` to skip the permission
 * check (the gate will still load and expose ``hasRole`` / ``hasPermission``).
 */
export function usePermissionGate(
  requiredPermissions: string[] = [],
  allowedRoles: string[] = [],
): PermissionGateResult {
  const { user } = useAuth();

  return useMemo(() => {
    const codes = collectPermissionCodes(user);
    const codeSet = new Set(codes);

    return {
      hasAllPermissions:
        requiredPermissions.length === 0 ||
        requiredPermissions.every((code) => codeSet.has(code)),
      hasAnyPermission:
        requiredPermissions.length === 0 ||
        requiredPermissions.some((code) => codeSet.has(code)),
      hasPermission: (code: string) => codeSet.has(code),
      hasRole: (...roles: string[]) =>
        !!user?.role && roles.some(
          (r) => r.toLowerCase() === (user.role?.name || '').toLowerCase(),
        ),
      isAdmin: (user?.role?.name || '').toLowerCase() === 'admin',
      _codes: codes, // for tests / debugging
    } as PermissionGateResult;
  }, [user, requiredPermissions.join('|'), allowedRoles.join('|')]);
}

/**
 * Walk the user's role + permissions and return a flat list of permission
 * codes. Handles nested permission objects the API might return.
 */
export function collectPermissionCodes(user: User | null | undefined): string[] {
  if (!user?.role?.permissions) return [];
  const perms = user.role.permissions;
  if (!Array.isArray(perms)) return [];
  return perms
    .map((p: Permission | string) => (typeof p === 'string' ? p : p?.code))
    .filter((c): c is string => !!c);
}
