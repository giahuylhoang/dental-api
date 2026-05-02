# PMS Module D5 — Chrome polish: sidebar, top bar, breadcrumbs, responsive

Make `make test-pms-d5` exit 0.

## Why

The pages now use the design system, but the *shell* (sidebar, top bar) is still 2024-grade scaffold. D5 makes the user feel like they're inside one product.

## Success criteria

### `frontend/src/features/shell/AppShell.tsx` — full rewrite

- **Sidebar** (left, fixed):
  - Width 256px on `>=1024px`; collapses to 64px (icon-only) on `<1024px`. Hover the icon-only sidebar to expand temporarily.
  - Below `768px`: sidebar becomes a Radix Sheet that slides in from the left, triggered by a hamburger button in the top bar.
  - Items grouped by section heading (small uppercase label):
    - **Care** — Patients, Schedule, Plans, Lab
    - **Ops** — Billing, Communications
    - **Growth** — CRM
    - **Insights** — Dashboard
    - **System** — Settings
  - Active route highlighted with action-color background tint.
  - Each item shows a `lucide-react` icon + label.
  - Show a small ⌘K hint at the bottom.
- **Top bar** (sticky top):
  - Left: clinic display name (read from `GET /api/v2/settings/clinic`, F0). Falls back to "Dental PMS" if unavailable.
  - Center: a `<Button variant="outline" />` that says "Search ⌘K" — clicking opens the command palette (existing M5 + D3 behavior).
  - Right: bell icon (no-op for now), then a user avatar `<DropdownMenu>` with items: "Profile", "Switch clinic" (only if user has access to >1 clinic), "Sign out".
- **Breadcrumbs** above the page title — appear only when route depth >1. Format: `Section / Subsection / <PatientChip variant="breadcrumb">`. The patient slot uses the D2 chip when on a patient route.

### `frontend/src/components/ui/page-header.tsx` (new primitive)

```tsx
<PageHeader title="Patients" description="…" actions={<Button>New patient</Button>} />
```

- Replaces the bare `<h2>Page Title</h2>` patterns at the top of every page.
- Renders title (large), optional description (muted), and right-aligned actions slot.

### Apply PageHeader

Replace the page header in each of: Dashboard, PatientList, Patient360, InvoiceList, LabCaseKanban, LeadKanban, CommInbox, TreatmentPlansPage, Scheduler, SettingsPage.

### Density toggle (Settings)

- Add a "Density" select to Settings → Clinic Info card: options `compact | comfortable | spacious`.
- Persist in `localStorage` under `pms.density`.
- On load, set `<html data-density="...">` from localStorage.
- D0 tokens already accept density via CSS (`html[data-density="compact"] { --space-base: 0.875rem; }`) — D5 wires the UI side.

## Tests first (`frontend/tests/track_pms_d5/`)

1. **`sidebar-collapses-at-narrow-viewport.test.tsx`** — set `window.innerWidth = 800`; render `<AppShell>`; assert sidebar root has class `w-16` (icon-only) or `data-collapsed="true"`.

2. **`sidebar-becomes-sheet-below-768.test.tsx`** — set `window.innerWidth = 600`; assert hamburger button visible in top bar; click → sheet opens.

3. **`top-bar-shows-clinic-display-name.test.tsx`** — mock GET `/api/v2/settings/clinic` returns `{ display_name: "Demo Dental Clinic", ... }`; assert "Demo Dental Clinic" visible in top bar.

4. **`breadcrumb-on-patient360-shows-chip.test.tsx`** — render `/patients/p1` route with mocked patient; assert breadcrumb has a `data-testid="patient-chip"` element with name "Alice".

5. **`top-bar-cmdk-button-opens-palette.test.tsx`** — click the "Search ⌘K" button in top bar; assert palette opens (`role="dialog"`).

6. **`page-header-renders-title-and-actions.test.tsx`** — render `<PageHeader title="Patients" actions={<button>X</button>} />`; assert both visible.

7. **`density-toggle-updates-html-data-attr.test.tsx`** — render Settings page; change density to "compact"; assert `document.documentElement.getAttribute('data-density') === 'compact'` and `localStorage.getItem('pms.density') === 'compact'`.

## Constraints

- Don't break the existing route table in `App.tsx`.
- Sidebar items are static for now (don't make them user-configurable).
- Don't fetch any new data beyond `/api/v2/settings/clinic` (already exposed by F0).

```bash
make test-pms-d5
```
