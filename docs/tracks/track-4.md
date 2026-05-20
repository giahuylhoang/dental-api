# Track 4 — Frontend shell + Clinical UI

You are a coding agent working on **one of five parallel tracks**. Read `~/.claude/plans/now-i-want-to-fizzy-valley.md` for full context. Don't read or modify other tracks' files.

## Mission

Build the React SPA shell and the clinical UI: auth flow, app layout (Twenty-style left nav + command palette), patient list and Patient 360 page, treatment plan editor, denture-case timeline, lab-case kanban, SOAP note editor with locking. Frontend-only — backend tracks own the API. While Track 1/2 are still in flight, mock everything via MSW handlers wired to `docs/openapi-v2.yaml`.

## Hard constraints (CI gate)

1. Don't touch `tmp/dental-calendar/` — existing clients may still build from it.
2. All work in `frontend/` (scaffolded in Phase 0). Only edit files under `frontend/src/features/{patients,clinical,lab,treatment-plans,auth,shell}/`, `frontend/src/api/`, `frontend/src/components/`, `frontend/src/lib/`, `frontend/tests/track_clinical/`, `frontend/src/mocks/`.
3. TypeScript strict mode on. No `any`. ESLint passes.
4. `cd frontend && npm run build` MUST succeed with zero errors and warnings.
5. `cd frontend && npm run test:track-4` MUST pass.
6. `cd frontend && npm run e2e:track-4` MUST pass (Playwright with MSW; no live backend required).

## Stack (pinned in Phase 0)

- Vite + React 19 + TypeScript
- React Router v6
- TanStack Query v5 (server state)
- Zustand (local UI state)
- shadcn/ui + Tailwind (run `npx shadcn@latest init` if not done; pick neutral theme)
- MSW v2 (request mocking)
- Vitest + @testing-library/react (unit)
- Playwright (e2e)
- `openapi-typescript` for generating `frontend/src/api/v2/types.ts` from `docs/openapi-v2.yaml`. Re-run on spec changes via `npm run gen:api`.

## Deliverables

### Auth (`frontend/src/features/auth/`)
- Login page; logout; refresh interceptor.
- Token store (Zustand). Persist refresh token in `localStorage`; access token in memory only.
- `<Authed>` and `<RequirePermission perms={[...]}>` route guards.
- `useCurrentUser` hook.

### App shell (`frontend/src/features/shell/`)
- Three-pane layout: left nav (Patients, Schedule, Lab, Plans, CRM, Billing, Settings), main content, right inspector (when applicable).
- Top bar: clinic switcher (admin only — list from `/api/v2/auth/me`), user menu, command-K palette (cmd+k → fuzzy nav + jump to patient).
- Toast notification system (one provider; tracks 5 reuses).

### Patients (`frontend/src/features/patients/`)
- `<PatientsList>` — server-paginated table, search by name/phone/email, status filters; uses `GET /api/patients` (v1, no auth required) AND `GET /api/v2/clinical/patients/{id}/...` for the 360 view.
- `<Patient360>` page with tabs:
  1. **Overview** — demographics, age computed from DOB, last appointment, open denture cases, open invoices summary
  2. **Medical** — medical history + allergies + medications editors (inline)
  3. **Insurance** — list of `patient_insurance` rows; add/edit; mark primary
  4. **Documents** — upload (POST URL+sha; client computes sha256 in-browser via `crypto.subtle`); thumbnails for image kinds
  5. **Treatment Plans** — list; click → editor (see below)
  6. **Denture Cases** — list with stage badge; click → timeline view
  7. **Notes** — SOAP editor (lock/amend chain UI)
  8. **Appointments** — list (calls v1 `GET /api/appointments?patient_id=`)
  9. **Invoices** — read-only summary (Track 5 owns the editor)
  10. **Communications** — read-only timeline (Track 5 owns send)

### Treatment plans (`frontend/src/features/treatment-plans/`)
- Editor: line-item rows with code autocomplete (calls `GET /api/v2/clinical/procedures?q=`); compute totals client-side and reconcile with server response on save.
- Estimate breakdown panel: subtotal, GST, insurance estimate, patient estimate.
- Workflow buttons: Save Draft, Present, Accept (collect signature via `<canvas>`), Decline, Complete.

### Denture cases (`frontend/src/features/clinical/denture-cases/`)
- `<DentureCaseTimeline>` — vertical stepper showing stages with current highlighted; "Advance Stage" modal collects note + photos.
- `<NewDentureCaseDialog>` — pick arch + type.

### Lab cases (`frontend/src/features/lab/`)
- `<LabCaseKanban>` — columns by status (draft/sent/in_progress/returned/remake). Drag a card to advance. Drop on `remake` opens a "Reason" dialog.
- `<LabVendorPicker>` for the new-case dialog.

### Notes (`frontend/src/features/clinical/notes/`)
- `<SoapEditor>` — four sections, autosave to draft. Lock button → confirms then disables editing. Amend button on locked note opens a fresh editor referencing `supersedes_id`.

### MSW handlers (`frontend/src/mocks/`)
- One file per resource (`patients.ts`, `denture-cases.ts`, `lab-cases.ts`, `treatment-plans.ts`, `auth.ts`).
- Drive responses from in-memory tables generated from a fixture seed file.
- All handlers respect the `X-Clinic-Id` header.
- Switch off in production builds (`if (import.meta.env.DEV) start()`).

### Tests (`frontend/tests/track_clinical/`)
- Vitest:
  - `patient360.test.tsx` — renders all tabs; switching tabs triggers correct query.
  - `treatment-plan-math.test.ts` — totals match the backend's invoice-math formulas (cross-check). Use the same lines from `tests/track_ops/test_invoice_math.py` if available.
  - `soap-locking.test.tsx` — locked note disables fields; Amend opens fresh editor.
- Playwright e2e (run against MSW):
  - `flows/clinical-end-to-end.spec.ts` — login → search patient → open 360 → create denture case → advance stage with photo → mark complete → SOAP note write+lock+amend.
  - `flows/lab-kanban.spec.ts` — drag card from sent→in_progress→returned; trigger remake from returned; new card appears.

### npm scripts (`frontend/package.json`)
```
"gen:api": "openapi-typescript ../docs/openapi-v2.yaml -o src/api/v2/types.ts",
"test:track-4": "vitest run tests/track_clinical",
"e2e:track-4": "playwright test tests/track_clinical/flows",
"lint": "eslint . && tsc --noEmit",
"build": "vite build",
"dev": "vite"
```

## Success gate

```
cd frontend && \
npm run lint && \
npm run gen:api && \
npm run build && \
npm run test:track-4 && \
npm run e2e:track-4
```

All must exit 0. Loop until green.

## Notes

- The shadcn components live in `frontend/src/components/ui/`. Add only what you need (Button, Input, Dialog, Table, Tabs, Toast, Command, DropdownMenu, Avatar, Badge, Card).
- For Drag-and-drop in the lab kanban, prefer `@dnd-kit/core` (small, accessible) over react-dnd.
- For the command palette, use shadcn's `<Command>` plus `cmdk`. Wire it to a global `cmd+k` listener.
- Keep API client thin: a `fetcher` in `src/api/client.ts` that injects `X-Clinic-Id` from the auth store, attaches Bearer token, refreshes on 401 once.
- For tests, MSW must be set up in a Vitest setup file (`frontend/tests/setup.ts`) and a Playwright global init.
- Keep image previews local — never upload bytes from the SPA in this track. The Document POST takes a pre-uploaded URL. Storage is Track 5's territory.
