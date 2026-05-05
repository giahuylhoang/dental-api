# Master Orchestrator — FE↔BE Audit & Hotfix Loop (kiro-cli, Opus 4.5)

You are running on **Claude Opus 4.5** inside `kiro-cli`, autonomously. The user is monitoring progress via the file `scripts/agent_phases/.progress.log` from a separate Claude Code session. Read this entire file before starting.

A more detailed reference (with rationale + design discussion) lives at `scripts/agent_loop.md` — consult it whenever a phase below feels under-specified.

---

## 0. How this loop works

You will execute **27 phases in numerical order**. After each phase passes its acceptance checks, you append exactly one line to `scripts/agent_phases/.progress.log`. The watcher reads that line and updates a UI for the user. Do **not** skip ahead, batch phases, or proceed past a failure.

### Per-phase contract

For each phase below:

1. Read the phase block.
2. Implement the work strictly **tests-first** (write the failing test, then the code).
3. Run the listed acceptance commands. ALL must pass.
4. Append progress line:
   ```
   echo "PHASE_<NN>: PASS $(date -u +%FT%TZ) <one-line summary>" >> /Users/giahuyhoangle/Projects/dental-api/scripts/agent_phases/.progress.log
   ```
5. Move to the next phase.

If a phase fails after **5 honest attempts** (or hits any STOP condition in §3):
```
echo "PHASE_<NN>: FAIL $(date -u +%FT%TZ) <reason>" >> /Users/giahuyhoangle/Projects/dental-api/scripts/agent_phases/.progress.log
echo "<full diagnostic>" >> /Users/giahuyhoangle/Projects/dental-api/scripts/agent_phases/.escalation.log
```
Then **HALT**. Do not proceed.

---

## 1. Operational context

- **Repo:** `/Users/giahuyhoangle/Projects/dental-api`
- **Cross-repo (DO NOT BREAK):** `/Users/giahuyhoangle/Projects/dental-agent` — its `clients/calendar_client.py` calls v1 paths in this repo.
- **Backend:** running on `:8001`, logs at `/tmp/dental-logs/backend.log`. After backend code changes, restart: `lsof -ti:8001 | xargs -r kill -9 && (cd /Users/giahuyhoangle/Projects/dental-api && DATABASE_URL=sqlite:///./dental_clinic.db PORT=8001 nohup uv run python run_api.py > /tmp/dental-logs/backend.log 2>&1 &)`. Wait 3s before next request.
- **Frontend:** running on `:3000`, logs at `/tmp/dental-logs/frontend.log`. Hot-reloads on file changes; rarely needs manual restart.
- **Brave (headless):** `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`
- **Python tests:** `uv run pytest -q` (full suite < 30s).
- **Test fixture for new tests:** `tests/conftest.py:91` (`client`, `client_market_mall`).

## 2. Locked files — never edit

- `database/models.py` (v1 schema is contract-locked)
- `api/main.py` lines ~241–1500 (v1 endpoint bodies). You **may** add middleware registration and new `app.include_router` lines near ~1552.
- v1 paths: `/api/calendar/*`, `/api/appointments/*`, `/api/patients/*`, `/api/providers`, `/api/services`, `/api/leads/*`
- `tests/test_contract_v1.py` (must stay 21/21 green throughout)

## 3. STOP conditions — log to `.escalation.log` and HALT

1. Five consecutive failed attempts on the same phase.
2. Any change makes a previously-green test in `tests/test_contract_v1.py` red.
3. Need to modify `database/models.py` or v1 endpoint bodies.
4. Any test in `dental-agent` repo turns red.
5. A migration / destructive DB op is required.
6. You'd need to call a paid 3rd-party API.

---

## 4. The 27 phases

### PHASE_01 — A1: Backend observability middleware

**Files:**
- NEW `api/middleware/__init__.py` (empty package init)
- NEW `api/middleware/observability.py`
- NEW `api/errors.py`
- EDIT `api/main.py` — register middleware **before** CORS
- NEW `tests/test_observability.py`

**Behavior:** `BaseHTTPMiddleware` reading `X-Request-Id` (uuid4 if absent), echoing on response, storing in `contextvars.ContextVar` named `request_id_ctx`. Logs structured JSON: `{ts, request_id, method, path, status, duration_ms, clinic_id, exc_type|null}`. Catches unhandled exceptions → `JSONResponse(500, {"error_id", "request_id", "message"})`.

