# Task 2C — admin-call-detail.html

Build the per-call detail page — the heaviest page in the prototype. This is where a clinic owner audits one call: listens to the audio, reads the transcript, and (optionally) opens the engineer view to see exactly what the AI did.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-call-detail.html`.

## Sidebar

`<AdminSidebar active="calls" ... />`.

## Note on source

`dental-agent/web/app/calls/[callId]/page.tsx` imports `./CallDetail` which **does not exist as a file**. There is no source-of-truth UI to mirror — design from product intent. The shape of the right rail (the engineer view) borrows from LiveKit's session-detail pattern surveyed in `INVENTORY.md`.

## Routing

Read `?call_id={id}` via `window.RRD.query('call_id')`. Look the call up in `ADMIN_MOCK.CALLS`; transcript/logs/latency in `ADMIN_MOCK.TRANSCRIPTS[call_id]`. If not found, render: header "Call not found." + back-link to `admin-calls.html`.

## Layout

Three-pane:
- **Left rail** (240px): caller card + outcome card.
- **Main** (flex): waveform + transcript.
- **Right rail** (320px, collapsible): engineer view.

@ <1024px: stack vertically (left → main → right). The right rail becomes a collapsible disclosure with summary "Open the engineer view".

### Left rail — caller + outcome cards

- Caller card: avatar (initials), full name (or formatted phone), phone number (mono), call time + duration, status pill.
- Outcome card: dynamic per outcome.
  - `booked`: panel headed "Booked an appointment" with the resolved appointment row (provider, time, procedure) and a link to `admin-schedule.html?date={date}`.
  - `transferred`: panel headed "Transferred to front desk" with which front-desk number rang.
  - `voicemail`: panel headed "Sent to voicemail" with link to a (mock) voicemail recording.
  - `missed`: panel headed "Caller hung up before pickup".
  - `agent_handled`: same as `booked` if appointment exists, else "Resolved without booking" + the agent's summary.
- Patient match panel: "Matched to existing patient" (link to `admin-patients.html?patient_id={id}`) or "New patient" (with phone).
- Action menu: Mark for review · Add note · Listen later. Visual only; clicking opens a stub `<dialog>` with "Coming soon".

### Main pane — audio + transcript

- **Waveform audio player** (build inline): SVG path that draws a randomized but deterministic waveform from the call_id (use a hashing function on the call_id to seed). Above: total duration, current-time indicator, play/pause icon button (visual only — no real audio), 1× / 1.25× / 1.5× / 2× speed pill row. Click on the waveform "seeks" — emits an event consumed by the transcript pane.
- **Confidence summary chip** above the transcript: "Confident on {high} of {total} turns" — derive from `transcripts[call_id].turns[*].confidence > 0.75`.
- **Transcript pane**: caller bubbles right-aligned (steel border), agent bubbles left-aligned (parchment border). Each bubble shows: speaker label, text, timestamp (mono), confidence chip when <0.6 (warn). Clicking a bubble "seeks" the audio (visual only — moves the playhead indicator on the waveform).
- Empty transcript: "This call ended before either side spoke. The audio above is the full record."

### Right rail — engineer view (collapsible)

Header copy (clinical, but acknowledges the audience split): `This is the engineer view. Open it if you want to see exactly what we were thinking. You don't have to.`

Sections (vertical accordion, all collapsed by default):

1. **Latency timeline** — per turn, horizontal bars: STT / LLM / tool / TTS, total ms readout. Hover shows segment ms.
2. **Intent classifier** — per turn, top-3 intents with confidence percentage bars.
3. **Agent flow** — small SVG flowchart (greet → identify → check schedule → book / transfer / voicemail). Highlight the path this call took.
4. **Logs** — log tail with: timestamp (mono), level pill (info / warn / error), message. Expand-arrow on each row reveals the JSON payload.

Default state: collapsed on @≥1024px (a thin tab labelled "Under the hood"). On smaller screens it stacks below the main pane as a disclosure.

## Verbatim strings

1. `Under the hood` (the engineer-view label)

(That's the only required verbatim — most copy on this page is original product copy you write in clinical voice.)

## Mock fallbacks

If `ADMIN_MOCK.TRANSCRIPTS[call_id]` is missing for a real call_id, generate a deterministic 6-turn transcript on the fly using the call's `caller_name` (or formatted phone) and a fixed scheduling-script template. Render the same waveform/transcript/log shapes; this keeps the prototype navigable while Task 3B is still pending.

## Forbidden

Do not modify `data/admin_mock.js`. Do not pull in a chart or audio library. Do not paraphrase the verbatim string. Do not produce real audio playback (visual only).

## Success criteria

- File written at the path above, ≥18KB and ≤55KB (this page is bigger).
- The verbatim string `Under the hood` is present.
- Three-pane layout at ≥1024px, single-column at <1024px.
- Waveform renders for any `?call_id=`, including missing IDs (uses fallback).
- Right rail collapses to a tab and re-opens on click.
- `<AdminSidebar active="calls" ...>` mounted.
- Write `_runbook/_state/02C.done.md` summarising what was produced and noting which mock IDs you generated fallback transcripts for.
