# PMS Module E1 — Scheduler: full shadcn redesign (top priority)

Make `make test-pms-e1` exit 0.

## Why

The user said the Scheduler is the **worst-looking page**: it's a bare `<FullCalendar>` plopped on the page with zero D1 components, no PageHeader, no toolbar, no filters, no view-toggle styling, and event chips show no patient name. E1 makes it look like a real product.

## Success criteria

### `frontend/src/features/scheduling/Scheduler.tsx` — full rewrite

The page becomes a vertical stack:

1. **PageHeader** (D5 primitive) — title "Schedule", description with current week range; right side: Today button (D1 `<Button variant="outline">`) and a `<Button>+ New appointment</Button>` that opens the create dialog at "now".
2. **Toolbar Card** — a `<Card>` with `<CardContent className="flex items-center gap-3">`:
   - Provider filter — D1 `<Select>` with "All providers" + each provider name (fetched from `/api/providers`).
   - Service filter — D1 `<Select>` with "All services" + each service.
   - Status legend chips — small `<Badge>`s showing color = status (scheduled / confirmed / completed / cancelled / no-show).
   - View toggle on the right — D1 `<Tabs>` with three tabs: Day / Week / Month → toggles FullCalendar view via `calRef.current.getApi().changeView()`.
3. **Calendar Card** — `<Card>` wrapping FullCalendar; remove the FullCalendar default header toolbar (we own the toolbar above) by passing `headerToolbar={false}`.
4. New file `frontend/src/features/scheduling/scheduler.css` — overrides for `.fc-*` selectors that consume design tokens:
   - `.fc { font-family: var(--font-display); }`
   - `.fc-event { border-radius: var(--radius-sm); padding: 2px 6px; font-size: var(--text-xs); }`
   - `.fc-event[data-status="scheduled"]` / `confirmed` / `completed` / `cancelled` / `noshow` — color coding from the `--ds-action`/`--ds-success`/etc tokens.
   - `.fc-col-header-cell-cushion`, `.fc-timegrid-slot-label-cushion` — text color from `--color-text-secondary`.
   - `.fc-day-today` — subtle bg from `--color-bg-clinical`.
   - Import this CSS from `Scheduler.tsx`.
5. **Event chips with patient name** — when building `fcEvents`, prepend the patient name (resolved via `usePatient(event.patient_id)` — but bulk-resolve via a single `useQuery(['patients-by-ids', ids])` call to avoid N+1). Format: `"<10:00> Alice Smith — Cleaning"`. Pass `extendedProps: { status, patientName }` so the CSS data-status attribute can be set in `eventDidMount`.
6. **Tooltip on hover** — `eventDidMount` attaches a D1 `<Tooltip>` showing patient + service + status (use `react-tooltip-style content` via portal, OR set `title` attribute with `usePatient`).

### `frontend/src/features/scheduling/NewAppointmentDialog.tsx` — D1 Dialog rewrite

- Replace the existing custom dialog wrapper with `<Dialog>`/`<DialogContent>`/`<DialogHeader>`/`<DialogFooter>`.
- Form layout: `<Form>` → `<FormField>` rows. Each row uses D1 `<Label>` + `<Input>` / `<Select>` / `<Textarea>`.
- Patient row: D2 `<PatientSearchInput>` (already wired) inside a `<FormField>` with label "Patient".
- Provider/Service: D1 `<Select>`.
- Start/end: D1 `<Input type="datetime-local">` (or two separate `<Input type="time">` for cleaner UX).
- Chief complaint: D1 `<Textarea>` (add this primitive in this module if missing — `frontend/src/components/ui/textarea.tsx`).
- Notes: same.
- "+ Create new patient" → opens `<QuickBookPopover>` (already exists from M1) inside a D1 `<Popover>`.
- Submit: `<Button type="submit">{isPending ? "Saving…" : "Create"}</Button>`. Cancel: `<Button variant="ghost">`.

### `frontend/src/features/scheduling/AppointmentDrawer.tsx` — D1 + PatientChip

- Replace custom drawer wrapper with D1 `<Sheet>` (E0) so it slides from the right.
- Header uses D2 `<PatientChip variant="card">` for the patient.
- Status pill = D1 `<Badge>` with variant by status.
- Action buttons (Reschedule, Cancel, Complete) = D1 `<Button>` row with proper variants (destructive for Cancel).

### Add primitive: `frontend/src/components/ui/textarea.tsx`

Standard shadcn-shape textarea.

## Tests first (`frontend/tests/track_pms_e1/`)

1. **`scheduler-redesign.test.tsx`** — render `<Scheduler />`; assert presence of:
   - PageHeader title text "Schedule"
   - Provider filter `<Select>` (data-testid or role)
   - View toggle tabs (Day/Week/Month) — three tabs visible
   - The "+ New appointment" button
   - The FullCalendar root `.fc`

2. **`scheduler-tabs-change-view.test.tsx`** — click the "Day" tab; assert the FullCalendar API was called with `changeView('timeGridDay')` (mock `calRef`).

3. **`scheduler-event-shows-patient-name.test.tsx`** — pre-mock `/api/calendar/events?...` to return one event with patient_id; mock `/api/patients?ids=...` (or whatever the bulk-resolve endpoint is — if it doesn't exist, hit `/api/patients/{id}` per id with caching); render; assert the rendered event title contains the patient's first name.

4. **`new-appointment-dialog-uses-d1.test.tsx`** — open NewAppointmentDialog; assert the dialog has a Radix `data-state="open"` attribute (D1 Dialog) AND inside it there's a D1 `<Select>` (`data-testid="provider-select"` etc).

5. **`appointment-drawer-uses-sheet.test.tsx`** — open AppointmentDrawer for a known appointment; assert it's rendered as a Sheet (right-side slide; data-attr).

## Strict gate (Makefile)

- `Scheduler.tsx` must have ≥3 `from '@/components/ui'` imports.
- `NewAppointmentDialog.tsx` must have ≥3 `from '@/components/ui'` imports.
- `AppointmentDrawer.tsx` must have ≥2 `from '@/components/ui'` imports.
- Zero raw `<button` elements in `Scheduler.tsx`.
- Zero ad-hoc `rounded.*border.*bg-white` in `Scheduler.tsx`.

## Constraints

- Don't break M1 tests (calendar-renders-fullcalendar, select-opens-dialog, quick-book-creates-patient, chief-complaint-saved). If they break due to legitimate UX changes, update them in this module preserving their *intent* (e.g., M1's "select range to open dialog" must still pass).
- The `events` data-fetching must still hit `/api/calendar/events?start=&end=` (backend GET we just added).
- FullCalendar's own toolbar is hidden (`headerToolbar={false}`); WE own the toolbar above.

```bash
make test-pms-e1
```
