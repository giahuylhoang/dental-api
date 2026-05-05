# Task 2A — admin-dashboard.html

Build the AI Receptionist overview dashboard. This is the first page a clinic admin sees after sign-in — it must prove the agent is paying for itself in three seconds.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-dashboard.html`.

## Sidebar

`<AdminSidebar active="dashboard" ... />`.

## Sections (top to bottom)

### 1. Page header

- Overline: `Reception`
- Title: `The Receptionist`
- Sub-paragraph: clinical voice, one sentence — what this surface does. Example: "Every call we took for you, what we did with it, and how much front-desk time you got back this period."

### 2. ROI KPI row (6 tiles, 2 rows × 3 columns @ ≥1024px; auto-fit on smaller)

Money/outcome (lead with these):
- **Estimated revenue captured** — booked count × `CLINIC.avg_case_value_cents`. Render as `$X,XXX`. Sub-caption: `From {bookings} bookings this period.`
- **After-hours revenue captured** — bookings outside business hours × avg case value. Sub-caption: `Revenue you'd have lost without overnight coverage.`
- **Front-desk hours saved** — total handled-call seconds / 3600. Sub-caption with $ equivalent at `CLINIC.front_desk_hourly_cost_cents`.

Operational:
- **Bookings** — count + delta vs last period.
- **Resolution rate** — percent calls resolved without front-desk transfer.
- **Missed-call recovery** — percent of inbound calls that would have gone to voicemail but got answered.

Each tile (build inline, do not extract a component):
- Overline (label): ALL CAPS, 0.62rem, 0.14em tracking
- Big number: Montserrat 700, ~2rem, navy-800
- Delta chevron + percent next to number, semantic green/red
- Inline SVG sparkline (build inline as SVG path — no chart library), height 28px, light steel stroke
- Plainspoken caption below, 1 sentence

### 3. Trend chart (full-width panel, 14-day)

- SVG line chart, two series: `calls` (steel blue stroke) and `booked` (navy stroke).
- X-axis: 14 day ticks. Y-axis: gridline at 25/50/75/100% of max.
- Hover (or focus) → tooltip showing date + both values.
- Source data: `KPIS.trend_14d`. If empty, render an empty-state caption: `Trend renders as soon as 14 days of calls land in the log.`

### 4. Quick links — five cards in a 2-col grid (verbatim)

Use the exact strings from `dental-agent/web/app/page.tsx`:

- **Calls** — `Recent calls and transcripts.` → `admin-calls.html`
- **Patients** — `CRM rollup from agent calls.` → `admin-patients.html`
- **Schedule** — `Today's appointments (read-only).` → `admin-schedule.html`
- **Routing** — `Hours, holidays, transfer rules.` → `admin-routing.html`
- **Greeting** — `Edit the AI greeting message.` → `admin-greeting.html`

Card styling: hover lifts border to steel, no other ornamentation.

### 5. Recent calls mini-table

Last 5 calls from `ADMIN_MOCK.CALLS` sorted by `started_at` desc. Columns: Time · Caller · Duration · Outcome (status pill) · Booked? (link to `admin-call-detail.html?call_id={id}` if outcome is "booked"). Footer link: `See all calls →` → `admin-calls.html`.

If `ADMIN_MOCK.CALLS.length === 0` (current state — Task 3B fills it): render the empty state: `The first call your AI takes will land here. Nothing to set up.`

## Status pills (inline component, not extracted)

Map outcome → tone:
- `booked` → green-100 bg, green-800 text
- `transferred` → steel-100 bg, navy-800 text
- `voicemail` → ink-100 bg, ink-700 text
- `missed` → amber-100 bg, amber-800 text
- `agent_handled` → green-100 (same as booked but lighter)
- `routing_gate*` (any prefix) → amber-100
- `error` → red-100 bg, red-800 text

## Verbatim strings — every one of these must appear in the rendered DOM

1. `The Receptionist`
2. `Recent calls and transcripts.`
3. `CRM rollup from agent calls.`
4. `Today's appointments (read-only).`
5. `Hours, holidays, transfer rules.`
6. `Edit the AI greeting message.`

## Forbidden

Do not modify `data/admin_mock.js`. Do not edit any existing kit page. Do not paraphrase any verbatim string. Do not pull in a chart library.

## Success criteria

- File written at the path above, ≥10KB and ≤40KB.
- All 6 verbatim strings present.
- 6 KPI tiles render with currently-zero values from mock (Task 3B fills the numbers — your job is layout + logic).
- Empty states present for both the trend chart and the recent-calls table.
- `<AdminSidebar active="dashboard" ...>` mounted.
- Sparklines and trend chart are SVG-only (no `import` of a chart library).
- Write `_runbook/_state/02A.done.md` summarising what was produced.
