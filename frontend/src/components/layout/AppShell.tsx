'use client';

import React from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { CommandPalette } from '../overlays/CommandPalette';
import { NotificationsDropdown } from '../overlays/NotificationsDropdown';
import { ToastProvider } from '../overlays/ToastContext';
import { usePathname } from 'next/navigation';

function AppShellInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [cmdOpen, setCmdOpen] = React.useState(false);
  const [notifOpen, setNotifOpen] = React.useState(false);

  React.useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); setCmdOpen(true); }
    };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, []);

  const getBreadcrumb = () => {
    const segments = pathname.split('/').filter(Boolean);
    if (segments.length === 0) return ['Dashboard'];
    const labels: Record<string, string> = {
      dashboard: 'Dashboard', patients: 'Patients', schedule: 'Schedule',
      treatment: 'Treatment Plans', lab: 'Lab Pipeline', billing: 'Billing',
      reports: 'Reports', crm: 'CRM', communications: 'Communications',
      plans: 'Plans', settings: 'Settings', invoices: 'Invoice', leads: 'Lead',
      denture: 'Denture Case', appointments: 'Appointment',
    };
    return segments.map(s => labels[s] || s.charAt(0).toUpperCase() + s.slice(1).replace(/-/g, ' '));
  };

  return (
    <>
      <div className="shell">
        <Sidebar />
        <div className="stage">
          <TopBar
            breadcrumb={getBreadcrumb()}
            onSearch={() => setCmdOpen(true)}
            onNotifications={() => setNotifOpen(o => !o)}
          />
          <div className="body">
            {children}
          </div>
        </div>
      </div>

      {cmdOpen && <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />}
      {notifOpen && <NotificationsDropdown onClose={() => setNotifOpen(false)} />}
    </>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <ToastProvider>
      <AppShellInner>{children}</AppShellInner>
    </ToastProvider>
  );
}
