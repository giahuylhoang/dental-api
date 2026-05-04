# R01 — /dashboard from dashboard.html

Read shared rules at `scripts/pms_rebuild/R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/dashboard.html` (818 lines)

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/dashboard/page.tsx` (overwrite — the current one is wrong)

## Composition (per HTML)
1. Page header with title + small action toolbar.
2. **4-column KPI strip** — port the exact tile labels and value formats.
3. **Today's appointments panel** with expandable cards + quick-action buttons (Confirm / Reschedule / Cancel-style).
4. **Side panel** (right column): Lab pipeline mini + Tooth chart preview.
5. **Recent patients** card list.
6. **Recent invoices** table.

## Data wiring
- KPI tiles → `/api/v2/reporting/kpi` (live).
- Today's appointments → `/api/appointments?date=today` (filter client-side if needed).
- Lab pipeline → `/api/v2/lab/cases` (live).
- Tooth chart preview → can use a recently viewed patient's tooth chart from `/api/v2/clinical/patients/{id}/tooth-chart`. If none in scope, render the HTML's seed shape with the TODO marker.
- Recent patients → `/api/patients?limit=5&sort=-created_at`.
- Recent invoices → `/api/v2/billing/invoices?limit=5`.

## Done when
- `web/app/(app)/dashboard/page.tsx` matches the HTML's structural layout (4-col KPI strip + appointments + side panel + recent patients + recent invoices).
- Page-specific styles ported into `web/app/(app)/dashboard/page.module.css`.
- `cd web && npx next build` green.