**`api/errors.py`:** `error_response(status, code, message, request_id) -> JSONResponse` with envelope `{error_id, code, message, request_id}`. Don't replace existing v1 HTTPExceptions whose payload shapes are asserted by `tests/test_contract_v1.py` — leave those alone.

**Acceptance:**
```bash
uv run pytest tests/test_observability.py tests/test_contract_v1.py -q
# restart backend; then:
curl -i http://localhost:8001/health | grep -i X-Request-Id   # header present
```

**Completion line:** `PHASE_01: PASS <ts> middleware live, X-Request-Id round-trips`

---

### PHASE_02 — A2: SQL event logger

**Files:**
- NEW `database/observability.py`
- EDIT `database/connection.py` — import the observability module so events register on the engine
- EDIT `tests/test_observability.py` — add SQL listener test

**Behavior:** SQLAlchemy `before_cursor_execute` / `after_cursor_execute` events on the engine. When `OBSERVE_SQL=1`, emit `{request_id (from request_id_ctx), statement, duration_ms, rowcount}` via the `dental-receptionist` logger. Off by default. The Phase-10 audit harness will set `OBSERVE_SQL=1`.

**Acceptance:**
```bash
OBSERVE_SQL=1 uv run pytest tests/test_observability.py -q
uv run pytest tests/test_contract_v1.py -q
```

**Completion line:** `PHASE_02: PASS <ts> SQL events emit with request_id`

---

### PHASE_03 — A3: Frontend trace propagation

**File:** EDIT `frontend/src/lib/api.ts`

**Behavior:** In `apiFetch`, generate `crypto.randomUUID()` per call, send as `X-Request-Id`, mirror server's echoed id back onto `ApiError.requestId`. Add dev-only ring buffer at `globalThis.__dental.lastTrace = [...]` capturing `{ts, method, path, status, requestId, durationMs}` (last 50). Skip when `process.env.NODE_ENV === 'production'`.

**Acceptance:**
```bash
cd frontend && npx next build              # no TS errors
# In browser at /settings, open devtools, run: window.__dental.lastTrace
# Expect array entries with requestId for each api call
```

**Completion line:** `PHASE_03: PASS <ts> FE propagates X-Request-Id; __dental.lastTrace populated`

---

### PHASE_04 — A4: Phase A acceptance gate

**Acceptance:**
```bash
uv run pytest tests/test_observability.py tests/test_contract_v1.py -q
curl -i http://localhost:8001/health | grep -i X-Request-Id
cd /Users/giahuyhoangle/Projects/dental-agent && uv run pytest tests/ -q -k calendar_client --ignore=tests/_legacy
```

**Completion line:** `PHASE_04: PASS <ts> observability foundation live, v1 + cross-repo green`

---

### PHASE_05 — B1: Treatment-plans path alias

**Files:**
- EDIT `api/main.py` — add second `app.include_router(treatment_plans_router, prefix="/api/v2/treatment_plans")` while keeping the existing hyphenated mount
- NEW `tests/test_v2_treatment_plans.py`

**Test cases:** create, list, get, items add, present, accept, decline, complete — each tested against **both** `/api/v2/treatment-plans` AND `/api/v2/treatment_plans` to lock the alias.

**Acceptance:**
```bash
uv run pytest tests/test_v2_treatment_plans.py tests/test_contract_v1.py -q
curl -s http://localhost:8001/api/v2/treatment_plans -H 'X-Clinic-Id: default' -o /dev/null -w "%{http_code}\n"   # 200
curl -s http://localhost:8001/api/v2/treatment-plans -H 'X-Clinic-Id: default' -o /dev/null -w "%{http_code}\n"   # 200
```

**Completion line:** `PHASE_05: PASS <ts> treatment_plans alias active, both paths return 200`

---

### PHASE_06 — B2: Scheduling reschedule Pydantic body

**Files:**
- EDIT `api/v2/scheduling/router.py` (~line 296) — replace `body: dict` with `body: RescheduleRequest` (BaseModel: `start_time: datetime`, `end_time: datetime`)
- EDIT `tests/track_ops/test_scheduling.py` — add cases: empty body → 422; missing `end_time` → 422; valid body → 200

**Acceptance:**
```bash
uv run pytest tests/track_ops/test_scheduling.py tests/test_contract_v1.py -q
```

