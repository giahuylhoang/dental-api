# PMS Module F3 — Lab cases: case numbers + plan link + denser sample (TDD)

Make `make test-pms-f3` exit 0.

## Success criteria

- Each lab card on the kanban renders the `case_number` prominently (e.g., `LC-2026-0042`) in a small monospace pill at the top of the card.
- `LabCaseDrawer` adds a "Linked Treatment Plan" section. If `case.treatment_plan_id` is present, show the plan's status pill + a "Open plan →" link to `/plans` (or `/plans?focus=<id>` if available). If NULL, hide the section (don't render an empty placeholder).
- POST `/api/v2/lab/cases` body accepts an optional `treatment_plan_id` (already added in F0). Update the create form (or the create-from-drawer flow) so a treatment plan can be selected — typeahead over `/api/v2/treatment-plans?patient_id=...`.
- Kanban shows ≥10 cases distributed across all 5 statuses (driven by F0 seed). Each column has at least one card.

## Tests first (`frontend/tests/track_pms_f3/`)

1. **`case-number-visible-on-card.test.tsx`** — render `<LabCaseKanban />` with MSW returning 3 cases each with `case_number` `LC-2026-0001|0002|0003`; assert each visible on the cards.

2. **`drawer-shows-linked-plan-link.test.tsx`** — render `<LabCaseDrawer case={withPlan} />`; assert "Open plan" link with `href` containing `/plans`. Then re-render with `treatment_plan_id: null`; assert no Linked Plan section.

3. **`create-case-with-plan-id.test.tsx`** — render the create form, select a plan from dropdown (mock `/api/v2/treatment-plans?...`), submit; assert the POST body to `/api/v2/lab/cases` includes `treatment_plan_id`.

4. **`kanban-distributes-12-cases.test.tsx`** — render with seed of 12 cases (≥1 per column); assert each column header shows count > 0.

## Implementation

- Modify: `frontend/src/features/lab/LabCaseKanban.tsx` — render `case_number` on cards (small monospace).
- Modify: `frontend/src/features/lab/LabCaseDrawer.tsx` — add "Linked Treatment Plan" section + create-form plan typeahead.
- Mocks: ensure `frontend/src/mocks/lab-cases.ts` (or wherever the lab handler lives) is seeded with ≥10 cases having varied statuses + some with `treatment_plan_id`.

## Constraints

- Don't break P3 lab tests (`frontend/tests/track_pms_p3/`).
- Don't break M3 ToothChart wiring on treatment plans.
- Card layout shouldn't break in narrow columns — case_number can wrap or truncate.

```bash
make test-pms-f3
```
