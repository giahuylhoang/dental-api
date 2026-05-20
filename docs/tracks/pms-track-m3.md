# PMS Module M3 — Treatment plan dental chart + care notes (TDD)

Make `make test-pms-m3` exit 0.

## Success criteria

- `TreatmentPlanEditor` renders the existing `ToothChart` SVG above the items table.
- The chart is **interactive**: clicking tooth #N pre-fills the "Add procedure" form with `tooth_number=N`.
- Each plan item row shows a `tooth_number` cell (editable) and a `care_notes` textarea (inline expandable).
- Items with the same `tooth_number` group together visually (subtle row grouping or shared color stripe).
- Teeth referenced in any plan item get a colored dot on the chart (so you can see which teeth are in the plan).
- Saving a plan PATCHes `/api/v2/treatment-plans/{id}/items` with `tooth_number` and `care_notes` per item; backend M0 has the columns.

## Tests first (`frontend/tests/track_pms_m3/`)

1. **`editor-shows-tooth-chart.test.tsx`** — mount `<TreatmentPlanEditor patientId="p1" planId="tp1" />`; assert an SVG element representing the chart is in the DOM.

2. **`click-tooth-prefills-add-form.test.tsx`** — mount editor, fire click on the SVG element with `data-tooth="14"`, assert the "Add procedure" form's tooth_number input now has value `14`.

3. **`care-notes-saved-per-item.test.tsx`** — mount editor with 1 existing item, type into the item's care_notes textarea, click Save, mock the PATCH; assert request body items array has the new care_notes string.

E2E (`frontend/e2e/track_pms_m3/`):
- /plans → open existing plan → click tooth #14 → procedure code search opens with tooth=14 → add procedure with notes "implant candidate" → save → row shows tooth + notes after reload.

## Implementation

- Modify `frontend/src/features/treatment-plans/TreatmentPlanEditor.tsx`:
  - Import `ToothChart` from `frontend/src/features/patients/ToothChart.tsx`.
  - Add `selectedTooth` state lifted up.
  - Pass `onToothClick={(num) => setSelectedTooth(num)}` to ToothChart.
  - The "Add procedure" sub-form reads `selectedTooth` as its initial tooth_number.
  - Item rows: add a TD with tooth_number (editable input) + an expandable section for care_notes.
  - When listing teeth referenced, pass `highlightedTeeth={items.map(i => i.tooth_number).filter(Boolean)}` to ToothChart.
- Modify `ToothChart.tsx` (extend, don't break P1 tests): accept `onToothClick` and `highlightedTeeth` props. Add `data-tooth={n}` attribute to each tooth element (used by tests).

## Constraints

- Existing P1 tests for ToothChart must still pass.
- Care notes max 1000 chars (zod validation).
- Backend M0 columns already exist; no migration needed here.

```bash
make test-pms-m3
```
