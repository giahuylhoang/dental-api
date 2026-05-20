# Track 2 — Backend clinical: Patient 360, Treatment Plans, Lab Cases

You are a coding agent working on **one of five parallel tracks** that together extend the dental-api repo into a PMS/CRM for denturist clinics. Read `~/.claude/plans/now-i-want-to-fizzy-valley.md` for full context. Don't read or modify other tracks' files.

## Mission

Add the clinical core: extended patient records (medical history, insurance, consent), denture-case workflow with stage tracking, lab-case management (the key differentiator), treatment plans with Alberta CDA fee codes, clinical notes (SOAP + locking), and document storage refs. All under `/api/v2/clinical/*`, `/api/v2/lab/*`, `/api/v2/treatment-plans/*`.

## Hard constraints (CI gate)

1. `pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q` MUST stay green at every commit.
2. Do not edit `api/main.py`'s existing routes, `database/models.py`'s existing models (you may add NEW classes if needed and `import database.models`), or any v1 test. Add new modules under `database/clinical/`, `api/v2/clinical/`, `api/v2/lab/`, `api/v2/treatment_plans/`, `tests/track_clinical/`.
3. New tables added via Alembic migration `track2_clinical`. Migrations must apply cleanly from `alembic upgrade head` on an empty SQLite or Postgres DB.
4. Existing `Patient` table is extended only via new sibling tables — no new required columns on `patients`.
5. All endpoints accept `X-Clinic-Id` and scope every query by `clinic_id`. Use `get_clinic` dep (`api/main.py:43`). Use `get_db` from `database/connection.py`. Optionally require auth via Track 1's `require_permissions("clinical.write")` — but make tests work even when Track 1 hasn't merged: skip auth checks if `os.getenv("V2_REQUIRE_AUTH","false") != "true"`.

## Deliverables

### New tables (`database/clinical/models.py`)

Patient extensions (sibling tables, all `clinic_id` + `patient_id`):
- `patient_medical_history` — id, conditions JSON (e.g. `[{name, since, severity}]`), bisphosphonates_use bool, allergies_text
- `patient_allergies` — id, name, reaction, severity
- `patient_medications` — id, name, dose, since
- `patient_insurance` — id, carrier, policy_number, group_number, holder_name, holder_relationship, assignment_of_benefits bool, coverage_pct_by_category JSON, valid_from, valid_to, is_primary
- `patient_consent` — id, form_kind, form_version, signed_at, signature_blob_url, witness_name

Documents:
- `documents` — id, clinic_id, patient_id, kind (photo|xray|consent|other), storage_url, content_sha256, mime, size_bytes, uploaded_by, created_at. Unique on (clinic_id, content_sha256) for dedup.

Clinical notes:
- `clinical_notes` — id, clinic_id, patient_id, appointment_id?, author_id?, soap_subjective, soap_objective, soap_assessment, soap_plan, locked_at?, supersedes_id? (FK to clinical_notes for amendment chain), created_at, updated_at

Denture case workflow:
- `denture_cases` — id, clinic_id, patient_id, arch (upper|lower|both), case_type (complete|partial|immediate|implant_retained), current_stage (consult|prelim_imp|final_imp|bite_reg|wax_tryin|insert|adjust|complete|cancelled), status (open|closed), opened_at, closed_at?, notes
- `denture_case_events` — id, case_id, stage, occurred_at, provider_id?, note, photo_document_ids JSON

Treatment plans:
- `treatment_plans` — id, clinic_id, patient_id, status (draft|presented|accepted|in_progress|completed|declined), total_estimate, insurance_estimate, patient_estimate, presented_at?, accepted_at?, declined_at?
- `treatment_plan_items` — id, plan_id, sequence, procedure_code, description, fee, insurance_coverage_pct, completed_at?

Procedures (Alberta CDA fee guide subset):
- `procedures` — id, clinic_id, code (ADA&C, e.g. "01101", "55101"), name, default_duration_min, default_fee, category (preventive|diagnostic|restorative|prosthodontic|periodontic|surgical|other)
- Seed via `scripts/seed_procedures_alberta.py` — idempotent. Include at minimum a denturist-relevant subset: complete dentures (51101, 51102), partial dentures (53101, 53102), reline hard (55301), reline soft (55302), repair (52101–52199), exam (01101), x-rays (02101 etc.), adjustments (55101).

Lab management:
- `lab_vendors` — id, clinic_id, name, contact_email, contact_phone, sla_days, price_list JSON, is_active
- `lab_cases` — id, clinic_id, denture_case_id, vendor_id, sent_at?, due_back_at?, returned_at?, status (draft|sent|in_progress|returned|remake|cancelled), remake_of_id? (FK self), remake_reason?, lab_fee, courier_tracking?
- `lab_case_events` — id, lab_case_id, kind, occurred_at, payload JSON

