# Task 06F — admin-services.html (NEW)

Build the AI-bookable service catalogue page for the dark prototype admin. Mirrors the kit's `AI Services` settings tab but as a dedicated page in the prototype.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-services.html`.

## Allow-list

`^ui_kits/website/_prototype/admin-services\.html$`

## Goal

A clinic owner sees every service from `window.SERVICES` (8 rows) as a kit-style table with an "AI Bookable" toggle column. The toggle reflects/edits `window.AI_CONFIG[currentClinicId].ai_bookable_service_ids`. A "Save service catalogue" button at the bottom.

## Scaffolding

Mirror the structure of `_prototype/admin-routing.html` (already in the codebase) for the page shell:
- DOCTYPE, head with React/ReactDOM/Babel UMD scripts
- `<link rel="stylesheet" href="../../../colors_and_type.css">`
- Google Fonts preconnect + Montserrat/Inter/JetBrains Mono link
- Page-specific `<style>` block at top
- Body with `<div id="root"></div>`
- Vanilla scripts loaded BEFORE babel scripts:
  - `<script src="../../../data/clinics.js"></script>`
  - `<script src="../../../data/admin_mock.js"></script>`
  - `<script src="../../../data/ai_config.js"></script>`
  - `<script src="../../../data/services.js"></script>`
  - `<script src="../../../lib/query.js"></script>`
  - `<script src="../../../lib/auth.js"></script>`
  - `<script src="../../../lib/console-tap.js"></script>`
- Babel scripts:
  - `<script type="text/babel" src="AdminSidebar.jsx"></script>`
- Inline `<script type="text/babel">` with the page body component

## Body component

Must mount `<AdminSidebar active="services" clinicName={CLINIC.name} clinicSlug={CLINIC.slug} />` and an inline AdminTopBar with the OwnerPill (matching 06E pattern).

Below the topbar, render:

1. **Page header** — title `<h1 className="page-title">The Service catalogue</h1>` and subtitle `Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only.`

2. **Service table** — kit-style:
   ```
   ┌─────────────┬──────────────────┬──────────┬─────────────┬────────────────────┐
   │ Service ID  │ Name             │ Duration │ Base price  │ AI Bookable        │
   ├─────────────┼──────────────────┼──────────┼─────────────┼────────────────────┤
   │ SVC-001     │ Recall Exam      │ 30 min   │ $80.00      │ [✓] AI Bookable    │
   │ SVC-002     │ Scaling — Full…  │ 60 min   │ $220.00     │ [ ] Front-desk only│
   │ ...         │                  │          │             │                    │
   └─────────────┴──────────────────┴──────────┴─────────────┴────────────────────┘
   ```
   For each service in `window.SERVICES`, the toggle is checked iff `service.id in AI_CONFIG[currentClinicId].ai_bookable_service_ids`.

3. **Save bar** at the bottom: navy `Save service catalogue` button (visual only — no real persistence in mock).

## Verbatim required

- `Services` (in `<title>` and breadcrumb)
- `The Service catalogue`
- `Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only.`
- `Service ID`
- `Duration`
- `Base price`
- `AI Bookable`
- `Front-desk only`
- `Save service catalogue`
- `SVC-001`
- `<AdminSidebar`
- `active="services"`
- `Rockyridge Dental AI` (in `<title>`)
- `id="rrd-profile-pill"` (from OwnerPill)

## Title

`<title>Services · Rockyridge Dental AI</title>`

## Breadcrumb

`['Dental AI', 'Configuration', 'Services']`

## Success criteria

- File size 9–32 KB.
- Verbatim strings all present.
- Loads `data/services.js` and `data/ai_config.js`.
- Mounts `AdminSidebar` with `active="services"`.
- Has `id="rrd-profile-pill"` exactly once.

## Constraints

- Use existing `_prototype` design tokens (navy `#0A192F` sidebar, warm-white `#FAF9F6` body, kit table styling via `colors_and_type.css`).
- No emoji.
- Clinical voice: definite article on system names ("The Service catalogue").
