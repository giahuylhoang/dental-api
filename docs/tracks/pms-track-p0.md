# PMS Track P0 — Backend gap fill

You are kiro-cli running headless. Implement the backend gaps below so the gate `make test-pms-p0` passes. The gate is:

1. `uv run pytest tests/track_pms_p0 -q` — pytest suite you'll write
2. `uv run pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q` — v1 contract MUST stay green
3. `cd frontend && npm run gen:api && npm run build` — OpenAPI spec must regenerate types and the frontend must still build

## Working directory & repo conventions

- Repo root: `/Users/giahuyhoangle/Projects/dental-api`
- Backend: FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Alembic. Multi-tenant via `X-Clinic-Id` header (default `"default"`).
- v2 router: `api/v2/clinical/router.py` and sibling routers under `api/v2/`. Mounted in `api/main.py` at the existing v2 prefix.
- Tests use **in-memory SQLite** seeded by `tests/conftest.py` (`client` fixture creates default clinic, providers, services). DO NOT introduce hardcoded URLs — use `client` fixture (TestClient).
- All endpoints MUST scope queries by `clinic_id` (from the `X-Clinic-Id` header → `get_clinic` dependency).
- Use `uv run pytest` not `pytest`.
- Use `uv run alembic ...` not `alembic ...`.

## Endpoints to add

### 1. `POST /api/v2/clinical/documents/upload`
- Multipart/form-data: file, kind (`photo|xray|consent|other`), patient_id (form field).
- Save the upload to `./var/uploads/{clinic_id}/{sha256[:2]}/{sha256}{ext}` (create dirs as needed). Use the file's actual sha256 as both the filename and the dedup key.
- Insert a `Document` row (database/clinical/models.py) with `storage_url` set to the relative path `var/uploads/...`, `sha256`, `kind`, `patient_id`, `clinic_id`, `mime_type`, `size_bytes`.
- If a `Document` row with the same `(clinic_id, sha256)` already exists, return that row and do NOT write the file again (idempotent dedup).
- Response 200: `{ id, storage_url, sha256, mime_type, size_bytes, kind, patient_id, deduped: bool }`.

### 2. `GET /api/v2/clinical/patients/{patient_id}/tooth-chart`
Returns 32 entries (one per tooth, ISO 1–32). If the row doesn't exist for a tooth, synthesize `{tooth_number, status: "present", surface_notes: null}` so the response is always 32 long.

### 3. `POST /api/v2/clinical/patients/{patient_id}/tooth-chart`
Body: `[{ tooth_number, status, surface_notes? }]` (partial; only the listed teeth are upserted). Status enum is the column enum on `ToothChartEntry`. Upsert by `(clinic_id, patient_id, tooth_number)`. Set `last_examined_at = now()`. Returns the same 32-entry shape as the GET.

### 4. `PUT /api/v2/clinical/patients/{patient_id}/insurance/{insurance_id}`
Update an existing `PatientInsurance` row scoped to `(clinic_id, patient_id, id)`. Body shape mirrors the existing POST. 404 if missing.

### 5. `DELETE /api/v2/clinical/patients/{patient_id}/insurance/{insurance_id}`
Hard delete. 204 on success, 404 if missing.

### 6. `GET /api/v2/clinical/denture-cases/{case_id}/implants`
Returns the list of `DentureCaseImplant` rows for the case (scoped to clinic_id via the parent denture_case).

### 7. `POST /api/v2/clinical/denture-cases/{case_id}/implants`
Body: `{ tooth_position, vendor, model?, lot_number, surface_treatment?, abutment_type?, placed_date? }`. Insert and return the new row.

### 8. `POST /api/v2/billing/invoices/from-plan`
Body: `{ treatment_plan_id, patient_id, gst_rate? }`. Behavior:
- Load all `treatment_plan_items` for the plan.
- Build invoice lines with `description = procedure_code + " — " + (item.description or "")`, `qty = 1`, `unit_price_cents = item.fee_cents`.
- Create the invoice (status=draft) using the same logic as `POST /api/v2/billing/invoices` (subtotal, gst, total, balance).
- Return the new invoice (same shape as POST /invoices).

## OpenAPI spec sync

Update `docs/openapi-v2.yaml` so every route added above (and any v2 routes already in `api/v2/*` that are missing from the spec) is documented. The frontend types are regenerated from this spec via `npm run gen:api`. The build will fail if the generated types are inconsistent with the components that import them — which is the gate we want.

## Tests to write

Create `tests/track_pms_p0/test_p0_endpoints.py`. Tests should use the `client` fixture from `tests/conftest.py`. At minimum:

```python
def test_documents_upload_and_dedup(client):
    # Create patient first via /api/patients
    # Upload file, expect deduped=False, then upload same bytes, expect deduped=True
    ...

def test_tooth_chart_get_returns_32_entries(client):
    # Create patient, GET tooth-chart, expect 32 entries with status=present
    ...

def test_tooth_chart_post_upserts(client):
    # POST with tooth 14 status=missing, GET, expect tooth 14 missing, others present
    ...

def test_insurance_put_and_delete(client):
    # POST insurance, PUT to update carrier, DELETE, then GET returns empty
    ...

def test_denture_case_implants_create_and_list(client):
    # Create denture case, POST implant, GET, expect 1 row
    ...

def test_invoice_from_plan(client):
    # Create patient, plan, items, then POST /from-plan, expect invoice with line per item
    ...
```

Also add `tests/track_pms_p0/__init__.py` (empty file).

## Constraints

- DO NOT modify v1 endpoints (`/api/*`) or v1 response shapes.
- DO NOT modify `tests/test_contract_v1.py`.
- DO NOT modify any existing column types in `database/models.py`.
- DO NOT modify `tests/conftest.py` (it already has the env-hygiene block).
- All migrations are already applied; no new migrations needed (all tables already exist).
- Use Pydantic v2 syntax (`model_config = ConfigDict(...)`, `Field(...)`).

## Commands you can run

```bash
uv run pytest tests/track_pms_p0 -q
uv run pytest tests/test_api.py tests/test_schema.py tests/test_contract_v1.py -q
cd frontend && npm run gen:api && npm run build
make test-pms-p0
```

When `make test-pms-p0` exits 0, you are done.
