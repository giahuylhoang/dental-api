# Agent Handoff Brief — FE↔BE Audit & Hotfix Loop

**Read this whole file before running any tool.** It is self-contained: you do not need access to any prior chat. Source of truth for design decisions is the plan at `/Users/giahuyhoangle/.claude/plans/enchanted-whistling-tiger.md`; this brief is the operational version.

You are running on **Claude Opus 4.5** inside `kiro-cli`. The user is asleep / away. Run autonomously until done or until you hit a STOP condition.

**Phase A is already complete and verified** (A1 middleware, A2 SQL event logger, A3 frontend trace propagation, A4 acceptance gate — `pytest tests/test_observability.py tests/test_contract_v1.py -q` is 27/27 green; `curl /health` returns `X-Request-Id`; cross-repo `dental-agent` calendar_client tests are 23/23). **Begin at B1.** The Phase A sections below are kept as reference only — do not re-implement them.

## 1. Repo & environment

- Repo: `/Users/giahuyhoangle/Projects/dental-api` — FastAPI backend + Next.js frontend.
- Cross-repo dependency (do **NOT** break): `/Users/giahuyhoangle/Projects/dental-agent` — its `clients/calendar_client.py` calls v1 paths in this repo.
- Backend running in background on `:8001` (logs: `/tmp/dental-logs/backend.log`).
- Frontend running in background on `:3000` (logs: `/tmp/dental-logs/frontend.log`).
- If either is down: `lsof -ti:8001,3000 | xargs -r kill -9` then re-launch with the commands at the bottom of this file.
- Brave (headless executable for Playwright): `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`.
- Python: `uv run pytest -q`. Node: `npm` from `frontend/`.

## 2. Locked files — never edit

- `database/models.py` (v1 schema is contract-locked).
- `api/main.py` lines ~241–1500 (v1 endpoint bodies). You **may** add middleware registration and new `app.include_router` calls near the bottom (~line 1552), but do not modify v1 handler bodies.
- `clients/calendar_client.py` paths: `/api/calendar/*`, `/api/appointments/*`, `/api/patients/*`, `/api/providers`, `/api/services`, `/api/leads/*`.
- `tests/test_contract_v1.py` — must stay green (21/21).

## 3. Audit findings already known (do not re-discover)

- ~1,100 interactive elements across 13 frontend pages; only ~115 (~10%) call `api.*`. The rest are local-state or no-op.
- **Path mismatch:** backend serves `/api/v2/treatment-plans` (hyphen); `frontend/src/lib/api.ts` calls `/api/v2/treatment_plans` (underscore). Fix backend by adding the underscore prefix as an *alias*; do not break the existing hyphenated path.
- **Validation gap:** `api/v2/scheduling/router.py:296` — `body: dict`. Replace with a Pydantic `RescheduleRequest`.
- **Tenant-leak risk:** `api/v2/settings/router.py` — `get_integrations` is not clinic-scoped. Add `Depends(get_clinic)`.
- **Voice tab race:** `frontend/test-integration.mjs` fails because the `useEffect` hydration finishes after the test queries the input. Fix with a `data-loaded` marker on the panel root, not by sleeping.
- **Zero tests** on `api/v2/treatment_plans/router.py` and `api/v2/reporting/router.py`. Add coverage as part of the relevant phase.

## 4. Execution plan — strictly in order

### LOOP A — Observability foundation + verified bug fixes

For each item below: **write the test first**, run it red, implement, run it green, then move on. Do not batch.

#### A1 — Backend request middleware
- NEW `api/middleware/__init__.py` (empty package init) and `api/middleware/observability.py` containing a `BaseHTTPMiddleware` that:
  - Reads `X-Request-Id` from inbound; generates a uuid4 if absent. Echoes on response.
  - Stores the request id in a `contextvars.ContextVar` named `request_id_ctx` (so the SQL logger in A2 can read it).
  - Logs one structured JSON line per request: `ts (ISO8601), request_id, method, path, status, duration_ms, clinic_id (from X-Clinic-Id header), exc_type (or null)`.
  - Catches unhandled exceptions, returns `JSONResponse(status_code=500, content={"error_id": "...", "request_id": "...", "message": "Internal server error"})`.
- NEW `api/errors.py` exposing `error_response(status, code, message, request_id)` returning a `JSONResponse` with the same envelope. Migrate any existing 4xx HTTPExceptions to use it where convenient — but keep payload shapes that v1 contract tests assert on **unchanged**.
- EDIT `api/main.py` — register the middleware **before** CORS.
- TEST `tests/test_observability.py` covering: (a) `X-Request-Id` round-trip, (b) generated id when absent, (c) structured log shape (capture via `caplog`), (d) 500 envelope contains `error_id` and `request_id`.

