# PMS Track P4 — Treatment plan editor wired + invoice handoff

You are kiro-cli running headless. Wire the existing `TreatmentPlanEditor` into a real route and add a "Generate invoice" handoff. Gate: `make test-pms-p4`.

## Deliverable files

- `frontend/src/features/treatment-plans/TreatmentPlansPage.tsx`
  - Route: `/plans` (modify `frontend/src/App.tsx` — currently a Placeholder; replace with this page)
  - Lists ALL treatment plans across patients (`GET /api/v2/treatment-plans`)
  - Filter chips: status=draft|presented|accepted|declined|completed
  - Search by patient name
  - Click row → opens existing `TreatmentPlanEditor` (reuse it; do NOT rewrite)
  - "New plan" button: prompts for patient (autocomplete) → creates plan and opens editor

- Modify `frontend/src/features/treatment-plans/TreatmentPlanEditor.tsx`:
  - Add a "Generate invoice from plan" button (only enabled when plan.status === 'accepted')
  - Clicking it: `POST /api/v2/billing/invoices/from-plan` body `{treatment_plan_id, patient_id}` (P0 endpoint), then navigates to `/billing` and (if P5 is shipped) opens InvoiceDrawer with the new invoice. If P5 not shipped, navigate to `/billing` and show a toast with the new invoice id.

- Modify `frontend/src/App.tsx`:
  - Replace `<Route path="/plans" element={<Placeholder ... />} />` with `<Route path="/plans" element={<TreatmentPlansPage />} />`

## Tests

Vitest (`frontend/tests/track_pms_p4/`):
- `treatment-plans-page.test.tsx` — renders list, filter chips work, search filters
- `generate-invoice.test.tsx` — button disabled when status≠accepted; click POSTs correct body

Playwright (`frontend/e2e/track_pms_p4/plan-flow.spec.ts`):
- Login → /plans → "New plan" → choose patient → editor opens → add 2 items → Present → Accept → "Generate invoice" → /billing reached

## Constraints

- Reuse existing `TreatmentPlanEditor.tsx`. Do NOT rewrite its core editing UI.
- Use the typed API client.
- The "Generate invoice from plan" backend endpoint is `POST /api/v2/billing/invoices/from-plan` (built in P0).

## Commands

```bash
cd frontend && npm run lint && npm run build
cd frontend && npm run test:pms-p4
cd frontend && npm run e2e:pms-p4
make test-pms-p4
```

When `make test-pms-p4` exits 0, you are done.
