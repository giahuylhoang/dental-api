# Rockyridge Dental AI — Website UI Kit

Standalone reference compositions, executable in the browser via Babel-standalone (no build step). Mirrors the layout of `rockyridgeai.com/ui_kits/website/` for muscle memory.

## Prototypes
| File | Theme | Purpose |
|------|-------|---------|
| `index.html`     | Light + dark sections | Marketing landing — Nav · Hero · Pillars · Philosophy · CTA · Footer. |
| `dashboard.html` | **Light** | Full PMS shell — Sidebar · TopBar · KPIs · Today's appointments · Lab pipeline · Recent patients table · Tooth chart. |
| `login.html`     | **Dark** | Split-layout login portal — cycling display word + animated node graph + floating LoginCard. |

## JSX components
PascalCase, single-window export idiom (`Object.assign(window, { Foo })`). Designed to be loaded via `<script type="text/babel" src="Foo.jsx"></script>`.

| File | Composes |
|------|----------|
| `Nav.jsx`             | Marketing top nav, sweep CTA |
| `Hero.jsx`            | Marketing hero with animated node graph + cycling word |
| `Pillars.jsx`         | Three-pillar section (Schedule · Chart · Lab) |
| `Philosophy.jsx`      | Brand-voice block on dark bg |
| `CTA.jsx`             | "Schedule a demo" form section + Footer |
| `Sidebar.jsx`         | App-shell sidebar (Care / Operations / Insights / System), collapsible |
| `TopBar.jsx`          | App-shell top bar (clinic name, breadcrumb, ⌘K, user menu) |
| `KpiTile.jsx`         | Dashboard KPI tile |
| `PatientCard.jsx`     | Patient summary row |
| `AppointmentCard.jsx` | Today's appointment row |
| `LabPipeline.jsx`     | Lab queue Kanban (3 columns) |
| `ToothChartTile.jsx`  | Compact 32-tooth chart, FDI numbering |
| `LoginCard.jsx`       | Dark-theme login form (used on login.html) |
| `EmptyState.jsx`      | Standard empty state |

## Design width
1280px desktop. Components keep working at 1024px; below 768px the sidebar collapses to icon-only.

## Tokens & utilities
Every component inherits from `../../colors_and_type.css`:
- Sweep button utilities — `.btn .btn-primary`, `.btn .btn-navy`, `.btn .btn-ghost`, `.btn .btn-white`, `.btn .btn-destructive`, `.btn .btn-solid`, sizes `btn-sm` / `btn-md` / `btn-lg`.
- Wordmark lockup — `.rr-wordmark`, `.rr-wordmark__brand` (Montserrat 800 caps), `.rr-wordmark__sub` (Montserrat 400 wide tracking).
- Nav-link underline-sweep — `.nav-link`, `.nav-link.active`.
