# T09 — /schedule

## Objective
FullCalendar-driven schedule with drag-to-reschedule + NewAppointmentDialog.

## References
- Visual: `ui_kits/website/schedule.html`, `appointment-detail.html`
- Logic: `frontend/src/features/scheduling/{Scheduler,Calendar,AppointmentDrawer,NewAppointmentDialog,DateTimePicker}.tsx`

## Implementation
- `web/app/(app)/schedule/page.tsx` (`"use client"`).
- Use `FullCalendar` from `@/components/layout/DynamicCalendar` with plugins: daygrid, timegrid, interaction.
- Provider + service filters (multi-select).
- Drag-to-reschedule: PUT `/api/appointments/{id}/reschedule` (preserve current behavior).
- New appointment: dialog wraps shadcn Dialog → POST `/api/appointments`.
- Click event → AppointmentDrawer (Sheet) with cancel/reschedule actions.

## Verify
```
cd web && npx tsc --noEmit && npx next build
```
