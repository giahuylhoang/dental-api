# Task 06E — topbar profile dropdown (8 admin-*.html files)

Each `_prototype/admin-*.html` page has its own inline AdminTopBar block with a static `DC` initials avatar in the top-right. Replace that with an interactive owner pill that opens a popover. Mirror the v2 kit `TopBar.jsx` (task 05G) implementation.

## Output

Modify exactly 8 files:
- `ui_kits/website/_prototype/admin-shell.html`
- `ui_kits/website/_prototype/admin-dashboard.html`
- `ui_kits/website/_prototype/admin-calls.html`
- `ui_kits/website/_prototype/admin-call-detail.html`
- `ui_kits/website/_prototype/admin-patients.html`
- `ui_kits/website/_prototype/admin-schedule.html`
- `ui_kits/website/_prototype/admin-routing.html`
- `ui_kits/website/_prototype/admin-greeting.html`

## Allow-list

`^ui_kits/website/_prototype/admin-(shell|dashboard|calls|call-detail|patients|schedule|routing|greeting)\.html$`

## Goal

In each file, replace the static `<div class="topbar-avatar">DC</div>` with a click-toggled `id="rrd-profile-pill"` button. Below it, conditionally render `id="rrd-profile-menu"` popover containing:
- Owner full name (from `RRD.getSession().full_name`, fallback `Demo User`)
- Email (mono small)
- Role pill (steel for `Owner`, parchment otherwise)
- Separator
- `Account` link (`href="#"`, `onClick` preventDefault)
- `Sign out` link that calls `RRD.logout()` then navigates to `login.html?logout=1`

## Approach

The current topbar block in each file looks roughly like:

```jsx
<div className="topbar-right">
  <span className="topbar-pill">{`Production · ${CLINIC.slug}`}</span>
  <div className="topbar-avatar">DC</div>
</div>
```

Replace the `<div className="topbar-avatar">DC</div>` block with an inline component-style React block. Because each admin page mounts its own `<AdminTopBar />` component, the simplest path is to add a small `OwnerPill` inline component near the top of each page's `<script type="text/babel">` block, then render `<OwnerPill />` in place of the static avatar.

Add this inline component just below the existing helper functions (or right before the page Body component definition) in each admin-*.html:

```jsx
const OwnerPill = () => {
  const session = (window.RRD && window.RRD.getSession && window.RRD.getSession()) || {};
  const userName = session.full_name || 'Demo User';
  const userEmail = session.email || '';
  const role = session.role || 'Demo';
  const initials = userName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();

  const [menuOpen, setMenuOpen] = React.useState(false);

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
    window.location.href = 'login.html?logout=1';
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        id="rrd-profile-pill"
        type="button"
        title={userEmail}
        aria-expanded={menuOpen}
        aria-controls="rrd-profile-menu"
        onClick={() => setMenuOpen(o => !o)}
        style={{ width: 32, height: 32, borderRadius: 999, background: '#3A7FBD', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.72rem' }}
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
          <a role="menuitem" href="login.html?logout=1"
             onClick={(e) => { e.preventDefault(); handleSignOut(); }}
             style={{ display: 'block', padding: '10px 14px', color: '#9B2335', fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', textDecoration: 'none', borderRadius: 4 }}
             onMouseEnter={e => e.currentTarget.style.background = '#F5F2EC'}
             onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >Sign out</a>
        </div>
      )}
    </div>
  );
};
```

Then replace the existing `<div className="topbar-avatar">DC</div>` (or equivalent static initials div) with `<OwnerPill />`.

## Verbatim required (per file)

- `rrd-profile-pill`
- `rrd-profile-menu`
- `role="menu"`
- `role="menuitem"`
- `Account`
- `Sign out`
- `RRD.logout`
- `login.html?logout=1`
- `OwnerPill`

## Forbidden post-task

- The literal string `>DC<` (the hard-coded initials) must NOT appear in any of the 8 files. Initials must come from `userName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()`.
- Removing the existing `topbar-pill` env badge.
- Changing the topbar height or layout flow.

## Success criteria

- Each of the 8 files has exactly ONE `id="rrd-profile-pill"` and exactly ONE `id="rrd-profile-menu"` (assert_grep_count = 1, 1).
- `assert_absent` for the literal `>DC<` across all 8 files.
- All 8 files still render (size deltas reasonable).

## Constraints

- Use only kit-aligned colours (steel `#3A7FBD`, navy/parchment grays).
- Match the existing inline-style approach.
- No new CSS classes.
- Each file gets its own copy of the OwnerPill component (the prototype is self-contained — no shared bundle).
