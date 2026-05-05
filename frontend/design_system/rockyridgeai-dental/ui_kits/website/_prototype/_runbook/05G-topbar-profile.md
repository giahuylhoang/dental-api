# Task 05G — TopBar.jsx profile dropdown

Replace the existing avatar pill's `onClick={onProfile}` with an internal popover that shows the signed-in user's name, email, role pill, an "Account" link, and a "Sign out" link. The existing `TopBar` export and breadcrumb / search / notifications behaviour must remain untouched.

## Output

Modify exactly one file: `ui_kits/website/TopBar.jsx`.

## Allow-list

`^ui_kits/website/TopBar\.jsx$`

## Goal

Click the avatar → a 240px popover anchors below it. Contents (top to bottom): full name, email (mono small), role pill (steel for Owner / parchment for others), separator, "Account" link (`href="#"`, no-op), "Sign out" link that calls `RRD.logout()` then navigates to `login.html?logout=1`.

## Approach

The current file is 51 lines. Wrap the function body so it owns React state for menu open/close. Hooks via `React.useState` / `React.useEffect`.

Add at the top of the `TopBar` arrow function body:

```js
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
  try { window.RRD?.logout?.(); } catch (_) { /* no-op */ }
  window.location.href = 'login.html?logout=1';
};
```

Replace the existing avatar `<button>` (current line 42) with one that has `id="rrd-profile-pill"` and `onClick={() => setMenuOpen(o => !o)}`. Below it, render the popover when `menuOpen`:

```jsx
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
      <a role="menuitem" href="login.html?logout=1"
         onClick={(e) => { e.preventDefault(); handleSignOut(); }}
         style={{ display: 'block', padding: '10px 14px', color: '#9B2335', fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', textDecoration: 'none', borderRadius: 4 }}
         onMouseEnter={e => e.currentTarget.style.background = '#F5F2EC'}
         onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >Sign out</a>
    </div>
  )}
</div>
```

You can remove the existing hidden `<a href="login.html?logout=1" id="topbar-signout-link">` at line 44 since the new menu replaces it.

## Verbatim required

- `rrd-profile-pill`
- `rrd-profile-menu`
- `role="menu"`
- `role="menuitem"`
- `Account`
- `Sign out`
- `RRD.logout` *(reference inside handleSignOut)*
- `login.html?logout=1`
- `Object.assign(window, { TopBar })` *(existing export, must be preserved)*
- `breadcrumb` *(existing prop, must be preserved)*
- `getSession` *(existing usage, must be preserved)*

## Forbidden

- Removing the `breadcrumb`, `clinicName`, `onSearch`, `onNotifications`, `onProfile` props from the function signature.
- Removing the search button or notifications button.
- Changing the height (`64`) or padding (`'0 28px'`) of the header.
- Renaming the `TopBar` component.

## Success criteria

- File size between 2 KB and 10 KB.
- `id="rrd-profile-pill"` and `id="rrd-profile-menu"` both present.
- The existing `clinicName` rendering at the breadcrumb start (lines 14-17 in current file) remains.
- `Object.assign(window, { TopBar });` at the end remains.

## Constraints

- Match the existing inline-style approach.
- Use kit colours: steel `#3A7FBD`, navy `rgba(10,25,47,...)`, parchment `#EDE9E0`, off-white `#F5F2EC`, ink `#1C2333`, slate `#4A5568`, error `#9B2335` (for sign-out link).
- Role pill colours: Owner = `#D9EAF5` bg + `#2E6494` text; everyone else = `#F5F2EC` bg + `#4A5568` text.
- No emoji. No animations beyond CSS transitions.
