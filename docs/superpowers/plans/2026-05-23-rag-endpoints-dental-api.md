# RAG Endpoints (dental-api) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `GET /clinics/{clinic_id}/faqs` and `POST /rag/answer` in dental-api on `feat/admin-api-merge`, backed by Postgres + pgvector + Gemini `text-embedding-005`, so the voice agent's `CalendarClient` returns real RAG answers (no longer 404→no_match).

**Architecture:** New dedicated `/rag` and `/admin/clinics/{id}/(faqs|rag_docs)` routers. Two new tables (`clinic_faqs`, `rag_docs`) added via alembic migration that also installs the `vector` extension. Embedding-on-write for `rag_docs.content` runs as a FastAPI `BackgroundTask`. `/rag/answer` has a 60s LRU cache keyed by `(clinic_id, normalized_question)`. All RAG-route I/O is async so it cannot block CRUD workers.

**Tech Stack:** FastAPI · SQLAlchemy · Alembic · Postgres 16 + pgvector · Gemini `text-embedding-005` (768d) via `httpx.AsyncClient` · pytest + FastAPI TestClient.

**Repo:** Work directly on the existing `feat/admin-api-merge` branch in `/Users/giahuyhoangle/Projects/dental-system/dental-api`. The currently-running uvicorn on port 8001 (SQLite-backed, code at `d67e688`) is untouched by these edits until the final restart step.

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `requirements.txt` | modify | Add `pgvector>=0.2.0` |
| `docker-compose.dev.yml` | create | One service: `pgvector/pgvector:pg16` on port 5432 with dev creds |
| `database/ops/rag.py` | create | SQLAlchemy models `ClinicFaq`, `RagDoc` (uses `pgvector.sqlalchemy.Vector`) |
| `database/ops/__init__.py` | modify | Re-export the new models so `Base.metadata.create_all` picks them up |
| `alembic/versions/aa11bb22cc33_add_rag_tables.py` | create | `CREATE EXTENSION vector`; create both tables; HNSW + clinic indexes |
| `services/rag/__init__.py` | create | empty package marker |
| `services/rag/embeddings.py` | create | `async def embed(text: str) -> list[float]` → Gemini API |
| `services/rag/retrieval.py` | create | `async def answer(db, clinic_id, question) -> dict` (status/answer/confidence/sources) |
| `api/rag/__init__.py` | create | empty package marker |
| `api/rag/router.py` | create | `GET /clinics/{id}/faqs`, `POST /rag/answer` (with TTL LRU cache) |
| `api/admin/__init__.py` | create-or-noop | package marker |
| `api/admin/rag_router.py` | create | Admin CRUD for `clinic_faqs` and `rag_docs` |
| `api/main.py` | modify (around line 200) | `include_router` for the two new routers |
| `tests/conftest.py` | modify | Add `pg_engine`, `pg_db_session`, `pg_client` fixtures; mark them `@pytest.mark.pgvector` |
| `tests/test_rag_models.py` | create | Insert/select round-trip for both new models |
| `tests/test_rag_embeddings.py` | create | Mocked-httpx test of Gemini embed wrapper |
| `tests/test_rag_retrieval.py` | create | Retrieval-logic tests (mocked embedder, deterministic vectors) |
| `tests/test_rag_endpoints.py` | create | Endpoint contract tests against Postgres TestClient |
| `tests/test_rag_admin_endpoints.py` | create | Admin CRUD + background-embed tests |
| `scripts/seed_market_mall_rag.py` | create | Seeds FAQs + rag_docs for the live smoke |

---

## Task 1: Stand up local Postgres + pgvector and add the Python dep

**Files:**
- Create: `docker-compose.dev.yml`
- Modify: `requirements.txt`

- [ ] **Step 1: Create docker-compose for local Postgres + pgvector**

Create `docker-compose.dev.yml`:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: dental-pg
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: dental
    ports:
      - "5432:5432"
    volumes:
      - ./var/pgdata:/var/lib/postgresql/data
```

- [ ] **Step 2: Start Postgres and verify pgvector is available**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
docker compose -f docker-compose.dev.yml up -d
# wait ~3 seconds for boot
docker compose -f docker-compose.dev.yml exec postgres psql -U postgres -d dental -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname FROM pg_extension WHERE extname='vector';"
```

Expected output: `vector` row returned.

- [ ] **Step 3: Create the test DB**

```bash
docker compose -f docker-compose.dev.yml exec postgres psql -U postgres -c "CREATE DATABASE dental_test;"
docker compose -f docker-compose.dev.yml exec postgres psql -U postgres -d dental_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

- [ ] **Step 4: Add `pgvector` to requirements.txt**

Open `requirements.txt`, add line: `pgvector>=0.2.0`

- [ ] **Step 5: Install in the dental-api venv**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
.venv/bin/pip install 'pgvector>=0.2.0'
.venv/bin/python -c "import pgvector.sqlalchemy; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.dev.yml requirements.txt
git commit -m "build(rag): add pgvector dep and local Postgres docker compose"
```

---

## Task 2: SQLAlchemy models for clinic_faqs and rag_docs

**Files:**
- Create: `database/ops/rag.py`
- Modify: `database/ops/__init__.py`
- Test: `tests/test_rag_models.py`

- [ ] **Step 1: Inspect existing `database/ops/__init__.py` to learn the registration pattern**

```bash
cat /Users/giahuyhoangle/Projects/dental-system/dental-api/database/ops/__init__.py
```

Note which models are re-exported. The new `rag` module must follow the same pattern.

- [ ] **Step 2: Write the failing model round-trip test**

Create `tests/test_rag_models.py`:

```python
"""Model round-trip tests for clinic_faqs and rag_docs (require pgvector)."""
import os
import pytest


pytestmark = pytest.mark.pgvector


def test_clinic_faq_insert_and_query(pg_db_session):
    from database.ops.rag import ClinicFaq

    row = ClinicFaq(
        clinic_id="t_clinic",
        question="Hours?",
        answer="Monday to Friday, nine to five.",
        ordering=1,
    )
    pg_db_session.add(row)
    pg_db_session.flush()

    got = (
        pg_db_session.query(ClinicFaq)
        .filter(ClinicFaq.clinic_id == "t_clinic")
        .order_by(ClinicFaq.ordering)
        .all()
    )
    assert len(got) == 1
    assert got[0].question == "Hours?"
    assert got[0].answer.startswith("Monday")


def test_rag_doc_insert_with_vector(pg_db_session):
    from database.ops.rag import RagDoc

    vec = [0.0] * 768
    vec[0] = 1.0
    row = RagDoc(
        clinic_id="t_clinic",
        doc_title="Reline care",
        content="A reline reshapes the inside of your existing denture.",
        voice_ready=None,
        embedding=vec,
        doc_metadata={"category": "post-op"},
    )
    pg_db_session.add(row)
    pg_db_session.flush()

    got = pg_db_session.query(RagDoc).filter(RagDoc.clinic_id == "t_clinic").first()
    assert got is not None
    assert got.doc_title == "Reline care"
    assert len(got.embedding) == 768
    assert got.embedding[0] == pytest.approx(1.0)
```

