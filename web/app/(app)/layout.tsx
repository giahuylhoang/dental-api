"use client";
import { AuthGuard } from "@/lib/auth/guard";
import { AppShell } from "@/components/layout/AppShell";
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}
