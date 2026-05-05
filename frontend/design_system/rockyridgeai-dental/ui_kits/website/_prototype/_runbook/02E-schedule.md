# Task 2E — admin-schedule.html

Build the read-only schedule view — what the AI Receptionist booked, alongside what the front desk booked, for the current day.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-schedule.html`.

## Sidebar

`<AdminSidebar active="schedule" ... />`.

## Source of truth

`dental-agent/web/app/schedule/page.tsx`. The current implementation prints raw JSON; this page is the upgrade. The schedule API returns `{ start_date, end_date, fetched_at, cache_ttl_seconds, appointments }`. `appointments[]` shape is loose — pick the shape from `ADMIN_MOCK.APPOINTMENTS`: `{ id, patient_id, patient_name, provider, time_start, time_end, procedure, booked_by: 'ai'|'front_desk', source_call_id }`.

## Page

- Header: overline `Practice`, title `The Schedule`, sub-paragraph clinical, one sentence.
- Helper sentence in slate-dark text: `Today's appointments (read-only).` (verbatim) followed by `Your practice management system is the source of truth.`
- Date picker: simple date input, default today (per `ADMIN_MOCK` clinic timezone — fall back to local `today` for the prototype).
- Cache footer line (mono, small, slate): `Fetched at {now} · cache 30s`.

## Day view

Three-provider day grid:
- Columns: providers from `appointments[*].provider` (deduped), in stable order. If empty: a single column "All providers".
- Time rows: 30-min increments, 09:00 → 19:00 (extend to cover the day's earliest/latest if outside that range).
- Each appointment renders as a card spanning its time range:
  - Patient name (bold, navy-800)
  - Procedure (smaller, slate-dark)
  - "Booked by" pill at top-right: `AI` (steel-100 / steel-800) or `Front desk` (ink-100 / ink-800).
  - Click → `admin-call-detail.html?call_id={source_call_id}` if `booked_by === 'ai' && source_call_id`; otherwise a stub dialog "This appointment was booked by the front desk."

Empty:
- (zero appointments today): `Nothing on the books for this day.`
- (no providers configured): `No providers in the mock yet.`

No edit affordances anywhere — no "+ New", no per-cell click-to-create. This page is read-only by design.

## Verbatim strings

1. `The Schedule`
2. `Today's appointments (read-only).`

## Forbidden

Do not modify `data/admin_mock.js`. Do not add edit/create UI. Do not pull in a calendar library — the day grid is plain CSS grid + absolute positioning.

## Success criteria

- File written at the path above, ≥8KB and ≤25KB.
- Both verbatim strings present.
- Day grid renders against `ADMIN_MOCK.APPOINTMENTS` (currently `[]`; the empty state should show).
- AI-booked vs. front-desk-booked are visually distinct.
- AI-booked cards link to `admin-call-detail.html?call_id=...`.
- `<AdminSidebar active="schedule" ...>` mounted.
- Write `_runbook/_state/02E.done.md`.
