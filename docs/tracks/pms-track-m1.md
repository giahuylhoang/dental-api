# PMS Module M1 — Scheduler with FullCalendar (TDD: tests first)

Make `make test-pms-m1` exit 0. Tests are written FIRST, then implementation.

## Repo facts

- Frontend: Vite 8 + React 19 + TypeScript + Tailwind + react-router-dom 7 + TanStack Query + Zustand
- API client: `frontend/src/api/client.ts` (`fetcher<T>(path, init?)`)
- Existing AppointmentDrawer: `frontend/src/features/scheduling/AppointmentDrawer.tsx` (built in P2 — keep using it for clicks on existing events)
- Existing Calendar: `frontend/src/features/scheduling/Calendar.tsx` — replaceable
- Backend M0 has shipped: `appointments.chief_complaint` column, accepted in POST body
- OSS already installed: `@fullcalendar/react @fullcalendar/timegrid @fullcalendar/daygrid @fullcalendar/interaction`
- Real backend on :8765, frontend dev/preview on :5178 or :4173 (Playwright honors `E2E_BASE_URL`)
- Login: admin@example.com / changeme

## Success criteria

- Route `/schedule` renders a FullCalendar component (a div with class `.fc` exists in the DOM).
- Toolbar lets user switch between **timeGridDay**, **timeGridWeek**, **dayGridMonth**.
- Slot granularity: 15 minutes (`slotDuration="00:15:00"`).
- **Click-and-drag on an empty range** → opens `NewAppointmentDialog` pre-filled with `{start, end}`.
- **Click an existing event** → opens `AppointmentDrawer` (already in P2).
- **Drag-to-reschedule** existing events → calls `PUT /api/appointments/{id}/reschedule` with new start/end.
- `NewAppointmentDialog`:
  - Patient combobox (typeahead over `/api/patients`). If no result, show "+ Create new patient" button → `QuickBookPopover` opens, on save the new patient is selected.
  - Provider dropdown.
  - Service dropdown.
  - Start/end (datetime-local inputs, pre-filled from drag).
  - **Pain points / Chief complaint** textarea.
  - Notes textarea.
  - Submit → `POST /api/calendar/events` body includes `chief_complaint`. On 200, dialog closes + calendar refetches.

## Tests first (write BEFORE implementation)

Create `frontend/tests/track_pms_m1/`:

1. **`calendar-renders-fullcalendar.test.tsx`** — render `<Scheduler />` (mock auth + react-query); assert `document.querySelector('.fc')` is not null.

2. **`select-opens-dialog.test.tsx`** — render `<Scheduler />`; trigger the FullCalendar `select` callback programmatically (or via the calendar API); assert `<NewAppointmentDialog>` is visible with the start time matching the selection.

3. **`quick-book-creates-patient.test.tsx`** — render dialog, click "Create new patient", fill name+phone in popover, submit; mock MSW handler for `POST /api/v2/clinical/patients/quick-book`; assert mocked call was made and patient is selected after.

4. **`chief-complaint-saved.test.tsx`** — render dialog with selected patient/provider/service, type "tooth pain throbbing" into pain-points textarea, submit; mock MSW for `POST /api/calendar/events`; assert request body has `chief_complaint: 'tooth pain throbbing'`.

Create `frontend/e2e/track_pms_m1/scheduler-flow.spec.ts`:

```ts
test('drag-to-create with chief complaint', async ({ page }) => {
  // login, navigate to /schedule
  // FullCalendar .fc-timegrid-slot-lane visible
  // simulate mousedown+mousemove+mouseup over a free range OR call FullCalendar.select() via window.__fc
  // dialog appears, fill pain-points + pick patient (existing) + service + provider
  // submit; event appears on the calendar
});
```

## Implementation files

- `frontend/src/features/scheduling/Scheduler.tsx` — FullCalendar wrapper. Plugins: `timeGridPlugin`, `dayGridPlugin`, `interactionPlugin`. Headerbar: `prev,next today, dayGridMonth,timeGridWeek,timeGridDay`. `slotDuration="00:15:00"`. `events` from `GET /api/calendar/events?start=...&end=...` (use a date range query). `select` callback opens dialog. `eventClick` opens AppointmentDrawer. `eventDrop` calls reschedule endpoint with new datetimes.
- `frontend/src/features/scheduling/NewAppointmentDialog.tsx` — uses shared `Drawer` or modal. Patient combobox uses `cmdk`-style or simple input + filtered list. "+ Create new" opens `QuickBookPopover`.
- `frontend/src/features/patients/QuickBookPopover.tsx` — small popover with name + phone fields, "Create" calls `POST /api/v2/clinical/patients/quick-book`, on success calls `onCreated(patient)`.
- Update `frontend/src/App.tsx` route `/schedule` → `<Scheduler />`.

## Constraints

- DO NOT delete `Calendar.tsx` (it might be used elsewhere); just route `/schedule` to `Scheduler.tsx`.
- DO NOT modify `AppointmentDrawer.tsx` from P2 (just use it).
- Reuse `Drawer` and `FormField` for the new dialog.
- v1 backend endpoints unchanged — `chief_complaint` is already accepted by `POST /api/calendar/events` after M0.

## Commands

```bash
cd frontend && npm run lint && npm run build
cd frontend && npm run test:pms-m1
cd frontend && npm run e2e:pms-m1
make test-pms-m1
```

When `make test-pms-m1` exits 0, you are done.
