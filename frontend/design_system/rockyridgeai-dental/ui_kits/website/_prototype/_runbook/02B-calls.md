# Task 2B — admin-calls.html

Build the call log page — the AI Receptionist's primary audit surface for the clinic.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-calls.html`.

## Sidebar

`<AdminSidebar active="calls" ... />`.

## Source of truth

`dental-agent/web/app/calls/page.tsx`. Read it for the exact column set and outcome enum semantics. The current implementation is a flat HTML table; the prototype is the upgrade.

## Page

- Header: overline `Reception`, title `The Call Log`, sub-paragraph clinical, one sentence.
- Filter pill bar above the table (build inline, do not extract). Filters:
  - Date range — chips: Today / 7 days / 30 days / Custom (date-range pickers when "Custom" is selected).
  - Outcome — multi-select pill set with all outcome values from `ADMIN_MOCK.CALLS` plus the standard ones: `booked`, `transferred`, `voicemail`, `missed`, `agent_handled`, `routing_gate*`, `error`.
  - After-hours toggle — `Show only after-hours calls` (uses each row's `after_hours` field).
  - Search input — name or phone (formatted), debounced 200ms.
- Counter: `Showing {n} of {total}` to the right of the filters.

## Table columns (in this order)

- **Time** — date + time, mono. Sub-line: relative ("3 hours ago").
- **Caller** — `caller_name` if known, else formatted E.164 (mono). Sub-line: tag from `patient_id` lookup ("New patient" / "Returning").
- **Duration** — formatted `m s` (use `dental-agent/web/app/calls/page.tsx`'s helper as inspiration). Mono.
- **Outcome** — status pill, see Task 2A for the tone map.
- **Appointment** — if `appointment_id` resolves in `ADMIN_MOCK.APPOINTMENTS`: the appointment time + provider on a single line; otherwise em-dash.
- **Listen** — inline mini-player stub (24px circular play button + waveform thumbnail SVG). Visual only; no audio source. Click opens the call-detail page.

Row interactions:
- Hover lifts row bg to off-white.
- Hovering a row shows a "View transcript →" affordance on the far right.
- Clicking the row OR the listen button navigates to `admin-call-detail.html?call_id={call_id}`.

## States

- Loading: skeleton rows (8 rows of grey blocks). Build inline.
- Empty (filters yield 0): `No calls match these filters. Widen the date range or clear an outcome to see more.`
- Empty (zero calls in mock): `No calls yet. The first call we take for you will land here.`

## Pagination

Cursor-style buttons (`Back to first page` / `Next page`) — see source page for the pattern. For the prototype, page-size is 20 client-side; "Next page" advances client offset.

## Verbatim strings

1. `The Call Log`
2. `Recent calls and transcripts.` (use this as the sub-paragraph or place it in the page meta — must appear once)

## Forbidden

Do not modify `data/admin_mock.js`. Do not edit other pages. Do not pull in any external library beyond the kit's existing CDN scripts.

## Success criteria

- File written at the path above, ≥10KB and ≤30KB.
- Both verbatim strings present.
- Table renders against `ADMIN_MOCK.CALLS` (currently `[]` — that's fine; the empty state should show).
- Filter pills are interactive client-side.
- `<AdminSidebar active="calls" ...>` mounted.
- Booked rows have a path/link with `?call_id=` query param.
- Write `_runbook/_state/02B.done.md` summarising what was produced and one screenshot description (text-only) of the rendered empty state for the user to spot-check.
