# R09 — /reports from reports.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/reports.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/reports/page.tsx` (overwrite)

## Composition
1. Page header.
2. **5-column KPI strip**: Revenue 30d, AR Outstanding, Recall conversion, New patients 30d, Avg booking lead.
3. **Multiple ChartCard panels** (port the HTML's chart components exactly — sparklines, bar charts, etc., no chart library — pure SVG).
4. **Advanced query/export panel** (bottom): render `<LockedFeature title="Advanced reports" body="Custom queries and CSV export are paused while we rebuild the export pipeline." backHref="/dashboard" />` — keep per earlier decision.

## Data wiring
- KPIs → `/api/v2/reporting/kpi` (existing) + any additional reporting endpoints.
- Charts → existing reporting endpoints; if a chart's series isn't available, port the HTML's seed shape with TODO.

## Done when
- 5-col KPI + ChartCard grid + locked advanced panel.
- `cd web && npx next build` green.
