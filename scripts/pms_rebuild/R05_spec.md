# R05 — /lab from lab.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/lab.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/lab/page.tsx` (overwrite)

## Composition
1. Page header with title.
2. **4-column KPI strip**: In flight, Returned/ready, Overdue, On-time rate.
3. **LabPipeline** widget (horizontal stage flow) — uses `LabPipeline.jsx` from `ui_kits/website/`.
4. Filtered cases table: Case ID (mono) / Patient / Item / Vendor / Sent / ETA / Status.
5. **Vendor cards panel** on the right: per-vendor stats card (avg turnaround, on-time %, open cases).

## Data wiring
- KPIs → derive from `/api/v2/lab/cases` aggregation, or port seed if no endpoint.
- Cases table → `/api/v2/lab/cases`.
- Vendors → `/api/v2/lab/vendors` if it exists; else seed.

## Done when
- KPI strip + pipeline + cases table + vendor panel all present.
- `cd web && npx next build` green.
