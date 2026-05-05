// TopBar.jsx — App shell top bar with breadcrumb, ⌘K trigger, profile popover

const TopBar = ({ clinicName = 'Oak Dental · Calgary', breadcrumb = ['Dashboard'], homeHref = 'dashboard.html', mode, onSearch, onNotifications, onProfile }) => {
  const session = window.RRD?.getSession?.();
  const userName = session?.full_name || 'Demo Clinician';
  const userEmail = session?.email || '';
  const initials = userName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();

  const [menuOpen, setMenuOpen] = React.useState(false);
  const role = session?.role || 'Demo';

  React.useEffect(() => {
    if (!menuOpen) return undefined;
    const handler = (e) => {
      const pill = document.getElementById('rrd-profile-pill');
      const menu = document.getElementById('rrd-profile-menu');
      if (pill && pill.contains(e.target)) return;
      if (menu && menu.contains(e.target)) return;
      setMenuOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  const handleSignOut = () => {
    try { if (window.RRD && window.RRD.logout) window.RRD.logout(); } catch (_) { /* no-op */ }
    window.location.href = '/ui_kits/website/login.html?logout=1';
  };

  return (
  <header style={{
    height: 64, padding: '0 28px', background: '#fff', borderBottom: '1px solid #EDE9E0',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 10,
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
      <a href={homeHref} style={{ textDecoration: 'none' }}>
        <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '0.9rem', color: '#0A192F', letterSpacing: '-0.01em' }}>{clinicName}</span>
      </a>
      {mode && (
        <span
          title="AI Receptionist control plane — distinct from the PMS"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: '#3A7FBD', color: '#fff',
            fontFamily: "'Inter', sans-serif", fontWeight: 700,
            fontSize: '0.6rem', letterSpacing: '0.14em', textTransform: 'uppercase',
            padding: '4px 10px', borderRadius: 999, lineHeight: 1,
          }}>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
          {mode}
        </span>
      )}
      <span style={{ width: 1, height: 18, background: '#EDE9E0' }} />
      <nav style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: '0.82rem', color: '#4A5568' }}>
        {breadcrumb.map((b, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span style={{ color: '#C8CCCC' }}>›</span>}
            <span style={{ color: i === breadcrumb.length - 1 ? '#1C2333' : '#4A5568', fontWeight: i === breadcrumb.length - 1 ? 500 : 400 }}>{b}</span>
          </React.Fragment>
        ))}
      </nav>
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <button onClick={onSearch} style={{
        display: 'inline-flex', alignItems: 'center', gap: 8,
        background: '#FAF9F6', border: '1px solid #EDE9E0', borderRadius: 6,
        padding: '7px 12px', cursor: 'pointer', color: '#4A5568', fontFamily: "'Inter', sans-serif", fontSize: '0.82rem',
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        Search
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.65rem', color: '#8A9BB0', padding: '1px 6px', background: '#EDE9E0', borderRadius: 3 }}>⌘K</span>
      </button>
      <button onClick={onNotifications} style={{ width: 36, height: 36, borderRadius: 6, background: '#FAF9F6', border: '1px solid #EDE9E0', cursor: 'pointer', color: '#4A5568', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
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
          style={{ width: 36, height: 36, borderRadius: 999, background: '#3A7FBD', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.78rem' }}
        >{initials}</button>
        {menuOpen && (
          <div
            id="rrd-profile-menu"
            role="menu"
            style={{
              position: 'absolute', top: '100%', right: 0, marginTop: 6, width: 240,
              background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6,
              boxShadow: '0 8px 24px rgba(10,25,47,0.18)', zIndex: 30, padding: 4,
            }}>
            <div style={{ padding: '12px 14px 8px' }}>
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.95rem', color: '#1C2333' }}>{userName}</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.74rem', color: '#4A5568', marginTop: 2 }}>{userEmail}</div>
              <span
                style={{
                  display: 'inline-block', marginTop: 8,
                  background: role === 'Owner' ? '#D9EAF5' : '#F5F2EC',
                  color:      role === 'Owner' ? '#2E6494' : '#4A5568',
                  padding: '3px 10px', borderRadius: 999, fontSize: '0.66rem', fontWeight: 600,
                  letterSpacing: '0.06em', textTransform: 'uppercase',
                }}
              >{role}</span>
            </div>
            <div style={{ height: 1, background: '#EDE9E0', margin: '4px 0' }} />
            <a role="menuitem" href="#"
               onClick={(e) => e.preventDefault()}
               style={{ display: 'block', padding: '10px 14px', color: '#1C2333', fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', textDecoration: 'none', borderRadius: 4 }}
               onMouseEnter={e => e.currentTarget.style.background = '#F5F2EC'}
               onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >Account</a>
            <a role="menuitem" href="/ui_kits/website/login.html?logout=1"
               onClick={(e) => { e.preventDefault(); handleSignOut(); }}
               style={{ display: 'block', padding: '10px 14px', color: '#9B2335', fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', textDecoration: 'none', borderRadius: 4 }}
               onMouseEnter={e => e.currentTarget.style.background = '#F5F2EC'}
               onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >Sign out</a>
          </div>
        )}
      </div>
    </div>
  </header>
  );
};

Object.assign(window, { TopBar });
