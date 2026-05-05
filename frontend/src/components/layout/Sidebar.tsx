'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV, GROUP_ORDER } from '@/lib/data';
import { 
  LayoutDashboard, Users, Calendar, ClipboardList, FlaskConical, 
  DollarSign, MessageCircle, UserRoundPlus, ChartLine, Mic, Settings, 
  ChevronDown, Check
} from 'lucide-react';

const iconMap: Record<string, React.ReactNode> = {
  LayoutDashboard: <LayoutDashboard size={16} strokeWidth={1.5} />,
  Users: <Users size={16} strokeWidth={1.5} />,
  Calendar: <Calendar size={16} strokeWidth={1.5} />,
  ClipboardList: <ClipboardList size={16} strokeWidth={1.5} />,
  FlaskConical: <FlaskConical size={16} strokeWidth={1.5} />,
  DollarSign: <DollarSign size={16} strokeWidth={1.5} />,
  MessageCircle: <MessageCircle size={16} strokeWidth={1.5} />,
  UserRoundPlus: <UserRoundPlus size={16} strokeWidth={1.5} />,
  ChartLine: <ChartLine size={16} strokeWidth={1.5} />,
  Mic: <Mic size={16} strokeWidth={1.5} />,
  Settings: <Settings size={16} strokeWidth={1.5} />,
};

interface SidebarProps {
  collapsed?: boolean;
  clinicName?: string;
  userName?: string;
}

export function Sidebar({ collapsed = false, clinicName = 'Oak Dental Calgary', userName = 'Dr Hau Le' }: SidebarProps) {
  const pathname = usePathname();
  const [switcherOpen, setSwitcherOpen] = React.useState(false);
  const W = collapsed ? 64 : 240;

  const getActiveKey = () => {
    for (const item of NAV) {
      if (pathname.startsWith(item.href) && item.href !== '/dashboard') return item.key;
    }
    return 'dashboard';
  };

  const active = getActiveKey();
  const groups = GROUP_ORDER.map(g => ({ label: g, items: NAV.filter(n => n.group === g) }));

  const initials = userName.split(' ').map(s => s[0]).slice(0, 2).join('');

  React.useEffect(() => {
    if (!switcherOpen) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('#rrd-clinic-switcher') || target.closest('#rrd-clinic-switcher-menu')) return;
      setSwitcherOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [switcherOpen]);

  return (
    <aside style={{
      width: W, minHeight: '100vh', background: '#0A192F', color: '#FAF9F6',
      display: 'flex', flexDirection: 'column', flexShrink: 0,
      transition: 'width 250ms cubic-bezier(0.16,1,0.3,1)',
      position: 'sticky', top: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '18px 16px 22px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <Link href="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <img src="/assets/RR_logo_white.svg" alt="RR" style={{ height: 28, flexShrink: 0 }} />
          {!collapsed && (
            <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.05 }}>
              <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: '0.78rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: '#FAF9F6' }}>ROCKYRIDGE</span>
              <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 400, fontSize: '0.66rem', color: 'rgba(250,249,246,0.6)', letterSpacing: 1.4, textTransform: 'uppercase' }}>DENTAL AI</span>
            </div>
          )}
        </Link>
      </div>

      {!collapsed && (
        <div style={{ padding: '12px 12px 4px', position: 'relative' }}>
          <button
            id="rrd-clinic-switcher"
            type="button"
            aria-expanded={switcherOpen}
            onClick={() => setSwitcherOpen(o => !o)}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: 'rgba(58,127,189,0.08)', border: '1px solid rgba(255,255,255,0.10)',
              borderRadius: 6, padding: '10px 12px', color: '#FAF9F6',
              fontFamily: "'Inter', sans-serif", fontSize: '0.82rem', fontWeight: 500,
              cursor: 'pointer', textAlign: 'left' as const,
            }}
          >
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {clinicName}
            </span>
            <ChevronDown size={14} strokeWidth={1.5} style={{ transform: switcherOpen ? 'rotate(180deg)' : 'none', transition: 'transform 200ms' }} />
          </button>
          {switcherOpen && (
            <ul id="rrd-clinic-switcher-menu" role="menu" style={{
              position: 'absolute', top: '100%', left: 12, right: 12, marginTop: 4,
              background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6,
              boxShadow: '0 8px 24px rgba(10,25,47,0.18)',
              listStyle: 'none', margin: 0, padding: 4, zIndex: 20,
            }}>
              <li role="menuitem" style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '8px 10px', borderRadius: 4, cursor: 'pointer',
                fontFamily: "'Inter', sans-serif", fontSize: '0.85rem',
                color: '#3A7FBD', fontWeight: 600, background: 'transparent',
              }}>
                <span>{clinicName}</span>
                <Check size={14} strokeWidth={2} />
              </li>
            </ul>
          )}
        </div>
      )}

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {groups.map(g => (
          <div key={g.label} style={{ padding: '16px 10px 4px' }}>
            {!collapsed && (
              <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.62rem', fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#8A9BB0', padding: '0 10px 4px' }}>
                {g.label}
              </div>
            )}
            {g.items.map(it => {
              const isActive = active === it.key;
              return (
                <Link
                  key={it.key}
                  href={it.href}
                  aria-current={isActive ? 'page' : undefined}
                  title={collapsed ? it.label : undefined}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                    padding: collapsed ? '10px 0' : '8px 10px',
                    justifyContent: collapsed ? 'center' : 'flex-start',
                    borderRadius: 4, background: isActive ? '#3A7FBD' : 'transparent',
                    color: isActive ? '#fff' : 'rgba(250,249,246,0.75)',
                    fontFamily: "'Inter', sans-serif", fontSize: '0.85rem',
                    fontWeight: isActive ? 600 : 400,
                    cursor: 'pointer', transition: 'background-color 200ms ease',
                    textDecoration: 'none', boxSizing: 'border-box',
                  }}
                >
                  {iconMap[it.icon]}
                  {!collapsed && (
                    <>
                      {it.label}
                      {it.isNew && (
                        <span style={{ marginLeft: 6, fontSize: '0.55rem', fontWeight: 700, letterSpacing: '0.08em', padding: '2px 6px', borderRadius: 999, background: '#3A7FBD', color: '#fff', textTransform: 'uppercase' }}>
                          NEW
                        </span>
                      )}
                    </>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      <div style={{ padding: '14px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: 999, background: '#3A7FBD', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.72rem', flexShrink: 0 }}>
          {initials}
        </div>
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
            <span style={{ fontSize: '0.82rem' }}>{userName}</span>
            <span style={{ fontSize: '0.66rem', color: '#8A9BB0' }}>{clinicName}</span>
          </div>
        )}
      </div>
    </aside>
  );
}