### Endpoints

`api/v2/clinical/router.py`:
- Patient extensions:
  - `GET/POST /api/v2/clinical/patients/{id}/medical-history`
  - `GET/POST /api/v2/clinical/patients/{id}/insurance` (multiple allowed; one `is_primary`)
  - `GET/POST /api/v2/clinical/patients/{id}/consents`
  - `GET/POST /api/v2/clinical/patients/{id}/documents` — POST is JSON `{kind, storage_url, content_sha256, mime, size_bytes}`. Dedup on sha.
- Clinical notes:
  - `POST /api/v2/clinical/notes` — create draft
  - `PATCH /api/v2/clinical/notes/{id}` — only when not locked
  - `POST /api/v2/clinical/notes/{id}/lock` — sets `locked_at`
  - `POST /api/v2/clinical/notes/{id}/amend` — creates a new note with `supersedes_id` set; original stays locked
  - `GET /api/v2/clinical/notes?patient_id=`
- Denture cases:
  - `POST /api/v2/clinical/denture-cases` — body `{patient_id, arch, case_type}`; opens at stage `consult`
  - `GET /api/v2/clinical/denture-cases/{id}`
  - `POST /api/v2/clinical/denture-cases/{id}/advance` — body `{stage, note?, photo_document_ids?}`. Validates valid forward transition.
  - `POST /api/v2/clinical/denture-cases/{id}/close`
  - `GET /api/v2/clinical/denture-cases?patient_id=&status=&stage=`

`api/v2/lab/router.py`:
- `GET/POST/PUT/DELETE /api/v2/lab/vendors`
- `POST /api/v2/lab/cases` — body `{denture_case_id, vendor_id, sent_at?, due_back_at?, lab_fee?, courier_tracking?}`. Status starts `draft`.
- `POST /api/v2/lab/cases/{id}/send` — sets status `sent`, stamps `sent_at`.
- `POST /api/v2/lab/cases/{id}/return` — sets `returned`, stamps `returned_at`.
- `POST /api/v2/lab/cases/{id}/remake` — body `{reason}`. Creates a NEW lab case linked via `remake_of_id`; original status becomes `remake`.
- `GET /api/v2/lab/cases?status=&vendor_id=&denture_case_id=`

`api/v2/treatment_plans/router.py`:
- `POST /api/v2/treatment-plans` — body `{patient_id, items: [{procedure_code, description?, fee?, insurance_coverage_pct?}]}`. If `fee`/`description` omitted, look up from `procedures`. Computes totals.
- `GET /api/v2/treatment-plans/{id}`
- `PATCH /api/v2/treatment-plans/{id}/items` — replace items; recompute totals.
- `POST /api/v2/treatment-plans/{id}/present` / `/accept` / `/decline` / `/complete`.
- `GET /api/v2/treatment-plans?patient_id=&status=`

### Tests (`tests/track_clinical/`)
- `test_denture_case_state_machine.py` — valid forward transitions only; backward/skipping rejected with 400; closed cases reject advance.
- `test_lab_case_workflow.py` — send → return; remake creates child; original parent is `remake`; child's `remake_of_id` matches parent.
- `test_treatment_plan_math.py` — 3-item plan; insurance coverage applied per category; totals match. Fee lookup from `procedures` when omitted.
- `test_document_dedup.py` — same `content_sha256` returns existing row, doesn't duplicate.
- `test_clinical_note_locking.py` — PATCH locked note → 409. Amend creates supersedes chain; both rows readable.
- `test_multi_tenant_scoping.py` — clinic A cannot read clinic B's patients/cases/plans (404 not 403).

Use existing `client_market_mall` fixture for multi-tenant tests; add a `client_other_clinic` fixture that POSTs `/api/clinics` with id `clinic-other` and uses `X-Clinic-Id: clinic-other`.

## Success gate

```
pytest tests/track_clinical -q && \
pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q && \
DATABASE_URL=sqlite:///./_track2_check.db uv run alembic upgrade head && \
rm -f _track2_check.db
```

All commands must exit 0. Loop until green.

## Notes

- For `clinical_notes`, store SOAP fields as plain `Text` columns; max 50k chars per field.
- For `documents`, the API doesn't upload bytes — it accepts a pre-uploaded URL and a sha. Storage backend is out of scope (track 5 will plug in S3/GCS).
- For `procedures.code`, store as string; the Alberta fee-guide codes are alphanumeric in some categories.
- Use Pydantic v2 models with `model_config = ConfigDict(from_attributes=True)`.
- Reuse the conflict-detection set `{SCHEDULED, CONFIRMED, PENDING_SYNC, PENDING}` if you query appointments.
- Don't introduce a queue. Background work stays in `BackgroundTasks` like the rest of the app.
