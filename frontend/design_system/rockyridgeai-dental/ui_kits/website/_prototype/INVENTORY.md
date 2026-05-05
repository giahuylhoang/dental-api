# Phase 0 Inventory — AI Receptionist Admin Prototype

This file is the source of truth for every later task. Do not invent fields, copy strings, or routes that contradict what's recorded here. If something here is wrong, fix it here first, then re-derive downstream.

---

## 1. Design system: how the kit actually works

The design system lives at `rockyridgeai-dental.com/`. Top-level layout:

- `colors_and_type.css` — master tokens (HSL shadcn channels + RR brand vars + utilities). Every page imports this.
- `data/*.js` — demo seed files. Each exposes `window.UPPER_SNAKE` (e.g. `window.PATIENTS`). Pages script-tag-include them via `../../data/<name>.js`.
- `data/index.js` — manifest listing the include order. Owns `window.RRD`.
- `lib/query.js` — small helper utilities, included before page logic; provides `window.RRD.requireSession?.()` auth gate used at the top of each page's `text/babel` block.
- `preview/*.html` — one self-contained reference page per shadcn component / token (badge, dialog, drawer, table, etc.). 65+ entries.
- `ui_kits/website/` — the **PMS prototype** (a different surface from the AI admin prototype we're building). 50+ files: `dashboard.html`, `patients.html`, `schedule.html`, `settings.html`, `lab.html`, `crm.html`, etc., plus their `.jsx` component definitions (`Sidebar.jsx`, `TopBar.jsx`, `KpiTile.jsx`, `DataTable.jsx`, `EmptyState.jsx`, `Drawer.jsx`, `StatusPill.jsx`, etc.). These pages **must not be modified** — the AI admin prototype is additive.

### Page mechanics (HTML + Babel-in-browser, not Next.js)

Every page follows the same pattern:

```html
<!DOCTYPE html><html><head>
  <link rel="stylesheet" href="../../colors_and_type.css">
  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin></script>
  <style>/* page-specific CSS */</style>
</head><body>
  <div id="root"></div>
  <script src="../../data/users.js"></script>
  <script src="../../data/patients.js"></script>          <!-- whichever seeds the page needs -->
  <script src="../../lib/query.js"></script>
  <script type="text/babel" src="Sidebar.jsx"></script>
  <script type="text/babel" src="TopBar.jsx"></script>
  <script type="text/babel">
    window.RRD.requireSession?.();
    /* page render here, mounting into #root */
  </script>
</body></html>
```

JSX components register globally via `Object.assign(window, { ComponentName });` so subsequent `<script type="text/babel">` blocks can reference them.

### Run command

From `INDEX.md`:
```
cd rockyridgeai-dental.com
python3 -m http.server 5180
open http://127.0.0.1:5180/ui_kits/website/index.html
```

### Brand voice (binding for every prototype page)

Per `rockyridgeai-dental.com/README.md`:
- **Authoritative, calm, clinical.** Trusted senior practitioner. Measured. Precise.
- **"We → you" framing.** *We* (Rockyridge) build the engine; *you* (the clinic) run your practice on top.
- **No hype words.** Never "world-class", "cutting-edge", "AI-powered", "smart". Replace with specifics ("schedules 240 patients/day with no double-booking", "OHIP code 23311 lookup").
- **Definite article on system names.** *The Schedule. The Roster. The Lab.* Capitalised, treated as proper nouns. For our surface: *The Receptionist. The Call Log. The Greeting.*
- **No emoji.** Anywhere. Toasts, empty states, copy.
- **Casing.** ALL CAPS section labels with 0.15em tracking. Title Case for CTAs. Sentence case for descriptive copy.

This **overrides** the "warm 40+-reader" voice from my memory (that voice is for the booking subdomain — a different surface).

### Brand colour & typography (use these — do not redefine)

- **Primary** Steel Blue `#3A7FBD` (CTAs, links, focus rings).
- **Secondary** Navy `#0A192F` (sidebar, login, marketing hero).
- **Surface** Warm White `#FAF9F6` (page) · `#FFFFFF` (cards) · Off-White `#F5F2EC` (wash).
- **Ink** `#1C2333` body · `#3D4D61` secondary · `#4A5568` muted.
- **Semantic** Success `#2A7D4F` · Warning `#B45309` · Error `#9B2335` · Info = Steel.
- **Display** Montserrat 600/700/800/900 (-0.03em on display sizes).
- **UI/Body** Inter 300/400/500/600/700.
- **Mono** JetBrains Mono 400/500/600 (IDs, durations, codes, timestamps).
- **Radius** 6px default, 999px pills, 0 sharp blocks.
- **Sweep-fill button** is the signature interaction — `.btn`, `.btn-primary`, `.btn-navy`, `.btn-ghost`, etc.

### Existing components to reuse (do not rebuild)

- `Sidebar.jsx` — the PMS sidebar. **Do not modify.** AI admin prototype gets its own `AdminSidebar.jsx` next to it.
- `TopBar.jsx`, `Avatar.jsx`, `Breadcrumb.jsx`
- `KpiTile.jsx` — KPI tile primitive
- `DataTable.jsx` — sortable data table
- `EmptyState.jsx` — standard empty state
- `Drawer.jsx` — right-side drawer (used in patients, dashboard)
- `StatusPill.jsx` — status badge
- `FilterChips.jsx`, `SearchInput.jsx`, `FormField.jsx`, `Tabs.jsx`
- `MoneyCell.jsx`, `MonoText.jsx`, `IconButton.jsx`
- All shadcn primitives previewed in `preview/*.html`

### Components we still need (LiveKit-borrowed)

These don't exist in the kit yet and need to be added under `components/admin/`:

- `WaveformAudioPlayer` — visual waveform + scrubber + speed selector + click-to-seek; transcript line click → `seek(ms)`.
- `TranscriptPane` — caller vs. agent bubbles, timestamp, confidence chip, autoscroll lock, audio-time highlight.
- `LogTailViewer` — timestamp + level pill + message + JSON expand; pause-autoscroll; level filter; "Jump to live" pill.
- `LatencyTimeline` — per-turn horizontal bars: STT / LLM / tool / TTS, total-ms readout.
- `IntentClassifierStrip` — top-3 intents per turn with confidence bars.
- `AgentFlowMini` — small flowchart highlighting the conversation path.
- `Sparkline`, `TrendChart` — SVG-only, no chart library.
- `TimeRangeRow` — open/close time pickers for the hours-per-weekday grid.
- `ToggleRow` — already styled in `settings.html` (`.toggle-row`); promote to a primitive.

---

## 2. Source of truth: dental-agent/web routes

7 routes total (the user confirmed this is the full set). Note: two of them — call detail and patient detail — only stub-import sibling components that don't exist as files (`./CallDetail`, `./PatientDetail`). For those two, design from product intent, not from existing UI.

### `/` (root) — `app/page.tsx`

- Hero: `<h1>Welcome</h1>` followed by `Signed in as <clinicId>` (font-mono).
- Quick links grid (2 columns @ ≥sm), 5 cards. **Verbatim labels + descriptions** (these match what the user quoted):
  - `/calls` — "Calls" — "Recent calls and transcripts."
  - `/patients` — "Patients" — "CRM rollup from agent calls."
  - `/schedule` — "Schedule" — "Today's appointments (read-only)."
  - `/settings/routing` — "Routing" — "Hours, holidays, transfer rules."
  - `/settings/greeting` — "Greeting" — "Edit the AI greeting message."
- No KPI tiles in current implementation. The "Welcome" page is barren — it's the prototype's biggest opportunity to add ROI metrics.

### `/calls` — `app/calls/page.tsx`

- `<h1>Calls</h1>`.
- Table columns: Started · Caller (E.164, mono) · Duration (m s) · Outcome · Turns · Patient (yes/no) · open-link.
- Outcome values seen in code: `agent_handled` (green), `routing_gate*` (amber, prefix-matched), `error` (red), other (ink-grey). **These are the real outcome strings — preserve in mock.**
- Pagination via cursor: "Next page" / "Back to first page".
- Empty state: "No calls yet."
- Loading: "Loading…". Error rendered via `ErrorBox`.
- API: `callsApi.list(clinicId, token, { limit: 25, cursor })` → `{ items, next_cursor }`.

### `/calls/[callId]` — `app/calls/[callId]/page.tsx`

**Imports `./CallDetail` which does not exist as a file.** No source-of-truth UI. Design from product intent:
- Caller card (left rail)
- Audio player + transcript (main)
- Logs / latency / intents / flow (right rail, collapsible engineer view)

### `/patients` — `app/patients/page.tsx`

- `<h1>Patients</h1>`.
- Filters: Search (name/phone/email), Tag, Status select.
- **Status enum (verbatim, in this order):** `''` (any), `new`, `contacted`, `booked`, `completed`, `lost`. Default UI label for empty: "any status".
- Table columns: Name · Phone (mono) · Status · Tags · Last contact · open-link.
- Empty state: "No patients match."
- API: `patientsApi.list(clinicId, token, { q, tag, status, limit: 25, cursor })`.

### `/patients/[patientId]` — `app/patients/[patientId]/page.tsx`

**Imports `./PatientDetail` which does not exist as a file.** Design from product intent. Out of scope for the 7 confirmed prototype pages — patient detail is **not** in the user's confirmed list, so do not build it. (Patients page row → side drawer with mocked rollup is sufficient for the prototype, mirroring the existing `patients.html` Drawer pattern.)

### `/schedule` — `app/schedule/page.tsx`

- `<h1>Schedule</h1>`.
- Filters: Date (date input, defaults to today), Days (number 1-14, defaults to 1).
- Footer line: `{start_date} → {end_date} · fetched {time} (cache {n}s)`.
- Body: appointments rendered as **raw JSON pre block** (current implementation — this is one of the most "raw" surfaces; the prototype is the upgrade).
- Empty state: "No appointments in this window."
- API: `scheduleApi.get(clinicId, token, { date, days })` → `{ start_date, end_date, fetched_at, cache_ttl_seconds, appointments }`. The schema of `appointments[]` is not enforced in the page — it's printed as JSON. Mock should pick a sensible shape: `{ id, patient_name, provider, time_start, time_end, procedure, booked_by: 'ai' | 'front_desk' }`.

### `/settings/routing` — `app/settings/routing/page.tsx`

**Verbatim copy strings (every one of these must appear in the prototype DOM):**

- `<h1>Routing</h1>`
- `Timezone` — text input, default `America/Edmonton`, mono.
- `Ring timeout (seconds)` — number, **default 20** (NOT 5 as my plan first had — corrected from source).
- `Front desk numbers (comma-separated, E.164)` — text, mono.
- `Backup number (optional)` — text, mono.
- `AI SIP URI (read-only here; engineer-managed)` — read-only mono input, ink-50 bg.
- Section heading: `Hours per weekday`. 2-col grid of 7 rows (mon/tue/wed/thu/fri/sat/sun, lowercase, uppercased visually). Each row: `<weekday> <time-input> → <time-input>`.
- Helper under hours grid: `Both blank means closed that day.`
- `Holidays (YYYY-MM-DD, one per line)` — textarea, mono, rows=3.
- Two checkboxes:
  - `AI handles after-hours calls` (default `true`)
  - `AI handles in-hours overflow` (default `true`)
- Submit button: `Save routing` / `Saving…`. Disabled when not admin.
- Read-only banner (non-admin): `Read-only — your role is <role>.`
- Section: `<h2>Preview</h2>`
- Helper: `What would the agent do at a given moment, against the currently saved rules? (Save first if you want to preview a draft.)` — note the literal italics on "currently saved".
- Preview controls:
  - `When (your local TZ)` — datetime-local input.
  - `Assume AI healthy` — checkbox, default checked.
  - Button: `Preview`.
- Preview output card (when `preview` set):
  - `at: <iso>` (mono)
  - `action: <decision.action>` (medium weight)
  - `reason: <decision.reason>`
  - `front desk: <numbers joined>` (mono, only when non-empty)

**Defaults (`blankConfig` in source):**
```
{ timezone: 'America/Edmonton', dids: [], front_desk_numbers: [],
  ring_timeout_seconds: 20, hours: {}, holidays: [],
  ai_after_hours: true, ai_in_hours_overflow: true,
  backup_number: null, ai_sip_uri: null }
```

### `/settings/greeting` — `app/settings/greeting/page.tsx`

**Verbatim copy strings:**

- `<h1>Greeting</h1>`
- `MAX = 280` characters. (Soft cap — `maxLength={MAX + 50}` allows a small overshoot so the counter can flag it.)
- StatusBanner when no record: `No custom greeting persisted yet. The agent uses the YAML default until you save one.` (amber-50 bg, amber-200 border, amber-800 text).
- StatusBanner when record exists: `Status: <status> · approved by <approved_by>`. Status `approved` → green tones; otherwise → amber tones.
- Textarea placeholder: `Welcome to … How can I help you today?` (`…` is U+2026, not three dots).
- Counter under textarea: `<n> / 280 characters`. Red when `n > 280`.
- Submit button: `Save greeting` / `Saving…`. Disabled when not admin.
- Read-only message (non-admin): `Read-only — your role is <role>.`
- Section: `<h2>Engineer approval</h2>`
- Helper: `First-time edits land as pending_review. An engineer (email allow-listed in GREETING_APPROVERS) must call /approve once per clinic; after that, edits auto-approve.` (`pending_review`, `GREETING_APPROVERS`, `/approve` are mono.)
- Approve button: `Approve clinic (engineer-gated)` / `Approving…`. Disabled when no record yet.

### `/login` — `app/login/page.tsx`

- `<h1>Sign in</h1>` — small (`text-lg`).
- Email + password fields, submit `Sign in` / `Signing in…`.
- Footer: `New users: ask an engineer to run grant-clinic-access.py first.` (mono on the script name).
- The kit's `login.html` is **dark-theme** and stays as-is. The dental-agent login is light-theme. We will not duplicate login — the prototype assumes the kit's `login.html` redirects to the new admin dashboard.

---

## 3. Real production values quoted by the user (capture in mock)

These came from the user's previous message and match what `dental-agent/web` displays for Northeast Denture Clinic. Mock should default to these so the prototype demos with a coherent, real-feeling configuration:

- Clinic: `northeast-denture-clinic`
- Timezone: `America/Edmonton`
- Ring timeout: `5` (user has 5 in production; defaults to 20, but their saved value is 5 — store 5 in mock)
- Front desk numbers: `+15879738089`
- Backup number: `+13682990959`
- AI SIP URI: `sip:34.130.210.160:5060`
- Hours: mon 09:00→17:00 · tue 09:00→17:00 · wed 09:00→19:00 · thu 09:00→19:00 · fri 09:00→14:00 · sat 09:00→18:00 · sun closed
- Holidays: empty
- AI handles after-hours calls: on
- AI handles in-hours overflow: on
- Greeting: not yet persisted (status banner is "No custom greeting persisted yet. The agent uses the YAML default until you save one.")

---

## 4. LiveKit reference inventory

`livekit_site/` is empty besides an `index.html` and a `projects/` dir. The actual material lives in `mhtml_unpacked/` — 94 directories, each named for a LiveKit Cloud route. Most-relevant for our admin dashboard:

- `projects_p_..._sessions` — sessions list (the LiveKit equivalent of our calls list). Borrow: column layout, status badges, time formatting, filter pill bar.
- `projects_p_..._sessions_RM_<id>` (× ~10) — session detail. Borrow: 3-pane layout, header with session metadata.
- `projects_p_..._sessions_RM_<id>_events` — per-session events feed. Borrow: log tail / event row patterns.
- `projects_p_..._sessions_RM_<id>_observability` — latency/observability per session. Borrow: latency timeline, intent confidence bars, structured key/value cards.
- `projects_p_..._sessions_RM_<id>_participants_PA_<id>` — participant detail with audio waveform. Borrow: audio waveform + scrubber + transcript-style log layout.
- `projects_p_..._agents_console_*` — agent config console. Borrow: agent settings form layout (only the form patterns; do not borrow the room/participant metaphor — clinics don't think in those terms).
- `projects_p_..._overview*` — project overview with KPI tiles + time-series chart. Borrow: KPI row, line chart, sparkline.

**Avoid carrying over:** room names, participant IDs, dispatch metaphors, SDK-installation panels, anything labelled "egress" / "ingress" / "sandbox templates" — clinics don't think in those terms and the user explicitly wants this clinic-friendly.

---

## 5. Open questions surfaced by inventory (need user answer before code)

1. **Voice direction.** Memory says "warm, plainspoken, reassurance-led, 40+ readers" — but that memory is tagged for **Market Mall booking subdomain**. The design system's own README mandates **"Authoritative, calm, clinical. No hype. Definite-article system names."** The admin dashboard is a clinical operator surface, not a patient-facing booking surface, so **clinical voice wins**. Confirm before writing copy.

2. **Sidebar approach.** The kit's `Sidebar.jsx` (Dashboard / Patients / Schedule / Treatment / Lab / Billing / Communications / CRM / Reports / Settings) is a full-PMS sidebar. The admin dashboard is a smaller surface (Dashboard / Calls / Patients / Schedule / Routing / Greeting). Three options:
   - (A) Build a separate `AdminSidebar.jsx` for the AI admin prototype, navy-themed, used only by admin pages. Existing Sidebar untouched. **Recommended** — matches the user's memory ("don't alter nav links") and the product reality (admin app is a separate hosted surface).
   - (B) Add an "AI Receptionist" group to the existing Sidebar containing Calls / Routing / Greeting. Patients/Schedule are shared. Risk: muddles two products into one chrome.
   - (C) Tabs under Settings for Routing/Greeting + a new top-level "Calls" entry. Worst of both worlds.

3. **Avg case value** for the dashboard's "Estimated revenue captured" KPI (proves AI ROI). Need a single number for the mock — placeholder $385 (denture-fit-leaning) but the user knows their average case value.

4. **Audio fixtures.** Drop 1–2 royalty-free dental-receptionist sample MP3s under `_prototype/_assets/audio/` for the player demo, or have the player be visually-only (no `src`)? The waveform component renders identically either way; only the play button is functional with a real source.

5. **Patient detail page.** `/patients/[patientId]` exists in routes but its `PatientDetail` component is missing. Stick with the user's confirmed 7-page list (no patient detail page; row-click drawer instead) or add `patient-detail.html` to fill the gap?

---

## 6. Updated build plan (corrections)

Based on the inventory, several plan items need correction before any task fires:

- **Pages that already exist** in the kit and must not be duplicated: a separate kit-level `dashboard.html`, `patients.html`, `schedule.html`, `settings.html`. The AI admin prototype creates parallel pages with **distinct filenames**:
  - `_prototype/admin-dashboard.html` (NOT `dashboard.html`)
  - `_prototype/admin-calls.html`
  - `_prototype/admin-call-detail.html`
  - `_prototype/admin-patients.html` (parallel to kit's `patients.html`, owned by AI admin sidebar)
  - `_prototype/admin-schedule.html`
  - `_prototype/admin-routing.html`
  - `_prototype/admin-greeting.html`
- **Existing primitives to reuse** (do NOT add to `components/admin/`): `KpiTile.jsx`, `DataTable.jsx`, `EmptyState.jsx`, `Drawer.jsx`, `StatusPill.jsx`, `FilterChips.jsx`, `FormField.jsx`, `SearchInput.jsx`, `Tabs.jsx`, `Avatar.jsx`, `Breadcrumb.jsx`, `IconButton.jsx`, `MoneyCell.jsx`, `MonoText.jsx`.
- **New components to add** (only these): `AdminSidebar.jsx`, `WaveformAudioPlayer.jsx`, `TranscriptPane.jsx`, `LogTailViewer.jsx`, `LatencyTimeline.jsx`, `IntentClassifierStrip.jsx`, `AgentFlowMini.jsx`, `Sparkline.jsx`, `TrendChart.jsx`, `TimeRangeRow.jsx`, `ToggleRow.jsx` (extracted from `settings.html` inline styles).
- **Mock data goes at** `data/admin_mock.js` (top-level `rockyridgeai-dental.com/data/`, not `ui_kits/website/data/` — the kit uses `../../data/` relative paths). Exposes `window.ADMIN_MOCK`.
- **Page CSS** lives in inline `<style>` per page (kit convention) — there is no separate `admin.css`. Tokens already in `colors_and_type.css`.
- **Smoke tests** assume `python3 -m http.server 5180` is the dev server. Playwright targets `http://127.0.0.1:5180/ui_kits/website/_prototype/<page>.html`.

These corrections supersede the plan at `/Users/giahuyhoangle/.claude/plans/valiant-coalescing-wand.md` where they conflict.
