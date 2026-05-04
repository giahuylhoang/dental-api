// TopBar.jsx — App shell top bar with breadcrumb, ⌘K trigger, user menu

const TopBar = ({ clinicName = 'Oak Dental · Calgary', breadcrumb = ['Dashboard'], onSearch, onNotifications, onProfile }) => {
  const session = window.RRD?.getSession?.();
  const userName = session?.full_name || 'Demo Clinician';
  const userEmail = session?.email || '';
  const initials = userName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
  return (
  <header style={{
    height: 64, padding: '0 28px', background: '#fff', borderBottom: '1px solid #EDE9E0',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 10,
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
      <a href="dashboard.html" style={{ textDecoration: 'none' }}>
        <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '0.9rem', color: '#0A192F', letterSpacing: '-0.01em' }}>{clinicName}</span>
      </a>
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
        <button onClick={onProfile} title={userEmail} style={{ width: 36, height: 36, borderRadius: 999, background: '#3A7FBD', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.78rem' }}>{initials}</button>
        {/* User menu — rendered by parent when onProfile opens it; sign-out link for static browsing */}
        <a href="login.html?logout=1" id="topbar-signout-link" style={{ display: 'none' }}>Sign out</a>
      </div>
    </div>
  </header>
  );
};

Object.assign(window, { TopBar });