**Completion line:** `PHASE_06: PASS <ts> reschedule body validated by Pydantic, 422 on bad input`

---

### PHASE_07 — B3: `/integrations` clinic-scoping

**Files:**
- EDIT `api/v2/settings/router.py` — add `clinic: Clinic = Depends(get_clinic)` to `get_integrations`. Read per-clinic flags if a row exists; else fall back to env defaults. Preserve all existing keys/types so frontend doesn't break.
- EDIT `tests/test_v2_ai_config.py` — two clinics with different flags see different responses; same baseline when nothing configured.

**Acceptance:**
```bash
uv run pytest tests/test_v2_ai_config.py tests/test_contract_v1.py -q
```

**Completion line:** `PHASE_07: PASS <ts> /integrations scoped to clinic`

---

### PHASE_08 — B4: Voice tab `data-loaded` markers

**Files:**
- EDIT `frontend/src/app/(app)/settings/page.tsx` — add `data-testid="voice-panel"` and `data-loaded={isVoiceLoaded ? 'true' : 'false'}` on the Voice & Persona panel root. Set `isVoiceLoaded=true` after `setVoiceDraft(vCfg)` resolves. Mirror on Disclosure (`data-testid="disclosure-panel"`), Services (`data-testid="services-panel"`), Knowledge (`data-testid="knowledge-panel"`).
- EDIT `frontend/test-integration.mjs` — replace the value-substring `waitForFunction` calls with `page.waitForSelector('[data-testid="voice-panel"][data-loaded="true"]')` and equivalents.

**Acceptance:**
```bash
FE_URL=http://localhost:3000 node frontend/test-integration.mjs   # 6/6 PASS
```

**Completion line:** `PHASE_08: PASS <ts> hydration race fixed via data-loaded; integration test 6/6`

---

### PHASE_09 — Phase A+B exit gate

**Acceptance:**
```bash
uv run pytest tests/test_observability.py tests/test_v2_treatment_plans.py tests/track_ops/test_scheduling.py tests/test_v2_ai_config.py tests/test_contract_v1.py -q
FE_URL=http://localhost:3000 node frontend/test-integration.mjs
cd /Users/giahuyhoangle/Projects/dental-agent && uv run pytest tests/ -q -k calendar_client --ignore=tests/_legacy
```

**Completion line:** `PHASE_09: PASS <ts> A+B exit gate green; ready for audit harness`

---

### PHASE_10 — C1: Brave audit harness skeleton

**Files:**
- NEW `frontend/audit/harness.mjs` — exports:
  - `launchBrave()` → Playwright `Browser` via `chromium.launch({executablePath: '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser', headless: true})`. If `BRAVE_PATH=skip`, fall back to bundled chromium.
  - `recordPage(page)` → attach `console`, `pageerror`, `requestfinished`, `requestfailed` listeners; return `{network, console}` arrays.
  - `joinBackendLog(network, logPath='/tmp/dental-logs/backend.log')` → reads recent backend log lines, joins by `request_id`.
- NEW `frontend/audit/rca.mjs` — `printRCA({page, selector, network, console, backend, expected})` printing the unified report sample (see `scripts/agent_loop.md` Phase C3).

**Output dir convention:** `frontend/audit/out/<page>/<ISO timestamp>/{dom-before.html, dom-after.html, network.json, console.json, backend.json}`.

**Acceptance:**
```bash
cd /Users/giahuyhoangle/Projects/dental-api/frontend && node -e "import('./audit/harness.mjs').then(m => m.launchBrave().then(b => b.close()))"   # exits 0
```

**Completion line:** `PHASE_10: PASS <ts> Brave harness launches headless`

---

### PHASE_11 — C2: Dead-button discovery + baseline

**File:** NEW `frontend/audit/dead_buttons.spec.mjs`

**Behavior:** Iterates `ROUTES = ['/dashboard', '/patients', '/schedule', '/treatment', '/plans', '/lab', '/billing', '/crm', '/communications', '/reports', '/settings']`. For each: `await page.locator('button, [role=button], [draggable=true]').all()`. Skip `data-audit="local-only"`. For each, click (1s network idle window). If no apiFetch AND no navigation → record DEAD. Output `frontend/audit/out/dead-buttons.json` with `[{page, selector, text, why}]`.

