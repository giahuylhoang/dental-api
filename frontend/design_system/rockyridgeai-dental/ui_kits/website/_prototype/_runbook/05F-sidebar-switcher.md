# Task 05F — Sidebar.jsx clinic switcher

Add a clinic switcher pill above the nav block in the existing `Sidebar.jsx`. The existing `NAV` array, the `Sidebar` component export, and every other behaviour must remain. This is purely additive.

## Output

Modify exactly one file: `ui_kits/website/Sidebar.jsx`.

## Allow-list

`^ui_kits/website/Sidebar\.jsx$`

## Goal

When the sidebar is expanded, a pill renders between the brand block (lines 31-39 in current file) and the nav body. Closed: shows the current clinic's `display_name` + a chevron. Open: a dropdown lists every clinic in `RRD.getAssignedClinicIds()`. Clicking a list item calls `RRD.setCurrentClinic(id)` and reloads the page so all data refreshes.

When collapsed (icon-only sidebar), the switcher hides — the user must expand the sidebar to switch clinics. This matches how the brand wordmark and footer also hide when collapsed.

## Approach

Inside the existing `Sidebar` arrow component (line 19), add `React.useState` and `React.useEffect` calls at the top of the function body to track:

```js
const [switcherOpen, setSwitcherOpen] = React.useState(false);
const [currentId, setCurrentId] = React.useState(() => window.RRD?.getCurrentClinicId?.() || null);
const assignedIds = (window.RRD?.getAssignedClinicIds?.() || []);
const allClinics = (window.CLINICS || []);
const currentClinic = allClinics.find(c => c.id === currentId) || allClinics[0] || null;
const switchableClinics = allClinics.filter(c => assignedIds.length === 0 || assignedIds.includes(c.id));
```

Then render the switcher block immediately after the brand block's closing `</div>` (after line 39), before the existing `<div style={{ flex: 1, overflowY: 'auto' }}>` nav container:

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
```

Add a body-level outside-click handler in `React.useEffect` to close the dropdown when the user clicks anywhere outside `#rrd-clinic-switcher` and `#rrd-clinic-switcher-menu`:

```js
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

## Verbatim required (must appear in the file)

- `rrd-clinic-switcher`
- `rrd-clinic-switcher-menu`
- `aria-expanded`
- `data-clinic-id`
- `setCurrentClinic`
- `getCurrentClinicId`
- `getAssignedClinicIds`
- `window.CLINICS`
- `Object.assign(window, { Sidebar })` *(existing export, must be preserved)*
- `const NAV =` *(existing nav array, must be preserved)*

## Forbidden

- Removing or renaming the `Sidebar` component or any nav item.
- Changing the existing `clinicName` / `userName` props default values in the function signature.
- Editing the existing brand block (lines 31-39) or footer block (lines 70-78).
- Removing the `Object.assign(window, { Sidebar });` export at the bottom.

## Success criteria

- File size between 4 KB and 18 KB.
- The existing 10-item `NAV` array is intact (assert: `dashboard`, `patients`, `schedule`, `plans`, `lab`, `billing`, `comms`, `crm`, `reports`, `settings` keys all present).
- The new switcher block renders only when `!collapsed`.
- Outside-click handler is wired in `React.useEffect`.
- No emoji.

## Constraints

- Match the existing inline-style approach (no new CSS classes).
- Use only kit-aligned colours (Steel `#3A7FBD`, navy `rgba(...)`, parchment `#EDE9E0`, off-white `#F5F2EC`, ink `#1C2333`, warm-white `#FAF9F6`).
- Lucide-shaped chevron and check icons (stroke 1.5 / 2, currentColor fill).
- Keep `React.useState` / `React.useEffect` namespacing — UMD doesn't expose hooks bare.
