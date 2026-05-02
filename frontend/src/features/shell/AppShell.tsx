import { type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../auth/store';

const NAV = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Patients', to: '/patients' },
  { label: 'Schedule', to: '/schedule' },
  { label: 'Lab', to: '/lab' },
  { label: 'Plans', to: '/plans' },
  { label: 'CRM', to: '/crm' },
  { label: 'Billing', to: '/billing' },
  { label: 'Communications', to: '/communications' },
  { label: 'Settings', to: '/settings' },
];

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-zinc-200 bg-white p-4">
        <h1 className="mb-4 text-lg font-semibold">Denturist PMS</h1>
        <nav className="space-y-1 text-sm">
          {NAV.map((n) => (
            <Link
              key={n.to}
              to={n.to}
              className="block rounded px-2 py-1 hover:bg-zinc-100"
            >
              {n.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3">
          <span className="text-sm text-zinc-500">Press ⌘K to search</span>
          <div className="flex items-center gap-3 text-sm">
            {user && <span className="text-zinc-700">{user.full_name}</span>}
            <button
              onClick={handleLogout}
              className="rounded px-2 py-1 text-zinc-500 hover:bg-zinc-100"
            >
              Sign out
            </button>
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
