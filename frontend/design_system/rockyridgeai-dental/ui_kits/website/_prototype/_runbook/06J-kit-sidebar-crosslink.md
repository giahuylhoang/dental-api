# Task 06J — kit Sidebar.jsx cross-link to AI Receptionist

Add ONE new nav item to the kit's `ui_kits/website/Sidebar.jsx`. Click clears the session and routes the user to login.html with a `next=` param so re-login lands them in the prototype admin.

## Output

Modify exactly one file: `ui_kits/website/Sidebar.jsx`.

## Allow-list

`^ui_kits/website/Sidebar\.jsx$`

## Goal

The kit's left sidebar gets a new nav item under the `Operations` group: `AI Receptionist` with a `NEW` pill badge. Clicking calls `RRD.logout()` and navigates to `login.html?next=_prototype/admin-dashboard.html&relogin=1`. The login flow's existing `?next=` handling lands the user at `_prototype/admin-dashboard.html` after re-auth.

## Approach

The current kit `Sidebar.jsx` defines `NAV` (10 items: dashboard, patients, schedule, plans, lab, billing, comms, crm, reports, settings). Each entry has shape:

```js
{ key, label, href, group, iconSvg }
```

Add ONE more entry just before `settings` so it appears in the `Operations` group above System:

```js
{ key: 'ai-receptionist',
  label: 'AI Receptionist',
  href: 'login.html?next=_prototype/admin-dashboard.html&relogin=1',
  group: 'Operations',
  isNew: true,
  iconSvg: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1z"/></>
}
```

Note the new `isNew: true` flag. Render rule: when `isNew` is truthy, append a small `NEW` pill badge next to the label. Pill style:

```js
<span style={{
  marginLeft: 6, fontSize: '0.55rem', fontWeight: 700,
  letterSpacing: '0.08em', padding: '2px 6px', borderRadius: 999,
  background: '#3A7FBD', color: '#fff', textTransform: 'uppercase',
}}>NEW</span>
```

In the existing nav `<a>` rendering loop, intercept clicks for `it.key === 'ai-receptionist'`:

```js
onClick={(e) => {
  if (it.key === 'ai-receptionist') {
    e.preventDefault();
    try { if (window.RRD && window.RRD.logout) window.RRD.logout(); } catch (_) {}
    window.location.href = it.href;
    return;
  }
  if (onNav) { e.preventDefault(); onNav(it.key); }
}}
```

(Preserve the existing `onNav` short-circuit branch for all other keys.)

## Verbatim required

- `ai-receptionist`
- `AI Receptionist`
- `_prototype/admin-dashboard.html`
- `relogin=1`
- `isNew`
- `NEW`
- `RRD.logout`
- `login.html?next=`
- `Object.assign(window, { Sidebar })` *(existing export, must be preserved)*
- `const NAV =` *(existing nav array, must be preserved)*
- All 10 existing nav `key:` strings: `dashboard`, `patients`, `schedule`, `plans`, `lab`, `billing`, `comms`, `crm`, `reports`, `settings`

## Forbidden post-task

- Removing or renaming any existing nav item.
- Changing `Sidebar` component name or props.
- Changing the existing `clinicName` / `userName` defaults.
- Editing the brand block, footer block, or clinic switcher (added in v2 by 05F — still present and unchanged).

## Success criteria

- File size 6–22 KB (the new nav item + click handler add ~20 lines).
- All 11 `key:` strings present in NAV array (10 original + `ai-receptionist`).
- The NEW pill rendering JSX is present.
- The click handler that calls `RRD.logout()` for the AI Receptionist key is present.
- `Object.assign(window, { Sidebar });` at the bottom remains.

## Constraints

- One nav item only — don't add anything else.
- Keep the existing inline-style approach.
- Use kit colors (steel `#3A7FBD` for the NEW pill).
- The `iconSvg` should be a minimal Lucide-shape icon (a star, a sparkle, a microphone, or a settings/cog — pick one that signals "voice AI"). Use stroke-width 1.5, no fill.
