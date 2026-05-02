# PMS Track P3 — Lab case detail + linkage

You are kiro-cli running headless. Make lab cases inspectable, linkable to denture cases, with implant + material consumption forms. Gate: `make test-pms-p3`.

## Deliverable files

- `frontend/src/features/lab/LabCaseDrawer.tsx`
  - Props: `{ caseId: string | null, open, onClose, onChanged }`
  - Loads via `GET /api/v2/lab/cases/{id}` (use the list endpoint with filter if no detail GET exists)
  - Shows: vendor name, due_back_at, lab_fee, courier_tracking, status, denture_case link
  - Tabs inside drawer: Detail | Implants | Materials
  - Buttons: "Send" (POST /send), "Return" (POST /return), "Remake" (opens reason form → POST /remake)

- `frontend/src/features/lab/DentureCaseDrawer.tsx`
  - Props: `{ caseId: string | null, open, onClose, onChanged }`
  - Loads via `GET /api/v2/clinical/denture-cases/{id}`
  - Shows: arch, case_type, current_stage, status, patient
  - "Advance stage" button → POST /advance (linear FSM enforced server-side)
  - "Close" button → POST /close

- `frontend/src/features/lab/ImplantForm.tsx`
  - Props: `{ dentureCaseId: string, onSaved }`
  - react-hook-form fields: tooth_position (1–32), vendor (text), model? (text), lot_number (text, required), surface_treatment (select: machined|SLA|RaSah|TiUnite|other), abutment_type (select: ball|bar|locator|magnet), placed_date (date)
  - Submits to `POST /api/v2/clinical/denture-cases/{id}/implants` (P0 endpoint)

- `frontend/src/features/lab/MaterialConsumptionForm.tsx`
  - Props: `{ labCaseId: string, onSaved }`
  - Loads inventory_items + inventory_lots from `GET /api/v2/inventory/items` and `/lots` (if endpoints exist; otherwise show a placeholder text "Inventory backend not wired" — but render a form skeleton with item_id, lot_id, qty_consumed, unit_cost fields)
  - Submits to `POST /api/v2/lab/cases/{id}/materials` if available; else log a console.warn and resolve.

- Modify `frontend/src/features/lab/LabCaseKanban.tsx`:
  - Card click → opens LabCaseDrawer
  - Don't break existing drag-to-change-status behavior
  - "Open denture case" link inside drawer opens DentureCaseDrawer (drawer-on-drawer is allowed; second drawer slides further left).

## Tests

Vitest (`frontend/tests/track_pms_p3/`):
- `lab-case-drawer.test.tsx` — renders with mocked GET response, tabs switch correctly
- `denture-case-drawer.test.tsx` — advance button calls POST
- `implant-form.test.tsx` — form validation (lot_number required), submit posts correct body
- `material-form.test.tsx` — renders with inventory list (or placeholder)

Playwright (`frontend/e2e/track_pms_p3/lab-flow.spec.ts`):
- Login → /lab → click a card → LabCaseDrawer opens → click Implants tab → fill form → save → row appears in implants list

## Constraints

- Reuse the shared `Drawer` from P1.
- Don't break the LabCaseKanban drag-and-drop status transitions.
- If the inventory endpoints don't exist, render a graceful placeholder rather than failing the build.

## Commands

```bash
cd frontend && npm run lint && npm run build
cd frontend && npm run test:pms-p3
cd frontend && npm run e2e:pms-p3
make test-pms-p3
```

When `make test-pms-p3` exits 0, you are done.