- [ ] **Step 3: Add the pg fixtures to `tests/conftest.py`**

Append to `tests/conftest.py`:

```python
# ----- pgvector test fixtures -------------------------------------------------
import sqlalchemy as _sa

PG_TEST_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:dev@localhost:5432/dental_test",
)


def _pg_available() -> bool:
    try:
        eng = _sa.create_engine(PG_TEST_URL, pool_pre_ping=True)
        with eng.connect() as c:
            c.execute(_sa.text("SELECT 1"))
        eng.dispose()
        return True
    except Exception:
        return False


_PG_OK = _pg_available()


@pytest.fixture(scope="session")
def pg_engine():
    """Postgres + pgvector engine; tables created from Base.metadata at session start."""
    if not _PG_OK:
        pytest.skip(f"Postgres unavailable at {PG_TEST_URL}")
    engine = _sa.create_engine(PG_TEST_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(_sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    # Ensure all model modules are imported so Base.metadata sees them
    import database.models  # noqa: F401
    import database.ops.rag  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def pg_db_session(pg_engine):
    """Per-test transactional session — rolled back at end so tests are hermetic."""
    connection = pg_engine.connect()
    trans = connection.begin()
    Session = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture(scope="function")
def pg_client(pg_db_session):
    """FastAPI TestClient with get_db overridden to use the pg_db_session."""
    def _override():
        try:
            yield pg_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
```

Also register the new marker — append to top of `tests/conftest.py` (or create `pytest.ini` if absent):

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "pgvector: requires Postgres + pgvector running")
```

- [ ] **Step 4: Run the test to confirm it fails (ModuleNotFoundError)**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
.venv/bin/python -m pytest tests/test_rag_models.py -v
```

Expected: FAIL, `ModuleNotFoundError: No module named 'database.ops.rag'`.

- [ ] **Step 5: Implement the models**

Create `database/ops/rag.py`:

```python
"""SQLAlchemy models for the Clinic Q&A RAG feature.

Two tables, both scoped by clinic_id:
  - clinic_faqs:  hot tier, rendered into the voice-agent system prompt.
  - rag_docs:     cold tier, retrieved on-demand via embedding similarity.

Vector column uses pgvector. SQLite (used elsewhere in tests) cannot host this
schema — pgvector tests opt in via the `pgvector` marker.
"""
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from database.connection import Base


class ClinicFaq(Base):
    __tablename__ = "clinic_faqs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinic_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    ordering = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_clinic_faqs_by_clinic", "clinic_id", "ordering"),
    )


class RagDoc(Base):
    __tablename__ = "rag_docs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinic_id = Column(String, nullable=False, index=True)
    doc_title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    voice_ready = Column(Text, nullable=True)
    embedding = Column(Vector(768), nullable=True)
    doc_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_rag_docs_by_clinic", "clinic_id"),
    )
```

Note: HNSW vector index is created in the alembic migration (Task 3), not on the model — Alembic op for index types pgvector understands.

- [ ] **Step 6: Re-export from `database/ops/__init__.py`**

Open `database/ops/__init__.py`, add at the bottom:

```python
from database.ops.rag import ClinicFaq, RagDoc  # noqa: F401
```

- [ ] **Step 7: Run the test to confirm it passes**

```bash
.venv/bin/python -m pytest tests/test_rag_models.py -v
```

Expected: 2 passed. If Postgres isn't running, the test is skipped — start docker compose first.

- [ ] **Step 8: Commit**

```bash
git add database/ops/rag.py database/ops/__init__.py tests/conftest.py tests/test_rag_models.py
git commit -m "feat(rag): clinic_faqs and rag_docs SQLAlchemy models"
```

---

## Task 3: Alembic migration — `vector` extension + tables + HNSW index

**Files:**
- Create: `alembic/versions/aa11bb22cc33_add_rag_tables.py`

