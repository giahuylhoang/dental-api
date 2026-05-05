# Task 06B — Branding sweep

Replace every "Receptionist" / "RECEPTIONIST" / "The Receptionist" string in the prototype with the unified "Dental AI" wordmark. Targets: 8 `admin-*.html` files + `AdminSidebar.jsx`.

## Output

Modify exactly 9 files:
- `ui_kits/website/_prototype/admin-shell.html`
- `ui_kits/website/_prototype/admin-dashboard.html`
- `ui_kits/website/_prototype/admin-calls.html`
- `ui_kits/website/_prototype/admin-call-detail.html`
- `ui_kits/website/_prototype/admin-patients.html`
- `ui_kits/website/_prototype/admin-schedule.html`
- `ui_kits/website/_prototype/admin-routing.html`
- `ui_kits/website/_prototype/admin-greeting.html`
- `ui_kits/website/_prototype/AdminSidebar.jsx`

## Allow-list

`^ui_kits/website/_prototype/(admin-(shell|dashboard|calls|call-detail|patients|schedule|routing|greeting)\.html|AdminSidebar\.jsx)$`

## Replacements (exact strings)

For each of the 8 admin-*.html files:

1. **`<title>`** — replace `Rockyridge Receptionist` with `Rockyridge Dental AI`. Examples:
   - `<title>Admin Shell · Rockyridge Receptionist</title>` → `<title>Admin Shell · Rockyridge Dental AI</title>`
   - `<title>Dashboard · Rockyridge Receptionist</title>` → `<title>Dashboard · Rockyridge Dental AI</title>`
   - same pattern for Calls, Call Detail, Patients, Schedule, Routing, Greeting.

2. **Breadcrumb literals** — every JS array literal `'The Receptionist'` becomes `'Dental AI'`. Examples:
   - `breadcrumb={['The Receptionist', 'Dashboard']}` → `breadcrumb={['Dental AI', 'Dashboard']}`
   - `breadcrumb={['The Receptionist', 'Practice', 'Patients']}` → `breadcrumb={['Dental AI', 'Practice', 'Patients']}`
   - `breadcrumb={['The Receptionist', 'Configuration', 'Routing']}` etc.
   - `breadcrumb={['Reception', 'Dashboard']}` STAYS — `Reception` is a nav-group label, not the brand.

3. **Page-title <h1> / heading literals** — wherever the literal `The Receptionist` appears as user-facing copy in the body, replace with `Dental AI`. Specifically:
   - `<h1 className="page-title">The Receptionist</h1>` → `<h1 className="page-title">Dental AI</h1>` (admin-dashboard.html)
   - Body sentences like `"caption=\"Appointments booked by The Receptionist this period.\""` → `"caption=\"Appointments booked by Dental AI this period.\""`
   - `"Dashboard, Calls — owned by The Receptionist."` → `"Dashboard, Calls — owned by Dental AI."`
   - `"The first thing callers hear when The Receptionist picks up..."` → `"The first thing callers hear when Dental AI picks up..."`

For `AdminSidebar.jsx`:

4. **Wordmark span** — line ~49 `<span>RECEPTIONIST</span>` (the second line of the sidebar header) → `<span>DENTAL AI</span>`.
5. **File header comment** — `// AdminSidebar.jsx — Navy sidebar for the AI Receptionist admin prototype` → `// AdminSidebar.jsx — Navy sidebar for the Dental AI admin prototype`.

## Forbidden post-task

Across all 9 touched files, NONE of these strings may remain:
- `Receptionist`
- `RECEPTIONIST`
- `The Receptionist`

The literal `Reception` (no `ist`) is allowed — it's the nav group label.

## Verbatim required post-task (per page)

Each admin-*.html must contain `Rockyridge Dental AI` in its `<title>` after this task.
`AdminSidebar.jsx` must contain `DENTAL AI` (uppercase wordmark span).

## Success criteria

- `assert_absent` for `Receptionist` and `RECEPTIONIST` and `The Receptionist` across all 9 touched files.
- Each admin-*.html title contains `Dental AI`.
- `AdminSidebar.jsx` contains `DENTAL AI` and the comment `Navy sidebar for the Dental AI admin prototype`.
- All 9 files still parse / render (size deltas within ±10% of pre-task).

## Constraints

- Surgical string replacements only. Do not reformat surrounding markup or change unrelated content.
- Preserve existing CSS classnames, IDs, JSX structure.
