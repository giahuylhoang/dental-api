# Task 2G — admin-greeting.html

Build the greeting page for the AI Receptionist admin prototype.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-greeting.html`.

## Goal

A clinic admin lands on this page to write or edit the agent's spoken greeting. The page mirrors `app/settings/greeting/page.tsx` from `dental-agent/web` (read it for verbatim copy and behavior). Two states are demoable from the mock (see "Demo states" below).

## Behavior

- Reads `window.ADMIN_MOCK.GREETING` for the current record (currently `null`).
- Textarea, autosize-feeling (rows=4 is fine), placeholder verbatim: `Welcome to … How can I help you today?` (U+2026, not three dots).
- Live character counter under textarea: `{n} / 280 characters`. Default ink-muted; warn at >240; red at >280; **disable Save when n>280**.
- Submit button: `Save greeting` / `Saving…` while saving (simulated with a 400ms `setTimeout`).
- Status banner above the form:
  - When `record == null`: amber-toned banner with verbatim text `No custom greeting persisted yet. The agent uses the YAML default until you save one.`
  - When `record.status === 'approved'`: green-toned banner: `Status: approved · approved by <email>` (use `record.approved_by`).
  - When `record.status === 'pending_review'`: amber-toned banner: `Status: pending_review`.
- Engineer approval section (separate panel below the form):
  - `<h2>` text: `Engineer approval`
  - Helper paragraph **verbatim**: `First-time edits land as pending_review. An engineer (email allow-listed in GREETING_APPROVERS) must call /approve once per clinic; after that, edits auto-approve.` — wrap `pending_review`, `GREETING_APPROVERS`, and `/approve` in `<code>` (mono).
  - Button: `Approve clinic (engineer-gated)` / `Approving…` (simulated, 400ms). Disabled when no record yet — tooltip via `title=`: `Save a greeting first; engineers approve a saved record, not a draft.`
- "Hear it back" inline button next to Save — visually present, no real audio. `disabled` with `title="Audio preview is wired in production."` is fine for the prototype.

## Demo states

The mock currently has `GREETING.record = null`. To demo the saved-and-approved state, the page must include a "Demo state" toggle group (small chip row at the top-right of the page header, NOT a top-bar overlay) with three options:

- `No record` — uses `record = null` (default; matches mock).
- `Pending review` — overrides record locally to `{ message: 'Welcome to Northeast Denture Clinic. How can I help you today?', status: 'pending_review' }`.
- `Approved` — overrides record locally to `{ message: 'Welcome to Northeast Denture Clinic. How can I help you today?', status: 'approved', clinic_approved: true, approved_by: 'engineer@rockyridgeai.com' }`.

This toggle is local React state — does NOT mutate `window.ADMIN_MOCK`.

## Layout

- Reuse the `AdminTopBar` pattern from `admin-routing.html` (inline component at top of the page's `<script type="text/babel">` block). Breadcrumb: `['The Receptionist', 'Configuration', 'Greeting']`.
- Page header: overline `Configuration`, title `Greeting`, sub-paragraph (warm but clinical, ≤2 sentences) explaining what callers hear when the AI picks up.
- Single-column layout, `max-width: 760px`, panels stacked.
- Use the same `.panel`, `.field`, `.lbl`, `.d-textarea`, `.btn-primary`, `.btn-ghost`, `.save-bar`, `.info-banner`, `.toggle-row`, `.overline` classes you'll find in `admin-routing.html`. Copy the `<style>` block forward and trim what you don't need.

## Sidebar

`<AdminSidebar active="greeting" ... />`.

## Verbatim strings — every one of these must appear in the rendered DOM

1. `Greeting`
2. `Welcome to … How can I help you today?`
3. ` / 280 characters` (the slash + suffix — the leading number varies)
4. `Save greeting`
5. `Engineer approval`
6. `pending_review`
7. `GREETING_APPROVERS`
8. `/approve`
9. `Approve clinic (engineer-gated)`
10. `No custom greeting persisted yet. The agent uses the YAML default until you save one.`

## Forbidden

Do not modify any other file. Do not change `data/admin_mock.js`. Do not paraphrase any verbatim string above.

## Success criteria

- File written at the path above, ≥4KB and ≤16KB.
- All 10 verbatim strings present (grep test).
- Page-specific `<style>` block at the top.
- `<AdminSidebar active="greeting" ...>` mounted.
- Counter updates live; Save disabled when over 280.
- Demo-state toggle switches the banner among the three states without page reload.
- No `console.error` calls in code; no `eval`; no inline `<script>` blocks beyond what the kit already uses (Babel + the page's `text/babel` block).
- Write `_runbook/_state/02G.done.md` summarising what was produced.
