# T13 — /reports + /plans (locked)

## Objective
Reports KPI tiles live; advanced query/export panel locked. `/plans` entirely locked.

## /reports — `web/app/(app)/reports/page.tsx`
- `"use client"`.
- Top: read-only KPI tiles fed by the same `/api/v2/reporting/*` endpoints used by `/dashboard` (period filter optional).
- Bottom panel "Advanced reports":
  ```tsx
  <LockedFeature
    title="Advanced reports"
    body="Custom queries and CSV export are paused while we rebuild the export pipeline."
    backHref="/dashboard"
  />
  ```

## /plans — `web/app/(app)/plans/page.tsx`
- Entire route is the locked overlay:
  ```tsx
  import { LockedFeature } from "@/components/dental/LockedFeature";
  export default function Page() {
    return (
      <LockedFeature
        title="Treatment Plans"
        body="The treatment plans workspace is paused while we redesign the clinical model."
        backHref="/dashboard"
      />
    );
  }
  ```

## Verify
```
cd web && npx tsc --noEmit && npx next build
```
