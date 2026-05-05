# Phase 2 — Add the 9 missing app pages

## Goal

Create 9 new HTML pages under `ui_kits/website/` so every Sidebar link and every detail-row href from Phase 1 lands on a real page. Every page reuses the existing `Sidebar`, `TopBar`, and `colors_and_type.css`. Visual language strictly from `frontend/design_system/rockyridgeai-dental.com/`. Content vocabulary inspired by `frontend/src/features/<area>/` files — but DO NOT copy any of their CSS/Tailwind/shadcn imports.

## Working directory

`frontend/design_system/rockyridgeai-dental.com/`

All paths relative.

## Read first (inspiration only — do not copy styles)

- `colors_and_type.css` — every token you may use (no new ones)
- Existing kit pages: `ui_kits/website/{dashboard,patients,schedule,treatment,lab,billing,communications,crm}.html` — match this house style exactly (font choices, KPI strip, table conventions, status pills, tab strips)
- Existing components: `Sidebar.jsx`, `TopBar.jsx`, `KpiTile.jsx`, `EmptyState.jsx`, `ToothChartTile.jsx`, `LabPipeline.jsx`, `AppointmentCard.jsx`, `PatientCard.jsx`
- `lib/query.js` — use `window.RRD.query('id')` to read `?id=...`
- Source files in the React app for content vocabulary (read for field names, status enums, tab names — not styling):

| New page | Inspiration file(s) |
|----------|---------------------|
| `reports.html` | `frontend/src/features/reporting/Dashboard.tsx` |
| `settings.html` | `frontend/src/features/settings/SettingsPage.tsx` and any sibling files |
| `plans.html` | `frontend/src/features/treatment-plans/TreatmentPlansPage.tsx` (or similar) |
| `patient-detail.html` | `frontend/src/features/patients/Patient360.tsx` |
| `invoice-detail.html` | `frontend/src/features/billing/InvoiceDrawer.tsx` + `ClaimDrawer.tsx` + `AdjudicateForm.tsx` |
| `appointment-detail.html` | `frontend/src/features/scheduling/AppointmentDrawer.tsx` (or NewAppointmentDialog) |
| `lead-detail.html` | `frontend/src/features/crm/LeadDrawer.tsx` + `LeadActivityTimeline.tsx` |
| `lab-case-detail.html` | `frontend/src/features/lab/LabCaseDrawer.tsx` |
| `denture-case-detail.html` | `frontend/src/features/clinical/DentureCaseDrawer.tsx` (or DentureCaseEditor) |

## Page contracts

Every new page:
1. Doctype HTML5, `<html lang="en" class="">` (no `dark` class — light theme).
2. `<title>` set to "{Page title} · Rockyridge Dental AI".
3. Loads in head: `<link rel="stylesheet" href="../../colors_and_type.css">`, Google Fonts (Montserrat, Inter, JetBrains Mono — same as existing pages), Lucide via `<script src="https://unpkg.com/lucide@latest"></script>` if needed, React + ReactDOM + Babel via unpkg pinned to the same versions as `dashboard.html`.
4. Loads its data with `<script src="../../data/<file>.js"></script>` for whichever globals it needs. (Phase 4 creates these files. For now, the page may fall back gracefully if the global is missing — render an `EmptyState`.)
5. Loads `<script src="../../lib/query.js"></script>`.
6. Uses Sidebar with the correct `active=` key:
   - `reports.html` → `reports`
   - `settings.html` → `settings`
   - `plans.html` → `plans`
   - `patient-detail.html` → `patients`
   - `invoice-detail.html` → `billing`
   - `appointment-detail.html` → `schedule`
   - `lead-detail.html` → `crm`
   - `lab-case-detail.html` → `lab`
   - `denture-case-detail.html` → `lab`
7. Calls `window.RRD.requireSession?.()` at top of `<script type="text/babel">` (Phase 5 wires the function; this phase just needs the call to exist for forward-compat).
8. Strict adherence to brand: Navy `--rr-navy-*`, Steel `--rr-steel-*`, Warm-white background, Montserrat for titles/numbers, Inter for body, JetBrains Mono for IDs/timestamps/money.

## Page-by-page content brief

### `reports.html`
- Page header: "Reports", subtitle "Operational and clinical KPIs".
- KPI strip (5 tiles): Revenue (last 30d, with delta vs prev 30d), AR outstanding, Recall conversion %, New patients (30d), Avg booking lead time.
- 2-col grid:
  - Revenue trend (inline SVG sparkline, 12-week)
  - AR aging (5 buckets, same as billing.html)
- 2-col grid:
  - Provider productivity table (provider, hours booked, hours billed, $/hr)
  - Top procedures (count, avg fee)
- Recall queue summary table (rule, due this week, conversion %).
- All numbers come from `window.REPORTS` if present; otherwise show inline-mocked numbers using the same dataset that already lives in `data/invoices.js` + `data/appointments.js`.

### `settings.html`
- Tab strip across the top: Clinic info · Working hours · Operatories · Providers · Users & roles · Integrations · Notifications · Audit log.
- One panel per tab; only one panel rendered at a time (use a `useState` for active tab).
- Clinic info panel: form with name, display_name, timezone, address, contact_phone, booking_notification_email.
- Working hours: 7-row table (day_of_week 0-6) with open/close + lunch break + closed checkbox.
- Operatories: rows of name + equipment_tags chip list + active toggle.
- Providers: list with name, title, specialty, active. (Read from `window.PROVIDERS` if present.)
- Users & roles: list with full_name, email, role chips. (`window.USERS`.)
- Integrations: cards for Twilio (SMS), SMTP (email), CDAnet (insurance) with "Connected" pill or "Connect" button.
- Notifications: toggles for booking confirmations, recall reminders, lab updates.
- Audit log: scrolling table of action / entity / user / when. (`window.AUDIT_LOG`.)

