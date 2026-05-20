# PMS Track P1 — Patient360 functional rewrite

You are kiro-cli running headless. Make the Patient detail page (`/patients/:id`) fully functional. The gate `make test-pms-p1` passes when:

1. The deliverable files listed below exist
2. `cd frontend && npm run lint && npm run build` succeed (TypeScript clean)
3. `npm run test:pms-p1` (vitest) green
4. `npm run e2e:pms-p1` (Playwright) green
5. `uv run pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q` (V1 contract) still green

## Working directory & conventions

- Repo root: `/Users/giahuyhoangle/Projects/dental-api`
- Frontend: Vite + React 19 + TypeScript + Tailwind + react-router-dom 7 + TanStack Query + Zustand
- Existing API client: `frontend/src/api/client.ts` (`fetcher<T>(path, init?)` — adds X-Clinic-Id + Bearer token)
- Existing types: `frontend/src/api/v2/types.ts` (regenerated from `docs/openapi-v2.yaml` via `npm run gen:api`)
- Existing Patient360: `frontend/src/features/patients/Patient360.tsx` (10 tabs, 6 are placeholders)
- Backend on `:8765` is already running for E2E (or use `E2E_BASE_URL` env var to override Playwright base)
- Backend Phase 0 (track P0) has shipped these endpoints — DO NOT mock them; use the real backend in E2E:
  - `POST /api/v2/clinical/documents/upload` (multipart)
  - `GET/POST /api/v2/clinical/patients/{id}/tooth-chart`
  - `PUT/DELETE /api/v2/clinical/patients/{id}/insurance/{ins_id}`

## Deliverable files

### Shared primitives (new)
- `frontend/src/components/Drawer.tsx` — slide-over panel. Props: `{ open, onClose, title, width?: 'sm'|'md'|'lg', children, footer? }`. Uses focus trap + ESC key close + click-outside-to-close. Tailwind only (no Radix).
- `frontend/src/components/forms/FormField.tsx` — labeled wrapper around `<input>` / `<textarea>` / `<select>`. Props: `{ label, name, error?, required?, hint?, children }`. Children render the actual input.

### Patient360 sub-components (new)
- `frontend/src/features/patients/LifecyclePanel.tsx`
  - Shows current status (from `GET /api/v2/clinical/patients/{id}/status`)
  - Buttons: "Promote to active" (calls `POST /promote`, disabled if already active or missing data) and a status dropdown (active|inactive|deceased|merged|pending) with confirm dialog before changing.
- `frontend/src/features/patients/MedicalForm.tsx`
  - react-hook-form, zod validation
  - Fields: medical_history (textarea), allergies (textarea), medications (textarea), bisphosphonates_use (checkbox)
  - Loads via `GET /patients/{id}/medical-history`, saves via `POST` (server upserts)
  - "Save" + "Reset" buttons; show toast on save.
- `frontend/src/features/patients/InsuranceList.tsx` + `InsuranceDrawer.tsx`
  - List shows: carrier, policy_number, holder_name, is_primary, group_number?, edit/delete row buttons
  - "Add insurance" opens InsuranceDrawer in create mode
  - Click row opens InsuranceDrawer in edit mode (PUT)
  - Delete confirmation; uses DELETE endpoint
- `frontend/src/features/patients/DocumentUploader.tsx` + `DocumentList.tsx`
  - Uploader: drag-drop zone OR click to choose file; shows preview thumbnail; kind selector; "Upload" button posts multipart to `/api/v2/clinical/documents/upload`
  - List: groups by kind, click filename to open `storage_url` in new tab; show uploaded_at + size
- `frontend/src/features/patients/NotesPanel.tsx`
  - Wraps existing `frontend/src/features/clinical/notes/SoapEditor.tsx` (DO NOT rewrite SoapEditor)
  - List of past notes (most recent first), click to open SoapEditor in either edit (if not locked) or read-only mode
  - "New note" button opens blank SoapEditor; on save, list refreshes
  - Lock button on unlocked note → calls `POST /notes/{id}/lock`; locked notes show 🔒
  - Amend button on locked note → opens SoapEditor with `supersedes_id` pre-set
- `frontend/src/features/patients/ToothChart.tsx`
  - SVG of 32 teeth (FDI numbering laid out maxillary 1–16 top, mandibular 17–32 bottom)
  - Each tooth colored by status (present=neutral, missing=hidden, extracted=red dashed, implant=blue, crowned=gold, filled=cyan)
  - Click a tooth → small popover with status dropdown + notes; "Save" calls POST `/tooth-chart` with just that tooth.
  - Loads via GET on mount.

### Patient360 page (modify)
Edit `frontend/src/features/patients/Patient360.tsx` so:
- Tab list: Overview | Status | Medical | Insurance | Documents | Tooth Chart | Treatment Plans | Denture Cases | Notes | Appointments | Invoices | Communications
- Each tab renders the corresponding component (Communications stays a placeholder; do NOT modify it)
- Use a controlled tab state via URL search param `?tab=medical` so deep-linking works

### Tests (new)

Vitest unit (`frontend/tests/track_pms_p1/`):
- `lifecycle-panel.test.tsx` — renders status, promote button disabled when already active
- `medical-form.test.tsx` — submits form, calls POST endpoint with correct body
- `insurance-list.test.tsx` — opens drawer on add, shows existing rows
- `document-uploader.test.tsx` — accepts file, posts multipart
- `notes-panel.test.tsx` — lists notes, locks correctly
- `tooth-chart.test.tsx` — clicking tooth opens popover, saves single-tooth update

Use MSW handlers in `frontend/src/mocks/` for unit tests (already present — extend if needed).

Playwright E2E (`frontend/e2e/track_pms_p1/patient-flow.spec.ts`):
- Logs in (admin@example.com / changeme)
- Quick-books a new patient
- Fills medical, uploads document, adds insurance, writes a SOAP note
- Promotes to active
- Uses real backend at `process.env.E2E_BASE_URL || 'http://localhost:4173'`

## Constraints

- DO NOT touch `frontend/src/features/communications/` — out of scope.
- DO NOT touch `tests/test_contract_v1.py` or any file under `api/main.py`.
- DO NOT remove existing tabs from Patient360 (Overview, Treatment Plans, Denture Cases, Appointments must stay functional).
- Reuse `Drawer` and `FormField` for ALL new UI.
- Preserve `VITE_USE_MSW=false` behavior for the production build.
- `npm run lint` includes `tsc --noEmit`. Keep TypeScript strict.

## Commands

```bash
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm run test:pms-p1
cd frontend && npm run e2e:pms-p1
make test-pms-p1
```

When `make test-pms-p1` exits 0, you are done.
