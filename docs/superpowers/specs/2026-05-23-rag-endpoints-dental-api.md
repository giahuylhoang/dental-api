# RAG Endpoints — dental-api implementation spec

**Date:** 2026-05-23
**Scope:** dental-api side of the cross-repo Clinic Q&A RAG design.
**Canonical design (cross-repo):** [`dental-agent/docs/superpowers/specs/2026-05-23-clinic-qa-rag-design.md`](../../../../dental-agent/docs/superpowers/specs/2026-05-23-clinic-qa-rag-design.md). Read that first — this file only records the dental-api-repo-specific implementation decisions.

## What this implementation ships

Two read endpoints that the voice agent's `CalendarClient` already targets:

- `GET /clinics/{clinic_id}/faqs` → `{"faqs": [{question, answer}, ...]}`
- `POST /rag/answer` → `{status, answer, confidence, sources}`

Plus the dental-api-side admin write routes the canonical spec enumerates (called by admin-api / portal frontend; needed so we can populate test data):

- `POST   /admin/clinics/{id}/faqs`           + PATCH/DELETE
- `POST   /admin/clinics/{id}/rag_docs`       + PATCH/DELETE

## Storage

**Postgres + pgvector** locally (Docker) and in prod. SQLite fallback is dropped for these endpoints — they require pgvector, and the canonical spec explicitly chooses Postgres so HNSW + per-tenant filter works.

Local dev: `docker run --name dental-pg -e POSTGRES_PASSWORD=dev -p 5432:5432 -d pgvector/pgvector:pg16`. Connection: `postgresql://postgres:dev@localhost:5432/dental`.

## Alembic migration

One new migration `add_rag_tables`:
1. `CREATE EXTENSION IF NOT EXISTS vector;`
2. Create `clinic_faqs` (id, clinic_id, question, answer, ordering, created_at, updated_at) — exact columns from canonical spec.
3. Create `rag_docs` (id, clinic_id, doc_title, content, voice_ready, embedding VECTOR(768), metadata JSONB, created_at, updated_at) — exact columns from canonical spec.
4. Index on `(clinic_id, ordering)` for faqs; index on `clinic_id` and HNSW on `embedding` for rag_docs.

No downgrade path beyond `DROP TABLE` — these are new tables, no data migration risk.

## File layout

| File | Purpose |
|---|---|
| `database/models.py` | Add `ClinicFaq`, `RagDoc` SQLAlchemy models with `pgvector.sqlalchemy.Vector(768)` column |
| `alembic/versions/<rev>_add_rag_tables.py` | The migration above |
| `services/rag/embeddings.py` | Thin async wrapper around Gemini `text-embedding-005` via `httpx.AsyncClient`. One function: `embed(text: str) -> list[float]`. Reads `GEMINI_API_KEY` from env. |
| `services/rag/retrieval.py` | One function: `answer(db, clinic_id, question) -> {status, answer, confidence, sources}`. Embeds the question, runs `SELECT … ORDER BY embedding <=> :q_embed LIMIT 5 WHERE clinic_id = :cid`, applies confidence threshold (0.6), returns the top doc's `voice_ready` (falling back to `content` excerpt). |
| `api/rag/router.py` | `POST /rag/answer` with LRU cache (60s TTL, keyed by `(clinic_id, normalized_question)`). `GET /clinics/{clinic_id}/faqs`. Mounted at root in `api/main.py`. |
| `api/admin/rag_router.py` | Admin CRUD for faqs + rag_docs. Embeddings filled via FastAPI `BackgroundTasks` on POST/PATCH of `rag_docs.content`. |
| `tests/test_rag_endpoints.py` | Contract tests, see below. |

## New deps (`requirements.txt`)

- `pgvector>=0.2.0` (SQLAlchemy bindings)
- `httpx` (already present, used elsewhere)

No `sentence-transformers`, no torch — we use Gemini's embeddings API.

## Env vars

- `GEMINI_API_KEY` — required for `/rag/answer`. Read in `services/rag/embeddings.py`. Returned 503 with structured error if missing.
- `DATABASE_URL` — must point at Postgres + pgvector instance.

`/admin/clinics/{id}/faqs/*` does NOT need `GEMINI_API_KEY` (no embeddings written for FAQs). Admin RAG-doc writes enqueue embedding as a `BackgroundTask` so the response returns 202 even if the embed call is slow.

## Tests

`tests/test_rag_endpoints.py` uses the existing TestClient + Postgres fixture (one is needed — see plan). Cases:

1. **FAQ happy path** — seed 3 rows for one clinic, GET returns them in `ordering` order.
2. **FAQ unknown clinic** — 404.
3. **FAQ empty** — returns `{"faqs": []}`, not 404.
4. **`/rag/answer` happy path** — seed rag_docs with deterministic stub embeddings, POST a question whose embedding is closest to one doc, assert `status=ok` and `sources[0].doc_id` matches.
5. **`/rag/answer` no_match** — POST a question with low similarity to all docs, assert `status=no_match`.
6. **`/rag/answer` missing GEMINI_API_KEY** — assert 503 with explicit reason.
7. **Cache hit** — POST the same question twice; second call shouldn't call the embedder. Use a counter-mock for the embedder.
8. **Background embed on write** — POST `/admin/clinics/{id}/rag_docs`, assert the row exists immediately with `embedding=NULL`, then await BackgroundTasks completion, assert embedding is filled.
9. **Per-tenant isolation** — seed docs for clinic A and clinic B, query as A, assert no B doc appears.

For the deterministic embedding tests we monkey-patch `services.rag.embeddings.embed` with a hash-based stub — no real Gemini call in tests.

## Live smoke (after restart)

Reuse `/tmp/v3_live_smoke.py`. After restart, the `answer_caller_question` call should return `status="ok"` (not `"no_match"`) when posed a seeded question, and `get_clinic_faqs()` should return the seeded faqs. We'll need to seed `market-mall-denture` via the admin routes as part of the smoke.

## Safety vs the currently-running uvicorn on port 8001

The running process is on SQLite + d67e688 code. Implementation steps that affect it:

1. **Add code on disk** — no effect on running process.
2. **Run alembic migration** — happens against the new Postgres DB, not the SQLite one in use.
3. **Restart uvicorn** with `DATABASE_URL=postgresql://...` to pick up new code + new DB. The old SQLite file (`dental_clinic_smoke.db`) is preserved on disk, untouched.

So at no point do we mutate the currently-running process or its data. The restart at the end is the only switch-over moment.

## Out of scope

- Re-indexing or migrating existing `ClinicKnowledgeDoc` content into `rag_docs`. The canonical spec covers FAQ + rag_docs as new content; `ClinicKnowledgeDoc` stays as-is for now.
- pgbouncer / connection pool tuning — note from canonical spec is a prod concern.
- Redis-shared cache across replicas — single-process LRU is fine for local + initial deploy.
- Re-embed migration when model changes — `embedding_model` column deferred.
