# Track 5 — Frontend ops UI + cross-track integration

You are a coding agent working on **one of five parallel tracks**. Read `~/.claude/plans/now-i-want-to-fizzy-valley.md` for full context. Don't read or modify other tracks' files.

## Mission

Build the operational UI: enhanced calendar (multi-resource, recurring, drag-reschedule), invoice editor + payment recording + statements, insurance claim tracker, communication inbox, lead pipeline kanban with one-click conversion, reporting dashboards. Once Tracks 2 & 3 land their backends, switch MSW off and run integration tests against `http://localhost:8000`.

## Hard constraints (CI gate)

1. Don't touch `tmp/dental-calendar/`. Don't edit Track 4's directories (`frontend/src/features/{patients,clinical,lab,treatment-plans,auth,shell}/`). You may consume their components and the auth store.
2. Work under `frontend/src/features/{scheduling,billing,communications,crm,reporting}/`, `frontend/tests/track_ops/`, plus shared `frontend/src/api/v2/` (additive).
3. TypeScript strict, ESLint clean, `cd frontend && npm run build` zero-warning.
4. Unit + e2e tests pass under MSW; with `E2E_BACKEND_URL=http://localhost:8000` set, e2e also passes against a live backend.

## Stack

Same as Track 4. New additions allowed: `@fullcalendar/react` family (already in repo for tmp/dental-calendar), `react-rnd` or similar for resize, `chart.js` or `recharts` for dashboards.

## Deliverables

### Scheduling (`frontend/src/features/scheduling/`)

- `<Calendar>` — week/day view. Resources axis = providers OR operatories (toggle). Drag to reschedule, opens a confirm dialog. Drop on busy slot → 409 toast with conflict details.
- `<NewAppointmentDialog>` — patient picker (calls into Track 4's patient search), provider, operatory, service, recurrence (none|daily|weekly|monthly with count or until).
- `<WaitlistDrawer>` — patients waiting for a slot. "Auto-fill" button calls `POST /api/v2/scheduling/waitlist/{id}/fill`.
- `<RecallList>` — due recalls, "Send reminder now" action.
- `<RemindersSettings>` — per-clinic configure reminder offsets (48h/24h/2h default).

### Billing (`frontend/src/features/billing/`)

- `<InvoiceEditor>` — line items with procedure-code autocomplete, GST toggle, subtotal/GST/total live.
- `<InvoiceList>` — patient invoices, status badge, balance, "Issue", "Record payment", "Void" actions.
- `<PaymentModal>` — method, amount, reference.
- `<StatementPreview>` — printable A/R aging per patient (CSS print stylesheet).

### Insurance (`frontend/src/features/billing/claims/`)

- `<ClaimsList>` — filter by status. Submit/Adjudicate buttons reflect state machine.
- `<ClaimDetail>` — predetermination vs claim, attached invoice/treatment plan, response payload viewer (JSON tree).

### Communications (`frontend/src/features/communications/`)

- `<CommInbox>` — global inbox: SMS + email, inbound + outbound, threaded by patient.
- `<CommComposeDialog>` — choose channel + body, related appointment optional. Calls `POST /api/v2/communications/send`.
- `<MarketingCampaigns>` — list + simple builder (audience query JSON editor; v1 keep simple — just a Monaco-light JSON textarea with schema validation).

### CRM (`frontend/src/features/crm/`)

- `<LeadKanban>` — columns by status (NEW → CONTACTED → QUALIFIED → CONVERTED → LOST).
- Drag to advance status. "Convert" button on a lead card calls `POST /api/v2/crm/leads/{id}/convert` and navigates to the new patient's 360.
- `<LeadDetail>` — events timeline (`/api/v2/crm/leads/{id}/events`).
- `<LeadCaptureForm>` — public-style form (still requires clinic context); used as a snippet by the marketing site.

### Reporting (`frontend/src/features/reporting/`)

- `<Dashboard>` — KPI tiles: production this month, A/R aging buckets (0-30, 31-60, 61-90, 90+), no-show %, lab cost per case (denturist-specific).
- `<ProductionByProvider>` chart.
- `<RemakeRateByLab>` chart — denture-clinic differentiator.

### Cross-track integration

- Replace MSW mocks with real fetches once `VITE_USE_MSW=false`. Single switch in `src/mocks/index.ts`.
- Add a Vite proxy: `/api → http://localhost:8000` so dev mode hits the live backend without CORS hassle.
- Add a `frontend/Makefile` or npm script `e2e:live` that boots backend (`./run_local.sh &`), waits for `/health`, runs Playwright with `VITE_USE_MSW=false`.

### Storage backend stub

- Add `frontend/src/lib/upload.ts`:
  - `uploadDocument(file): { url, sha256, mime, size_bytes }`
  - In dev/MSW mode: returns a `blob:` URL.
  - In real mode: POSTs to a presign endpoint (you DO NOT need to add the endpoint — leave a TODO and a typed wrapper that fails clearly with "presign endpoint not implemented" until ops sets up GCS/S3 + a `/api/v2/uploads/presign` route).

### Tests (`frontend/tests/track_ops/`)

- Vitest:
  - `invoice-math.test.ts` — mirror backend math; load same fixtures from `tests/fixtures/invoices.json` (commit with both numerators).
  - `lead-conversion.test.ts` — convert action: optimistic update; if mutation fails, rollback.
- Playwright (MSW):
  - `flows/booking-to-payment.spec.ts` — book multi-resource appointment → reminder fires (mock advance time) → mark complete → invoice → submit predetermination → record payment.
  - `flows/lead-pipeline.spec.ts` — drag through pipeline → convert → arrives on patient 360.
- Playwright (live, gated by env):
  - `flows/live-smoke.spec.ts` — repeats booking-to-payment but against `${E2E_BACKEND_URL}`.

## Success gate

```
cd frontend && \
npm run lint && \
npm run build && \
npm run test:track-5 && \
npm run e2e:track-5
```

If `E2E_BACKEND_URL` is set, ALSO:
```
npm run e2e:live
```

All must exit 0. Loop until green.

## Notes

- For drag-to-reschedule on the calendar, debounce to a confirm dialog — never silently overwrite a booking.
- Use FullCalendar's `resourceTimeGrid` plugin for the multi-resource axis.
- For currency formatting, use `Intl.NumberFormat('en-CA', { style:'currency', currency:'CAD' })`. Don't write your own.
- For dates: TanStack Query keys must include the clinic id from the auth store, otherwise switching clinics will leak cached data.
- The lead-conversion success path should `queryClient.invalidateQueries(['patients'])` so the destination Patient 360 is fresh.
- Reporting v1 is read-only — no edits, no exports beyond CSV (use a tiny `papaparse` fork if needed).
