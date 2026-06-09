# Telnyx SMS cutover runbook

## Pre-flight (operational, NOT code)

1. Telnyx Messaging Profile created in the Telnyx Portal.
2. Number(s) provisioned with SMS enabled + added to the Messaging Profile.
3. Webhook URL on the Messaging Profile set to:

   ```
   https://<dental-api-host>/webhooks/telnyx/sms-inbound
   ```

4. Ed25519 public key copied from the Messaging Profile webhook settings → Secret Manager as `TELNYX_PUBLIC_KEY` (base64 string).
5. `TELNYX_API_KEY`, `TELNYX_MESSAGING_PROFILE_ID`, `TELNYX_SMS_FROM_NUMBER` written to Secret Manager and injected into the dental-api-v2 Cloud Run service.

## Cutover

1. Deploy current dental-api with `SMS_PROVIDER=twilio` (no behavior change — sanity).
2. Send a manual test SMS through the Telnyx Portal to the production number to verify end-to-end inbound reception arrives at the webhook (signature must verify).
3. Flip the Cloud Run env: `SMS_PROVIDER=telnyx`. Single env update; no code redeploy.
4. Trigger one real booking through Emma (or the admin UI) to a test phone; verify the booking-confirmation SMS lands via Telnyx.
5. Monitor logs for 1 week. Expected per-message cost on Telnyx for NA: ~$0.004 outbound, ~$0.004 inbound — significantly cheaper than the Twilio equivalent.

## Rollback

Flip the Cloud Run env back to `SMS_PROVIDER=twilio`. No code change needed. The Twilio path stays in the binary for at least one release after this cutover.

## Post-cutover cleanup (separate spec)

Once Telnyx is stable for >1 week:
- Remove `_send_via_twilio` from `clients/sms_client.py`.
- Remove the `SMS_PROVIDER` env flag.
- Remove Twilio creds from Secret Manager.
- Remove `twilio` from `pyproject.toml` and `requirements.txt`.

## Failure modes to watch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| All Telnyx sends return None in logs | `TELNYX_*` env missing or wrong | Verify Secret Manager + Cloud Run env injection |
| Webhook 401 on every inbound | `TELNYX_PUBLIC_KEY` mismatch with the active profile | Copy key from Telnyx Portal again; redeploy |
| Webhook 200 but reminders never status=replied | Reminder row not matching `from_phone` | Check Patient.phone vs the actual SIP From — Telnyx canonical-izes numbers |
| Sends succeed but inbound times out | Cloud Run cold start past Telnyx webhook timeout (5s) | Set `min_instances=1` or accept that reminders may dedupe |
