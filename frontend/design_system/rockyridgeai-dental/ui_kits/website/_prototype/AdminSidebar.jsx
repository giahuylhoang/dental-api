// AdminSidebar.jsx — Navy sidebar for the Dental AI admin prototype.
// Mirrors Sidebar.jsx conventions (240px expanded / 64px collapsed, navy bg,
// Lucide stroke-1.5 icons) but the nav set is scoped to the AI admin app:
// Dashboard, Calls, Patients, Schedule, Routing, Greeting.

const ADMIN_NAV = [
  { key: 'dashboard', label: 'Dashboard', href: 'admin-dashboard.html', group: 'Reception',
    iconSvg: <><path d="M3 13h8V3H3z"/><path d="M13 21h8v-8h-8z"/><path d="M3 21h8v-6H3z"/><path d="M13 11h8V3h-8z"/></> },
  { key: 'calls',     label: 'Calls',     href: 'admin-calls.html', group: 'Reception',
    iconSvg: <><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></> },
  { key: 'patients',  label: 'Patients',  href: 'admin-patients.html', group: 'Practice',
    iconSvg: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></> },
  { key: 'schedule',  label: 'Schedule',  href: 'admin-schedule.html', group: 'Practice',
    iconSvg: <><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></> },
  { key: 'routing',   label: 'Routing',   href: 'admin-routing.html', group: 'Configuration',
    iconSvg: <><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></> },
  { key: 'greeting',  label: 'Greeting',  href: 'admin-greeting.html', group: 'Configuration',
    iconSvg: <><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></> },
  { key: 'services',   label: 'Services',         href: 'admin-services.html',   group: 'Configuration',
    iconSvg: <><circle cx="9" cy="9" r="2"/><path d="M13 13l5 5"/><rect x="3" y="3" width="18" height="18" rx="2"/></> },
  { key: 'knowledge',  label: 'Knowledge',        href: 'admin-knowledge.html',  group: 'Configuration',
    iconSvg: <><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></> },
  { key: 'disclosure', label: 'AI disclosure',    href: 'admin-disclosure.html', group: 'Configuration',
    iconSvg: <><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></> },
  { key: 'voice',      label: 'Voice & persona',  href: 'admin-voice.html',      group: 'Configuration',
    iconSvg: <><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></> },
];

const ADMIN_GROUP_ORDER = ['Reception', 'Practice', 'Configuration'];

const AdminSidebar = ({
  active = 'dashboard',
  collapsed = false,
  clinicName = 'Northeast Denture Clinic',
  clinicSlug = 'northeast-denture-clinic',
  userName = 'Demo Clinician',
  onNav,
}) => {
  const W = collapsed ? 64 : 240;
  const groups = ADMIN_GROUP_ORDER.map(g => ({
    label: g,
    items: ADMIN_NAV.filter(n => n.group === g),
  }));

  const [switcherOpen, setSwitcherOpen] = React.useState(false);
  const [currentId, setCurrentId] = React.useState(() =>
    (window.RRD && window.RRD.getCurrentClinicId && window.RRD.getCurrentClinicId()) || null);
  const assignedIds = (window.RRD && window.RRD.getAssignedClinicIds && window.RRD.getAssignedClinicIds()) || [];
  const allClinics = (window.CLINICS || []);
  const currentClinic = allClinics.find(c => c.id === currentId) || allClinics[0] || null;
  const switchableClinics = allClinics.filter(c => assignedIds.length === 0 || assignedIds.includes(c.id));

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
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '18px 16px 14px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <img src="../../../assets/RR_logo_white.svg" alt="" style={{ height: 28, flexShrink: 0, marginTop: 2 }} />
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.05, gap: 6 }}>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: '0.78rem', letterSpacing: '0.08em', textTransform: 'uppercase' }}>ROCKYRIDGE</span>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 400, fontSize: '0.62rem', color: 'rgba(250,249,246,0.6)', letterSpacing: 1.4, textTransform: 'uppercase' }}>DENTAL AI</span>
            {/* Mode signature — anchors the fact this is the AI Receptionist control plane, not the PMS */}
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 5, marginTop: 4,
              fontFamily: "'Inter', sans-serif", fontWeight: 700,
              fontSize: '0.54rem', letterSpacing: '0.16em', textTransform: 'uppercase',
              color: '#6BAED6',
            }}>
              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              </svg>
              AI Receptionist
            </span>
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
                        if (window.RRD && window.RRD.setCurrentClinic) {
                          window.RRD.setCurrentClinic(c.id);
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
            {!collapsed && (
              <div style={{
                fontFamily: "'Inter', sans-serif", fontSize: '0.62rem', fontWeight: 600,
                letterSpacing: '0.14em', textTransform: 'uppercase', color: '#8A9BB0',
                padding: '0 10px 4px',
              }}>{g.label}</div>
            )}
            {g.items.map(it => {
              const isActive = active === it.key;
              return (
                <a className="nav-item" href={it.href}
                  key={it.key}
                  aria-current={isActive ? 'page' : undefined}
                  title={collapsed ? it.label : undefined}
                  onClick={onNav ? (e) => { e.preventDefault(); onNav(it.key); } : undefined}
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
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">{it.iconSvg}</svg>
                  {!collapsed && it.label}
                </a>
              );
            })}
          </div>
        ))}
      </div>

      <div style={{ padding: '14px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 999, background: '#3A7FBD',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 600, fontSize: '0.72rem', flexShrink: 0,
        }}>{userName.split(' ').map(s => s[0]).slice(0, 2).join('')}</div>
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2, minWidth: 0 }}>
            <span style={{ fontSize: '0.82rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{clinicName}</span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.62rem', color: '#8A9BB0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{clinicSlug}</span>
          </div>
        )}
      </div>
    </aside>
  );
};

Object.assign(window, { AdminSidebar });