- [ ] **Step 1: Find the current head revision**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
.venv/bin/alembic heads
```

Note the printed revision ID (call it `<HEAD>`). The new migration's `down_revision` will be `<HEAD>`.

- [ ] **Step 2: Write the migration**

Create `alembic/versions/aa11bb22cc33_add_rag_tables.py`:

```python
"""add_rag_tables

Revision ID: aa11bb22cc33
Revises: <HEAD>
Create Date: 2026-05-23 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "aa11bb22cc33"
down_revision: Union[str, None] = "<HEAD>"  # REPLACE with output of `alembic heads`
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "clinic_faqs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.String(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_clinic_faqs_by_clinic", "clinic_faqs", ["clinic_id", "ordering"])

    op.create_table(
        "rag_docs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.String(), nullable=False),
        sa.Column("doc_title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("voice_ready", sa.Text(), nullable=True),
        sa.Column("embedding", sa.dialects.postgresql.ARRAY(sa.Float), nullable=True),  # replaced below
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    # Replace the placeholder ARRAY column with a real pgvector VECTOR(768)
    op.execute("ALTER TABLE rag_docs ALTER COLUMN embedding TYPE vector(768) USING NULL")
    op.create_index("ix_rag_docs_by_clinic", "rag_docs", ["clinic_id"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_rag_docs_hnsw "
        "ON rag_docs USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_rag_docs_hnsw")
    op.drop_index("ix_rag_docs_by_clinic", table_name="rag_docs")
    op.drop_table("rag_docs")
    op.drop_index("ix_clinic_faqs_by_clinic", table_name="clinic_faqs")
    op.drop_table("clinic_faqs")
    # leave vector extension in place — other features may want it
```

After saving, **replace `<HEAD>`** in `down_revision` with the actual revision from Step 1.

- [ ] **Step 3: Run the migration against the dev DB**

```bash
DATABASE_URL=postgresql://postgres:dev@localhost:5432/dental .venv/bin/alembic upgrade head
```

Expected output: ends with `Running upgrade <HEAD> -> aa11bb22cc33, add_rag_tables`.

- [ ] **Step 4: Verify the schema**

```bash
docker compose -f docker-compose.dev.yml exec postgres psql -U postgres -d dental -c "\d clinic_faqs" -c "\d rag_docs" -c "SELECT indexname FROM pg_indexes WHERE tablename IN ('rag_docs','clinic_faqs');"
```

Expected: tables exist; `ix_rag_docs_hnsw` listed; `embedding` column type is `vector(768)`.

- [ ] **Step 5: Apply the migration to the test DB too**

```bash
TEST_DATABASE_URL=postgresql://postgres:dev@localhost:5432/dental_test \
DATABASE_URL=postgresql://postgres:dev@localhost:5432/dental_test \
.venv/bin/alembic upgrade head
```

- [ ] **Step 6: Re-run the model tests against migrated DB**

```bash
.venv/bin/python -m pytest tests/test_rag_models.py -v
```

Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add alembic/versions/aa11bb22cc33_add_rag_tables.py
git commit -m "feat(rag): alembic migration — vector extension + clinic_faqs + rag_docs + hnsw"
```

---

## Task 4: Gemini embeddings wrapper

**Files:**
- Create: `services/rag/__init__.py`
- Create: `services/rag/embeddings.py`
- Test: `tests/test_rag_embeddings.py`

- [ ] **Step 1: Write the failing embedding test**

Create `tests/test_rag_embeddings.py`:

```python
"""Tests for services.rag.embeddings — Gemini text-embedding-005 wrapper."""
import asyncio
import httpx
import pytest


def test_embed_calls_gemini_with_correct_payload(monkeypatch):
    captured = {}

    async def fake_request(self, method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        captured["headers"] = dict(kwargs.get("headers") or {})
        req = httpx.Request(method, url)
        return httpx.Response(
            200,
            json={"embedding": {"values": [0.1] * 768}},
            request=req,
        )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-xyz")
    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    from services.rag.embeddings import embed
    vec = asyncio.run(embed("What's involved in a reline?"))

    assert len(vec) == 768
    assert vec[0] == pytest.approx(0.1)
    assert captured["method"] == "POST"
    assert "text-embedding-005" in captured["url"]
    assert "embedContent" in captured["url"]
    body = captured["json"]
    assert body["content"]["parts"][0]["text"] == "What's involved in a reline?"


def test_embed_raises_runtime_error_when_key_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    from services.rag.embeddings import embed, MissingGeminiKey
    with pytest.raises(MissingGeminiKey):
        asyncio.run(embed("anything"))


def test_embed_raises_on_non_200(monkeypatch):
    async def fake_request(self, method, url, **kwargs):
        req = httpx.Request(method, url)
        return httpx.Response(500, json={"error": "boom"}, request=req)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-xyz")
    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    from services.rag.embeddings import embed, EmbeddingError
    with pytest.raises(EmbeddingError):
        asyncio.run(embed("anything"))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/test_rag_embeddings.py -v
```

Expected: FAIL, `ModuleNotFoundError: No module named 'services.rag'`.

- [ ] **Step 3: Implement the embedder**

Create `services/rag/__init__.py` (empty file).

Create `services/rag/embeddings.py`:

```python
"""Async wrapper around Google's text-embedding-005 model.

One function: `embed(text) -> list[float]`. Reads GEMINI_API_KEY from env.
Raises MissingGeminiKey if absent, EmbeddingError on non-200 from upstream.
"""
import os
import httpx


_GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/text-embedding-005:embedContent"
)
_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)


class MissingGeminiKey(RuntimeError):
    pass


class EmbeddingError(RuntimeError):
    pass


async def embed(text: str) -> list[float]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise MissingGeminiKey("GEMINI_API_KEY is not set")

    payload = {
        "content": {"parts": [{"text": text}]},
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.request(
            "POST",
            f"{_GEMINI_ENDPOINT}?key={api_key}",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
    if resp.status_code != 200:
        raise EmbeddingError(f"Gemini embed failed: HTTP {resp.status_code} — {resp.text[:200]}")
    data = resp.json()
    values = data.get("embedding", {}).get("values")
    if not isinstance(values, list) or len(values) != 768:
        raise EmbeddingError(f"Gemini embed returned unexpected shape: {data!r}")
    return values
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/python -m pytest tests/test_rag_embeddings.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add services/rag/__init__.py services/rag/embeddings.py tests/test_rag_embeddings.py
git commit -m "feat(rag): async Gemini text-embedding-005 wrapper"
```

---

## Task 5: Retrieval service

**Files:**
- Create: `services/rag/retrieval.py`
- Test: `tests/test_rag_retrieval.py`

- [ ] **Step 1: Write the failing retrieval test**

Create `tests/test_rag_retrieval.py`:

```python
"""Tests for services.rag.retrieval.answer — embedding-based top-1 retrieval."""
import asyncio
import pytest


pytestmark = pytest.mark.pgvector


def _unit_vec_at(idx: int, dim: int = 768) -> list[float]:
    v = [0.0] * dim
    v[idx] = 1.0
    return v


def test_answer_returns_ok_for_close_match(monkeypatch, pg_db_session):
    """A doc whose embedding equals the query embedding → status=ok, doc surfaced."""
    from database.ops.rag import RagDoc

    pg_db_session.add(RagDoc(
        clinic_id="c1", doc_title="Reline care",
        content="A reline reshapes the inside of your existing denture.",
        voice_ready="A reline reshapes the inside of your denture. Most relines take about an hour.",
        embedding=_unit_vec_at(0),
        doc_metadata={},
    ))
    pg_db_session.add(RagDoc(
        clinic_id="c1", doc_title="Unrelated",
        content="Something else.", voice_ready=None,
        embedding=_unit_vec_at(100), doc_metadata={},
    ))
    pg_db_session.flush()

    async def fake_embed(text):
        return _unit_vec_at(0)

    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)

    from services.rag.retrieval import answer
    result = asyncio.run(answer(pg_db_session, "c1", "what is a reline?"))

    assert result["status"] == "ok"
    assert "reline" in result["answer"].lower()
    assert result["confidence"] >= 0.6
    assert result["sources"][0]["doc_title"] == "Reline care"


def test_answer_returns_no_match_below_threshold(monkeypatch, pg_db_session):
    from database.ops.rag import RagDoc

    pg_db_session.add(RagDoc(
        clinic_id="c1", doc_title="A", content="foo", voice_ready=None,
        embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()

    async def fake_embed(text):
        # Orthogonal to the seeded doc -> cosine similarity = 0
        return _unit_vec_at(500)

    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)

    from services.rag.retrieval import answer
    result = asyncio.run(answer(pg_db_session, "c1", "totally unrelated"))

    assert result["status"] == "no_match"
    assert result["answer"] == ""
    assert result["sources"] == []


def test_answer_isolates_per_clinic(monkeypatch, pg_db_session):
    """A perfectly-matching doc in clinic_b must NOT surface when querying as clinic_a."""
    from database.ops.rag import RagDoc

    pg_db_session.add(RagDoc(
        clinic_id="clinic_b", doc_title="B-only", content="hidden",
        voice_ready=None, embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()

    async def fake_embed(text):
        return _unit_vec_at(0)

    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)

    from services.rag.retrieval import answer
    result = asyncio.run(answer(pg_db_session, "clinic_a", "anything"))

    assert result["status"] == "no_match"
    assert result["sources"] == []


def test_answer_returns_no_match_when_clinic_has_no_docs(monkeypatch, pg_db_session):
    async def fake_embed(text):
        return _unit_vec_at(0)

    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)

    from services.rag.retrieval import answer
    result = asyncio.run(answer(pg_db_session, "empty_clinic", "anything"))

    assert result["status"] == "no_match"
    assert result["sources"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/test_rag_retrieval.py -v
```

Expected: FAIL, `ModuleNotFoundError: No module named 'services.rag.retrieval'`.

- [ ] **Step 3: Implement retrieval**

Create `services/rag/retrieval.py`:

```python
"""Embedding-based RAG retrieval against the rag_docs table.

