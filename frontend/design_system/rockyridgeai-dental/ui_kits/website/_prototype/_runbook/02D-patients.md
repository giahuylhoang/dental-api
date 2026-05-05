# Task 2D — admin-patients.html

Build the AI Receptionist's CRM rollup — every caller the agent has spoken to, with the option to drill into their call history without leaving the page.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-patients.html`.

## Sidebar

`<AdminSidebar active="patients" ... />`.

## Source of truth

`dental-agent/web/app/patients/page.tsx`. Note the lead status enum (verbatim, in this order): `''` (any), `new`, `contacted`, `booked`, `completed`, `lost`. Default UI label for the empty value: `any status`.

## Page

- Header: overline `Practice`, title `The Roster`, sub-paragraph clinical, one sentence — frame this as "every caller, not yet a chart entry".
- Sub-helper paragraph (smaller, slate-dark): `CRM rollup from agent calls.` — verbatim.
- Filter bar (inline, do not extract):
  - Search input — name / phone / email, placeholder "Search name, phone, or email".
  - Tag input — single text field, label "Tag".
  - Status select — labels: `any status`, `new`, `contacted`, `booked`, `completed`, `lost`. Default `any status`.

## Table columns

- **Name** — `first_name last_name` or em-dash.
- **Phone** — formatted E.164 (mono).
- **Status** — status pill (color-mapped: new → steel, contacted → ink, booked → green, completed → green-700, lost → ink-300).
- **Tags** — comma-separated, small pills. Empty → em-dash.
- **Last contact** — date (locale-formatted), with relative sub-line.
- **Calls** — total call count, mono.
- (open) — link icon at row end.

Row click opens the patient drawer (right-side, slides in 350ms). The drawer shows:

- Header: name + phone + status pill, close button.
- Tabs: `Overview`, `Calls`, `Appointments`, `Notes` (read-only).
  - Overview: contact card (phone, email, last contact, total calls), tags as pills.
  - Calls: table mirroring the call log columns, filtered by `patient_id`. Clicking a row → `admin-call-detail.html?call_id={id}`.
  - Appointments: table from `ADMIN_MOCK.APPOINTMENTS` filtered by `patient_id`. Each row links to `admin-schedule.html?date={date}`.
  - Notes: read-only block of `notes` field; if empty, "No notes yet."

## States

- Empty (zero patients): `Your patient list builds itself as we take calls. Once a few come in, you'll see them here, with every conversation linked.`
- Empty (filters yield 0): `No patients match. Try clearing a filter.`
- Loading: 8 skeleton rows.

## Verbatim strings

1. `The Roster`
2. `CRM rollup from agent calls.`
3. `any status`

## Forbidden

Do not modify `data/admin_mock.js`. Do not edit other pages. Do not borrow the existing kit's `Drawer.jsx` — write a small inline drawer component instead (the existing one is owned by the PMS prototype and we keep them isolated).

## Success criteria

- File written at the path above, ≥10KB and ≤30KB.
- All 3 verbatim strings present.
- Drawer opens on row click and closes on backdrop click / ESC.
- Tabs switch without unmounting the drawer.
- Empty states present.
- `<AdminSidebar active="patients" ...>` mounted.
- Write `_runbook/_state/02D.done.md`.
