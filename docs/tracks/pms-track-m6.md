# PMS Module M6 — Communications WhatsApp + inline reply (TDD)

Make `make test-pms-m6` exit 0.

## Success criteria

- `ComposeDialog` channel toggle: SMS / Email / WhatsApp (3 buttons or a segmented control).
- WhatsApp option posts to `/api/v2/communications/send` body `{patient_id, channel: 'whatsapp', body, to}` — backend M0 routes that to `send_whatsapp` via Twilio.
- Each inbound message in `CommInbox` has a "Reply" button → opens compose pre-filled with the inbound channel and the inbound sender as the recipient.
- Channel icons in the inbox: 📱 (sms), ✉️ (email), 💬 (whatsapp).

## Tests first (`frontend/tests/track_pms_m6/`)

1. **`compose-channel-toggle.test.tsx`** — render compose dialog open, click WhatsApp toggle, fill body, submit; mock POST `/api/v2/communications/send`; assert request body has `channel: 'whatsapp'`.

2. **`reply-prefills-channel.test.tsx`** — render an inbound message row of channel='sms' from '+15550101010'; click "Reply"; assert compose opens with `channel='sms'` and `to='+15550101010'`.

E2E (`frontend/e2e/track_pms_m6/`):
- /communications → click an inbound message Reply button → compose opens with prefilled fields → toggle to WhatsApp → send (mock backend) → outbound row appears.

## Implementation

- Modify: `frontend/src/features/communications/CommInbox.tsx`:
  - Channel union: `'sms' | 'email' | 'whatsapp'`.
  - Channel toggle in compose dialog: 3 buttons.
  - Reply button on inbound rows → calls `setCompose({channel: row.channel, to: row.from})`.
- No backend changes (M0 handles routing).

## Constraints

- Don't break existing SMS/email send flow.
- Backend M0 has `send_whatsapp` ready.
- Configurable via env `TWILIO_WHATSAPP_FROM` (fall back handled in M0).

```bash
make test-pms-m6
```
