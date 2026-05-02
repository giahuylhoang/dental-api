import { type ReactNode, useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LayoutDashboard, Users, CalendarDays, FlaskConical, FileText,
  CreditCard, MessageSquare, TrendingUp, Settings, Bell, Menu, X,
} from 'lucide-react';
import { useAuthStore } from '../auth/store';
import CommandPalette from '../search/CommandPalette';
import { PatientChip } from '../patients/PatientChip';
import { fetcher } from '../../api/client';
import { Button } from '../../components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';

interface ClinicSettings { display_name: string }

const NAV_SECTIONS = [
  {
    label: 'Care',
    items: [
      { label: 'Patients', to: '/patients', icon: Users },
      { label: 'Schedule', to: '/schedule', icon: CalendarDays },
      { label: 'Plans', to: '/plans', icon: FileText },
      { label: 'Lab', to: '/lab', icon: FlaskConical },
    ],
  },
  {
    label: 'Ops',
    items: [
      { label: 'Billing', to: '/billing', icon: CreditCard },
      { label: 'Communications', to: '/communications', icon: MessageSquare },
    ],
  },
  {
    label: 'Growth',
    items: [
      { label: 'CRM', to: '/crm', icon: TrendingUp },
    ],
  },
  {
    label: 'Insights',
    items: [
      { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label: 'System',
    items: [
      { label: 'Settings', to: '/settings', icon: Settings },
    ],
  },
];

function usePaletteOpen() {
  const [open, setOpen] = useState(false);
  const openPalette = useCallback(() => {
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true }));
  }, []);
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') setOpen((v) => !v);
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);
  return { open, openPalette };
}

function SidebarContent({ collapsed, pathname }: { collapsed: boolean; pathname: string }) {
  return (
    <nav className="flex flex-col h-full py-4 overflow-y-auto">
      {NAV_SECTIONS.map((section) => (
        <div key={section.label} className="mb-2">
          {!collapsed && (
            <p className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
              {section.label}
            </p>
          )}
          {section.items.map(({ label, to, icon: Icon }) => {
            const active = pathname === to || pathname.startsWith(to + '/');
            return (
              <Link
                key={to}
                to={to}
                title={collapsed ? label : undefined}
                className={`flex items-center gap-3 rounded-md mx-2 px-2 py-2 text-sm transition-colors ${
                  active
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-zinc-600 hover:bg-zinc-100'
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span>{label}</span>}
              </Link>
            );
          })}
        </div>
      ))}
      {!collapsed && (
        <div className="mt-auto px-3 py-2 text-xs text-zinc-400">⌘K to search</div>
      )}
    </nav>
  );
}

function Breadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split('/').filter(Boolean);

  if (segments.length <= 1) return null;

  const crumbs: ReactNode[] = [];
  let path = '';
  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    path += '/' + seg;
    const isLast = i === segments.length - 1;
    const isPatientId = segments[i - 1] === 'patients' && seg !== 'patients';

    if (isLast && isPatientId) {
      crumbs.push(
        <span key={path} className="text-zinc-700">
          <PatientChip patientId={seg} variant="breadcrumb" />
        </span>
      );
    } else {
      const label = seg.charAt(0).toUpperCase() + seg.slice(1);
      crumbs.push(
        isLast ? (
          <span key={path} className="text-zinc-700 font-medium">{label}</span>
        ) : (
          <Link key={path} to={path} className="text-zinc-500 hover:text-zinc-700">{label}</Link>
        )
      );
    }

    if (!isLast) {
      crumbs.push(<span key={path + '-sep'} className="text-zinc-400 mx-1">/</span>);
    }
  }

  return (
    <nav aria-label="breadcrumb" className="flex items-center text-sm mb-2">
      {crumbs}
    </nav>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [hovered, setHovered] = useState(false);
  const { openPalette } = usePaletteOpen();

  const { data: clinicSettings } = useQuery<ClinicSettings>({
    queryKey: ['settings', 'clinic'],
    queryFn: () => fetcher<ClinicSettings>('/api/v2/settings/clinic'),
    staleTime: Infinity,
    retry: false,
  });

  const clinicName = clinicSettings?.display_name ?? 'Dental PMS';

  // Responsive: <768 = mobile sheet, 768-1023 = icon-only, >=1024 = full
  const [width, setWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024);
  useEffect(() => {
    function onResize() { setWidth(window.innerWidth); }
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const isMobile = width < 768;
  const isNarrow = width >= 768 && width < 1024;
  const collapsed = isNarrow && !hovered;

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const userInitials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : 'U';

  return (
    <div className="flex min-h-screen bg-zinc-50">
      {/* Desktop sidebar */}
      {!isMobile && (
        <aside
          data-collapsed={collapsed ? 'true' : 'false'}
          onMouseEnter={() => isNarrow && setHovered(true)}
          onMouseLeave={() => isNarrow && setHovered(false)}
          className={`shrink-0 border-r border-zinc-200 bg-white transition-all duration-200 ${
            collapsed ? 'w-16' : 'w-64'
          }`}
        >
          <div className={`px-3 py-4 border-b border-zinc-100 ${collapsed ? 'text-center' : ''}`}>
            {!collapsed && <span className="font-semibold text-sm text-zinc-800">{clinicName}</span>}
          </div>
          <SidebarContent collapsed={collapsed} pathname={location.pathname} />
        </aside>
      )}

      {/* Mobile sheet overlay */}
      {isMobile && mobileOpen && (
        <div className="fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <aside className="relative z-50 w-64 bg-white border-r border-zinc-200 flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-100">
              <span className="font-semibold text-sm">{clinicName}</span>
              <button onClick={() => setMobileOpen(false)} aria-label="Close menu">
                <X className="h-4 w-4" />
              </button>
            </div>
            <SidebarContent collapsed={false} pathname={location.pathname} />
          </aside>
        </div>
      )}

      <div className="flex flex-1 flex-col min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-zinc-200 bg-white px-4 py-2 gap-4">
          <div className="flex items-center gap-3">
            {isMobile && (
              <button
                aria-label="Open menu"
                data-testid="hamburger"
                onClick={() => setMobileOpen(true)}
                className="rounded p-1 hover:bg-zinc-100"
              >
                <Menu className="h-5 w-5" />
              </button>
            )}
            <span className="font-semibold text-sm text-zinc-800 hidden sm:block">{clinicName}</span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={openPalette}
            className="text-zinc-500 text-sm"
          >
            Search ⌘K
          </Button>

          <div className="flex items-center gap-2">
            <button aria-label="Notifications" className="rounded p-1 hover:bg-zinc-100">
              <Bell className="h-5 w-5 text-zinc-500" />
            </button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  aria-label="User menu"
                  className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-500 text-xs font-medium text-white"
                >
                  {userInitials}
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>Profile</DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout}>Sign out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="flex-1 p-6">
          <Breadcrumbs />
          {children}
        </main>
      </div>

      <CommandPalette />
    </div>
  );
}
