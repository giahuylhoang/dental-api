# Admin portal auth cutover — runbook

**Spec:** `docs/superpowers/specs/2026-05-28-admin-portal-auth-design.md`
**Plan:** `docs/superpowers/plans/2026-05-28-admin-portal-auth-plan.md`

This runbook walks the soft-fallback migration of `/api/portal/*` from
token-claim-based clinic authorization to the DB-backed
`user_clinic_memberships` table introduced by the CRM auth plan.

## Pre-flight

The CRM auth plan (`docs/superpowers/plans/2026-05-28-crm-api-auth-plan.md`)
Tasks 1–2 must have shipped to prod. Confirm by querying the Cloud SQL
prod DB:

```sql
\dt user_clinic_memberships
```

If the table does not exist, **stop**. Deploy the CRM plan migration
first, then resume here.

## Step 1 — Backfill memberships from existing Firebase claims

From a workstation with prod-DB credentials and Firebase Admin SDK
access:

```bash
cd dental-api
DATABASE_URL='postgresql://...prod...' \
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json \
python scripts/backfill_portal_memberships.py
```

Expected log line on success:

```
backfill complete: {'users_scanned': N, 'rows_inserted': N, 'rows_skipped_existing': 0, 'users_without_claim': 0}
```

If the script exits non-zero, the log includes the partial summary
showing how many users were scanned before the failure. Resolve the
underlying issue and re-run — the script is idempotent
(`rows_skipped_existing` will rise on the second run).

If `users_without_claim > 0`, those users have no `clinic_ids` claim on
their Firebase token — they would be 403'd by the new gate. Decide
per-user whether to grant access via the CRM auth plan's CLI:

```bash
python scripts/grant_clinic_access.py --uid <uid> --clinic <clinic_id>
```

## Step 2 — Deploy dental-api with this plan's code

Trigger the CI/CD pipeline or manual Cloud Run deploy. The new
`require_clinic_access` ships with the soft fallback already in place —
existing users keep working because (a) they have membership rows from
Step 1, OR (b) the fallback grants on their token claim.

Verify the new revision is serving:

```bash
gcloud run services describe dental-api-v2 \
  --region=northamerica-northeast2 \
  --project=rockyridgeai-dental \
  --format="value(status.latestReadyRevisionName,status.traffic[0].percent)"
```

Expect 100% on the latest revision.

## Step 3 — Monitor the warn log

Tail Cloud Run logs:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND
   resource.labels.service_name="dental-api-v2" AND
   textPayload:portal_membership_missing' \
  --project=rockyridgeai-dental \
  --limit=50 --format=json
```

Expected: warn count drops to zero within minutes if backfill was
complete. If non-zero, identify the `uid` and `clinic_id` from each
log line and run `grant_clinic_access.py` for them, then re-check.

## Step 4 — Soak

Watch for 7 consecutive days. Confirm zero `portal_membership_missing`
warn lines. Acceptable threshold per day: 0.

During this window, any new Firebase user added to the system must
also get a `user_clinic_memberships` row at creation time — otherwise
they hit the fallback path and surface a warn. The CRM auth plan's
`grant_clinic_access.py` CLI is the canonical tool.

## Step 5 — Remove the fallback

Open a follow-up PR that:

- Deletes the fallback block in `api/portal/deps.py:require_clinic_access`:

  ```python
  # Delete these lines:
  if clinic_id in (user.clinic_ids or []):
      _log.warning(
          "portal_membership_missing uid=%s clinic_id=%s email=%s",
          user.uid, clinic_id, user.email,
      )
      return clinic_id
  ```

- Optionally: remove `clinic_ids` from `PortalUser` and from
  `get_portal_user`'s claim extraction. Keep them if
  `/api/portal/whoami` still surfaces `clinic_ids` for the frontend
  sidebar; otherwise drop.
- Update the 4 contract tests in `tests/portal/test_deps.py` —
  `test_require_clinic_access_no_row_but_token_claim_allows_with_warn`
  and `test_require_clinic_access_stale_claim_with_no_row_still_allows_during_cutover`
  must flip to expect 403 instead of 200 + warn.

That commit fails closed: no DB row → 403, no fallback.

## Rollback

Revert this plan's commit (`feat(portal): DB-backed clinic auth ...`).
The portal returns to claim-only checks instantly. Backfilled
membership rows are harmless to leave in the DB — they're just unused
ahead of a future re-deploy.

If the rollback is needed urgently and the revert PR isn't ready:

```bash
# Deploy the previous Cloud Run revision (no rebuild needed):
gcloud run services update-traffic dental-api-v2 \
  --region=northamerica-northeast2 \
  --to-revisions=<previous-revision>=100 \
  --project=rockyridgeai-dental
```

Find the previous revision name via:

```bash
gcloud run revisions list \
  --service=dental-api-v2 \
  --region=northamerica-northeast2 \
  --project=rockyridgeai-dental \
  --limit=3
```