**Acceptance:**
```bash
cd /Users/giahuyhoangle/Projects/dental-api/frontend && node audit/dead_buttons.spec.mjs
test "$(jq 'length' audit/out/dead-buttons.json)" -gt 0   # baseline > 0 (sanity: discovery works)
```

**Completion line:** `PHASE_11: PASS <ts> baseline dead-button count = <N>`

---

### PHASE_12 — D1: appointments/[id] wiring

**Page:** `frontend/src/app/(app)/appointments/[id]/page.tsx`
**Wire:** Confirm / Check-in / Start / Complete / No-show / Reschedule / Cancel buttons.
**Endpoints:** `PUT /api/appointments/{id}/cancel`, `PUT /api/appointments/{id}/reschedule`, `PUT /api/appointments/{id}/status`.
**Spec:** NEW `frontend/audit/specs/appointments_detail.spec.mjs` — assert hydration arrives, click → network call → DOM updates → reload preserves state.

**Acceptance:**
```bash
node frontend/audit/specs/appointments_detail.spec.mjs   # green
node frontend/audit/dead_buttons.spec.mjs               # count drops from baseline
uv run pytest tests/test_contract_v1.py -q              # still 21/21
```

**Completion line:** `PHASE_12: PASS <ts> appointments/[id] wired; dead-count: <prev> → <new>`

---

### PHASE_13 — D2: communications wiring

**Page:** `frontend/src/app/(app)/communications/page.tsx`
**Wire:** Send, New message, mark-read, thread switch.
**Endpoints:** `POST /api/v2/communications/send`, `PATCH /api/v2/communications/threads/{key}/read`, `GET /api/v2/communications`.
**Spec:** NEW `frontend/audit/specs/communications.spec.mjs`.

**Acceptance:** spec green; `dead_buttons.spec.mjs` count drops; `tests/test_contract_v1.py` 21/21.

**Completion line:** `PHASE_13: PASS <ts> communications wired; dead-count: <prev> → <new>`

---

### PHASE_14 — D3: CRM wiring

**Page:** `frontend/src/app/(app)/crm/page.tsx`
**Wire:** dnd-kit `onDragEnd` → status change; New lead Save; Activity add.
**Endpoints:** `PUT /api/leads/{id}/status`, `POST /api/leads`, `POST /api/v2/crm/leads/{id}/activities`.
**Spec:** NEW `frontend/audit/specs/crm.spec.mjs`. Note: this is the largest dead cluster (170 elements).

**Acceptance:** spec green; `dead_buttons` drops by ≥30; `tests/test_contract_v1.py` 21/21.

**Completion line:** `PHASE_14: PASS <ts> CRM wired; dead-count: <prev> → <new>`

---

### PHASE_15 — D4: lab wiring

**Page:** `frontend/src/app/(app)/lab/page.tsx`
**Wire:** Kanban column move, New case, status transitions (send/return/remake).
**Endpoints:** `POST /api/v2/lab/cases`, `PATCH /api/v2/lab/cases/{id}/status`, `POST /api/v2/lab/cases/{id}/{send,return,remake}`.
**Spec:** NEW `frontend/audit/specs/lab.spec.mjs`.

**Acceptance:** spec green; dead drops; v1 21/21.

**Completion line:** `PHASE_15: PASS <ts> lab wired; dead-count: <prev> → <new>`

---

### PHASE_16 — D5: billing wiring

**Page:** `frontend/src/app/(app)/billing/page.tsx`
**Wire:** New invoice, claim submit, mark-paid.
**Endpoints:** `POST /api/v2/billing/invoices` (+ `/issue`, `/payments`, `/void`), `POST /api/v2/insurance/claims` (+ `/submit`, `/adjudicate`, `/mark-paid`).
**Spec:** NEW `frontend/audit/specs/billing.spec.mjs`.

**Acceptance:** spec green; dead drops; v1 21/21.

**Completion line:** `PHASE_16: PASS <ts> billing wired; dead-count: <prev> → <new>`

---

### PHASE_17 — D6: treatment wiring

**Page:** `frontend/src/app/(app)/treatment/page.tsx`
**Wire:** Create plan, items, present/accept/decline/complete.
**Endpoints:** `/api/v2/treatment_plans/*` (alias from PHASE_05).
**Spec:** NEW `frontend/audit/specs/treatment.spec.mjs`.

**Acceptance:** spec green; dead drops; v1 21/21.

**Completion line:** `PHASE_17: PASS <ts> treatment wired; dead-count: <prev> → <new>`