#### A2 — SQL event logger
- NEW `database/observability.py` registering SQLAlchemy `before_cursor_execute`/`after_cursor_execute` events on the `engine` exported by `database/connection.py`. When `OBSERVE_SQL=1` env, emit `{request_id, statement, duration_ms, rowcount}` via the `dental-receptionist` logger.
- The handler reads `request_id` from `request_id_ctx` (from A1).
- Off by default in prod. The `frontend/audit/harness.mjs` will set `OBSERVE_SQL=1` for audit runs.
- Append a small test in `tests/test_observability.py` verifying the listener fires and includes the request id.

#### A3 — Frontend trace propagation
- EDIT `frontend/src/lib/api.ts`:
  - In `apiFetch`, generate a `crypto.randomUUID()` per call, send as `X-Request-Id` header, and store the header echoed by the server back onto `ApiError.requestId` on failure.
  - Add a dev-only ring buffer at `globalThis.__dental ||= {}; __dental.lastTrace = [...]` capturing `{ts, method, path, status, requestId, durationMs}` for the last 50 requests. Skip when `process.env.NODE_ENV === 'production'`.
- No frontend test required here (the audit harness in C1 will read `__dental.lastTrace` directly).

#### A4 — Phase A acceptance
- `uv run pytest tests/test_observability.py tests/test_contract_v1.py -q` → green.
- `curl -i http://localhost:8001/health | grep -i X-Request-Id` → header present.

#### B1 — Treatment-plans path alias
- EDIT `api/main.py` near the existing `app.include_router(...)` for treatment_plans (search for `treatment_plans`). Add a *second* `app.include_router(treatment_plans_router, prefix="/api/v2/treatment_plans")`. Keep the original hyphenated mount.
- NEW `tests/test_v2_treatment_plans.py` — covers create, list, get, items add, present, accept, decline, complete. Test on **both** `/api/v2/treatment-plans` and `/api/v2/treatment_plans` to lock the alias.
- Acceptance: both paths return 200 for the same payload; `tests/test_contract_v1.py` still green.

#### B2 — Scheduling reschedule validation
- EDIT `api/v2/scheduling/router.py:296` — replace `body: dict` with a Pydantic `RescheduleRequest(BaseModel)` (`start_time: datetime`, `end_time: datetime`).
- Add to existing `tests/track_ops/test_scheduling.py`: empty body → 422; missing `end_time` → 422; valid body → 200.

