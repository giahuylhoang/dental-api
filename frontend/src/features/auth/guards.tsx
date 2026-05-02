import { type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from './store';

export function Authed({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function RequirePermission({
  perms,
  children,
}: {
  perms: string[];
  children: ReactNode;
}) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  const allowed =
    user.permissions.includes('*.*') ||
    perms.every((p) => user.permissions.includes(p));
  if (!allowed) return <div className="p-6 text-sm text-red-600">Access denied.</div>;
  return <>{children}</>;
}
