# R02 — /patients from patients.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/patients.html` (513 lines)

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/patients/page.tsx` (overwrite)

## Composition
1. Page header with **"Import CSV"** + **"+ New patient"** action buttons (right-aligned).
2. **4-column KPI strip**: Total active, New this month, Recall due, Plans pending.
3. Toolbar row: search input (left) + filter chips (All / Active / Recall due / Plan / Inactive) + sort dropdown (right).
4. Clickable DataTable with rows per HTML's column set; row click navigates to `/patients/{id}`.

## Data wiring
- KPI tiles → if there's no aggregation endpoint, derive client-side from `/api/patients?limit=500` OR port the HTML seed shape with TODO marker.
- Patient list → `/api/patients?page=X&limit=Y`.
- Import CSV button → wire to a placeholder modal with `<LockedFeature>` body if no backend, OR open a file picker that POSTs to a not-yet-existing endpoint with the TODO marker.

## Done when
- Page matches HTML's KPI + toolbar + table layout exactly.
- `cd web && npx next build` green.
