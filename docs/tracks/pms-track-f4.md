# PMS Module F4 — Treatment plans: endpoint cleanup + status flow + tiptap notes (TDD)

Make `make test-pms-f4` exit 0.

## OSS

- `@tiptap/react` (already added in F1) — reused for `care_notes` per item.

## Success criteria

- All TreatmentPlan API calls use `/api/v2/treatment-plans` (or `/api/v2/treatment-plans/{id}/...`). Eliminate any path containing `/api/v2/clinical/patients/.../treatment-plans` (currently mismatched between `TreatmentPlansPage.tsx:54` and `TreatmentPlanEditor.tsx:88`).
- Each plan in the list view has a status pill (draft / presented / accepted / in_progress / completed / declined) with consistent colors.
- `TreatmentPlanEditor` shows a row of status transition buttons whose visibility depends on the current status:
  - `draft` → "Present" button (POSTs `/api/v2/treatment-plans/{id}/present`)
  - `presented` → "Accept" + "Decline"
  - `accepted` → "Mark in progress" (POSTs `/{id}/in-progress` if exists, else `/{id}/accept` is the terminal — check existing endpoints)
  - `in_progress` → "Complete" (POSTs `/{id}/complete`)
- Per-item `care_notes` editable in `@tiptap/react` (StarterKit, plain-text on save). Saved via existing `PATCH /api/v2/treatment-plans/{id}/items` flow.
- Sample data shows ≥6 plans across multiple statuses (driven by F0 seed).

## Tests first (`frontend/tests/track_pms_f4/`)

1. **`plan-list-shows-status-pills.test.tsx`** — render `<TreatmentPlansPage />` with 4 plans of varying statuses; assert all 4 status text labels visible.

2. **`present-plan-fires-correct-endpoint.test.tsx`** — render `<TreatmentPlanEditor planId="P1" />` for a draft plan; click "Present"; assert POST to `/api/v2/treatment-plans/P1/present` (capture URL via MSW spy).

3. **`tiptap-care-notes-roundtrip.test.tsx`** — render editor with one item; type "needs follow-up" in the care_notes Tiptap; save; assert `PATCH /api/v2/treatment-plans/{id}/items` body has the item with `care_notes: "needs follow-up"`.

4. **`endpoint-consistency.test.tsx`** — render `<TreatmentPlansPage />` and `<TreatmentPlanEditor>`; trigger create flow + load flow; capture all outbound URLs; assert NONE match `/api/v2/clinical/patients/.+/treatment-plans` and ALL plan-related calls match `/api/v2/treatment-plans*`.

## Implementation

- Modify: `frontend/src/features/treatment-plans/TreatmentPlansPage.tsx` — fix create endpoint; add status pills.
- Modify: `frontend/src/features/treatment-plans/TreatmentPlanEditor.tsx` — fix endpoint; add status transition buttons; swap care_notes textarea for Tiptap.
- Tiny utility: `frontend/src/features/treatment-plans/statusFlow.ts` — exports `nextActions(status)` returning the array of transition buttons.

## Constraints

- Don't break M3 ToothChart click-to-add-procedure flow (`frontend/tests/track_pms_m3/`).
- Don't break P4 treatment plan tests (`frontend/tests/track_pms_p4/`).
- Existing PATCH items endpoint replaces all items; preserve that semantics — just add `care_notes` to each item.

```bash
make test-pms-f4
```
