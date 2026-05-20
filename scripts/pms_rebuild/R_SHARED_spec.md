# Shared rules for R-tasks (pixel-perfect HTML → Next.js port)

## Hard mandate

**The HTML file at `/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/<page>.html` is the LITERAL source of truth.** Open it. Read its `<style>` block. Read its `<script type="text/babel">` block. Reproduce the page in Next.js so the resulting Next page renders the *same* layout, the *same* sections in the *same* order, the *same* KPI strip / page-header / panels / tables / sidebars, with the *same* text labels.

Do **NOT** infer structure from `/Users/giahuyhoangle/Projects/dental-api/frontend/src/features/...` — that Vite app is wrong and is being replaced. Do **NOT** keep my prior version of the page at `web/app/(app)/<route>/page.tsx` — overwrite it.

`_prototype/` subfolder is a separate AI-receptionist surface — IGNORE it for these tasks.

## Procedure (per page)

1. Read the HTML file fully.
2. Read every sibling JSX component the HTML imports via `<script type="text/babel" src="...jsx">` (e.g. `Sidebar.jsx`, `KpiTile.jsx`, `DataTable.jsx`, `Drawer.jsx`, etc.) — these define the components used in the babel-JSX block.
3. Read every `data/*.js` seed file the HTML script-tag-includes — these define the data shape the page expects.
4. Look up which equivalent Next/TSX components already exist under `web/components/dental/` and `web/components/ui/`. Reuse them where the API matches; if a component is missing or the API is wrong, ADD or EXTEND the component (don't fudge the page).
5. Convert the HTML's `<style>` block into a sibling CSS module `web/app/(app)/<route>/page.module.css` (or `(portal)/login/page.module.css` for login). Adjust selectors as needed (no `.app-shell` collisions with the global shell).
6. Convert the HTML's `<script type="text/babel">` body into the Next.js page (`page.tsx`). Add `'use client';` at the top.
7. **Data wiring** (CRITICAL):
   - For every data read the HTML does (`window.PATIENTS`, `window.APPOINTMENTS`, etc.), check whether the FastAPI backend at port 8001 has an endpoint for it (cross-reference `frontend/src/features/.../*.tsx` for the existing fetcher calls — those endpoint paths are correct).
   - If yes: use `useQuery({ queryKey, queryFn: () => fetcher(...) })` from `@/lib/api/client`. Preserve `X-Clinic-Id`.
   - If no (e.g. operatory grid, A/R aging buckets, lab pipeline stages): port the HTML's seed shape directly into a `const SEED_X = [...]` constant inside the page, prefixed with the comment `// TODO: wire to dental-agent — endpoint not yet implemented`. The page must still look pixel-perfect; the user accepted "Render with HTML's seed mock + TODO marker" for missing data.
8. **Locked overlays** — these four spots render `<LockedFeature />` *inside* the new page composition (do not delete the surrounding chrome):
   - `/plans` — entire page
   - `/reports` — advanced query/export panel only (KPI tiles stay live)
   - `/settings` — Integrations tab and Notifications tab (other tabs stay live)
   - `/communications` — composer area (inbox + thread list stay live)
9. **Inline styles allowed** in these page files when they directly mirror the HTML's inline JSX styles. The strict no-hex/no-inline rule is RELAXED for the rebuilt pages so visual parity wins. Tokens (`var(--primary)`, `var(--card)`, etc.) still preferred when the HTML uses them.
10. Build green: `cd web && npx next build`.

## Existing data wiring you MUST preserve

- `useAuthStore` from `@/lib/auth/store` (Zustand) — accessToken, clinicId, user.
- `fetcher<T>(path, init)` from `@/lib/api/client` — automatically adds `Authorization` and `X-Clinic-Id`, refreshes on 401.
- `<AuthGuard>` wrapping in `app/(app)/layout.tsx`.
- All endpoints already in use by `frontend/src/features/*/*.tsx` — those paths still work.

## Verify

```bash
cd web && npx next build
```

The page-level test script (e.g. `test_R01.sh`) will additionally grep for HTML signature strings that prove the port was structural, not just superficial.
