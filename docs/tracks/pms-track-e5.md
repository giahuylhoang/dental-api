# PMS Module E5 — Billing + Communications

Make `make test-pms-e5` exit 0.

## Success criteria

### `frontend/src/features/billing/InvoiceList.tsx` — rewrite

- PageHeader — title "Billing", desc "{outstanding $}{...} outstanding"; right: `<Button>+ New invoice</Button>`.
- Toolbar `<Card>` — search + status `<Select>` filter + date range placeholder.
- `<DataTable>` (E0) — cols: invoice_number, patient (PatientChip variant="inline"), status Badge, total ($), age (days), actions DropdownMenu (View / Issue / Void / Download PDF).
- Click row → InvoiceDrawer opens.
- Empty state.

### `frontend/src/features/billing/InvoiceDrawer.tsx` — D1 Sheet

- D1 `<Sheet>` from right.
- Sticky header: PatientChip variant="card", invoice_number monospace, status Badge.
- Tabs: Detail / Lines / Payments / Claims / PDF.

### `frontend/src/features/communications/CommInbox.tsx` — Resizable two-pane

- Use `react-resizable-panels` (E0) — left pane = ThreadList, right pane = ThreadDetail. User can resize the divider.
- Above ThreadList: channel filter chips (`<Badge>`s acting as toggles) + a `<Button>+ Compose</Button>`.
- ThreadList rows are styled as Card-like rows: avatar (PatientChip initials), name, last-message preview, channel icon, time, unread badge (D1 `<Badge>`).
- ThreadDetail uses D1 styles too: header with PatientChip variant="card" + channel name, message bubbles with asymmetric rounded corners (`rounded-2xl rounded-br-sm` for outbound right, `rounded-2xl rounded-bl-sm` for inbound left), bg from tokens (outbound = primary, inbound = muted).
- Footer "Reply" button opens ComposeDialog pre-filled.

### `frontend/src/features/communications/ComposeDialog.tsx` — D1 Dialog polish

- Use D1 Dialog properly.
- Channel selector: a horizontal D1 `<Tabs>` with three tabs (SMS / Email / WhatsApp) instead of the segmented Buttons.
- Patient: D2 `<PatientSearchInput>`.
- Body: existing tiptap editor in a styled wrapper.

## Tests first (`frontend/tests/track_pms_e5/`)

1. **`billing-comms-redesign.test.tsx`** — render InvoiceList; assert PageHeader, DataTable testid, ≥3 ui imports.

2. **`comms-resizable-panes.test.tsx`** — render CommInbox; assert presence of `<PanelGroup>` (resizable) elements (`data-panel-group`).

3. **`message-bubble-asymmetric-corners.test.tsx`** — render ThreadDetail with outbound + inbound; assert outbound bubble has class containing `rounded-br-sm` and inbound has `rounded-bl-sm`.

4. **`compose-dialog-tabs-channel.test.tsx`** — render compose; assert 3 Tabs (SMS / Email / WhatsApp); click Email; assert active.

## Strict gate

- `InvoiceList.tsx` ≥3 ui imports.
- `CommInbox.tsx` ≥2 ui imports.
- Zero raw `<button` in `InvoiceList.tsx`.

## Constraints

- Don't break P5, M6, F1, F2 tests. F1's compose channel-toggle test will need to switch from segmented buttons to Tabs — update it in this module preserving intent.

```bash
make test-pms-e5
```
