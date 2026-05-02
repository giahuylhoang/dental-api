# PMS Module F1 — Communications: threaded UX + organized compose (TDD)

Make `make test-pms-f1` exit 0.

## Why

`/communications` today shows a flat list pulled from an empty `commsDb`, and ComposeDialog asks for raw "Patient ID" + bare "To" string. F0 already seeded ~30 messages threaded across 3 channels and added `thread_key`, `read_at`, the mark-read endpoint. F1 makes the UI worthy of that data.

## OSS

- `@tiptap/react`, `@tiptap/pm`, `@tiptap/starter-kit` (MIT) — rich text in compose body.

## Success criteria

- `/communications` is a two-pane layout:
  - **Left: ThreadList** — one row per `(patient × channel)` thread (group `commsDb` by `thread_key`). Row shows: patient name, channel icon (📱 SMS / ✉️ email / 💬 whatsapp), last-message preview (~60 chars), relative time, unread badge (count of `read_at = null` inbound messages).
  - **Right: ThreadDetail** — selected thread renders chat-style bubbles (outbound right-aligned zinc-900 bg, inbound left-aligned zinc-200 bg). Each bubble shows time + status indicator. Auto-marks read on open via `PATCH /api/v2/communications/threads/:thread_key/read`.
- Channel filter chips above ThreadList: All / SMS / Email / WhatsApp.
- **ComposeDialog redesign:**
  - "To: Patient" — typeahead autocomplete over `/api/patients?q=`. Replaces the raw "Patient ID" input. Stores both `patient_id` and the resolved patient object.
  - "Channel" — segmented control with icons (3 pill buttons in a single rounded container).
  - When channel changes, the recipient `to` field auto-resolves from the patient: `patient.phone` for `sms` / `whatsapp`, `patient.email` for `email`. Editable but pre-filled.
  - Body uses `@tiptap/react` with `StarterKit` (bold, italic, lists). Submit serializes to plain text via `editor.getText()`.
  - Submit POSTs `/api/v2/communications/send` with `{patient_id, channel, body, to}`.
- "Reply" button on inbound message bubble → opens compose pre-filled with the inbound's `patient_id`, `channel`, and `from` (as `to`).

## Tests first (`frontend/tests/track_pms_f1/`)

1. **`thread-list-renders.test.tsx`** — wrap with QueryClient + MSW seed of 6 messages across 3 threads; assert ≥3 thread rows render with channel icons + at least one unread badge.

2. **`compose-patient-autocomplete.test.tsx`** — open ComposeDialog; type "ali" in patient field; mock `/api/patients` returns Alice; assert dropdown shows "Alice"; click → patient_id state becomes Alice's id.

3. **`compose-channel-resolves-recipient.test.tsx`** — with patient {phone: '+15551234567', email: 'a@x.com'} selected, click Email pill → `to` input value === 'a@x.com'; click WhatsApp → value === '+15551234567'.

4. **`mark-thread-read.test.tsx`** — render with seeded thread containing 1 unread inbound; click thread; assert `PATCH /api/v2/communications/threads/{thread_key}/read` is fired (mock the request to capture URL).

5. **`tiptap-body-serializes.test.tsx`** — render compose with mounted Tiptap; type "hello world", select all, click bold (or call command); submit; assert mocked POST body has `body === "hello world"` (plain text, not HTML).

6. **`reply-prefills-channel-and-to.test.tsx`** — render ThreadDetail with one inbound SMS message from `+15550000`; click "Reply" button on bubble; assert ComposeDialog opens with `channel === 'sms'`, `to === '+15550000'`, and `patient_id` set.

## Implementation

- Modify: `frontend/src/features/communications/CommInbox.tsx` → becomes a layout shell with `<ThreadList>` + `<ThreadDetail>` + `<ComposeDialog>` + state for selected thread.
- New: `frontend/src/features/communications/ThreadList.tsx`
- New: `frontend/src/features/communications/ThreadDetail.tsx`
- New: `frontend/src/features/communications/MessageBubble.tsx`
- Rewrite: `frontend/src/features/communications/ComposeDialog.tsx` (or extract from current CommInbox into its own file if not already).
- Reuse: `frontend/src/lib/fetcher.ts` for all API calls; `frontend/src/components/Drawer.tsx` is not needed here (this is inline panel).

## Constraints

- Don't break the M6 channel-toggle pattern (existing test `frontend/tests/track_pms_m6/compose-channel-toggle.test.tsx` must still pass — submit body must include `channel` field).
- Don't break M6 reply-prefill test (`reply-prefills-channel.test.tsx`).
- Mark-read endpoint failures should NOT bubble — log + continue.
- ComposeDialog is opened from two places: a "+ Compose" button in the inbox toolbar AND from "Reply" buttons. Both paths must work.

```bash
make test-pms-f1
```