---

### PHASE_18 — D7: plans page

**Page:** `frontend/src/app/(app)/plans/page.tsx`
**Decision:** No backend exists. Mark all 15 dead elements with `data-audit="local-only"` so the audit harness ignores them. Rationale: this is a marketing-style pricing page, not a CRUD surface.
**Spec:** NEW minimal `frontend/audit/specs/plans.spec.mjs` — asserts page renders without JS errors.

**Acceptance:** spec green; dead drops by 15.

**Completion line:** `PHASE_18: PASS <ts> plans marked local-only; dead-count: <prev> → <new>`

---

### PHASE_19 — D8: schedule wiring

**Page:** `frontend/src/app/(app)/schedule/page.tsx`
**Wire:** Drag-create appointment, drag-reschedule, event detail action buttons (Confirm/Check-in/Cancel/etc).
**Endpoints:** `GET /api/calendar/slots`, `POST /api/calendar/events`, `PUT /api/appointments/{id}/{cancel,reschedule,status}`.
**Spec:** NEW `frontend/audit/specs/schedule.spec.mjs` — uses Playwright mouse coordinates for FullCalendar drag (the wrapper intercepts standard clicks).

**Acceptance:** spec green; dead drops by ≥50; v1 21/21.

**Completion line:** `PHASE_19: PASS <ts> schedule wired; dead-count: <prev> → <new>`

---

### PHASE_20 — D9: dashboard wiring

**Page:** `frontend/src/app/(app)/dashboard/page.tsx`
**Wire:** Drawer Save → reuse PHASE_19 endpoints. Modal actions (Confirm/Check-in/Start/etc) → reuse PHASE_12 endpoints. Export day → if no backend, mark `data-audit="local-only"`.
**Spec:** NEW `frontend/audit/specs/dashboard.spec.mjs`.

**Acceptance:** spec green; dead drops; v1 21/21.

**Completion line:** `PHASE_20: PASS <ts> dashboard wired; dead-count: <prev> → <new>`

---

### PHASE_21 — D10: patients/[id] wiring

**Page:** `frontend/src/app/(app)/patients/[id]/page.tsx`
**Wire:** Tab API hydration for medical-history, insurance, documents, notes, consents, tooth-chart. Schedule Drawer + New invoice.
**Endpoints:** `/api/v2/clinical/patients/{id}/{tooth-chart,medical-history,insurance,documents,notes,consents}`.
**Spec:** NEW `frontend/audit/specs/patients_detail.spec.mjs`.

**Acceptance:** spec green; dead drops; v1 21/21.

**Completion line:** `PHASE_21: PASS <ts> patients/[id] wired; dead-count: <prev> → <new>`

---

### PHASE_22 — D11: reports wiring + new tests

**Page:** `frontend/src/app/(app)/reports/page.tsx`
**Wire:** KPI tiles, Export CSV.
**Endpoints:** `GET /api/v2/reporting/{kpi,production-by-provider,remake-rate-by-lab}`.
**Files:**
- EDIT `frontend/src/app/(app)/reports/page.tsx`
- NEW `frontend/audit/specs/reports.spec.mjs`
- NEW `tests/test_v2_reporting.py` — closes the zero-coverage gap; 3 endpoints, sunny-day + tenant isolation cases.

**Acceptance:**
```bash
uv run pytest tests/test_v2_reporting.py tests/test_contract_v1.py -q
node frontend/audit/specs/reports.spec.mjs
node frontend/audit/dead_buttons.spec.mjs   # length should now be 0 (or only data-audit="local-only" exclusions)
```

**Completion line:** `PHASE_22: PASS <ts> reports wired + tested; dead-count: <prev> → 0`

---

### PHASE_23 — E1: Schema validation + OpenAPI gate

**Files:**
- Sweep `api/v2/**` for any `body: dict` or untyped form params; replace with Pydantic models.
- NEW `tests/test_openapi_sync.py` — asserts every route in `app.routes` has non-empty `requestBody` (non-GET) and `responses["200"]` schema; route-count snapshot at `tests/_snapshots/openapi_route_counts.json`.
- NEW `tests/test_v2_validation.py` — one negative test per endpoint asserting 422 on missing-required.
- Add `Field(...)` constraints where obvious: `min_length=1` on names, `ge=0` on amounts.

