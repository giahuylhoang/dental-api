# Task 06D — AdminSidebar.jsx clinic switcher

Add a clinic switcher pill above the nav body in `_prototype/AdminSidebar.jsx`. Mirror the v2 kit Sidebar (task 05F) implementation. The existing `ADMIN_NAV` array, `Object.assign(window, { AdminSidebar })` export, and every other behaviour must remain untouched.

## Output

Modify exactly one file: `ui_kits/website/_prototype/AdminSidebar.jsx`.

## Allow-list

`^ui_kits/website/_prototype/AdminSidebar\.jsx$`

## Goal

Between the brand block (which renders `ROCKYRIDGE / DENTAL AI` after task 06B) and the nav body, insert a clinic switcher pill. When `!collapsed`, render the pill. Click toggles a dropdown listing every clinic in `RRD.getAssignedClinicIds()`. Clicking an item calls `RRD.setCurrentClinic(id)` and reloads the page.

## Approach

Add `React.useState` and `React.useEffect` calls at the top of the `AdminSidebar` component's function body:

```js
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
```

Render the switcher block immediately after the brand block (which ends with the `DENTAL AI` span div) and before the existing nav container:

```jsx
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
                  if (window.RRD && window.RRD.setCurrentClinic && window.RRD.setCurrentClinic(c.id)) {
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
```

## Verbatim required (must appear in the file)

- `rrd-clinic-switcher`
- `rrd-clinic-switcher-menu`
- `aria-expanded`
- `data-clinic-id`
- `setCurrentClinic`
- `getCurrentClinicId`
- `getAssignedClinicIds`
- `window.CLINICS`
- `Object.assign(window, { AdminSidebar })` *(existing export, must be preserved)*
- `const ADMIN_NAV =` *(existing nav array, must be preserved)*
- `DENTAL AI` *(from 06B branding sweep)*

## Forbidden post-task

- `RECEPTIONIST`
- `Receptionist`
- Removing or renaming the `AdminSidebar` component or any nav item.
- Editing the existing brand block content beyond what 06B already changed.
- Editing the footer block (the existing user-initials block at the bottom).

## Success criteria

- File size 6–22 KB.
- Existing 6-item `ADMIN_NAV` array intact (assert keys: `dashboard`, `calls`, `patients`, `schedule`, `routing`, `greeting`).
- `id="rrd-clinic-switcher"` present.
- Outside-click handler wired in `React.useEffect`.
- `Object.assign(window, { AdminSidebar });` at the bottom remains.
- No emoji.

## Constraints

- Match the existing inline-style approach (no new CSS classes).
- Keep `React.useState` / `React.useEffect` namespacing — UMD doesn't expose hooks bare.
- Lucide-shaped chevron + check icons, stroke 1.5 / 2, `currentColor` fill.
