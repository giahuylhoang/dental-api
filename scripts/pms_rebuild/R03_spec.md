# R03 — /patients/[id] from patient-detail.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/patient-detail.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/patients/[id]/page.tsx` (overwrite)

## Composition
1. **Hero card**: avatar, full name, status badge, file/chart number (font-mono), DOB, phone, email, insurance summary.
2. **Tabbed interface**: Overview / Appointments / Insurance / Notes (and any additional tabs the HTML has — port them all).
3. Overview tab: tooth chart preview + detail rows (DOB, Phone, Email, Insurance carrier, Recall due, etc.).
4. Appointments tab: list with date, time, type, provider, status.
5. Insurance tab: card list of insurance plans with details.
6. Notes tab: clinical notes + admin notes split panels.
7. Footer/header buttons: "Open full chart" / "Close" / etc. as the HTML has.

## Data wiring
- Patient hero → `/api/patients/{id}`.
- Appointments → `/api/appointments?patient_id={id}`.
- Insurance → `/api/v2/clinical/patients/{id}/insurance`.
- Notes → `/api/v2/clinical/notes?patient_id={id}`.
- Tooth chart → `/api/v2/clinical/patients/{id}/tooth-chart`.
- Documents (if HTML shows) → `/api/v2/clinical/patients/{id}/documents`.

## Done when
- Tab structure matches HTML exactly.
- `cd web && npx next build` green.
