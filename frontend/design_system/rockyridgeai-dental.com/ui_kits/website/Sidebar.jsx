// Sidebar.jsx — Light-mode app shell sidebar (240px, collapsible)

// NAV items — href="dashboard.html" href="patients.html" href="schedule.html" href="plans.html" href="lab.html" href="billing.html" href="communications.html" href="crm.html" href="reports.html" href="settings.html"
const NAV = [
  { key: 'dashboard', label: 'Dashboard',      href: 'dashboard.html',      group: 'Care',       iconSvg: <><path d="M3 13h8V3H3z"/><path d="M13 21h8v-8h-8z"/><path d="M3 21h8v-6H3z"/><path d="M13 11h8V3h-8z"/></> },
  { key: 'patients',  label: 'Patients',        href: 'patients.html',       group: 'Care',       iconSvg: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></> },
  { key: 'schedule',  label: 'Schedule',        href: 'schedule.html',       group: 'Care',       iconSvg: <><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></> },
  { key: 'plans',     label: 'Treatment',       href: 'plans.html',          group: 'Care',       iconSvg: <><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/></> },
  { key: 'lab',       label: 'Lab',             href: 'lab.html',            group: 'Care',       iconSvg: <><path d="M10 2v7.31"/><path d="M14 9.3V1.99"/><path d="M8.5 2h7"/><path d="M14 9.3a6.5 6.5 0 1 1-4 0"/><path d="M5.52 16h12.96"/></> },
  { key: 'billing',   label: 'Billing',         href: 'billing.html',        group: 'Operations', iconSvg: <><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></> },
  { key: 'comms',     label: 'Communications',  href: 'communications.html', group: 'Operations', iconSvg: <><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></> },
  { key: 'crm',       label: 'CRM',             href: 'crm.html',            group: 'Operations', iconSvg: <><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></> },
  { key: 'reports',   label: 'Reports',         href: 'reports.html',        group: 'Insights',   iconSvg: <><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></> },
  { key: 'settings',  label: 'Settings',        href: 'settings.html',       group: 'System',     iconSvg: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></> },
];

const GROUP_ORDER = ['Care', 'Operations', 'Insights', 'System'];

const Sidebar = ({ active = 'dashboard', collapsed = false, clinicName = 'Oak Dental Calgary', userName = 'Dr Hau Le', onNav, onClick }) => {
  const W = collapsed ? 64 : 240;

  const groups = GROUP_ORDER.map(g => ({ label: g, items: NAV.filter(n => n.group === g) }));

  return (
    <aside style={{
      width: W, minHeight: '100vh', background: '#0A192F', color: '#FAF9F6',
      display: 'flex', flexDirection: 'column', flexShrink: 0,
      transition: 'width 250ms cubic-bezier(0.16,1,0.3,1)',
      position: 'sticky', top: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '18px 16px 22px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <img src="../../assets/RR_logo_white.svg" style={{ height: 28, flexShrink: 0 }} />
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.05 }}>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: '0.78rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>ROCKYRIDGE</span>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 400, fontSize: '0.66rem', color: 'rgba(250,249,246,0.6)', letterSpacing: 1.4, textTransform: 'uppercase' }}>DENTAL AI</span>
          </div>
        )}
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {groups.map(g => (
          <div key={g.label} style={{ padding: '16px 10px 4px' }}>
            {!collapsed && <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.62rem', fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#8A9BB0', padding: '0 10px 4px' }}>{g.label}</div>}
            {g.items.map(it => {
              const isActive = active === it.key;
              return (
                <a className="nav-item" href={`${it.href}`}
                  key={it.key}
                  aria-current={isActive ? 'page' : undefined}
                  title={collapsed ? it.label : undefined}
                  onClick={onNav ? (e) => { e.preventDefault(); onNav(it.key); } : undefined}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                    padding: collapsed ? '10px 0' : '8px 10px', justifyContent: collapsed ? 'center' : 'flex-start',
                    borderRadius: 4, background: isActive ? '#3A7FBD' : 'transparent',
                    color: isActive ? '#fff' : 'rgba(250,249,246,0.75)',
                    fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', fontWeight: isActive ? 600 : 400,
                    cursor: 'pointer', transition: 'background-color 200ms ease',
                    textDecoration: 'none', boxSizing: 'border-box',
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">{it.iconSvg}</svg>
                  {!collapsed && it.label}
                </a>
              );
            })}
          </div>
        ))}
      </div>
      <div style={{ padding: '14px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: 999, background: '#3A7FBD', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.72rem', flexShrink: 0 }}>{userName.split(' ').map(s=>s[0]).slice(0,2).join('')}</div>
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
            <span style={{ fontSize: '0.82rem' }}>{userName}</span>
            <span style={{ fontSize: '0.66rem', color: '#8A9BB0' }}>{clinicName}</span>
          </div>
        )}
      </div>
    </aside>
  );
};

Object.assign(window, { Sidebar });