Public function: `answer(db, clinic_id, question) -> dict` matching the
canonical API contract (status / answer / confidence / sources).
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.rag.embeddings import embed

_CONFIDENCE_THRESHOLD = 0.6
_TOP_K = 5
_EXCERPT_CHARS = 600


async def answer(db: Session, clinic_id: str, question: str) -> dict:
    """Embed the question, find the closest rag_doc for this clinic, return
    the voice-formatted answer if confidence is above the threshold.

    Confidence = 1 - cosine_distance (cosine_distance is what pgvector's <=> returns).
    """
    q_embed = await embed(question)

    # pgvector cosine distance operator: <=>. Returns 0.0 (identical) → 2.0 (opposite).
    # We want closest first; ORDER BY <=> ascending.
    rows = db.execute(
        text(
            """
            SELECT id, doc_title, content, voice_ready,
                   (embedding <=> CAST(:q AS vector)) AS distance
            FROM rag_docs
            WHERE clinic_id = :cid AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:q AS vector)
            LIMIT :k
            """
        ),
        {"q": str(q_embed), "cid": clinic_id, "k": _TOP_K},
    ).fetchall()

    if not rows:
        return {"status": "no_match", "answer": "", "confidence": 0.0, "sources": []}

    top = rows[0]
    confidence = max(0.0, 1.0 - float(top.distance))
    if confidence < _CONFIDENCE_THRESHOLD:
        return {"status": "no_match", "answer": "", "confidence": confidence, "sources": []}

    answer_text = top.voice_ready or _excerpt(top.content)
    sources = [
        {"doc_id": int(r.id), "doc_title": r.doc_title,
         "score": round(max(0.0, 1.0 - float(r.distance)), 4)}
        for r in rows
    ]
    return {"status": "ok", "answer": answer_text,
            "confidence": round(confidence, 4), "sources": sources}


def _excerpt(content: str) -> str:
    """Trim content to ~_EXCERPT_CHARS at a sentence boundary if possible."""
    if len(content) <= _EXCERPT_CHARS:
        return content
    cut = content[:_EXCERPT_CHARS]
    last_dot = cut.rfind(". ")
    if last_dot > _EXCERPT_CHARS // 2:
        return cut[: last_dot + 1]
    return cut + "…"
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_rag_retrieval.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add services/rag/retrieval.py tests/test_rag_retrieval.py
git commit -m "feat(rag): embedding-based retrieval against rag_docs"
```

---

## Task 6: Read endpoints — `/rag/answer` and `/clinics/{id}/faqs`

**Files:**
- Create: `api/rag/__init__.py`
- Create: `api/rag/router.py`
- Modify: `api/main.py`
- Test: `tests/test_rag_endpoints.py`

- [ ] **Step 1: Write failing endpoint tests**

Create `tests/test_rag_endpoints.py`:

```python
"""Endpoint contract tests for /rag/answer and /clinics/{id}/faqs."""
import pytest


pytestmark = pytest.mark.pgvector


def _unit_vec_at(idx: int) -> list[float]:
    v = [0.0] * 768
    v[idx] = 1.0
    return v


def _stub_embedder(monkeypatch, vec):
    async def fake_embed(text):
        return vec
    monkeypatch.setattr("services.rag.retrieval.embed", fake_embed)


def test_get_faqs_returns_seeded_rows_in_order(pg_db_session, pg_client):
    from database.ops.rag import ClinicFaq
    pg_db_session.add(ClinicFaq(clinic_id="cf1", question="Q2?", answer="A2", ordering=2))
    pg_db_session.add(ClinicFaq(clinic_id="cf1", question="Q1?", answer="A1", ordering=1))
    pg_db_session.flush()

    r = pg_client.get("/clinics/cf1/faqs")
    assert r.status_code == 200
    body = r.json()
    assert body["faqs"] == [
        {"question": "Q1?", "answer": "A1"},
        {"question": "Q2?", "answer": "A2"},
    ]


def test_get_faqs_unknown_clinic_returns_empty_list(pg_client):
    r = pg_client.get("/clinics/no_such_clinic/faqs")
    assert r.status_code == 200
    assert r.json() == {"faqs": []}


