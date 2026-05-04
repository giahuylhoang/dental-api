# T07 — /dashboard

## Objective
Build the production dashboard at `web/app/(app)/dashboard/page.tsx`, matching `ui_kits/website/dashboard.html`, wired to existing `/api/v2/reporting/*` endpoints via `@/lib/api/client.ts` `fetcher`.

## Reference
- Visual: `/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/dashboard.html`
- Existing logic: `/Users/giahuyhoangle/Projects/dental-api/frontend/src/features/reporting/Dashboard.tsx`

## Sections
1. KPI tiles using `KpiTile` from `@/components/dental/KpiTile`: production, no-show rate, lab cost, A/R balance.
2. A/R aging — `DataTable` columns: `bucket, count, total`.
3. Provider production — list/table grouped by provider.
4. Lab remake rates — list with `StatusPill` for severity.
5. Recent activity feed.

## Implementation
- `"use client"`.
- `useQuery` per section against `/api/v2/reporting/*` paths used in the Vite app (preserve query keys + paths).
- Render `Skeleton` while loading; `EmptyState` when arrays are empty.
- All chrome via tokens: `bg-card`, `border-border`, `shadow-md`, `rounded-lg`, `font-display` for headlines and KPI numbers, `font-mono` for numeric values.
- Page header via `@/components/ui/page-header` (or compose with `font-display` + breadcrumb).

## Verify
```
cd web && npx tsc --noEmit && npx next build
```

## Done when
- `/dashboard` page builds, renders without console errors against MSW mocks.
- No raw hex / inline styles in the page.
