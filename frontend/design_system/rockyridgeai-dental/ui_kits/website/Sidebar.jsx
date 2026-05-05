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
  { key: 'ai-receptionist', label: 'AI Receptionist', href: 'login.html?next=_prototype/admin-dashboard.html&relogin=1', group: 'Operations', isNew: true, iconSvg: <><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></> },
  { key: 'settings',  label: 'Settings',        href: 'settings.html',       group: 'System',     iconSvg: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></> },
];

const GROUP_ORDER = ['Care', 'Operations', 'Insights', 'System'];

const Sidebar = ({ active = 'dashboard', collapsed = false, clinicName = 'Oak Dental Calgary', userName = 'Dr Hau Le', onNav, onClick }) => {
  const W = collapsed ? 64 : 240;

  const groups = GROUP_ORDER.map(g => ({ label: g, items: NAV.filter(n => n.group === g) }));

  // Clinic switcher state
  const [switcherOpen, setSwitcherOpen] = React.useState(false);
  const [currentId, setCurrentId] = React.useState(() => window.RRD?.getCurrentClinicId?.() || null);
  const assignedIds = (window.RRD?.getAssignedClinicIds?.() || []);
  const allClinics = (window.CLINICS || []);
  const currentClinic = allClinics.find(c => c.id === currentId) || allClinics[0] || null;
  const switchableClinics = allClinics.filter(c => assignedIds.length === 0 || assignedIds.includes(c.id));

  // Outside-click handler
  React.useEffect(() => {
    if (!switcherOpen) return undefined;
    const handler = (e) => {
      const pill = document.getElementById('rrd-clinic-switcher');
      const menu = document.getElementById('rrd-clinic-switcher-menu');
      if (pill && pill.contains(e.target)) return;
      if (menu && menu.contains(e.target)) return;
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
        <img src="../../assets/RR_logo_white.svg" style={{ height: 28, flexShrink: 0 }} />
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.05 }}>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: '0.78rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>ROCKYRIDGE</span>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 400, fontSize: '0.66rem', color: 'rgba(250,249,246,0.6)', letterSpacing: 1.4, textTransform: 'uppercase' }}>DENTAL AI</span>
          </div>
        )}
      </div>
      {!collapsed && switchableClinics.length > 0 && (
        <div style={{ padding: '12px 12px 4px', position: 'relative' }}>
          <button
            id="rrd-clinic-switcher"
            type="button"
            aria-expanded={switcherOpen}
            aria-controls="rrd-clinic-switcher-menu"
            onClick={() => setSwitcherOpen(o => !o)}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: 'rgba(58,127,189,0.08)', border: '1px solid rgba(255,255,255,0.10)',
              borderRadius: 6, padding: '10px 12px', color: '#FAF9F6',
              fontFamily: "'Inter', sans-serif", fontSize: '0.82rem', fontWeight: 500,
              cursor: 'pointer', textAlign: 'left',
            }}
          >
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {currentClinic ? currentClinic.display_name : 'Select clinic'}
            </span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                 style={{ transform: switcherOpen ? 'rotate(180deg)' : 'none', transition: 'transform 200ms' }}>
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          {switcherOpen && (
            <ul id="rrd-clinic-switcher-menu" role="menu"
                style={{
                  position: 'absolute', top: '100%', left: 12, right: 12, marginTop: 4,
                  background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6,
                  boxShadow: '0 8px 24px rgba(10,25,47,0.18)',
                  listStyle: 'none', margin: 0, padding: 4, zIndex: 20,
                }}>
              {switchableClinics.map(c => {
                const isCurrent = c.id === currentId;
                return (
                  <li key={c.id} role="menuitem" data-clinic-id={c.id}
                      onClick={() => {
                        if (window.RRD?.setCurrentClinic?.(c.id)) {
                          window.location.reload();
                        }
                      }}
                      style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '8px 10px', borderRadius: 4, cursor: 'pointer',
                        fontFamily: "'Inter', sans-serif", fontSize: '0.85rem',
                        color: isCurrent ? '#3A7FBD' : '#1C2333',
                        fontWeight: isCurrent ? 600 : 400,
                        background: 'transparent',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = '#F5F2EC'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <span>{c.display_name}</span>
                    {isCurrent && (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                           strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
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
                  onClick={(e) => {
                    if (it.key === 'ai-receptionist') {
                      e.preventDefault();
                      try { if (window.RRD && window.RRD.logout) window.RRD.logout(); } catch (_) {}
                      window.location.href = it.href;
                      return;
                    }
                    if (onNav) { e.preventDefault(); onNav(it.key); }
                  }}
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
                  {!collapsed && <>{it.label}{it.isNew && <span style={{ marginLeft: 6, fontSize: '0.55rem', fontWeight: 700, letterSpacing: '0.08em', padding: '2px 6px', borderRadius: 999, background: '#3A7FBD', color: '#fff', textTransform: 'uppercase' }}>NEW</span>}</>}
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