### `plans.html`
- Two-column layout: left list of treatment plans (status pipeline pills `draft / presented / accepted / in_progress / completed / declined`), right inline editor pane that shows the selected plan's items.
- List columns: patient name, total estimate, insurance estimate, patient estimate, status, presented_at.
- Editor pane: per-line procedure_code, description, fee, insurance_coverage_pct, tooth_number, completed_at.
- Reads `window.TREATMENT_PLANS`. If `?patient=<id>` is present, default-filter to that patient.

### `patient-detail.html`
- Reads patient by `?id=` from `window.PATIENTS`.
- Header: 64px monogram avatar, name, MRN (mono), DOB + age, primary insurance pill, lifecycle status (`active|inactive|pending|deceased|merged`), action buttons (Schedule, New invoice, Send message, Edit).
- Tab strip: Overview · Tooth chart · Insurance · Documents · Notes · Treatment plans · Communications · Billing · Audit.
- Overview panel: medical history flags (allergies, medications, bisphosphonates), recent appointments, upcoming recalls.
- Tooth chart: render via `<ToothChartTile>` reusing the existing component.
- Insurance: list of `PatientInsurance` rows (carrier, policy_number, group, holder, coverage % JSON shown as compact pill list).
- Documents: grid of cards with kind pill (photo|xray|consent|other), filename, size.
- Notes: list of clinical notes (SOAP fields) with `locked_at` indicator.
- Treatment plans: list with status pipeline and "Open in editor" → `plans.html?patient={id}`.
- Communications: thread list filtered to this patient.
- Billing: invoice + payment list filtered to this patient.
- Audit: per-record audit log filtered to this patient.

### `invoice-detail.html`
- Reads invoice by `?id=` from `window.INVOICES`.
- Header: invoice id, status pill, total, balance, issued_at, due_at, "Send invoice" / "Record payment" / "Open claim" buttons.
- Lines table: sequence, code, description, qty, unit_price, total.
- Payments table: method (cash|card|cheque|etransfer|insurance), amount, received_at, reference.
- Claim section (`#claim` anchor target): claim status pipeline (`draft → submitted → accepted → adjudicated → paid` plus rejected/partial), carrier, kind (claim|predetermination), assignment_of_benefits, response codes table, inline adjudicate form (Outcome select / Accepted amount / Codes / Notes / Save).

### `appointment-detail.html`
- Reads from `window.APPOINTMENTS` by `?id=`.
- Header: start_time / end_time / duration / chief_complaint / status pill (one of `SCHEDULED, CONFIRMED, COMPLETED, NO_SHOW, PENDING, PENDING_SYNC, RESCHEDULED, REMINDER_SENT, CANCELLED`).
- Body: patient summary card (avatar + name + DOB + insurance pill, links to `patient-detail.html?id={p.id}`), provider card, service card.
- Reminders log table.
- Related invoices list.
- Action buttons: Confirm, Reschedule, Cancel, Mark complete, Mark no-show.

### `lead-detail.html`
- Reads from `window.LEADS` by `?id=`.
- Header: avatar + name + status pill (`NEW|CONTACTED|QUALIFIED|CONVERTED|LOST`), phone (mono), email, source pill, owner avatar.
- Tabs: Detail · Activities · Convert.
- Detail panel: form (first/last/phone/email/owner select/status select/notes textarea + source).
- Activities: compose strip (Note/Call/Email/SMS/Meeting kind chips) + reverse-chronological activity timeline (`window.LEAD_ACTIVITIES` may not exist; fall back to inline 5 demo events using kinds `note|call|email|sms|meeting|status_change`).
- Convert: form (insurance fields + first appointment date/provider/service) and a primary CTA "Create patient + appointment".

### `lab-case-detail.html`
- Reads from `window.LAB_CASES` by `?id=`.
- Header: case_number, status pill (`draft|sent|in_progress|returned|remake|cancelled`), vendor, sent_at, due_back_at, returned_at, lab_fee, courier_tracking (mono).
- Body: stage timeline (events list ordered by occurred_at), materials table (item, lot, qty_consumed, unit_cost), photos grid (placeholder cells with "no image" if absent).
- Action buttons: Mark sent / Mark returned / Open remake.

### `denture-case-detail.html`
- Reads from `window.DENTURE_CASES` by `?id=`.
- Header: case id, arch (`upper|lower|both`), case_type (`complete|partial|immediate|implant_retained`), status (`open|closed`), opened_at.
- Body: stage progression chips (use the `current_stage` field), implants table (tooth_position, vendor, model, lot_number, surface_treatment, abutment_type, placed_date), notes section, related lab cases list with link to `lab-case-detail.html?id={lc.id}`.

## Pass criterion

Run `bash scripts/test_phase2.sh`. It checks:
1. Each of the 9 files exists.
2. Each imports `colors_and_type.css`.
3. HTTP 200 from a `python3 -m http.server` smoke.
4. Phase-1 link audit re-runs cleanly (no missing href targets remain).

## Rules

- Do NOT touch `colors_and_type.css`, `README.md`, `SKILL.md`, `preview/*`, `assets/*`, `uploads/*`.
- Do NOT touch any file under `frontend/src/`. Read-only.
- Do NOT introduce new colour or font tokens; reuse existing variables.
- Each new page's `<a href>` targets must resolve to a real file in `ui_kits/website/`.
