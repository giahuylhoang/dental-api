# PMS Track P2 — Calendar booking detail + status workflow

You are kiro-cli running headless. Make calendar appointments inspectable and status-changeable. Gate: `make test-pms-p2`.

## Deliverable files

- `frontend/src/features/scheduling/appt-status.ts`
  - Exports `APPT_STATUSES = ['SCHEDULED','CONFIRMED','CHECKED_IN','IN_PROGRESS','COMPLETED','NO_SHOW','CANCELLED'] as const`
  - Type `ApptStatus`
  - `nextAllowed(current: ApptStatus): ApptStatus[]` — state-machine allowed transitions
  - `statusColor(s: ApptStatus): string` — Tailwind class for the badge color
  - `statusLabel(s: ApptStatus): string` — human-readable label

- `frontend/src/features/scheduling/AppointmentDrawer.tsx`
  - Props: `{ appointmentId: string | null, open: boolean, onClose, onChanged }`
  - Loads appointment via `GET /api/appointments/{id}` (v1; existing endpoint)
  - Shows: patient name (link to /patients/:id), provider name, service, start/end time, status badge, notes
  - Action buttons (each calls the corresponding v1 endpoint):
    - "Confirm" → `PUT /api/appointments/{id}/status` body `{status: 'CONFIRMED'}` — only when current is SCHEDULED
    - "Check in" → status `CHECKED_IN` — only when CONFIRMED
    - "Start" → status `IN_PROGRESS` — only when CHECKED_IN
    - "Complete" → status `COMPLETED` — only when IN_PROGRESS
    - "No show" → status `NO_SHOW` — only when SCHEDULED or CONFIRMED
    - "Cancel" → confirmation dialog → `PUT /api/appointments/{id}/cancel`
    - "Reschedule" → opens DateTimePicker → `PUT /api/appointments/{id}/reschedule`
  - Buttons disable based on `nextAllowed(currentStatus)`.

- `frontend/src/features/scheduling/DateTimePicker.tsx`
  - Inline date input + time picker (use native `<input type="datetime-local">` for simplicity).
  - Props: `{ value: Date | null, onChange, min?, max? }`.

- Modify `frontend/src/features/scheduling/Calendar.tsx`:
  - Click on appointment block → opens `AppointmentDrawer` for that ID
  - Drag-to-reschedule continues to work (do not regress)
  - Status badge color comes from `statusColor()`
  - Add a small legend in the header (one chip per status with its color)

## Tests

Vitest (`frontend/tests/track_pms_p2/`):
- `appt-status.test.ts` — state machine: cannot skip from SCHEDULED to COMPLETED, can go CONFIRMED → CHECKED_IN, etc.
- `appointment-drawer.test.tsx` — renders, "Confirm" button enabled iff status=SCHEDULED, click calls PUT with correct body
- `calendar-click.test.tsx` — clicking a slot opens the drawer (mock calendar with 1 appointment)

Playwright (`frontend/e2e/track_pms_p2/calendar-flow.spec.ts`):
- Login → /schedule → click an appointment → drawer opens → click "Confirm" → status badge updates → close drawer

## Constraints

- DO NOT modify v1 appointment response shape.
- Use the v1 endpoints `/api/appointments/{id}/status`, `/cancel`, `/reschedule` (NOT v2 — v2 has more fields the calendar doesn't need yet).
- Reuse the shared `Drawer` from `frontend/src/components/Drawer.tsx` (built in P1).
- Reuse `FormField` for any forms (built in P1).

## Commands

```bash
cd frontend && npm run lint && npm run build
cd frontend && npm run test:pms-p2
cd frontend && npm run e2e:pms-p2
make test-pms-p2
```

When `make test-pms-p2` exits 0, you are done.