#### B3 — `/integrations` clinic scoping
- EDIT `api/v2/settings/router.py` — add `clinic: Clinic = Depends(get_clinic)` to `get_integrations`. Read per-clinic flags if a row exists; else fall back to env defaults (preserve existing keys/types so frontend doesn't break).
- Append to `tests/test_v2_ai_config.py` — two clinics with different flags see different responses. Same payload across clinics when nothing is configured.

#### B4 — Voice tab hydration race
- EDIT `frontend/src/app/(app)/settings/page.tsx`:
  - Add `data-testid="voice-panel"` and `data-loaded={isVoiceLoaded ? 'true' : 'false'}` on the Voice & Persona panel root.
  - Set `isVoiceLoaded=true` after `setVoiceDraft(vCfg)` resolves in the `useEffect` at line ~111.
  - Mirror the pattern on Disclosure (`data-testid="disclosure-panel"`), Services (`data-testid="services-panel"`), Knowledge (`data-testid="knowledge-panel"`).
- EDIT `frontend/test-integration.mjs` — replace the value-substring `waitForFunction` calls with `page.waitForSelector('[data-testid="voice-panel"][data-loaded="true"]')` and equivalents.
- Acceptance: `FE_URL=http://localhost:3000 node frontend/test-integration.mjs` → 6/6 PASS.

#### Phase A+B exit gate

```bash
uv run pytest tests/test_observability.py tests/test_v2_treatment_plans.py tests/track_ops/test_scheduling.py tests/test_v2_ai_config.py tests/test_contract_v1.py -q
FE_URL=http://localhost:3000 node frontend/test-integration.mjs
cd /Users/giahuyhoangle/Projects/dental-agent && uv run pytest tests/ -q -k calendar_client --ignore=tests/_legacy
```

All three commands must be green before continuing to LOOP B.

### LOOP B — Brave-headless audit + page wiring

#### C1 — Brave audit harness
- NEW `frontend/audit/harness.mjs`:
  - Exports `launchBrave()` returning a Playwright `Browser` via `chromium.launch({ executablePath: BRAVE, headless: true })` where `BRAVE = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'`. Fall back to bundled chromium if env `BRAVE_PATH=skip` is set.
  - Exports `recordPage(page)` attaching listeners: `console`, `pageerror`, `requestfinished`, `requestfailed` (all into per-test arrays).
  - Exports `joinBackendLog(network, logPath = '/tmp/dental-logs/backend.log')` that reads recent backend log lines and, for each FE network entry, attaches the matching backend record by `request_id`.
  - Output dir: `frontend/audit/out/<page>/<ISO timestamp>/{dom-before.html, dom-after.html, network.json, console.json, backend.json, trace.zip}`.
- NEW `frontend/audit/rca.mjs` — exports `printRCA({page, selector, network, console, backend, expected})` that prints the unified report sample shown in the plan (Phase C3).

#### C2 — Dead-button discovery
- NEW `frontend/audit/dead_buttons.spec.mjs`:
  - Iterates over `ROUTES = ['/dashboard', '/patients', '/schedule', '/treatment', '/plans', '/lab', '/billing', '/crm', '/communications', '/reports', '/settings']`.
  - For each: `await page.locator('button, [role=button], [draggable=true]').all()`. Skip elements with `data-audit="local-only"`. For each, click (with a 1s network idle window). If no `apiFetch` call AND no navigation → record as DEAD with `{page, selector, text, why}`.
  - Writes `frontend/audit/out/dead-buttons.json`.
- Run it once and commit nothing — this is the baseline. Capture the count via `jq 'length' frontend/audit/out/dead-buttons.json`.

#### D1–D11 — Per-page wiring (TDD, in this exact order)

For each row in this table:

| # | Page | First handlers | Backend |
|---|------|----------------|---------|
| 1 | `appointments/[id]` | Confirm, Check-in, Start, Complete, No-show, Reschedule, Cancel | `PUT /api/appointments/{id}/{cancel,reschedule,status}` |
| 2 | `communications` | Send, New message, mark-read, thread switch | `POST /api/v2/communications/send`, `PATCH /threads/{key}/read`, `GET /api/v2/communications` |
| 3 | `crm` | dnd-kit `onDragEnd` → status, New lead Save | `PUT /api/leads/{id}/status`, `POST /api/leads`, `POST /api/v2/crm/leads/{id}/activities` |
| 4 | `lab` | Kanban move, New case, send/return/remake | `POST /api/v2/lab/cases`, `PATCH /api/v2/lab/cases/{id}/status`, send/return/remake |
| 5 | `billing` | New invoice, claim submit, mark-paid | `POST /api/v2/billing/invoices`, `POST /api/v2/insurance/claims`, adjudicate/mark-paid |
| 6 | `treatment` | Create plan, present/accept/decline/complete | `/api/v2/treatment_plans/*` (alias from B1) |
| 7 | `plans` | Pricing CTAs (or mark `data-audit="local-only"`) | (none) |
| 8 | `schedule` | Drag-create, drag-reschedule, event actions | `GET /api/calendar/slots`, `POST /api/calendar/events`, `PUT /api/appointments/{id}/{cancel,reschedule}` |
| 9 | `dashboard` | Drawer Save, modal actions, Export day | reuse 1/8 endpoints |
| 10 | `patients/[id]` | Tab API hydration, Schedule Drawer, New invoice | `/api/v2/clinical/patients/{id}/{tooth-chart,medical-history,insurance,documents,notes,consents}` |
| 11 | `reports` | KPI tiles, Export CSV | `GET /api/v2/reporting/{kpi,production-by-provider,remake-rate-by-lab}` (also add `tests/test_v2_reporting.py` — closes the zero-coverage gap) |

Per page:
1. Write `frontend/audit/specs/<page>.spec.mjs` using `harness.mjs`. Assert: hydration arrives, click → network call → DOM updates with server data → reload preserves state.
2. Run the spec; it must fail (red).
3. Replace the local-state mutation with `api.*` in the page file. Keep the `process.env.NEXT_PUBLIC_USE_MOCKS === '1'` early-return mock fallback.
4. Re-run the spec; must pass.
5. Re-run `node frontend/audit/dead_buttons.spec.mjs`. The dead count must drop strictly.
6. Run `uv run pytest tests/test_contract_v1.py -q` — still 21/21.

### LOOP C — Architectural improvements

Each must close with its DoD checklist green.

#### E1 — Schema validation + OpenAPI gate
- Sweep `api/v2/**` for any handler with `body: dict` or untyped form params. Replace with Pydantic models. (B2 covered scheduling; check the rest.)
- NEW `tests/test_openapi_sync.py`:
  - Asserts every route in `app.routes` has a non-empty `requestBody` (for non-GET) and `responses["200"]` schema.
  - Asserts the **count** of routes per tag matches a snapshot stored at `tests/_snapshots/openapi_route_counts.json`. Snapshot file is created on first run; subsequent runs that change counts fail and require updating the snapshot deliberately.
- Add `Field(...)` constraints where obvious: `min_length=1` on names, `ge=0` on amounts, regex on `id` formats that follow a pattern.
- DoD: zero `body: dict` in `api/v2/**`; openapi snapshot test green; one negative-test case per endpoint asserting 422 on missing-required (group these into `tests/test_v2_validation.py`).

#### E2 — Observability dashboard
- NEW `frontend/audit/report.mjs`:
  - Reads `frontend/audit/out/**` and emits `frontend/audit/out/REPORT.md` with: dead-button trend over time, top 10 latencies, top 10 exceptions by `exc_type`.
  - Runs in <5s on the existing data set.
- DoD: `node frontend/audit/report.mjs` produces a valid Markdown file; every failing E2E spec attaches the joined trace bundle to its failure output (use `test.info().attachments`).

#### E3 — Read-side caching
- BACKEND: add `ETag` (sha256 of payload prefix) + `Cache-Control: private, max-age=10` on read-heavy GETs:
  - `GET /api/v2/settings/clinic`
  - `GET /api/v2/settings/ai/{voice,disclosure,services-bookable,knowledge}`
  - `GET /api/v2/reporting/*`
  - `GET /api/services`, `GET /api/providers`
  - On `If-None-Match` match → 304.
- FRONTEND: add `apiFetchCached(path, ttl)` in `lib/api.ts` using `sessionStorage` keyed by path. Revalidate via `If-None-Match` after TTL.
- **Do NOT** cache anything mutation-bearing or `/api/calendar/*`, `/api/appointments/*` (real-time).
- DoD: with `OBSERVE_SQL=1`, two consecutive `GET /api/v2/settings/ai/voice` within 10s produce SQL on the first and zero SQL on the second (verified by reading the structured logs in the test).

#### E4 — Edge-case test seeder
- NEW `scripts/seed_edge_cases.py` exporting `seed_empty(db)`, `seed_maxed(db)`, `seed_adversarial(db)`, `seed_concurrent_test(db)` (the latter prepares fixtures, the actual concurrency test lives in pytest).
- NEW `tests/test_edge_cases.py` with `pytest -k edge_<scenario>` cases:
  - `edge_empty` — clean clinic renders without JS errors via Brave harness.
  - `edge_maxed` — 1k patients / 5k appointments — pages still render under 3s p95.
  - `edge_adversarial` — unicode (`José`, `田中`, 4-byte emoji), very long strings, SQL-quote chars round-trip cleanly.
  - `edge_concurrent` — two parallel `POST /api/calendar/events` for the same slot — exactly one returns 409.
- DoD: all four `edge_` tests green.

## 5. Exit criteria (loop is done when all are simultaneously true)

```bash
# In dental-api
uv run pytest -q                                                # all tests green
uv run pytest tests/test_contract_v1.py -q                      # 21/21
cd frontend && npx playwright test                              # green
cd frontend && npx next build                                   # clean
node audit/dead_buttons.spec.mjs                                # length == 0 (or only data-audit="local-only" exclusions)

# In dental-agent
cd /Users/giahuyhoangle/Projects/dental-agent
uv run pytest tests/ -q -k calendar_client --ignore=tests/_legacy   # green
```

When all five are green at once, write a final summary at `frontend/audit/out/HANDOFF_REPORT.md` with: dead-button counts before/after per phase, files changed, tests added, deferred items (anything you escalated). Exit.

## 6. STOP conditions — escalate, do not push past

Stop and write `frontend/audit/out/ESCALATION.md` describing the situation when any of these triggers:

1. Five consecutive failed iterations on the same dead-button entry.
2. Any change makes a previously-green test in `tests/test_contract_v1.py` red.
3. You feel the need to modify `database/models.py` or v1 endpoint bodies.
4. Any test in the `dental-agent` repo turns red.
5. A migration or destructive DB operation is required (drop column, type change).
6. You hit any unauthenticated 3rd-party API or paid resource.

## 7. Operational tips

- The frontend dev server hot-reloads on file changes; a restart is rarely needed.
- The backend (uvicorn `run_api.py`) does **not** auto-reload in this background setup. After backend code changes, restart it: `lsof -ti:8001 | xargs -r kill -9 && (cd /Users/giahuyhoangle/Projects/dental-api && DATABASE_URL=sqlite:///./dental_clinic.db PORT=8001 nohup uv run python run_api.py > /tmp/dental-logs/backend.log 2>&1 &)`.
- After a schema-touching change, also run `python scripts/sync_db.py` (it is idempotent).
- Run `uv run pytest -q` frequently. The full suite takes <30s.
- Never use `--no-verify` or skip pre-commit hooks. If hooks fail, fix the root cause.
- Use the existing `client` fixture (`tests/conftest.py:91`) for new tests — it seeds `default` clinic in in-memory SQLite.

Begin with **B1**. Mark each phase complete in your scratchpad as you go.
