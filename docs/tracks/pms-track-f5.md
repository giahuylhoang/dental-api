# PMS Module F5 — CRM: skeleton loading + endpoint fix + denser sample (TDD)

Make `make test-pms-f5` exit 0.

## Success criteria

- `LeadKanban` replaces the current `"Loading…"` text (line ~77) with skeleton cards. While the leads query is loading, render 5 columns × 2 placeholder cards (zinc-200 animated pulse boxes). When data arrives, swap to real cards.
- Drag-to-change-status fires `PUT /api/v2/crm/leads/{id}` body `{status: '<NEW>'}`. The current code (`LeadKanban.tsx:47`) uses `/api/leads/{id}/status` which is the wrong path — fix it. The M4 backend already exposes `PUT /api/v2/crm/leads/{id}` accepting partial fields including status.
- Each card shows a small source pill: 📞 phone / 🌐 web / 👥 referral / 🚶 walk-in / ❓ other.
- Sample data: 15 leads spread NEW(5) / CONTACTED(4) / QUALIFIED(3) / CONVERTED(2) / LOST(1) — driven by F0 seed.

## Tests first (`frontend/tests/track_pms_f5/`)

1. **`kanban-shows-skeletons-while-loading.test.tsx`** — mount `<LeadKanban />` with MSW handler that delays the leads response; immediately query `getAllByTestId('lead-skeleton')` returns ≥5; after waitFor for real data, skeletons disappear.

2. **`drag-fires-correct-status-endpoint.test.tsx`** — render kanban with one lead in NEW; simulate the drag-end callback (call the `onDragEnd` handler directly with payload moving lead to CONTACTED); MSW captures the request URL and method; assert `PUT /api/v2/crm/leads/{id}` (NOT `/api/leads/{id}/status`).

3. **`source-pill-rendered.test.tsx`** — render with 5 leads each with different source values; assert all 5 source labels visible.

4. **`kanban-distributes-15-leads.test.tsx`** — render with 15 fixture leads; assert each column header count: NEW=5, CONTACTED=4, QUALIFIED=3, CONVERTED=2, LOST=1.

## Implementation

- Modify: `frontend/src/features/crm/LeadKanban.tsx`:
  - Replace `if (isLoading) return <p>Loading…</p>;` with a skeleton grid.
  - Replace `fetcher('/api/leads/{id}/status', { method: 'PUT', body: ... })` with `fetcher('/api/v2/crm/leads/{id}', { method: 'PUT', body: { status } })`.
  - Add source pill rendering.
- Optionally tiny new component `frontend/src/features/crm/LeadCardSkeleton.tsx` for the placeholder.

## Constraints

- Don't break M4 CRM tests (`frontend/tests/track_pms_m4/`).
- Don't break the existing drag-and-drop behavior (dnd-kit setup stays).
- Skeleton must be removed once `isLoading === false`, even if data is empty (show empty columns, not perpetual skeletons).

```bash
make test-pms-f5
```
