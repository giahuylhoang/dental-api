# Task 06K — AdminSidebar.jsx config-group expansion

Add 4 new nav items to the existing `Configuration` group in `_prototype/AdminSidebar.jsx`: Services, Knowledge, AI disclosure, Voice & persona. The existing 6 nav items (dashboard, calls, patients, schedule, routing, greeting), the brand block, the clinic switcher (added in 06D), and the footer block must all remain intact.

## Output

Modify exactly one file: `ui_kits/website/_prototype/AdminSidebar.jsx`.

## Allow-list

`^ui_kits/website/_prototype/AdminSidebar\.jsx$`

## Goal

After this task, `ADMIN_NAV` has 10 entries (6 existing + 4 new). Group order: `['Reception', 'Practice', 'Configuration']`. Configuration group lists, in this order: `Routing, Greeting, Services, Knowledge, AI disclosure, Voice & persona`.

## Approach

The current `ADMIN_NAV` ends with the `greeting` item:

```js
{ key: 'greeting', label: 'Greeting', href: 'admin-greeting.html', group: 'Configuration', iconSvg: <…> },
```

Append 4 more entries in the same shape:

```js
{ key: 'services',   label: 'Services',         href: 'admin-services.html',   group: 'Configuration',
  iconSvg: <><circle cx="9" cy="9" r="2"/><path d="M13 13l5 5"/><rect x="3" y="3" width="18" height="18" rx="2"/></> },
{ key: 'knowledge',  label: 'Knowledge',        href: 'admin-knowledge.html',  group: 'Configuration',
  iconSvg: <><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></> },
{ key: 'disclosure', label: 'AI disclosure',    href: 'admin-disclosure.html', group: 'Configuration',
  iconSvg: <><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></> },
{ key: 'voice',      label: 'Voice & persona',  href: 'admin-voice.html',      group: 'Configuration',
  iconSvg: <><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></> },
```

Pick distinct Lucide-shape icons for each (the SVG paths above are reasonable approximations: book / book-open / alert-circle / microphone). Stroke width 1.5, no fill.

## Verbatim required

After this task, `_prototype/AdminSidebar.jsx` must contain:

- `'services'` *(as a key in ADMIN_NAV)*
- `'knowledge'`
- `'disclosure'`
- `'voice'`
- `admin-services.html`
- `admin-knowledge.html`
- `admin-disclosure.html`
- `admin-voice.html`
- `'Services'` *(label)*
- `'Knowledge'`
- `'AI disclosure'`
- `'Voice & persona'`
- All 6 existing nav items (`'dashboard'`, `'calls'`, `'patients'`, `'schedule'`, `'routing'`, `'greeting'`) must still be present.
- `rrd-clinic-switcher` *(from 06D, must be preserved)*
- `Object.assign(window, { AdminSidebar })`
- `DENTAL AI` *(from 06B branding sweep, must be preserved)*

## Forbidden post-task

- Removing any of the 6 existing nav items.
- Removing the clinic switcher block.
- Removing the brand block or footer block.
- Reordering the existing 6 nav items.

## Success criteria

- File size 8–28 KB.
- `ADMIN_NAV` has exactly 10 entries (6 existing + 4 new).
- All 4 new keys are in `Configuration` group.
- Group order array `['Reception', 'Practice', 'Configuration']` (or equivalent constant) unchanged.
- `assert_grep_count "key: '" 10 12` (the 10 nav entries plus minor variability for legacy comments).

## Constraints

- Append to ADMIN_NAV — don't reorder the existing entries.
- Use Lucide-shape icons (stroke-width 1.5, no fill).
- Keep the existing inline-style approach.
- No emoji.
