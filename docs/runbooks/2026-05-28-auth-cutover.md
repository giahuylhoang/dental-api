# Auth cutover runbook — 2026-05-28

Flip `dental-api` from "trusts any X-Clinic-Id" to "Firebase token + membership required."

## Preconditions

- Migration `i3j4k5l6m7n8_user_clinic_memberships` deployed to the live database.
- dental-api redeployed with the auth dependencies wired and Cloud Run env var `ADMIN_AUTH_BYPASS=true` set. Bypass mode means the new code is live but no enforcement happens — same behaviour as before.
- CRM frontend deployed with `AuthProvider` + login + Authorization header (Tasks 9–14) AND `apphosting.yaml` populated with a real `NEXT_PUBLIC_FIREBASE_APP_ID` (Task 15 leaves a `TODO-CRM-APP-ID` placeholder — that must be replaced with the appId from a registered CRM Firebase web app BEFORE push).
- Admin frontend already sends `Authorization: Bearer` since commit `a1146d9`. **Known gap:** the admin does NOT send `X-Clinic-Id` — it encodes clinic_id in the URL path (`/api/portal/clinics/<id>/...`). dental-api's `get_authorized_clinic` reads `X-Clinic-Id` from the header. After cutover, admin requests to `/api/clinics/me`, `/api/clinics/{id}/config` etc. that go through the header-based dep will 401 with `missing_clinic_header`. Two fixes (pick one BEFORE flipping):
  - Update admin's `lib/api.ts` `request` helper to inject `X-Clinic-Id` derived from the URL path (smallest change).
  - Update those dental-api routes to read clinic_id from the path parameter instead of the header.

## Cutover steps

### 1. Provision yourself a Firebase user + memberships

Connect to the prod Cloud SQL DB via `cloud-sql-proxy`:

```bash
# In one terminal — proxy to prod
gcloud auth login
cloud-sql-proxy rockyridgeai-dental:northamerica-northeast2:dental-api-v2-database --port=5434
```

In another terminal, from `dental-api/`:

```bash
DATABASE_URL=postgresql+psycopg2://postgres:<password>@127.0.0.1:5434/dental \
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-admin-key.json \
python scripts/grant_clinic_access.py \
  --email giahuy@rockyridgeai.com \
  --password '<one-time-strong-password>' \
  --clinics market-mall-denture,northeast-denture-clinic
```

Confirm:

```bash
python scripts/grant_clinic_access.py --list --email giahuy@rockyridgeai.com
```

Should print both clinic IDs.

### 2. Smoke test — bypass STILL ON

While `ADMIN_AUTH_BYPASS=true`, both frontends should still work:

- CRM: sign in at `https://dental-crm--rockyridgeai-dental.us-central1.hosted.app/login`. Click every sidebar item. Confirm DevTools → Network shows `Authorization: Bearer <jwt>` on every `/api/...` request and `X-Clinic-Id: <id>`.
- Admin: same drill at `https://clinic-admin-dashboard--rockyridgeai-dental.us-central1.hosted.app/`. Confirm `Authorization` header. (X-Clinic-Id is encoded in URL paths for admin's portal routes — see known gap above.)

If anything is missing in either frontend, fix BEFORE step 3.

### 3. Flip the switch

```bash
gcloud run services update dental-api-v2 \
  --region=northamerica-northeast2 \
  --update-env-vars=ADMIN_AUTH_BYPASS=false,DENTAL_API_INTERNAL_SECRET=<generate-rotate-this>
```

The new revision starts taking traffic within ~30s.

### 4. Re-smoke-test — bypass OFF

- CRM: sign in → every page loads, switcher only shows your authorized clinics.
- Admin: every page loads (assuming the X-Clinic-Id gap was addressed in preconditions).
- Sign out → next `/api/clinics/me` returns 401 `missing_token`.
- Hand-craft a curl with a token for one clinic + header for another:
  ```bash
  TOKEN=<copy from DevTools Network → request headers>
  curl -i \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Clinic-Id: northeast-denture-clinic" \
    https://dental-api-v2-qkwzgio7eq-pd.a.run.app/api/clinics/me
  ```
  Expected: 403 `clinic_forbidden` if your uid is not bound to northeast-denture-clinic.

### 5. Update routing infra (if applicable)

If the Telnyx routing webhook or voice agent calls `/api/clinics/by-did`, `/api/clinics/{id}/config`, or `/api/clinics/{id}/routing`, set the same `DENTAL_API_INTERNAL_SECRET` on those callers and have them send `X-Internal-Secret: <value>`. Without it they'll start getting 401 `internal_auth_failed`.

## Rollback

```bash
gcloud run services update dental-api-v2 \
  --region=northamerica-northeast2 \
  --update-env-vars=ADMIN_AUTH_BYPASS=true
```

Instant. The next request after the new revision takes traffic uses the bypass path again. No data loss; user membership rows stay in the DB harmlessly.

## Provisioning more users later

Same script, same proxy:

```bash
python scripts/grant_clinic_access.py \
  --email staffer@clinic.com \
  --password '<one-time>' \
  --clinics market-mall-denture
```

They sign in to the CRM with that password, then immediately use "Forgot password?" to set their own.

## Common gotchas

- **`firebase-admin` not initialized**: the script calls `firebase_admin.initialize_app()` which relies on Application Default Credentials. Run with `GOOGLE_APPLICATION_CREDENTIALS=<key.json>` pointing to a service account key with `firebaseauth.admin` role.
- **`UNIQUE constraint failed: clinics.id`**: don't pre-seed clinics that already exist. The script only inserts `user_clinic_memberships` rows; the clinics must already exist.
- **CRM `invalid-api-key` in console**: `NEXT_PUBLIC_FIREBASE_APP_ID` is still `TODO-CRM-APP-ID` — Task 15's placeholder. Register the web app, paste the appId, push the branch.
- **CRM "auth/unauthorized-domain" on sign-in**: the hosted-app domain wasn't added to Firebase Auth's Authorized Domains list. Add it under Authentication → Settings.

## Files involved (for reference)

- `dental-api/api/dependencies/auth.py` — `get_current_uid`, `get_authorized_clinic`, `get_internal_caller`, `ADMIN_AUTH_BYPASS`, `INTERNAL_SECRET`.
- `dental-api/scripts/grant_clinic_access.py` — provisioning CLI.
- `dental-api/alembic/versions/i3j4k5l6m7n8_user_clinic_memberships.py` — migration.
- `dental-crm-frontend/apphosting.yaml` — has `TODO-CRM-APP-ID` to fill in.
- `dental-crm-frontend/src/lib/firebase.ts`, `components/AuthProvider.tsx`, `components/RequireAuth.tsx`, `lib/api.ts` — CRM auth wiring.
- `dental-admin-frontend/lib/api.ts` — admin already sends `Authorization` header (commit `a1146d9`).
