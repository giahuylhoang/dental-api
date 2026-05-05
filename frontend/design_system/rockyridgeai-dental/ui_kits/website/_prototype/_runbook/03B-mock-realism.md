# Task 3B — Mock data realism pass

Make `window.ADMIN_MOCK` tell a coherent story. After this task, navigating the prototype should feel like a real clinic — bookings on the schedule match calls in the log; KPI counts on the dashboard equal filter counts on the calls page; transcripts make sense for the calls they belong to.

## Output

Modify exactly one file: `data/admin_mock.js`.

## Constraints

- Do not change the **shape** of any field that other pages already read. You may add fields (e.g. `appointment_summary` on a call), but every key currently referenced by `admin-routing.html`, `admin-greeting.html`, `admin-dashboard.html`, etc. must continue to exist with the same name.
- Do not change the clinic identity (`CLINIC.slug`, `CLINIC.name`, `CLINIC.timezone`, `CLINIC.avg_case_value_cents`) or the routing values quoted from production (`ROUTING.*`). Those are user-set ground truth.

## Generate

Anchor everything to **today** (use a function that produces ISO timestamps relative to `new Date()` at file-load time so re-loading the prototype always shows fresh "this month" data).

### Patients (12 entries)

40+-skewed first names, mixed Edmonton-area surnames. Each has:
- `patient_id` — slug like `pt_<6-char>`
- `first_name`, `last_name`
- `phone_e164` — `+1587…` or `+1780…`
- `email` — optional, ~60% have one
- `lead_status` — distribution: 3 `new`, 3 `contacted`, 4 `booked`, 1 `completed`, 1 `lost`
- `tags` — at least one of: `denture-fitting`, `recall`, `new-patient`, `emergency`, `consult`
- `last_contact_at` — within last 14 days
- `total_calls` — integer 1–6
- `notes` — short clinical-voice paragraph

### Calls (32 entries across 14 days)

Each:
- `call_id` — `call_<8-char>`
- `started_at` — ISO timestamp distributed across the past 14 days. Skew toward 08:00–10:00 and 16:00–18:00, with a small after-hours cluster wed/thu evenings.
- `caller_e164` — pulls from a patient (most calls) or a new number (~15%)
- `caller_name` — patient's name when matched, else null
- `patient_id` — patient ref or null
- `duration_seconds` — 30–360s, weighted toward 90–180s
- `outcome` — distribution exactly: 14 `booked`, 8 `transferred`, 5 `voicemail`, 3 `missed`, 2 `agent_handled` (resolved without booking)
- `transcript_turns` — integer 4–22
- `has_patient` — derived (`patient_id != null`)
- `after_hours` — derived from `ROUTING.hours` and `started_at` in clinic TZ
- `appointment_id` — for each `booked` call, refers to the `APPOINTMENTS` row created for it

### Appointments (today's schedule, 14 entries)

Each:
- `id` — `apt_<6-char>`
- `patient_id` (and `patient_name`)
- `provider` — pick from: `Dr. Hau Le`, `Dr. Sara Osei`, `Hygienist Maya`
- `time_start`, `time_end` — ISO strings on today; durations 30–90 min; cluster around 09:00–17:00
- `procedure` — strings like "Denture fit-and-adjust", "Recall + hygiene", "Implant consult", "Crown delivery"
- `booked_by` — for 9 of 14 → `'ai'`; remaining 5 → `'front_desk'`
- `source_call_id` — for AI-booked: the call_id of the booking call (must exist in CALLS and have outcome `booked`)

### Transcripts (3 fully-written, plus stubs for the rest)

Three `TRANSCRIPTS` entries (one for each of three different `booked` calls — pick a short, medium, and long call):

- **Short** (~6 turns): caller asks for nearest available appt; AI offers; caller accepts.
- **Medium** (~12 turns): caller has a partial denture issue, AI asks clarifying questions, books a fit-and-adjust.
- **Long** (~22 turns): caller is comparison-shopping, asks pricing/insurance/timing, AI navigates and books a consult.

