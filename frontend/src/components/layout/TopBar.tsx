'use client';

import React from 'react';
import Link from 'next/link';
import { Search, Bell, Mic, ChevronRight } from 'lucide-react';

interface TopBarProps {
  clinicName?: string;
  breadcrumb?: string[];
  homeHref?: string;
  mode?: string; // e.g., "AI Receptionist"
  onSearch?: () => void;
  onNotifications?: () => void;
}

export function TopBar({ 
  clinicName = 'Oak Dental · Calgary', 
  breadcrumb = ['Dashboard'], 
  homeHref = '/dashboard',
  mode,
  onSearch,
  onNotifications,
}: TopBarProps) {
  const userName = 'Dr Hau Le';
  const userEmail = 'hau@oakdentalcalgary.com';
  const initials = userName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
  const [menuOpen, setMenuOpen] = React.useState(false);

  React.useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('#rrd-profile-pill') || target.closest('#rrd-profile-menu')) return;
      setMenuOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  return (
    <header style={{
      height: 64, padding: '0 28px', background: '#fff', borderBottom: '1px solid #EDE9E0',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      position: 'sticky', top: 0, zIndex: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <Link href={homeHref} style={{ textDecoration: 'none' }}>
          <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '0.9rem', color: '#0A192F', letterSpacing: '-0.01em' }}>
            {clinicName}
          </span>
        </Link>
        {mode && (
          <span title="AI Receptionist control plane" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: '#3A7FBD', color: '#fff',
            fontFamily: "'Inter', sans-serif", fontWeight: 700,
            fontSize: '0.6rem', letterSpacing: '0.14em', textTransform: 'uppercase',
            padding: '4px 10px', borderRadius: 999, lineHeight: 1,
          }}>
            <Mic size={11} strokeWidth={2} />
            {mode}
          </span>
        )}
        <span style={{ width: 1, height: 18, background: '#EDE9E0' }} />
        <nav style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: '0.82rem', color: '#4A5568' }}>
          {breadcrumb.map((b, i) => (
            <React.Fragment key={i}>
              {i > 0 && <ChevronRight size={14} style={{ color: '#C8CCCC' }} />}
              <span style={{
                color: i === breadcrumb.length - 1 ? '#1C2333' : '#4A5568',
                fontWeight: i === breadcrumb.length - 1 ? 500 : 400,
              }}>{b}</span>
            </React.Fragment>
          ))}
        </nav>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <button onClick={onSearch} style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#FAF9F6', border: '1px solid #EDE9E0', borderRadius: 6,
          padding: '7px 12px', cursor: 'pointer', color: '#4A5568',
          fontFamily: "'Inter', sans-serif", fontSize: '0.82rem',
        }}>
          <Search size={14} strokeWidth={1.5} />
          Search
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.65rem', color: '#8A9BB0', padding: '1px 6px', background: '#EDE9E0', borderRadius: 3 }}>⌘K</span>
        </button>

        <button onClick={onNotifications} style={{
          width: 36, height: 36, borderRadius: 6, background: '#FAF9F6',
          border: '1px solid #EDE9E0', cursor: 'pointer', color: '#4A5568',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', position: 'relative',
        }}>
          <Bell size={16} strokeWidth={1.5} />
          <span style={{ position: 'absolute', top: 6, right: 8, width: 6, height: 6, borderRadius: 999, background: '#9B2335' }} />
        </button>

        <div style={{ position: 'relative' }}>
          <button
            id="rrd-profile-pill"
            type="button"
            title={userEmail}
            aria-expanded={menuOpen}
            aria-controls="rrd-profile-menu"
            onClick={() => setMenuOpen(o => !o)}
            style={{
              width: 36, height: 36, borderRadius: 999, background: '#3A7FBD',
              color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.78rem',
            }}
          >{initials}</button>
          {menuOpen && (
            <div id="rrd-profile-menu" role="menu" style={{
              position: 'absolute', top: '100%', right: 0, marginTop: 6, width: 240,
              background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6,
              boxShadow: '0 8px 24px rgba(10,25,47,0.18)', zIndex: 30, padding: 4,
            }}>
              <div style={{ padding: '12px 14px 8px' }}>
                <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.95rem', color: '#1C2333' }}>{userName}</div>
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.74rem', color: '#4A5568', marginTop: 2 }}>{userEmail}</div>
                <span style={{
                  display: 'inline-block', marginTop: 8,
                  background: '#D9EAF5', color: '#2E6494',
                  padding: '3px 10px', borderRadius: 999, fontSize: '0.66rem', fontWeight: 600,
                  letterSpacing: '0.06em', textTransform: 'uppercase',
                }}>Owner</span>
              </div>
              <div style={{ height: 1, background: '#EDE9E0', margin: '4px 0' }} />
              <Link href="/settings" role="menuitem" style={{ display: 'block', padding: '10px 14px', color: '#1C2333', fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', textDecoration: 'none', borderRadius: 4 }}
                onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = '#F5F2EC'}
                onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = 'transparent'}
              >Account</Link>
              <Link href="/login?logout=1" role="menuitem" style={{ display: 'block', padding: '10px 14px', color: '#9B2335', fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', textDecoration: 'none', borderRadius: 4 }}
                onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = '#F5F2EC'}
                onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = 'transparent'}
              >Sign out</Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