**Acceptance:**
```bash
uv run pytest tests/test_openapi_sync.py tests/test_v2_validation.py tests/test_contract_v1.py -q
grep -RIn "body: dict" api/v2/ | grep -v "__pycache__"   # empty
```

**Completion line:** `PHASE_23: PASS <ts> 0 untyped bodies, OpenAPI snapshot locked`

---

### PHASE_24 — E2: Observability dashboard

**File:** NEW `frontend/audit/report.mjs`

**Behavior:** Reads `frontend/audit/out/**`, emits `frontend/audit/out/REPORT.md` with: dead-button trend over time, top 10 latencies, top 10 exceptions by `exc_type`. Runs in <5s.

Also: every failing E2E spec must attach the joined trace bundle to its failure (use `test.info().attachments` or equivalent).

**Acceptance:**
```bash
cd frontend && time node audit/report.mjs   # < 5s, REPORT.md present
ls -la audit/out/REPORT.md
```

**Completion line:** `PHASE_24: PASS <ts> REPORT.md generated; failures attach trace bundles`

---

### PHASE_25 — E3: Read-side caching

**Backend:** add `ETag` (sha256 prefix of payload) + `Cache-Control: private, max-age=10` on:
- `GET /api/v2/settings/clinic`
- `GET /api/v2/settings/ai/{voice,disclosure,services-bookable,knowledge}`
- `GET /api/v2/reporting/*`
- `GET /api/services`, `GET /api/providers`

`If-None-Match` match → 304. **Do NOT** cache mutations or `/api/calendar/*`, `/api/appointments/*` (real-time).

**Frontend:** `apiFetchCached(path, ttl)` in `lib/api.ts` using `sessionStorage` keyed by path; revalidates via `If-None-Match` after TTL.

**Acceptance:** with `OBSERVE_SQL=1`, two consecutive `GET /api/v2/settings/ai/voice` within 10s produce SQL on the first request and 0 SQL on the second (verified via the structured log). New test: `tests/test_caching.py`.

**Completion line:** `PHASE_25: PASS <ts> caching live; verified 0 SQL on warm read`

---

### PHASE_26 — E4: Edge-case test seeder

**Files:**
- NEW `scripts/seed_edge_cases.py` — `seed_empty(db)`, `seed_maxed(db)`, `seed_adversarial(db)`, `seed_concurrent_test(db)`.
- NEW `tests/test_edge_cases.py` — `pytest -k edge_<scenario>` cases:
  - `edge_empty` — clean clinic renders without JS errors via Brave harness.
  - `edge_maxed` — 1k patients / 5k appointments / 200 plans — pages render under 3s p95.
  - `edge_adversarial` — unicode (`José`, `田中`, 4-byte emoji), very long strings, SQL-quote chars round-trip cleanly.
  - `edge_concurrent` — two parallel `POST /api/calendar/events` for the same slot — exactly one returns 409.

**Acceptance:**
```bash
uv run pytest tests/test_edge_cases.py -q
```

**Completion line:** `PHASE_26: PASS <ts> edge-case suite green (4/4 scenarios)`

---

### PHASE_27 — Final sweep + HANDOFF_REPORT.md

**Acceptance (all must be simultaneously green):**
```bash
# In dental-api
uv run pytest -q
uv run pytest tests/test_contract_v1.py tests/test_contract_v2_ai_config.py -q
cd frontend && npx next build
cd frontend && npx playwright test
node audit/dead_buttons.spec.mjs
test "$(jq 'length' audit/out/dead-buttons.json)" = "0"
# In dental-agent
cd /Users/giahuyhoangle/Projects/dental-agent && uv run pytest tests/ -q -k calendar_client --ignore=tests/_legacy
```

**Then write** `frontend/audit/out/HANDOFF_REPORT.md` covering: dead-button counts before/after per phase; files added/edited; tests added; any items deferred to follow-up; cross-repo regression check status.

**Completion line:** `PHASE_27: PASS <ts> ALL GREEN — handoff report at frontend/audit/out/HANDOFF_REPORT.md`

After PHASE_27 PASS: write a final summary line:
```
echo "LOOP_DONE: $(date -u +%FT%TZ) all 27 phases complete" >> /Users/giahuyhoangle/Projects/dental-api/scripts/agent_phases/.progress.log
```

Then halt. The user's monitor will pick this up.

---

## 5. Begin

Start with **PHASE_01**. Do not skip ahead. Do not batch. Tests first, every time.