Each turn:
- `t` — ms offset from call start
- `speaker` — `caller` | `agent`
- `text` — clinical, not breathless. Caller can be casual; agent is calm, "we → you", no emoji, no exclamation points.
- `confidence` — float 0.0–1.0; mostly 0.85+ with a few 0.4–0.6 dips
- `intents` — top-3, each `{ name, score }`. Names: `book_appointment`, `cancel_appointment`, `ask_pricing`, `ask_hours`, `confirm_address`, `transfer_to_human`, `ask_provider_availability`, `general_information`, etc.
- `latency_ms` — `{ stt, llm, tool, tts, total }` — total 600–2200ms; tool-call turns higher.

For each transcript: a sibling `logs[]` array (mock observability). Each log: `{ ts_ms, level: 'info'|'warn'|'error', message, payload }`. Mix in a couple of warn-level entries about partial-confidence intents; one error-level entry tied to a fallback if appropriate. Also include `flow_path`: an ordered array of the conversation states traversed (e.g. `['greet', 'identify_caller', 'check_schedule', 'offer_slots', 'confirm', 'book']`).

For the other ~11 booked calls: omit transcripts (the call-detail page generates fallbacks).

### KPIs

Compute from the data above so dashboard counts == filter counts:

- `period_label`: 'This month' (or fixed string)
- `bookings.value`: count of calls with `outcome === 'booked'` (== 14)
- `revenue_captured_cents.value`: 14 × `CLINIC.avg_case_value_cents` (== `91000 00` cents = $9100; render as $9,100 in pages)
- `after_hours_revenue_cents.value`: count of `booked` calls where `after_hours === true` × avg case value
- `front_desk_hours_saved.value`: sum of `duration_seconds` for non-`missed` calls / 3600, rounded to one decimal
- `calls_handled.value`: total non-`missed` (== 29 if 3 missed)
- `calls_handled.in_hours` / `after_hours`: derived split
- `resolution_rate_pct.value`: `(booked + agent_handled) / (booked + agent_handled + transferred + voicemail)` × 100
- `missed_call_recovery_pct.value`: `non_missed / total` × 100
- `avg_response_seconds.value`: pick a believable number (e.g. 1.4s)

For each KPI, populate `delta_pct` with a plausible value (e.g. `+12`, `−3`).

### Sparklines (for KPI tiles)

For each sparkline key in `KPIS.sparklines`, fill a 14-element array with day-by-day values that, when summed, equal the KPI's `value` (where applicable).

### Trend chart

Fill `KPIS.trend_14d` with 14 entries: `{ date: 'YYYY-MM-DD', calls, booked }`. The sums must equal the corresponding KPI counts.

## Quality gate

After writing, the file should self-validate. Add a small invariants block at the bottom of `admin_mock.js`:

```js
(function validateAdminMock() {
  const m = window.ADMIN_MOCK;
  console.assert(
    m.KPIS.bookings.value === m.CALLS.filter(c => c.outcome === 'booked').length,
    'KPI bookings mismatch'
  );
  console.assert(
    m.KPIS.bookings.value === m.APPOINTMENTS.filter(a => a.booked_by === 'ai').length,
    'AI-booked appointments mismatch booked calls'
  );
  console.assert(
    m.KPIS.trend_14d.reduce((s, d) => s + d.booked, 0) === m.KPIS.bookings.value,
    'Trend booked sum mismatch'
  );
})();
```

## Forbidden

- Do not modify any prototype page — only `data/admin_mock.js`.
- Do not invent verbatim copy strings from settings/routing/greeting — those are owned by the page tasks.
- Do not include emoji in any string.

## Success criteria

- File rewritten with all collections populated.
- The three `console.assert` invariants pass on page load (no warning in browser console).
- 14 `booked` calls, 9 of which produced AI-booked appointments today (with the other 5 today's appointments being front-desk-booked).
- 3 fully-written transcripts present.
- Write `_runbook/_state/03B.done.md` summarising counts and any invariant near-misses.
