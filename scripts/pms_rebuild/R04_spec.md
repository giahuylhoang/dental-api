# R04 — /schedule from schedule.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/schedule.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/schedule/page.tsx` (**fully replace** — current FullCalendar version is wrong)

## Composition (CRITICAL — different from current)
The HTML uses a **custom 30-min × operatories grid**, NOT FullCalendar. Port it exactly:
1. Day toolbar: date picker, day-of-week pills (Mon / Tue / Wed / Thu / Fri / Sat / Sun) — clicking jumps to that weekday, provider filter dropdown.
2. **Custom grid**: rows = 30-min increments, columns = operatories (Op1, Op2, Op3, ...).
3. **Appointment blocks** with colored left-border by provider, status color-coded background.
4. **Provider sidebar** on the right: each provider's name + load count for the day.
5. "Now" line (horizontal red/blue indicator at current time).
6. Status legend at bottom.
7. Toast notifications on actions.

REMOVE all `@fullcalendar/*` imports from this page.

## Data wiring
- Appointments for the day → `/api/appointments?date=YYYY-MM-DD`.
- Operatories → if no endpoint, port HTML's seed shape (operatories list) with TODO marker.
- Providers → `/api/providers`.
- Drag/drop reschedule → PUT `/api/appointments/{id}/reschedule` (existing).

## Done when
- No FullCalendar imports in this file.
- Custom 30-min × operatories grid present.
- Provider sidebar with load counts present.
- `cd web && npx next build` green.
