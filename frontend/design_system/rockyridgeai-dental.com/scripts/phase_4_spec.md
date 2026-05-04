# Phase 4 — Data seed expansion

## Goal

Add 14 new seed-data JS files (plus a 15th aggregator) under `data/`. Each file sets a single `window.<UPPER_SNAKE>` global. Status enums use canonical spellings from `database/models.py`. Pages from Phases 2 and 3 already reference these globals; this phase makes them real.

## Working directory

`frontend/design_system/rockyridgeai-dental.com/`

## Files to create

| File | Global | Records | Notes |
|------|--------|---------|-------|
| `data/leads.js` | `LEADS` | 10 | name (split first/last), phone (E.164ish), email, source (Google\|Referral\|Instagram\|Walk-in\|Other), status (NEW\|CONTACTED\|QUALIFIED\|CONVERTED\|LOST), notes, owner_id, clinic_id="default" |
| `data/threads.js` | `THREADS` | 8 | thread_key, patient_id, channel (sms\|email\|whatsapp), unread (int), last_at, subject, messages: [{ id, direction (in\|out), body, sent_at, read_at? }] |
| `data/claims.js` | `CLAIMS` | 6 | id (mono-style "CLM-2026-0001"), invoice_id, carrier, kind (claim\|predetermination), status (draft\|submitted\|accepted\|adjudicated\|paid\|rejected\|partial), assignment_of_benefits, submitted_at, adjudicated_at, accepted_amount, response_codes ([{code, description, severity}]) |
| `data/lab_cases.js` | `LAB_CASES` | 8 | id ("LC-2026-0001"), denture_case_id?, vendor_id, vendor_name, case_number, sent_at, due_back_at, returned_at?, status (draft\|sent\|in_progress\|returned\|remake\|cancelled), lab_fee, courier_tracking, events: [{ kind, occurred_at, payload }] |
| `data/treatment_plans.js` | `TREATMENT_PLANS` | 6 | id, patient_id, status (draft\|presented\|accepted\|in_progress\|completed\|declined), total_estimate, insurance_estimate, patient_estimate, presented_at?, accepted_at?, items: [{sequence, procedure_code, description, fee, insurance_coverage_pct, tooth_number, completed_at?}] |
| `data/providers.js` | `PROVIDERS` | 4 | id, name, title (Dr\|Mr\|Ms), specialty (Denturist\|General Dentist\|Hygienist\|Lab Tech), is_active, color (hex used by schedule.html) |
| `data/services.js` | `SERVICES` | 8 | id, name, description, duration_min, base_price (Decimal-like number) |
| `data/recalls.js` | `RECALLS` | 6 | id, patient_id, rule_id, due_at, sent_at?, status (pending\|sent\|completed\|cancelled), channel (sms\|email\|both) |
| `data/waitlist.js` | `WAITLIST` | 4 | id, patient_id, requested_window_start, requested_window_end, provider_pref?, service_id?, priority (1-3), status (open\|filled\|expired\|cancelled) |
| `data/denture_cases.js` | `DENTURE_CASES` | 4 | id, patient_id, arch (upper\|lower\|both), case_type (complete\|partial\|immediate\|implant_retained), current_stage, status (open\|closed), opened_at, closed_at?, notes |
| `data/audit_log.js` | `AUDIT_LOG` | 12 | id, user_id, action (insert\|update\|delete\|read\|export), entity_type, entity_id, occurred_at, ip |
| `data/tooth_chart.js` | `TOOTH_CHART` | mapping object | `{ "<patient_id>": [{ tooth_number: 1..32, status (present\|missing\|extracted\|implant\|bridge_pontic\|crowned\|filled\|root_treated\|to_extract), surface_notes?, last_examined_at? }, …] }` for at least 2 patients |
| `data/users.js` | `USERS` | 4 | id, clinic_id="default", email, full_name, role (Owner\|Manager\|Provider\|Front-desk), is_active. Include at least one user with email "demo@rockyridge.dental" so login.html demo works. |
| `data/clinics.js` | `CLINICS` | 1 | id="default", name, display_name, timezone="America/Edmonton", working_hour_start, working_hour_end, address, contact_phone, booking_notification_email |
| `data/index.js` | (none) | — | A bootstrap that loads ALL the seed files. Implementation: just contains a JSDoc-ish comment listing each file in load order. (Pages explicitly include `<script src="../../data/<file>.js">` themselves.) |

## File template

Each seed file should look like:

```js
// data/<name>.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.<UPPER_SNAKE> = [
    { id: "…", … },
    …
  ];
})();
```

For `tooth_chart.js`, use an object instead of an array.

For `index.js`, use:
```js
// data/index.js — manifest of demo seed files. Pages must include each .js file directly.
// Order:
//   clinics, users, providers, services, patients, appointments,
//   treatment_plans, tooth_chart, denture_cases, lab_cases,
//   invoices, claims, recalls, waitlist, threads, leads, audit_log
window.RRD = window.RRD || {};
window.RRD.SEED_MANIFEST = [
  "clinics","users","providers","services","patients","appointments",
  "treatment_plans","tooth_chart","denture_cases","lab_cases",
  "invoices","claims","recalls","waitlist","threads","leads","audit_log"
];
```

## Pass criterion

Run `bash scripts/test_phase4.sh`. It checks:
1. Every file exists, parses with `node --check`, and sets a `window.<UPPER>` global (except `index.js`).
2. Status fields in each file use the canonical enum spellings.
3. `data/index.js` references every other seed file.
4. Each global is consumed by at least one page (or the seed file is loaded via `<script src>`).

## Rules

- Match the spellings in `database/models.py` exactly. The test greps for canonical enums; a typo will fail.
- Cross-reference IDs across files: lead-activities reference lead.id, invoices reference patient.id, lab_cases reference denture_case.id, etc.
- Money fields are plain numbers (no currency string in the data).
- Dates are ISO strings (`2026-04-30T14:30:00`).
- ~6–10 records per collection unless the table above says otherwise.
- DO NOT remove or modify the existing `data/{patients,appointments,invoices}.js` — extend them only if a new field is needed; otherwise leave them alone.
