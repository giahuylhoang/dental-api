# PMS Module F6 — Settings page (TDD)

Make `make test-pms-f6` exit 0.

## Success criteria

- `/settings` replaces the placeholder at `App.tsx:49` with a real `SettingsPage` bound to F0's `GET/PUT /api/v2/settings/clinic` and `GET /api/v2/settings/integrations`.
- The page is composed of 4 collapsible cards (default expanded for "Clinic Info"), each with its own form + Save button:
  - **Clinic Info** (`ClinicInfoCard.tsx`): `display_name`, `address`, `contact_phone`, `timezone` (select with 6 common timezones — America/Edmonton, America/Toronto, America/Vancouver, America/New_York, Europe/London, UTC).
  - **Working Hours** (`WorkingHoursCard.tsx`): `working_hour_start`, `working_hour_end` as `<input type="time">`.
  - **Notifications** (`NotificationsCard.tsx`): `booking_notification_email`.
  - **Integrations** (`IntegrationsCard.tsx`): READ-ONLY — three rows (SMS / Email / WhatsApp) each with a green/red dot reflecting `enabled` from `GET /integrations`.
- Each editable card uses `react-hook-form` + `zod` (already installed via `@hookform/resolvers`) for validation. Empty `display_name` is invalid. Email validates as email.
- On Save: PUT `/api/v2/settings/clinic` with the changed fields; on success, show a toast "Saved" (simple inline `<span class="text-green-600">Saved</span>` that fades after 2s — no toast lib).
- After successful save, refetch GET to confirm persistence.

## Tests first (`frontend/tests/track_pms_f6/`)

1. **`settings-loads-clinic-config.test.tsx`** — render `<SettingsPage />` with MSW mock returning `{display_name: "Smile Co", timezone: "America/Edmonton", ...}`; assert form prefilled.

2. **`save-clinic-info-puts-correct-body.test.tsx`** — render, change `display_name` to "New Name", click Save in Clinic Info card; assert PUT `/api/v2/settings/clinic` body contains `{display_name: "New Name"}`.

3. **`validation-blocks-empty-name.test.tsx`** — render, clear `display_name`, click Save; assert no PUT fired AND visible error message under the input.

4. **`integrations-section-shows-status.test.tsx`** — render with `GET /integrations` returning `{sms:{enabled:true}, email:{enabled:false}, whatsapp:{enabled:true}}`; assert SMS row shows enabled indicator, Email shows disabled, WhatsApp enabled.

E2E (`frontend/e2e/track_pms_f6/settings-flow.spec.ts`): Login → /settings → edit display name → save → reload → name persists.

## Implementation

- New: `frontend/src/features/settings/SettingsPage.tsx` (top-level layout + data fetching with `useQuery`).
- New: `frontend/src/features/settings/ClinicInfoCard.tsx`
- New: `frontend/src/features/settings/WorkingHoursCard.tsx`
- New: `frontend/src/features/settings/NotificationsCard.tsx`
- New: `frontend/src/features/settings/IntegrationsCard.tsx`
- Modify: `frontend/src/App.tsx` line 49 — replace `<Placeholder title="Settings" />` with `<SettingsPage />` and import.

## Constraints

- Each card saves independently (separate forms — minimizes the chance one card's validation blocks another's save).
- Don't add a toast lib for one inline success message.
- The integrations card is read-only — no env editing from the UI.
- Keep the existing AppShell sidebar Settings link working.

```bash
make test-pms-f6
```