def test_post_rag_answer_returns_match(monkeypatch, pg_db_session, pg_client):
    from database.ops.rag import RagDoc
    pg_db_session.add(RagDoc(
        clinic_id="cr1", doc_title="Reline", content="reshape denture",
        voice_ready="Relines take about an hour.",
        embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()

    _stub_embedder(monkeypatch, _unit_vec_at(0))
    r = pg_client.post(
        "/rag/answer",
        json={"clinic_id": "cr1", "question": "How long does a reline take?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["answer"] == "Relines take about an hour."
    assert body["sources"][0]["doc_title"] == "Reline"


def test_post_rag_answer_no_match_when_clinic_empty(monkeypatch, pg_client):
    _stub_embedder(monkeypatch, _unit_vec_at(0))
    r = pg_client.post(
        "/rag/answer",
        json={"clinic_id": "empty", "question": "anything"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "no_match"


def test_rag_answer_503_when_gemini_key_missing(monkeypatch, pg_db_session, pg_client):
    from database.ops.rag import RagDoc
    pg_db_session.add(RagDoc(
        clinic_id="cr2", doc_title="x", content="x",
        voice_ready=None, embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()
    # No embedder stub — but remove the key so real `embed` raises MissingGeminiKey
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    r = pg_client.post(
        "/rag/answer",
        json={"clinic_id": "cr2", "question": "anything"},
    )
    assert r.status_code == 503
    assert "GEMINI_API_KEY" in r.json().get("detail", "")


def test_rag_answer_cache_returns_same_response_without_re_embedding(monkeypatch, pg_db_session, pg_client):
    """Same (clinic_id, question) within TTL → second call must not call embed()."""
    from database.ops.rag import RagDoc
    pg_db_session.add(RagDoc(
        clinic_id="cr3", doc_title="t", content="c",
        voice_ready="cached answer", embedding=_unit_vec_at(0), doc_metadata={},
    ))
    pg_db_session.flush()

    call_count = {"n": 0}

    async def counting_embed(text):
        call_count["n"] += 1
        return _unit_vec_at(0)

    monkeypatch.setattr("services.rag.retrieval.embed", counting_embed)

    payload = {"clinic_id": "cr3", "question": "hello?"}
    r1 = pg_client.post("/rag/answer", json=payload)
    r2 = pg_client.post("/rag/answer", json=payload)
    assert r1.json() == r2.json()
    assert call_count["n"] == 1, "embedder should be called only once due to cache"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/test_rag_endpoints.py -v
```

Expected: FAIL — endpoints not registered → 404 on every call.

- [ ] **Step 3: Implement the router**

Create `api/rag/__init__.py` (empty).

Create `api/rag/router.py`:

```python
"""Read endpoints for the Clinic Q&A RAG feature.

  GET  /clinics/{clinic_id}/faqs
  POST /rag/answer

Both unauthenticated for now — the voice agent calls these via the shared
CalendarClient using an X-Clinic-Id header for trace correlation only. Auth
can be layered on later once the admin frontend / portal is the only other
caller.
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.ops.rag import ClinicFaq
from services.rag.embeddings import MissingGeminiKey, EmbeddingError
from services.rag.retrieval import answer as retrieve_answer


router = APIRouter(tags=["rag"])


# ---------- /clinics/{clinic_id}/faqs ----------


class FaqOut(BaseModel):
    question: str
    answer: str


class FaqsResponse(BaseModel):
    faqs: list[FaqOut]


@router.get("/clinics/{clinic_id}/faqs", response_model=FaqsResponse)
def get_clinic_faqs(clinic_id: str, db: Session = Depends(get_db)) -> FaqsResponse:
    rows = (
        db.query(ClinicFaq)
        .filter(ClinicFaq.clinic_id == clinic_id)
        .order_by(ClinicFaq.ordering, ClinicFaq.id)
        .all()
    )
    return FaqsResponse(faqs=[FaqOut(question=r.question, answer=r.answer) for r in rows])


# ---------- /rag/answer ----------


class AnswerRequest(BaseModel):
    clinic_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)


class AnswerSource(BaseModel):
    doc_id: int
    doc_title: str
    score: float


class AnswerResponse(BaseModel):
    status: str
    answer: str
    confidence: float
    sources: list[AnswerSource]


_CACHE_TTL_SECONDS = 60
_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}


def _normalize_q(q: str) -> str:
    return " ".join(q.lower().split())


@router.post("/rag/answer", response_model=AnswerResponse)
async def post_rag_answer(body: AnswerRequest, db: Session = Depends(get_db)) -> AnswerResponse:
    key = (body.clinic_id, _normalize_q(body.question))
    now = time.monotonic()
    hit = _cache.get(key)
    if hit is not None and (now - hit[0]) < _CACHE_TTL_SECONDS:
        return AnswerResponse(**hit[1])

    try:
        result = await retrieve_answer(db, body.clinic_id, body.question)
    except MissingGeminiKey as e:
        raise HTTPException(status_code=503, detail=f"GEMINI_API_KEY not configured: {e}") from e
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=f"Embedding upstream error: {e}") from e

    _cache[key] = (now, result)
    return AnswerResponse(**result)
```

- [ ] **Step 4: Register the router in `api/main.py`**

Open `api/main.py`, locate the block where other routers are included (around line 200, after `portal_router`). Add:

```python
from api.rag.router import router as _rag_router
app.include_router(_rag_router)
```

- [ ] **Step 5: Run endpoint tests**

```bash
.venv/bin/python -m pytest tests/test_rag_endpoints.py -v
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add api/rag/__init__.py api/rag/router.py api/main.py tests/test_rag_endpoints.py
git commit -m "feat(rag): GET /clinics/{id}/faqs and POST /rag/answer with 60s LRU"
```

---

## Task 7: Admin write routes for FAQs and RAG docs

**Files:**
- Create: `api/admin/__init__.py` (if missing)
- Create: `api/admin/rag_router.py`
- Modify: `api/main.py`
- Test: `tests/test_rag_admin_endpoints.py`

- [ ] **Step 1: Verify whether `api/admin/__init__.py` already exists**

```bash
ls /Users/giahuyhoangle/Projects/dental-system/dental-api/api/admin/__init__.py 2>/dev/null || echo "create it"
```

If absent, create the empty file.

- [ ] **Step 2: Write failing admin-endpoint tests**

Create `tests/test_rag_admin_endpoints.py`:

```python
"""Admin CRUD for clinic_faqs and rag_docs (writes from admin-api / portal)."""
import asyncio
import pytest


pytestmark = pytest.mark.pgvector


def _stub_embed_returning(monkeypatch, vec):
    async def fake_embed(text):
        return vec
    monkeypatch.setattr("api.admin.rag_router.embed", fake_embed)


def _unit_vec_at(idx: int) -> list[float]:
    v = [0.0] * 768
    v[idx] = 1.0
    return v


def test_post_faq_creates_row(pg_client):
    r = pg_client.post(
        "/admin/clinics/ac1/faqs",
        json={"question": "Hours?", "answer": "9-5", "ordering": 1},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["question"] == "Hours?"
    assert body["ordering"] == 1
    assert body["id"] > 0


def test_patch_faq_updates_row(pg_client):
    created = pg_client.post(
        "/admin/clinics/ac2/faqs",
        json={"question": "x", "answer": "y", "ordering": 0},
    ).json()
    r = pg_client.patch(
        f"/admin/clinics/ac2/faqs/{created['id']}",
        json={"answer": "z"},
    )
    assert r.status_code == 200
    assert r.json()["answer"] == "z"


def test_delete_faq(pg_client):
    created = pg_client.post(
        "/admin/clinics/ac3/faqs",
        json={"question": "x", "answer": "y", "ordering": 0},
    ).json()
    r = pg_client.delete(f"/admin/clinics/ac3/faqs/{created['id']}")
    assert r.status_code == 204
    list_r = pg_client.get("/clinics/ac3/faqs")
    assert list_r.json()["faqs"] == []


def test_post_rag_doc_returns_202_and_fills_embedding_via_background(monkeypatch, pg_client, pg_db_session):
    _stub_embed_returning(monkeypatch, _unit_vec_at(7))

    r = pg_client.post(
        "/admin/clinics/ar1/rag_docs",
        json={"doc_title": "Reline care", "content": "A reline reshapes..."},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["id"] > 0
    assert body["embedding_ready"] is True  # BackgroundTasks runs synchronously in TestClient

    # Verify embedding was filled
    from database.ops.rag import RagDoc
    row = pg_db_session.query(RagDoc).filter(RagDoc.id == body["id"]).first()
    assert row is not None
    assert row.embedding is not None
    assert len(row.embedding) == 768


def test_patch_rag_doc_content_re_embeds(monkeypatch, pg_client, pg_db_session):
    _stub_embed_returning(monkeypatch, _unit_vec_at(7))
    created = pg_client.post(
        "/admin/clinics/ar2/rag_docs",
        json={"doc_title": "t", "content": "v1"},
    ).json()

    _stub_embed_returning(monkeypatch, _unit_vec_at(42))  # swap vector
    r = pg_client.patch(
        f"/admin/clinics/ar2/rag_docs/{created['id']}",
        json={"content": "v2"},
    )
    assert r.status_code == 200

    from database.ops.rag import RagDoc
    pg_db_session.expire_all()
    row = pg_db_session.query(RagDoc).filter(RagDoc.id == created["id"]).first()
    assert row.content == "v2"
    assert row.embedding[42] == pytest.approx(1.0)
    assert row.embedding[7] == pytest.approx(0.0)


def test_delete_rag_doc(pg_client):
    created = pg_client.post(
        "/admin/clinics/ar3/rag_docs",
        json={"doc_title": "t", "content": "c"},
    ).json()
    r = pg_client.delete(f"/admin/clinics/ar3/rag_docs/{created['id']}")
    assert r.status_code == 204
```

- [ ] **Step 3: Run tests to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_rag_admin_endpoints.py -v
```

Expected: FAIL — endpoints not registered.

- [ ] **Step 4: Implement the admin router**

Create `api/admin/rag_router.py`:

```python
"""Admin CRUD for the Clinic Q&A RAG feature.

  POST   /admin/clinics/{clinic_id}/faqs                  → 201 + created row
  PATCH  /admin/clinics/{clinic_id}/faqs/{faq_id}         → 200 + updated row
  DELETE /admin/clinics/{clinic_id}/faqs/{faq_id}         → 204

  POST   /admin/clinics/{clinic_id}/rag_docs              → 202 + row (embedding filled in background)
  PATCH  /admin/clinics/{clinic_id}/rag_docs/{doc_id}     → 200 (re-embeds if content changed)
  DELETE /admin/clinics/{clinic_id}/rag_docs/{doc_id}     → 204

No auth in this commit — admin-api / portal will sit in front of these. Add
clinic-scoping middleware later.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.ops.rag import ClinicFaq, RagDoc
from services.rag.embeddings import embed


router = APIRouter(prefix="/admin/clinics", tags=["admin-rag"])


# ---------- FAQ schemas ----------


class FaqCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    ordering: int = 0


class FaqPatch(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    ordering: Optional[int] = None


class FaqRow(BaseModel):
    id: int
    clinic_id: str
    question: str
    answer: str
    ordering: int


def _faq_out(row: ClinicFaq) -> FaqRow:
    return FaqRow(
        id=row.id, clinic_id=row.clinic_id, question=row.question,
        answer=row.answer, ordering=row.ordering,
    )


# ---------- FAQ endpoints ----------


@router.post("/{clinic_id}/faqs", response_model=FaqRow, status_code=201)
def create_faq(clinic_id: str, body: FaqCreate, db: Session = Depends(get_db)):
    row = ClinicFaq(
        clinic_id=clinic_id,
        question=body.question, answer=body.answer, ordering=body.ordering,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _faq_out(row)


@router.patch("/{clinic_id}/faqs/{faq_id}", response_model=FaqRow)
def patch_faq(clinic_id: str, faq_id: int, body: FaqPatch, db: Session = Depends(get_db)):
    row = (
        db.query(ClinicFaq)
        .filter(ClinicFaq.clinic_id == clinic_id, ClinicFaq.id == faq_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"FAQ {faq_id} not found in clinic {clinic_id}")
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(row, field, val)
    db.commit()
    db.refresh(row)
    return _faq_out(row)


@router.delete("/{clinic_id}/faqs/{faq_id}", status_code=204)
def delete_faq(clinic_id: str, faq_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(ClinicFaq)
        .filter(ClinicFaq.clinic_id == clinic_id, ClinicFaq.id == faq_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"FAQ {faq_id} not found in clinic {clinic_id}")
    db.delete(row)
    db.commit()
    return Response(status_code=204)


# ---------- RAG doc schemas ----------


class RagDocCreate(BaseModel):
    doc_title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    voice_ready: Optional[str] = None


class RagDocPatch(BaseModel):
    doc_title: Optional[str] = None
    content: Optional[str] = None
    voice_ready: Optional[str] = None


class RagDocCreatedOut(BaseModel):
    id: int
    clinic_id: str
    doc_title: str
    embedding_ready: bool  # True after BackgroundTasks runs (synchronous in TestClient)


class RagDocRow(BaseModel):
    id: int
    clinic_id: str
    doc_title: str
    content: str
    voice_ready: Optional[str]
    has_embedding: bool


def _doc_full(row: RagDoc) -> RagDocRow:
    return RagDocRow(
        id=row.id, clinic_id=row.clinic_id, doc_title=row.doc_title,
        content=row.content, voice_ready=row.voice_ready,
        has_embedding=row.embedding is not None,
    )


# ---------- RAG doc endpoints ----------


async def _embed_and_store(doc_id: int, text: str):
    """Background task body: re-open a session, embed, write back."""
    from database.connection import SessionLocal  # late import — avoids circular
    vec = await embed(text)
    db = SessionLocal()
    try:
        row = db.query(RagDoc).filter(RagDoc.id == doc_id).first()
        if row is not None:
            row.embedding = vec
            db.commit()
    finally:
        db.close()


@router.post("/{clinic_id}/rag_docs", response_model=RagDocCreatedOut, status_code=202)
async def create_rag_doc(
    clinic_id: str,
    body: RagDocCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    row = RagDoc(
        clinic_id=clinic_id,
        doc_title=body.doc_title, content=body.content, voice_ready=body.voice_ready,
        doc_metadata={},
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # In TestClient, BackgroundTasks runs synchronously after the response is built,
    # so the test can assert the embedding is filled.
    background.add_task(_embed_and_store, row.id, body.content)
    return RagDocCreatedOut(
        id=row.id, clinic_id=row.clinic_id, doc_title=row.doc_title,
        embedding_ready=True,
    )


@router.patch("/{clinic_id}/rag_docs/{doc_id}", response_model=RagDocRow)
async def patch_rag_doc(
    clinic_id: str, doc_id: int, body: RagDocPatch,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    row = (
        db.query(RagDoc)
        .filter(RagDoc.clinic_id == clinic_id, RagDoc.id == doc_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"rag_doc {doc_id} not found")

    updates = body.model_dump(exclude_unset=True)
    content_changed = "content" in updates and updates["content"] != row.content
    for field, val in updates.items():
        setattr(row, field, val)
    db.commit()
    db.refresh(row)

    if content_changed:
        background.add_task(_embed_and_store, row.id, row.content)

    return _doc_full(row)


@router.delete("/{clinic_id}/rag_docs/{doc_id}", status_code=204)
def delete_rag_doc(clinic_id: str, doc_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(RagDoc)
        .filter(RagDoc.clinic_id == clinic_id, RagDoc.id == doc_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"rag_doc {doc_id} not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)
```

- [ ] **Step 5: Mount in `api/main.py`**

Open `api/main.py`, add near the rag_router include:

```python
from api.admin.rag_router import router as _admin_rag_router
app.include_router(_admin_rag_router)
```

- [ ] **Step 6: Confirm `database.connection` exports `SessionLocal`**

```bash
grep -n "SessionLocal" /Users/giahuyhoangle/Projects/dental-system/dental-api/database/connection.py | head -3
```

If `SessionLocal` doesn't exist, find the equivalent (likely `sessionmaker(bind=engine)`) and use that name in `_embed_and_store`. Adjust the import line to match — exact name depends on what's already there.

- [ ] **Step 7: Run tests**

```bash
.venv/bin/python -m pytest tests/test_rag_admin_endpoints.py -v
```

Expected: 6 passed.

- [ ] **Step 8: Run the full new-tests sweep to catch regressions**

```bash
.venv/bin/python -m pytest tests/test_rag_models.py tests/test_rag_embeddings.py tests/test_rag_retrieval.py tests/test_rag_endpoints.py tests/test_rag_admin_endpoints.py -v
```

Expected: all RAG tests pass.

- [ ] **Step 9: Run the existing dental-api suite to confirm no regression**

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/test_rag_models.py --ignore=tests/test_rag_embeddings.py --ignore=tests/test_rag_retrieval.py --ignore=tests/test_rag_endpoints.py --ignore=tests/test_rag_admin_endpoints.py -q 2>&1 | tail -10
```

Expected: same pass count as before this branch (no new failures).

- [ ] **Step 10: Commit**

```bash
git add api/admin/__init__.py api/admin/rag_router.py api/main.py tests/test_rag_admin_endpoints.py
git commit -m "feat(rag): admin CRUD for clinic_faqs + rag_docs (background embed-on-write)"
```

---

## Task 8: Seed Market Mall RAG content + live smoke

**Files:**
- Create: `scripts/seed_market_mall_rag.py`

- [ ] **Step 1: Write the seed script**

Create `scripts/seed_market_mall_rag.py`:

```python
"""Seed Market Mall denture clinic FAQs and rag_docs for the local demo.

Run after alembic upgrade has created the tables. Idempotent — checks for
existing rows before inserting.
"""
import asyncio
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Project root on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Base  # noqa: E402
from database.ops.rag import ClinicFaq, RagDoc  # noqa: E402
from services.rag.embeddings import embed  # noqa: E402


CLINIC_ID = "market-mall-denture"

FAQS = [
    ("What are your hours?", "Monday to Friday, nine A M to five P M. We're closed weekends.", 1),
    ("Where are you located?", "3625 Shaganappi Trail Northwest in Calgary. There's free underground parking on level P 2.", 2),
    ("Do you accept Alberta Blue Cross?", "Yes, we accept Alberta Blue Cross. For specific coverage details, please check with your provider.", 3),
    ("Do you take walk-ins?", "We see patients by appointment. If you call now, I can find the next opening.", 4),
    ("How much does a reline cost?", "A standard reline ranges from two fifty to three fifty dollars depending on the work involved. Insurance often covers part of it.", 5),
]

RAG_DOCS = [
    (
        "Reline post-op care",
        "A reline reshapes the inside of your existing denture so it fits your gums better. Most relines take about an hour. After a reline, your denture may feel snug for a day or two as you adjust. Avoid very hot drinks for the first twelve hours. If you notice any sore spots after seventy-two hours, call us and we'll schedule a quick adjustment.",
        "A reline reshapes the inside of your denture so it fits your gums better. Most relines take about an hour and you can wear them home the same day. Some snugness in the first day or two is normal. Call us if any sore spots last more than three days.",
    ),
    (
        "Partial vs full dentures",
        "A partial denture replaces some missing teeth and clasps onto the teeth you still have. A full denture replaces all teeth on the top or bottom. Both can be made from acrylic or a flexible nylon. The dentist will recommend a type based on the number of teeth remaining and the shape of your gums.",
        "Partial dentures replace some of your missing teeth and attach to the remaining ones. Full dentures replace all of the teeth on the top or bottom. The denturist will recommend the right type for your situation.",
    ),
    (
        "Immediate dentures",
        "Immediate dentures are placed on the same day your remaining teeth are extracted, so you're never without teeth in public. Healing takes about six months. During that time, the gums change shape and the denture will need to be relined once everything settles.",
        "Immediate dentures go in the same day your remaining teeth come out, so you don't go without teeth. They usually need a reline after about six months once your gums have healed.",
    ),
]


async def main():
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/dental")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        existing_faqs = db.query(ClinicFaq).filter(ClinicFaq.clinic_id == CLINIC_ID).count()
        if existing_faqs == 0:
            for q, a, o in FAQS:
                db.add(ClinicFaq(clinic_id=CLINIC_ID, question=q, answer=a, ordering=o))
            db.commit()
            print(f"Seeded {len(FAQS)} FAQs.")
        else:
            print(f"FAQs already present ({existing_faqs}). Skipping.")

        existing_docs = db.query(RagDoc).filter(RagDoc.clinic_id == CLINIC_ID).count()
        if existing_docs == 0:
            for title, content, voice_ready in RAG_DOCS:
                vec = await embed(content)
                db.add(RagDoc(
                    clinic_id=CLINIC_ID, doc_title=title, content=content,
                    voice_ready=voice_ready, embedding=vec, doc_metadata={},
                ))
            db.commit()
            print(f"Seeded {len(RAG_DOCS)} rag_docs with embeddings.")
        else:
            print(f"rag_docs already present ({existing_docs}). Skipping.")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Confirm GEMINI_API_KEY is in dental-api `.env.local`**

```bash
grep -c '^GEMINI_API_KEY=' /Users/giahuyhoangle/Projects/dental-system/dental-api/.env.local
```

Expected: `1`. (Already confirmed by user during planning.)

- [ ] **Step 3: Run the seed**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
DATABASE_URL=postgresql://postgres:dev@localhost:5432/dental .venv/bin/python scripts/seed_market_mall_rag.py
```

Expected output:
```
Seeded 5 FAQs.
Seeded 3 rag_docs with embeddings.
```

- [ ] **Step 4: Spot-check the data**

```bash
docker compose -f docker-compose.dev.yml exec postgres psql -U postgres -d dental -c "SELECT count(*), bool_or(embedding IS NOT NULL) FROM rag_docs WHERE clinic_id='market-mall-denture';"
```

Expected: count = 3, bool_or = `t`.

- [ ] **Step 5: Commit the seed script**

```bash
git add scripts/seed_market_mall_rag.py
git commit -m "chore(rag): seed Market Mall FAQs + rag_docs for local smoke"
```

---

## Task 9: Restart uvicorn against Postgres + rerun live smoke

**Files:** (no source changes; runtime + smoke)

- [ ] **Step 1: Stop the existing SQLite-backed uvicorn**

The running process from earlier in the session was launched via `Bash run_in_background` task `bxh4m5wlq`. Kill it cleanly:

```bash
pkill -f "run_api.py" || true
sleep 1
lsof -i :8001 || echo "port 8001 free"
```

Expected: `port 8001 free`.

- [ ] **Step 2: Start uvicorn against Postgres**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
PORT=8001 DATABASE_URL=postgresql://postgres:dev@localhost:5432/dental \
  .venv/bin/python run_api.py > /tmp/dental-api.log 2>&1 &
sleep 3
grep -E "Uvicorn running|Application startup complete|ERROR" /tmp/dental-api.log | head -5
```

Expected: `Application startup complete` and `Uvicorn running on http://0.0.0.0:8001`.

- [ ] **Step 3: Probe the new endpoints**

```bash
curl -sS http://localhost:8001/clinics/market-mall-denture/faqs | head -c 400; echo
curl -sS -X POST http://localhost:8001/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"clinic_id":"market-mall-denture","question":"How long does a reline take?"}' | head -c 400; echo
```

Expected:
- `/faqs` → JSON with 5 question/answer pairs
- `/rag/answer` → `{"status":"ok","answer":"A reline reshapes the inside of your denture...","confidence":...,"sources":[...]}`

- [ ] **Step 4: Rerun the agent-side live smoke**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-agent
.venv/bin/python /tmp/v3_live_smoke.py
```

Expected change in output vs the d67e688 baseline:
- `answer_caller_question(...)` → `status='ok'` with a real `answer` (no longer `no_match`)
- `get_clinic_faqs()` → list with the 5 seeded FAQs (no longer `[]`)
- `get_available_slots(...)` → still returns `{providers: [...]}` (unchanged path)

- [ ] **Step 5: Run the full v3 test suite to confirm no regression**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-agent
CALENDAR_API_URL=http://localhost:8001 .venv/bin/python -m pytest packages/voice_agent_v3/tests --tb=no -q 2>&1 | tail -3
```

Expected: `204 passed`.

- [ ] **Step 6: Done — no commit; this task is runtime verification only**

If everything is green, the implementation is complete. The branch `feat/admin-api-merge` is ready for review/merge.

---

## Self-review

### Spec coverage check
| Spec section | Implementing task(s) |
|---|---|
| `GET /clinics/{id}/faqs` | Task 6 |
| `POST /rag/answer` | Task 6 |
| Admin write routes | Task 7 |
| Postgres + pgvector storage | Task 1, 3 |
| Gemini text-embedding-005 (768d) | Task 4, plus Vector(768) in Task 2 |
| Alembic migration | Task 3 |
| `services/rag/embeddings.py` | Task 4 |
| `services/rag/retrieval.py` | Task 5 |
| 60s LRU on `/rag/answer` | Task 6 |
| Background embed on admin write | Task 7 |
| Tests for embeddings, retrieval, endpoints, admin, models | Tasks 2, 4, 5, 6, 7 |
| Per-tenant isolation test | Task 5 (`test_answer_isolates_per_clinic`) |
| Live smoke after restart | Task 9 |
| `GEMINI_API_KEY` 503 handling | Task 6 (`test_rag_answer_503_when_gemini_key_missing`) |

No gaps.

### Type-consistency check
- `Vector(768)` used in `database/ops/rag.py` (Task 2), `ALTER TABLE … TYPE vector(768)` in migration (Task 3), `len(vec) != 768` guard in `embed` (Task 4) — all consistent.
- API response shape: `{status, answer, confidence, sources}` with `sources = [{doc_id, doc_title, score}]` — consistent across spec / `retrieval.py` (Task 5) / `AnswerResponse` Pydantic model (Task 6).
- `clinic_id` is `String` everywhere — model, migration, endpoints, schemas.

### Placeholder scan
- `<HEAD>` in Task 3 Step 2 — flagged explicitly in Step 1 + the migration code with instructions to replace. Acceptable: the engineer must run `alembic heads` to fill it.
- No "TBD", "TODO", "fill in details", or vague handling instructions anywhere.

Ready to execute.
