# T12 — /settings (two locked overlays)

## Objective
Settings page with ClinicInfo + WorkingHours live; Integrations + Notifications locked.

## References
- Visual: `ui_kits/website/settings.html`
- Logic: `frontend/src/features/settings/{ClinicInfoCard,WorkingHoursCard,IntegrationsCard,NotificationsCard}.tsx`

## Layout
- `web/app/(app)/settings/page.tsx` (`"use client"`).
- Tabs or stacked sections in this order:
  1. **Clinic Info** (live) — port `ClinicInfoCard.tsx`.
  2. **Working Hours** (live) — port `WorkingHoursCard.tsx`.
  3. **Integrations** —
     ```tsx
     <LockedFeature
       title="Integrations"
       body="Integrations are paused while we rework auth and webhook signing."
       backHref="/settings"
     />
     ```
  4. **Notifications** —
     ```tsx
     <LockedFeature
       title="Notifications"
       body="Notifications are paused while we migrate the templating engine."
       backHref="/settings"
     />
     ```

## Verify
```
cd web && npx tsc --noEmit && npx next build
```
